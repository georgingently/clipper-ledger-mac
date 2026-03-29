#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

VERSION="$(tr -d '[:space:]' < VERSION)"
APP_NAME="GEORGIN Accounting"
DMG_PATH="dist/GEORGIN_Accounting_Installer.dmg"
TAG="v$VERSION"
VERSION_JSON="docs/version.json"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required."
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This folder is not a git repository."
  exit 1
fi

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
if [ -z "$REPO" ]; then
  echo "Unable to resolve GitHub repository from current checkout."
  exit 1
fi

mkdir -p docs
cat > "$VERSION_JSON" <<EOF
{
  "version": "$VERSION",
  "download_url": "https://github.com/$REPO/releases/latest/download/GEORGIN_Accounting_Installer.dmg",
  "notes": "GitHub release $TAG"
}
EOF
touch docs/.nojekyll

bash build_app.sh

if ! git diff --quiet || ! git diff --cached --quiet; then
  git add VERSION build_app.sh georgin_app.py README.md docs/version.json docs/.nojekyll release_app.sh
  git commit -m "Release $TAG"
fi

git push origin main

if git rev-parse "$TAG" >/dev/null 2>&1; then
  git tag -d "$TAG" >/dev/null 2>&1 || true
fi
git tag -a "$TAG" -m "$APP_NAME $TAG"
git push origin "$TAG" --force

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  gh release upload "$TAG" "$DMG_PATH" --repo "$REPO" --clobber
else
  gh release create "$TAG" "$DMG_PATH" \
    --repo "$REPO" \
    --title "$APP_NAME $TAG" \
    --notes "Release $TAG"
fi

echo "Release published: $TAG"
