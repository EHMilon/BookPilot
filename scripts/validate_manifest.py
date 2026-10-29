"""Validate book_manifest.json tag allowlist contract.

- top-level `tags`: 27 curated entries, unique, no `Others` (app-only)
- top-level `features`: unique ids, each resolves to a book
- every books[].tags entry is a member of top-level `tags`
- no `feature` pseudo-tag remains, no duplicate book ids

Usage: python3 scripts/validate_manifest.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "book_manifest.json"

EXPECTED_TAGS = [
    "Self-Help",
    "Psychology",
    "Philosophy",
    "Mindfulness & Spirituality",
    "Neuroscience & Brain",
    "Mental Health & Wellbeing",
    "Health & Nutrition",
    "Productivity & Habits",
    "Business & Leadership",
    "Finance & Wealth",
    "Communication & Relationships",
    "Creativity & Art",
    "Education & Learning",
    "Science & Technology",
    "Memoir & Biography",
    "History & Classics",
    "Nature & Environment",
    "Travel & Adventure",
    "Culture & Society",
    "Parenting & Family",
    "Happiness & Resilience",
    "Essays & Poetry",
    "Lifestyle & Minimalism",
    "Fiction & Literature",
    "Fantasy & Sci-Fi",
    "Mystery & Thriller",
    "Tales & Fables",
]

errors = []


def fail(msg):
    errors.append(msg)


def main():
    data = json.loads(MANIFEST.read_text())
    tags = data.get("tags")
    features = data.get("features")
    books = data.get("books")

    if tags != EXPECTED_TAGS:
        fail(f"top-level tags mismatch: got {len(tags) if isinstance(tags, list) else tags!r}, want {len(EXPECTED_TAGS)} curated")
        if isinstance(tags, list):
            missing = [t for t in EXPECTED_TAGS if t not in tags]
            extra = [t for t in tags if t not in EXPECTED_TAGS]
            if missing:
                fail(f"  missing: {missing}")
            if extra:
                fail(f"  extra (incl. forbidden Others?): {extra}")
    if isinstance(tags, list):
        if len(set(tags)) != len(tags):
            fail("top-level tags not unique")
        if any(t.strip().casefold() == "others" for t in tags):
            fail("`Others` must NOT be stored in manifest tags (app-only)")
        if any(t.strip().casefold() == "feature" for t in tags):
            fail("`feature` must NOT be a category")

    if not isinstance(features, list):
        fail("top-level features missing/not a list")
        features = []
    ids = [b.get("id") for b in books] if isinstance(books, list) else []
    if len(set(ids)) != len(ids):
        dupes = [k for k, v in Counter(ids).items() if v > 1]
        fail(f"duplicate book ids: {dupes}")
    idset = set(ids)
    if len(set(features)) != len(features):
        fail("features not unique")
    for fid in features:
        if fid not in idset:
            fail(f"feature id has no book: {fid!r}")

    counts = Counter()
    empty = []
    for b in books or []:
        for t in b.get("tags", []):
            if not isinstance(t, str):
                fail(f"{b.get('id')}: non-string tag {t!r}")
                continue
            if t.strip().casefold() in ("feature", "others"):
                fail(f"{b.get('id')}: forbidden stored tag {t!r}")
            if t not in (tags or []):
                fail(f"{b.get('id')}: tag {t!r} not in allowlist")
            counts[t] += 1
        if not b.get("tags"):
            empty.append(b.get("id"))

    print(f"books: {len(books or [])}")
    print(f"tags: {len(tags) if isinstance(tags, list) else tags}")
    print(f"features: {len(features)}")
    print(f"books falling to app Others: {len(empty)}")
    for tag in tags or []:
        print(f"  {counts.get(tag, 0):4d}  {tag}")
    thin = [t for t in tags or [] if counts.get(t, 0) < 3]
    if thin:
        print(f"sections with <3 books: {thin}")
    if empty:
        print(f"Others-bound ids (first 20): {empty[:20]}")

    if errors:
        print("\nFAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK: manifest contract valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
