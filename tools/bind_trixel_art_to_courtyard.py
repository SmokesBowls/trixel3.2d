#!/usr/bin/env python3
"""Bind real, editable Trixel art onto the ACTUAL Trixel Capability
Courtyard geometry -- not a fresh test footprint, not an isolated
specimen. Every piece of geometry here comes from calling
tools/export_trixel_capability_courtyard.py's own build_scene() and
per-piece builder functions UNMODIFIED (read-only reuse -- that tool is
never edited, never re-derived) -- the hub, all three terraces, and all
three ramps are the SAME objects the pending courtyard already contains.
The only thing this tool adds is real per-cell pixel art, replacing the
flat Kd colors those pieces currently use for their ground surface.

Per the architecture correction that produced pixel_surface_v1.py: the
authority is an editable TrixelSurface per piece, never a PNG. Each
piece's atlas PNG here is a disposable, regenerable projection --
rendered fresh via tools/pixel_surface_render_v1.py, never hand-edited,
never read back as an input.

Two different geometry authorities are bound here, each the correct way
for its own data shape:

  - hub + 3 terraces come from trixel32d_surface_builder.py (via
    consume_surface_request_packet, called inside build_scene()). Their
    PRIMARY_PIXEL_FACE surfaces currently carry a trivial per-quad
    [0,0]-[1,0]-[0,1]-[1,1] UV (the builder's own QUAD_UVS constant) --
    this tool remaps ONLY those UVs into this piece's atlas rect for the
    matching (field_x, field_y) cell, computed the same way
    artwork_mapping_v1.corner_uv derives a UV from a row/column address.
    NEUTRAL_GAP_FILL surfaces (walls, bottoms) are untouched -- they keep
    the existing flat gap-fill material exactly as before; ground art was
    never meant to wrap onto retaining walls or slab undersides.
    Positions, indices, normals, and every other geometry field from the
    builder are read, never modified.

  - the 3 ramps come from pixel_geometry's own compile_footprint (via
    embed_declared_angle_ramp_fold, called inside each build_north/
    build_south/build_east()). These already carry proper per-corner UV
    via artwork_mapping_v1.footprint_corner_uvs -- ObjWriter.
    add_textured_footprint (imported unmodified from the courtyard export
    tool) already does exactly the right thing; this tool only supplies a
    real recipe-rendered atlas as that material's texture instead of the
    diagnostic strip.

Wall, floor/wall demo, and pillar keep their existing real (non-recipe)
textures unchanged -- they were never flat-color ground surfaces and are
out of scope for this pass.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.cell_atlas_layout_v1 import cell_atlas_rect, uniform_atlas_size
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.pixel_surface_v1 import build_surface
from tools.pixel_surface_render_v1 import render_uniform_atlas
from tools.export_trixel_capability_courtyard import (
    DEMO_TEXTURE,
    DIAGNOSTIC_ART,
    WALL_TEXTURE,
    ObjWriter,
    build_scene,
)
from trixel.pixel_geometry.contracts_v1 import (
    EMBEDDING_CYLINDRICAL_CLOSED_WRAP,
    EMBEDDING_FLAT,
    EMBEDDING_HARD_90_DEGREE_HINGE_FOLD,
    EMBEDDING_RIGID,
)

GRASS_RECIPE = REPO_ROOT / "recipes" / "terrain" / "forest.dense_canopy.json"
DIRT_RECIPE = REPO_ROOT / "recipes" / "transitions" / "grass_to_dirt.json"
TILE_PX = 16

OUT_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "courtyard_with_trixel_art"
ATLAS_DIR = OUT_DIR / "atlases"
SURFACES_DIR = OUT_DIR / "trixel_surfaces"


def _footprint_like(built: dict[str, Any]) -> dict[str, Any]:
    """A minimal footprint-shaped dict (width/height only) sufficient for
    cell_atlas_layout_v1's pure address arithmetic and pixel_surface_v1's
    build_surface -- trixel32d_surface_builder cells are already addressed
    by (field_x, field_y) exactly like a pixel_geometry footprint's
    (x, row), so no bridging beyond dimensions is needed."""
    field_xs = [r["field_x"] for r in built["cell_geometry_ranges"]]
    field_ys = [r["field_y"] for r in built["cell_geometry_ranges"]]
    return {"width": max(field_xs) + 1, "height": max(field_ys) + 1}


def surface_for_built_terrain(built: dict[str, Any]) -> tuple[dict, dict]:
    """Build a TrixelSurface for a trixel32d_surface_builder BUILT packet,
    recipe assigned per cell from its OWN 'terrain' field (grass/dirt) --
    never re-guessed from a hardcoded column/row pattern -- so this always
    matches whatever the actual courtyard geometry declares, even if its
    dirt-path layout ever changes."""
    footprint = _footprint_like(built)
    recipe_by_cell = {}
    for cell_range in built["cell_geometry_ranges"]:
        addr = (cell_range["field_x"], cell_range["field_y"])
        recipe = DIRT_RECIPE if cell_range["terrain"] == "dirt" else GRASS_RECIPE
        recipe_by_cell[addr] = str(recipe.relative_to(REPO_ROOT))
    surface = build_surface(footprint, default_density=TILE_PX, recipe_by_cell=recipe_by_cell)
    return footprint, surface


def atlas_uv_for_local(local_u: float, local_v: float, field_x: int, field_y: int, footprint: dict) -> tuple[float, float]:
    """Remap trixel32d_surface_builder's trivial per-quad UV (local_u,
    local_v each 0.0 or 1.0, from its own QUAD_UVS constant) into this
    cell's rectangle inside the shared atlas -- the same row-0-is-top
    convention artwork_mapping_v1.corner_uv already established, applied
    per-cell instead of per-corner-address since trixel32d_surface_builder
    has no shared-corner concept (its cells are independently quadded)."""
    width, height = footprint["width"], footprint["height"]
    u0, u1 = field_x / width, (field_x + 1) / width
    v0, v1 = 1.0 - (field_y + 1) / height, 1.0 - field_y / height
    u = u0 + local_u * (u1 - u0)
    v = v0 + local_v * (v1 - v0)
    return (u, v)


def write_art_bound_terrain(writer: ObjWriter, built: dict[str, Any], footprint: dict, primary_material: str) -> None:
    """Like ObjWriter.add_terrain, but PRIMARY_PIXEL_FACE surfaces get
    real atlas UV + the shared recipe-art material instead of a flat
    per-cell color; NEUTRAL_GAP_FILL surfaces are untouched, same
    gap_fill_flat material as before."""
    positions = built["geometry"]["positions"]
    for pos in positions:
        writer.lines.append(f"v {pos[0]} {pos[1]} {pos[2]}")
    vertex_base = writer.vertex_offset

    # UVs only for PRIMARY_PIXEL_FACE vertices -- gap-fill vertices never
    # get a vt line, matching add_terrain's existing plain-position faces.
    uv_index_by_global_vertex: dict[int, int] = {}
    for cell_range in built["cell_geometry_ranges"]:
        field_x, field_y = cell_range["field_x"], cell_range["field_y"]
        for surface in cell_range["surfaces"]:
            if surface["role"] != "PRIMARY_PIXEL_FACE":
                continue
            start = surface["vertex_start"]
            for local_index in range(surface["vertex_count"]):
                local_u, local_v = ([0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0])[local_index]
                u, v = atlas_uv_for_local(local_u, local_v, field_x, field_y, footprint)
                writer.lines.append(f"vt {u} {v}")
                uv_index_by_global_vertex[start + local_index] = writer.uv_offset
                writer.uv_offset += 1

    for cell_range in built["cell_geometry_ranges"]:
        for surface in cell_range["surfaces"]:
            start = surface["vertex_start"]
            is_primary = surface["role"] == "PRIMARY_PIXEL_FACE"
            material = primary_material if is_primary else "gap_fill_flat"
            quad = [vertex_base + start + i for i in range(4)]
            if is_primary:
                uv_quad = [uv_index_by_global_vertex[start + i] for i in range(4)]
                tri_a = f"{quad[0]}/{uv_quad[0]} {quad[1]}/{uv_quad[1]} {quad[2]}/{uv_quad[2]}"
                tri_b = f"{quad[1]}/{uv_quad[1]} {quad[3]}/{uv_quad[3]} {quad[2]}/{uv_quad[2]}"
            else:
                tri_a = f"{quad[0]} {quad[1]} {quad[2]}"
                tri_b = f"{quad[1]} {quad[3]} {quad[2]}"
            writer.face_blocks.append((material, [tri_a, tri_b]))

    writer.vertex_offset += len(positions)


def build_and_write_piece_atlas(built: dict[str, Any], name: str) -> tuple[dict, Path]:
    footprint, surface = surface_for_built_terrain(built)
    atlas = render_uniform_atlas(surface, footprint)
    SURFACES_DIR.mkdir(parents=True, exist_ok=True)
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    (SURFACES_DIR / f"{name}.json").write_text(json.dumps(surface, indent=2) + "\n")
    atlas_path = ATLAS_DIR / f"{name}.png"
    atlas.save(atlas_path)
    return footprint, atlas_path


def build_and_write_ramp_atlas(footprint: dict, name: str) -> Path:
    from trixel.pixel_geometry.addressing_v1 import cell_addresses

    recipe_by_cell = {addr: str(DIRT_RECIPE.relative_to(REPO_ROOT)) for addr in cell_addresses(footprint)}
    surface = build_surface(footprint, default_density=TILE_PX, recipe_by_cell=recipe_by_cell)
    atlas = render_uniform_atlas(surface, footprint)
    SURFACES_DIR.mkdir(parents=True, exist_ok=True)
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    (SURFACES_DIR / f"{name}.json").write_text(json.dumps(surface, indent=2) + "\n")
    atlas_path = ATLAS_DIR / f"{name}.png"
    atlas.save(atlas_path)
    return atlas_path


def write_mtl(mtl_path: Path, atlas_paths: dict[str, Path]) -> None:
    mtl_dir = mtl_path.parent
    lines: list[str] = []
    GAP_FILL_COLOR = [0.30, 0.28, 0.24, 1.0]
    lines += ["newmtl gap_fill_flat", f"Kd {GAP_FILL_COLOR[0]} {GAP_FILL_COLOR[1]} {GAP_FILL_COLOR[2]}", "illum 1"]
    for material, atlas_path in atlas_paths.items():
        rel = os.path.relpath(atlas_path, start=mtl_dir)
        lines += [f"newmtl {material}", "Kd 1.0 1.0 1.0", "illum 1", f"map_Kd {rel}"]
    for material, texture_path in (("wall_stone", WALL_TEXTURE), ("demo_stone", DEMO_TEXTURE), ("pillar_diagnostic", DIAGNOSTIC_ART)):
        rel = os.path.relpath(texture_path, start=mtl_dir)
        lines += [f"newmtl {material}", "Kd 1.0 1.0 1.0", "illum 1", f"map_Kd {rel}"]
    mtl_path.write_text("\n".join(lines) + "\n")


def export_pieces() -> dict[str, Path]:
    scene = build_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mtl_path = OUT_DIR / "courtyard_with_trixel_art.mtl"

    atlas_paths: dict[str, Path] = {}
    paths: dict[str, Path] = {}

    def write_piece(name: str, build) -> None:
        writer = ObjWriter()
        build(writer)
        out_path = OUT_DIR / f"{name}.obj"
        writer.write(out_path, mtl_path.name, object_name=name)
        paths[name] = out_path

    hub_footprint, hub_atlas = build_and_write_piece_atlas(scene["hub_built"], "hub")
    atlas_paths["hub_art"] = hub_atlas
    write_piece("hub", lambda w: write_art_bound_terrain(w, scene["hub_built"], hub_footprint, "hub_art"))

    for prefix in ("north", "south", "east"):
        spec = scene[prefix]
        ramp_atlas = build_and_write_ramp_atlas(spec["footprint"], f"{prefix}_ramp")
        atlas_paths[f"{prefix}_ramp_art"] = ramp_atlas
        write_piece(
            f"{prefix}_ramp",
            lambda w, spec=spec, prefix=prefix: w.add_textured_footprint(
                spec["footprint"], spec["positions"], embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD,
                material=f"{prefix}_ramp_art",
            ),
        )

        terrace_footprint, terrace_atlas = build_and_write_piece_atlas(spec["terrace_built"], f"{prefix}_terrace")
        atlas_paths[f"{prefix}_terrace_art"] = terrace_atlas
        write_piece(
            f"{prefix}_terrace",
            lambda w, spec=spec, footprint=terrace_footprint, prefix=prefix: write_art_bound_terrain(
                w, spec["terrace_built"], footprint, f"{prefix}_terrace_art"
            ),
        )

    wall = scene["wall"]
    write_piece(
        "west_wall",
        lambda w: w.add_textured_footprint(wall["footprint"], wall["positions"], embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD, material="wall_stone"),
    )
    demo = scene["floor_wall_demo"]
    write_piece(
        "floor_demo",
        lambda w: w.add_textured_footprint(demo["footprint"], demo["floor_positions"], embedding_id=EMBEDDING_FLAT, material="demo_stone"),
    )
    write_piece(
        "wall_demo",
        lambda w: w.add_textured_footprint(demo["footprint"], demo["wall_positions"], embedding_id=EMBEDDING_RIGID, material="demo_stone"),
    )
    pillar = scene["pillar"]
    write_piece(
        "pillar",
        lambda w: w.add_textured_footprint(pillar["footprint"], pillar["positions"], embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, material="pillar_diagnostic"),
    )

    write_mtl(mtl_path, atlas_paths)
    return paths


def main() -> int:
    paths = export_pieces()
    for name, path in paths.items():
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
