#!/usr/bin/env python3
"""Trial 2.5 -- HARD 90 DEGREE HINGE FOLD.

Inserted 2026-09-20 before the cylinder trial, per instruction: a
whole-footprint rotation (Trial 2) is not the same claim as folding one
footprint over a straight edge. This is the decisive test of the
doctrine's actual proposition -- that a CellFootprint's intrinsic
structure survives being split across two non-coplanar faces, not merely
translated or rotated as one rigid body.

4x4 footprint, columns A B | C D (hinge between columns 1 and 2, exactly
on a cell boundary). C, D and every cell beneath them fold 90 degrees
around that shared boundary.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_addresses
from trixel.pixel_geometry.adjacency_v1 import (
    compiled_adjacency_matches_source,
    no_proximity_derived_adjacency,
    source_adjacency,
)
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths, positions_by_cell_center
from trixel.pixel_geometry.embedding_v1 import embed_hard_90_degree_hinge_fold
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_HARD_90_DEGREE_HINGE_FOLD

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_HINGE_FOLD][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    # A B C D / E F G H / I J K L / M N O P, row-major.
    labels = [["A", "B", "C", "D"], ["E", "F", "G", "H"], ["I", "J", "K", "L"], ["M", "N", "O", "P"]]
    footprint = build_footprint(4, 4, labels)
    HINGE_X = 2  # exactly between column 1 (B/F/J/N) and column 2 (C/G/K/O)

    positions = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_X)
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD)

    report("SIXTEEN_CELLS_NO_NEW_NO_LOST", len(compiled["dispositions"]) == 16)
    report(
        "ALL_DISPOSITIONS_STILL_PRESERVED_1_TO_1",
        all(v == "PRESERVED_1_TO_1" for v in compiled["dispositions"].values()),
    )

    # Unchanged source adjacency -- the compiled graph is compared to the
    # SAME source_adjacency() used before any embedding existed. If the
    # fold had silently performed a topology operation, this would be the
    # only place that could still be trusted to catch it.
    report(
        "COMPILED_ADJACENCY_UNCHANGED_BY_FOLD",
        compiled_adjacency_matches_source(footprint, compiled["compiled_adjacency"]),
    )
    adjacency = source_adjacency(footprint)
    named_pairs = [((1, 0), (2, 0), "B/C"), ((1, 1), (2, 1), "F/G"), ((1, 2), (2, 2), "J/K"), ((1, 3), (2, 3), "N/O")]
    for a, b, name in named_pairs:
        report(f"{name.replace('/', '_')}_REMAIN_NEIGHBORS", b in adjacency[a] and a in adjacency[b])

    # Hinge corner samples shared exactly: independently recompute BOTH
    # formulas at every hinge address and compare -- not just trusting the
    # embedding function's own internal branch.
    hinge_shared = True
    for r in range(footprint["height"] + 1):
        near_formula = (float(HINGE_X), 0.0, float(r))
        far_formula = (float(HINGE_X), float(HINGE_X - HINGE_X), float(r))  # offset=0 at the hinge itself
        actual = positions[(HINGE_X, r)]
        if not (all(close(a, b) for a, b in zip(near_formula, actual)) and near_formula == far_formula):
            hinge_shared = False
    report("HINGE_CORNER_SAMPLES_SHARED_EXACTLY", hinge_shared)

    # No scaling / no stretching: every cell edge in the compiled geometry,
    # including every edge that crosses the hinge, must equal the declared
    # cell_metric of 1.0 exactly.
    lengths = edge_lengths(compiled)
    report(
        "EVERY_CELL_EDGE_EQUALS_DECLARED_METRIC_1_0",
        all(close(length, 1.0) for length in lengths),
        f"min={min(lengths):.6f} max={max(lengths):.6f} n={len(lengths)}",
    )

    # Fixed side stays flat (Y=0); folded side actually left the plane.
    fixed_side_flat = all(
        close(positions[(x, r)][1], 0.0) for x, r in corner_addresses(footprint) if x <= HINGE_X
    )
    folded_side_left_plane = any(
        not close(positions[(x, r)][1], 0.0) for x, r in corner_addresses(footprint) if x > HINGE_X
    )
    report("FIXED_SIDE_STAYS_ON_ORIGINAL_PLANE", fixed_side_flat)
    report("FOLDED_SIDE_ACTUALLY_LEFT_THE_PLANE", folded_side_left_plane)

    # No proximity-derived adjacency: report any non-declared cell pair
    # that ended up spatially close after folding.
    centers = positions_by_cell_center(compiled)
    offenders = no_proximity_derived_adjacency(centers, adjacency, proximity_tolerance=0.5)
    report(
        "NO_UNDECLARED_CELLS_BECAME_SUSPICIOUSLY_CLOSE",
        len(offenders) == 0,
        f"offenders={offenders}" if offenders else "",
    )

    # Toxic cases: hinge NOT on an existing cell boundary must reject.
    toxic_ok = True
    for bad_hinge in (0, footprint["width"], -1, footprint["width"] + 3):
        try:
            embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=bad_hinge)
            toxic_ok = False
        except ValueError:
            pass
    try:
        embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=1.5)  # not even an int -- "through the middle of a cell"
        toxic_ok = False
    except ValueError:
        pass
    report("TOXIC_OFF_BOUNDARY_HINGE_REJECTED", toxic_ok)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_HINGE_FOLD][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
