## Relevant Files

- `README.md` — public-facing project description; currently uses local absolute file links and does not fully explain the migration motivation.
- `models/dbf_layer.py` — data layer; previously defaulted to a developer-local sibling data folder if `GEORGIN_DATA` was unset.
- `run.sh` — local Flask launcher; currently hardcodes a local workstation DB path.
- `run_tui.sh` — local TUI launcher; currently hardcodes a local workstation DB path.
- `run_app.sh` — desktop launcher; already clean and launches without hardcoded data path.
- `build_app.sh` — packaging script; safe to keep public because it packages the app without bundling DB files.
- `release_app.sh` — release automation; safe to keep public, but should remain generic and not encode local release assumptions.
- `UPDATES.md` — update strategy notes; must stay deliberate and not imply insecure private-token shipping.
- `VERSION` — release/version source of truth.
- `.gitignore` — repo hygiene for generated outputs.

## Data Flow

1. On launch, `georgin_app.py` calls `_ensure_data_path()`.
2. `_ensure_data_path()` checks the active `dbf_layer.DATA_DIR`, then saved settings, then prompts the user to choose a folder.
3. `models/dbf_layer.py` currently initializes `DATA_DIR` from `GEORGIN_DATA` or a developer-local sibling data folder.
4. `build_app.sh` packages application code and resources, but not database files.
5. `run.sh` and `run_tui.sh` bypass folder selection by exporting a local path before starting the app.

## Constraints & Risks

- No tracked file should expose the author’s local DB path once the repository is public.
- No tracked file should imply the database is bundled with the app or stored in the repo.
- Public repo docs should read like an intentional migration project, not an ad hoc prototype.
- Changing DB fallback behavior must not break the first-launch folder selection flow in the app.
- Making the repo public must only happen after local-path leaks are removed and docs are upgraded.
- The repo is already GitHub-backed, so visibility changes and release metadata updates must preserve release continuity.

## Open Questions

None.
