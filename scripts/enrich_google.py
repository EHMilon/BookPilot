"""Enrich missing metadata.json files via Google Books API.

Primary for the folders Open Library missed (network outage), plus fills
description/pageCount/categories wherever Google scores better.
Key comes ONLY from env var GOOGLE_BOOKS_KEY (never committed).

Usage: GOOGLE_BOOKS_KEY=... python3 scripts/enrich_google.py [--limit N]
"""

import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "book_manifest.json"
BOOKS_DIR = ROOT / "books"
REPORT = Path(__file__).resolve().parent / "fetch_report.json"

SLEEP = 0.15
MIN_SCORE = 0.34
STOP = {
    "the", "a", "an", "of", "and", "in", "on", "to", "for", "how",
    "is", "it", "its", "by", "with", "from", "at", "my",
}


def tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if t not in STOP]


def score(qt, title, authors):
    if not qt:
        return 0.0
    hay = set(tokens(title) + tokens(" ".join(authors or [])))
    return sum(1 for t in qt if t in hay) / len(qt)


def variants(folder):
    words = folder.split("-")
    out = [" ".join(words)]
    for n in (2, 3, 4):
        if len(words) > n + 1:
            out.append(" ".join(words[:-n]))
    return out


def search(query, key):
    params = urllib.parse.urlencode({
        "q": query, "maxResults": 5, "printType": "books", "key": key,
    })
    req = urllib.request.Request(
        f"https://www.googleapis.com/books/v1/volumes?{params}",
        headers={"User-Agent": "BookPilot/2.0 (metadata backfill)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get("items", [])


def clean_desc(raw, limit=320):
    text = re.sub(r"<[^>]+>", " ", html.unescape(raw or "")).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = cut.rfind(". ")
    return (cut[:dot + 1] if dot > 120 else cut.rstrip() + "…")


def to_metadata(folder, item, query, s):
    vi = item.get("volumeInfo", {})
    ids = {d.get("type"): d.get("identifier", "")
           for d in vi.get("industryIdentifiers", [])}
    authors = vi.get("authors", [])
    cats = vi.get("categories", [])
    return {
        "id": folder,
        "title": vi.get("title", ""),
        "author": authors[0] if authors else "",
        "authors": authors,
        "publisher": vi.get("publisher", ""),
        "publishedDate": vi.get("publishedDate", ""),
        "isbn13": ids.get("ISBN_13", ""),
        "isbn10": ids.get("ISBN_10", ""),
        "pageCount": vi.get("pageCount", 0),
        "googleCategories": cats,
        "description": clean_desc(vi.get("description", "")),
        "source": "google-books",
        "sourceId": item.get("id", ""),
        "sourceQuery": query,
        "sourceScore": round(s, 3),
        "review": s < MIN_SCORE,
    }


def main():
    key = os.environ.get("GOOGLE_BOOKS_KEY", "")
    if not key:
        print("Set GOOGLE_BOOKS_KEY env var.")
        return 1
    args = sys.argv[1:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None

    manifest_ids = {b["id"] for b in json.loads(MANIFEST.read_text())["books"]}
    folders = sorted(d.name for d in BOOKS_DIR.iterdir() if d.is_dir())
    missing = [f for f in folders if f not in manifest_ids]
    if limit:
        missing = missing[:limit]

    report = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    written = {r["id"]: r for r in report.get("written", [])}
    failed_ids = [f["id"] for f in report.get("failed", [])]
    targets = [f for f in missing if f in failed_ids or f not in written]
    print(f"targets: {len(targets)} (failed retry + not yet attempted)")

    fixed, still_bad = 0, []
    for i, folder in enumerate(targets, 1):
        if (BOOKS_DIR / folder / "metadata.json").exists():
            continue
        print(f"[{i}/{len(targets)}] {folder}", flush=True)
        best = (None, "", 0.0)
        try:
            for q in variants(folder):
                for item in search(q, key):
                    vi = item.get("volumeInfo", {})
                    s = score(tokens(q), vi.get("title", ""), vi.get("authors", []))
                    if s > best[2]:
                        best = (item, q, s)
                time.sleep(SLEEP)
                if best[2] >= 0.8:
                    break
        except Exception as e:
            print(f"  ! error: {e}", flush=True)
            still_bad.append(folder)
            continue
        item, q, s = best
        if item is None:
            still_bad.append(folder)
            print("  -> NO RESULTS", flush=True)
            continue
        meta = to_metadata(folder, item, q, s)
        (BOOKS_DIR / folder / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        written[folder] = {"id": folder, "title": meta["title"],
                           "score": meta["sourceScore"], "review": meta["review"]}
        fixed += 1
        print(f"  -> {meta['title']} / {meta['author']} ({s:.2f})", flush=True)

    report["written"] = sorted(written.values(), key=lambda r: r["id"])
    report["failed"] = [{"id": f, "reason": "google-books no results"} for f in still_bad]
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nDone: +{fixed} via google-books, {len(still_bad)} still missing.")


if __name__ == "__main__":
    sys.exit(main())
