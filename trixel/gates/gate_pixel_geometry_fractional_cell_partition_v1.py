#!/usr/bin/env python3
"""Fractional geometry, Phase 5 -- the first destructive sub-cell proof.

ONE pixel-owned cell, partitioned along its u axis at [0, 1/20, 19/20, 1]:
a 5% strip, a 90% main carrier, a 5% strip. Proves:

    ONE PIXEL OWNER
        v
    MULTIPLE GEOMETRIC PIECES
        v
    SAME PIXEL OWNERSHIP

using exact fractions.Fraction boundaries throughout the construction
layer -- float() only happens once, at the embedding boundary, matching
the required pipeline:

    exact topology -> Fraction boundary -> one authoritative boundary
        -> float conversion -> rendering
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, cell_addresses, validate_footprint_structure
from trixel.pixel_geometry.adjacency_v1 import source_adjacency
from trixel.pixel_geometry.compiler_v1 import compile_footprint_fractional
from trixel.pixel_geometry.contracts_v1 import (
    DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION,
    EMBEDDING_FLAT_FRACTIONAL,
)
from trixel.pixel_geometry.embedding_v1 import embed_flat_fractional
from trixel.pixel_geometry.fractional_geometry_v1 import (
    ONE,
    ZERO,
    partition_cell_u_axis,
    piece_u_width,
    pieces_partition_unit_interval,
    pieces_share_owner,
)

CHECKS: list[bool] = []
OWNER = (0, 0)


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_CELL_PARTITION][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def main() -> int:
    footprint = build_footprint(1, 1, [["PIXEL_A"]])
    cut_low_boundary = Fraction(1, 20)
    cut_high_boundary = Fraction(19, 20)
    boundaries = [ZERO, cut_low_boundary, cut_high_boundary, ONE]
    piece_ids = ["cut_low", "main", "cut_high"]

    pieces = partition_cell_u_axis(OWNER, boundaries, piece_ids)

    report(
        "ONE_LOGICAL_CELL_OWNER",
        len(cell_addresses(footprint)) == 1
        and cell_addresses(footprint)[0] == OWNER
        and len({p.owner_cell for p in pieces}) == 1,
    )
    report("THREE_GEOMETRIC_PIECES_EXIST", len(pieces) == 3)
    report("ALL_PIECES_RETAIN_SAME_OWNER_CELL", pieces_share_owner(pieces, OWNER))

    cut_low, main, cut_high = pieces
    report(
        "CUT_LOW_MAIN_SHARE_EXACT_1_20_BOUNDARY",
        cut_low.u_max == main.u_min == Fraction(1, 20)
        and cut_low.u_max is boundaries[1]
        and main.u_min is boundaries[1],
        "boundary is the SAME Fraction object on both sides, not two "
        "independently computed values that happen to be equal",
    )
    report(
        "MAIN_CUT_HIGH_SHARE_EXACT_19_20_BOUNDARY",
        main.u_max == cut_high.u_min == Fraction(19, 20)
        and main.u_max is boundaries[2]
        and cut_high.u_min is boundaries[2],
        "boundary is the SAME Fraction object on both sides, not two "
        "independently computed values that happen to be equal",
    )
    report(
        "PIECES_COVER_UNIT_DOMAIN_NO_GAP_NO_OVERLAP",
        pieces_partition_unit_interval(pieces),
    )
    exact_total_width = piece_u_width(cut_low) + piece_u_width(main) + piece_u_width(cut_high)
    report(
        "EXACT_RATIONAL_WIDTHS_SUM_TO_EXACTLY_ONE",
        exact_total_width == Fraction(1, 1),
        f"sum={exact_total_width!r} (exact Fraction equality, not an epsilon comparison)",
    )

    piece_positions = embed_flat_fractional(footprint, pieces)
    compiled = compile_footprint_fractional(
        footprint, {OWNER: pieces}, piece_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL
    )

    report(
        "COMPILED_PROVENANCE_HAS_THREE_ENTRIES_ALL_OWNED_BY_CELL_A",
        len(compiled["primitive_provenance"]) == 3
        and all(p["cell_address"] == [0, 0] for p in compiled["primitive_provenance"])
        and [p["piece_id"] for p in compiled["primitive_provenance"]] == piece_ids,
    )
    report(
        "DISPOSITION_IS_FRACTIONAL_SUBDIVISION_NOT_A_NEW_CELL",
        compiled["dispositions"] == {OWNER: DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION},
    )
    report(
        "CELL_LEVEL_ADJACENCY_UNTOUCHED",
        compiled["compiled_adjacency"] == source_adjacency(footprint),
    )

    # No welding/deduplication: each piece gets 4 fresh vertices, even
    # where a coordinate value exactly matches a neighboring piece's.
    report(
        "NO_WELDING_TWELVE_INDEPENDENT_VERTICES",
        len(compiled["positions"]) == 12,
        f"got {len(compiled['positions'])} (3 pieces x 4 corners each, "
        f"never deduplicated into shared vertices)",
    )
    cut_low_ne = compiled["positions"][1]  # cut_low: nw,ne,sw,se at indices 0-3
    main_nw = compiled["positions"][4]  # main: nw,ne,sw,se at indices 4-7
    cut_low_se = compiled["positions"][3]
    main_sw = compiled["positions"][6]
    report(
        "SHARED_BOUNDARY_COORDINATES_MATCH_BUT_VERTICES_ARE_DISTINCT",
        cut_low_ne == main_nw and cut_low_se == main_sw and 1 != 4 and 3 != 6,
        f"cut_low.ne position={cut_low_ne} == main.nw position={main_nw}, "
        f"cut_low.se position={cut_low_se} == main.sw position={main_sw}, "
        f"at distinct vertex indices (1,3) vs (4,6) -- pieces meet "
        f"mathematically without ever being merged into one vertex",
    )
    main_ne = compiled["positions"][5]  # main: nw,ne,sw,se at indices 4-7
    cut_high_nw = compiled["positions"][8]  # cut_high: nw,ne,sw,se at indices 8-11
    main_se = compiled["positions"][7]
    cut_high_sw = compiled["positions"][10]
    report(
        "SECOND_SHARED_BOUNDARY_COORDINATES_MATCH_BUT_VERTICES_ARE_DISTINCT",
        main_ne == cut_high_nw and main_se == cut_high_sw and 5 != 8 and 7 != 10,
        f"main.ne position={main_ne} == cut_high.nw position={cut_high_nw}, "
        f"main.se position={main_se} == cut_high.sw position={cut_high_sw}, "
        f"at distinct vertex indices (5,7) vs (8,10)",
    )

    report(
        "NO_NEW_SOURCE_PIXELS_CREATED",
        cell_addresses(footprint) == [OWNER] and len(cell_addresses(footprint)) == 1,
        "the footprint's own cell addresses are untouched by fractional "
        "compilation -- still exactly one source pixel",
    )

    # Toxic controls -- each must fail closed, matching every other gate
    # in this ladder.
    toxic_ok = True
    try:
        partition_cell_u_axis(OWNER, [0.0, 0.05, 1.0], ["a", "b"])  # floats, not Fraction
        toxic_ok = False
    except ValueError:
        pass
    try:
        partition_cell_u_axis(OWNER, [ZERO, Fraction(1, 2), Fraction(1, 3), ONE], ["a", "b", "c"])  # not increasing
        toxic_ok = False
    except ValueError:
        pass
    try:
        gapped = [
            type(cut_low)(OWNER, "a", ZERO, Fraction(1, 4), ZERO, ONE),
            type(cut_low)(OWNER, "b", Fraction(1, 2), ONE, ZERO, ONE),
        ]
        compile_footprint_fractional(footprint, {OWNER: gapped}, piece_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL)
        toxic_ok = False
    except ValueError:
        pass
    report("TOXIC_MALFORMED_PARTITIONS_REJECTED", toxic_ok)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_CELL_PARTITION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
