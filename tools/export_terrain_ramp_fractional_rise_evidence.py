#!/usr/bin/env python3
"""Second terrain integration: non-integer rise.

The prior proof (gate_pixel_geometry_terrain_ramp_integration_v1.py) chose
its worked example so the rise (5.0) happened to be a whole number of
height layers -- terrain's own elevation authority represented it
directly (elevation=1.0, max_height_layers=5 -> world_cell_y=5). That
left an open question: does the seam only close because the rise happened
to fit the terrain's own integer quantization?

This proof answers no. Worked example:

    ramp cells    = 5
    cell metric   = 1.0
    required rise = 2.5   (not a whole number)

    angle = 30 degrees
    run   = sqrt(5^2 - 2.5^2) = 4.330127018922193...

The upper terrain block is built through the UNMODIFIED consumer/builder
exactly like the lower one -- same elevation (0.0), same "natural"
placement parameters, entirely inside its own ordinary integer-layer
space. It is NEVER asked to produce world_cell_y=2.5; max_height_layers
stays an arbitrary whole number and elevation stays 0.0. The fractional
rise is reached entirely by one explicit whole-artifact rigid translation
(terrain_ramp_integration_v1.translate_built_geometry), applied AFTER the
terrain builder has already finished -- proving terrain-local height
authority and world-placement authority are two separate concepts, not
one conflated one.
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
    translate_built_geometry,
    verify_attachment,
)
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
OUT_OBJ = FIXTURES / "terrain_ramp_fractional_rise.obj"
OUT_MANIFEST = FIXTURES / "terrain_ramp_fractional_rise_manifest.json"

COLUMNS = 8
ROWS = 4
DIRT_COLUMNS = {3, 4}
GRASS_COLOR = [0.25, 0.55, 0.20, 1.0]
DIRT_COLOR = [0.50, 0.35, 0.20, 1.0]
GAP_FILL_COLOR = [0.35, 0.30, 0.25, 1.0]

FAR_SEGMENT_CELLS = 5     # worked example: ramp cells = 5
REQUIRED_RISE = 2.5        # non-integer rise -- the whole point of this proof
HINGE_CORNER_X = 1
RAMP_WIDTH = HINGE_CORNER_X + FAR_SEGMENT_CELLS  # 6
PATH_WIDTH_CELLS = len(DIRT_COLUMNS)              # 2

# Deliberately NOT derived from the rise -- terrain's own vertical metric
# never has to represent 2.5, so this can be any ordinary whole number.
MAX_HEIGHT_LAYERS = 1
TERRAIN_ELEVATION = 0.0  # BOTH blocks: terrain-local height authority never leaves world_cell_y=0

CENTER_COLUMN = (min(DIRT_COLUMNS) + max(DIRT_COLUMNS)) / 2.0  # 3.5
PATH_X_OFFSET = -PATH_WIDTH_CELLS / 2.0                          # -1.0
CENTER_ROW = (ROWS - 1) + 0.5  # 3.5: the SAME "natural" row placement for both blocks


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
    return float(HINGE_CORNER_X)


def _terrain_pixel_field() -> list[dict[str, Any]]:
    cells = []
    for field_y in range(ROWS):
        for field_x in range(COLUMNS):
            is_dirt = field_x in DIRT_COLUMNS
            cells.append(
                {
                    "field_x": field_x,
                    "field_y": field_y,
                    "elevation": TERRAIN_ELEVATION,
                    "terrain": "dirt" if is_dirt else "grass",
                    "recipe": "default.generic",
                    "base_color": DIRT_COLOR if is_dirt else GRASS_COLOR,
                }
            )
    return cells


def _terrain_request(*, request_id: str) -> dict[str, Any]:
    """The SAME ordinary request shape for both blocks -- neither one is
    ever asked to represent a fractional elevation or a rise-derived
    max_height_layers. Only request_id differs."""
    return {
        "packet_type": "trixel32d_surface_request",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": request_id,
            "source_scene_id": "scene.terrain_ramp_fractional_rise_proof.001",
            "provenance": {
                "source_scene_id": "scene.terrain_ramp_fractional_rise_proof.001",
                "topology_artifact_id": "terrain_ramp_fractional_rise.synthetic_field.001",
                "metric_layout_artifact_id": "terrain_ramp_fractional_rise.metric.001",
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
            "center_row": CENTER_ROW,
        },
        "vertical_metric": {
            "granted_by": "cartographer",
            "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
            "unit": "meter",
            "max_height_layers": MAX_HEIGHT_LAYERS,
            "source_artifact_id": "terrain_ramp_fractional_rise.metric.001",
        },
        "gap_fill": {
            "enabled": True,
            "mode": "CONNECTED_SLAB",
            "adjacency_policy": "SHARED_EDGE_STITCHED",
            "resolved_color": GAP_FILL_COLOR,
            "thickness_local_units": 0.5,
        },
        "pixel_field_data": _terrain_pixel_field(),
    }


def build_lower_terrain_request() -> dict[str, Any]:
    return _terrain_request(request_id="t32dreq_lower_terrain_fractional")


def build_upper_terrain_request() -> dict[str, Any]:
    """Identical shape to the lower request -- built as if it were just
    another copy of the same flat block, not yet placed anywhere near the
    ramp. Placement happens afterward, explicitly, in build_scene()."""
    return _terrain_request(request_id="t32dreq_upper_terrain_fractional")


def upper_placement_translation(solved: Any) -> tuple[float, float, float]:
    """The one explicit whole-artifact rigid translation that places the
    upper terrain. Derived from the ramp's own solved geometry: the
    natural (untranslated) near-the-ramp edge of the upper block -- built
    with the SAME center_row as the lower block -- sits at
    (Y=0, Z=CENTER_ROW+0.5); it must land at (Y=REQUIRED_RISE, Z=-run)."""
    natural_near_edge_z = CENTER_ROW + 0.5
    target_z = -solved.run
    target_y = REQUIRED_RISE
    return (0.0, target_y - 0.0, target_z - natural_near_edge_z)


def build_scene() -> dict[str, Any]:
    footprint, ramp_positions, ramp_info = build_ramp()
    solved = ramp_info["solved"]

    lower_request = build_lower_terrain_request()
    upper_request = build_upper_terrain_request()
    lower_built = consume_surface_request_packet(lower_request, recipe_root=RECIPE_ROOT)
    upper_built_natural = consume_surface_request_packet(upper_request, recipe_root=RECIPE_ROOT)

    translation = upper_placement_translation(solved)
    upper_built = translate_built_geometry(upper_built_natural, translation)

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
        "upper_built_natural": upper_built_natural,
        "upper_built": upper_built,
        "translation": translation,
        "attachment": attachment,
    }


def _write_obj(scene: dict[str, Any]) -> None:
    lines: list[str] = [f"mtllib {OUT_OBJ.with_suffix('.mtl').name}", "o terrain_ramp_fractional_rise"]
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
        world = ramp_position_to_world(ramp_positions[addr], path_x_offset=PATH_X_OFFSET, ramp_z_offset=ramp_z_offset())
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
    if scene["lower_built"].get("status") != "BUILT" or scene["upper_built_natural"].get("status") != "BUILT":
        print("terrain build failed:", scene["lower_built"].get("errors"), scene["upper_built_natural"].get("errors"))
        return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_obj(scene)

    solved = scene["ramp_info"]["solved"]
    manifest = {
        "far_segment_cells": FAR_SEGMENT_CELLS,
        "required_rise": REQUIRED_RISE,
        "solved": {"angle_degrees": solved.angle_degrees, "run": solved.run, "chain_length": solved.chain_length},
        "terrain_elevation_both_blocks": TERRAIN_ELEVATION,
        "max_height_layers": MAX_HEIGHT_LAYERS,
        "upper_placement_translation": list(scene["translation"]),
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
