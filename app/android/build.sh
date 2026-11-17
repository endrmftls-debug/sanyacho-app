#!/usr/bin/env bash
# Builds the APK without Gradle: aapt2 (resources) -> javac -> d8 (dex) -> zipalign -> apksigner.
# Usage: app/android/build.sh <www-dir> <out.apk> [versionCode] [versionName]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WWW="$(cd "$1" && pwd)"
OUT_APK="$2"
VCODE="${3:-1}"
VNAME="${4:-0.1}"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/home/claude/android-sdk}}"
BT="$(ls -d "$SDK"/build-tools/* | sort -V | tail -1)"
PLAT="$(ls -d "$SDK"/platforms/android-* | sort -V | tail -1)/android.jar"
B="$(mktemp -d)"
trap 'rm -rf "$B"' EXIT
mkdir -p "$B/res" "$B/gen" "$B/classes" "$B/dex" "$B/assets"

ln -s "$WWW" "$B/assets/www"
"$BT/aapt2" compile --dir "$HERE/res" -o "$B/res/res.zip"
"$BT/aapt2" link -o "$B/unsigned.apk" -I "$PLAT" --manifest "$HERE/AndroidManifest.xml" \
  --min-sdk-version 24 --target-sdk-version 35 --version-code "$VCODE" --version-name "$VNAME" \
  --java "$B/gen" -A "$B/assets" -0 onnx -0 wasm -0 jpg -0 png -0 zip "$B/res/res.zip"
javac -nowarn -source 8 -target 8 -bootclasspath "$PLAT" -d "$B/classes" \
  $(find "$HERE/src" -name '*.java') $(find "$B/gen" -name '*.java') 2>&1 | grep -v "warning: \[options\]" || true
[ -n "$(find "$B/classes" -name '*.class' | head -1)" ] || { echo "javac failed"; exit 1; }
"$BT/d8" --release --min-api 24 --lib "$PLAT" --output "$B/dex" $(find "$B/classes" -name '*.class')
(cd "$B/dex" && zip -q -u "$B/unsigned.apk" classes.dex)
"$BT/zipalign" -p -f 4 "$B/unsigned.apk" "$B/aligned.apk"
KS="$HERE/signing/sanyacho.jks"
if [ ! -f "$KS" ]; then
  keytool -genkeypair -keystore "$KS" -storepass sanyacho -keypass sanyacho -alias sanyacho \
    -keyalg RSA -keysize 3072 -validity 20000 -dname "CN=Sanyacho Guide, O=Personal, C=KR" >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:sanyacho --key-pass pass:sanyacho --ks-key-alias sanyacho \
  --out "$OUT_APK" "$B/aligned.apk"
"$BT/apksigner" verify "$OUT_APK" && echo "built $OUT_APK ($(du -h "$OUT_APK" | cut -f1))"
