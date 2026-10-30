"""Bulk ISBN backfill via Open Library search (no key, generous limits).

For each manifest book lacking isbn: OL search -> local score
(title-token recall + author surname bonus) -> first ISBN-13.

Usage: python3 scripts/backfill_isbn_ol.py [--write] [--limit N]
Writes manifest + metadata.json only with --write.
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

SLEEP = 0.3
MIN_SCORE = 0.5
STOP = {
    "the", "a", "an", "of", "and", "in", "on", "to", "for", "how",
    "is", "it", "its", "by", "with", "from", "at", "my",
}
JUNK_PUB = re.compile(r"summary|instantread|cooltura|penzen|businessnews|review|study guide|keynotes", re.I)


def tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if t not in STOP]


def surname(author):
    parts = re.findall(r"[a-z]+", (author or "").lower())
    return parts[-1] if parts else ""


def search(query):
    params = urllib.parse.urlencode({
        "q": query, "limit": 8,
        "fields": "title,author_name,first_publish_year,isbn,publisher",
    })
    req = urllib.request.Request(
        f"https://openlibrary.org/search.json?{params}",
        headers={"User-Agent": "BookPilot/2.0 (isbn backfill)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get("docs", [])


def score_book(doc, want_title, want_author):
    qt = tokens(want_title)
    title = doc.get("title", "")
    authors = doc.get("author_name", [])
    hay = set(tokens(title))
    rec = sum(1 for t in qt if t in hay) / max(len(qt), 1)
    s = rec
    wa = surname(want_author)
    if wa and any(wa in a.lower() for a in authors):
        s += 0.25
    pubs = " ".join(doc.get("publisher", []) or [])
    if JUNK_PUB.search(pubs):
        s -= 0.5
    return round(min(s, 1.0), 3)


def best_isbn(doc):
    for i in doc.get("isbn", []) or []:
        if len(i) == 13 and i.isdigit():
            return i
    for i in doc.get("isbn", []) or []:
        if len(i) == 10:
            return i
    return ""


def main():
    write = "--write" in sys.argv
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None

    m = json.loads(MANIFEST.read_text())
    books = [b for b in m["books"] if not b.get("isbn")]
    if limit:
        books = books[:limit]
    print(f"missing isbn: {len(books)} (write={write})", flush=True)

    found, missing = {}, []
    for i, b in enumerate(books, 1):
        q = f"{b['title']} {b.get('author', '')}".strip()
        try:
            docs = search(q)
        except Exception as e:
            print(f"[{i}/{len(books)}] {b['id']} ! {e}", flush=True)
            missing.append(b["id"])
            continue
        time.sleep(SLEEP)
        cands = [(score_book(d, b["title"], b.get("author", "")), d) for d in docs]
        cands = [(s, d) for s, d in cands if s >= MIN_SCORE and best_isbn(d)]
        if not cands:
            print(f"[{i}/{len(books)}] {b['id']} -> NONE", flush=True)
            missing.append(b["id"])
            continue
        cands.sort(key=lambda x: -x[0])
        s, d = cands[0]
        isbn = best_isbn(d)
        found[b["id"]] = isbn
        print(f"[{i}/{len(books)}] {b['id']} -> {isbn} ({d.get('title', '')[:50]} {s})", flush=True)

    if write and found:
        idmap = {b["id"]: b for b in m["books"]}
        for bid, isbn in found.items():
            idmap[bid]["isbn"] = isbn
            mp = BOOKS_DIR / bid / "metadata.json"
            if mp.exists():
                try:
                    meta = json.loads(mp.read_text())
                    if isbn not in (meta.get("isbn13"), meta.get("isbn10")):
                        if not meta.get("isbn13"):
                            meta["isbn13"] = isbn
                        meta.setdefault("isbn_source", "openlibrary-bulk")
                        mp.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
                except (json.JSONDecodeError, OSError):
                    pass
        MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        print("manifest + metadata updated.")

    print(f"\nfound: {len(found)}, still missing: {len(missing)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    sys.exit(main())
