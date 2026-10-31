# BookPilot

<!--
  File: README.md
  Purpose: Project overview for the BookPilot open book-summary library.
  Scope: What this repo is, how content is organised, how the app uses it,
         and where to go next (contribute, license, takedown, privacy).
  Rules: Keep marketing claims out. Do not quote book counts as promises;
         manifests are the source of truth and change with every merge.
-->

BookPilot is an open community library of book summaries. Read the
essence of a book in minutes, in your own language. If a book exists
in English, its summary can live in yours — Bangla, English, or
whatever your community reads next.

## What this is

An independent, open-source content project: a collection of original
book summaries, maintained by volunteers, stored as plain Markdown so
anyone can read, fork, and improve it.

The BookPilot app reads from this repository. This repo is the library;
the app is one reader built on top of it.

## How content is organised

```text
books/<book-slug>/
  summary.md        # English summary (required)
  summary-bn.md     # Bangla summary (optional, growing)
  cover.png         # cover art (optional)
  metadata.json     # fetched source metadata (optional)
manifest/book_manifest_en.json  # English index (source of truth)
manifest/book_manifest_bn.json  # Bangla index (in progress)
book_manifest.json              # legacy combined index
```

Each book folder uses a kebab-case slug: `atomic-habits`,
`the-power-of-now`. Summaries are original synopses written by
contributors — key ideas in your own words, never copied text from the
book.

The manifest is the machine-readable index (id, title, author, tags,
paths). The BookPilot app renders shelves, search, and featured books
from it.

## Tags and featured shelf

Tags come from a fixed allowlist of 27 curated categories
(`Self-Help`, `Psychology`, `Philosophy`, …). Each book carries 1–3
tags. There is no `Others` or `feature` tag in storage — the app appends
an `Others` section at render time, and the manifest's top-level
`features` array drives the featured shelf by book id.

## Use it

Clone or fork the repo, or browse `books/` directly on GitHub. Every
summary is a Markdown file — no build step, no account, no paywall.

```bash
git clone https://github.com/EHMilon/BookPilot.git
ls books/atomic-habits/
```

Validate the manifest before opening a pull request:

```bash
python3 scripts/validate_manifest.py
```

## Contribute

Everyone is welcome. Add a missing summary, translate one into your
language, fix a mistake, improve a tag. Start with
[CONTRIBUTE.md](CONTRIBUTE.md) — it covers folder syntax, writing
rules, and the manifest contract.

## License

All content in this repository — summaries, translations, metadata,
manifests, images, and scripts — is licensed under
**Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International (CC BY-NC-SA 4.0)**. See [LICENSE](LICENSE).

That means: free for personal use, study, and sharing, with credit,
under the same terms. Commercial use requires prior written permission:
eh.milon.dev@gmail.com

## Rights and privacy

Summaries here are original transformative synopses, not reproductions
of book text. If you hold rights to a work and believe content here
oversteps, see [DMCA-Policy.md](DMCA-Policy.md) — valid requests are
reviewed and the material removed, normally within 14 days.

App data handling is described in [privacy_policy.md](privacy_policy.md).

## Contact

- Issues and pull requests: https://github.com/EHMilon/BookPilot
- Email: eh.milon.dev@gmail.com
