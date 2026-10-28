#!/bin/bash
# Bangun "/Applications/RIXSUN AI STUDIO LOCAL.app" dari AIStudio.swift (ikon AppIcon.icns, latar Latar.jpg)
# + payload pemasang untuk Mac lain (setup.sh, skrip studio, suara narator).
#   build.sh          bangun & pasang ke /Applications
#   build.sh dmg      juga buat installer dist/RIXSUN-AI-Studio-Local.dmg
set -e
D="$(cd "$(dirname "$0")" && pwd)"
STUDIO="$(dirname "$D")"
AI="$(dirname "$STUDIO")"
APP="/Applications/RIXSUN AI STUDIO LOCAL.app"
TMP="$(mktemp -d)/RIXSUN AI STUDIO LOCAL.app"
mkdir -p "$TMP/Contents/MacOS" "$TMP/Contents/Resources/payload/tts/ref"
swiftc -O -swift-version 5 -parse-as-library -target arm64-apple-macos14 "$D/AIStudio.swift" -o "$TMP/Contents/MacOS/AIStudio"
cp "$D/AppIcon.icns" "$TMP/Contents/Resources/AppIcon.icns"
[ -f "$D/Latar.jpg" ] && cp "$D/Latar.jpg" "$TMP/Contents/Resources/Latar.jpg"
cp "$STUDIO/donasi.json" "$TMP/Contents/Resources/donasi.json"
# payload: skrip studio tanpa cadangan/cache/sumber app/pilihan otak pribadi
rsync -a --exclude "_cadangan*" --exclude __pycache__ --exclude .DS_Store --exclude otak.txt --exclude app \
    --exclude "*.scpt" --exclude ikon.png --exclude .git --exclude .gitignore --exclude README.md --exclude donasi.json "$STUDIO/" "$TMP/Contents/Resources/payload/studio/"
cp "$AI/tts/ref/narator_wanita_66.wav" "$AI/tts/ref/narator_wanita_66.txt" "$TMP/Contents/Resources/payload/tts/ref/"
cp "$D/pasang/setup.sh" "$D/pasang/mflux-req.txt" "$TMP/Contents/Resources/payload/"
cat > "$TMP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>AIStudio</string>
  <key>CFBundleIdentifier</key><string>com.ikya.aistudiolocal</string>
  <key>CFBundleName</key><string>RIXSUN AI STUDIO LOCAL</string>
  <key>CFBundleDisplayName</key><string>RIXSUN AI STUDIO LOCAL</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>2.3</string>
  <key>CFBundleVersion</key><string>4</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>LSArchitecturePriority</key><array><string>arm64</string></array>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOF
codesign --force --deep -s - "$TMP"

if [ "$1" = dmg ]; then
    mkdir -p "$D/dist"; ISI="$(mktemp -d)/RIXSUN AI Studio Local"; mkdir -p "$ISI"
    ditto "$TMP" "$ISI/RIXSUN AI STUDIO LOCAL.app"
    ln -s /Applications "$ISI/Applications"
    cat > "$ISI/READ ME FIRST.txt" <<'EOF'
RIXSUN AI STUDIO LOCAL - installing on a Mac

Requirements: Mac with Apple silicon (M1/M2/M3/M4), 16 GB RAM or more,
~52 GB free disk space (full package), internet connection.

1. Drag "RIXSUN AI STUDIO LOCAL" into the Applications folder.
2. Open Applications, RIGHT-CLICK the app -> Open -> Open
   (once only; the app is not signed by Apple).
   If it is still blocked: System Settings -> Privacy & Security -> "Open Anyway".
3. The Setup screen appears: choose a location (an external SSD is
   recommended) and the packages, then click Install.
   Terminal opens and downloads everything automatically (1-3 hours).
   If the connection drops, click Install again; it resumes.
4. Content package: VoiceStudio opens; finish its wizard, then press Enter in Terminal.
5. Done: click "Check Again" in the app.

Language: the app follows your Mac's language (English / Indonesian).
Change it in Settings (gear icon, or Cmd+,).

Optional online AI brains:
- Claude / Opus  : install Claude Code (https://claude.com/claude-code) and sign in.
- Free DeepSeek  : install OpenCode -> curl -fsSL https://opencode.ai/install | bash

Source & help: https://github.com/maulanaikya99/rixsun-ai-studio-local
EOF
    rm -f "$D/dist/RIXSUN-AI-Studio-Local.dmg"
    hdiutil create -quiet -volname "RIXSUN AI Studio Local" -srcfolder "$ISI" -fs HFS+ -format UDZO "$D/dist/RIXSUN-AI-Studio-Local.dmg"
    echo "DMG: $D/dist/RIXSUN-AI-Studio-Local.dmg ($(du -h "$D/dist/RIXSUN-AI-Studio-Local.dmg" | cut -f1))"
fi

rm -rf "$APP"
mv "$TMP" "$APP"
touch "$APP"
echo "OK: $APP"
