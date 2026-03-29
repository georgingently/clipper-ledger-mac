# GEORGIN Accounting

GEORGIN Accounting is a macOS desktop application for working with legacy GEORGIN accounting data stored in DBF files.

The motivation for this project is straightforward: preserve the speed and familiarity of an old CA-Clipper style accounting workflow while moving the actual day-to-day application experience onto macOS. Instead of asking users to remain on an old Windows/XP-era environment, this project rebuilds the workflow as a standalone Mac app with the same operational model, the same data source family, and a cleaner installation path.

## Why This Exists

The original GEORGIN workflow was tied to legacy Clipper-style software and DBF-based accounting tables. That model still has value:

- operators know the flow already
- the business data already exists in DBF tables
- the UI model is fast for bookkeeping work

What did not age well was the runtime environment. This project exists to bridge that gap:

- keep the accounting workflow recognizable
- keep compatibility with legacy DBF data
- distribute a native-feeling macOS app instead of a legacy Windows dependency

## Project Goals

- Preserve familiar Clipper-era accounting flows on macOS
- Read and write existing GEORGIN DBF data
- Package the app as a self-contained `.app` and DMG
- Let end users choose their own database folder at runtime
- Keep database files out of the repository and out of packaged source control history

## Current Application Scope

The desktop app includes:

- Entry modules for Cash Book, Bank Book, Sales, Purchase, and Journal
- Clipper-style navigation for Entries, Reports, Utilities, Files, Help, and Quit
- Legacy DOS/Clipper-inspired window framing to keep the on-screen workflow visually close to the original GEORGIN screens
- Report and master-data screens for key legacy tables
- A generic database table browser so uncovered DBF families remain reachable
- Workflow PDF export for sharing recreated legacy screen flows as a single document
- macOS app packaging and DMG release automation

## Repository Structure

- `georgin_app.py` — main PyQt desktop application
- `georgin_tui.py` — terminal/TUI reference implementation used as a legacy behavior guide
- `models/dbf_layer.py` — DBF read/write layer and data-folder detection
- `build_app.sh` — builds the macOS `.app` bundle and DMG
- `release_app.sh` — builds, tags, and publishes a GitHub release
- `docs/version.json` — GitHub Pages update feed used by the in-app updater
- `VERSION` — source of truth for the application version
- `UPDATES.md` — update strategy notes

## Database Handling

This repository does not include live accounting databases.

Important points:

- database files are not committed here
- the packaged app does not bundle a production database
- users select their own GEORGIN DBF folder on first launch
- if a valid data folder is already configured, the app reuses it

If you want to skip the folder prompt during local development, set `GEORGIN_DATA` before launching.

## Running Locally

Desktop app:

```bash
python3 georgin_app.py
```

or:

```bash
./run_app.sh
```

Legacy web helper:

```bash
./run.sh
```

Terminal/TUI reference:

```bash
./run_tui.sh
```

## Building the macOS App

Build the `.app` bundle and DMG:

```bash
bash build_app.sh
```

Build artifacts:

- `dist/GEORGIN Accounting.app`
- `dist/GEORGIN_Accounting_Installer.dmg`

The macOS bundle version is read from `VERSION`.

## Publishing Releases

To build the app, push the current branch, tag the current version, and publish a GitHub release:

```bash
bash release_app.sh
```

For the test updater, enable GitHub Pages for the public repository and publish from the `docs/` folder so `docs/version.json` is available at:

```text
https://georgingently.github.io/clipper-ledger-mac/version.json
```

## End User Installation

For end users on Apple Silicon Macs:

1. Open the DMG
2. Drag `GEORGIN Accounting.app` into `Applications`
3. Open the app
4. Select the GEORGIN data folder when prompted

No separate Python or dependency installation is required.

## Distribution Notes

- current packaged target is Apple Silicon (`ARM64`)
- the app is self-contained for end users
- because the app is not notarized yet, macOS may require first launch via right-click -> `Open`

## Documentation

- `CHANGELOG.md` — release history
- `CONTRIBUTING.md` — contribution and release guidance
- `UPDATES.md` — update-path options and constraints

## Status

This project is an active migration effort from a legacy Clipper-style accounting environment to a supported macOS desktop application. The intent is continuity of workflow, not novelty for its own sake.
