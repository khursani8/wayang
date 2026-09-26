#!/usr/bin/env bash
# content_engine vendor entry. Contract: build.sh PROJECT_DIR OUT_DIR
# Reads PROJECT_DIR/project.yaml (canonical), writes OUT_DIR/video.mp4.
# Idempotent: the workdir is rebuilt from scratch on every run.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: build.sh PROJECT_DIR OUT_DIR" >&2
  exit 2
fi

PROJECT_DIR="$(cd "$1" && pwd)"
OUT_DIR="$(mkdir -p "$2" && cd "$2" && pwd)"
VENDOR_DIR="$(cd "$(dirname "$0")" && pwd)"
NAME="$(basename "$PROJECT_DIR")"
WORK="$VENDOR_DIR/.work/$NAME"

echo "[hyperframes-vendor] project: $PROJECT_DIR"
echo "[hyperframes-vendor] workdir: $WORK"

rm -rf "$WORK"
mkdir -p "$WORK"

# Project voices + assets land in the workdir before mapping
if [ -d "$PROJECT_DIR/voices" ]; then cp -R "$PROJECT_DIR/voices" "$WORK/voices"; fi
if [ -d "$PROJECT_DIR/assets" ]; then cp -R "$PROJECT_DIR/assets" "$WORK/assets"; fi

# Canonical YAML -> HyperFrames composition (index.html + package.json +
# expected-seconds.txt + background/voices/images copies)
npm install --prefix "$VENDOR_DIR/scripts" --silent
node "$VENDOR_DIR/scripts/map-project.mjs" "$PROJECT_DIR" "$WORK"

echo "[hyperframes-vendor] rendering (npx hyperframes, downloads CLI on first run)..."
(cd "$WORK" && npx --yes hyperframes@latest render --output "$WORK/out.mp4" -f 30)

# Duration regression guard: rendered length must match the computed
# timeline. Tolerance 0.5s covers container rounding.
EXPECTED="$(cat "$WORK/expected-seconds.txt" 2>/dev/null || true)"
if [ -n "$EXPECTED" ]; then
  if command -v ffprobe >/dev/null 2>&1; then
    ACTUAL="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$WORK/out.mp4")"
    echo "[hyperframes-vendor] duration check: actual=${ACTUAL}s expected=${EXPECTED}s"
    ok="$(awk -v a="$ACTUAL" -v e="$EXPECTED" 'BEGIN { print (a >= e - 0.5 && a <= e + 0.5) ? 1 : 0 }')"
    if [ "$ok" != "1" ]; then
      echo "[hyperframes-vendor] ERROR: rendered duration deviates from the computed timeline" >&2
      exit 1
    fi
  else
    echo "[hyperframes-vendor] WARNING: duration guard skipped, ffprobe not found"
  fi
fi

cp "$WORK/out.mp4" "$OUT_DIR/video.mp4"
echo "[hyperframes-vendor] wrote $OUT_DIR/video.mp4"
