# BookPilot
BookPilot is a AI Powered Book Summary App. Where You can get 1000+ books summary for free, Chat With books, Take notes and BookMark Summaries.

Name convention Kebab-case, all lowercase

# Data Model

## book_manifest.json
```json
{
  "books": [
    {
      "id": "atomic-habits",
      "title": "Atomic Habits",
      "author": "James Clear",
      "publicationDate": "2018-10-16",
      "description": "An easy and proven way to build good habits and break bad ones.",
      "tags": ["Self-help", "Personal Development", "Psychology"],
      "coverImageUrl":"",
      "coverImagePath": "books/atomic-habits/cover.png",
      "summariesPath": { 
        "en": "books/atomic-habits/summary.md",
        "bn": "books/atomic-habits/summary-bn.md"
      },
      "isbn": "",
      "updatedAt": "2024-01-01T00:00:00.000Z",
      "version": "1.0.0"
    }
  ],
  "lastUpdated": "2024-01-08T12:00:00.000Z"
}

```

# Screenshots

<table>
  <tr>
    <td><img src="assets/images/auth-screen.png" width="100%"></td>
    <td><img src="assets/images/home-screen-1.png" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/images/home-screen-2.png" width="100%"></td>
    <td><img src="assets/images/book-summary.png" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/images/book-details-conversation.png" width="100%"></td>
    <td><img src="assets/images/chat-screen.png" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/images/chat-screen-keyboad.png" width="100%"></td>
    <td><img src="assets/images/saved-screen.png" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/images/settings-screen.png" width="100%"></td>
    <td><img src="assets/images/screen-20251025-170351.gif" width="100%"></td>
  </tr>
</table>


