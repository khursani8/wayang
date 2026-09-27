"""Generate mascot PNGs (Momo tapir, Kiki hornbill, Rimau tiger): base + emotions.

The _open and _close variants of a character share one SVG template; only the
mouth group string is swapped, so every other pixel is guaranteed identical.
Renders 1024x1024 PNGs with cairosvg and verifies the pixel diff bbox.

Emotion variants (happy, surprised, thinking, sad) for both characters are
rendered to /tmp/mascot-art/emotions/ the same way (identical body, swapped
eye/brow + mouth groups), pair-verified against each other and against the
base art, then deployed into the template and demo-project asset directories.

Rimau (chibi Malayan tiger) renders base + emotion pairs to
/tmp/mascot-art/rimau/ and deploys into the rimau-intro demo project.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path

import cairosvg

OUT_DIR = Path("/tmp/mascot-art")
EMO_DIR = Path("/tmp/mascot-art/emotions")
RIMAU_DIR = Path("/tmp/mascot-art/rimau")
ART_ROOT = Path("/mnt/data/work/wayang")
FRAMES_ROOT = ART_ROOT / "assets" / "mascots" / "frames"
TEMPLATE_NAMES = ("dialog", "presentation", "storytelling", "community")
EMOTIONS = ("happy", "surprised", "thinking", "sad")
SIZE = 1024
OUTLINE = "#1C1C22"
CREAM = "#F7F3E8"
ORANGE = "#F57C00"

# open/close diff must stay inside the mouth box; emotion-vs-base diff must
# stay inside the whole face box (eyes, brows, mouth).
EMO_DIFF_BOX = {
    "momo": (396, 484, 628, 636),
    "kiki": (404, 396, 620, 566),
    "rimau": (410, 460, 614, 610),
}
FACE_BOX = {
    "momo": (336, 248, 688, 644),
    "kiki": (330, 184, 694, 564),
    "rimau": (330, 240, 694, 615),
}

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


# ------------------------------------------------------------------ Rimau (tiger)
def rimau_mouth_open() -> str:
    return (
        '<clipPath id="rimau-mouth-clip">'
        '<path d="M 452 506 Q 512 524 572 506 Q 580 556 512 574 Q 444 556 452 506 Z"/>'
        "</clipPath>"
        '<path d="M 452 506 Q 512 524 572 506 Q 580 556 512 574 Q 444 556 452 506 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="11"/>'
        '<g clip-path="url(#rimau-mouth-clip)">'
        '<ellipse cx="512" cy="578" rx="36" ry="20" fill="#E98A96"/>'
        '<rect x="472" y="504" width="18" height="20" rx="5" fill="#FFFFFF"/>'
        '<rect x="534" y="504" width="18" height="20" rx="5" fill="#FFFFFF"/>'
        "</g>"
    )


def rimau_mouth_close() -> str:
    return (
        '<path d="M 452 506 Q 512 534 572 506" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
    )


def rimau_body(mouth: str, eyes: str | None = None) -> str:
    if eyes is None:
        # Rimau shares Momo's round chibi eye set (same face geometry).
        eyes = momo_eyes_default()
    parts = [
        # striped tail (behind body)
        f'<path d="M 676 800 Q 800 780 824 664" fill="none" stroke="{OUTLINE}" stroke-width="58"/>',
        f'<path d="M 676 800 Q 800 780 824 664" fill="none" stroke="{ORANGE}" stroke-width="34"/>',
        '<path d="M 757 751 L 778 774 M 792 708 L 820 723" '
        'stroke="#262626" stroke-width="12" fill="none"/>',
        # cream paws
        f'<rect x="430" y="860" width="88" height="90" rx="42" fill="{CREAM}" stroke="{OUTLINE}" stroke-width="12"/>',
        f'<rect x="506" y="860" width="88" height="90" rx="42" fill="{CREAM}" stroke="{OUTLINE}" stroke-width="12"/>',
        '<path d="M 458 902 L 458 938 M 490 902 L 490 938 M 534 902 L 534 938 M 566 902 L 566 938" '
        'stroke="#D8C9A6" stroke-width="6" fill="none"/>',
        # body with cream belly + side stripes, clipped
        f'<ellipse cx="512" cy="690" rx="195" ry="215" fill="{ORANGE}" stroke="{OUTLINE}" stroke-width="14"/>',
        '<clipPath id="rimau-body-clip">'
        '<ellipse cx="512" cy="690" rx="195" ry="215"/></clipPath>',
        '<g clip-path="url(#rimau-body-clip)">'
        f'<ellipse cx="512" cy="790" rx="112" ry="118" fill="{CREAM}"/>'
        '<path d="M 340 566 L 428 556 L 430 584 L 342 596 Z" fill="#262626"/>'
        '<path d="M 322 640 L 414 632 L 416 660 L 324 670 Z" fill="#262626"/>'
        '<path d="M 684 566 L 596 556 L 594 584 L 682 596 Z" fill="#262626"/>'
        '<path d="M 702 640 L 610 632 L 608 660 L 700 670 Z" fill="#262626"/>'
        '<path d="M 330 796 L 408 804 L 406 832 L 332 824 Z" fill="#262626"/>'
        '<path d="M 694 796 L 616 804 L 618 832 L 692 824 Z" fill="#262626"/></g>',
        # redraw body outline over the clipped fills
        f'<ellipse cx="512" cy="690" rx="195" ry="215" fill="none" stroke="{OUTLINE}" stroke-width="14"/>',
        # stubby arms
        '<g transform="rotate(14 322 700)">'
        f'<ellipse cx="322" cy="700" rx="52" ry="78" fill="{ORANGE}" stroke="{OUTLINE}" stroke-width="12"/></g>',
        '<g transform="rotate(-14 702 700)">'
        f'<ellipse cx="702" cy="700" rx="52" ry="78" fill="{ORANGE}" stroke="{OUTLINE}" stroke-width="12"/></g>',
        # round ears with cream inner
        f'<circle cx="330" cy="170" r="60" fill="{ORANGE}" stroke="{OUTLINE}" stroke-width="12"/>',
        f'<circle cx="694" cy="170" r="60" fill="{ORANGE}" stroke="{OUTLINE}" stroke-width="12"/>',
        '<clipPath id="rimau-ear-l"><circle cx="330" cy="170" r="60"/></clipPath>',
        '<clipPath id="rimau-ear-r"><circle cx="694" cy="170" r="60"/></clipPath>',
        f'<g clip-path="url(#rimau-ear-l)"><ellipse cx="322" cy="120" rx="50" ry="32" fill="{CREAM}"/></g>',
        f'<g clip-path="url(#rimau-ear-r)"><ellipse cx="702" cy="120" rx="50" ry="32" fill="{CREAM}"/></g>',
        # head
        f'<ellipse cx="512" cy="372" rx="246" ry="224" fill="{ORANGE}" stroke="{OUTLINE}" stroke-width="14"/>',
        # forehead stripes
        '<path d="M 500 176 L 512 248 L 524 176 Z" fill="#262626"/>',
        '<path d="M 434 184 L 446 240 L 462 178 Z" fill="#262626"/>',
        '<path d="M 590 184 L 578 240 L 562 178 Z" fill="#262626"/>',
        # cheek stripes, clipped to the head
        '<clipPath id="rimau-head-clip">'
        '<ellipse cx="512" cy="372" rx="246" ry="224"/></clipPath>',
        '<g clip-path="url(#rimau-head-clip)">'
        '<path d="M 262 366 L 348 358 L 350 384 L 264 394 Z" fill="#262626"/>'
        '<path d="M 272 416 L 344 410 L 346 434 L 274 442 Z" fill="#262626"/>'
        '<path d="M 762 366 L 676 358 L 674 384 L 760 394 Z" fill="#262626"/>'
        '<path d="M 752 416 L 680 410 L 678 434 L 750 442 Z" fill="#262626"/></g>',
        # redraw head outline over the cheek stripes
        f'<ellipse cx="512" cy="372" rx="246" ry="224" fill="none" stroke="{OUTLINE}" stroke-width="14"/>',
        # cream muzzle, nose, whisker dots
        f'<ellipse cx="512" cy="470" rx="118" ry="74" fill="{CREAM}"/>',
        '<path d="M 486 448 Q 512 438 538 448 Q 546 458 534 472 Q 522 482 512 482 '
        'Q 502 482 490 472 Q 478 458 486 448 Z" fill="#262626"/>',
        f'<path d="M 512 482 L 512 500" stroke="{OUTLINE}" stroke-width="8" fill="none"/>',
        '<g fill="#262626" opacity="0.45">'
        '<circle cx="444" cy="464" r="4"/><circle cx="434" cy="482" r="4"/>'
        '<circle cx="580" cy="464" r="4"/><circle cx="590" cy="482" r="4"/></g>',
        # eyes
        eyes,
        # blush
        '<ellipse cx="360" cy="468" rx="40" ry="22" fill="#EFA3AC" opacity="0.55"/>',
        '<ellipse cx="664" cy="468" rx="40" ry="22" fill="#EFA3AC" opacity="0.55"/>',
        mouth,
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
        + '<ellipse cx="404" cy="312" rx="9" ry="13" fill="#7EB8E0"/>'
        + '<ellipse cx="407" cy="306" rx="3" ry="5" fill="#C9E8F5"/>'
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
    d = "M 458 494 Q 512 524 566 494 Q 560 542 512 554 Q 464 542 458 494 Z"
    return (
        f'<clipPath id="kiki-sad-clip"><path d="{d}"/></clipPath>'
        f'<path d="{d}" fill="#7A3B44" stroke="{OUTLINE}" stroke-width="10"/>'
        '<g clip-path="url(#kiki-sad-clip)">'
        '<ellipse cx="512" cy="548" rx="34" ry="16" fill="#E98A96"/></g>'
        + kiki_beak_lower(0, 42)
        + kiki_beak_upper()
    )


def kiki_sad_close() -> str:
    return (
        kiki_beak_lower()
        + kiki_beak_upper()
        + '<path d="M 462 504 Q 512 484 562 504" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
    )


def rimau_happy_open() -> str:
    return (
        '<clipPath id="rimau-happy-clip">'
        '<path d="M 432 496 Q 512 478 592 496 Q 588 546 512 562 Q 436 546 432 496 Z"/>'
        "</clipPath>"
        '<path d="M 432 496 Q 512 478 592 496 Q 588 546 512 562 Q 436 546 432 496 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="11"/>'
        '<g clip-path="url(#rimau-happy-clip)">'
        '<rect x="492" y="492" width="40" height="16" rx="8" fill="#FFFFFF"/>'
        '<ellipse cx="512" cy="576" rx="36" ry="18" fill="#E98A96"/></g>'
    )


def rimau_happy_close() -> str:
    return (
        '<path d="M 436 516 Q 512 570 588 516" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
    )


def rimau_surprised_open() -> str:
    return (
        '<clipPath id="rimau-surprised-clip">'
        '<ellipse cx="512" cy="528" rx="42" ry="42"/></clipPath>'
        '<ellipse cx="512" cy="528" rx="42" ry="42" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="11"/>'
        '<g clip-path="url(#rimau-surprised-clip)">'
        '<ellipse cx="512" cy="552" rx="24" ry="14" fill="#E98A96"/></g>'
    )


def rimau_surprised_close() -> str:
    return (
        '<ellipse cx="512" cy="530" rx="13" ry="15" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="8"/>'
    )


def rimau_thinking_open() -> str:
    return (
        '<ellipse cx="512" cy="524" rx="32" ry="11" fill="#7A3B44" '
        f'stroke="{OUTLINE}" stroke-width="9"/>'
    )


def rimau_thinking_close() -> str:
    return f'<path d="M 476 524 L 548 524" fill="none" stroke="{OUTLINE}" stroke-width="9"/>'


def rimau_sad_open() -> str:
    return (
        '<path d="M 448 560 Q 512 528 576 560 Q 552 574 512 576 Q 472 574 448 560 Z" '
        f'fill="#7A3B44" stroke="{OUTLINE}" stroke-width="11"/>'
    )


def rimau_sad_close() -> str:
    return f'<path d="M 456 548 Q 512 532 568 548" fill="none" stroke="{OUTLINE}" stroke-width="10"/>'


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
# Rimau reuses Momo's round eye set for every emotion (same face geometry).
RIMAU_EYES = MOMO_EYES
RIMAU_MOUTHS = {
    "happy": (rimau_happy_open, rimau_happy_close),
    "surprised": (rimau_surprised_open, rimau_surprised_close),
    "thinking": (rimau_thinking_open, rimau_thinking_close),
    "sad": (rimau_sad_open, rimau_sad_close),
}

CHARACTERS = {
    "momo": (momo_body, MOMO_EYES, MOMO_MOUTHS),
    "kiki": (kiki_body, KIKI_EYES, KIKI_MOUTHS),
    "rimau": (rimau_body, RIMAU_EYES, RIMAU_MOUTHS),
}


def emotion_body(character: str, emotion: str, state: str) -> str:
    """Same body as the base art; only the expression groups change."""
    body, eyes_map, mouths_map = CHARACTERS[character]
    eyes = eyes_map[emotion]()
    mouth = mouths_map[emotion][0 if state == "open" else 1]()
    return svg_wrap(body(mouth, eyes), None)


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


def deploy_base() -> None:
    """Copy the base lip-flap pairs into the canonical frames root."""
    copied = 0
    for character in ("momo", "kiki"):
        for state in ("open", "close"):
            src = OUT_DIR / f"{character}_{state}.png"
            dest_dir = FRAMES_ROOT / character
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest_dir / f"mouth_{state}.png")
            copied += 1
    logger.info("deployed %d base PNGs to %s", copied, FRAMES_ROOT)


def deploy_emotions() -> None:
    copied = 0
    for character in ("momo", "kiki"):
        for emotion in EMOTIONS:
            for state in ("open", "close"):
                src = EMO_DIR / f"{character}_{emotion}_{state}.png"
                dest_dir = FRAMES_ROOT / character
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest_dir / f"{emotion}_{state}.png")
                copied += 1
    logger.info("deployed %d emotion PNGs to %s", copied, FRAMES_ROOT)


RIMAU_DEPLOY_NAMES = {
    "rimau_mouth_open.png": "mouth_open.png",
    "rimau_mouth_close.png": "mouth_close.png",
    "rimau_happy_open.png": "happy_open.png",
    "rimau_happy_close.png": "happy_close.png",
    "rimau_surprised_open.png": "surprised_open.png",
    "rimau_surprised_close.png": "surprised_close.png",
    "rimau_thinking_open.png": "thinking_open.png",
    "rimau_thinking_close.png": "thinking_close.png",
    "rimau_sad_open.png": "sad_open.png",
    "rimau_sad_close.png": "sad_close.png",
}


def generate_rimau() -> None:
    RIMAU_DIR.mkdir(parents=True, exist_ok=True)
    base = {}
    for state in ("open", "close"):
        mouth = rimau_mouth_open() if state == "open" else rimau_mouth_close()
        filename = f"rimau_mouth_{state}.png"
        svg_str = svg_wrap(rimau_body(mouth), None)
        svg_path = RIMAU_DIR / filename.replace(".png", ".svg")
        svg_path.write_text(svg_str, encoding="utf-8")
        out_path = RIMAU_DIR / filename
        render(svg_str, out_path)
        check_frame(out_path)
        base[state] = out_path
    verify_pair(
        base["open"], base["close"], EMO_DIFF_BOX["rimau"], "rimau",
    )
    check_character_presentation(
        "rimau", base["open"], base["close"], (430, 490, 594, 585),
    )
    for emotion in EMOTIONS:
        frames = {}
        for state in ("open", "close"):
            filename = f"rimau_{emotion}_{state}.png"
            svg_str = emotion_body("rimau", emotion, state)
            svg_path = RIMAU_DIR / filename.replace(".png", ".svg")
            svg_path.write_text(svg_str, encoding="utf-8")
            out_path = RIMAU_DIR / filename
            render(svg_str, out_path)
            check_frame(out_path)
            frames[state] = out_path
        verify_pair(
            frames["open"], frames["close"],
            EMO_DIFF_BOX["rimau"], f"rimau-{emotion}",
        )
        verify_pair(
            frames["open"], base["open"],
            FACE_BOX["rimau"], f"rimau-{emotion}-open-vs-base",
        )
        verify_pair(
            frames["close"], base["close"],
            FACE_BOX["rimau"], f"rimau-{emotion}-close-vs-base",
        )


def deploy_rimau() -> None:
    dest_dir = FRAMES_ROOT / "rimau"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src_name, dest_name in RIMAU_DEPLOY_NAMES.items():
        shutil.copyfile(RIMAU_DIR / src_name, dest_dir / dest_name)
    logger.info("deployed %d rimau PNGs to %s", len(RIMAU_DEPLOY_NAMES), dest_dir)


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


def check_character_presentation(
    name: str,
    open_path: Path,
    close_path: Path,
    mbox: tuple[int, int, int, int],
) -> None:
    """Check canvas size, background, centering, and mouth colors per variant."""
    from PIL import Image  # noqa: PLC0415

    for variant, path in (("open", open_path), ("close", close_path)):
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


def check_presentation() -> None:
    expected = {
        "momo": (430, 510, 595, 600),
        "kiki": (420, 410, 610, 545),
    }
    for name, mbox in expected.items():
        check_character_presentation(
            name, OUT_DIR / f"{name}_open.png", OUT_DIR / f"{name}_close.png", mbox,
        )


def main() -> None:
    deploy_base()
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
    generate_rimau()
    deploy_rimau()
    logger.info(
        "done: 4 base PNGs in %s, 16 emotion PNGs in %s, 10 rimau PNGs in %s",
        OUT_DIR, EMO_DIR, RIMAU_DIR,
    )


if __name__ == "__main__":
    main()
