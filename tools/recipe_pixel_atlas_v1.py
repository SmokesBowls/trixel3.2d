"""Bind trixel_recipe_renderer.py's proven pixel-writing machinery to a
pixel_geometry footprint's cell addresses, producing one shared atlas PNG
whose per-cell regions sit exactly where
cell_atlas_layout_v1.cell_atlas_rect() says they must.

This is the "cell-owned pixel surface" step in the chain the archaeology
pass surfaced:

    current 3.2 recipe JSON (recipes/terrain/*.json, recipes/transitions/*.json)
            -> proven pixel-writing machinery (trixel/trixel_recipe_renderer.py,
               unmodified -- Canvas + RecipeRenderer, already frozen and
               gated by gate_all_recipes_validation_contract.py /
               gate_tundra_recipe_render_contract.py)
            -> cell-owned pixel surface (this module)
            -> current 3.2 geometry (embedding_v1.py / compiler_v1.py,
               untouched -- called by the caller, never by this module)

Never imports embedding_v1, compiler_v1, or adjacency_v1 -- this module
has no opinion about geometry, only about pixels. Never imports
tools/export_trixel_capability_courtyard.py -- that tool stays scoped to
the courtyard deliverable, which remains unfrozen pending the user's own
review; no dependency runs in either direction between it and this file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.trixel_recipe_renderer import Canvas, RecipeRenderer
from trixel.pixel_geometry.addressing_v1 import cell_addresses
from trixel.pixel_geometry.cell_atlas_layout_v1 import cell_atlas_rect, uniform_atlas_size


def render_recipe_canvas(recipe_path: Path, *, tile_px: int | None = None) -> Canvas:
    """Render one recipe JSON to a Canvas via the unmodified RecipeRenderer.

    tile_px overrides the recipe's own declared canvas.width/height. This
    is not a resize of a rendered image -- it re-executes the SAME recipe
    passes against a differently-sized Canvas from the start, proving the
    passes themselves are resolution-parameterized (gradient_fill,
    noise_scatter, and h_band all already work in fractions of
    canvas.width/height, per trixel_recipe_renderer.py). Omit tile_px to
    use the recipe's own declared canvas size unchanged.
    """
    recipe = json.loads(recipe_path.read_text())
    canvas_decl = recipe.get("canvas", {"width": 16, "height": 16})
    width = tile_px if tile_px is not None else canvas_decl.get("width", 16)
    height = tile_px if tile_px is not None else canvas_decl.get("height", 16)
    canvas = Canvas(width, height)
    RecipeRenderer(canvas).execute(recipe)
    return canvas


def canvas_to_image(canvas: Canvas) -> Image.Image:
    img = Image.new("RGB", (canvas.width, canvas.height))
    flat = [tuple(canvas.pixels[y][x]) for y in range(canvas.height) for x in range(canvas.width)]
    img.putdata(flat)
    return img


def build_uniform_atlas(
    footprint: dict[str, Any],
    cell_to_recipe: dict[tuple[int, int], Path],
    *,
    tile_px: int,
    background: tuple[int, int, int] = (0, 0, 0),
) -> tuple[Image.Image, dict[tuple[int, int], Image.Image]]:
    """One shared atlas image, one tile_px x tile_px region per cell,
    placed exactly at cell_atlas_layout_v1.cell_atlas_rect(x, row, tile_px)
    -- the same rectangle artwork_mapping_v1's UV convention implies for a
    uniform grid at this tile_px. cell_to_recipe must map every footprint
    cell address to the recipe file that renders its tile, or this raises.

    Returns (atlas_image, rendered_tiles_by_recipe_path) -- the second
    value lets a caller (or a gate) re-check any cell's atlas region
    against the exact tile image that was pasted there, pixel for pixel,
    without re-deriving anything.
    """
    atlas_w, atlas_h = uniform_atlas_size(footprint, tile_px)
    atlas = Image.new("RGB", (atlas_w, atlas_h), background)

    rendered: dict[Path, Image.Image] = {}
    for addr in cell_addresses(footprint):
        if addr not in cell_to_recipe:
            raise ValueError(f"cell {addr} has no assigned recipe")
        recipe_path = cell_to_recipe[addr]
        if recipe_path not in rendered:
            rendered[recipe_path] = canvas_to_image(render_recipe_canvas(recipe_path, tile_px=tile_px))
        tile_img = rendered[recipe_path]
        x, row = addr
        left, top, _, _ = cell_atlas_rect(x, row, tile_px)
        atlas.paste(tile_img, (left, top))
    return atlas, rendered
