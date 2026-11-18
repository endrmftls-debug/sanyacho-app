#!/usr/bin/env bash
# Downloads a trained model release (from the train-model workflow) into app/www.
# Usage: app/fetch_model.sh [tag]   (default: newest model-v* release)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WWW="$HERE/www"
REPO="${REPO:-endrmftls-debug/sanyacho-app}"
TAG="${1:-}"
if [ -z "$TAG" ]; then
  TAG="$(git -C "$HERE/.." ls-remote --tags origin 'model-v*' | sed 's#.*refs/tags/##' | sort -V | tail -1)"
fi
[ -n "$TAG" ] || { echo "no model release found"; exit 1; }
BASE="https://github.com/$REPO/releases/download/$TAG"
mkdir -p "$WWW/model" "$WWW/data" "$WWW/ref"
curl -fsSL -o "$WWW/model/plant.onnx" "$BASE/plant.onnx"
curl -fsSL -o "$WWW/data/labels.json" "$BASE/labels.json"
curl -fsSL -o "$HERE/model_report.md" "$BASE/report.md"
curl -fsSL -o /tmp/ref_photos.zip "$BASE/ref_photos.zip"
rm -rf "$WWW/ref" && mkdir -p "$WWW/ref" && (cd "$WWW/ref" && unzip -q /tmp/ref_photos.zip)
echo "$TAG" > "$WWW/model/VERSION"
echo "model $TAG ready ($(du -h "$WWW/model/plant.onnx" | cut -f1))"
