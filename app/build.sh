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
# payload: skrip studio tanpa cadangan/cache/sumber app/pilihan otak pribadi
rsync -a --exclude "_cadangan*" --exclude __pycache__ --exclude .DS_Store --exclude otak.txt --exclude app \
    --exclude "*.scpt" --exclude ikon.png --exclude .git --exclude .gitignore --exclude README.md "$STUDIO/" "$TMP/Contents/Resources/payload/studio/"
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
  <key>CFBundleShortVersionString</key><string>2.1</string>
  <key>CFBundleVersion</key><string>3</string>
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
    cat > "$ISI/BACA DULU.txt" <<'EOF'
RIXSUN AI STUDIO LOCAL - cara pasang di Mac lain

Syarat: Mac chip Apple (M1/M2/M3/M4), RAM 16 GB atau lebih, ruang kosong ±52 GB (paket lengkap), internet.

1. Seret "RIXSUN AI STUDIO LOCAL" ke folder Applications.
2. Buka Applications, KLIK KANAN aplikasinya -> Open -> Open
   (sekali saja; aplikasi ini tidak ditandatangani Apple).
   Bila tetap diblokir: System Settings -> Privacy & Security -> "Open Anyway".
3. Muncul layar Persiapan: pilih lokasi (SSD eksternal disarankan) dan paket, klik Pasang.
   Terminal terbuka dan mengunduh semuanya otomatis (1-3 jam). Bila terputus, klik Pasang lagi.
4. Paket Konten: VoiceStudio akan terbuka; selesaikan wizard-nya lalu tekan Enter di Terminal.
5. Selesai: klik "Periksa Lagi" di aplikasi.

Opsional (otak AI online):
- Claude / Opus : pasang Claude Code (https://claude.com/claude-code) lalu login.
- DeepSeek gratis: pasang OpenCode -> curl -fsSL https://opencode.ai/install | bash
EOF
    rm -f "$D/dist/RIXSUN-AI-Studio-Local.dmg"
    hdiutil create -quiet -volname "RIXSUN AI Studio Local" -srcfolder "$ISI" -fs HFS+ -format UDZO "$D/dist/RIXSUN-AI-Studio-Local.dmg"
    echo "DMG: $D/dist/RIXSUN-AI-Studio-Local.dmg ($(du -h "$D/dist/RIXSUN-AI-Studio-Local.dmg" | cut -f1))"
fi

rm -rf "$APP"
mv "$TMP" "$APP"
touch "$APP"
echo "OK: $APP"
