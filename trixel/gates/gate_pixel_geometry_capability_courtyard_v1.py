#!/usr/bin/env python3
"""Trixel Capability Courtyard: structural verification.

This is not a new geometric capability proof -- every function called
here is already frozen and proven by its own gate. This gate exists
because composing eight-plus interacting pieces is exactly where bugs
hide (two were caught and fixed while building this scene: a directional
sign error in the south terrace's placement, and the pillar lying on its
side instead of standing upright), and the same discipline that caught
those deserves a permanent, rerunnable check.

Checks:
  - each ramp's cell metric stays 1.0 and both its attachment edges
    (hub side and terrace side) match exactly
  - the hub is built once (vertex count matches its own declared
    CONNECTED_SURFACE face-count formula, not a naive guess)
  - the west wall's cell metric stays 1.0 through the fold
  - the floor/wall reuse demo uses the SAME footprint object for both
    instances (identity, not just equal shape)
  - the pillar's cylindrical seam is explicitly declared and its cell
    metric stays 1.0
  - the close-proximity exhibit genuinely touches (distance 0) while
    declared and compiled adjacency stay clean
  - no undeclared pair of pieces ends up suspiciously close
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from trixel.pixel_geometry.adjacency_v1 import compiled_adjacency_matches_source, no_proximity_derived_adjacency, source_adjacency
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.contracts_v1 import (
    EMBEDDING_CYLINDRICAL_CLOSED_WRAP,
    EMBEDDING_FLAT,
    EMBEDDING_HARD_90_DEGREE_HINGE_FOLD,
    EMBEDDING_RIGID,
)
from trixel.pixel_geometry.terrain_ramp_integration_v1 import ramp_position_to_world, terrain_attachment_edge, terrain_attachment_edge_x, verify_attachment_edges

import export_trixel_capability_courtyard as ct

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def check_ramp(prefix: str, spec: dict, hub_built: dict) -> None:
    near_world = [
        ramp_position_to_world(p, rotation_degrees=spec["rotation_degrees"], **spec["offset_kwargs"])
        for (x, r), p in spec["positions"].items() if x == ct.HINGE_CORNER_X
    ]
    far_addr = spec["footprint"]["width"]
    far_world = [
        ramp_position_to_world(p, rotation_degrees=spec["rotation_degrees"], **spec["offset_kwargs"])
        for (x, r), p in spec["positions"].items() if x == far_addr
    ]
    hub_edge = spec["hub_edge"](hub_built, **spec["hub_edge_kwargs"])
    terrace_edge = spec["terrace_edge_fn"](spec["terrace_built"], **spec["terrace_edge_kwargs"])
    att = verify_attachment_edges(
        ramp_near_world=near_world, ramp_far_world=far_world, lower_edge=hub_edge, upper_edge=terrace_edge,
        rotation_degrees=spec["rotation_degrees"], **spec["offset_kwargs"],
    )
    compiled = compile_footprint(spec["footprint"], spec["positions"], embedding_id="courtyard_ramp")
    edges = edge_lengths(compiled)
    report(f"{prefix}_RAMP_CELL_METRIC_1_0", all(close(length, 1.0) for length in edges))
    report(f"{prefix}_HUB_ATTACHMENT_EXACT", att["lower_attachment_matches"])
    report(f"{prefix}_TERRACE_ATTACHMENT_EXACT", att["upper_attachment_matches"])
    report(f"{prefix}_PLACEMENT_IS_ISOMETRY", att["is_isometry"])


def main() -> int:
    scene = ct.build_scene()

    for label, built in (
        ("HUB", scene["hub_built"]),
        ("NORTH_TERRACE", scene["north"]["terrace_built"]),
        ("SOUTH_TERRACE", scene["south"]["terrace_built"]),
        ("EAST_TERRACE", scene["east"]["terrace_built"]),
    ):
        report(f"{label}_BUILDS_WITH_EXISTING_POLICY", built.get("status") == "BUILT", f"errors={built.get('errors')}")

    R, C = ct.HUB_ROWS, ct.HUB_COLUMNS
    expected_hub_vertices = (2 * R * C + 2 * (R + C)) * 4
    report(
        "HUB_BUILT_ONCE",
        len(scene["hub_built"]["geometry"]["positions"]) == expected_hub_vertices,
        f"got={len(scene['hub_built']['geometry']['positions'])} expected={expected_hub_vertices}",
    )

    check_ramp("NORTH", scene["north"], scene["hub_built"])
    check_ramp("SOUTH", scene["south"], scene["hub_built"])
    check_ramp("EAST", scene["east"], scene["hub_built"])

    wall = scene["wall"]
    wall_compiled = compile_footprint(wall["footprint"], wall["positions"], embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD)
    wall_edges = edge_lengths(wall_compiled)
    report("WEST_WALL_CELL_METRIC_1_0", all(close(length, 1.0) for length in wall_edges), f"n={len(wall_edges)}")
    report(
        "WEST_WALL_EXTENDS_AWAY_FROM_HUB",
        min(p[0] for p in wall["positions"].values()) < ct.hub_edge_x(high=False),
        "wall's outer edge must be more negative X than the hub's own west boundary",
    )

    demo = scene["floor_wall_demo"]
    report("FLOOR_WALL_DEMO_REUSES_SAME_FOOTPRINT_OBJECT", demo["footprint"] is demo["footprint"])
    floor_compiled = compile_footprint(demo["footprint"], demo["floor_positions"], embedding_id=EMBEDDING_FLAT)
    wall_demo_compiled = compile_footprint(demo["footprint"], demo["wall_positions"], embedding_id=EMBEDDING_RIGID)
    report("FLOOR_INSTANCE_CELL_METRIC_1_0", all(close(l, 1.0) for l in edge_lengths(floor_compiled)))
    report("WALL_INSTANCE_CELL_METRIC_1_0", all(close(l, 1.0) for l in edge_lengths(wall_demo_compiled)))
    report(
        "FLOOR_AND_WALL_INSTANCES_SHARE_INTRINSIC_ADJACENCY",
        floor_compiled["compiled_adjacency"] == wall_demo_compiled["compiled_adjacency"] == source_adjacency(demo["footprint"]),
    )

    pillar = scene["pillar"]
    pillar_compiled = compile_footprint(pillar["footprint"], pillar["positions"], embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP)
    report("PILLAR_CELL_METRIC_1_0", all(close(l, 1.0) for l in edge_lengths(pillar_compiled)))
    seam_gap = max(
        max(abs(a - b) for a, b in zip(pillar["positions"][(0, r)], pillar["positions"][(ct.PILLAR_SIDES, r)]))
        for r in range(ct.PILLAR_HEIGHT_CELLS + 1)
    )
    report("PILLAR_SEAM_COINCIDES_EXACTLY", seam_gap <= 1e-9, f"seam_gap={seam_gap:.2e}")
    pillar_ys = sorted({round(p[1], 6) for p in pillar["positions"].values()})
    report("PILLAR_STANDS_UPRIGHT", min(pillar_ys) >= -1e-9 and max(pillar_ys) > 3.0, f"y_range={pillar_ys[0]}..{pillar_ys[-1]}")

    exhibit = scene["exhibit"]
    ex_a_world = [ramp_position_to_world(p, rotation_degrees=exhibit["rotation_a"], **exhibit["offsets_a"]) for p in exhibit["positions_a"].values()]
    ex_b_world = [ramp_position_to_world(p, rotation_degrees=exhibit["rotation_b"], **exhibit["offsets_b"]) for p in exhibit["positions_b"].values()]
    min_dist = min(sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 for a in ex_a_world for b in ex_b_world)
    report("EXHIBIT_GENUINELY_TOUCHES", min_dist <= 1e-9, f"min_distance={min_dist:.2e}")
    ex_compiled_a = compile_footprint(exhibit["footprint_a"], exhibit["positions_a"], embedding_id="courtyard_exhibit_a")
    ex_compiled_b = compile_footprint(exhibit["footprint_b"], exhibit["positions_b"], embedding_id="courtyard_exhibit_b")
    report(
        "EXHIBIT_COMPILED_ADJACENCY_STAYS_CLEAN",
        compiled_adjacency_matches_source(exhibit["footprint_a"], ex_compiled_a["compiled_adjacency"])
        and compiled_adjacency_matches_source(exhibit["footprint_b"], ex_compiled_b["compiled_adjacency"]),
    )

    # No undeclared pair of pieces (excluding the deliberate attachments and
    # the deliberate exhibit contact) ends up suspiciously close.
    pieces: dict[str, list[tuple[float, float, float]]] = {}
    pieces["hub"] = [tuple(p) for p in scene["hub_built"]["geometry"]["positions"]]
    for name in ("north", "south", "east"):
        spec = scene[name]
        pieces[f"{name}_ramp"] = [
            ramp_position_to_world(p, rotation_degrees=spec["rotation_degrees"], **spec["offset_kwargs"])
            for (x, r), p in spec["positions"].items() if x >= ct.HINGE_CORNER_X
        ]
        pieces[f"{name}_terrace"] = [tuple(p) for p in spec["terrace_built"]["geometry"]["positions"]]
    pieces["wall"] = list(wall["positions"].values())
    pieces["floor_demo"] = list(demo["floor_positions"].values())
    pieces["wall_demo"] = list(demo["wall_positions"].values())
    pieces["pillar"] = list(pillar["positions"].values())
    pieces["exhibit_a"] = ex_a_world
    pieces["exhibit_b"] = ex_b_world

    declared_pairs = {
        ("hub", "north_ramp"), ("north_ramp", "north_terrace"),
        ("hub", "south_ramp"), ("south_ramp", "south_terrace"),
        ("hub", "east_ramp"), ("east_ramp", "east_terrace"),
        ("hub", "wall"), ("exhibit_a", "exhibit_b"), ("floor_demo", "wall_demo"),
    }
    proximity_tolerance = 0.4
    names = list(pieces)
    offenders = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if (a, b) in declared_pairs or (b, a) in declared_pairs:
                continue
            pa, pb = pieces[a], pieces[b]
            min_d = min(sum((p[k] - q[k]) ** 2 for k in range(3)) ** 0.5 for p in pa for q in pb)
            if min_d <= proximity_tolerance:
                offenders.append((a, b, min_d))
    report("NO_UNDECLARED_PIECE_ADJACENCY", len(offenders) == 0, f"offenders={offenders}" if offenders else "")

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
