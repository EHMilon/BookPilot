"""Fetch best-effort metadata for book folders missing from the manifest.

Source: Open Library Search API (no key, generous limits).
For each folder in books/ with no manifest entry, queries Open Library,
picks the best-matching doc, and writes books/<id>/metadata.json.

Writes are resume-safe: folders already containing metadata.json are skipped.
Low-confidence matches are still written but flagged ("review": true) for a
later manual pass (read summary + websearch) instead of burning tokens now.

Usage:
  python3 scripts/fetch_metadata.py            # all missing folders
  python3 scripts/fetch_metadata.py --limit 20 # smoke test
  python3 scripts/fetch_metadata.py --ids sapiens,antifragile

Output: books/<id>/metadata.json + scripts/fetch_report.json
"""

import json
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

API = "https://openlibrary.org/search.json"
SLEEP = 0.25  # polite delay between requests
MIN_SCORE = 0.34  # below this -> review:true

STOP = {
    "the", "a", "an", "of", "and", "in", "on", "to", "for", "how",
    "is", "it", "its", "by", "with", "from", "at", "my",
}


def tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP]


def score(query_toks, title, authors):
    """Token-overlap score of query against title+authors (0..1)."""
    if not query_toks:
        return 0.0
    hay = set(tokens(title or "") + tokens(" ".join(authors or [])))
    hit = sum(1 for t in query_toks if t in hay)
    return hit / len(query_toks)


def query_variants(folder):
    """Full kebab query + progressively trimmed (author-suffixed folders)."""
    words = folder.split("-")
    variants = [" ".join(words)]
    for n in (2, 3, 4):
        if len(words) > n + 1:
            variants.append(" ".join(words[:-n]))
    return variants


def search(query):
    params = urllib.parse.urlencode({
        "q": query, "limit": 5,
        "fields": "key,title,author_name,first_publish_year,isbn,publisher",
    })
    req = urllib.request.Request(
        f"{API}?{params}", headers={"User-Agent": "BookPilot/2.0 (metadata backfill)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get("docs", [])


def pick(folder):
    """Return (doc, query_used, score) of best doc across variants."""
    best = (None, "", 0.0)
    for q in query_variants(folder):
        try:
            docs = search(q)
        except Exception as e:  # network hiccup -> treat as no result
            print(f"  ! query failed {q!r}: {e}", flush=True)
            continue
        time.sleep(SLEEP)
        qt = tokens(q)
        for d in docs:
            s = score(qt, d.get("title", ""), d.get("author_name", []))
            if s > best[2]:
                best = (d, q, s)
        if best[2] >= 0.8:
            break
    return best


def to_metadata(folder, doc, query, s):
    isbns = doc.get("isbn") or []
    isbn13 = next((i for i in isbns if len(i) == 13 and i.isdigit()), "")
    isbn10 = next((i for i in isbns if len(i) == 10), "")
    authors = doc.get("author_name") or []
    year = doc.get("first_publish_year")
    pubs = doc.get("publisher") or []
    return {
        "id": folder,
        "title": doc.get("title", ""),
        "author": authors[0] if authors else "",
        "authors": authors,
        "publisher": pubs[0] if pubs else "",
        "publishedDate": str(year) if year else "",
        "isbn13": isbn13,
        "isbn10": isbn10,
        "source": "openlibrary",
        "sourceKey": doc.get("key", ""),
        "sourceQuery": query,
        "sourceScore": round(s, 3),
        "review": s < MIN_SCORE,
    }


def main():
    args = sys.argv[1:]
    limit = None
    only = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if "--ids" in args:
        only = set(args[args.index("--ids") + 1].split(","))

    manifest_ids = {b["id"] for b in json.loads(MANIFEST.read_text())["books"]}
    folders = sorted(d.name for d in BOOKS_DIR.iterdir() if d.is_dir())
    missing = [f for f in folders if f not in manifest_ids]
    if only:
        missing = [f for f in missing if f in only]
    if limit:
        missing = missing[:limit]

    report = {"total": len(missing), "written": [], "skipped": [], "failed": []}
    if REPORT.exists():
        try:
            prev = json.loads(REPORT.read_text())
            report["written"] = prev.get("written", [])
            report["skipped"] = prev.get("skipped", [])
        except json.JSONDecodeError:
            pass
    done = {r["id"] for r in report["written"]} | set(report["skipped"])

    for i, folder in enumerate(missing, 1):
        if folder in done:
            continue
        meta_path = BOOKS_DIR / folder / "metadata.json"
        if meta_path.exists():
            report["skipped"].append(folder)
            continue
        print(f"[{i}/{len(missing)}] {folder}", flush=True)
        doc, query, s = pick(folder)
        if doc is None:
            report["failed"].append({"id": folder, "reason": "no results"})
            print("  -> NO RESULTS", flush=True)
            continue
        meta = to_metadata(folder, doc, query, s)
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        report["written"].append(
            {"id": folder, "title": meta["title"], "score": meta["sourceScore"],
             "review": meta["review"]})
        flag = " [REVIEW]" if meta["review"] else ""
        print(f"  -> {meta['title']} / {meta['author']} ({s:.2f}){flag}", flush=True)

    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    n_rev = sum(1 for r in report["written"] if r["review"])
    print(f"\nDone: {len(report['written'])} written "
          f"({n_rev} need review), {len(report['failed'])} failed, "
          f"{len(report['skipped'])} skipped.")
    if report["failed"]:
        print("Failed:", [f["id"] for f in report["failed"]])


if __name__ == "__main__":
    sys.exit(main())
