# BookPilot
BookPilot is a AI Powered Book Summary App. Where You can get 1000+ books summary for free, Chat With books, Take notes and BookMark Summaries.

Name convention Kebab-case, all lowercase

# Data Model

## book_manifest.json
```json
{
      "id": "12-rules-for-life",
      "title": "12 Rules for Life",
      "author": "Jordan Peterson",
      "publicationDate": "2018-01-23",
      "description": "An antidote to chaos.",
      "tags": [
        "Philosophy",
        "Psychology",
        "Self-help"
      ],
      "coverImagePath": "books/12-rules-for-life/cover.png", // leave it blank
      "summariesPath": {
        "en": "books/12-rules-for-life/summary.md"
      },
      "isbn": "", //Fill it or leave it blank
      "updatedAt": "2026-05-04T04:31:10.125840Z",
      "version": "2.0.0"
    },
```

When new books added update the book_list.md




