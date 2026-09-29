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
cp "$PROJECT_DIR/voices/lipsync.json" "$WORK/voices/" 2>/dev/null || true
if [ -d "$PROJECT_DIR/assets" ]; then cp -R "$PROJECT_DIR/assets" "$WORK/assets"; fi

# Canonical YAML -> HyperFrames composition (index.html + package.json +
# expected-seconds.txt + background/voices/images copies)
npm install --prefix "$VENDOR_DIR/scripts" --silent
node "$VENDOR_DIR/scripts/map-project.mjs" "$PROJECT_DIR" "$WORK"

DRAFT_FLAGS=""
if [ "${WAYANG_DRAFT:-0}" = "1" ]; then
  DRAFT_FLAGS="-q draft"
  echo "[hyperframes-vendor] draft mode: -q draft"
fi
echo "[hyperframes-vendor] rendering (npx hyperframes, downloads CLI on first run)..."
(cd "$WORK" && npx --yes hyperframes@latest render --output "$WORK/out.mp4" -f 30 $DRAFT_FLAGS)

# The duration guard is platform-owned: OUT_DIR carries expected-seconds.txt;
# tools/wayang.py compares it against the render after this script exits.
cp "$WORK/expected-seconds.txt" "$OUT_DIR/expected-seconds.txt"

cp "$WORK/timeline.json" "$OUT_DIR/timeline.json"
cp "$WORK/out.mp4" "$OUT_DIR/video.mp4"
echo "[hyperframes-vendor] wrote $OUT_DIR/video.mp4"
