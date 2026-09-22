#!/usr/bin/env python3
"""Fourth terrain integration proof: multiple ramps in one composition.

    SCENE A (unmodified, reused verbatim from
             export_terrain_ramp_integration_evidence.build_scene())
        lower terrain
              |  ramp travels along -Z (rotation_degrees=90)
        upper terrain

    SCENE B (unmodified, reused verbatim from
             export_terrain_ramp_rotated_orientation_evidence.build_scene(),
             then rigidly translated by SCENE_B_OFFSET)
        lower terrain -- ramp travels along +X (rotation_degrees=0) -- upper terrain

Deliberately controlled: no new ramp mathematics, no new cell metric, no
new slope. Both scenes reuse the EXACT SAME already-proven worked example
(8 ramp cells, required rise 5.0). The only new capability this proof
introduces is composing two ALREADY-COMPLETE, ALREADY-VERIFIED scenes into
one world without either one interfering with the other -- Scene A is
built and left exactly where its own frozen proof puts it; Scene B is
built exactly as its own frozen proof does, then moved as one rigid whole
(terrain_ramp_integration_v1.translate_built_geometry for its terrain,
the same rotation-plus-translation the ramp already uses for its ramp)
far enough away that nothing in it can be mistaken for part of Scene A.

The question under test:

    Can two independently placed metric-preserving ramp artifacts coexist
    in one terrain composition without either placement transform,
    attachment seam, adjacency graph, or terrain artifact interfering
    with the other?
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import corner_index
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.terrain_ramp_integration_v1 import (
    ramp_position_to_world,
    terrain_attachment_edge_x,
    translate_built_geometry,
    verify_attachment_edges,
)

import export_terrain_ramp_integration_evidence as scene_a_tool
import export_terrain_ramp_rotated_orientation_evidence as scene_b_tool

FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
OUT_OBJ = FIXTURES / "terrain_multi_ramp_composition.obj"
OUT_MANIFEST = FIXTURES / "terrain_multi_ramp_composition_manifest.json"

GRASS_COLOR = scene_a_tool.GRASS_COLOR
DIRT_COLOR = scene_a_tool.DIRT_COLOR
GAP_FILL_COLOR = scene_a_tool.GAP_FILL_COLOR

# Whole-scene rigid separation: Scene B's own bounding box (as built by its
# own frozen proof) is roughly X in [-4, 10.2], Z in [-4, 4]. Scene A's is
# roughly X in [-4, 4], Z in [-10.2, 4]. A -30 unit shift in Z puts Scene B
# entirely clear of Scene A with wide margin on every axis.
SCENE_B_OFFSET = (0.0, 0.0, -30.0)


def build_scene_a() -> dict[str, Any]:
    """Scene A, completely unmodified: the frozen integer-rise control."""
    return scene_a_tool.build_scene()


def build_scene_b_shifted() -> dict[str, Any]:
    """Scene B, built exactly as its own frozen proof does, then moved as
    one rigid whole by SCENE_B_OFFSET. translate_built_geometry() never
    touches vertex count, indices, or declared world_cell_y -- and the
    ramp's own placement offsets simply gain the same additive shift,
    which is still exactly a rotation-plus-translation (an isometry)."""
    raw = scene_b_tool.build_scene()
    solved = raw["ramp_info"]["solved"]

    shifted_path_x_offset = scene_b_tool.RAMP_X_OFFSET + SCENE_B_OFFSET[0]
    shifted_ramp_z_offset = scene_b_tool.PATH_Z_OFFSET + SCENE_B_OFFSET[2]

    lower_built = translate_built_geometry(raw["lower_built"], SCENE_B_OFFSET)
    upper_built = translate_built_geometry(raw["upper_built"], SCENE_B_OFFSET)

    ramp_near_world = [
        ramp_position_to_world(
            pos, path_x_offset=shifted_path_x_offset, ramp_z_offset=shifted_ramp_z_offset, rotation_degrees=scene_b_tool.ROTATION_DEGREES
        )
        for (x, r), pos in raw["ramp_positions"].items()
        if x == scene_b_tool.HINGE_CORNER_X
    ]
    ramp_far_world = [
        ramp_position_to_world(
            pos, path_x_offset=shifted_path_x_offset, ramp_z_offset=shifted_ramp_z_offset, rotation_degrees=scene_b_tool.ROTATION_DEGREES
        )
        for (x, r), pos in raw["ramp_positions"].items()
        if x == scene_b_tool.RAMP_WIDTH
    ]
    lower_edge = terrain_attachment_edge_x(lower_built, field_y_values=scene_b_tool.DIRT_ROWS, field_x=scene_b_tool.COLUMNS - 1, edge="high_x")
    upper_edge = terrain_attachment_edge_x(upper_built, field_y_values=scene_b_tool.DIRT_ROWS, field_x=0, edge="low_x")

    attachment = verify_attachment_edges(
        ramp_near_world=ramp_near_world,
        ramp_far_world=ramp_far_world,
        lower_edge=lower_edge,
        upper_edge=upper_edge,
        path_x_offset=shifted_path_x_offset,
        ramp_z_offset=shifted_ramp_z_offset,
        rotation_degrees=scene_b_tool.ROTATION_DEGREES,
    )

    return {
        "footprint": raw["footprint"],
        "ramp_positions": raw["ramp_positions"],
        "ramp_info": raw["ramp_info"],
        "lower_built": lower_built,
        "upper_built": upper_built,
        "shifted_path_x_offset": shifted_path_x_offset,
        "shifted_ramp_z_offset": shifted_ramp_z_offset,
        "attachment": attachment,
    }


def build_scene() -> dict[str, Any]:
    scene_a = build_scene_a()
    scene_b = build_scene_b_shifted()
    return {"scene_a": scene_a, "scene_b": scene_b}


def ramp_world_points_a(scene_a: dict[str, Any], *, exclude_stub: bool) -> list[tuple[float, float, float]]:
    positions = scene_a["ramp_positions"]
    return [
        ramp_position_to_world(pos, path_x_offset=scene_a_tool.PATH_X_OFFSET, ramp_z_offset=scene_a_tool.ramp_z_offset())
        for (x, r), pos in positions.items()
        if (x >= scene_a_tool.HINGE_CORNER_X) or not exclude_stub
    ]


def ramp_world_points_b(scene_b: dict[str, Any], *, exclude_stub: bool) -> list[tuple[float, float, float]]:
    positions = scene_b["ramp_positions"]
    return [
        ramp_position_to_world(
            pos,
            path_x_offset=scene_b["shifted_path_x_offset"],
            ramp_z_offset=scene_b["shifted_ramp_z_offset"],
            rotation_degrees=scene_b_tool.ROTATION_DEGREES,
        )
        for (x, r), pos in positions.items()
        if (x >= scene_b_tool.HINGE_CORNER_X) or not exclude_stub
    ]


def _write_terrain(lines: list[str], vertex_offset: int, built: dict[str, Any], face_blocks: list) -> int:
    positions = built["geometry"]["positions"]
    for pos in positions:
        lines.append(f"v {pos[0]} {pos[1]} {pos[2]}")
    base = vertex_offset
    for cell_range in built["cell_geometry_ranges"]:
        material = "dirt_flat" if cell_range["terrain"] == "dirt" else "grass_flat"
        for surface in cell_range["surfaces"]:
            mat = material if surface["role"] == "PRIMARY_PIXEL_FACE" else "gap_fill_flat"
            start = surface["vertex_start"]
            quad = [base + start, base + start + 1, base + start + 2, base + start + 3]
            face_blocks.append((mat, [(quad[0], quad[1], quad[2]), (quad[1], quad[3], quad[2])]))
    return vertex_offset + len(positions)


def _write_ramp(
    lines: list[str],
    vertex_offset: int,
    footprint: dict,
    ramp_positions: dict,
    face_blocks: list,
    *,
    path_x_offset: float,
    ramp_z_offset: float,
    rotation_degrees: float,
    hinge_corner_x: int,
) -> int:
    width = footprint["width"]
    ordered = sorted(ramp_positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    ramp_index = {addr: vertex_offset + i for i, addr in enumerate(ordered)}
    for addr in ordered:
        world = ramp_position_to_world(
            ramp_positions[addr], path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset, rotation_degrees=rotation_degrees
        )
        lines.append(f"v {world[0]} {world[1]} {world[2]}")
    compiled = compile_footprint(footprint, ramp_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    for prov in compiled["primitive_provenance"]:
        if prov["cell_address"][0] < hinge_corner_x:
            continue
        start = prov["primitive_start"] * 3
        tri_a = compiled["indices"][start : start + 3]
        tri_b = compiled["indices"][start + 3 : start + 6]
        face_blocks.append(("dirt_flat", [tuple(ramp_index[ordered[i]] for i in tri_a), tuple(ramp_index[ordered[i]] for i in tri_b)]))
    return vertex_offset + len(ordered)


def _write_obj(scene: dict[str, Any]) -> None:
    scene_a, scene_b = scene["scene_a"], scene["scene_b"]
    lines: list[str] = [f"mtllib {OUT_OBJ.with_suffix('.mtl').name}", "o terrain_multi_ramp_composition"]
    face_blocks: list = []
    vertex_offset = 1

    vertex_offset = _write_terrain(lines, vertex_offset, scene_a["lower_built"], face_blocks)
    vertex_offset = _write_terrain(lines, vertex_offset, scene_a["upper_built"], face_blocks)
    vertex_offset = _write_ramp(
        lines, vertex_offset, scene_a["footprint"], scene_a["ramp_positions"], face_blocks,
        path_x_offset=scene_a_tool.PATH_X_OFFSET, ramp_z_offset=scene_a_tool.ramp_z_offset(),
        rotation_degrees=90.0, hinge_corner_x=scene_a_tool.HINGE_CORNER_X,
    )

    vertex_offset = _write_terrain(lines, vertex_offset, scene_b["lower_built"], face_blocks)
    vertex_offset = _write_terrain(lines, vertex_offset, scene_b["upper_built"], face_blocks)
    vertex_offset = _write_ramp(
        lines, vertex_offset, scene_b["footprint"], scene_b["ramp_positions"], face_blocks,
        path_x_offset=scene_b["shifted_path_x_offset"], ramp_z_offset=scene_b["shifted_ramp_z_offset"],
        rotation_degrees=scene_b_tool.ROTATION_DEGREES, hinge_corner_x=scene_b_tool.HINGE_CORNER_X,
    )

    for material, tris in face_blocks:
        lines.append(f"usemtl {material}")
        for a, b, c in tris:
            lines.append(f"f {a} {b} {c}")

    OUT_OBJ.write_text("\n".join(lines) + "\n")

    mtl_lines = []
    for name, color in (("grass_flat", GRASS_COLOR), ("dirt_flat", DIRT_COLOR), ("gap_fill_flat", GAP_FILL_COLOR)):
        mtl_lines.append(f"newmtl {name}")
        mtl_lines.append(f"Kd {color[0]} {color[1]} {color[2]}")
        mtl_lines.append("illum 1")
    OUT_OBJ.with_suffix(".mtl").write_text("\n".join(mtl_lines) + "\n")


def main() -> int:
    scene = build_scene()
    scene_a, scene_b = scene["scene_a"], scene["scene_b"]
    for label, built in (("a_lower", scene_a["lower_built"]), ("a_upper", scene_a["upper_built"]), ("b_lower", scene_b["lower_built"]), ("b_upper", scene_b["upper_built"])):
        if built.get("status") != "BUILT":
            print(f"terrain build failed for {label}:", built.get("errors"))
            return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_obj(scene)

    manifest = {
        "scene_a": {
            "rotation_degrees": 90.0,
            "far_segment_cells": scene_a_tool.FAR_SEGMENT_CELLS,
            "required_rise": scene_a_tool.REQUIRED_RISE,
            "lower_attachment_matches": scene_a["attachment"]["lower_attachment_matches"],
            "upper_attachment_matches": scene_a["attachment"]["upper_attachment_matches"],
        },
        "scene_b": {
            "rotation_degrees": scene_b_tool.ROTATION_DEGREES,
            "far_segment_cells": scene_b_tool.FAR_SEGMENT_CELLS,
            "required_rise": scene_b_tool.REQUIRED_RISE,
            "offset": list(SCENE_B_OFFSET),
            "lower_attachment_matches": scene_b["attachment"]["lower_attachment_matches"],
            "upper_attachment_matches": scene_b["attachment"]["upper_attachment_matches"],
        },
        "obj": OUT_OBJ.name,
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {OUT_OBJ}")
    print(f"wrote {OUT_MANIFEST}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
