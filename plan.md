## Scope

Rename the public GitHub repository to `clipper-ledger-mac`, then update tracked documentation so the public-facing repo identity is consistent and intentional.

## Files To Modify

- `README.md`
- `UPDATES.md`
- `research.md`
- `plan.md`
- `tasks/todo.md`

## Design Decisions

1. Rename only the GitHub repository, not the app/package name.
Tradeoff: public repo identity improves without forcing a product rename or installer changes.

2. Use `clipper-ledger-mac` as the new repo name.
Tradeoff: it is more descriptive for outside users, but it is less tightly tied to the historical internal project naming.

3. Update docs to the new canonical repo path even though GitHub will redirect old links.
Tradeoff: requires a small doc sweep now, but avoids long-term drift and stale examples.

## Code-Level Approach

- Rename the repository with `gh repo rename clipper-ledger-mac`.
- Update explicit repo-name mentions in docs, especially `UPDATES.md`.
- Leave release scripts intact because they resolve the repository dynamically.
- Verify the new repo URL and release/PR visibility after rename.

## Success Criteria

- GitHub repository name becomes `clipper-ledger-mac`.
- Public repo URL resolves under the new name.
- No tracked docs still reference the previous repository path.
- Release automation remains valid after rename.

## Test Strategy

- `rg -n "clipper-ledger-mac|previous repository path" README.md UPDATES.md CONTRIBUTING.md CHANGELOG.md release_app.sh research.md plan.md tasks/todo.md`
- `gh repo view georgingently/clipper-ledger-mac --json name,nameWithOwner,url`
- `git status --short`

## Assumptions

- Only the GitHub repository name needs to change in this task.
- The existing app display name `GEORGIN Accounting` should remain unchanged.

## Rollback Strategy

- If the rename causes an unexpected blocker, rename the repo back to the previous name with the same GitHub CLI workflow.
- Because scripts resolve repo identity dynamically, doc-only fixes are easy to revert independently if needed.

## Security Impact

- Neutral. The rename does not alter auth, secrets, or data-handling behavior.

## Performance Impact

- None. This is a metadata and documentation change only.

## Active Lessons

- Do not commit developer-specific database paths or machine-local filesystem assumptions into tracked launchers or defaults before publishing the repository.
- Public-facing repository docs should explain the engineering motivation and current constraints clearly so the project reads as intentional, not improvised.

## Annotation Review

Round 1:
- Files affected by the rename are explicitly named.
- Tradeoffs are documented.
- Verification covers metadata and docs.
- No open questions remain.

## Plan vs Reality

- The GitHub rename itself completed cleanly with no script changes required because `release_app.sh` already resolves the repo dynamically.
- The user added an additional requirement during execution: future dropped database files must never be staged accidentally. This expanded the implementation to harden `.gitignore` with DBF/Clipper file-family patterns and known data-folder names.
- Verification focused on repo metadata and ignore-rule behavior rather than code compilation because the implementation was metadata/documentation only.
