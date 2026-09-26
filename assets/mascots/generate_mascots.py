"""Generate 4 mascot PNGs (Momo tapir, Kiki hornbill) with open/closed mouths.

The _open and _close variants of a character share one SVG template; only the
mouth group string is swapped, so every other pixel is guaranteed identical.
Renders 1024x1024 PNGs with cairosvg and verifies the pixel diff bbox.
"""

import logging
import os
import tempfile
from pathlib import Path

import cairosvg

OUT_DIR = Path("/tmp/mascot-art")
SIZE = 1024
OUTLINE = "#1C1C22"
CREAM = "#F7F3E8"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mascots")


def svg_wrap(body: str, bg: str | None) -> str:
    """bg=None renders a transparent background (alpha PNG)."""
    bg_rect = f'<rect width="{SIZE}" height="{SIZE}" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
        f'viewBox="0 0 {SIZE} {SIZE}">'
        f'<g stroke-linecap="round" stroke-linejoin="round">'
        f"{bg_rect}{body}</g></svg>"
    )


# ---------------------------------------------------------------- Momo (tapir)
def momo_mouth_open() -> str:
    return (
        '<clipPath id="momo-mouth-clip">'
        '<path d="M 445 528 Q 512 548 579 528 Q 585 574 512 588 Q 439 574 445 528 Z"/>'
        "</clipPath>"
        '<path d="M 445 528 Q 512 548 579 528 Q 585 574 512 588 Q 439 574 445 528 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="11"/>'
        '<g clip-path="url(#momo-mouth-clip)">'
        '<ellipse cx="512" cy="590" rx="38" ry="22" fill="#E98A96"/>'
        '<rect x="492" y="522" width="40" height="16" rx="8" fill="#FFFFFF"/>'
        "</g>"
    )


def momo_mouth_close() -> str:
    return (
        '<path d="M 445 528 Q 512 556 579 528" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
    )


def momo_body(mouth: str) -> str:
    parts = [
        # stubby tail (behind body)
        f'<circle cx="718" cy="768" r="42" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/>',
        # feet
        f'<rect x="430" y="860" width="88" height="90" rx="42" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/>',
        f'<rect x="506" y="860" width="88" height="90" rx="42" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/>',
        # toe lines
        '<path d="M 458 900 L 458 938 M 490 900 L 490 938 M 534 900 L 534 938 M 566 900 L 566 938" '
        'stroke="#565664" stroke-width="6" fill="none"/>',
        # body
        f'<ellipse cx="512" cy="690" rx="195" ry="215" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="14"/>',
        # white saddle band + white belly, clipped to body
        '<clipPath id="momo-body-clip">'
        '<ellipse cx="512" cy="690" rx="195" ry="215"/></clipPath>',
        '<g clip-path="url(#momo-body-clip)">'
        f'<ellipse cx="512" cy="652" rx="215" ry="82" fill="{CREAM}"/>'
        f'<ellipse cx="512" cy="824" rx="128" ry="86" fill="{CREAM}"/></g>',
        # redraw body outline over the band
        f'<ellipse cx="512" cy="690" rx="195" ry="215" fill="none" stroke="{OUTLINE}" stroke-width="14"/>',
        # stubby arms
        '<g transform="rotate(14 322 700)">'
        f'<ellipse cx="322" cy="700" rx="52" ry="78" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/></g>',
        '<g transform="rotate(-14 702 700)">'
        f'<ellipse cx="702" cy="700" rx="52" ry="78" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/></g>',
        # ears (Malayan tapir: dark with white tips)
        f'<circle cx="318" cy="172" r="62" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/>',
        f'<circle cx="706" cy="172" r="62" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="12"/>',
        '<clipPath id="momo-ear-l"><circle cx="318" cy="172" r="62"/></clipPath>',
        '<clipPath id="momo-ear-r"><circle cx="706" cy="172" r="62"/></clipPath>',
        f'<g clip-path="url(#momo-ear-l)"><ellipse cx="310" cy="122" rx="52" ry="34" fill="{CREAM}"/></g>',
        f'<g clip-path="url(#momo-ear-r)"><ellipse cx="714" cy="122" rx="52" ry="34" fill="{CREAM}"/></g>',
        # head
        f'<ellipse cx="512" cy="375" rx="252" ry="230" fill="#2F2F38" stroke="{OUTLINE}" stroke-width="14"/>',
        # muzzle
        '<ellipse cx="512" cy="492" rx="142" ry="88" fill="#45454F"/>',
        '<ellipse cx="474" cy="468" rx="11" ry="16" fill="#262626"/>',
        '<ellipse cx="550" cy="468" rx="11" ry="16" fill="#262626"/>',
        # eyes
        '<ellipse cx="418" cy="362" rx="40" ry="50" fill="#FFFFFF"/>',
        '<ellipse cx="606" cy="362" rx="40" ry="50" fill="#FFFFFF"/>',
        '<circle cx="418" cy="366" r="21" fill="#262626"/>',
        '<circle cx="606" cy="366" r="21" fill="#262626"/>',
        '<circle cx="427" cy="352" r="9" fill="#FFFFFF"/>',
        '<circle cx="615" cy="352" r="9" fill="#FFFFFF"/>',
        '<circle cx="408" cy="376" r="4" fill="#FFFFFF"/>',
        '<circle cx="596" cy="376" r="4" fill="#FFFFFF"/>',
        # blush
        '<ellipse cx="352" cy="462" rx="42" ry="24" fill="#EFA3AC" opacity="0.55"/>',
        '<ellipse cx="672" cy="462" rx="42" ry="24" fill="#EFA3AC" opacity="0.55"/>',
        mouth,
    ]
    return "".join(parts)


