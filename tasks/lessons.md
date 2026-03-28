# Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.
- For repositories that work with DBF datasets, `.gitignore` must block the full DBF/memo/index file family so accidental local data drops never get pushed.
