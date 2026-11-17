#!/usr/bin/env bash
# Publishes work/ci (progress, errors, metrics) to the "ci-status" branch so it can be read with git.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -n "${GITHUB_REPOSITORY:-}" ] || { echo "not in CI, skip"; exit 0; }
TMP=$(mktemp -d)
cp -r "$ROOT/work/ci/." "$TMP/" 2>/dev/null || true
if [ -f "$TMP/log.txt" ]; then tail -n 400 "$TMP/log.txt" > "$TMP/log_tail.txt"; rm -f "$TMP/log.txt"; fi
echo "run=${GITHUB_RUN_NUMBER:-?} sha=${GITHUB_SHA:-?} job_status=${JOB_STATUS:-running} at=$(date -u +%FT%TZ)" > "$TMP/RUN.txt"
cd "$TMP"
git init -q
git checkout -q -b ci-status
git config user.name "github-actions"
git config user.email "github-actions@users.noreply.github.com"
git add -A
git commit -qm "ci status: run ${GITHUB_RUN_NUMBER:-?} ${JOB_STATUS:-running}"
git push -q -f "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" ci-status && echo "status pushed"
