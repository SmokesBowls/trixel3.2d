#!/usr/bin/env python3
"""First 3.2d visual-object proof: bind trixel_recipe_renderer.py's real
pixel-writing machinery onto trixel/pixel_geometry's own cell/UV
addressing, on a footprint matching the Trixel Capability Courtyard hub's
shape (12x12, plus-shaped dirt path, DIRT_COLUMNS/DIRT_ROWS={5,6}) -- but
built fresh through pixel_geometry's OWN compile_footprint/embed_flat, not
through trixel32d_surface_builder.py (the separate terrain-lane authority
that built the courtyard's actual Hub_CentralTerrain_12x12 piece). That
distinction matters: only pixel_geometry's compiler carries cell-owned UV
addressing (artwork_mapping_v1.py) at all, so this proof exercises that
layer specifically, on a footprint chosen to be visually recognizable as
"the hub" without touching the pending courtyard.blend or any frozen
production module.

Writes BOTH a BEFORE object (identical geometry, flat per-cell Kd color --
the courtyard hub's own current appearance convention) and an AFTER object
(identical geometry, real per-cell recipe-rendered pixel tiles bound via
UV into one shared atlas), so the only thing that differs between them is
whether a real pixel surface is bound to each cell -- never the mesh.

Recipes used (existing, unmodified, already gated):
    grass cells      -> recipes/terrain/forest.dense_canopy.json
    dirt/path cells  -> recipes/transitions/grass_to_dirt.json
(the same two recipes docs/TRIXEL_CAPABILITY_COURTYARD_V1.md already names
as the source of the courtyard hub's sampled flat colors -- this proof
binds their actual rendered pixels instead of one sampled color.)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_FLAT
from trixel.pixel_geometry.embedding_v1 import embed_flat
from tools.recipe_pixel_atlas_v1 import build_uniform_atlas

WIDTH = HEIGHT = 12
DIRT_COLUMNS = {5, 6}
DIRT_ROWS = {5, 6}
TILE_PX = 16

GRASS_RECIPE = REPO_ROOT / "recipes" / "terrain" / "forest.dense_canopy.json"
DIRT_RECIPE = REPO_ROOT / "recipes" / "transitions" / "grass_to_dirt.json"

OUT_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "recipe_bound_hub"

GRASS_KD = (0.141, 0.498, 0.125)
DIRT_KD = (0.518, 0.482, 0.188)


def is_dirt(x: int, row: int) -> bool:
    return x in DIRT_COLUMNS or row in DIRT_ROWS


def build_footprint_and_geometry() -> tuple[dict, dict, dict]:
    payload = [["dirt" if is_dirt(x, row) else "grass" for x in range(WIDTH)] for row in range(HEIGHT)]
    footprint = build_footprint(WIDTH, HEIGHT, payload)
    positions = embed_flat(footprint)
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_FLAT)
    return footprint, positions, compiled


def geometry_hash(compiled: dict) -> str:
    payload = json.dumps({"positions": compiled["positions"], "indices": compiled["indices"]}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_before_obj(footprint: dict, positions: dict, compiled: dict, out_path: Path, mtl_path: Path) -> None:
    width = footprint["width"]
    ordered = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    vindex = {addr: i + 1 for i, addr in enumerate(ordered)}
    lines = [f"mtllib {mtl_path.name}", "o hub_before_flat_color"]
    for addr in ordered:
        p = positions[addr]
        lines.append(f"v {p[0]} {p[1]} {p[2]}")
    by_material: dict[str, list[str]] = {"grass_flat": [], "dirt_flat": []}
    for prov in compiled["primitive_provenance"]:
        x, row = prov["cell_address"]
        material = "dirt_flat" if is_dirt(x, row) else "grass_flat"
        start = prov["primitive_start"] * 3
        for tri in (compiled["indices"][start : start + 3], compiled["indices"][start + 3 : start + 6]):
            refs = " ".join(str(vindex[ordered[i]]) for i in tri)
            by_material[material].append(refs)
    for material, faces in by_material.items():
        lines.append(f"usemtl {material}")
        for face in faces:
            lines.append(f"f {face}")
    out_path.write_text("\n".join(lines) + "\n")
    mtl_path.write_text(
        "\n".join(
            [
                "newmtl grass_flat",
                f"Kd {GRASS_KD[0]} {GRASS_KD[1]} {GRASS_KD[2]}",
                "illum 1",
                "newmtl dirt_flat",
                f"Kd {DIRT_KD[0]} {DIRT_KD[1]} {DIRT_KD[2]}",
                "illum 1",
            ]
        )
        + "\n"
    )


def write_after_obj(footprint: dict, positions: dict, compiled: dict, out_path: Path, mtl_path: Path, atlas_png: Path) -> None:
    width = footprint["width"]
    ordered = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    vindex = {addr: i + 1 for i, addr in enumerate(ordered)}
    uv_map = footprint_corner_uvs(footprint)
    uvindex = {addr: i + 1 for i, addr in enumerate(ordered)}
    lines = [f"mtllib {mtl_path.name}", "o hub_after_recipe_pixels"]
    for addr in ordered:
        p = positions[addr]
        lines.append(f"v {p[0]} {p[1]} {p[2]}")
    for addr in ordered:
        u, v = uv_map[addr]
        lines.append(f"vt {u} {v}")
    lines.append("usemtl hub_recipe_atlas")
    for prov in compiled["primitive_provenance"]:
        start = prov["primitive_start"] * 3
        for tri in (compiled["indices"][start : start + 3], compiled["indices"][start + 3 : start + 6]):
            refs = " ".join(f"{vindex[ordered[i]]}/{uvindex[ordered[i]]}" for i in tri)
            lines.append(f"f {refs}")
    out_path.write_text("\n".join(lines) + "\n")
    rel = os.path.relpath(atlas_png, start=mtl_path.parent)
    mtl_path.write_text("\n".join(["newmtl hub_recipe_atlas", "Kd 1.0 1.0 1.0", "illum 1", f"map_Kd {rel}"]) + "\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    footprint, positions, compiled = build_footprint_and_geometry()

    cell_to_recipe = {
        (x, row): (DIRT_RECIPE if is_dirt(x, row) else GRASS_RECIPE) for row in range(HEIGHT) for x in range(WIDTH)
    }
    atlas, _rendered = build_uniform_atlas(footprint, cell_to_recipe, tile_px=TILE_PX)
    atlas_path = OUT_DIR / "hub_recipe_atlas.png"
    atlas.save(atlas_path)

    before_obj = OUT_DIR / "hub_before_flat_color.obj"
    before_mtl = OUT_DIR / "hub_before_flat_color.mtl"
    write_before_obj(footprint, positions, compiled, before_obj, before_mtl)

    after_obj = OUT_DIR / "hub_after_recipe_pixels.obj"
    after_mtl = OUT_DIR / "hub_after_recipe_pixels.mtl"
    write_after_obj(footprint, positions, compiled, after_obj, after_mtl, atlas_path)

    manifest = {
        "contract": "trixel.recipe_bound_hub_proof.v1",
        "width": WIDTH,
        "height": HEIGHT,
        "dirt_columns": sorted(DIRT_COLUMNS),
        "dirt_rows": sorted(DIRT_ROWS),
        "tile_px": TILE_PX,
        "grass_recipe": str(GRASS_RECIPE.relative_to(REPO_ROOT)),
        "dirt_recipe": str(DIRT_RECIPE.relative_to(REPO_ROOT)),
        "atlas_size": list(atlas.size),
        "geometry_hash": geometry_hash(compiled),
        "cell_recipe_by_address": {
            f"{x},{row}": ("dirt" if is_dirt(x, row) else "grass") for row in range(HEIGHT) for x in range(WIDTH)
        },
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {before_obj}")
    print(f"wrote {after_obj}")
    print(f"wrote {atlas_path} ({atlas.size[0]}x{atlas.size[1]})")
    print(f"wrote {OUT_DIR / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
