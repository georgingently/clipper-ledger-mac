## Scope

Make the Sales screen open a full editable details section when a bill is selected, keep that editor fully DBF-backed through `SREG41`, and harden the legacy menu activation path so packaged-app slot exceptions become visible errors instead of aborts.

## Files To Modify

- `georgin_app.py`
- `research.md`
- `plan.md`
- `tasks/todo.md`

## Design Decisions

1. Replace the current lightweight sales inline form workflow with a richer lower detail section inside `SalesModule`.
Tradeoff: this matches the legacy editing flow more closely than a popup and keeps the browse grid visible, but it still can only expose fields available from `SREG41`.

2. Treat row selection as the trigger for loading full bill details.
Tradeoff: this satisfies the user request directly and removes dependence on double-click editing, but it changes the sales interaction from manual edit initiation to selection-driven detail loading.

3. Keep the Sales edit surface DBF-backed only.
Tradeoff: no synthetic line-item editor will be added unless a backed sales-detail table exists in the codebase; the detail section will cover the full persisted sales-header record instead.

4. Add a `try/except` guard around menu item activation.
Tradeoff: this does not fix every possible slot failure globally, but it directly protects the crash path shown in the user’s packaged traces.

## Code-Level Approach

- Rework `SalesModule` into a two-part legacy screen:
  - top sales register browse table
  - lower editable detail section for the selected/new bill
- Remove the current minimal “NEW SALE” quick-entry behavior and replace it with full-field sales editing controls.
- Load the selected row’s record into that detail section on selection change and expose explicit actions for new, save, and delete.
- Keep create/update/delete operations writing to `SREG41`.
- Wrap `DosMenuPage._activate_item` in a guarded handler that shows a dialog and logs the error instead of letting packaged PyQt abort on an uncaught exception.

## Success Criteria

- Opening Sales from the main menu does not crash the packaged app because of an uncaught activation exception.
- Selecting a sales row loads a full editable details section immediately.
- The sales detail section can save updates back to `SREG41`.
- New sales can still be created from the sales screen.
- Delete, print, PDF, and CSV remain available from the sales screen.
- No duplicate quick-edit behavior remains in Sales.

## Test Strategy

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- `QT_QPA_PLATFORM=offscreen python3 - <<'PY' ... instantiate SalesModule ... PY`
- `QT_QPA_PLATFORM=offscreen python3 - <<'PY' ... instantiate DosMenuPage with stub handler that raises and verify no abort / dialog-safe path ... PY`
- If possible locally, simulate selecting a sales row and verify the detail widgets populate.
- `git diff --stat`

## Assumptions

- The currently implemented `SREG41` record is the authoritative editable sales source for this app version.
- “Full details section” means the full persisted bill header fields available in the database, since no wired sales line-item DBF layer exists in the repository.
- A menu activation guard is acceptable even if the user-visible message is generic, because packaged stability is the immediate requirement.

## Rollback Strategy

- Keep the sales redesign localized to `SalesModule` and the menu hardening localized to `DosMenuPage`.
- If the new sales detail section regresses editing, revert that module while keeping the safer menu activation guard.

## Security Impact

- Neutral. The change only affects local UI flow and DBF-backed CRUD behavior already present in the app.

## Performance Impact

- Negligible. The new detail section reuses already loaded sales records and removes redundant edit signal handling.

## Active Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.
- For repositories that work with DBF datasets, `.gitignore` must block the full DBF/memo/index file family so accidental local data drops never get pushed.
- In packaged PyQt apps, unhandled Python exceptions inside Qt slots can abort the entire app, so slot entry points that construct complex modules should fail visibly instead of propagating raw exceptions into Qt.

## Annotation Review

Round 1:
- The user-requested behavior and the crash trace are both represented in scope.
- The plan stays inside the current DBF-backed data model instead of inventing unsupported sales detail tables.

Round 2:
- The implementation is localized and testable.
- The success criteria map directly to the user-visible sales flow and the packaged crash symptom.

## Plan vs Reality

- `SalesModule` was redesigned in place instead of wiring the dormant `SalesEntryPage`; this kept the browse grid and the editing area visible together, which matches the requested workflow more closely.
- The sales register columns were shifted toward the legacy register wording (`Bill`, `Date`, `Party`, `Sls. Amt`, `Nett Amt`, `Type`) while the lower detail editor now holds the fuller persisted bill fields.
- The packaged crash mitigation was implemented at `DosMenuPage._activate_item` with a guarded `try/except` around handler execution, turning menu-triggered Python exceptions into dialogs instead of raw Qt aborts.
