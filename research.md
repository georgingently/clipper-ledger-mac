## Relevant Files

- `README.md` — public-facing project documentation; should reflect the new repository identity where relevant.
- `UPDATES.md` — update strategy notes; currently references the existing repository name directly.
- `release_app.sh` — release automation; resolves the repo dynamically, so it is low-risk for rename but should be checked.
- `CHANGELOG.md` — release history; may need wording review after repo rename.
- `CONTRIBUTING.md` — contribution guidance; should remain valid after rename.
- GitHub repository metadata — actual repo name, URL, and derived release/PR paths.

## Data Flow

1. GitHub repository name controls the canonical clone URL, PR URL, and release URL.
2. `release_app.sh` queries the current repo name dynamically via `gh repo view`, so it should continue to work after rename without hardcoded changes.
3. Repository docs may still mention the old repo path explicitly, especially in update-strategy notes.
4. GitHub normally redirects renamed repository URLs, but public-facing docs should still be updated to the new canonical name.

## Constraints & Risks

- The rename should not break release automation or any scripts that dynamically resolve the current GitHub repo.
- Public docs should avoid stale references to the previous repository path.
- The repo rename should preserve current release history and PR history.
- No app/package rename is requested here; only the GitHub repository identity should change.

## Open Questions

None.
