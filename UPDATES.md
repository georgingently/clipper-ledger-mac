# Update Strategy

## Current State

This repository is private. That is fine for source control, but it is the main blocker for end-user automatic updates if the update files are hosted only in GitHub private releases.

## Why Private GitHub Releases Are Not Enough

GitHub’s release asset API requires authentication for private repository assets. Unauthenticated access works only for public resources. That means a standalone desktop app cannot safely download private GitHub release assets for arbitrary end users unless every user has repository access and authenticates separately.

Embedding a GitHub personal access token inside the app is not acceptable.

## Recommended Architecture

Keep the code repository private, but host update artifacts separately.

Recommended setup:

1. Private source repository on GitHub
2. Public update host for release artifacts and metadata
3. Signed macOS app archives
4. Sparkle appcast feed pointing to the public update artifacts

## Best Path

The standard macOS solution is Sparkle.

Sparkle requires:

- an appcast feed
- signed update archives
- proper app version metadata
- ideally Developer ID signing and notarization for production distribution

## Practical Recommendation For This Project

1. Keep the source repository private
2. Publish DMG or ZIP update artifacts to a public location
3. Add Sparkle only after the public artifact host is ready
4. Keep version numbers synchronized with the `VERSION` file

## Already Prepared In This Repo

- `VERSION` file for release versioning
- `build_app.sh` updates the app bundle version metadata
- `release_app.sh` builds the app and publishes a tagged GitHub release

## Remaining Work Before True Auto-Update

- choose a public update host
- integrate Sparkle into the packaged app
- sign update archives with Sparkle keys
- add code signing and notarization if distributing broadly
