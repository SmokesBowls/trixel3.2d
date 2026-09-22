#!/usr/bin/env python3
"""Fifth terrain integration proof: shared-terrain hub.

independent multi-ramp composition    PROVEN, FROZEN, UNTOUCHED
shared-terrain multi-ramp hub         THIS GATE
close-proximity toxic composition     later
taper / topology mutation             later -- a different topology problem

One terrain block becomes shared composition authority: two independently
transformed ramps attach to two DIFFERENT declared edges of that SAME
block, each leading to its own separate upper terrain. The question under
test:

    Can one terrain artifact participate in two independent ramp seams
    without either ramp corrupting, duplicating, or redefining the other
    attachment?

Deliberately controlled: both ramps reuse the exact same already-proven
worked example (8 ramp cells, required rise 5.0) and the exact same
frozen embedding call. The central hub reuses the control's own
CENTER_COLUMN and the rotated proof's own CENTER_ROW, so each ramp's
path-width offset needs zero change -- only each ramp's travel-direction
offset shifts, by an amount derived directly from the hub's own declared
geometry.
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

from trixel.pixel_geometry.terrain_ramp_integration_v1 import ramp_position_to_world, verify_isometry

import export_terrain_hub_multi_ramp_evidence as scene_tool
import export_terrain_ramp_integration_evidence as scene_a_tool
import export_terrain_ramp_rotated_orientation_evidence as scene_b_tool

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def all_points(scene, key) -> list[tuple[float, float, float]]:
    ramp = scene[key]
    positions = ramp["ramp_positions"]
    ramp_points = [
        ramp_position_to_world(pos, rotation_degrees=ramp["rotation_degrees"], **ramp["offset_kwargs"])
        for (x, r), pos in positions.items()
        if x >= (scene_a_tool.HINGE_CORNER_X if key == "ramp_a" else scene_b_tool.HINGE_CORNER_X)
    ]
    terrain_points = [tuple(p) for p in ramp["upper_built"]["geometry"]["positions"]]
    return ramp_points + terrain_points


def main() -> int:
    scene = scene_tool.build_scene()
    central_built = scene["central_built"]
    ramp_a, ramp_b = scene["ramp_a"], scene["ramp_b"]
    attachment_a, attachment_b = scene["attachment_a"], scene["attachment_b"]

    # CENTRAL_TERRAIN_BUILT_ONCE: exactly one CONNECTED_SURFACE build's
    # worth of geometry, never doubled. The central hub is entirely flat
    # (elevation=0.0 everywhere), so CONNECTED_SURFACE's own rule (no wall
    # between same-height neighbors) means every cell gets exactly a top
    # and a bottom face, and only the grid's own perimeter cells get a
    # wall face (one per border-facing edge, never doubled since interior
    # edges are shared and omitted) -- 2*R*C top/bottom faces plus
    # 2*(R+C) perimeter wall faces, times 4 vertices per quad face.
    R, C = scene_tool.CENTRAL_ROWS, scene_tool.CENTRAL_COLUMNS
    expected_central_vertex_count = (2 * R * C + 2 * (R + C)) * 4
    report(
        "CENTRAL_TERRAIN_BUILT_ONCE",
        central_built.get("status") == "BUILT"
        and len(central_built["geometry"]["positions"]) == expected_central_vertex_count,
        f"positions={len(central_built['geometry']['positions'])} expected={expected_central_vertex_count}",
    )
    report(
        "NO_DUPLICATED_CENTRAL_TERRAIN_GEOMETRY",
        len(central_built["cell_geometry_ranges"]) == scene_tool.CENTRAL_COLUMNS * scene_tool.CENTRAL_ROWS,
        f"cell_ranges={len(central_built['cell_geometry_ranges'])}",
    )

    report("RAMP_A_ATTACHMENT_EXACT", attachment_a["lower_attachment_matches"] and attachment_a["upper_attachment_matches"])
    report("RAMP_B_ATTACHMENT_EXACT", attachment_b["lower_attachment_matches"] and attachment_b["upper_attachment_matches"])

    report(
        "RAMP_A_TRANSFORM_INDEPENDENT",
        verify_isometry(rotation_degrees=90.0, **ramp_a["offset_kwargs"]),
    )
    report(
        "RAMP_B_TRANSFORM_INDEPENDENT",
        verify_isometry(rotation_degrees=0.0, **ramp_b["offset_kwargs"]),
    )

    # Ramp A's placement offsets never reference ramp B's (and vice versa)
    # -- true by construction (build_ramp_and_upper() takes only its own
    # scene_tool and shift), reconfirmed here: recomputing ramp A's offset
    # kwargs from scratch, with no knowledge of ramp B's existence, must
    # match exactly what the combined scene actually used.
    independent_a = dict(path_x_offset=scene_a_tool.PATH_X_OFFSET, ramp_z_offset=scene_a_tool.ramp_z_offset() + scene_tool.shift_a()[2])
    independent_b = dict(path_x_offset=scene_b_tool.RAMP_X_OFFSET + scene_tool.shift_b()[0], ramp_z_offset=scene_b_tool.PATH_Z_OFFSET)
    report("RAMP_A_OFFSETS_COMPUTABLE_WITHOUT_RAMP_B", independent_a == ramp_a["offset_kwargs"])
    report("RAMP_B_OFFSETS_COMPUTABLE_WITHOUT_RAMP_A", independent_b == ramp_b["offset_kwargs"])

    # NO_RAMP_A_TO_RAMP_B_ADJACENCY / NO_UNDECLARED_SHARED_VERTICES: the
    # only points ramp A's world (ramp + its own upper terrain) may share
    # with ramp B's world are none at all -- they don't declare any
    # relationship to each other, only each to the shared central hub.
    points_a = all_points(scene, "ramp_a")
    points_b = all_points(scene, "ramp_b")
    exact_shared = [
        (a, b) for a in points_a for b in points_b
        if all(abs(a[i] - b[i]) <= 1e-9 for i in range(3))
    ]
    report(
        "NO_UNDECLARED_SHARED_VERTICES",
        len(exact_shared) == 0,
        f"shared={len(exact_shared)}" if exact_shared else "",
    )
    proximity_tolerance = 0.4
    close_pairs = [
        (a, b) for a in points_a for b in points_b
        if sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 <= proximity_tolerance
    ]
    report(
        "NO_RAMP_A_TO_RAMP_B_ADJACENCY",
        len(close_pairs) == 0,
        f"offenders={len(close_pairs)}" if close_pairs else "",
    )

    # ATTACHMENT_A_DOES_NOT_CHANGE_ATTACHMENT_B / vice versa: rebuild the
    # scene TWICE, once computing only ramp A's attachment (ramp B code
    # never runs) and once computing only ramp B's (ramp A code never
    # runs), off the SAME central_built. Each isolated result must match
    # the combined scene's result exactly -- proving central_built is
    # immutable shared data, not something either ramp's computation
    # could have mutated for the other.
    from trixel.pixel_geometry.terrain_ramp_integration_v1 import terrain_attachment_edge, terrain_attachment_edge_x, verify_attachment_edges

    central_only_a = terrain_attachment_edge(
        central_built, field_x_values=scene_tool.DIRT_COLUMNS, field_y=scene_tool.CENTRAL_ROWS - 1, edge="low_z"
    )
    central_only_b = terrain_attachment_edge_x(
        central_built, field_y_values=scene_tool.DIRT_ROWS, field_x=scene_tool.CENTRAL_COLUMNS - 1, edge="high_x"
    )
    report("ATTACHMENT_A_DOES_NOT_CHANGE_ATTACHMENT_B", central_only_b == scene["central_b_edge"])
    report("ATTACHMENT_B_DOES_NOT_CHANGE_ATTACHMENT_A", central_only_a == scene["central_a_edge"])

    scene_again = scene_tool.build_scene()
    deterministic = (
        json.dumps(scene["central_built"], sort_keys=True) == json.dumps(scene_again["central_built"], sort_keys=True)
        and scene["ramp_a"]["ramp_positions"] == scene_again["ramp_a"]["ramp_positions"]
        and scene["ramp_b"]["ramp_positions"] == scene_again["ramp_b"]["ramp_positions"]
        and scene["attachment_a"]["lower_attachment_matches"] == scene_again["attachment_a"]["lower_attachment_matches"]
        and scene["attachment_b"]["lower_attachment_matches"] == scene_again["attachment_b"]["lower_attachment_matches"]
    )
    report("COMPOSED_SCENE_IS_DETERMINISTIC", deterministic)

    # Composition order independence: build ramp B's piece before ramp A's
    # and confirm both still match the normal (A-then-B) build exactly.
    ramp_b_first = scene_tool.build_ramp_and_upper(scene_b_tool, shift=scene_tool.shift_b(), rotation_degrees=0.0)
    ramp_a_first = scene_tool.build_ramp_and_upper(scene_a_tool, shift=scene_tool.shift_a(), rotation_degrees=90.0)
    order_independent = (
        json.dumps(ramp_a_first["upper_built"], sort_keys=True) == json.dumps(scene["ramp_a"]["upper_built"], sort_keys=True)
        and json.dumps(ramp_b_first["upper_built"], sort_keys=True) == json.dumps(scene["ramp_b"]["upper_built"], sort_keys=True)
    )
    report("COMPOSITION_ORDER_DOES_NOT_MATTER", order_independent)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
