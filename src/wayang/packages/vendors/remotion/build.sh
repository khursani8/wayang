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

# Lipsync schedule (optional): consumed by scripts/sync-script.ts to drive the
# mouth art. Absent on draft/estimate renders; the fixed mouth clock applies.
cp "$PROJECT_DIR/voices/lipsync.json" "$WORK/public/voices/" 2>/dev/null || true

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

# Incremental-render modes (see docs/vendor-contract.md):
#   WAYANG_PLAN_ONLY=1        map only; write timeline/expected, render nothing
#   WAYANG_RENDER_FRAMES=A-B  render frames A..B (inclusive) to span.mp4
DRAFT_FLAGS=""
if [ "${WAYANG_DRAFT:-0}" = "1" ]; then
  DRAFT_FLAGS="--scale=0.5"
  echo "[remotion-vendor] draft mode: --scale=0.5"
fi
RANGE_FLAGS=""
OUT_NAME="video.mp4"
if [ -n "${WAYANG_RENDER_FRAMES:-}" ]; then
  RANGE_FLAGS="--frames=${WAYANG_RENDER_FRAMES}"
  OUT_NAME="span.mp4"
  echo "[remotion-vendor] span mode: frames ${WAYANG_RENDER_FRAMES} -> ${OUT_NAME}"
fi

if [ "${WAYANG_PLAN_ONLY:-0}" = "1" ]; then
  echo "[remotion-vendor] plan-only: mapped timeline, no render"
else
  # Generate engine sources from the mapped configs
  (cd "$WORK" && npm run sync)
  echo "[remotion-vendor] rendering..."
  (cd "$WORK" && npx remotion render src/index.ts Main "out/$OUT_NAME" $DRAFT_FLAGS $RANGE_FLAGS)
  cp "$WORK/out/$OUT_NAME" "$OUT_DIR/$OUT_NAME"
fi

# The duration guard is platform-owned: OUT_DIR carries expected-seconds.txt;
# tools/wayang.py compares it against the render after this script exits.
# Both plan-only and span modes emit the full-project timeline: the mapper
# computes it from the voice manifest, independent of the rendered range.
cp "$WORK/expected-seconds.txt" "$OUT_DIR/expected-seconds.txt"

cp "$WORK/timeline.json" "$OUT_DIR/timeline.json"
echo "[remotion-vendor] wrote $OUT_DIR/$OUT_NAME + timeline.json"