# ------------------------------------------------------------------ Kiki (hornbill)
def kiki_beak_lower(dx: int = 0, dy: int = 0) -> str:
    return (
        f'<g transform="translate({dx} {dy})">'
        '<path d="M 442 442 Q 476 468 512 468 Q 548 468 582 442 Q 604 458 592 488 '
        'Q 562 516 512 516 Q 462 516 432 488 Q 420 458 442 442 Z" '
        f'fill="#F2A93B" stroke="{OUTLINE}" stroke-width="12"/></g>'
    )


def kiki_beak_upper() -> str:
    return (
        '<path d="M 418 372 Q 428 342 512 338 Q 596 342 606 372 Q 616 402 584 430 '
        'Q 548 458 512 458 Q 476 458 440 430 Q 408 402 418 372 Z" '
        f'fill="#F2A93B" stroke="{OUTLINE}" stroke-width="12"/>'
        '<circle cx="466" cy="386" r="8" fill="#262626" opacity="0.85"/>'
        '<circle cx="558" cy="386" r="8" fill="#262626" opacity="0.85"/>'
    )


def kiki_mouth_open() -> str:
    return (
        '<clipPath id="kiki-mouth-clip">'
        '<path d="M 438 446 Q 512 486 586 446 Q 596 528 512 548 Q 428 528 438 446 Z"/>'
        "</clipPath>"
        '<path d="M 438 446 Q 512 486 586 446 Q 596 528 512 548 Q 428 528 438 446 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="10"/>'
        '<g clip-path="url(#kiki-mouth-clip)">'
        '<ellipse cx="512" cy="514" rx="38" ry="22" fill="#E98A96"/></g>'
        + kiki_beak_lower(0, 50)
        + kiki_beak_upper()
    )


def kiki_mouth_close() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<path d="M 446 452 Q 512 480 578 452" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="10"/>'
    )


