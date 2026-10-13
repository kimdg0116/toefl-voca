#!/bin/zsh
# 토플 단어.app (mac/main.swift → 맥 앱 한 개, 창 한 개) 를 toefl-voca 폴더에 만든다. Dock 으로 끌어다 두면 된다.
# 단어 파일(data/toefl-words.json)과 연결 코드(sync/Secret.js)를 앱 안에 넣는다 — 둘 다 git 에 없다
set -e
cd "$(dirname "$0")/.."
APP="토플 단어.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
swiftc -O mac/main.swift -o "$APP/Contents/MacOS/toefl-voca"
cp data/toefl-words.json "$APP/Contents/Resources/"
sed -n "s/.*CODE = '\([0-9]*\)'.*/\1/p" sync/Secret.js > "$APP/Contents/Resources/sync-code.txt"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleIdentifier</key><string>com.kimdg0116.toefl-voca</string>
  <key>CFBundleName</key><string>토플 단어</string>
  <key>CFBundleDisplayName</key><string>토플 단어</string>
  <key>CFBundleExecutable</key><string>toefl-voca</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
# 아이콘 (토플 Writing 과 같은 모양)
python3 - <<'PY'
from PIL import Image, ImageDraw, ImageFont
F = '/System/Library/Fonts/Avenir Next Condensed.ttc'
n = 1024
im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rounded_rectangle((90, 90, n - 90, n - 90), radius=190, fill='white')
d.text((n/2, n*0.36), 'TOEFL', font=ImageFont.truetype(F, 120, index=0), fill='#2e70ff', anchor='mm')
d.text((n/2, n*0.56), 'VOCA', font=ImageFont.truetype(F, 250, index=0), fill='#1428a0', anchor='mm')
d.rounded_rectangle((n*0.32, n*0.70, n*0.68, n*0.72), radius=8, fill='#2e70ff')
im.save('/tmp/toefl-voca-icon.png')
PY
rm -rf /tmp/tv.iconset && mkdir /tmp/tv.iconset
for s in 16 32 128 256 512; do
  sips -z $s $s /tmp/toefl-voca-icon.png --out /tmp/tv.iconset/icon_${s}x${s}.png >/dev/null
  sips -z $((s*2)) $((s*2)) /tmp/toefl-voca-icon.png --out /tmp/tv.iconset/icon_${s}x${s}@2x.png >/dev/null
done
iconutil -c icns /tmp/tv.iconset -o "$APP/Contents/Resources/AppIcon.icns"
codesign --force --deep -s - "$APP"
touch "$APP"
echo "만듦: $PWD/$APP"
