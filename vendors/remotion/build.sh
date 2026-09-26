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

# TTS: real VOICEVOX audio when reachable, otherwise keep estimates
if curl -fsS --max-time 3 http://localhost:50021/version >/dev/null 2>&1; then
  echo "[remotion-vendor] TTS source: voicevox"
  (cd "$WORK" && npx ts-node scripts/generate-voices.ts && npm run sync-script)
else
  echo "[remotion-vendor] TTS source: estimate (VOICEVOX not reachable at localhost:50021)"
  echo "[remotion-vendor] audio: silent placeholder tracks, timing from character-count estimate"
fi

echo "[remotion-vendor] rendering..."
(cd "$WORK" && npx remotion render src/index.ts Main out/video.mp4)

cp "$WORK/out/video.mp4" "$OUT_DIR/video.mp4"
echo "[remotion-vendor] wrote $OUT_DIR/video.mp4"