def kiki_body(mouth: str) -> str:
    parts = [
        '<g transform="translate(0 -24)">',
        # white tail fan (behind everything)
        '<g fill="#F6F2E9" stroke="%s" stroke-width="12">' % OUTLINE,
        '<g transform="rotate(-16 512 805)"><rect x="492" y="795" width="40" height="175" rx="20"/></g>',
        '<g transform="rotate(16 512 805)"><rect x="492" y="795" width="40" height="175" rx="20"/></g>',
        '<rect x="492" y="795" width="40" height="175" rx="20"/>',
        "</g>",
        # legs + feet
        '<g fill="#6B625C" stroke="%s" stroke-width="12">' % OUTLINE,
        '<rect x="442" y="845" width="44" height="100" rx="18"/>',
        '<rect x="538" y="845" width="44" height="100" rx="18"/>',
        '<ellipse cx="462" cy="950" rx="48" ry="20"/>',
        '<ellipse cx="562" cy="950" rx="48" ry="20"/>',
        "</g>",
        f'<path d="M 446 940 L 446 958 M 478 940 L 478 958 M 546 940 L 546 958 M 578 940 L 578 958" '
        f'stroke="{OUTLINE}" stroke-width="5" fill="none"/>',
        # body
        f'<ellipse cx="512" cy="640" rx="205" ry="218" fill="#3A3230" stroke="{OUTLINE}" stroke-width="14"/>',
        # wings
        '<path d="M 340 585 Q 250 620 268 720 Q 320 770 372 720 Q 380 640 340 585 Z" '
        f'fill="#4A403C" stroke="{OUTLINE}" stroke-width="12"/>',
        f'<path d="M 320 640 Q 295 680 300 715 M 348 630 Q 330 675 336 715" stroke="{OUTLINE}" '
        'stroke-width="6" fill="none"/>',
        '<path d="M 684 585 Q 774 620 756 720 Q 704 770 652 720 Q 644 640 684 585 Z" '
        f'fill="#4A403C" stroke="{OUTLINE}" stroke-width="12"/>',
        f'<path d="M 704 640 Q 729 680 724 715 M 676 630 Q 694 675 688 715" stroke="{OUTLINE}" '
        'stroke-width="6" fill="none"/>',
        # head
        f'<ellipse cx="512" cy="350" rx="238" ry="218" fill="#3A3230" stroke="{OUTLINE}" stroke-width="14"/>',
        # casque on top of beak
        '<path d="M 470 382 Q 452 300 490 240 Q 512 210 540 226 Q 560 240 552 280 '
        f'Q 544 330 556 382 Z" fill="#E8862B" stroke="{OUTLINE}" stroke-width="12"/>',
        mouth,
        # eyes (hornbill lashes)
        '<ellipse cx="402" cy="322" rx="42" ry="54" fill="#FFFFFF"/>',
        '<ellipse cx="622" cy="322" rx="42" ry="54" fill="#FFFFFF"/>',
        '<circle cx="402" cy="326" r="22" fill="#262626"/>',
        '<circle cx="622" cy="326" r="22" fill="#262626"/>',
        '<circle cx="411" cy="310" r="10" fill="#FFFFFF"/>',
        '<circle cx="631" cy="310" r="10" fill="#FFFFFF"/>',
        '<circle cx="392" cy="338" r="4" fill="#FFFFFF"/>',
        '<circle cx="612" cy="338" r="4" fill="#FFFFFF"/>',
        f'<path d="M 366 280 Q 354 266 342 260 M 384 270 Q 378 252 368 244" stroke="{OUTLINE}" stroke-width="8" fill="none"/>',
        f'<path d="M 658 280 Q 670 266 682 260 M 640 270 Q 646 252 656 244" stroke="{OUTLINE}" stroke-width="8" fill="none"/>',
        "</g>",
    ]
    return "".join(parts)


def render(svg_str: str, path: Path) -> None:
    png = cairosvg.svg2png(
        bytestring=svg_str.encode("utf-8"),
        output_width=SIZE,
        output_height=SIZE,
    )
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


def verify_pair(open_png: Path, close_png: Path, box: tuple[int, int, int, int], name: str) -> None:
    """Assert the open/close pair differs only inside the mouth region."""
    from PIL import Image  # noqa: PLC0415

    a = Image.open(open_png).convert("RGBA")
    b = Image.open(close_png).convert("RGBA")
    if a.size != b.size:
        raise RuntimeError(f"{name}: size mismatch {a.size} vs {b.size}")
    diff = set()
    pa, pb = a.tobytes(), b.tobytes()
    w, h = a.size
    for y in range(h):
        row_a = pa[y * w * 4 : (y + 1) * w * 4]
        row_b = pb[y * w * 4 : (y + 1) * w * 4]
        if row_a == row_b:
            continue
        for x in range(w):
            i = x * 4
            if row_a[i : i + 4] != row_b[i : i + 4]:
                diff.add((x, y))
    if not diff:
        raise RuntimeError(f"{name}: open and close images are identical, mouth did not change")
    xs = [p[0] for p in diff]
    ys = [p[1] for p in diff]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    x0, y0, x1, y1 = box
    inside = x0 <= bbox[0] and bbox[2] <= x1 and y0 <= bbox[1] and bbox[3] <= y1
    logger.info(
        "%s: %d differing pixels, bbox=%s, confined to mouth region %s -> %s",
        name, len(diff), bbox, box, "PASS" if inside else "FAIL",
    )
    if not inside:
        raise RuntimeError(f"{name}: changes leak outside the mouth region: bbox={bbox}")


