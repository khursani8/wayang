"""Generate mascot PNGs (Momo tapir, Kiki hornbill): base mouths + emotion variants.

The _open and _close variants of a character share one SVG template; only the
mouth group string is swapped, so every other pixel is guaranteed identical.
Renders 1024x1024 PNGs with cairosvg and verifies the pixel diff bbox.

Emotion variants (happy, surprised, thinking, sad) for both characters are
rendered to /tmp/mascot-art/emotions/ the same way (identical body, swapped
eye/brow + mouth groups), pair-verified against each other and against the
base art, then deployed into the template and demo-project asset directories.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path

import cairosvg

OUT_DIR = Path("/tmp/mascot-art")
EMO_DIR = Path("/tmp/mascot-art/emotions")
ART_ROOT = Path("/mnt/data/work/content_engine")
TEMPLATE_NAMES = ("dialog", "presentation", "storytelling", "community")
EMOTIONS = ("happy", "surprised", "thinking", "sad")
SIZE = 1024
OUTLINE = "#1C1C22"
CREAM = "#F7F3E8"

# open/close diff must stay inside the mouth box; emotion-vs-base diff must
# stay inside the whole face box (eyes, brows, mouth).
EMO_DIFF_BOX = {"momo": (396, 484, 628, 636), "kiki": (404, 396, 620, 566)}
FACE_BOX = {"momo": (336, 248, 688, 644), "kiki": (330, 184, 694, 564)}

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


def momo_eyes_default() -> str:
    return (
        '<ellipse cx="418" cy="362" rx="40" ry="50" fill="#FFFFFF"/>'
        '<ellipse cx="606" cy="362" rx="40" ry="50" fill="#FFFFFF"/>'
        '<circle cx="418" cy="366" r="21" fill="#262626"/>'
        '<circle cx="606" cy="366" r="21" fill="#262626"/>'
        '<circle cx="427" cy="352" r="9" fill="#FFFFFF"/>'
        '<circle cx="615" cy="352" r="9" fill="#FFFFFF"/>'
        '<circle cx="408" cy="376" r="4" fill="#FFFFFF"/>'
        '<circle cx="596" cy="376" r="4" fill="#FFFFFF"/>'
    )


def momo_body(mouth: str, eyes: str | None = None) -> str:
    if eyes is None:
        eyes = momo_eyes_default()
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
        eyes,
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


def kiki_eyes_base() -> str:
    return (
        '<ellipse cx="402" cy="322" rx="42" ry="54" fill="#FFFFFF"/>'
        '<ellipse cx="622" cy="322" rx="42" ry="54" fill="#FFFFFF"/>'
        '<circle cx="402" cy="326" r="22" fill="#262626"/>'
        '<circle cx="622" cy="326" r="22" fill="#262626"/>'
        '<circle cx="411" cy="310" r="10" fill="#FFFFFF"/>'
        '<circle cx="631" cy="310" r="10" fill="#FFFFFF"/>'
        '<circle cx="392" cy="338" r="4" fill="#FFFFFF"/>'
        '<circle cx="612" cy="338" r="4" fill="#FFFFFF"/>'
    )


def kiki_eyes_default() -> str:
    return (
        kiki_eyes_base()
        + f'<path d="M 366 280 Q 354 266 342 260 M 384 270 Q 378 252 368 244" stroke="{OUTLINE}" stroke-width="8" fill="none"/>'
        + f'<path d="M 658 280 Q 670 266 682 260 M 640 270 Q 646 252 656 244" stroke="{OUTLINE}" stroke-width="8" fill="none"/>'
    )


def kiki_body(mouth: str, eyes: str | None = None) -> str:
    if eyes is None:
        eyes = kiki_eyes_default()
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
        eyes,
        "</g>",
    ]
    return "".join(parts)


# -------------------------------------------------------------- emotion variants
def _brow(d: str) -> str:
    return f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="10"/>'


def _arc(d: str) -> str:
    return f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="14"/>'


def momo_eyes_happy() -> str:
    return _arc("M 376 372 Q 418 330 460 372") + _arc("M 564 372 Q 606 330 648 372")


def momo_eyes_surprised() -> str:
    return (
        momo_eyes_default()
        + _brow("M 366 286 Q 416 262 466 284")
        + _brow("M 558 284 Q 608 262 658 286")
    )


def momo_eyes_thinking() -> str:
    return (
        '<ellipse cx="418" cy="362" rx="40" ry="50" fill="#FFFFFF"/>'
        '<ellipse cx="606" cy="362" rx="40" ry="50" fill="#FFFFFF"/>'
        '<circle cx="429" cy="357" r="21" fill="#262626"/>'
        '<circle cx="617" cy="357" r="21" fill="#262626"/>'
        '<circle cx="436" cy="344" r="9" fill="#FFFFFF"/>'
        '<circle cx="624" cy="344" r="9" fill="#FFFFFF"/>'
        '<circle cx="417" cy="368" r="4" fill="#FFFFFF"/>'
        '<circle cx="605" cy="368" r="4" fill="#FFFFFF"/>'
        + _brow("M 370 300 Q 418 292 466 300")
        + _brow("M 558 272 Q 608 260 658 272")
    )


def momo_eyes_sad() -> str:
    return (
        momo_eyes_default()
        + _brow("M 462 282 Q 412 288 368 306")
        + _brow("M 562 306 Q 606 288 656 282")
    )


def momo_happy_open() -> str:
    return (
        '<clipPath id="momo-happy-clip">'
        '<path d="M 432 516 Q 512 498 592 516 Q 588 566 512 582 Q 436 566 432 516 Z"/>'
        "</clipPath>"
        '<path d="M 432 516 Q 512 498 592 516 Q 588 566 512 582 Q 436 566 432 516 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="11"/>'
        '<g clip-path="url(#momo-happy-clip)">'
        '<rect x="492" y="512" width="40" height="16" rx="8" fill="#FFFFFF"/>'
        '<ellipse cx="512" cy="596" rx="36" ry="18" fill="#E98A96"/></g>'
    )


def momo_happy_close() -> str:
    return (
        '<path d="M 436 536 Q 512 590 588 536" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
    )


def momo_surprised_open() -> str:
    return (
        '<clipPath id="momo-surprised-clip">'
        '<ellipse cx="512" cy="550" rx="44" ry="44"/></clipPath>'
        '<ellipse cx="512" cy="550" rx="44" ry="44" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
        '<g clip-path="url(#momo-surprised-clip)">'
        '<ellipse cx="512" cy="576" rx="26" ry="16" fill="#E98A96"/></g>'
    )


def momo_surprised_close() -> str:
    return (
        '<ellipse cx="512" cy="552" rx="13" ry="15" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="8"/>'
    )


def momo_thinking_open() -> str:
    return (
        '<ellipse cx="512" cy="544" rx="32" ry="11" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="9"/>'
    )


def momo_thinking_close() -> str:
    return '<path d="M 476 544 L 548 544" fill="none" ' f'stroke="{OUTLINE}" stroke-width="9"/>'


def momo_sad_open() -> str:
    return (
        '<path d="M 448 578 Q 512 546 576 578 Q 550 592 512 594 Q 474 592 448 578 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="11"/>'
    )


def momo_sad_close() -> str:
    return '<path d="M 456 566 Q 512 550 568 566" fill="none" ' f'stroke="{OUTLINE}" stroke-width="10"/>'


def kiki_eyes_happy() -> str:
    return _arc("M 362 330 Q 402 288 442 330") + _arc("M 582 330 Q 622 288 662 330")


def kiki_eyes_surprised() -> str:
    return (
        kiki_eyes_base()
        + _brow("M 346 250 Q 400 226 454 248")
        + _brow("M 570 248 Q 624 226 678 250")
    )


def kiki_eyes_thinking() -> str:
    return (
        '<ellipse cx="402" cy="322" rx="42" ry="54" fill="#FFFFFF"/>'
        '<ellipse cx="622" cy="322" rx="42" ry="54" fill="#FFFFFF"/>'
        '<circle cx="414" cy="314" r="22" fill="#262626"/>'
        '<circle cx="634" cy="314" r="22" fill="#262626"/>'
        '<circle cx="423" cy="298" r="10" fill="#FFFFFF"/>'
        '<circle cx="643" cy="298" r="10" fill="#FFFFFF"/>'
        '<circle cx="404" cy="326" r="4" fill="#FFFFFF"/>'
        '<circle cx="624" cy="326" r="4" fill="#FFFFFF"/>'
        + _brow("M 348 256 Q 400 246 452 256")
        + _brow("M 572 234 Q 624 220 676 236")
    )


def kiki_eyes_sad() -> str:
    return (
        kiki_eyes_base()
        + _brow("M 450 242 Q 396 250 350 270")
        + _brow("M 574 270 Q 628 250 674 242")
    )


def kiki_surprised_open() -> str:
    d = "M 434 440 Q 512 474 590 440 Q 602 520 512 552 Q 422 520 434 440 Z"
    return (
        f'<clipPath id="kiki-surprised-clip"><path d="{d}"/></clipPath>'
        f'<path d="{d}" fill="#7A3B44" stroke="{OUTLINE}" stroke-width="10"/>'
        '<g clip-path="url(#kiki-surprised-clip)">'
        '<ellipse cx="512" cy="524" rx="34" ry="18" fill="#E98A96"/></g>'
        + kiki_beak_lower(0, 56)
        + kiki_beak_upper()
    )


def kiki_surprised_close() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<ellipse cx="512" cy="494" rx="13" ry="15" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="8"/>'
    )


def kiki_thinking_open() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<ellipse cx="512" cy="486" rx="34" ry="8" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="8"/>'
    )


def kiki_thinking_close() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<path d="M 478 486 L 546 486" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="9"/>'
    )


def kiki_sad_open() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<path d="M 462 500 Q 512 478 562 500" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="10"/>'
    )


def kiki_sad_close() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<path d="M 466 498 Q 512 490 558 498" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="9"/>'
    )


MOMO_EYES = {
    "happy": momo_eyes_happy,
    "surprised": momo_eyes_surprised,
    "thinking": momo_eyes_thinking,
    "sad": momo_eyes_sad,
}
MOMO_MOUTHS = {
    "happy": (momo_happy_open, momo_happy_close),
    "surprised": (momo_surprised_open, momo_surprised_close),
    "thinking": (momo_thinking_open, momo_thinking_close),
    "sad": (momo_sad_open, momo_sad_close),
}
KIKI_EYES = {
    "happy": kiki_eyes_happy,
    "surprised": kiki_eyes_surprised,
    "thinking": kiki_eyes_thinking,
    "sad": kiki_eyes_sad,
}
KIKI_MOUTHS = {
    "happy": (kiki_mouth_open, kiki_mouth_close),
    "surprised": (kiki_surprised_open, kiki_surprised_close),
    "thinking": (kiki_thinking_open, kiki_thinking_close),
    "sad": (kiki_sad_open, kiki_sad_close),
}


def emotion_body(character: str, emotion: str, state: str) -> str:
    """Same body as the base art; only the expression groups change."""
    eyes = (MOMO_EYES if character == "momo" else KIKI_EYES)[emotion]()
    mouths = (MOMO_MOUTHS if character == "momo" else KIKI_MOUTHS)[emotion]
    mouth = mouths[0 if state == "open" else 1]()
    if character == "momo":
        return svg_wrap(momo_body(mouth, eyes), None)
    return svg_wrap(kiki_body(mouth, eyes), None)


def check_frame(path: Path) -> None:
    """1024x1024 with transparent corners, like the base presentation check."""
    from PIL import Image  # noqa: PLC0415

    img = Image.open(path).convert("RGBA")
    if img.size != (SIZE, SIZE):
        raise RuntimeError(f"{path.name}: wrong size {img.size}")
    px = img.load()
    corners = [px[5, 5], px[SIZE - 6, 5], px[5, SIZE - 6], px[SIZE - 6, SIZE - 6]]
    if any(c[3] != 0 for c in corners):
        raise RuntimeError(f"{path.name}: corners not transparent: {corners}")


def generate_emotions() -> None:
    EMO_DIR.mkdir(parents=True, exist_ok=True)
    for character in ("momo", "kiki"):
        base_open = OUT_DIR / f"{character}_open.png"
        base_close = OUT_DIR / f"{character}_close.png"
        for emotion in EMOTIONS:
            frames = {}
            for state in ("open", "close"):
                filename = f"{character}_{emotion}_{state}.png"
                svg_str = emotion_body(character, emotion, state)
                svg_path = EMO_DIR / filename.replace(".png", ".svg")
                svg_path.write_text(svg_str, encoding="utf-8")
                out_path = EMO_DIR / filename
                render(svg_str, out_path)
                check_frame(out_path)
                frames[state] = out_path
            verify_pair(
                frames["open"], frames["close"],
                EMO_DIFF_BOX[character], f"{character}-{emotion}",
            )
            verify_pair(
                frames["open"], base_open,
                FACE_BOX[character], f"{character}-{emotion}-open-vs-base",
            )
            verify_pair(
                frames["close"], base_close,
                FACE_BOX[character], f"{character}-{emotion}-close-vs-base",
            )


def deploy_emotions() -> None:
    roots = [ART_ROOT / "templates" / name / "assets" / "images" for name in TEMPLATE_NAMES]
    roots.append(ART_ROOT / "projects" / "hf-demo" / "assets" / "images")
    copied = 0
    for character in ("momo", "kiki"):
        for emotion in EMOTIONS:
            for state in ("open", "close"):
                src = EMO_DIR / f"{character}_{emotion}_{state}.png"
                for root in roots:
                    dest_dir = root / character
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dest_dir / f"{emotion}_{state}.png")
                    copied += 1
    logger.info("deployed %d emotion PNGs to %d asset roots", copied, len(roots))


# --------------------------------------------------------------------- pipeline
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
    """Assert the two images differ only inside the given region box."""
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
        raise RuntimeError(f"{name}: images are identical, nothing changed")
    xs = [p[0] for p in diff]
    ys = [p[1] for p in diff]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    x0, y0, x1, y1 = box
    inside = x0 <= bbox[0] and bbox[2] <= x1 and y0 <= bbox[1] and bbox[3] <= y1
    logger.info(
        "%s: %d differing pixels, bbox=%s, confined to %s -> %s",
        name, len(diff), bbox, box, "PASS" if inside else "FAIL",
    )
    if not inside:
        raise RuntimeError(f"{name}: changes leak outside the region: bbox={bbox}")


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
    generate_emotions()
    deploy_emotions()
    logger.info(
        "done: 4 base PNGs in %s, 16 emotion PNGs in %s, deployed to templates + demo",
        OUT_DIR, EMO_DIR,
    )


if __name__ == "__main__":
    main()
