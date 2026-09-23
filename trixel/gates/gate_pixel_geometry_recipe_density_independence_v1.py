#!/usr/bin/env python3
"""Density-independence proof, gated: two independent footprints, same
dimensions and payload pattern, placed edge-to-edge, bound to the SAME
two recipes at DIFFERENT tile pixel densities (8x8 vs 32x32 px/cell).

Required result:
    LOCAL_GEOMETRY_IDENTICAL_BETWEEN_INSTANCES   true
    UV_MAPS_IDENTICAL_BETWEEN_INSTANCES          true
    ATLAS_DENSITY_ACTUALLY_DIFFERS               true (4x, 8px vs 32px)
    HIGH_DENSITY_ATLAS_IS_NOT_A_RESIZE           true (real re-render, not upscale)
    TOUCHING_INSTANCES_CREATE_NO_ADJACENCY       true (toxic/proximity control)

If all five hold, pixel density has been demonstrated as a property of
the bound raster surface alone -- never of geometry, never of UV
topology, never of declared adjacency.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.adjacency_v1 import no_proximity_derived_adjacency, source_adjacency
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import positions_by_cell_center
from tools.build_recipe_density_proof import (
    GRASS_RECIPE,
    HIGH_TILE_PX,
    LOW_TILE_PX,
    WIDTH,
    build_instance,
    cell_to_recipe_map,
)
from tools.recipe_pixel_atlas_v1 import build_uniform_atlas

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_RECIPE_DENSITY_INDEPENDENCE][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def main() -> int:
    low_footprint, low_positions, low_compiled = build_instance(translation_x=0.0)
    high_footprint, high_positions, high_compiled = build_instance(translation_x=float(WIDTH))

    # LOCAL_GEOMETRY_IDENTICAL_BETWEEN_INSTANCES: strip the HIGH
    # instance's translation back off and compare its positions to the
    # LOW instance's positions directly -- indices must already match
    # exactly since both come from the same footprint dimensions/payload
    # shape through the same compiler.
    untranslated_high_positions = {
        addr: (x - WIDTH, y, z) for addr, (x, y, z) in high_positions.items()
    }
    positions_match = untranslated_high_positions == low_positions
    indices_match = high_compiled["indices"] == low_compiled["indices"]
    report(
        "LOCAL_GEOMETRY_IDENTICAL_BETWEEN_INSTANCES",
        positions_match and indices_match,
        f"positions_match={positions_match} indices_match={indices_match}",
    )

    # UV_MAPS_IDENTICAL_BETWEEN_INSTANCES
    low_uv = footprint_corner_uvs(low_footprint)
    high_uv = footprint_corner_uvs(high_footprint)
    report("UV_MAPS_IDENTICAL_BETWEEN_INSTANCES", uvs_are_identical(low_uv, high_uv))

    # ATLAS_DENSITY_ACTUALLY_DIFFERS
    low_recipes = cell_to_recipe_map(low_footprint)
    high_recipes = cell_to_recipe_map(high_footprint)
    low_atlas, low_tiles = build_uniform_atlas(low_footprint, low_recipes, tile_px=LOW_TILE_PX)
    high_atlas, high_tiles = build_uniform_atlas(high_footprint, high_recipes, tile_px=HIGH_TILE_PX)
    expected_low = (WIDTH * LOW_TILE_PX, WIDTH * LOW_TILE_PX)
    expected_high = (WIDTH * HIGH_TILE_PX, WIDTH * HIGH_TILE_PX)
    density_differs = low_atlas.size == expected_low and high_atlas.size == expected_high and low_atlas.size != high_atlas.size
    report(
        "ATLAS_DENSITY_ACTUALLY_DIFFERS",
        density_differs,
        f"low={low_atlas.size} high={high_atlas.size}",
    )

    # HIGH_DENSITY_ATLAS_IS_NOT_A_RESIZE: the high-density tile must not
    # equal a naive nearest-neighbor upscale of the low-density tile --
    # it was re-executed against a larger Canvas from scratch (noise
    # passes use per-pixel randomness, so an independent re-render at 4x
    # the pixel count will not reproduce the same noise pattern a resize
    # would).
    from PIL import Image

    low_grass_tile = low_tiles[GRASS_RECIPE]
    high_grass_tile = high_tiles[GRASS_RECIPE]
    naive_upscale = low_grass_tile.resize(high_grass_tile.size, Image.NEAREST)
    not_a_resize = list(naive_upscale.getdata()) != list(high_grass_tile.getdata())
    report("HIGH_DENSITY_ATLAS_IS_NOT_A_RESIZE", not_a_resize)

    # TOUCHING_INSTANCES_CREATE_NO_ADJACENCY: the two footprints touch
    # exactly at x=WIDTH (low's right edge coincides with high's left
    # edge) but are two independently declared footprints -- there is no
    # declared cross-footprint adjacency at all, and no_proximity_derived_
    # adjacency must find the coincident cell-center pairs across the
    # seam (offenders is EXPECTED non-empty here, matching the same
    # inverted-expectation pattern gate_pixel_geometry_ramp_close_
    # proximity_v1.py established) while each footprint's OWN compiled
    # adjacency stays exactly its own source_adjacency(), regardless.
    low_centers = positions_by_cell_center(low_compiled)
    high_centers = positions_by_cell_center(high_compiled)
    combined_centers = {("low", addr): pos for addr, pos in low_centers.items()}
    combined_centers.update({("high", addr): pos for addr, pos in high_centers.items()})
    # Declare each footprint's OWN real intra-footprint adjacency (so
    # ordinary same-footprint neighbors, also 1.0 apart center-to-center,
    # are correctly excluded) -- but declare NOTHING between "low" and
    # "high": they are two independent footprints that merely happen to
    # touch after placement.
    declared: dict = {}
    for addr, neighbors in source_adjacency(low_footprint).items():
        declared[("low", addr)] = {("low", n) for n in neighbors}
    for addr, neighbors in source_adjacency(high_footprint).items():
        declared[("high", addr)] = {("high", n) for n in neighbors}
    offenders = no_proximity_derived_adjacency(combined_centers, declared, proximity_tolerance=1.01)
    cross_footprint_offenders = [pair for pair in offenders if pair[0][0] != pair[1][0]]
    low_adjacency_clean = low_compiled["compiled_adjacency"] == source_adjacency(low_footprint)
    high_adjacency_clean = high_compiled["compiled_adjacency"] == source_adjacency(high_footprint)
    report(
        "TOUCHING_INSTANCES_CREATE_NO_ADJACENCY",
        low_adjacency_clean and high_adjacency_clean and len(cross_footprint_offenders) > 0,
        f"cross_footprint_proximity_offenders={len(cross_footprint_offenders)} (must be >0 -- they really do touch -- "
        f"yet never promoted into either footprint's own compiled_adjacency)",
    )

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_RECIPE_DENSITY_INDEPENDENCE][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
