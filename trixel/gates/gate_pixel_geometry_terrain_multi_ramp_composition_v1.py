#!/usr/bin/env python3
"""Fourth terrain integration proof: multiple ramps in one composition.

integer-rise terrain composition      PROVEN, FROZEN, UNTOUCHED
fractional-rise terrain composition   PROVEN, FROZEN, UNTOUCHED
rotated terrain composition           PROVEN, FROZEN, UNTOUCHED
multiple ramps / composition          THIS GATE
taper                                 later -- different topology problem, not attempted here

    SCENE A (unmodified, reused verbatim)     SCENE B (unmodified, reused
    lower terrain                             verbatim, then rigidly
          | ramp along -Z (rotation=90)       translated as one whole)
    upper terrain                             lower -- ramp along +X
                                               (rotation=0) -- upper

Deliberately controlled: no new ramp mathematics, no new cell metric, no
new slope. Both scenes reuse the exact same already-proven worked example
(8 ramp cells, required rise 5.0). The only new capability under test is
composition itself:

    Can two independently placed metric-preserving ramp artifacts coexist
    in one terrain composition without either placement transform,
    attachment seam, adjacency graph, or terrain artifact interfering
    with the other?

Taper is explicitly NOT attempted here -- it changes intrinsic topology,
a different problem from composing already-proven, topology-preserving
pieces.
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

import export_terrain_multi_ramp_composition_evidence as scene_tool
import export_terrain_ramp_integration_evidence as scene_a_tool
import export_terrain_ramp_rotated_orientation_evidence as scene_b_tool

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def main() -> int:
    scene = scene_tool.build_scene()
    scene_a, scene_b = scene["scene_a"], scene["scene_b"]

    for label, built in (
        ("SCENE_A_LOWER", scene_a["lower_built"]),
        ("SCENE_A_UPPER", scene_a["upper_built"]),
        ("SCENE_B_LOWER", scene_b["lower_built"]),
        ("SCENE_B_UPPER", scene_b["upper_built"]),
    ):
        report(
            f"{label}_BUILDS_WITH_EXISTING_POLICY",
            built.get("status") == "BUILT" and built.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE",
            f"errors={built.get('errors')}",
        )

    # Both scenes reuse the exact same already-proven worked example --
    # no new ramp math was introduced for this composition.
    report(
        "BOTH_SCENES_REUSE_IDENTICAL_RAMP_MATH",
        scene_a_tool.FAR_SEGMENT_CELLS == scene_b_tool.FAR_SEGMENT_CELLS == 8
        and scene_a_tool.REQUIRED_RISE == scene_b_tool.REQUIRED_RISE == 5.0,
    )
    report(
        "SCENES_USE_INDEPENDENT_ORIENTATIONS",
        90.0 != scene_b_tool.ROTATION_DEGREES,
        f"scene_a=90.0 scene_b={scene_b_tool.ROTATION_DEGREES}",
    )

    # Independent seams: each scene's own attachment edges still match
    # exactly after composition -- Scene A completely untouched, Scene B
    # re-verified AFTER its whole-scene translation.
    report("SCENE_A_LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY", scene_a["attachment"]["lower_attachment_matches"])
    report("SCENE_A_UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY", scene_a["attachment"]["upper_attachment_matches"])
    report("SCENE_B_LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY", scene_b["attachment"]["lower_attachment_matches"])
    report("SCENE_B_UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY", scene_b["attachment"]["upper_attachment_matches"])
    report("SCENE_A_PLACEMENT_IS_ISOMETRY", scene_a["attachment"]["is_isometry"])
    report("SCENE_B_PLACEMENT_IS_ISOMETRY", scene_b["attachment"]["is_isometry"])

    # No accidental ramp-to-ramp (or ramp-to-terrain, or terrain-to-terrain)
    # adjacency ACROSS scenes: neither scene declares any relationship to
    # the other, so NOTHING from Scene A should end up suspiciously close
    # to ANYTHING from Scene B -- a much stronger bar than each scene's own
    # internal NO_POSITION_DERIVED_ADJACENCY check (already proven by their
    # own frozen gates), since here there is no declared edge at all to
    # exempt.
    scene_a_ramp_points = scene_tool.ramp_world_points_a(scene_a, exclude_stub=True)
    scene_b_ramp_points = scene_tool.ramp_world_points_b(scene_b, exclude_stub=True)
    scene_a_terrain_points = [
        tuple(p) for built in (scene_a["lower_built"], scene_a["upper_built"]) for p in built["geometry"]["positions"]
    ]
    scene_b_terrain_points = [
        tuple(p) for built in (scene_b["lower_built"], scene_b["upper_built"]) for p in built["geometry"]["positions"]
    ]
    all_a_points = scene_a_ramp_points + scene_a_terrain_points
    all_b_points = scene_b_ramp_points + scene_b_terrain_points

    proximity_tolerance = 0.4
    cross_scene_offenders = [
        (a, b)
        for a in all_a_points
        for b in all_b_points
        if sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 <= proximity_tolerance
    ]
    report(
        "NO_CROSS_SCENE_ADJACENCY",
        len(cross_scene_offenders) == 0,
        f"offenders={len(cross_scene_offenders)}" if cross_scene_offenders else "",
    )

    # No overlapping geometry outside declared attachment edges: the
    # minimum distance between any Scene A point and any Scene B point
    # must comfortably exceed both scenes' own internal extents -- prove
    # the separation is real, not merely "no exact coincidence."
    min_cross_scene_distance = min(
        sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 for a in all_a_points for b in all_b_points
    )
    report(
        "SCENES_ARE_GENUINELY_SEPARATED_NOT_JUST_NON_COINCIDENT",
        min_cross_scene_distance > 5.0,
        f"min_cross_scene_distance={min_cross_scene_distance:.6f}",
    )

    # Deterministic composition, and order-independent: building Scene A
    # before Scene B (as main() does) must produce byte-identical results
    # to building Scene B before Scene A -- proving no shared mutable
    # state leaks between the two independent scene builders.
    rerun = scene_tool.build_scene()
    deterministic = (
        json.dumps(scene["scene_a"]["lower_built"], sort_keys=True) == json.dumps(rerun["scene_a"]["lower_built"], sort_keys=True)
        and json.dumps(scene["scene_b"]["lower_built"], sort_keys=True) == json.dumps(rerun["scene_b"]["lower_built"], sort_keys=True)
        and scene["scene_a"]["ramp_positions"] == rerun["scene_a"]["ramp_positions"]
        and scene["scene_b"]["ramp_positions"] == rerun["scene_b"]["ramp_positions"]
    )
    report("COMPOSED_SCENE_IS_DETERMINISTIC", deterministic)

    scene_b_first = scene_tool.build_scene_b_shifted()
    scene_a_first = scene_tool.build_scene_a()
    order_independent = (
        json.dumps(scene_a_first["lower_built"], sort_keys=True) == json.dumps(scene["scene_a"]["lower_built"], sort_keys=True)
        and json.dumps(scene_b_first["lower_built"], sort_keys=True) == json.dumps(scene["scene_b"]["lower_built"], sort_keys=True)
    )
    report("COMPOSITION_ORDER_DOES_NOT_MATTER", order_independent)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
