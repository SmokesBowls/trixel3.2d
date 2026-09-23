"""Pure-function mapping from a footprint's cell addresses to atlas pixel
rectangles, given a per-cell tile pixel size.

This module never touches PIL, the filesystem, or a recipe. Its only job
is arithmetic: which pixel rectangle of a to-be-assembled atlas image does
each cell own, given the UV convention artwork_mapping_v1.py already
established (corner_row=0 is the footprint's top, v=1.0 -- "matching the
usual image convention where row 0 is the top of the source image").
Deliberately separate from pixel generation (tools/recipe_pixel_atlas_v1.py
calls trixel_recipe_renderer.py) and from geometry (embedding_v1.py /
compiler_v1.py) -- this file only answers "where does this cell's texture
live in a shared raster atlas," never "what color are those pixels" or
"where is this cell in 3D."
"""
from __future__ import annotations

from typing import Any


def uniform_atlas_size(footprint: dict[str, Any], tile_px: int) -> tuple[int, int]:
    """Pixel (width, height) of an atlas giving every cell an equal
    tile_px x tile_px region, laid out width cells across, height cells
    down."""
    width, height = footprint["width"], footprint["height"]
    return width * tile_px, height * tile_px


def cell_atlas_rect(x: int, row: int, tile_px: int) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) pixel rect for cell (x, row) in a
    UNIFORM atlas where every cell owns exactly tile_px x tile_px pixels.
    Pixel row 0 is the footprint's row 0 (top), the same row-0-is-top
    convention corner_uv() already uses -- so a cell's rect here lines up
    exactly with footprint_corner_uvs()'s (u, v) values for that cell's
    four corners once the atlas is treated as the UV(0,0)-(1,1) image."""
    left = x * tile_px
    top = row * tile_px
    return (left, top, left + tile_px, top + tile_px)
