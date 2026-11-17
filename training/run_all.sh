#!/usr/bin/env bash
# Runs the whole training pipeline. Used by .github/workflows/train.yml
set -euo pipefail
export PYTHONUNBUFFERED=1
cd "$(dirname "$0")/pipeline"
mkdir -p ../../work/ci
log=../../work/ci/log.txt
# publish progress every 10 minutes so it can be followed from the ci-status branch
(while sleep 600; do bash ../push_status.sh >/dev/null 2>&1 || true; done) &
TICKER=$!
trap 'kill $TICKER 2>/dev/null || true' EXIT
step() { echo "===== $1 $(date -u +%H:%M:%S) =====" | tee -a "$log"; python "$1.py" 2>&1 | tee -a "$log"; }
step collect
bash ../push_status.sh || true
step embed
bash ../push_status.sh || true
step train_head
step export
step report
