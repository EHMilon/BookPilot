"""Build manifest entries for folders that have metadata.json + summary.md
but no manifest entry. Dry-run by default; --write to apply.

Entry rules: title/author/date/isbn/description from metadata.json,
tags [] (app shows under Others until classified), coverImagePath '',
version 2.0.0, updatedAt today. Folders without summary.md are skipped
and reported (stray folders, e.g. no-summary 'breathe').
"""

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "book_manifest.json"
BOOKS_DIR = ROOT / "books"


def norm_date(s):
    s = (s or "").strip()
    if len(s) == 4 and s.isdigit():
        return f"{s}-01-01"
    if len(s) == 7 and s[4] == "-":
        return f"{s}-01"
    return s or "2000-01-01"


def build(folder, m):
    return {
        "id": folder,
        "title": m.get("title", ""),
        "author": m.get("author", ""),
        "description": m.get("description", ""),
        "language": "en",
        "coverImagePath": "",
        "summariesPath": f"books/{folder}/summary.md",
        "summaryFileName": "summary.md",
        "publicationDate": norm_date(m.get("publishedDate", "")),
        "isbn": m.get("isbn13", "") or m.get("isbn10", ""),
        "pages": m.get("pageCount", 0) or 0,
        "tags": [],
        "updatedAt": datetime.date.today().isoformat(),
        "version": "2.0.0",
    }


def main():
    write = "--write" in sys.argv
    manifest = json.loads(MANIFEST.read_text())
    have = {b["id"] for b in manifest["books"]}
    new, skipped, no_desc = [], [], []
    for d in sorted(BOOKS_DIR.iterdir()):
        if not d.is_dir() or d.name in have:
            continue
        mp = d / "metadata.json"
        sm = d / "summary.md"
        if not mp.exists():
            skipped.append((d.name, "no metadata.json"))
            continue
        if not sm.exists():
            skipped.append((d.name, "no summary.md"))
            continue
        m = json.loads(mp.read_text())
        if not m.get("title") or not m.get("author"):
            skipped.append((d.name, "metadata missing title/author"))
            continue
        e = build(d.name, m)
        if not e["description"]:
            no_desc.append(d.name)
        new.append(e)

    print(f"new entries: {len(new)}, skipped: {len(skipped)}, empty description: {len(no_desc)}")
    for n, r in skipped:
        print(f"  SKIP {n}: {r}")
    if no_desc:
        print(f"  NO-DESC ({len(no_desc)}): {no_desc[:30]}")

    if write and new:
        manifest["books"].extend(new)
        manifest["lastUpdated"] = datetime.date.today().isoformat()
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {len(new)} entries to manifest.")
    elif not write:
        print("dry-run only; pass --write to apply.")


if __name__ == "__main__":
    main()
