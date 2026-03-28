## Scope

Rebuild the desktop application shell so it matches the attached legacy GEORGIN/Clipper screenshots as closely as possible while preserving the existing DBF-backed workflows, then add a PDF workflow export that captures the recreated legacy screens.

## Files To Modify

- `georgin_app.py`
- `README.md`
- `research.md`
- `plan.md`
- `tasks/todo.md`

## Design Decisions

1. Keep the current DBF data-access and module actions intact, and redesign the PyQt shell around them.
Tradeoff: this minimizes business-logic regression risk, but some widgets must be restructured instead of fully replaced.

2. Introduce shared legacy-shell helpers for header, title tabs, footers, framed panels, and browse/edit layouts.
Tradeoff: a shared shell creates consistency across screens, but it requires touching several existing module classes.

3. Replace modern toolbars/button rows with legacy function-key footer hints and tighter inline/edit panels that mirror the screenshots.
Tradeoff: stronger visual parity is achieved, but some convenience controls become less visually explicit.

4. Add a workflow PDF generator that exports recreated legacy screens from the app rather than relying on HTML table printouts.
Tradeoff: this is closer to the screenshots, but it requires a second export path separate from the tabular report print helpers.

5. Preserve current menu destinations and navigation order exactly where possible.
Tradeoff: some screenshot-specific intermediate dialogs may need to be represented by inline framed panels instead of literal legacy keystroke popups.

## Code-Level Approach

- Refactor the global app stylesheet to tighten the palette, typography, spacing, and selection colors toward the screenshots.
- Replace the current `DosMenuPage` left-list plus right-info panel with a real legacy menu frame:
  - boxed top header
  - horizontal section labels and line art
  - left submenu list
  - optional secondary/parameter panels on the right for report flows
  - bottom fixed footer help bar
- Extend `ModuleBase` with reusable helpers for:
  - centered title-tab headers
  - bordered browse tables
  - edit panels beneath the browse panel
  - footer key legends
  - screen capture/export support
- Update entry/report/master modules to render in the same browse/edit composition as the screenshots:
  - Cash Book / Bank Book
  - Purchase
  - Sales
  - Journal
  - Stock Receipt / Stock Issue
  - Account / Item master
  - report viewer screens for ledger / trial balance / stock summary / itemwise flows
- Add a workflow PDF export path that can stitch together screen captures of the recreated UI into a single PDF.
- Keep the existing HTML print/PDF helpers only for tabular exports where they remain useful, but route the new “workflow PDF” requirement through the legacy-screen capture flow.

## Success Criteria

- The main window visually matches the legacy screenshots closely:
  - black background
  - white/gray line frames
  - centered title tabs
  - legacy header/footer treatment
  - red and teal highlight states
- Menu workflow remains intact for Entries, Reports, Utilities, Files, Help, and Quit.
- Core modules render in the same browse/edit workflow shape as the screenshots without changing DBF-backed behavior.
- The app can generate a PDF that documents the recreated workflow screens in sequence.
- Existing desktop startup still works without changing DBF read/write semantics.

## Test Strategy

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- Launch the desktop app locally and validate:
  - menu shell
  - cash/bank browse/edit layout
  - purchase browse/edit layout
  - sales browse/edit layout
  - journal browse/edit layout
  - account/item master browse/edit layout
  - at least one report-viewer layout
- Generate the workflow PDF and confirm the file is created successfully.
- `git diff --stat`

## Assumptions

- The user wants the PyQt desktop app to be the canonical implementation target.
- The existing DBF-backed modules already represent the correct functional workflow and should be preserved.
- Recreated local screen captures are acceptable for the PDF deliverable because the prompt attachments are not available as filesystem images inside the repository.

## Rollback Strategy

- Keep DBF-layer behavior unchanged so UI refactors can be reverted without data-format consequences.
- If a shared-shell refactor destabilizes multiple modules, revert the shell/helper changes and reapply the redesign incrementally to the highest-priority screens first.
- If the new workflow PDF path proves unstable, preserve the UI redesign and temporarily fall back to exporting a reduced set of recreated screens while documenting the limitation.

## Security Impact

- Neutral. The work changes desktop presentation and export behavior, not auth, secrets, or remote connectivity.

## Performance Impact

- Low risk. The new shell adds more framed widgets and optional screen rendering for PDF export, but the DBF access pattern is unchanged.
- The only potentially heavier operation is PDF generation from screen captures; that should be user-triggered and not affect normal browsing or editing.

## Active Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.
- For repositories that work with DBF datasets, `.gitignore` must block the full DBF/memo/index file family so accidental local data drops never get pushed.

## Annotation Review

Round 1:
- All currently expected files to modify are explicitly named.
- The workflow-preservation constraint is documented.
- The PDF limitation around non-local prompt attachments is recorded up front.
- Test strategy maps to the major UI success criteria.

Round 2:
- Shared-shell refactor is the chosen implementation path to avoid duplicated one-off styling edits.
- Entry, report, and master modules are all covered explicitly.
- No open questions remain from `research.md`.

## Plan vs Reality

- The implementation stayed centered on `georgin_app.py`; the existing DBF data layer did not need changes.
- Instead of embedding the prompt attachment binaries directly into the PDF, the app now exports a recreated legacy workflow PDF composed from in-app rendered reference screens. This matches the screenshots structurally while avoiding a dependency on non-repository image files.
- Verification used offscreen Qt PDF generation plus Python syntax checks because the repository does not bundle a test dataset for a full interactive desktop run in automation.
