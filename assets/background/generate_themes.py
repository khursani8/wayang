"""Generate the background theme set (1920x1080 PNGs).

Same pipeline as the chalkboard: flat-vector SVG, deterministic geometry,
rendered with cairosvg, pixel-probed after render. One builder per theme.
"""

import logging
import os
import tempfile
from pathlib import Path

import cairosvg

OUT = Path(__file__).resolve().parent.parent / "backgrounds"
W, H = 1920, 1080

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("themes")


def save(name: str, svg: str, checks: list) -> None:
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=W, output_height=H)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    fd, tmp = tempfile.mkstemp(dir=str(OUT), suffix=".png.tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(png)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    from PIL import Image

    img = Image.open(path).convert("RGB")
    if img.size != (W, H):
        raise RuntimeError(f"{name}: wrong size {img.size}")
    px = img.load()
    for x, y, hexc, tol in checks:
        want = tuple(int(hexc[i : i + 2], 16) for i in (1, 3, 5))
        got = px[x, y]
        if not all(abs(got[i] - want[i]) <= tol for i in range(3)):
            raise RuntimeError(f"{name}: probe ({x},{y}) got {got} want {want} (tol {tol})")
    logger.info("%s: %d bytes, %d probe(s) passed", name, len(png), len(checks))


def svg_wrap(body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f"<defs>{defs}</defs>{body}</svg>"
    )


def whiteboard():
    body = (
        f'<rect width="{W}" height="{H}" fill="#FDFDFB"/>'
        f'<rect x="40" y="40" width="{W - 80}" height="{H - 80}" rx="12" fill="none" stroke="#D5D8DC" stroke-width="6"/>'
        f'<rect x="{W // 2 - 220}" y="{H - 70}" width="440" height="22" rx="11" fill="#D5D8DC"/>'
    )
    return svg_wrap(body), [(5, 5, "#FDFDFB", 4), (960, 540, "#FDFDFB", 4), (960, H - 59, "#D5D8DC", 10)]


def night_sky():
    stars = [(120, 80), (260, 150), (400, 60), (520, 210), (660, 120), (800, 70), (940, 170), (1080, 90),
             (1220, 200), (1360, 60), (1500, 140), (1640, 100), (1780, 180), (200, 320), (560, 300),
             (880, 260), (1160, 330), (1420, 280), (1700, 340), (340, 470), (980, 430), (1300, 480)]
    parts = [f'<rect width="{W}" height="{H}" fill="#0F1B3D"/>']
    for x, y in stars:
        parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#F5F3CE" opacity="0.9"/>')
    parts.append('<circle cx="1650" cy="190" r="70" fill="#F5F3CE"/>')
    parts.append('<circle cx="1620" cy="170" r="60" fill="#0F1B3D"/>')
    parts.append(f'<ellipse cx="400" cy="{H + 140}" rx="900" ry="320" fill="#16233F"/>')
    parts.append(f'<ellipse cx="1500" cy="{H + 180}" rx="1000" ry="360" fill="#101B33"/>')
    checks = [(5, 5, "#0F1B3D", 6), (960, 560, "#0F1B3D", 6), (960, H - 40, "#101B33", 8), (1680, 220, "#F5F3CE", 12)]
    return svg_wrap("".join(parts)), checks


def kraft_paper():
    speckles = [(300, 200), (700, 340), (1100, 180), (1500, 420), (420, 620), (900, 700),
                (1300, 620), (1650, 800), (250, 850), (760, 940), (1180, 880), (1550, 960)]
    parts = [f'<rect width="{W}" height="{H}" fill="#C9A66B"/>']
    for x, y in speckles:
        parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#A9834F" opacity="0.6"/>')
    parts.append(f'<rect x="26" y="26" width="{W - 52}" height="{H - 52}" fill="none" stroke="#A9834F" stroke-width="12" opacity="0.8"/>')
    checks = [(5, 5, "#C9A66B", 8), (960, 540, "#C9A66B", 8), (26, 26, "#A9834F", 16)]
    return svg_wrap("".join(parts)), checks


def batik():
    parts = [f'<rect width="{W}" height="{H}" fill="#F5EDD8"/>']
    for band_y in (0, H - 90):
        parts.append(f'<rect x="0" y="{band_y}" width="{W}" height="90" fill="#F0E6CC"/>')
        for x in range(80, W, 160):
            cy = band_y + 45
            for i in range(6):
                import math
                a = i * 60
                px_ = x + 18 * math.cos(math.radians(a))
                py_ = cy + 18 * math.sin(math.radians(a))
                parts.append(f'<ellipse cx="{px_:.0f}" cy="{py_:.0f}" rx="10" ry="6" fill="#8D6E3A" transform="rotate({a} {px_:.0f} {py_:.0f})"/>')
            parts.append(f'<circle cx="{x}" cy="{cy}" r="9" fill="#A63D2F"/>')
    checks = [(960, 540, "#F5EDD8", 6), (160, 45, "#F0E6CC", 8), (80, 45, "#A63D2F", 16)]
    return svg_wrap("".join(parts)), checks


def notebook():
    parts = [f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    for y in range(140, H, 96):
        parts.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#B8D8F0" stroke-width="3"/>')
    parts.append(f'<line x1="150" y1="0" x2="150" y2="{H}" stroke="#E57373" stroke-width="4"/>')
    checks = [(5, 5, "#FFFFFF", 4), (960, 132, "#FFFFFF", 6), (960, 140, "#B8D8F0", 12)]
    return svg_wrap("".join(parts)), checks


def sunrise():
    defs = (
        '<linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FFB74D"/>'
        '<stop offset="0.55" stop-color="#FFE0B2"/>'
        '<stop offset="1" stop-color="#B3E5FC"/>'
        "</linearGradient>"
    )
    body = f'<rect width="{W}" height="{H}" fill="url(#g)"/>'
    checks = [(960, 40, "#FFB74D", 14), (960, 540, "#FFE0B2", 14), (960, H - 40, "#B3E5FC", 14)]
    return svg_wrap(body, defs), checks


def studio():
    defs = (
        '<radialGradient id="g" cx="0.5" cy="0.40" r="0.85">'
        '<stop offset="0" stop-color="#FFFFFF"/>'
        '<stop offset="0.55" stop-color="#E3E8EC"/>'
        '<stop offset="1" stop-color="#9FB0BA"/>'
        "</radialGradient>"
    )
    body = [
        f'<rect width="{W}" height="{H}" fill="url(#g)"/>',
        # stage floor: darker band across the lower third
        f'<rect x="0" y="{int(H * 0.72)}" width="{W}" height="{H - int(H * 0.72)}" fill="#B7C4CC"/>',
        f'<rect x="0" y="{int(H * 0.72)}" width="{W}" height="8" fill="#8FA1AC"/>',
        # spotlight pools on the floor
        '<ellipse cx="640" cy="980" rx="420" ry="60" fill="#DDE5EA" opacity="0.7"/>',
        '<ellipse cx="1400" cy="1000" rx="380" ry="54" fill="#DDE5EA" opacity="0.7"/>',
    ]
    body = "".join(body)
    checks = [(960, 300, "#FFFFFF", 10), (30, 30, "#CAD4DB", 10), (60, 1000, "#B7C4CC", 14)]
    return svg_wrap(body, defs), checks


def riverbank():
    parts = [
        f'<rect width="{W}" height="600" fill="#BBDEFB"/>',
        '<ellipse cx="500" cy="150" rx="140" ry="40" fill="#FFFFFF" opacity="0.9"/>',
        '<ellipse cx="1400" cy="220" rx="170" ry="46" fill="#FFFFFF" opacity="0.9"/>',
        f'<rect y="600" width="{W}" height="240" fill="#4FC3F7"/>',
        f'<rect y="840" width="{W}" height="{H - 840}" fill="#81C784"/>',
    ]
    for y in (660, 720, 780):
        parts.append(f'<line x1="120" y1="{y}" x2="700" y2="{y}" stroke="#81D4FA" stroke-width="4" stroke-linecap="round"/>')
        parts.append(f'<line x1="1100" y1="{y + 30}" x2="1750" y2="{y + 30}" stroke="#81D4FA" stroke-width="4" stroke-linecap="round"/>')
    checks = [(960, 200, "#BBDEFB", 8), (960, 700, "#4FC3F7", 8), (960, 1000, "#81C784", 8)]
    return svg_wrap("".join(parts)), checks


def slate():
    smudges = [(300, 220, 150, 26, -8), (700, 380, 190, 22, 5), (1250, 260, 160, 24, -4),
               (480, 620, 180, 26, 6), (1050, 700, 200, 24, -6), (1500, 780, 150, 20, 4)]
    parts = [f'<rect width="{W}" height="{H}" fill="#263238"/>']
    for x, y, rx, ry, rot in smudges:
        parts.append(
            f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#FFFFFF" opacity="0.05" '
            f'transform="rotate({rot} {x} {y})"/>'
        )
    checks = [(5, 5, "#263238", 6), (960, 540, "#263238", 6)]
    return svg_wrap("".join(parts)), checks


def wood_table():
    parts = [f'<rect width="{W}" height="{H}" fill="#A1662F"/>']
    for i, y in enumerate(range(0, H, 180)):
        color = "#A1662F" if i % 2 == 0 else "#96602B"
        parts.append(f'<rect x="0" y="{y}" width="{W}" height="180" fill="{color}"/>')
        parts.append(f'<rect x="0" y="{y + 174}" width="{W}" height="6" fill="#6E4218"/>')
        for x in (240, 800, 1400):
            parts.append(f'<line x1="{x}" y1="{y + 40}" x2="{x + 420}" y2="{y + 46}" stroke="#7A4A20" stroke-width="3" opacity="0.5" stroke-linecap="round"/>')
    checks = [(960, 90, "#A1662F", 8), (960, 270, "#96602B", 8), (960, 537, "#6E4218", 14)]
    return svg_wrap("".join(parts)), checks


def main() -> None:
    themes = {
        "whiteboard": whiteboard,
        "night-sky": night_sky,
        "kraft-paper": kraft_paper,
        "batik": batik,
        "notebook": notebook,
        "sunrise": sunrise,
        "studio": studio,
        "riverbank": riverbank,
        "slate": slate,
        "wood-table": wood_table,
    }
    for name, builder in themes.items():
        svg, checks = builder()
        save(name, svg, checks)
    logger.info("done: %d theme PNGs in %s", len(themes), OUT)


if __name__ == "__main__":
    main()
