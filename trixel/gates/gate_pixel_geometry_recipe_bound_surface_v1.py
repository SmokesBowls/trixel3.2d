#!/usr/bin/env python3
"""First 3.2d visual-object proof, gated: prove that binding real
recipe-rendered pixels onto pixel_geometry's cell/UV addressing never
touches geometry, that every cell's atlas region holds exactly the
correct recipe's pixels (no resampling, no cross-contamination between
grass and dirt), that the binding is deterministic, and -- as a toxic
control matching this ladder's established adversarial-proof discipline
-- that a deliberately WRONG atlas placement is actually detectable by
the same pixel-exact comparison this gate relies on.

geometry (embed_flat / compile_footprint)     PROVEN, FROZEN (trials 1-12)
recipe pixel writing (trixel_recipe_renderer)  PROVEN, FROZEN (recipe gates)
cell-owned pixel binding                       THIS GATE

Required result:
    GEOMETRY_UNCHANGED_BY_PIXEL_BINDING   true
    EVERY_CELL_ATLAS_REGION_EXACT         true
    UV_RECT_MATCHES_ATLAS_REGION          true (for every cell, all 12x12)
    ATLAS_BINDING_IS_DETERMINISTIC        true
    TOXIC_WRONG_ATLAS_PLACEMENT_DETECTED  true (adversarial control)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, cell_addresses
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs
from trixel.pixel_geometry.cell_atlas_layout_v1 import cell_atlas_rect, uniform_atlas_size
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_FLAT
from trixel.pixel_geometry.embedding_v1 import embed_flat
from tools.recipe_pixel_atlas_v1 import build_uniform_atlas
from tools.build_recipe_bound_hub_proof import (
    DIRT_RECIPE,
    GRASS_RECIPE,
    HEIGHT,
    TILE_PX,
    WIDTH,
    build_footprint_and_geometry,
    geometry_hash,
    is_dirt,
)

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_RECIPE_BOUND_SURFACE][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def main() -> int:
    footprint, positions, compiled = build_footprint_and_geometry()

    # GEOMETRY_UNCHANGED_BY_PIXEL_BINDING: rebuild geometry a second,
    # completely independent time, never touching the atlas/binding code
    # at all, and prove positions/indices are byte-identical to what the
    # proof tool produced. This is the direct check that pixel binding
    # cannot have altered geometry, since this path never calls it.
    control_footprint = build_footprint(
        WIDTH, HEIGHT, [["dirt" if is_dirt(x, row) else "grass" for x in range(WIDTH)] for row in range(HEIGHT)]
    )
    control_positions = embed_flat(control_footprint)
    control_compiled = compile_footprint(control_footprint, control_positions, embedding_id=EMBEDDING_FLAT)
    geometry_matches = (
        control_compiled["positions"] == compiled["positions"] and control_compiled["indices"] == compiled["indices"]
    )
    report("GEOMETRY_UNCHANGED_BY_PIXEL_BINDING", geometry_matches, f"hash={geometry_hash(compiled)}")

    # Build the atlas fresh here too (not reusing any file the tool wrote)
    # so every check below is against an independently rebuilt artifact.
    cell_to_recipe = {
        (x, row): (DIRT_RECIPE if is_dirt(x, row) else GRASS_RECIPE) for row in range(HEIGHT) for x in range(WIDTH)
    }
    atlas, rendered_tiles = build_uniform_atlas(footprint, cell_to_recipe, tile_px=TILE_PX)
    expected_w, expected_h = uniform_atlas_size(footprint, TILE_PX)
    report("ATLAS_SIZE_MATCHES_UNIFORM_LAYOUT", atlas.size == (expected_w, expected_h), f"got={atlas.size}")

    # EVERY_CELL_ATLAS_REGION_EXACT: for every cell, the atlas pixels at
    # its rect must equal -- pixel for pixel, no resampling -- the tile
    # image that was rendered for its assigned recipe.
    every_cell_exact = True
    offenders: list[tuple[int, int]] = []
    for x, row in cell_addresses(footprint):
        recipe_path = cell_to_recipe[(x, row)]
        expected_tile = rendered_tiles[recipe_path]
        left, top, right, bottom = cell_atlas_rect(x, row, TILE_PX)
        actual_region = atlas.crop((left, top, right, bottom))
        if list(actual_region.getdata()) != list(expected_tile.getdata()):
            every_cell_exact = False
            offenders.append((x, row))
    report("EVERY_CELL_ATLAS_REGION_EXACT", every_cell_exact, f"offenders={offenders[:5]}" if offenders else "")

    # UV_RECT_MATCHES_ATLAS_REGION: corner_uv's normalized rect for every
    # cell, scaled by the atlas dimensions, must equal the exact pixel
    # rect cell_atlas_rect() computed independently -- no off-by-one, no
    # rounding drift, for all 144 cells.
    uv_map = footprint_corner_uvs(footprint)
    uv_matches = True
    uv_offenders: list[tuple[int, int]] = []
    for x, row in cell_addresses(footprint):
        u0, v_top = uv_map[(x, row)]
        u1, v_bottom = uv_map[(x + 1, row + 1)]
        px_left = round(u0 * atlas.size[0])
        px_right = round(u1 * atlas.size[0])
        px_top = round((1.0 - v_top) * atlas.size[1])
        px_bottom = round((1.0 - v_bottom) * atlas.size[1])
        expected = cell_atlas_rect(x, row, TILE_PX)
        if (px_left, px_top, px_right, px_bottom) != expected:
            uv_matches = False
            uv_offenders.append((x, row))
    report("UV_RECT_MATCHES_ATLAS_REGION", uv_matches, f"offenders={uv_offenders[:5]}" if uv_offenders else "")

    # ATLAS_BINDING_IS_DETERMINISTIC: rebuild the whole atlas a second
    # time and byte-compare every pixel.
    atlas_again, _ = build_uniform_atlas(footprint, cell_to_recipe, tile_px=TILE_PX)
    report("ATLAS_BINDING_IS_DETERMINISTIC", list(atlas.getdata()) == list(atlas_again.getdata()))

    # TOXIC control: deliberately swap two cells' atlas regions (grass
    # tile pasted where a dirt cell's rect is, and vice versa) and prove
    # the SAME pixel-exact comparison this gate relies on actually
    # catches it. This never touches production code -- the corruption
    # is constructed locally, in the gate, exactly like the cylindrical
    # wrap and close-proximity toxic controls before it.
    corrupted = atlas.copy()
    swap_a, swap_b = (0, 0), (5, 0)  # a grass cell and an adjacent dirt cell
    assert not is_dirt(*swap_a) and is_dirt(*swap_b), "toxic control setup assumption broken"
    rect_a = cell_atlas_rect(swap_a[0], swap_a[1], TILE_PX)
    rect_b = cell_atlas_rect(swap_b[0], swap_b[1], TILE_PX)
    region_a = corrupted.crop(rect_a)
    region_b = corrupted.crop(rect_b)
    corrupted.paste(region_b, rect_a[:2])
    corrupted.paste(region_a, rect_b[:2])

    toxic_detected = False
    for x, row in (swap_a, swap_b):
        recipe_path = cell_to_recipe[(x, row)]
        expected_tile = rendered_tiles[recipe_path]
        left, top, right, bottom = cell_atlas_rect(x, row, TILE_PX)
        actual_region = corrupted.crop((left, top, right, bottom))
        if list(actual_region.getdata()) != list(expected_tile.getdata()):
            toxic_detected = True
    report("TOXIC_WRONG_ATLAS_PLACEMENT_DETECTED", toxic_detected)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_RECIPE_BOUND_SURFACE][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
