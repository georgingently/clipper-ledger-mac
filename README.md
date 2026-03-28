# GEORGIN Accounting

GEORGIN Accounting is a macOS desktop application for working with legacy GEORGIN DBF accounting data. It is packaged as a self-contained `.app` and DMG for distribution to end users on Apple Silicon Macs.

## What It Does

- Opens GEORGIN DBF data by letting the user choose the database folder on first launch
- Provides Clipper-style accounting screens inside a single main application window
- Supports core entry flows such as Cash Book, Bank Book, Sales, Purchase, and Journal
- Includes reports, master data screens, utilities, and a generic database table browser
- Builds into a distributable macOS app bundle and DMG installer

## Project Layout

- [`georgin_app.py`](/Volumes/Workspace/Projects/Clipper/GEORGIN_MAC/georgin_app.py): main PyQt desktop application
- [`models/dbf_layer.py`](/Volumes/Workspace/Projects/Clipper/GEORGIN_MAC/models/dbf_layer.py): DBF read/write layer
- [`georgin_tui.py`](/Volumes/Workspace/Projects/Clipper/GEORGIN_MAC/georgin_tui.py): old Clipper-style reference implementation
- [`build_app.sh`](/Volumes/Workspace/Projects/Clipper/GEORGIN_MAC/build_app.sh): macOS app + DMG build script

## Running Locally

From the project directory:

```bash
python3 georgin_app.py
```

Or:

```bash
./run_app.sh
```

## Building the macOS App

Build the `.app` bundle and DMG:

```bash
bash build_app.sh
```

Artifacts are created in:

- `dist/GEORGIN Accounting.app`
- `dist/GEORGIN_Accounting_Installer.dmg`

## End User Installation

Send the DMG to the user. They only need to:

1. Open the DMG
2. Drag `GEORGIN Accounting.app` to `Applications`
3. Open the app
4. Select their GEORGIN database folder

No separate Python or dependency installation is required.

## Notes

- Current packaged build target is Apple Silicon (`ARM64`)
- Because the app is not notarized, macOS may require first launch via right-click -> `Open`
- Database files are not stored in this repository; the user selects them at runtime
