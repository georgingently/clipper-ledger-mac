## Checklist

- [x] Create branch from latest `origin/main`
- [x] Refresh `research.md`
- [x] Refresh `plan.md`
- [x] Rename the GitHub repository to `clipper-ledger-mac`
- [x] Update documentation references to the new repo name
- [x] Verify no tracked docs still use the previous repo path
- [ ] Commit and push branch changes
- [ ] Complete PR/merge/cleanup flow
- [ ] Update `tasks/lessons.md` if needed

## Execution Notes

- Branch: `chore/repo-rename`
- Current repo: `georgingently/clipper-ledger-mac`
- Target repo: `georgingently/clipper-ledger-mac`
- App/package name remains unchanged in this task

## Review

- Repo rename verified via `gh repo view georgingently/clipper-ledger-mac --json name,nameWithOwner,url,visibility`
- Previous repo path scan: `rg -n "georgingently/GEORGIN_MAC|GEORGIN_MAC" README.md UPDATES.md CONTRIBUTING.md CHANGELOG.md release_app.sh research.md plan.md tasks/todo.md`
- Git ignore verification: `git check-ignore -v` confirms DBF, memo/index, and `.georgin_settings.json` paths are ignored
