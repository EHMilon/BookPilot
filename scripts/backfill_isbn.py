"""Backfill missing ISBNs in book_manifest.json (and metadata.json where present).

For each manifest book with empty isbn:
  1. Google Books (env GOOGLE_BOOKS_KEY): intitle+inauthor query, best
     non-junk match -> ISBN_13 (fallback ISBN_10).
  2. Fallback Open Library: search -> work key -> editions.json ->
     first English-language edition with an ISBN.
Report-only by default; --write applies to manifest + metadata files.

Usage: GOOGLE_BOOKS_KEY=... python3 scripts/backfill_isbn.py [--write] [--limit N]
"""

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

SLEEP = float(os.environ.get("ISBN_SLEEP", "0.5"))
JUNK = re.compile(r"summary|summaries|review|study guide|cooltura|instantread|"
                  r"businessnews|penzen|young adult|cliff|monarch|bookmate",
                  re.I)

STOPW = {"the", "a", "an", "of", "and", "in", "on", "to", "for",
         "how", "is", "it", "its", "by", "with", "from", "my"}


def qtokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower())
            if t not in STOPW]


def match_score(title, author, vi):
    tq, aq = set(qtokens(title)), set(qtokens(author))
    tt = set(qtokens(vi.get("title", "")))
    at = set(qtokens(" ".join(vi.get("authors", []) or [])))
    if not tq:
        return 0.0
    s = len(tq & tt) / len(tq)
    if aq and (aq & at):
        s += 0.5
    return s


def gvolumes(query, key):
    params = urllib.parse.urlencode(
        {"q": query, "maxResults": 5, "printType": "books", "key": key})
    req = urllib.request.Request(
        f"https://www.googleapis.com/books/v1/volumes?{params}",
        headers={"User-Agent": "BookPilot/2.0 (isbn backfill)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get("items", [])


def ol_edition_isbn(title, author):
    """Via Open Library search -> work editions -> first English ISBN."""
    q = urllib.parse.urlencode({"q": f"{title} {author}", "limit": 3,
                                "fields": "key,title,author_name"})
    req = urllib.request.Request(
        f"https://openlibrary.org/search.json?{q}",
        headers={"User-Agent": "BookPilot/2.0 (isbn backfill)"})
    docs = json.load(urllib.request.urlopen(req, timeout=25)).get("docs", [])
    for d in docs:
        key = d.get("key", "")
        if not key.startswith("/works/"):
            continue
        try:
            ereq = urllib.request.Request(
                f"https://openlibrary.org{key}/editions.json?limit=50",
                headers={"User-Agent": "BookPilot/2.0 (isbn backfill)"})
            eds = json.load(urllib.request.urlopen(ereq, timeout=25)).get("entries", [])
        except Exception:
            continue
        time.sleep(SLEEP)
        for e in eds:
            langs = [l.get("key", "") for l in e.get("languages", [])]
            if langs and "/languages/eng" not in langs:
                continue
            for i in e.get("isbn_13", []) + e.get("isbn_10", []):
                if i:
                    return i
    return ""


def main():
    key = os.environ.get("GOOGLE_BOOKS_KEY", "")
    if not key:
        print("Set GOOGLE_BOOKS_KEY env var.")
        return 1
    args = sys.argv[1:]
    write = "--write" in args
    skip_ol = "--skip-ol" in args
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    offset = int(args[args.index("--offset") + 1]) if "--offset" in args else 0
    out = args[args.index("--out") + 1] if "--out" in args else ""

    m = json.loads(MANIFEST.read_text())
    targets = [b for b in m["books"] if not b.get("isbn")]
    if offset:
        targets = targets[offset:]
    if limit:
        targets = targets[:limit]
    print(f"missing isbn: {len(targets)} (write={write})")

    found, still = {}, []
    for i, b in enumerate(targets, 1):
        bid, title, author = b["id"], b["title"], b.get("author", "")
        isbn = ""
        try:
            items = gvolumes(f"{title} {author}".strip(), key)

            def rank(item):
                vi = item.get("volumeInfo", {})
                ids = {d.get("type"): d.get("identifier", "")
                       for d in vi.get("industryIdentifiers", [])}
                junk = bool(JUNK.search(" ".join(
                    vi.get("authors", []) + [vi.get("publisher", "")])))
                return (junk,
                        -match_score(title, author, vi),
                        vi.get("language", "") != "en",
                        not ids.get("ISBN_13", ""),
                        not (ids.get("ISBN_13", "") or ids.get("ISBN_10", "")))
                vi = item.get("volumeInfo", {})
                ids = {d.get("type"): d.get("identifier", "")
                       for d in vi.get("industryIdentifiers", [])}
                junk = bool(JUNK.search(" ".join(
                    vi.get("authors", []) + [vi.get("publisher", "")])))
                return (junk,
                        vi.get("language", "") != "en",
                        not ids.get("ISBN_13", ""),
                        not (ids.get("ISBN_13", "") or ids.get("ISBN_10", "")))
            for item in sorted(items, key=rank):
                vi = item.get("volumeInfo", {})
                if match_score(title, author, vi) < 0.5:
                    continue
                ids = {d.get("type"): d.get("identifier", "")
                       for d in vi.get("industryIdentifiers", [])}
                isbn = ids.get("ISBN_13", "") or ids.get("ISBN_10", "")
                if isbn:
                    break
            time.sleep(SLEEP)
        except Exception as e:
            print(f"  ! google err {bid}: {e}", flush=True)
        if not isbn and not skip_ol:
            try:
                isbn = ol_edition_isbn(title, author)
            except Exception as e:
                print(f"  ! ol err {bid}: {e}", flush=True)
        if isbn:
            found[bid] = isbn
            print(f"[{i}/{len(targets)}] {bid} -> {isbn}", flush=True)
        else:
            still.append(bid)
            print(f"[{i}/{len(targets)}] {bid} -> NONE", flush=True)

    print(f"\nfound: {len(found)}, still missing: {len(still)}")
    if still:
        print("missing:", ", ".join(still))
    if out:
        Path(out).write_text(json.dumps(
            {"found": found, "still": still}, indent=2))
        print(f"shard results -> {out}")
        return 0
    if write and found:
        for b in m["books"]:
            if b["id"] in found:
                b["isbn"] = found[b["id"]]
                mp = BOOKS_DIR / b["id"] / "metadata.json"
                if mp.exists():
                    try:
                        meta = json.loads(mp.read_text())
                        if len(found[b["id"]]) == 13:
                            meta["isbn13"] = found[b["id"]]
                        else:
                            meta["isbn10"] = found[b["id"]]
                        mp.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
                    except Exception as e:
                        print(f"  ! meta write {b['id']}: {e}")
        from datetime import datetime, timezone
        m["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        print("manifest + metadata updated.")


if __name__ == "__main__":
    sys.exit(main())
