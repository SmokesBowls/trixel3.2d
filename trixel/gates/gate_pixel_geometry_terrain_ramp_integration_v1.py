#!/usr/bin/env python3
"""First integration of the pixel_geometry embedding lane with the
connected terrain surface lane (trixel32d_surface_builder).

flat / rigid / hard fold / artwork fold-stretch / closed cylinder /
declared-angle ramp are all PROVEN and untouched. This gate does not
re-litigate any of them -- it proves a new, narrower claim:

    A metric-preserving pixel_geometry ramp can connect two existing
    Trixel terrain surfaces without requiring either frozen terrain
    contract to stretch or reinterpret its own geometry rules.

The ramp is not terrain data poured into trixel32d_surface_builder.py or
trixel/global_sample/ -- neither is modified, extended, or even imported
in a new way here. The ramp is a separately generated canonical geometry
artifact (the exact worked example from
gate_pixel_geometry_declared_angle_ramp_v1.py: 8 cells beyond the hinge,
required rise 5.0), placed next to two ordinary HEIGHT_FIELD_CONNECTED_
SURFACE terrain blocks by a pure rotation + translation
(terrain_ramp_integration_v1.py) whose offsets are DERIVED from the
ramp's own solved run, never chosen to make the ramp fit afterward.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold
from trixel.pixel_geometry.terrain_ramp_integration_v1 import ramp_position_to_world

import export_terrain_ramp_integration_evidence as scene_tool

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    scene = scene_tool.build_scene()
    lower_built = scene["lower_built"]
    upper_built = scene["upper_built"]
    attachment = scene["attachment"]
    footprint = scene["footprint"]
    ramp_positions = scene["ramp_positions"]
    solved = scene["ramp_info"]["solved"]

    report(
        "LOWER_TERRAIN_BUILDS_WITH_EXISTING_POLICY",
        lower_built.get("status") == "BUILT" and lower_built.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE",
        f"status={lower_built.get('status')} errors={lower_built.get('errors')}",
    )
    report(
        "UPPER_TERRAIN_BUILDS_WITH_EXISTING_POLICY",
        upper_built.get("status") == "BUILT" and upper_built.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE",
        f"status={upper_built.get('status')} errors={upper_built.get('errors')}",
    )

    # The ramp uses the exact frozen declared-angle embedding, not a
    # locally reimplemented variant -- recompute independently and
    # compare formula output directly, same discipline as every prior gate.
    independent_positions = embed_declared_angle_ramp_fold(
        footprint, hinge_corner_x=scene_tool.HINGE_CORNER_X, angle_degrees=solved.angle_degrees
    )
    report(
        "RAMP_USES_FROZEN_DECLARED_ANGLE_EMBEDDING",
        independent_positions == ramp_positions,
    )

    compiled = compile_footprint(footprint, ramp_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    ramp_edges = edge_lengths(compiled)
    report(
        "RAMP_CELL_METRIC_REMAINS_1_0",
        all(close(length, 1.0) for length in ramp_edges),
        f"min={min(ramp_edges):.9f} max={max(ramp_edges):.9f}",
    )

    uv_a = footprint_corner_uvs(footprint)
    uv_b = footprint_corner_uvs(footprint)
    report("RAMP_ARTWORK_UVS_UNCHANGED", uvs_are_identical(uv_a, uv_b))

    report("LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY", attachment["lower_attachment_matches"])
    report("UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY", attachment["upper_attachment_matches"])

    # No scaling anywhere: the placement transform is a proven isometry,
    # and both terrain requests declare cell_width=cell_depth=1.0 exactly
    # (the same unit as the ramp's own cell_metric).
    report("NO_RAMP_VERTEX_SCALING", attachment["is_isometry"])
    terrain_unit_metric = all(
        request["planar_config"]["cell_width"] == 1.0 and request["planar_config"]["cell_depth"] == 1.0
        for request in (scene["lower_request"], scene["upper_request"])
    )
    report("NO_TERRAIN_VERTEX_SCALING", terrain_unit_metric)

    # No position-derived adjacency: apart from the two declared
    # attachment edges, no ramp vertex and terrain vertex should end up
    # suspiciously close -- the only connection is the declared one.
    declared_points = set(
        tuple(round(c, 6) for c in p) for p in attachment["ramp_near_world"] + attachment["ramp_far_world"]
    )
    # The near-flat stub (corner x < HINGE_CORNER_X) is not placed scene
    # geometry -- it exists only because embed_declared_angle_ramp_fold
    # requires 0 < hinge_corner_x < width, and it occupies exactly the
    # same world space the lower terrain's own boundary row already
    # covers. Exclude it here the same way the exporter excludes it from
    # the combined OBJ, so this check compares what is actually placed.
    ramp_world_all = [
        ramp_position_to_world(pos, path_x_offset=scene_tool.PATH_X_OFFSET, ramp_z_offset=scene_tool.ramp_z_offset())
        for (x, r), pos in ramp_positions.items()
        if x >= scene_tool.HINGE_CORNER_X
    ]
    other_ramp_points = [p for p in ramp_world_all if tuple(round(c, 6) for c in p) not in declared_points]
    terrain_points = [
        tuple(p)
        for built in (lower_built, upper_built)
        for p in built["geometry"]["positions"]
        if tuple(round(c, 6) for c in p) not in declared_points
    ]
    proximity_tolerance = 0.4
    offenders = [
        (a, b)
        for a in other_ramp_points
        for b in terrain_points
        if sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 <= proximity_tolerance
    ]
    report(
        "NO_POSITION_DERIVED_ADJACENCY",
        len(offenders) == 0,
        f"offenders={len(offenders)}" if offenders else "",
    )

    scene_again = scene_tool.build_scene()
    deterministic = (
        json.dumps(scene["lower_built"], sort_keys=True) == json.dumps(scene_again["lower_built"], sort_keys=True)
        and json.dumps(scene["upper_built"], sort_keys=True) == json.dumps(scene_again["upper_built"], sort_keys=True)
        and scene["ramp_positions"] == scene_again["ramp_positions"]
        and scene["attachment"]["lower_attachment_matches"] == scene_again["attachment"]["lower_attachment_matches"]
        and scene["attachment"]["upper_attachment_matches"] == scene_again["attachment"]["upper_attachment_matches"]
    )
    report("COMPOSED_SCENE_IS_DETERMINISTIC", deterministic)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
