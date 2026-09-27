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
ENGINE="$VENDOR_DIR/engine"
NAME="$(basename "$PROJECT_DIR")"
WORK="$VENDOR_DIR/.work/$NAME"

echo "[remotion-vendor] project: $PROJECT_DIR"
echo "[remotion-vendor] workdir: $WORK"

rm -rf "$WORK"
mkdir -p "$WORK/public/voices"

# Copy engine source (shared node_modules stays in engine/)
tar -C "$ENGINE" --exclude=node_modules --exclude=out -cf - . | tar -C "$WORK" -xf -
ln -s "$ENGINE/node_modules" "$WORK/node_modules"

# Project assets land in public/ before mapping so visual checks see them
if [ -d "$PROJECT_DIR/assets" ]; then
  cp -R "$PROJECT_DIR/assets/." "$WORK/public/"
  echo "[remotion-vendor] copied project assets -> public/"
fi

# Canonical YAML -> engine configs + estimate durations + silent placeholder wavs
node "$VENDOR_DIR/scripts/map-project.mjs" "$PROJECT_DIR" "$WORK"

# Generate engine sources from the mapped configs
(cd "$WORK" && npm run sync)

echo "[remotion-vendor] rendering..."
(cd "$WORK" && npx remotion render src/index.ts Main out/video.mp4)

# The duration guard is platform-owned: OUT_DIR carries expected-seconds.txt;
# tools/wayang.py compares it against the render after this script exits.
cp "$WORK/expected-seconds.txt" "$OUT_DIR/expected-seconds.txt"

cp "$WORK/timeline.json" "$OUT_DIR/timeline.json"
cp "$WORK/out/video.mp4" "$OUT_DIR/video.mp4"
echo "[remotion-vendor] wrote $OUT_DIR/video.mp4"
