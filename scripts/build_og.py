#!/usr/bin/env python3
"""Build the Open Graph social share image (og.png, 1200x630).

Idempotent: overwrites og.png in the repo root.
Only run when the OG design changes — CI does not need to rebuild it.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install Pillow: pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "og.png"

W, H = 1200, 630
BG = (250, 248, 248)
INK = (26, 26, 26)
MUTED = (107, 107, 107)
ACCENT = (40, 75, 99)


def _load_font(size: int, weight: str = "regular") -> ImageFont.ImageFont:
    """Try a few common font paths for Inter/system sans."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if weight == "bold" else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Inter.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if weight == "bold" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def main() -> int:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Accent band on left
    draw.rectangle([(0, 0), (16, H)], fill=ACCENT)

    # Name
    name_font = _load_font(96, "bold")
    tagline_font = _load_font(38, "regular")
    small_font = _load_font(26, "regular")

    x = 88
    draw.text((x, 200), "Navnita Nandakumar", fill=INK, font=name_font)
    draw.text(
        (x, 336),
        "Software engineer.",
        fill=MUTED,
        font=tagline_font,
    )
    draw.text(
        (x, 388),
        "Voice AI, dev tools, and weekend projects.",
        fill=MUTED,
        font=tagline_font,
    )

    # Footer URL
    draw.text((x, H - 96), "nnavnita.com", fill=ACCENT, font=small_font)

    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
