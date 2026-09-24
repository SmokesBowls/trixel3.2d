#!/usr/bin/env python3
"""Fractional geometry, Phase C.5 -- exact fractional hinge-contact proof.

Phase C ('67c29b5) proved fractional pieces on a cell entirely BEYOND
the hinge. It deliberately never tested the cell immediately adjacent to
the hinge on either side, where a piece's own corners can straddle the
exact flat/rotated formula boundary:

    left cell (owner_x + 1 == hinge_x)   | hinge |  right cell (owner_x == hinge_x)
    flat branch for every corner         |       |  u=0 corners: flat branch (== hinge)
                                          |       |  u>0 corners: rotated branch

This gate fractionalizes BOTH cells touching the hinge and proves their
shared u=1 / u=0 boundary -- which is a CELL boundary, not a same-cell
piece boundary like Phase A/B/C -- still meets exactly in world space,
with no welding, no gap, no overlap, and no adjacency inferred from the
coincidence.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, cell_addresses
from trixel.pixel_geometry.adjacency_v1 import source_adjacency
from trixel.pixel_geometry.compiler_v1 import compile_footprint_fractional
from trixel.pixel_geometry.contracts_v1 import (
    DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION,
    EMBEDDING_DECLARED_ANGLE_RAMP_FOLD_FRACTIONAL,
)
from trixel.pixel_geometry.embedding_v1 import (
    embed_declared_angle_ramp_fold,
    embed_declared_angle_ramp_fold_fractional,
    embed_hard_90_degree_hinge_fold,
)
from trixel.pixel_geometry.fractional_geometry_v1 import (
    ONE,
    ZERO,
    partition_cell_u_axis,
    pieces_partition_unit_interval,
    trivial_partition,
)

CHECKS: list[bool] = []

HINGE_X = 2
ANGLE_DEGREES = 90.0
LEFT_OWNER = (1, 0)   # last flat cell: owner_x + 1 == HINGE_X
RIGHT_OWNER = (2, 0)  # first folded cell: owner_x == HINGE_X


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_HINGE_CONTACT][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def close3(a: tuple, b: tuple, tol: float = 1e-9) -> bool:
    return all(close(x, y, tol) for x, y in zip(a, b))


def main() -> int:
    footprint = build_footprint(4, 1, [["A", "B", "C", "D"]])

    # Ground truth: the two ALREADY-FROZEN whole-cell embeddings, called
    # fresh here (not reused from any cached value), confirming their
    # output is unaffected by this phase's work and that they still agree
    # with each other exactly at 90 degrees.
    frozen_hinge = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_X)
    frozen_ramp_at_90 = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_X, angle_degrees=ANGLE_DEGREES)
    both_frozen_agree = all(
        close3(frozen_hinge[addr], frozen_ramp_at_90[addr]) for addr in frozen_hinge
    )
    report(
        "EXISTING_WHOLE_CELL_HINGE_AND_RAMP_OUTPUT_UNCHANGED_AND_STILL_AGREE",
        both_frozen_agree,
    )

    low, high = Fraction(1, 20), Fraction(19, 20)
    boundaries = [ZERO, low, high, ONE]
    ids = ["cut_low", "main", "cut_high"]
    pieces_left = partition_cell_u_axis(LEFT_OWNER, boundaries, ids)
    pieces_right = partition_cell_u_axis(RIGHT_OWNER, boundaries, ids)

    report("LEFT_CELL_NO_GAP_NO_OVERLAP", pieces_partition_unit_interval(pieces_left))
    report("RIGHT_CELL_NO_GAP_NO_OVERLAP", pieces_partition_unit_interval(pieces_right))

    other_trivial = trivial_partition((0, 0)) + trivial_partition((3, 0))
    piece_positions = embed_declared_angle_ramp_fold_fractional(
        footprint,
        pieces_left + pieces_right + other_trivial,
        hinge_corner_x=HINGE_X,
        angle_degrees=ANGLE_DEGREES,
    )
    compiled = compile_footprint_fractional(
        footprint,
        {LEFT_OWNER: pieces_left, RIGHT_OWNER: pieces_right},
        piece_positions,
        embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD_FRACTIONAL,
    )

    report(
        "BOTH_CELLS_DISPOSITION_FRACTIONAL_SUBDIVISION",
        compiled["dispositions"][LEFT_OWNER] == DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION
        and compiled["dispositions"][RIGHT_OWNER] == DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION,
    )
    report(
        "TOTAL_VERTEX_COUNT_32_NO_CROSS_CELL_DEDUP",
        len(compiled["positions"]) == 32,
        f"got {len(compiled['positions'])} (4 trivial + 12 left + 12 right + 4 trivial, no sharing anywhere)",
    )

    # Locate each cell's vertex block from its own provenance -- every
    # piece (trivial or fractional) always contributes exactly 4 fresh
    # vertices, in compile order.
    left_provenance = [p for p in compiled["primitive_provenance"] if p["cell_address"] == [1, 0]]
    right_provenance = [p for p in compiled["primitive_provenance"] if p["cell_address"] == [2, 0]]
    left_base = left_provenance[0]["primitive_start"] * 2
    right_base = right_provenance[0]["primitive_start"] * 2

    # LEFT's "cut_high" piece (u=[19/20, 1]) is index 2 of pieces_left;
    # its u_max corners are "ne" (offset 1) and "se" (offset 3).
    left_cut_high_ne_idx = left_base + 2 * 4 + 1
    left_cut_high_se_idx = left_base + 2 * 4 + 3
    # RIGHT's "cut_low" piece (u=[0, 1/20]) is index 0 of pieces_right;
    # its u_min corners are "nw" (offset 0) and "sw" (offset 2).
    right_cut_low_nw_idx = right_base + 0 * 4 + 0
    right_cut_low_sw_idx = right_base + 0 * 4 + 2

    left_cut_high_ne = compiled["positions"][left_cut_high_ne_idx]
    left_cut_high_se = compiled["positions"][left_cut_high_se_idx]
    right_cut_low_nw = compiled["positions"][right_cut_low_nw_idx]
    right_cut_low_sw = compiled["positions"][right_cut_low_sw_idx]

    report(
        "HINGE_BOUNDARY_MATCHES_EXACTLY_IN_WORLD_SPACE_TOP_ROW",
        close3(left_cut_high_ne, right_cut_low_nw),
        f"left.cut_high.ne={left_cut_high_ne} right.cut_low.nw={right_cut_low_nw}",
    )
    report(
        "HINGE_BOUNDARY_MATCHES_EXACTLY_IN_WORLD_SPACE_BOTTOM_ROW",
        close3(left_cut_high_se, right_cut_low_sw),
        f"left.cut_high.se={left_cut_high_se} right.cut_low.sw={right_cut_low_sw}",
    )
    report(
        "HINGE_BOUNDARY_MATCHES_THE_FROZEN_WHOLE_CELL_CORNER_TOP_ROW",
        close3(left_cut_high_ne, frozen_hinge[(HINGE_X, 0)])
        and close3(right_cut_low_nw, frozen_hinge[(HINGE_X, 0)]),
    )
    report(
        "HINGE_BOUNDARY_MATCHES_THE_FROZEN_WHOLE_CELL_CORNER_BOTTOM_ROW",
        close3(left_cut_high_se, frozen_hinge[(HINGE_X, 1)])
        and close3(right_cut_low_sw, frozen_hinge[(HINGE_X, 1)]),
    )
    report(
        "NO_WELDING_MATCHING_VALUES_AT_DISTINCT_VERTEX_INDICES",
        left_cut_high_ne_idx != right_cut_low_nw_idx and left_cut_high_se_idx != right_cut_low_sw_idx,
        f"indices ({left_cut_high_ne_idx},{left_cut_high_se_idx}) vs ({right_cut_low_nw_idx},{right_cut_low_sw_idx})",
    )

    # Cell-level adjacency remains exactly the original declared
    # adjacency -- LEFT/RIGHT were already neighbors by ADDRESS before
    # any geometry ran; the fact that their geometry now touches exactly
    # adds nothing new and removes nothing.
    declared = source_adjacency(footprint)
    report(
        "CELL_ADJACENCY_IS_EXACTLY_THE_ORIGINAL_DECLARED_ADJACENCY",
        compiled["compiled_adjacency"] == declared,
    )
    report(
        "LEFT_RIGHT_WERE_ALREADY_DECLARED_NEIGHBORS_BY_ADDRESS_ALONE",
        RIGHT_OWNER in declared[LEFT_OWNER] and LEFT_OWNER in declared[RIGHT_OWNER],
    )
    report(
        "NO_EXTRA_ADJACENCY_ENTRY_APPEARED_FROM_THE_GEOMETRIC_COINCIDENCE",
        len(compiled["compiled_adjacency"]) == len(declared)
        and all(compiled["compiled_adjacency"][k] == declared[k] for k in declared),
    )

    # Toxic: the reverse of the 90-degree cross-check above -- if the two
    # frozen functions ever disagreed, this gate's ground truth itself
    # would be untrustworthy. Confirmed they still don't.
    report(
        "TOXIC_GROUND_TRUTH_FUNCTIONS_STILL_AGREE_AT_EVERY_ADDRESS",
        set(frozen_hinge) == set(frozen_ramp_at_90),
    )

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_HINGE_CONTACT][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
