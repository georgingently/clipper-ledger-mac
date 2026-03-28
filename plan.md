## Scope

Prepare the repository for public visibility without exposing any local database path or implying that DBF data is tracked in source control. Upgrade the repository presentation so it clearly explains the project as a deliberate migration from a legacy Clipper accounting workflow to a native-feeling macOS desktop app.

## Files To Modify

- `README.md`
- `models/dbf_layer.py`
- `run.sh`
- `run_tui.sh`
- `.gitignore`
- `CHANGELOG.md` (new)
- `CONTRIBUTING.md` (new)
- `tasks/todo.md` (new)
- `tasks/lessons.md` (new)

## Design Decisions

1. Remove hardcoded local DB defaults from tracked launch scripts and data initialization.
Tradeoff: local convenience is reduced, but public safety and portability improve.

2. Keep runtime DB selection user-driven rather than committing sample/local paths.
Tradeoff: first launch requires a folder selection step, but the repository remains clean and reusable.

3. Rewrite `README.md` around project motivation, architecture, install flow, and release flow.
Tradeoff: more documentation maintenance, but the repo becomes credible and understandable to outside users.

4. Add `CHANGELOG.md` and `CONTRIBUTING.md` for repository completeness.
Tradeoff: slight maintenance overhead, but it removes the “unfinished” feel and sets contribution expectations.

5. Make the GitHub repository public only after verification passes.
Tradeoff: one extra final step, but it avoids exposing incomplete cleanup.

## Code-Level Approach

- Change `models/dbf_layer.py` so default `DATA_DIR` comes only from `GEORGIN_DATA` or the current working context, not a sibling local workstation folder.
- Update `run.sh` and `run_tui.sh` to launch without exporting a developer-specific DB path.
- Rewrite `README.md` with:
  - project motivation
  - legacy-to-macOS migration story
  - architecture summary
  - install and build instructions
  - explicit statement that DB data is not bundled or committed
- Add `CHANGELOG.md` for current release history.
- Add `CONTRIBUTING.md` with contribution/release guidance.
- Add `tasks/todo.md` and `tasks/lessons.md` per workflow requirements.
- Use `gh repo edit --visibility public` only after validation.

## Success Criteria

- No tracked file contains a developer-local absolute database path.
- No tracked launcher exports a local DB path.
- Default DB discovery does not assume a sibling local data folder in the repo.
- README clearly explains the project motivation and distribution model.
- Repository contains `README.md`, `CHANGELOG.md`, and `CONTRIBUTING.md`.
- Repo is made public after code/docs verification.

## Test Strategy

- Search-based verification that no local absolute DB path remains in tracked files.
- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- `bash build_app.sh`
- Verify built app metadata and packaging still succeed.
- Confirm git status clean before public visibility change and before PR flow.

## Assumptions

- Making the repository public is desired immediately after documentation and path cleanup.
- Database files themselves are outside the repository and should remain so.
- The user still wants current GitHub releases and repo history preserved.

## Rollback Strategy

- If cleanup breaks launch behavior, revert the specific script/data-layer changes on the branch before merge.
- If public visibility introduces an unexpected issue, set the repository back to private immediately and continue fixes on the same branch.

## Security Impact

- Positive impact: removes exposure of local workstation paths and avoids publishing implicit private filesystem structure.
- No new auth or token handling is introduced.

## Performance Impact

- Negligible. Changes are documentation and startup-path resolution only.

## Active Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.

## Annotation Review

Round 1:
- All files to modify are explicitly named.
- Tradeoffs are documented for each major decision.
- Verification maps directly to each success criterion.
- No open questions remain from `research.md`.

## Plan vs Reality

- `README.md` required a fuller rewrite than initially expected because the previous version still looked like an internal workspace note rather than a public migration project.
- The DB cleanup was narrower than a codebase-wide refactor: the critical fixes were removing hardcoded launcher paths and changing the data-layer default away from a local sibling data folder.
- Verification stayed aligned with plan: leak scan, compile checks, and full packaging rebuild were all run successfully.
