# Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.
- For repositories that work with DBF datasets, `.gitignore` must block the full DBF/memo/index file family so accidental local data drops never get pushed.
- In packaged PyQt apps, unhandled Python exceptions inside Qt slots can abort the entire app, so menu/event wiring must avoid duplicate dispatch and constructor paths used by slots must be import-safe.
