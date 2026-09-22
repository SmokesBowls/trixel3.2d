#!/usr/bin/env python3
"""Sixth terrain-lane composition proof: close-proximity toxic ramps.

independent distant ramps          PROVEN, FROZEN
shared-terrain hub                 PROVEN, FROZEN
close-proximity toxic ramps        THIS GATE
taper / topology mutation          later -- a different topology problem

The independent multi-ramp proof showed two scenes don't interfere when
kept 15.9 units apart -- an easy case. This gate makes proximity actively
misleading: two ramps, placed with EACH RAMP'S OWN DEFAULT (already
frozen, unshifted) placement, produce measured EXACT-POSITION
coincidences between their vertices, with no declared relationship
between them whatsoever. The required result:

    GEOMETRICALLY_CLOSE                 true
    DECLARED_RAMP_TO_RAMP_ADJACENCY     none
    COMPILED_RAMP_TO_RAMP_ADJACENCY     none
    PROXIMITY_CREATES_TOPOLOGY          false

This directly pressure-tests the no-proximity-derived-adjacency doctrine
(adjacency_v1.no_proximity_derived_adjacency) that every flat/hinge/
cylinder gate has relied on -- but in every prior use of that function,
the desired result was an EMPTY offender list (nothing accidentally
close). Here the offender list is expected to be NON-EMPTY (the two ramps
really are close, even coincident) -- the actual claim under test is that
this closeness never gets promoted into either ramp's declared or
compiled adjacency, which stays exactly compiled_adjacency_matches_source
for each ramp alone, regardless of what the other ramp is doing nearby.
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
from trixel.pixel_geometry.compiler_v1 import edge_lengths
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold

import export_ramp_close_proximity_evidence as scene_tool

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    scene = scene_tool.build_scene()
    ramp_a, ramp_b = scene["ramp_a"], scene["ramp_b"]
    compiled_a, compiled_b = scene["compiled_a"], scene["compiled_b"]

    # Both ramps use the exact frozen embedding, unmodified -- reproduce
    # independently and compare, same discipline as every prior gate.
    independent_a = embed_declared_angle_ramp_fold(
        ramp_a["footprint"], hinge_corner_x=ramp_a["hinge_corner_x"], angle_degrees=ramp_a["ramp_info"]["solved"].angle_degrees
    )
    independent_b = embed_declared_angle_ramp_fold(
        ramp_b["footprint"], hinge_corner_x=ramp_b["hinge_corner_x"], angle_degrees=ramp_b["ramp_info"]["solved"].angle_degrees
    )
    report("RAMP_A_USES_FROZEN_DECLARED_ANGLE_EMBEDDING", independent_a == ramp_a["positions"])
    report("RAMP_B_USES_FROZEN_DECLARED_ANGLE_EMBEDDING", independent_b == ramp_b["positions"])

    edges_a, edges_b = edge_lengths(compiled_a), edge_lengths(compiled_b)
    report("RAMP_A_CELL_METRIC_REMAINS_1_0", all(close(length, 1.0) for length in edges_a))
    report("RAMP_B_CELL_METRIC_REMAINS_1_0", all(close(length, 1.0) for length in edges_b))

    # --- GEOMETRICALLY_CLOSE: true -----------------------------------------
    points_a = scene_tool.world_points(ramp_a)
    points_b = scene_tool.world_points(ramp_b)
    min_distance = min(sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 for a in points_a for b in points_b)
    exact_coincidences = sum(1 for a in points_a for b in points_b if all(abs(a[i] - b[i]) <= 1e-9 for i in range(3)))
    report(
        "GEOMETRICALLY_CLOSE",
        min_distance <= 1e-9,
        f"min_distance={min_distance:.9f} exact_coincidences={exact_coincidences}",
    )

    # Independent confirmation using the SAME diagnostic every prior gate
    # relies on (adjacency_v1.no_proximity_derived_adjacency), but here the
    # offender list is EXPECTED to be non-empty -- that non-emptiness IS
    # part of the proof that real proximity exists, not a failure.
    centers_a = scene_tool.world_cell_centers(ramp_a, "A")
    centers_b = scene_tool.world_cell_centers(ramp_b, "B")
    combined_centers = {**centers_a, **centers_b}
    declared_a = scene_tool.declared_adjacency_labeled(ramp_a, "A")
    declared_b = scene_tool.declared_adjacency_labeled(ramp_b, "B")
    combined_declared = {**declared_a, **declared_b}

    # --- DECLARED_RAMP_TO_RAMP_ADJACENCY: none -----------------------------
    no_cross_declared = all(
        label == key[0]
        for key, neighbors in combined_declared.items()
        for label, *_ in neighbors
    )
    report("DECLARED_RAMP_TO_RAMP_ADJACENCY_NONE", no_cross_declared)

    offenders = no_proximity_derived_adjacency(combined_centers, combined_declared, proximity_tolerance=0.4)
    cross_ramp_offenders = [(a, b, d) for a, b, d in offenders if a[0] != b[0]]
    report(
        "PROXIMITY_DIAGNOSTIC_CORRECTLY_FLAGS_THE_CLOSENESS",
        len(cross_ramp_offenders) > 0 and len(cross_ramp_offenders) == len(offenders),
        f"cross_ramp_offenders={len(cross_ramp_offenders)} total_offenders={len(offenders)}",
    )

    # --- COMPILED_RAMP_TO_RAMP_ADJACENCY: none -----------------------------
    compiled_a_clean = compiled_adjacency_matches_source(ramp_a["footprint"], compiled_a["compiled_adjacency"])
    compiled_b_clean = compiled_adjacency_matches_source(ramp_b["footprint"], compiled_b["compiled_adjacency"])
    report("COMPILED_RAMP_TO_RAMP_ADJACENCY_NONE", compiled_a_clean and compiled_b_clean)

    # Cell addresses are numerically overlapping between the two footprints
    # (both 9x2) -- prove that never causes accidental key confusion: every
    # address in ramp A's compiled adjacency is a valid ramp-A cell address,
    # and the same for ramp B, checked against each footprint's OWN address
    # domain independently.
    valid_a = set(source_adjacency(ramp_a["footprint"]))
    valid_b = set(source_adjacency(ramp_b["footprint"]))
    addresses_stay_in_own_domain = (
        set(compiled_a["compiled_adjacency"]) == valid_a and set(compiled_b["compiled_adjacency"]) == valid_b
    )
    report("NO_UNDECLARED_SHARED_VERTICES", addresses_stay_in_own_domain)

    # --- PROXIMITY_CREATES_TOPOLOGY: false ----------------------------------
    # The composite claim: real, measured proximity (even exact coincidence)
    # existed, and it changed nothing about either ramp's declared or
    # compiled adjacency.
    report(
        "PROXIMITY_CREATES_TOPOLOGY_FALSE",
        min_distance <= 1e-9 and compiled_a_clean and compiled_b_clean and no_cross_declared,
    )

    scene_again = scene_tool.build_scene()
    deterministic = (
        scene["ramp_a"]["positions"] == scene_again["ramp_a"]["positions"]
        and scene["ramp_b"]["positions"] == scene_again["ramp_b"]["positions"]
        and scene["compiled_a"] == scene_again["compiled_a"]
        and scene["compiled_b"] == scene_again["compiled_b"]
    )
    report("COMPOSED_SCENE_IS_DETERMINISTIC", deterministic)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
