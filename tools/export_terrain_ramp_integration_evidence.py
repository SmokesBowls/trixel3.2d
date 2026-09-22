#!/usr/bin/env python3
"""Compose and export the first integration of the pixel_geometry embedding
lane with the connected terrain surface lane (trixel32d_surface_builder):

    LOWER TERRAIN (existing HEIGHT_FIELD_CONNECTED_SURFACE, untouched)
            |  exact attachment seam
            v
    DECLARED-ANGLE RAMP (pixel_geometry, frozen embedding, metric-preserving)
            |  exact attachment seam
            v
    UPPER TERRAIN (existing HEIGHT_FIELD_CONNECTED_SURFACE, untouched)

Neither trixel32d_surface_builder.py, trixel32d_surface_consumer.py, nor
anything under trixel/global_sample/ is modified or extended. The ramp is
not terrain data poured into either contract -- it is a separately
generated canonical geometry artifact, placed by a pure rotation +
translation (trixel/pixel_geometry/terrain_ramp_integration_v1.py) derived
FROM the ramp's own solved run/rise, never the other way around.

Scene: two 8-column x 4-row terrain blocks, pattern per row
"GGGDDGGG" (columns 3 and 4 are the dirt path), connected by a ramp whose
math is exactly the worked example already proven in
gate_pixel_geometry_declared_angle_ramp_v1.py: 8 cells beyond the hinge,
required rise 5.0.
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
from trixel.pixel_geometry.terrain_ramp_integration_v1 import ramp_position_to_world, verify_attachment
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
OUT_OBJ = FIXTURES / "terrain_ramp_integration.obj"
OUT_MANIFEST = FIXTURES / "terrain_ramp_integration_manifest.json"

# --- Scene constants, all derived from the ramp's own solved geometry ----
COLUMNS = 8
ROWS = 4
DIRT_COLUMNS = {3, 4}
GRASS_COLOR = [0.25, 0.55, 0.20, 1.0]
DIRT_COLOR = [0.50, 0.35, 0.20, 1.0]
GAP_FILL_COLOR = [0.35, 0.30, 0.25, 1.0]

FAR_SEGMENT_CELLS = 8    # same worked example as gate_pixel_geometry_declared_angle_ramp_v1
REQUIRED_RISE = 5.0
HINGE_CORNER_X = 1        # minimal near-flat stub; the terrain itself supplies the approach
RAMP_WIDTH = HINGE_CORNER_X + FAR_SEGMENT_CELLS  # 9
PATH_WIDTH_CELLS = len(DIRT_COLUMNS)              # 2, matches the ramp's row/width axis

MAX_HEIGHT_LAYERS = REQUIRED_RISE  # world_cell_y=5 at elevation=1.0, matching the ramp's rise exactly

CENTER_COLUMN = (min(DIRT_COLUMNS) + max(DIRT_COLUMNS)) / 2.0  # 3.5: dirt columns straddle world X=0
PATH_X_OFFSET = -PATH_WIDTH_CELLS / 2.0                               # -1.0


def solve_ramp() -> Any:
    return solve_ramp_run_and_angle(FAR_SEGMENT_CELLS, REQUIRED_RISE)


def build_ramp() -> tuple[dict, dict, dict]:
    solved = solve_ramp()
    payload = [["dirt_ramp" for _ in range(RAMP_WIDTH)] for _ in range(PATH_WIDTH_CELLS)]
    footprint = build_footprint(RAMP_WIDTH, PATH_WIDTH_CELLS, payload)
    positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved.angle_degrees)
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    return footprint, positions, {"solved": solved, "compiled": compiled}


def ramp_z_offset() -> float:
    return float(HINGE_CORNER_X)  # world_z(hinge_corner_x) = -hinge_corner_x + ramp_z_offset = 0


def center_row_lower() -> float:
    return (ROWS - 1) + 0.5  # lower terrain's far (low-Z) edge lands at world Z = 0


def center_row_upper(solved: Any) -> float:
    # upper terrain's near (high-Z) edge must land at the ramp's far-edge world Z = -run
    return -solved.run - 0.5


def _terrain_pixel_field(elevation: float) -> list[dict[str, Any]]:
    cells = []
    for field_y in range(ROWS):
        for field_x in range(COLUMNS):
            is_dirt = field_x in DIRT_COLUMNS
            cells.append(
                {
                    "field_x": field_x,
                    "field_y": field_y,
                    "elevation": elevation,
                    "terrain": "dirt" if is_dirt else "grass",
                    "recipe": "default.generic",
                    "base_color": DIRT_COLOR if is_dirt else GRASS_COLOR,
                }
            )
    return cells


def _terrain_request(*, request_id: str, elevation: float, center_row: float) -> dict[str, Any]:
    return {
        "packet_type": "trixel32d_surface_request",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": request_id,
            "source_scene_id": "scene.terrain_ramp_integration_proof.001",
            "provenance": {
                "source_scene_id": "scene.terrain_ramp_integration_proof.001",
                "topology_artifact_id": "terrain_ramp_integration.synthetic_field.001",
                "metric_layout_artifact_id": "terrain_ramp_integration.metric.001",
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
            "center_column": CENTER_COLUMN,
            "center_row": center_row,
        },
        "vertical_metric": {
            "granted_by": "cartographer",
            "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
            "unit": "meter",
            "max_height_layers": MAX_HEIGHT_LAYERS,
            "source_artifact_id": "terrain_ramp_integration.metric.001",
        },
        "gap_fill": {
            "enabled": True,
            "mode": "CONNECTED_SLAB",
            "adjacency_policy": "SHARED_EDGE_STITCHED",
            "resolved_color": GAP_FILL_COLOR,
            "thickness_local_units": 0.5,
        },
        "pixel_field_data": _terrain_pixel_field(elevation),
    }


def build_lower_terrain_request() -> dict[str, Any]:
    return _terrain_request(request_id="t32dreq_lower_terrain", elevation=0.0, center_row=center_row_lower())


def build_upper_terrain_request(solved: Any) -> dict[str, Any]:
    return _terrain_request(request_id="t32dreq_upper_terrain", elevation=1.0, center_row=center_row_upper(solved))


def build_scene() -> dict[str, Any]:
    """Build the whole composed scene through the UNMODIFIED terrain
    consumer/builder and the FROZEN ramp embedding, then verify the seam.
    Returns everything a gate or exporter needs, computed once."""
    footprint, ramp_positions, ramp_info = build_ramp()
    solved = ramp_info["solved"]

    lower_request = build_lower_terrain_request()
    upper_request = build_upper_terrain_request(solved)
    lower_built = consume_surface_request_packet(lower_request, recipe_root=RECIPE_ROOT)
    upper_built = consume_surface_request_packet(upper_request, recipe_root=RECIPE_ROOT)

    attachment = verify_attachment(
        ramp_positions=ramp_positions,
        lower_terrain_built=lower_built,
        upper_terrain_built=upper_built,
        hinge_corner_x=HINGE_CORNER_X,
        ramp_far_corner_x=RAMP_WIDTH,
        path_x_offset=PATH_X_OFFSET,
        ramp_z_offset=ramp_z_offset(),
        lower_field_x_values=DIRT_COLUMNS,
        lower_field_y=ROWS - 1,
        upper_field_x_values=DIRT_COLUMNS,
        upper_field_y=0,
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
    lines: list[str] = [f"mtllib {OUT_OBJ.with_suffix('.mtl').name}", "o terrain_ramp_integration"]
    vertex_offset = 1
    face_blocks: list[tuple[str, list[tuple[int, int, int]]]] = []

    def add_terrain(built: dict[str, Any], label: str) -> None:
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

    add_terrain(scene["lower_built"], "lower")
    add_terrain(scene["upper_built"], "upper")

    footprint = scene["footprint"]
    width = footprint["width"]
    ramp_positions = scene["ramp_positions"]
    ordered = sorted(ramp_positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    ramp_index = {addr: vertex_offset + i for i, addr in enumerate(ordered)}
    for addr in ordered:
        world = ramp_position_to_world(ramp_positions[addr], path_x_offset=PATH_X_OFFSET, ramp_z_offset=ramp_z_offset())
        lines.append(f"v {world[0]} {world[1]} {world[2]}")
    compiled = compile_footprint(footprint, ramp_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    for prov in compiled["primitive_provenance"]:
        # The near-flat stub cell (x < HINGE_CORNER_X) exists only because
        # embed_declared_angle_ramp_fold requires 0 < hinge_corner_x < width;
        # it occupies exactly the same world space the lower terrain's own
        # boundary row already covers, so it is not placed as scene geometry
        # -- only the sloped cells (x >= HINGE_CORNER_X) are.
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
        "placement": {
            "path_x_offset": PATH_X_OFFSET,
            "ramp_z_offset": ramp_z_offset(),
            "center_row_lower": center_row_lower(),
            "center_row_upper": center_row_upper(solved),
            "center_column": CENTER_COLUMN,
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
