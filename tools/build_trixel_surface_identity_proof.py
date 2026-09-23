#!/usr/bin/env python3
"""The corrected first 3.2d visual-object proof.

The earlier atlas-binding proof (tools/build_recipe_bound_hub_proof.py,
retained as an experiment, not frozen) made a real architectural mistake:
it made a generated PNG atlas the authoritative visual object. That
violates the project's own rule -- if it is rendered, it must remain
editable. This tool replaces that authority direction with the correct
one:

    EDITABLE TRIXEL DATA (pixel_surface_v1.py, saved as JSON)
            -> compiled only ->
    disposable render texture (pixel_surface_render_v1.py, regenerable)

ONE TrixelSurface (8x8, every cell assigned the same grass recipe) is
embedded THREE separate ways -- flat, hinge-folded, and ramp-raised --
using nothing but already-frozen embedding functions. The surface itself
carries no 3D information; only its cell addressing is shared with the
footprint each embedding operates on. This is the actual "3.2d" claim
under test: a genuinely 2D, editable pixel-art object continuing to be
itself while its embodiment in 3D space changes underneath it.

Walkthrough this tool performs and records:
    1. build the base surface, render it (disposable) for all 3 embodiments
    2. edit exactly ONE trixel -- cell (4, 7), pixel (3, 5) of its 8x8
       tile, grass-green -> dirt-brown -- directly on the surface object,
       never on an image file
    3. re-render (disposable) for all 3 embodiments again
    4. bump the WHOLE surface's density 8x8 -> 32x32 and re-render again,
       proving geometry is untouched by a pure raster-resolution change

The gate (gate_pixel_geometry_trixel_surface_identity_v1.py) independently
re-renders everything this tool writes -- including deleting the disposable
cache and rebuilding it from surface JSON alone -- rather than trusting
any file this tool produced.
"""
from __future__ import annotations

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
from trixel.pixel_geometry.contracts_v1 import (
    EMBEDDING_DECLARED_ANGLE_RAMP_FOLD,
    EMBEDDING_FLAT,
    EMBEDDING_HARD_90_DEGREE_HINGE_FOLD,
)
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold, embed_flat, embed_hard_90_degree_hinge_fold
from trixel.pixel_geometry.pixel_surface_v1 import build_surface, edit_trixel_at_density, set_all_density
from tools.pixel_surface_render_v1 import render_uniform_atlas

WIDTH = HEIGHT = 8
HINGE_CORNER_X = 4
RAMP_ANGLE_DEGREES = 45.0
BASE_DENSITY = 8
RAISED_DENSITY = 32

GRASS_RECIPE = REPO_ROOT / "recipes" / "terrain" / "forest.dense_canopy.json"
EDIT_CELL = (4, 7)
EDIT_PX, EDIT_PY = 3, 5
EDIT_COLOR = (139, 90, 43)  # dirt-brown

OUT_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "trixel_surface_identity_proof"
CACHE_DIR = OUT_DIR / "generated_cache"
EMBODIMENTS_DIR = OUT_DIR / "embodiments"

EMBODIMENTS = ("flat", "hinge", "ramp")


def build_footprint_obj() -> dict:
    payload = [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]
    return build_footprint(WIDTH, HEIGHT, payload)


def embodiment_geometry(footprint: dict, name: str) -> dict:
    if name == "flat":
        positions = embed_flat(footprint)
        return compile_footprint(footprint, positions, embedding_id=EMBEDDING_FLAT)
    if name == "hinge":
        positions = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_CORNER_X)
        return compile_footprint(footprint, positions, embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD)
    if name == "ramp":
        positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=RAMP_ANGLE_DEGREES)
        return compile_footprint(footprint, positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    raise ValueError(name)


def embodiment_positions(footprint: dict, name: str) -> dict:
    if name == "flat":
        return embed_flat(footprint)
    if name == "hinge":
        return embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_CORNER_X)
    if name == "ramp":
        return embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=RAMP_ANGLE_DEGREES)
    raise ValueError(name)


def render_stage(surface: dict, footprint: dict, stage_dir: Path) -> dict[str, Path]:
    """Render the disposable atlas independently once PER EMBODIMENT NAME
    -- not shared-by-reference -- so the gate can prove regenerated
    content is identical across independently-triggered renders, not just
    identical because one file was copied three times."""
    stage_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name in EMBODIMENTS:
        atlas = render_uniform_atlas(surface, footprint)
        path = stage_dir / f"atlas_for_{name}.png"
        atlas.save(path)
        paths[name] = path
    return paths


def write_textured_obj(footprint: dict, positions: dict, compiled: dict, out_path: Path, mtl_path: Path, atlas_png: Path, material: str) -> None:
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


def write_embodiment_objs(footprint: dict, atlas_paths: dict[str, Path], out_dir: Path, suffix: str = "") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in EMBODIMENTS:
        positions = embodiment_positions(footprint, name)
        compiled = embodiment_geometry(footprint, name)
        obj_path = out_dir / f"{name}{suffix}.obj"
        mtl_path = out_dir / f"{name}{suffix}.mtl"
        write_textured_obj(footprint, positions, compiled, obj_path, mtl_path, atlas_paths[name], f"{name}{suffix}_surface")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    footprint = build_footprint_obj()

    recipe_by_cell = {(x, row): str(GRASS_RECIPE.relative_to(REPO_ROOT)) for row in range(HEIGHT) for x in range(WIDTH)}
    base_surface = build_surface(footprint, default_density=BASE_DENSITY, recipe_by_cell=recipe_by_cell)

    (OUT_DIR / "surface_base.json").write_text(json.dumps(base_surface, indent=2) + "\n")
    before_paths = render_stage(base_surface, footprint, CACHE_DIR / "before_edit")
    write_embodiment_objs(footprint, before_paths, EMBODIMENTS_DIR / "before_edit")

    edited_surface = edit_trixel_at_density(
        base_surface, EDIT_CELL, EDIT_PX, EDIT_PY, at_density=BASE_DENSITY, color=EDIT_COLOR
    )
    (OUT_DIR / "surface_edited.json").write_text(json.dumps(edited_surface, indent=2) + "\n")
    after_paths = render_stage(edited_surface, footprint, CACHE_DIR / "after_edit")
    write_embodiment_objs(footprint, after_paths, EMBODIMENTS_DIR / "after_edit")

    densified_surface = set_all_density(edited_surface, RAISED_DENSITY)
    (OUT_DIR / "surface_edited_density32.json").write_text(json.dumps(densified_surface, indent=2) + "\n")
    density_paths = render_stage(densified_surface, footprint, CACHE_DIR / "after_density32")
    write_embodiment_objs(footprint, density_paths, EMBODIMENTS_DIR / "after_density32")

    manifest = {
        "contract": "trixel.trixel_surface_identity_proof.v1",
        "width": WIDTH,
        "height": HEIGHT,
        "hinge_corner_x": HINGE_CORNER_X,
        "ramp_angle_degrees": RAMP_ANGLE_DEGREES,
        "base_density": BASE_DENSITY,
        "raised_density": RAISED_DENSITY,
        "edit_cell": list(EDIT_CELL),
        "edit_pixel_at_base_density": [EDIT_PX, EDIT_PY],
        "edit_color": list(EDIT_COLOR),
        "embodiments": list(EMBODIMENTS),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {OUT_DIR / 'surface_base.json'}")
    print(f"wrote {OUT_DIR / 'surface_edited.json'}")
    print(f"wrote {OUT_DIR / 'surface_edited_density32.json'}")
    print(f"wrote embodiment OBJs under {EMBODIMENTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
