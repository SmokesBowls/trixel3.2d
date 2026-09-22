#!/usr/bin/env python3
"""Fifth terrain integration proof: shared-terrain hub.

    upper B
       |
       | ramp B travels +X (rotation=0)
       |
lower A -- CENTRAL TERRAIN (built ONCE) -- upper A
       |
       | ramp A travels -Z (rotation=90)
       |
    (ramp A's own upper terrain, further -Z, not shown above)

One terrain block becomes shared composition authority: two
independently transformed ramps attach to two DIFFERENT declared edges of
that SAME block. The question under test:

    Can one terrain artifact participate in two independent ramp seams
    without either ramp corrupting, duplicating, or redefining the other
    attachment?

Deliberately controlled, same discipline as the prior composition proof:
no new ramp mathematics, no new cell metric. Both ramps reuse the exact
same already-proven worked example (8 ramp cells, required rise 5.0) and
the exact same frozen embedding call. The central terrain is an 8x8 grass
block with a plus-shaped dirt path: DIRT_COLUMNS={3,4} reaches its low_z
edge (where ramp A attaches, exactly the same column positions the
integer-rise control already used) and DIRT_ROWS={3,4} reaches its high_x
edge (where ramp B attaches, exactly the same row positions the
rotated-orientation proof already used). Because the central block reuses
the SAME center_column (3.5, from the control) and the SAME center_row
(3.5, from the rotated proof), each ramp's own path-width offset is
completely unchanged from its own frozen proof -- only each ramp's
travel-direction offset shifts, by an amount derived directly from where
the central block's own edges actually land, not chosen to make it fit.
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
    terrain_attachment_edge,
    terrain_attachment_edge_x,
    translate_built_geometry,
    verify_attachment_edges,
)
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

import export_terrain_ramp_integration_evidence as scene_a_tool
import export_terrain_ramp_rotated_orientation_evidence as scene_b_tool

RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
OUT_OBJ = FIXTURES / "terrain_hub_multi_ramp.obj"
OUT_MANIFEST = FIXTURES / "terrain_hub_multi_ramp_manifest.json"

GRASS_COLOR = scene_a_tool.GRASS_COLOR
DIRT_COLOR = scene_a_tool.DIRT_COLOR
GAP_FILL_COLOR = scene_a_tool.GAP_FILL_COLOR

# Central hub: an 8x8 grass block with a plus-shaped dirt path. DIRT_COLUMNS
# reaches the low_z edge (ramp A, same columns as the control). DIRT_ROWS
# reaches the high_x edge (ramp B, same rows as the rotated proof).
CENTRAL_COLUMNS = 8
CENTRAL_ROWS = 8
DIRT_COLUMNS = {3, 4}
DIRT_ROWS = {3, 4}

# Reusing the control's own CENTER_COLUMN (3.5) and the rotated proof's own
# CENTER_ROW (3.5) means each ramp's path-width offset needs NO change at
# all -- only each ramp's travel-direction offset shifts.
CENTER_COLUMN_CENTRAL = (min(DIRT_COLUMNS) + max(DIRT_COLUMNS)) / 2.0  # 3.5
CENTER_ROW_CENTRAL = (min(DIRT_ROWS) + max(DIRT_ROWS)) / 2.0            # 3.5
MAX_HEIGHT_LAYERS = scene_a_tool.REQUIRED_RISE  # 5.0, shared with both ramps' rise

assert CENTER_COLUMN_CENTRAL == scene_a_tool.CENTER_COLUMN
assert CENTER_ROW_CENTRAL == scene_b_tool.CENTER_ROW


def central_low_z_edge_z() -> float:
    """Where the central block's low_z (ramp-A-facing) edge actually
    lands, computed from the block's own declared geometry -- never
    assumed."""
    return (CENTER_ROW_CENTRAL - (CENTRAL_ROWS - 1)) - 0.5


def central_high_x_edge_x() -> float:
    """Where the central block's high_x (ramp-B-facing) edge actually
    lands, computed from the block's own declared geometry."""
    return ((CENTRAL_COLUMNS - 1) - CENTER_COLUMN_CENTRAL) + 0.5


def original_scene_a_lower_edge_z() -> float:
    """Where the control's OWN lower terrain's attachment edge sits, by
    the control's own frozen formula -- world Z = -hinge_corner_x +
    ramp_z_offset() = 0.0."""
    return -float(scene_a_tool.HINGE_CORNER_X) + scene_a_tool.ramp_z_offset()


