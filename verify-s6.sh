#!/bin/bash
set -e
cd /mnt/data/work/wayang
uv run tools/wayang.py check-templates 2>&1 | tail -6
uv run tools/wayang.py init tutorial video-tutorial-verify 2>&1 | tail -1
uv run tools/wayang.py validate projects/video-tutorial-verify
echo "FRESH INIT OK"
uv run tools/wayang.py init-episode test-series ep-3 2>&1 | tail -1
