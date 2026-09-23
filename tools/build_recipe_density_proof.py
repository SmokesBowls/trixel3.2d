#!/usr/bin/env python3
"""Second half of the first-3.2d-visual-object proof: prove pixel density
is a raster/atlas-authoring choice, completely decoupled from both
geometry and UV topology.

Two INDEPENDENT footprints -- same dimensions, same dirt-cross payload
pattern, each compiled through the same frozen embed_flat/compile_footprint
path -- are placed edge-to-edge (touching, never welded, never sharing a
corner address -- two separate compile_footprint() calls, matching the
close-proximity toxic discipline gate_pixel_geometry_ramp_close_
proximity_v1.py already established). One instance binds its recipe
pixels at LOW tile density (8x8 px/cell); the other binds the SAME two
recipes at HIGH tile density (32x32 px/cell) -- four times the raster
pixels per cell, same recipe passes, same UV rectangles, same mesh.

If the gate can show:
    - both instances' local (untranslated) compiled positions and indices
      are byte-identical (same geometry, just placed differently)
    - both instances' UV maps are byte-identical (UV depends only on
      footprint width/height/address, never on chosen tile_px)
    - only the atlas raster dimensions differ (8x8 vs 32x32 per cell)
    - touching them does not create any adjacency between the two
      footprints

...then pixel density has been shown to be a property of the bound
raster surface alone, never of the geometry or its addressing -- the
actual claim "3.2d" makes that "3D" alone does not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_FLAT, EMBEDDING_RIGID
from trixel.pixel_geometry.embedding_v1 import embed_flat, embed_rigid
from tools.recipe_pixel_atlas_v1 import build_uniform_atlas

WIDTH = HEIGHT = 6
DIRT_COLUMNS = {2, 3}
DIRT_ROWS = {2, 3}

LOW_TILE_PX = 8
HIGH_TILE_PX = 32

GRASS_RECIPE = REPO_ROOT / "recipes" / "terrain" / "forest.dense_canopy.json"
DIRT_RECIPE = REPO_ROOT / "recipes" / "transitions" / "grass_to_dirt.json"

OUT_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "recipe_density_proof"


def is_dirt(x: int, row: int) -> bool:
    return x in DIRT_COLUMNS or row in DIRT_ROWS


def build_base_footprint() -> dict:
    payload = [["dirt" if is_dirt(x, row) else "grass" for x in range(WIDTH)] for row in range(HEIGHT)]
    return build_footprint(WIDTH, HEIGHT, payload)


def build_instance(*, translation_x: float) -> tuple[dict, dict, dict]:
    footprint = build_base_footprint()
    local_positions = embed_flat(footprint)
    if translation_x == 0.0:
        positions = local_positions
        embedding_id = EMBEDDING_FLAT
    else:
        positions = embed_rigid(local_positions, translation=(translation_x, 0.0, 0.0))
        embedding_id = EMBEDDING_RIGID
    compiled = compile_footprint(footprint, positions, embedding_id=embedding_id)
    return footprint, positions, compiled


def cell_to_recipe_map(footprint: dict) -> dict[tuple[int, int], Path]:
    return {
        (x, row): (DIRT_RECIPE if is_dirt(x, row) else GRASS_RECIPE) for row in range(HEIGHT) for x in range(WIDTH)
    }


def write_textured_obj(footprint: dict, positions: dict, compiled: dict, out_path: Path, mtl_path: Path, atlas_png: Path, material: str) -> None:
    import os

    width = footprint["width"]
    ordered = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    vindex = {addr: i + 1 for i, addr in enumerate(ordered)}
    uv_map = footprint_corner_uvs(footprint)
    uvindex = {addr: i + 1 for i, addr in enumerate(ordered)}
    lines = [f"mtllib {mtl_path.name}", f"o {material}"]
    for addr in ordered:
        p = positions[addr]
        lines.append(f"v {p[0]} {p[1]} {p[2]}")
    for addr in ordered:
        u, v = uv_map[addr]
        lines.append(f"vt {u} {v}")
    lines.append(f"usemtl {material}")
    for prov in compiled["primitive_provenance"]:
        start = prov["primitive_start"] * 3
        for tri in (compiled["indices"][start : start + 3], compiled["indices"][start + 3 : start + 6]):
            refs = " ".join(f"{vindex[ordered[i]]}/{uvindex[ordered[i]]}" for i in tri)
            lines.append(f"f {refs}")
    out_path.write_text("\n".join(lines) + "\n")
    rel = os.path.relpath(atlas_png, start=mtl_path.parent)
    mtl_path.write_text("\n".join([f"newmtl {material}", "Kd 1.0 1.0 1.0", "illum 1", f"map_Kd {rel}"]) + "\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    low_footprint, low_positions, low_compiled = build_instance(translation_x=0.0)
    high_footprint, high_positions, high_compiled = build_instance(translation_x=float(WIDTH))

    low_recipes = cell_to_recipe_map(low_footprint)
    high_recipes = cell_to_recipe_map(high_footprint)

    low_atlas, _ = build_uniform_atlas(low_footprint, low_recipes, tile_px=LOW_TILE_PX)
    high_atlas, _ = build_uniform_atlas(high_footprint, high_recipes, tile_px=HIGH_TILE_PX)

    low_atlas_path = OUT_DIR / "density_low_atlas.png"
    high_atlas_path = OUT_DIR / "density_high_atlas.png"
    low_atlas.save(low_atlas_path)
    high_atlas.save(high_atlas_path)

    write_textured_obj(
        low_footprint, low_positions, low_compiled, OUT_DIR / "density_low.obj", OUT_DIR / "density_low.mtl",
        low_atlas_path, "density_low_atlas",
    )
    write_textured_obj(
        high_footprint, high_positions, high_compiled, OUT_DIR / "density_high.obj", OUT_DIR / "density_high.mtl",
        high_atlas_path, "density_high_atlas",
    )

    manifest = {
        "contract": "trixel.recipe_density_independence_proof.v1",
        "width": WIDTH,
        "height": HEIGHT,
        "low_tile_px": LOW_TILE_PX,
        "high_tile_px": HIGH_TILE_PX,
        "low_atlas_size": list(low_atlas.size),
        "high_atlas_size": list(high_atlas.size),
        "translation_x_high": WIDTH,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {OUT_DIR / 'density_low.obj'} atlas={low_atlas.size}")
    print(f"wrote {OUT_DIR / 'density_high.obj'} atlas={high_atlas.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