def check_presentation() -> None:
    """Check canvas size, background, centering, and mouth colors per variant."""
    from PIL import Image  # noqa: PLC0415

    expected = {
        "momo": (430, 510, 595, 600),
        "kiki": (420, 410, 610, 545),
    }
    for name, mbox in expected.items():
        for variant in ("open", "close"):
            path = OUT_DIR / f"{name}_{variant}.png"
            img = Image.open(path).convert("RGBA")
            if img.size != (SIZE, SIZE):
                raise RuntimeError(f"{path.name}: wrong size {img.size}")
            px = img.load()
            corners = [px[5, 5], px[SIZE - 6, 5], px[5, SIZE - 6], px[SIZE - 6, SIZE - 6]]
            if any(c[3] != 0 for c in corners):
                raise RuntimeError(f"{path.name}: corners not transparent: {corners}")
            # ink bbox: any pixel with alpha
            xs, ys = [], []
            for y in range(0, SIZE, 2):
                for x in range(0, SIZE, 2):
                    if px[x, y][3] > 0:
                        xs.append(x)
                        ys.append(y)
            bbox = (min(xs), min(ys), max(xs), max(ys))
            cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
            ok_pos = bbox[0] > 20 and bbox[1] > 20 and bbox[2] < SIZE - 21 and bbox[3] < SIZE - 21
            ok_center = abs(cx - SIZE / 2) < 60 and abs(cy - SIZE / 2) < 80
            logger.info(
                "%s: ink bbox=%s center=(%.0f,%.0f) margins-ok=%s centered=%s",
                path.name, bbox, cx, cy, ok_pos, ok_center,
            )
            if not (ok_pos and ok_center):
                raise RuntimeError(f"{path.name}: bad placement bbox={bbox}")
            # mouth color counts inside the mouth box
            def count(target_hex: str) -> int:
                t = tuple(int(target_hex[i : i + 2], 16) for i in (1, 3, 5))
                n = 0
                for y in range(mbox[1], mbox[3]):
                    for x in range(mbox[0], mbox[2]):
                        p = px[x, y]
                        if all(abs(p[i] - t[i]) <= 3 for i in range(3)):
                            n += 1
                return n

            maroon = count("#7A3B44")
            tongue = count("#E98A96")
            if variant == "open":
                ok = maroon > 200 and tongue > 30
            else:
                ok = maroon < 20 and tongue < 20
            logger.info(
                "%s: mouth box maroon=%d tongue=%d -> %s",
                path.name, maroon, tongue, "PASS" if ok else "FAIL",
            )
            if not ok:
                raise RuntimeError(f"{path.name}: mouth color check failed")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("momo_open.png", momo_body(momo_mouth_open())),
        ("momo_close.png", momo_body(momo_mouth_close())),
        ("kiki_open.png", kiki_body(kiki_mouth_open())),
        ("kiki_close.png", kiki_body(kiki_mouth_close())),
    ]
    for filename, body in jobs:
        svg_path = OUT_DIR / filename.replace(".png", ".svg")
        svg_str = svg_wrap(body, None)
        svg_path.write_text(svg_str, encoding="utf-8")
        render(svg_str, OUT_DIR / filename)
    verify_pair(
        OUT_DIR / "momo_open.png", OUT_DIR / "momo_close.png",
        (340, 460, 684, 640), "momo",
    )
    verify_pair(
        OUT_DIR / "kiki_open.png", OUT_DIR / "kiki_close.png",
        (340, 360, 684, 620), "kiki",
    )
    check_presentation()
    logger.info("done: 4 PNGs in %s", OUT_DIR)


if __name__ == "__main__":
    main()
