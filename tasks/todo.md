## Checklist

- [x] Create branch from latest `origin/main`
- [x] Refresh `research.md`
- [x] Refresh `plan.md`
- [x] Rebuild the legacy shell and main menu UI in `georgin_app.py`
- [x] Align core module browse/edit layouts to the attached workflow
- [x] Add workflow PDF export for recreated legacy screens
- [x] Verify app launch and PDF generation
- [x] Run Python syntax checks
- [ ] Commit and push branch changes
- [ ] Complete PR/merge/cleanup flow
- [ ] Update `tasks/lessons.md` if needed

## Execution Notes

- Branch: `feature/legacy-ui-parity`
- Branch base: `origin/main` @ `98ca1b9`
- Branch creation helper script from skill `02-git-create-branch-from-main` was not present in the repository, so the equivalent safe fetch-and-branch flow was executed manually.
- Primary implementation target: `georgin_app.py`
- Constraint: preserve existing DBF-backed workflow while matching the attached Clipper-era visuals.

## Review

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- `QT_QPA_PLATFORM=offscreen python3 ... export_workflow_pdf(..., 'workflow_preview.pdf')`
- Verified generated artifact: `/Volumes/Workspace/Projects/Clipper/GEORGIN_MAC/workflow_preview.pdf`
