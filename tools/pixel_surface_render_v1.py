"""Compile a TrixelSurface (trixel/pixel_geometry/pixel_surface_v1.py)
into a raster Canvas/Image -- ALWAYS a disposable, regenerable
projection, never the authoritative object.

    EDITABLE TRIXEL DATA (pixel_surface_v1.py)
            -> compiled only (THIS MODULE) ->
    derived render texture (disposable)

Delete every image this module writes and build_trixel_surface_identity_
proof.py (or the gate) can rebuild them byte-for-byte from a surface.json
alone -- that regenerability is the actual claim under test, so this
module must never read back its own PNG output as an input to anything.

render_uniform_atlas() requires one shared density across every cell in
the footprint. A true non-uniform atlas packer (different pixel
allocation per cell density, sharing one raster) is a real follow-up this
proof does not attempt -- documented here rather than silently assumed,
matching this ladder's practice of naming a scope boundary instead of
faking generality (e.g. the closed-wrap seam only ever handling the one
first/last-column case, per adjacency_v1.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import cell_addresses
from trixel.pixel_geometry.cell_atlas_layout_v1 import cell_atlas_rect, uniform_atlas_size
from trixel.pixel_geometry.pixel_surface_v1 import cell_density, cell_recipe, edits_for_cell
from trixel.trixel_recipe_renderer import Canvas
from tools.recipe_pixel_atlas_v1 import canvas_to_image, render_recipe_canvas


def render_cell_tile(surface: dict, cell_address: tuple[int, int]) -> Canvas:
    """Render one cell's tile fresh: its recipe's base artwork at the
    cell's CURRENT density, then apply every recorded edit on top by
    converting its density-independent fractional position back into a
    pixel index at this density. Edits are applied in list order, so a
    later edit at the same resulting pixel wins -- "last wins," the same
    rule any ordinary paint history follows."""
    density = cell_density(surface, cell_address)
    recipe_path = REPO_ROOT / cell_recipe(surface, cell_address)
    canvas = render_recipe_canvas(recipe_path, tile_px=density)
    for edit in edits_for_cell(surface, cell_address):
        px = min(density - 1, max(0, int(edit["u_frac"] * density)))
        py = min(density - 1, max(0, int(edit["v_frac"] * density)))
        canvas.set_pixel(px, py, tuple(edit["color"]))
    return canvas


def render_uniform_atlas(surface: dict, footprint: dict) -> Image.Image:
    densities = {cell_density(surface, addr) for addr in cell_addresses(footprint)}
    if len(densities) != 1:
        raise ValueError(
            "render_uniform_atlas requires one shared density across all cells; "
            f"got {sorted(densities)} -- per-cell mixed-density atlas packing is "
            "a documented follow-up, not yet built (see this module's docstring)"
        )
    density = densities.pop()
    atlas_w, atlas_h = uniform_atlas_size(footprint, density)
    atlas = Image.new("RGB", (atlas_w, atlas_h), (0, 0, 0))
    for addr in cell_addresses(footprint):
        tile_img = canvas_to_image(render_cell_tile(surface, addr))
        left, top, _, _ = cell_atlas_rect(addr[0], addr[1], density)
        atlas.paste(tile_img, (left, top))
    return atlas
