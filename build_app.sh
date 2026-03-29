#!/bin/bash
# Build GEORGIN Accounting.app and a distributable DMG for macOS.
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="GEORGIN Accounting"
APP_BUNDLE="$APP_NAME.app"
DMG_NAME="GEORGIN_Accounting_Installer.dmg"
STAGING_DIR="dist/dmg-staging"
APP_VERSION="$(tr -d '[:space:]' < VERSION)"

echo "Cleaning previous build artifacts..."
rm -rf build "$APP_NAME.spec"
if [ -d dist ]; then
  find dist -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  rmdir dist 2>/dev/null || true
fi

echo "Building $APP_BUNDLE..."
pyinstaller \
  --name "$APP_NAME" \
  --windowed \
  --onedir \
  --noconfirm \
  --add-data "models:models" \
  --add-data "VERSION:." \
  --hidden-import dbfread \
  --hidden-import dbf \
  --hidden-import reportlab \
  --hidden-import PyQt6 \
  --hidden-import PyQt6.QtPrintSupport \
  --osx-bundle-identifier "com.georgin.accounting" \
  georgin_app.py

APP_PLIST="dist/$APP_BUNDLE/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$APP_PLIST"
if /usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$APP_PLIST" >/dev/null 2>&1; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$APP_PLIST"
else
  /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $APP_VERSION" "$APP_PLIST"
fi

echo "Re-signing app bundle after Info.plist update..."
xattr -cr "dist/$APP_BUNDLE"
codesign \
  --force \
  --deep \
  --sign - \
  --timestamp=none \
  "dist/$APP_BUNDLE"

echo "Preparing DMG contents..."
mkdir -p "$STAGING_DIR"
cp -R "dist/$APP_BUNDLE" "$STAGING_DIR/"
ln -sfn /Applications "$STAGING_DIR/Applications"

rm -f "dist/$DMG_NAME"
echo "Creating DMG..."
hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  "dist/$DMG_NAME"

echo ""
echo "Build complete!"
echo "App bundle: dist/$APP_BUNDLE"
echo "Installer DMG: dist/$DMG_NAME"
echo ""
echo "Send the DMG file to users. They can open it and drag"
echo "\"$APP_BUNDLE\" into Applications."
echo ""
echo "On first launch, the app will ask them to select the"
echo "folder containing their GEORGIN DBF data."
