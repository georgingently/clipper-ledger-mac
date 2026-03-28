# Contributing

## Project Intent

This project is a migration of a legacy GEORGIN accounting workflow from a Clipper-style environment to a macOS desktop application. Contributions should preserve that intent:

- keep workflows recognizable to existing operators
- keep DBF compatibility intact
- avoid unnecessary visual or architectural churn

## Ground Rules

- Do not commit production database files
- Do not hardcode developer-local filesystem paths into tracked files
- Keep end-user installation self-contained
- Prefer minimal, reversible changes over broad rewrites

## Development Setup

Run the desktop app:

```bash
python3 georgin_app.py
```

Build the macOS app:

```bash
bash build_app.sh
```

Publish a release:

```bash
bash release_app.sh
```

## Data Handling

This repository does not track live GEORGIN DBF data.

For local development:

- set `GEORGIN_DATA` if you want to point to a specific local dataset
- otherwise let the application ask for the database folder

## Release Expectations

Before publishing a release:

1. Update `VERSION`
2. Update `CHANGELOG.md`
3. Verify the app still builds
4. Confirm no local database path or private machine detail was added to tracked files

## Pull Requests

Pull requests should explain:

- what changed
- why the change was needed
- how it was verified

Keep PRs narrow and easy to review.
