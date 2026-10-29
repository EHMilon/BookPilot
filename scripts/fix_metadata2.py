"""Fix pass 2: free-text query (title + author), verify locally.

Pass 1 failed because unquoted multi-word intitle:/inauthor: operators
return empty. Free text + local scoring worked in the enrich pass.
Filters junk editions (summaries, young-adult adaptations, study guides).

Usage: GOOGLE_BOOKS_KEY=... python3 scripts/fix_metadata2.py [--limit N]
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
BOOKS_DIR = ROOT / "books"

JUNK = re.compile(r"young adult|kids|junior|adapted|summary|summaries|review keypoints|study guide|cooltura|instantread|penzen|businessnews|namaskar|decarbonizing|thesis|dissertation", re.I)


def surname(a):
    a = re.split(r"[&,/]| and ", a)[0].strip()
    parts = a.split()
    return parts[-1].lower().strip(" -.") if parts else ""


def toks(s):
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower())
            if t not in {"the", "a", "an", "of", "and", "in", "on", "to"}]


def title_overlap(qt, title):
    qt, ht = set(qt), set(toks(title))
    return len(qt & ht) / max(len(qt), 1)


def search(q, key):
    params = urllib.parse.urlencode(
        {"q": q, "maxResults": 5, "printType": "books", "key": key})
    req = urllib.request.Request(
        f"https://www.googleapis.com/books/v1/volumes?{params}",
        headers={"User-Agent": "BookPilot/2.0 (metadata fix2)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get("items", [])


def clean_desc(raw, limit=320):
    text = re.sub(r"<[^>]+>", " ", html.unescape(raw or "")).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = cut.rfind(". ")
    return cut[:dot + 1] if dot > 120 else cut.rstrip() + "…"


def build(folder, item, old):
    vi = item.get("volumeInfo", {})
    authors = vi.get("authors", []) or []
    ids = {d.get("type"): d.get("identifier", "")
           for d in vi.get("industryIdentifiers", [])}
    return {
        "id": folder,
        "title": vi.get("title", "") or old.get("title", ""),
        "author": authors[0] if authors else old.get("author", ""),
        "authors": authors,
        "publisher": vi.get("publisher", "") or old.get("publisher", ""),
        "publishedDate": vi.get("publishedDate", "") or old.get("publishedDate", ""),
        "isbn13": ids.get("ISBN_13", "") or old.get("isbn13", ""),
        "isbn10": ids.get("ISBN_10", "") or old.get("isbn10", ""),
        "pageCount": vi.get("pageCount", 0) or old.get("pageCount", 0),
        "googleCategories": vi.get("categories", []) or old.get("googleCategories", []),
        "description": old.get("description", "") or clean_desc(vi.get("description", "")),
        "source": "google-books-fix2",
        "sourceId": item.get("id", ""),
        "sourceQuery": "",
        "sourceScore": 1.0,
        "review": False,
    }


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fix_metadata", ROOT / "scripts" / "fix_metadata.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    FIX = mod.FIX  # noqa
    key = os.environ.get("GOOGLE_BOOKS_KEY", "")
    if not key:
        print("Set GOOGLE_BOOKS_KEY env var.")
        return 1
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None

    todo = [f for f, (_, a) in FIX.items() if a]  # only author-hinted ones
    done = set()
    for f in todo:
        mp = BOOKS_DIR / f / "metadata.json"
        if mp.exists():
            m = json.loads(mp.read_text())
            if m.get("source") in ("google-books-fix2",) and not m.get("review"):
                done.add(f)
    todo = [f for f in todo if f not in done]
    if limit:
        todo = todo[:limit]

    fixed, need_eye = [], []
    for i, folder in enumerate(todo, 1):
        title_q, author_q = FIX[folder]
        mp = BOOKS_DIR / folder / "metadata.json"
        old = json.loads(mp.read_text()) if mp.exists() else {}
        q = f"{title_q} {author_q}"
        print(f"[{i}/{len(todo)}] {q}", flush=True)
        try:
            items = search(q, key)
        except Exception as e:
            print(f"  ! error: {e}", flush=True)
            need_eye.append(folder)
            continue
        time.sleep(0.15)
        want = surname(author_q)
        qt = toks(title_q)
        scored = []
        for item in items:
            vi = item.get("volumeInfo", {})
            t, authors = vi.get("title", ""), vi.get("authors", []) or []
            pub = vi.get("publisher", "")
            if JUNK.search(f"{t} {pub}"):
                continue
            surnames = [surname(a) for a in authors]
            ok = any(want in s or s in want for s in surnames if s)
            if not ok:
                continue
            scored.append((title_overlap(qt, t), item))
        if not scored:
            print("  -> NO VERIFIED MATCH", flush=True)
            need_eye.append(folder)
            continue
        scored.sort(key=lambda x: -x[0])
        item = scored[0][1]
        meta = build(folder, item, old)
        meta["sourceQuery"] = q
        mp.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        fixed.append(folder)
        print(f"  -> {meta['title']} / {meta['author']}", flush=True)

    print(f"\nDone: {len(fixed)} fixed, {len(need_eye)} still need eye")
    if need_eye:
        print(need_eye)


if __name__ == "__main__":
    sys.exit(main())
