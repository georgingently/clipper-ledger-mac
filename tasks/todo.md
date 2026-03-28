## Checklist

- [x] Audit tracked files for local database path leakage and public-repo issues
- [x] Create `research.md`
- [x] Create `plan.md`
- [x] Remove hardcoded local DB paths from tracked launch/config files
- [x] Rewrite `README.md` around project motivation and public-facing quality
- [x] Add `CHANGELOG.md`
- [x] Add `CONTRIBUTING.md`
- [x] Verify no local DB path remains in tracked files
- [x] Run compile/build verification
- [ ] Commit and push branch changes
- [ ] Make the repository public
- [ ] Complete PR/merge/cleanup flow
- [ ] Update `tasks/lessons.md`

## Execution Notes

- Branch: `chore/public-release-readiness`
- Base: `origin/main`
- Main risks: local DB path leakage, weak repo presentation, accidental public exposure before verification

## Review

- Leak scan: `rg -n "/Volumes/Workspace|GEORGIN tra" . --glob '!dist/**' --glob '!build/**' --glob '!.git/**'`
- Compile check: `python3 -m py_compile georgin_app.py models/dbf_layer.py app.py`
- Packaging check: `bash build_app.sh`
