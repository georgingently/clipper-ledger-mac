# Changelog

All notable changes to this project will be documented here.

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
