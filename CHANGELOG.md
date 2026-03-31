# Changelog

All notable changes to this project will be documented here.

## [0.1.4] - 2026-03-31

### Changed

- Improved DMG auto-install handling by removing quarantine before mount and surfacing mount errors
- Restored keyboard-first TUI navigation for menus and table cursor movement

### Notes

- Release includes updated in-app feed metadata for automatic update checks

## [0.1.0] - 2026-03-28

### Added

- Initial public project documentation
- Versioned release workflow via `VERSION` and `release_app.sh`
- Packaged macOS `.app` and DMG release process

### Changed

- Desktop app migrated toward a Clipper-style single-window macOS experience
- Database folder selection made user-driven instead of relying on a developer-local path
- Public repository hygiene improved by removing hardcoded local DB path launch defaults

### Notes

- Legacy GEORGIN DBF data is intentionally not committed to this repository
- End users select their own database folder at runtime
