# BookPilot
BookPilot is a AI Powered Book Summary App. Where You can get 1000+ books summary for free, Chat With books, Take notes and BookMark Summaries.

Name convention Kebab-case, all lowercase

# Data Model

## book_manifest.json
```json
{
  "lastUpdated": "2026-05-08T17:00:00.000000Z",
  "tags": ["Self-Help", "Psychology", "... (27 curated)"],
  "features": ["atomic-habits", "deep-work", "..."],
  "books": [
    {
      "id": "12-rules-for-life",
      "title": "12 Rules for Life",
      "author": "Jordan Peterson",
      "publicationDate": "2018-01-23",
      "description": "An antidote to chaos.",
      "tags": [
        "Philosophy",
        "Psychology",
        "Self-Help"
      ],
      "coverImagePath": "books/12-rules-for-life/cover.png", // leave it blank
      "summariesPath": {
        "en": "books/12-rules-for-life/summary.md"
      },
      "isbn": "", //Fill it or leave it blank
      "updatedAt": "2026-05-04T04:31:10.125840Z",
      "version": "2.0.0"
    }
  ]
}
```

Rules:
- `tags` (top-level) is the allowlist: 27 curated categories. Pick from it, never invent new strings (exact case-sensitive match — `Self-Help`, not `Self-help`).
- `Others` is NOT in `tags` — it is app-only. Books whose tags match nothing render under an app-appended `Others` section last.
- `features` (top-level) is the featured-shelf: array of book `id`s. Add/remove ids here, never use a `feature` tag on books.
- `books[].tags`: 1–3 entries from the allowlist.
- Validate before commit: `python3 scripts/validate_manifest.py`. After bulk edits: `python3 scripts/normalize_tags.py` (dedupes by `id`, remaps old tags, rebuilds `features`).

When new books added update the book_list.md




