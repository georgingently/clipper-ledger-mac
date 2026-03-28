## Scope

Fix the packaged-app crash in the legacy menu flow, stop duplicate Cash/Bank opening behavior, improve UI parity toward the attached screenshots, and ensure every exposed menu option opens a real DBF-backed screen instead of a broken or placeholder path.

## Files To Modify

- `georgin_app.py`
- `research.md`
- `plan.md`
- `tasks/todo.md`

## Design Decisions

1. Fix the crash by eliminating unsafe menu double-dispatch and by making generic stock/table modules inherit the shared base class they already depend on.
Tradeoff: this is the smallest stable fix path and directly addresses the stack trace, but it does not by itself complete pixel-perfect parity.

2. Treat duplicate Cash/Bank opening as an event-wiring bug, not a book-selection-data bug.
Tradeoff: removing duplicate Qt signal handling is lower risk than adding stateful guards around individual handlers.

3. Keep menu destinations DBF-backed by routing stock and table options through working modules only.
Tradeoff: generic DBF browser views remain less exact than the screenshots, but they preserve database coverage while the parity refactor continues.

4. Tighten the legacy shell text and labels where they still diverge materially from the screenshots.
Tradeoff: this is still iterative; exact parity requires matching both structure and wording without destabilizing working screens.

## Code-Level Approach

- Update `DosMenuPage` signal wiring so a double-click opens exactly once.
- Add a small activation guard only if needed after signal cleanup.
- Change `GenericTableModule` to inherit from `ModuleBase` so `_title_bar`, `_search_box`, `_footer_bar`, and table helpers are always available.
- Review table/master/report openers and ensure they each resolve to a DBF-backed widget without constructor errors.
- Reduce remaining placeholder preview text and align key titles/labels closer to the screenshots.
- Re-run the workflow PDF export and Python syntax checks after the fixes.

## Success Criteria

- Double-clicking a menu item opens it once.
- Cash Book and Bank Book do not prompt twice.
- Stock Receipt / Stock Issue / Glass Stock / Database Tables do not crash on open.
- Exposed menu options remain linked to DBF-backed modules or generic DBF table viewers.
- The packaged-app crash path from the provided trace is addressed in code.
- Legacy labels and shell text are closer to the attached screenshots than the current state.

## Test Strategy

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- Launch the app and manually verify:
  - double-clicking menu items opens once
  - Cash Book opens directly once
  - Bank Book asks for selection once
  - Stock Receipt / Stock Issue / Glass Stock open without crashing
  - Database Tables opens and arbitrary table drill-in works
- `QT_QPA_PLATFORM=offscreen python3 - <<'PY' ... export_workflow_pdf(None, 'A4 2024-25,2025-2026', 'workflow_preview.pdf') ... PY`
- `git diff --stat`

## Assumptions

- The crash came from the current merged `main` state, not from an untracked local packaging-only change.
- The user’s “all options” requirement means every visible menu item should either open a real screen or a generic DBF browser, not silently do nothing.
- Exact text parity can be improved in this task, but the highest priority remains crash-free single-path workflow execution.

## Rollback Strategy

- Keep the fixes localized to menu wiring and module inheritance so they can be reverted without touching DBF semantics.
- If a menu refactor causes wider regressions, revert to the last merged shell commit and reapply only the crash/double-open fixes first.

## Security Impact

- Neutral. This is a UI/control-flow stability fix with no auth, network, or secret-handling changes.

## Performance Impact

- Negligible. The changes reduce duplicate handler execution and avoid exception-driven aborts.

## Active Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.
- For repositories that work with DBF datasets, `.gitignore` must block the full DBF/memo/index file family so accidental local data drops never get pushed.
- In packaged PyQt apps, unhandled Python exceptions inside Qt slots can abort the entire app, so menu/event wiring must avoid duplicate dispatch and constructor paths used by slots must be import-safe.

## Annotation Review

Round 1:
- Crash root cause candidates are explicitly tied to the stack trace and named code paths.
- Every file to modify is named.
- Test strategy maps directly to the user-reported failures.

Round 2:
- Duplicate-open handling and `GenericTableModule` inheritance are the primary code changes.
- No open questions remain from `research.md`.

## Plan vs Reality

- The crash fix was split into two direct changes: remove duplicate menu double-click dispatch and make `GenericTableModule` self-sufficient instead of relying on `ModuleBase` methods it could not safely inherit at its declaration point.
- To move closer to the screenshot text, the visible Reports and Files menus were renamed toward the legacy wording and mapped to DBF-backed modules or generic DBF viewers.
- Verification remained lightweight and offscreen because no bundled GEORGIN sample database is available for full automated UI traversal.
