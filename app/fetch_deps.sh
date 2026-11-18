#!/usr/bin/env bash
# Puts the offline runtime pieces into app/www: ONNX Runtime Web (wasm build) and two Korean fonts.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WWW="$HERE/www"
ORT_VERSION="${ORT_VERSION:-1.31.1}"
FS_VERSION="${FS_VERSION:-5.3.0}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
cd "$T"
npm pack --silent "onnxruntime-web@$ORT_VERSION" "@fontsource/ibm-plex-sans-kr@$FS_VERSION" "@fontsource/black-han-sans@$FS_VERSION" >/dev/null
for f in *.tgz; do mkdir -p "x_$f"; tar -xzf "$f" -C "x_$f"; done
ORT="$(ls -d x_onnxruntime-web-*)/package/dist"
mkdir -p "$WWW/lib" "$WWW/fonts"
cp "$ORT/ort.wasm.min.mjs" "$ORT/ort-wasm-simd-threaded.mjs" "$ORT/ort-wasm-simd-threaded.wasm" "$WWW/lib/"
PLEX="$(ls -d x_fontsource-ibm-plex-sans-kr-*)/package/files"
BHS="$(ls -d x_fontsource-black-han-sans-*)/package/files"
for w in 400 600; do
  cp "$PLEX/ibm-plex-sans-kr-korean-$w-normal.woff2" "$PLEX/ibm-plex-sans-kr-latin-$w-normal.woff2" "$WWW/fonts/"
done
cp "$BHS/black-han-sans-korean-400-normal.woff2" "$BHS/black-han-sans-latin-400-normal.woff2" "$WWW/fonts/"
echo "deps ready: $(du -sh "$WWW/lib" | cut -f1) runtime, $(du -sh "$WWW/fonts" | cut -f1) fonts"
