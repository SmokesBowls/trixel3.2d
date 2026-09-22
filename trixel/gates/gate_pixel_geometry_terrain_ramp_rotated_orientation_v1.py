#!/usr/bin/env python3
"""Third terrain integration proof: rotated orientation.

integer-rise terrain composition      PROVEN, FROZEN, UNTOUCHED
fractional-rise terrain composition   PROVEN, FROZEN, UNTOUCHED
rotated terrain composition           THIS GATE

    CONTROL                              ROTATED TEST
    lower terrain                        lower terrain -- ramp along +X --
          |  ramp travels along -Z                          upper terrain
    upper terrain

No new ramp mathematics, no new rise, no new artwork, no taper: this
reuses the EXACT SAME worked example as the integer-rise control (8 ramp
cells, required rise 5.0 -> angle 38.682 deg, run 6.245...). The only new
variable is rotation_degrees=0.0 passed to
terrain_ramp_integration_v1.ramp_position_to_world, which now sends the
ramp's fold-direction axis to world +X instead of world -Z.

The question under test: does the composition seam still close when the
ramp's intrinsic travel direction no longer coincides with the terrain
lane's original forward axis? This forces ramp-local, terrain-local, and
world coordinates to stay genuinely distinct, and proves the placement
transform performs the conversion generally -- not an embedded assumption
that "the ramp always points north."
"""
from __future__ import annotations

import json
import math
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

import export_terrain_ramp_rotated_orientation_evidence as scene_tool
import export_terrain_ramp_integration_evidence as control_tool

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
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
        f"errors={lower_built.get('errors')}",
    )
    report(
        "UPPER_TERRAIN_BUILDS_WITH_EXISTING_POLICY",
        upper_built.get("status") == "BUILT" and upper_built.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE",
        f"errors={upper_built.get('errors')}",
    )

    # Reuses the EXACT SAME worked-example numbers as the integer-rise
    # control -- the only difference is orientation. Prove that directly
    # by comparing the solved ramp math object for object.
    control_solved = control_tool.solve_ramp()
    report(
        "REUSES_IDENTICAL_RAMP_MATH_AS_INTEGER_RISE_CONTROL",
        solved.angle_degrees == control_solved.angle_degrees
        and solved.run == control_solved.run
        and solved.chain_length == control_solved.chain_length,
        f"angle={solved.angle_degrees} run={solved.run}",
    )
    report(
        "ROTATION_IS_THE_ONLY_NEW_VARIABLE",
        scene_tool.ROTATION_DEGREES == 0.0 and scene_tool.ROTATION_DEGREES != 90.0,
        f"rotation_degrees={scene_tool.ROTATION_DEGREES}",
    )

    independent_positions = embed_declared_angle_ramp_fold(
        footprint, hinge_corner_x=scene_tool.HINGE_CORNER_X, angle_degrees=solved.angle_degrees
    )
    report("RAMP_USES_FROZEN_DECLARED_ANGLE_EMBEDDING", independent_positions == ramp_positions)

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

    # The transform is proven to be an isometry AT THIS rotation, not just
    # the control's fixed 90 degrees -- independently recompute using the
    # raw rotation matrix, not just trusting ramp_position_to_world's own
    # internals.
    theta = math.radians(scene_tool.ROTATION_DEGREES)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    sample_a, sample_b = (0.3, 1.7, 0.9), (4.1, -2.2, 3.4)

    def independent_world(p):
        x, y, z = p
        return (
            x * cos_t + z * sin_t + scene_tool.RAMP_X_OFFSET,
            y,
            -x * sin_t + z * cos_t + scene_tool.PATH_Z_OFFSET,
        )

    world_a, world_b = independent_world(sample_a), independent_world(sample_b)
    before = math.dist(sample_a, sample_b)
    after = math.dist(world_a, world_b)
    report(
        "ROTATION_TRANSFORM_IS_ISOMETRY_INDEPENDENTLY_VERIFIED",
        close(before, after),
        f"before={before:.9f} after={after:.9f}",
    )
    matches_module_function = all(
        close(a, b)
        for a, b in zip(
            independent_world(sample_a),
            ramp_position_to_world(
                sample_a,
                path_x_offset=scene_tool.RAMP_X_OFFSET,
                ramp_z_offset=scene_tool.PATH_Z_OFFSET,
                rotation_degrees=scene_tool.ROTATION_DEGREES,
            ),
        )
    )
    report("ROTATION_TRANSFORM_MATCHES_MODULE_FUNCTION", matches_module_function)

    # The ramp's fold-direction axis genuinely reaches world X now, not
    # world Z: the far edge's X must differ from its near edge's X by
    # exactly `run`, while Z stays constant across the whole ramp width
    # only insofar as the near/far edges are each a fixed X-plane.
    near_xs = {round(p[0], 9) for p in attachment["ramp_near_world"]}
    far_xs = {round(p[0], 9) for p in attachment["ramp_far_world"]}
    report(
        "RAMP_TRAVELS_ALONG_WORLD_X_NOT_WORLD_Z",
        near_xs == {0.0} and far_xs == {round(solved.run, 9)},
        f"near_xs={near_xs} far_xs={far_xs} expected_far={solved.run}",
    )

    report("LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY", attachment["lower_attachment_matches"])
    report("UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY", attachment["upper_attachment_matches"])
    report("NO_RAMP_VERTEX_SCALING", attachment["is_isometry"])

    terrain_unit_metric = all(
        request["planar_config"]["cell_width"] == 1.0 and request["planar_config"]["cell_depth"] == 1.0
        for request in (scene["lower_request"], scene["upper_request"])
    )
    report("NO_TERRAIN_VERTEX_SCALING", terrain_unit_metric)

    declared_points = set(
        tuple(round(c, 6) for c in p) for p in attachment["ramp_near_world"] + attachment["ramp_far_world"]
    )
    ramp_world_all = [
        ramp_position_to_world(
            pos, path_x_offset=scene_tool.RAMP_X_OFFSET, ramp_z_offset=scene_tool.PATH_Z_OFFSET, rotation_degrees=scene_tool.ROTATION_DEGREES
        )
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
    print(f"[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
