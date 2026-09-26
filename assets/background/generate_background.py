"""Generate the default chalkboard background PNG (1920x1080).

Geometry matches the engine's flat board exactly (Main.tsx contract):
board inset top 40 / sides 60 / bottom 160, 24px wooden trim at the board
bottom edge, white room around it. Flat-vector style consistent with the
mascot art; deterministic, no randomness. Rendered with cairosvg.
"""

import logging
import os
import tempfile
from pathlib import Path

import cairosvg

OUT = Path("/mnt/data/work/content_engine/vendors/remotion/engine/public/background.png")
W, H = 1920, 1080
BOARD = "#2d5a3d"
BOARD_DARK = "#275036"
WOOD = "#8B4513"
WOOD_DARK = "#6E3710"
ROOM = "#FFFFFF"
OUTLINE = "#1C1C22"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("background")

# chalk smudge streaks on the board (x, y, rx, ry, rotation, opacity)
SMUDGES = [
    (300, 220, 150, 26, -8, 0.05),
    (700, 380, 190, 22, 5, 0.04),
    (1250, 260, 160, 24, -4, 0.05),
    (1550, 520, 140, 20, 7, 0.04),
    (480, 620, 180, 26, 6, 0.045),
    (1050, 700, 200, 24, -6, 0.04),
    (1500, 780, 150, 20, 4, 0.05),
    (760, 800, 130, 18, -5, 0.04),
]

# wood grain streaks on the trim (x1, x2, y, opacity)
GRAINS = [
    (80, 420, 903, 0.25),
    (500, 900, 911, 0.2),
    (980, 1350, 905, 0.25),
    (1420, 1840, 912, 0.2),
    (300, 640, 917, 0.18),
    (1100, 1560, 918, 0.18),
]


def build_svg() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        # room
        f'<rect width="{W}" height="{H}" fill="{ROOM}"/>',
        # board with dark outline, inset top 40 / sides 60 / bottom 160
        f'<rect x="54" y="34" width="{W - 108}" height="{H - 188}" rx="12" fill="{OUTLINE}"/>',
        f'<rect x="60" y="40" width="{W - 120}" height="{H - 200}" rx="8" fill="{BOARD}"/>',
    ]
    # chalk dust smudges, clipped to the board area
    parts.append('<clipPath id="board"><rect x="60" y="40" width="' f'{W - 120}" height="{H - 200}" rx="8"/></clipPath>')
    parts.append('<g clip-path="url(#board)">')
    for x, y, rx, ry, rot, op in SMUDGES:
        parts.append(
            f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" '
            f'fill="#FFFFFF" opacity="{op}" '
            f'transform="rotate({rot} {x} {y})"/>'
        )
    # faint bottom-edge chalk tray shading inside the board
    parts.append(f'<rect x="60" y="{H - 240}" width="{W - 120}" height="34" fill="{BOARD_DARK}" opacity="0.5"/>')
    parts.append("</g>")
    # wooden trim along the board bottom (matches the old 24px band)
    parts.append(f'<rect x="60" y="{H - 184}" width="{W - 120}" height="24" rx="4" fill="{WOOD}"/>')
    for x1, x2, y, op in GRAINS:
        parts.append(
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
            f'stroke="{WOOD_DARK}" stroke-width="3" opacity="{op}" stroke-linecap="round"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def render(svg_str: str, path: Path) -> None:
    png = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), output_width=W, output_height=H)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".png.tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(png)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    logger.info("wrote %s (%d bytes)", path, len(png))


def check(path: Path) -> None:
    from PIL import Image  # noqa: PLC0415

    img = Image.open(path).convert("RGB")
    if img.size != (W, H):
        raise RuntimeError(f"wrong size {img.size}")
    px = img.load()

    def near(c, t, tol=8):
        return all(abs(c[i] - t[i]) <= tol for i in range(3))

    room = (255, 255, 255)
    board = tuple(int(BOARD[i : i + 2], 16) for i in (1, 3, 5))
    wood = tuple(int(WOOD[i : i + 2], 16) for i in (1, 3, 5))
    corners = [px[5, 5], px[W - 6, 5], px[5, 5], px[W - 6, 5]]
    if not all(near(c, room) for c in corners):
        raise RuntimeError(f"room corners not white: {corners}")
    if not near(px[W // 2, 300], board):
        raise RuntimeError(f"board center not {BOARD}: {px[W // 2, 300]}")
    if not near(px[200, H - 172], wood):
        raise RuntimeError(f"trim not wooden: {px[200, H - 172]}")
    logger.info("checks passed: room white, board green, trim wooden")


def main() -> None:
    path = OUT
    path.parent.mkdir(parents=True, exist_ok=True)
    render(build_svg(), path)
    check(path)
    logger.info("done: %s", path)


if __name__ == "__main__":
    main()
