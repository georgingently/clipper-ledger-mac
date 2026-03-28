## Relevant Files

- `georgin_app.py` — contains the legacy shell, menu activation path, `SalesModule`, and the unused `SalesEntryPage` detail editor.
- `models/dbf_layer.py` — DBF read/write layer backing `SREG41`; needed to confirm which sales fields can be shown and edited from the database.
- `plan.md` — single source of truth for the sales detail redesign and crash hardening.
- `tasks/todo.md` — execution tracker for this fix.

## Data Flow

1. `MainWindow` creates `DosMenuPage`, whose `QListWidget` routes menu activations into handlers like `_open_sales`.
2. `_open_sales` instantiates `SalesModule`, which reads sales header records from `SREG41`.
3. `SalesModule` currently renders a top browse table and a lightweight inline form under it; clicking a row only copies a subset of fields into that inline form.
4. `SalesEntryPage` already exists as a fuller sales editor, but it is not wired into the active sales workflow.
5. Saving sales edits writes back to `SREG41` through `write_record` / `update_record` in `models/dbf_layer.py`.

## Constraints & Risks

- The user wants the sales workflow to behave like the legacy screenshots: selecting a sale should expose the full editable detail area, not just a partial quick form.
- The current packaged crash traces still terminate inside Qt slot proxies; even when the originating bug is in downstream module construction, an uncaught Python exception in `DosMenuPage._activate_item` can abort the whole packaged app.
- `SREG41` provides only sales-header fields in the current codebase. There is no existing linked line-item sales table implementation to populate a full item grid from DBF data.
- Reworking the sales screen must preserve DBF-backed editing and avoid adding placeholder-only UI that cannot save.

## Findings

1. `SalesModule` still connects both `clicked` and `doubleClicked` to `_edit_entry`, and `_edit_entry` only hydrates the small inline form instead of opening a fuller detail section.
2. The existing `SalesEntryPage` proves the app already has a fuller sales editor shape, but it is effectively dead code in the current user workflow.
3. `DosMenuPage._activate_item` currently calls handlers directly with no exception guard, which leaves the packaged app vulnerable to fatal aborts whenever a handler raises during a Qt-triggered menu activation.
4. Offscreen construction of `SalesModule` succeeds with the current repo state, so the remaining crash risk is more likely from slot exception propagation during live activation than from a permanent import-time failure.

## Open Questions

None.
