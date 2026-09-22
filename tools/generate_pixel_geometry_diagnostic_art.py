#!/usr/bin/env python3
"""Generate a deterministic 16x16 diagnostic pixel-art asset for the pixel
art fold-vs-stretch proof.

Every pixel's origin is a rule, not a hand-placed choice, so it is exactly
reproducible and every source pixel can be traced back to why it is the
color it is:

  - a 1-pixel bright border around the full 16x16 frame
  - a vertical center line at column 8, a horizontal center line at row 8
    (these fall exactly on the hinge boundary used by the fold gate)
  - four checkerboard quadrants, each in its own distinct 2-color palette,
    so rotation/mirroring of any quadrant is immediately visible
  - one asymmetric 3-pixel marker placed only in the upper-left quadrant,
    breaking the 4-fold rotational symmetry the quadrant palettes alone
    would still leave ambiguous about orientation

No resampling of any kind is used: the image is authored at its native
16x16 resolution and saved as-is, so one PNG pixel equals one source
visual cell.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "fixtures" / "pixel_geometry" / "pixel_fold_diagnostic_16x16.png"

SIZE = 16
CENTER = 8  # column/row where the center lines fall -- matches hinge_corner_x=8

BORDER_COLOR = (255, 255, 0)        # bright yellow frame
CENTER_LINE_COLOR = (255, 255, 255)  # white cross at the hinge boundary
MARKER_COLOR = (255, 0, 255)        # bright magenta asymmetric marker

# (light, dark) palette per quadrant -- each quadrant is a visually
# distinct hue family so a rotated or mirrored quadrant is unmistakable.
QUADRANT_PALETTES = {
    "UL": ((200, 50, 50), (120, 20, 20)),     # red family
    "UR": ((50, 200, 50), (20, 120, 20)),     # green family
    "LL": ((50, 50, 200), (20, 20, 120)),     # blue family
    "LR": ((200, 140, 20), (120, 80, 10)),    # orange family
}

# Asymmetric marker: an L-shaped 3-pixel mark placed only in the
# upper-left quadrant's interior, well clear of the border and center
# lines, so no rotation or mirror of the image can reproduce it elsewhere.
MARKER_PIXELS = [(1, 1), (2, 1), (1, 2)]


def quadrant_of(x: int, y: int) -> str:
    if x < CENTER and y < CENTER:
        return "UL"
    if x >= CENTER and y < CENTER:
        return "UR"
    if x < CENTER and y >= CENTER:
        return "LL"
    return "LR"


def build_diagnostic_image() -> Image.Image:
    image = Image.new("RGB", (SIZE, SIZE))

    # 1. Base layer: alternating checker per quadrant, distinct palette.
    for y in range(SIZE):
        for x in range(SIZE):
            light, dark = QUADRANT_PALETTES[quadrant_of(x, y)]
            color = light if (x + y) % 2 == 0 else dark
            image.putpixel((x, y), color)

    # 2. Center lines (vertical at column CENTER, horizontal at row CENTER).
    for y in range(SIZE):
        image.putpixel((CENTER, y), CENTER_LINE_COLOR)
    for x in range(SIZE):
        image.putpixel((x, CENTER), CENTER_LINE_COLOR)

    # 3. Border, drawn after the center lines so it wins at the frame edge.
    for x in range(SIZE):
        image.putpixel((x, 0), BORDER_COLOR)
        image.putpixel((x, SIZE - 1), BORDER_COLOR)
    for y in range(SIZE):
        image.putpixel((0, y), BORDER_COLOR)
        image.putpixel((SIZE - 1, y), BORDER_COLOR)

    # 4. Asymmetric marker, drawn last so it always wins in its cells.
    for x, y in MARKER_PIXELS:
        image.putpixel((x, y), MARKER_COLOR)

    return image


def main() -> int:
    image = build_diagnostic_image()
    if image.size != (SIZE, SIZE):
        raise ValueError(f"diagnostic image must be exactly {SIZE}x{SIZE}, got {image.size}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT_PATH)

    reloaded = Image.open(OUT_PATH)
    reloaded.load()
    print(f"wrote {OUT_PATH}")
    print(f"size={reloaded.size} mode={reloaded.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
