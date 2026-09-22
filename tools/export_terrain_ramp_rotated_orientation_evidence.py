#!/usr/bin/env python3
"""Third terrain integration proof: rotated orientation.

    CONTROL   (gate_pixel_geometry_terrain_ramp_integration_v1)
        lower terrain
              |  ramp travels along -Z
        upper terrain

    ROTATED TEST  (this proof)
        lower terrain -- ramp travels along +X -- upper terrain

No new ramp mathematics, no new rise, no new artwork, no taper: this
reuses the EXACT SAME worked example as the integer-rise control (8 ramp
cells, required rise 5.0 -> angle 38.682 deg, run 6.245...). The only
thing that changes is rotation_degrees passed to
terrain_ramp_integration_v1.ramp_position_to_world (0.0 here instead of
the control's default 90.0), which sends the ramp's fold-direction axis
to world +X instead of world -Z.

The terrain block itself is the SAME shape as the control's, transposed:
where the control was 8 columns (path width, along X) x 4 rows (depth,
along Z) with a 2-column dirt path, this proof is 4 columns (depth, along
X) x 8 rows (path width, along Z) with a 2-row dirt path -- the direct
consequence of the path now needing to face an X-boundary edge instead of
a Z-boundary edge, not a new terrain concept.

The question under test: does the composition seam still close when the
ramp's intrinsic travel direction no longer coincides with the terrain
lane's original forward axis? Answering that requires keeping ramp-local,
terrain-local, and world coordinates genuinely distinct, and proving the
placement transform performs the conversion -- not an embedded assumption
that "the ramp always points north."
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold
from trixel.pixel_geometry.ramp_geometry_v1 import solve_ramp_run_and_angle
from trixel.pixel_geometry.terrain_ramp_integration_v1 import (
    ramp_position_to_world,
    terrain_attachment_edge_x,
    verify_attachment_edges,
)
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
OUT_OBJ = FIXTURES / "terrain_ramp_rotated_orientation.obj"
OUT_MANIFEST = FIXTURES / "terrain_ramp_rotated_orientation_manifest.json"

# Terrain block, transposed from the control: depth (toward/away from the
# ramp) is now along X (COLUMNS), path width is now along Z (ROWS).
COLUMNS = 4
ROWS = 8
DIRT_ROWS = {3, 4}
GRASS_COLOR = [0.25, 0.55, 0.20, 1.0]
DIRT_COLOR = [0.50, 0.35, 0.20, 1.0]
GAP_FILL_COLOR = [0.35, 0.30, 0.25, 1.0]

# Identical worked example to the integer-rise control -- no new ramp math.
FAR_SEGMENT_CELLS = 8
REQUIRED_RISE = 5.0
HINGE_CORNER_X = 1
RAMP_WIDTH = HINGE_CORNER_X + FAR_SEGMENT_CELLS  # 9
PATH_WIDTH_CELLS = len(DIRT_ROWS)                 # 2

MAX_HEIGHT_LAYERS = REQUIRED_RISE  # world_cell_y=5 at elevation=1.0, matching the rise exactly, as in the control

ROTATION_DEGREES = 0.0  # the only new variable: ramp travels along +X instead of -Z

CENTER_ROW = (min(DIRT_ROWS) + max(DIRT_ROWS)) / 2.0  # 3.5: dirt rows straddle world Z=0
PATH_Z_OFFSET = -PATH_WIDTH_CELLS / 2.0                # -1.0
RAMP_X_OFFSET = -float(HINGE_CORNER_X)                 # -1.0: ramp's near edge lands at world X=0


def solve_ramp() -> Any:
    return solve_ramp_run_and_angle(FAR_SEGMENT_CELLS, REQUIRED_RISE)


def build_ramp() -> tuple[dict, dict, dict]:
    solved = solve_ramp()
    payload = [["dirt_ramp" for _ in range(RAMP_WIDTH)] for _ in range(PATH_WIDTH_CELLS)]
    footprint = build_footprint(RAMP_WIDTH, PATH_WIDTH_CELLS, payload)
    positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved.angle_degrees)
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    return footprint, positions, {"solved": solved, "compiled": compiled}


def center_column_lower() -> float:
    return (COLUMNS - 1) + 0.5  # lower terrain's high-X (far) edge lands at world X = 0


def center_column_upper(solved: Any) -> float:
    return -solved.run - 0.5  # upper terrain's low-X (near) edge lands at world X = run


def _terrain_pixel_field() -> list[dict[str, Any]]:
    cells = []
    for field_y in range(ROWS):
        for field_x in range(COLUMNS):
            is_dirt = field_y in DIRT_ROWS
            cells.append(
                {
                    "field_x": field_x,
                    "field_y": field_y,
                    "elevation": 0.0,
                    "terrain": "dirt" if is_dirt else "grass",
                    "recipe": "default.generic",
                    "base_color": DIRT_COLOR if is_dirt else GRASS_COLOR,
                }
            )
    return cells


def _terrain_request(*, request_id: str, elevation_scale: float, center_column: float) -> dict[str, Any]:
    cells = _terrain_pixel_field()
    for cell in cells:
        cell["elevation"] = elevation_scale
    return {
        "packet_type": "trixel32d_surface_request",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": request_id,
            "source_scene_id": "scene.terrain_ramp_rotated_orientation_proof.001",
            "provenance": {
                "source_scene_id": "scene.terrain_ramp_rotated_orientation_proof.001",
                "topology_artifact_id": "terrain_ramp_rotated_orientation.synthetic_field.001",
                "metric_layout_artifact_id": "terrain_ramp_rotated_orientation.metric.001",
            },
        },
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "orientation": {
            "basis_authority": "VECTORS",
            "field_axis_binding": {
                "field_x_increases_along": "RIGHT",
                "field_y_increases_along": "FORWARD",
            },
            "tolerance": 0.0001,
            "vectors": {"right": [1.0, 0.0, 0.0], "forward": [0.0, 0.0, -1.0], "up": [0.0, 1.0, 0.0]},
        },
        "construction": {
            "appearance_policy": "RECIPE_REFERENCE",
            "ordering": "ROW_MAJOR",
            "topology_policy": "HEIGHT_FIELD_CONNECTED_SURFACE",
        },
        "planar_config": {
            "field_coverage": "DENSE",
            "field_width_columns": COLUMNS,
            "field_height_rows": ROWS,
            "cell_width": 1.0,
            "cell_depth": 1.0,
            "center_column": center_column,
            "center_row": CENTER_ROW,
        },
        "vertical_metric": {
            "granted_by": "cartographer",
            "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
            "unit": "meter",
            "max_height_layers": MAX_HEIGHT_LAYERS,
            "source_artifact_id": "terrain_ramp_rotated_orientation.metric.001",
        },
        "gap_fill": {
            "enabled": True,
            "mode": "CONNECTED_SLAB",
            "adjacency_policy": "SHARED_EDGE_STITCHED",
            "resolved_color": GAP_FILL_COLOR,
            "thickness_local_units": 0.5,
        },
        "pixel_field_data": cells,
    }


def build_lower_terrain_request() -> dict[str, Any]:
    return _terrain_request(request_id="t32dreq_lower_terrain_rotated", elevation_scale=0.0, center_column=center_column_lower())


def build_upper_terrain_request(solved: Any) -> dict[str, Any]:
    return _terrain_request(request_id="t32dreq_upper_terrain_rotated", elevation_scale=1.0, center_column=center_column_upper(solved))


def build_scene() -> dict[str, Any]:
    footprint, ramp_positions, ramp_info = build_ramp()
    solved = ramp_info["solved"]

    lower_request = build_lower_terrain_request()
    upper_request = build_upper_terrain_request(solved)
    lower_built = consume_surface_request_packet(lower_request, recipe_root=RECIPE_ROOT)
    upper_built = consume_surface_request_packet(upper_request, recipe_root=RECIPE_ROOT)

    ramp_near_world = [
        ramp_position_to_world(pos, path_x_offset=RAMP_X_OFFSET, ramp_z_offset=PATH_Z_OFFSET, rotation_degrees=ROTATION_DEGREES)
        for (x, r), pos in ramp_positions.items()
        if x == HINGE_CORNER_X
    ]
    ramp_far_world = [
        ramp_position_to_world(pos, path_x_offset=RAMP_X_OFFSET, ramp_z_offset=PATH_Z_OFFSET, rotation_degrees=ROTATION_DEGREES)
        for (x, r), pos in ramp_positions.items()
        if x == RAMP_WIDTH
    ]
    # Lower terrain sits BEFORE the ramp along the direction of travel (+X):
    # its HIGH-X edge faces the ramp. Upper terrain sits AFTER: its LOW-X
    # edge faces the ramp. Opposite polarity from the control's low_z/high_z
    # pairing -- a direct consequence of the rotation, not a new concept.
    lower_edge = terrain_attachment_edge_x(lower_built, field_y_values=DIRT_ROWS, field_x=COLUMNS - 1, edge="high_x")
    upper_edge = terrain_attachment_edge_x(upper_built, field_y_values=DIRT_ROWS, field_x=0, edge="low_x")

    attachment = verify_attachment_edges(
        ramp_near_world=ramp_near_world,
        ramp_far_world=ramp_far_world,
        lower_edge=lower_edge,
        upper_edge=upper_edge,
        path_x_offset=RAMP_X_OFFSET,
        ramp_z_offset=PATH_Z_OFFSET,
        rotation_degrees=ROTATION_DEGREES,
    )

    return {
        "footprint": footprint,
        "ramp_positions": ramp_positions,
        "ramp_info": ramp_info,
        "lower_request": lower_request,
        "upper_request": upper_request,
        "lower_built": lower_built,
        "upper_built": upper_built,
        "attachment": attachment,
    }


def _write_obj(scene: dict[str, Any]) -> None:
    lines: list[str] = [f"mtllib {OUT_OBJ.with_suffix('.mtl').name}", "o terrain_ramp_rotated_orientation"]
    vertex_offset = 1
    face_blocks: list[tuple[str, list[tuple[int, int, int]]]] = []

    def add_terrain(built: dict[str, Any]) -> None:
        nonlocal vertex_offset
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
                tris = [(quad[0], quad[1], quad[2]), (quad[1], quad[3], quad[2])]
                face_blocks.append((mat, tris))
        vertex_offset += len(positions)

    add_terrain(scene["lower_built"])
    add_terrain(scene["upper_built"])

    footprint = scene["footprint"]
    width = footprint["width"]
    ramp_positions = scene["ramp_positions"]
    ordered = sorted(ramp_positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    ramp_index = {addr: vertex_offset + i for i, addr in enumerate(ordered)}
    for addr in ordered:
        world = ramp_position_to_world(
            ramp_positions[addr], path_x_offset=RAMP_X_OFFSET, ramp_z_offset=PATH_Z_OFFSET, rotation_degrees=ROTATION_DEGREES
        )
        lines.append(f"v {world[0]} {world[1]} {world[2]}")
    compiled = compile_footprint(footprint, ramp_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    for prov in compiled["primitive_provenance"]:
        if prov["cell_address"][0] < HINGE_CORNER_X:
            continue
        start = prov["primitive_start"] * 3
        tri_a = compiled["indices"][start : start + 3]
        tri_b = compiled["indices"][start + 3 : start + 6]
        face_blocks.append(("dirt_flat", [tuple(ramp_index[ordered[i]] for i in tri_a), tuple(ramp_index[ordered[i]] for i in tri_b)]))
    vertex_offset += len(ordered)

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
    if scene["lower_built"].get("status") != "BUILT" or scene["upper_built"].get("status") != "BUILT":
        print("terrain build failed:", scene["lower_built"].get("errors"), scene["upper_built"].get("errors"))
        return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_obj(scene)

    solved = scene["ramp_info"]["solved"]
    manifest = {
        "far_segment_cells": FAR_SEGMENT_CELLS,
        "required_rise": REQUIRED_RISE,
        "solved": {"angle_degrees": solved.angle_degrees, "run": solved.run, "chain_length": solved.chain_length},
        "rotation_degrees": ROTATION_DEGREES,
        "placement": {
            "path_x_offset_param": RAMP_X_OFFSET,
            "ramp_z_offset_param": PATH_Z_OFFSET,
            "center_column_lower": center_column_lower(),
            "center_column_upper": center_column_upper(solved),
            "center_row": CENTER_ROW,
        },
        "attachment": {
            "lower_attachment_matches": scene["attachment"]["lower_attachment_matches"],
            "upper_attachment_matches": scene["attachment"]["upper_attachment_matches"],
            "is_isometry": scene["attachment"]["is_isometry"],
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