def original_scene_b_lower_edge_x() -> float:
    """Where the rotated proof's OWN lower terrain's attachment edge sits,
    by its own frozen formula -- world X = hinge_corner_x + path_x_offset
    = 0.0."""
    return float(scene_b_tool.HINGE_CORNER_X) + scene_b_tool.RAMP_X_OFFSET


def shift_a() -> tuple[float, float, float]:
    """The whole-scene rigid shift that moves ramp A + upper A (reused
    verbatim from the control) so ramp A's near edge lands exactly on the
    central hub's own low_z edge, instead of on the control's own lower
    terrain (which the hub replaces)."""
    return (0.0, 0.0, central_low_z_edge_z() - original_scene_a_lower_edge_z())


def shift_b() -> tuple[float, float, float]:
    """The analogous shift for ramp B + upper B."""
    return (central_high_x_edge_x() - original_scene_b_lower_edge_x(), 0.0, 0.0)


def build_central_request() -> dict[str, Any]:
    cells = []
    for field_y in range(CENTRAL_ROWS):
        for field_x in range(CENTRAL_COLUMNS):
            is_dirt = field_x in DIRT_COLUMNS or field_y in DIRT_ROWS
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
    return {
        "packet_type": "trixel32d_surface_request",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": "t32dreq_central_hub_terrain",
            "source_scene_id": "scene.terrain_hub_multi_ramp_proof.001",
            "provenance": {
                "source_scene_id": "scene.terrain_hub_multi_ramp_proof.001",
                "topology_artifact_id": "terrain_hub_multi_ramp.synthetic_field.001",
                "metric_layout_artifact_id": "terrain_hub_multi_ramp.metric.001",
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
            "field_width_columns": CENTRAL_COLUMNS,
            "field_height_rows": CENTRAL_ROWS,
            "cell_width": 1.0,
            "cell_depth": 1.0,
            "center_column": CENTER_COLUMN_CENTRAL,
            "center_row": CENTER_ROW_CENTRAL,
        },
        "vertical_metric": {
            "granted_by": "cartographer",
            "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
            "unit": "meter",
            "max_height_layers": MAX_HEIGHT_LAYERS,
            "source_artifact_id": "terrain_hub_multi_ramp.metric.001",
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


def build_ramp_and_upper(scene_tool, *, shift: tuple[float, float, float], rotation_degrees: float) -> dict[str, Any]:
    """Reuse an already-frozen single-ramp scene's ramp + upper terrain
    verbatim, then move BOTH as one rigid whole by `shift` -- exactly the
    technique already proven in the multi-ramp composition proof, just
    with the shift derived from the central hub's geometry instead of an
    arbitrary large separation."""
    raw = scene_tool.build_scene()
    upper_built = translate_built_geometry(raw["upper_built"], shift)

    if rotation_degrees == 90.0:
        shifted_offset_kwargs = dict(path_x_offset=scene_tool.PATH_X_OFFSET, ramp_z_offset=scene_tool.ramp_z_offset() + shift[2])
    else:
        shifted_offset_kwargs = dict(path_x_offset=scene_tool.RAMP_X_OFFSET + shift[0], ramp_z_offset=scene_tool.PATH_Z_OFFSET)

    near_world = [
        ramp_position_to_world(pos, rotation_degrees=rotation_degrees, **shifted_offset_kwargs)
        for (x, r), pos in raw["ramp_positions"].items()
        if x == scene_tool.HINGE_CORNER_X
    ]
    far_world = [
        ramp_position_to_world(pos, rotation_degrees=rotation_degrees, **shifted_offset_kwargs)
        for (x, r), pos in raw["ramp_positions"].items()
        if x == scene_tool.RAMP_WIDTH
    ]

    return {
        "footprint": raw["footprint"],
        "ramp_positions": raw["ramp_positions"],
        "ramp_info": raw["ramp_info"],
        "upper_built": upper_built,
        "offset_kwargs": shifted_offset_kwargs,
        "rotation_degrees": rotation_degrees,
        "near_world": near_world,
        "far_world": far_world,
    }


def build_scene() -> dict[str, Any]:
    central_request = build_central_request()
    central_built = consume_surface_request_packet(central_request, recipe_root=RECIPE_ROOT)  # built ONCE

    ramp_a = build_ramp_and_upper(scene_a_tool, shift=shift_a(), rotation_degrees=90.0)
    ramp_b = build_ramp_and_upper(scene_b_tool, shift=shift_b(), rotation_degrees=0.0)

    central_a_edge = terrain_attachment_edge(central_built, field_x_values=DIRT_COLUMNS, field_y=CENTRAL_ROWS - 1, edge="low_z")
    central_b_edge = terrain_attachment_edge_x(central_built, field_y_values=DIRT_ROWS, field_x=CENTRAL_COLUMNS - 1, edge="high_x")

    upper_a_edge = terrain_attachment_edge(
        ramp_a["upper_built"], field_x_values=DIRT_COLUMNS, field_y=0, edge="high_z"
    )
    upper_b_edge = terrain_attachment_edge_x(
        ramp_b["upper_built"], field_y_values=DIRT_ROWS, field_x=0, edge="low_x"
    )

    attachment_a = verify_attachment_edges(
        ramp_near_world=ramp_a["near_world"], ramp_far_world=ramp_a["far_world"],
        lower_edge=central_a_edge, upper_edge=upper_a_edge,
        rotation_degrees=90.0, **ramp_a["offset_kwargs"],
    )
    attachment_b = verify_attachment_edges(
        ramp_near_world=ramp_b["near_world"], ramp_far_world=ramp_b["far_world"],
        lower_edge=central_b_edge, upper_edge=upper_b_edge,
        rotation_degrees=0.0, **ramp_b["offset_kwargs"],
    )

    return {
        "central_built": central_built,
        "ramp_a": ramp_a,
        "ramp_b": ramp_b,
        "attachment_a": attachment_a,
        "attachment_b": attachment_b,
        "central_a_edge": central_a_edge,
        "central_b_edge": central_b_edge,
    }


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


def _write_ramp(lines: list[str], vertex_offset: int, ramp: dict[str, Any], face_blocks: list, *, hinge_corner_x: int) -> int:
    footprint = ramp["footprint"]
    width = footprint["width"]
    positions = ramp["ramp_positions"]
    ordered = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    ramp_index = {addr: vertex_offset + i for i, addr in enumerate(ordered)}
    for addr in ordered:
        world = ramp_position_to_world(positions[addr], rotation_degrees=ramp["rotation_degrees"], **ramp["offset_kwargs"])
        lines.append(f"v {world[0]} {world[1]} {world[2]}")
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    for prov in compiled["primitive_provenance"]:
        if prov["cell_address"][0] < hinge_corner_x:
            continue
        start = prov["primitive_start"] * 3
        tri_a = compiled["indices"][start : start + 3]
        tri_b = compiled["indices"][start + 3 : start + 6]
        face_blocks.append(("dirt_flat", [tuple(ramp_index[ordered[i]] for i in tri_a), tuple(ramp_index[ordered[i]] for i in tri_b)]))
    return vertex_offset + len(ordered)


def _write_obj(scene: dict[str, Any]) -> None:
    lines: list[str] = [f"mtllib {OUT_OBJ.with_suffix('.mtl').name}", "o terrain_hub_multi_ramp"]
    face_blocks: list = []
    vertex_offset = 1

    vertex_offset = _write_terrain(lines, vertex_offset, scene["central_built"], face_blocks)
    vertex_offset = _write_ramp(lines, vertex_offset, scene["ramp_a"], face_blocks, hinge_corner_x=scene_a_tool.HINGE_CORNER_X)
    vertex_offset = _write_terrain(lines, vertex_offset, scene["ramp_a"]["upper_built"], face_blocks)
    vertex_offset = _write_ramp(lines, vertex_offset, scene["ramp_b"], face_blocks, hinge_corner_x=scene_b_tool.HINGE_CORNER_X)
    vertex_offset = _write_terrain(lines, vertex_offset, scene["ramp_b"]["upper_built"], face_blocks)

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
    for label, built in (
        ("central", scene["central_built"]),
        ("upper_a", scene["ramp_a"]["upper_built"]),
        ("upper_b", scene["ramp_b"]["upper_built"]),
    ):
        if built.get("status") != "BUILT":
            print(f"terrain build failed for {label}:", built.get("errors"))
            return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_obj(scene)

    manifest = {
        "central": {"columns": CENTRAL_COLUMNS, "rows": CENTRAL_ROWS, "dirt_columns": sorted(DIRT_COLUMNS), "dirt_rows": sorted(DIRT_ROWS)},
        "shift_a": list(shift_a()),
        "shift_b": list(shift_b()),
        "attachment_a": {
            "lower_attachment_matches": scene["attachment_a"]["lower_attachment_matches"],
            "upper_attachment_matches": scene["attachment_a"]["upper_attachment_matches"],
        },
        "attachment_b": {
            "lower_attachment_matches": scene["attachment_b"]["lower_attachment_matches"],
            "upper_attachment_matches": scene["attachment_b"]["upper_attachment_matches"],
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
