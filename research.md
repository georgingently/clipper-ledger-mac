## Relevant Files

- `georgin_app.py` — contains the PyQt desktop shell, menu list event wiring, entry/report handlers, and the modules for stock/report/master screens.
- `models/dbf_layer.py` — DBF read/write layer used by all menu destinations; needed to confirm which screens are truly database-backed.
- `README.md` — may need a small update if behavior changes materially.
- `tasks/todo.md` — execution tracker for this fix task.
- `plan.md` — single source of truth for crash/root-cause fixes and verification.

## Data Flow

1. `MainWindow` instantiates `DosMenuPage`, which exposes a `QListWidget` of actions under Entries / Reports / Utilities / Files / Help / Quit.
2. Double-clicking a menu item currently routes through Qt slot proxies into `_activate_item`, which then calls a handler like `_open_cash_book`, `_open_bank_book`, `_open_stock_receipt`, or `_open_db_tables`.
3. Many handlers build a module widget and push it onto the stacked desktop shell. Those modules then load DBF tables through `models/dbf_layer.py`.
4. `GenericTableModule` is used for Stock Receipt, Stock Issue, Glass Stock, and arbitrary table browsing from Database Tables, so any constructor error there breaks multiple menu paths.

## Constraints & Risks

- The user wants exact legacy parity, but the immediate bug fix must prioritize stability and single-invocation workflow correctness.
- The crash log points to a Python exception propagating through a Qt slot proxy during a `QListWidget` double-click path; PyQt packaged apps abort on these unhandled slot exceptions.
- The current menu widget connects both `itemActivated` and `itemDoubleClicked` to the same opener. On macOS this can trigger duplicate opens for the same user action.
- `GenericTableModule` currently subclasses `QWidget` while using helper methods only defined on `ModuleBase`, creating a likely `AttributeError` when opening stock/generic-table screens.
- “All options should be linked to the database” means menu targets should open real DBF-backed modules wherever data exists instead of placeholders or broken generic pages.

## Open Questions

None.
