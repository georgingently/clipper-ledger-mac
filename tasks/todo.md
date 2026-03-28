## Checklist

- [x] Create branch from latest `origin/main`
- [x] Refresh `research.md`
- [x] Refresh `plan.md`
- [x] Fix menu double-open behavior
- [x] Fix crash path for generic stock/table screens
- [x] Tighten legacy text/layout parity where still off
- [x] Verify DBF-backed linkage for visible menu options
- [x] Re-run workflow PDF export
- [x] Run Python syntax checks
- [ ] Commit and push branch changes
- [ ] Complete PR/merge/cleanup flow
- [x] Update `tasks/lessons.md` if needed

## Execution Notes

- Branch: `fix/legacy-ui-crash-parity`
- Branch base: `origin/main` @ `31e98cd`
- Crash trace points at a Python exception escaping a `QListWidget` double-click slot on the main thread.
- Two immediate suspects:
  - menu action double-dispatch from both `itemActivated` and `itemDoubleClicked`
  - `GenericTableModule` using `ModuleBase` helpers without inheriting from `ModuleBase`

## Review

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- `QT_QPA_PLATFORM=offscreen python3 ... DosMenuPage(...) / GenericTableModule('SRCT') ...`
- `QT_QPA_PLATFORM=offscreen python3 ... export_workflow_pdf(None, 'A4 2024-25,2025-2026', 'workflow_preview.pdf') ...`
