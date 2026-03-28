## Relevant Files

- `georgin_app.py` — primary PyQt desktop app; contains the window shell, DOS-style menu page, entry modules, report modules, export helpers, and the current PDF/export flow.
- `georgin_tui.py` — terminal reference for legacy Clipper interaction patterns; useful for parity cues and menu flow wording.
- `models/dbf_layer.py` — DBF read/write layer and table discovery; must remain unchanged in behavior so the UI redesign does not break legacy data access.
- `README.md` — should reflect the new legacy-UI parity and workflow PDF capability if those features become user-visible.
- `tasks/todo.md` — execution tracker for this task.
- `plan.md` — single source of truth for implementation scope, risks, and verification.

## Data Flow

1. `MainWindow` boots with a selected financial year and company, then routes the user through `DosMenuPage`.
2. Menu handlers open PyQt module widgets such as `CashBankBookModule`, `SalesModule`, `PurchaseModule`, `JournalModule`, and report/master modules.
3. Each module reads and writes DBF tables through `models/dbf_layer.py`; this data path is already working and should be preserved.
4. Existing print/PDF/export behavior is HTML-table based; it does not match the legacy screenshots and needs a new workflow-oriented PDF output path.
5. The user’s screenshots show a stricter legacy frame:
   - boxed header with date, company/year, and time
   - horizontal top menu with left-side submenu workflow
   - browse screens with centered title tabs
   - edit overlays and report-viewer screens
   - persistent bottom help/function-key footer

## Constraints & Risks

- The user explicitly wants the UI to match the attached screenshots and does not want the workflow changed, so the existing menu targets and data-entry flow must stay intact.
- The safest way to achieve parity is to reuse current DBF handlers and reshape only presentation, layout, and navigation chrome.
- Many modules already have “Clipper-like” styling, but they are inconsistent and still contain modern controls/buttons. Converging them to a single legacy shell risks regressions if shared helpers are changed carelessly.
- The repository does not include sample DBF data, so verification may depend on whether a local GEORGIN dataset is available in the runtime environment.
- The attached screenshots are visible in the conversation but not available as local image files, so the PDF workflow likely needs to use recreated in-app screens or exported local captures rather than embedding the original prompt assets directly.

## Open Questions

None.
