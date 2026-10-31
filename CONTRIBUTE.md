# Contributing to BookPilot

<!--
  File: CONTRIBUTE.md
  Purpose: Contributor guide for the BookPilot summary library.
  Scope: Writing rules, folder syntax, manifest contract, PR workflow.
  Rules: Original words only. Never paste book text. Keep slugs kebab-case.
         validate_manifest.py must pass before a PR is opened.
-->

Pull requests are welcome — new book summaries, translations, corrections,
better tags. You do not need permission to start; open a PR and a
maintainer will review it.

## Ground rules

1. Write in your own words. Summaries are original synopses of key
   ideas, not excerpts. Never copy sentences from the book, from
   publishers, or from other summary sites.
2. No spoilers-as-content for fiction beyond what a back cover reveals.
   Focus on themes and takeaways.
3. One book, one folder. Folder names are kebab-case, all lowercase:
   `books/the-power-of-now/`, never `The_Power of Now`.
4. English first, your language next. A book read in English can carry
   its summary in Bangla or any language you speak — that is the point
   of this library.

## Folder layout

```text
books/<book-slug>/
  summary.md        # English summary, required for new books
  summary-bn.md     # Bangla (or future summary-<lang>.md), optional
  cover.png         # optional, must be freely usable or your own
  metadata.json     # optional, source metadata only
```

A good `summary.md` is 500–1500 words: the hook, 3–7 key ideas with a
line or two of why each matters, and a closing takeaway. Markdown only,
no HTML.

## Manifest entry

Every book needs an entry in the index. Add it to
`manifest/book_manifest_en.json` (and the matching language manifest
when translating):

```json
{
  "id": "the-power-of-now",
  "title": "The Power of Now",
  "author": "Eckhart Tolle",
  "publicationDate": "1997-01-01",
  "description": "One clear sentence on what the book is about.",
  "tags": ["Mindfulness & Spirituality", "Self-Help"],
  "coverImagePath": "books/the-power-of-now/cover.png",
  "summariesPath": { "en": "books/the-power-of-now/summary.md" },
  "isbn": "",
  "updatedAt": "2026-10-31T00:00:00Z",
  "version": "2.0.0"
}
```

Contract, enforced by `scripts/validate_manifest.py`:

- `id` matches the folder slug, unique across the manifest.
- `tags`: 1–3 entries, exact case-sensitive match against the
  top-level allowlist of 27 categories. Never invent a tag; never store
  `Others` or `feature`.
- `features` (top-level) is the featured shelf: an array of book ids.
  Add or remove ids there; do not use tags for featuring.
- `isbn`, `coverImagePath` may be empty strings when unknown. Leave
  them blank rather than guessing.
- `updatedAt` is UTC ISO-8601. Bump it on every content change.

## Before you open a PR

```bash
python3 scripts/validate_manifest.py
```

The script must print `OK: manifest contract valid.` If it fails, fix
the reported ids or tags and re-run. After bulk tag edits, run
`python3 scripts/normalize_tags.py` first, then validate.

Keep PRs small: one book per PR when adding content, one concern per PR
when editing tags or metadata. Describe what you read and what you
changed in the PR body.

## Translations

To add a Bangla summary for an existing book, create
`books/<slug>/summary-bn.md` and extend that book's `summariesPath`
with `"bn": "books/<slug>/summary-bn.md"`. Translate meaning, not
word-for-word — adapt examples so they land for your readers.

## License note

By contributing you agree your work is released under the repository's
CC BY-NC-SA 4.0 license: free for non-commercial sharing with credit,
commercial use only with the author's permission. Do not submit text
you do not have the right to license this way.
