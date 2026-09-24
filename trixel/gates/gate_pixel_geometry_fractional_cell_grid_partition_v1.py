#!/usr/bin/env python3
"""Fractional geometry, Phase B -- exact 2D sub-cell partition.

ONE pixel-owned cell, partitioned independently along BOTH u and v at
[0, 1/20, 19/20, 1]:

    +-----+------------------+-----+
    | 5%  |       90%        | 5%  |
    +-----+------------------+-----+
    |     |                  |     |
    | 5%  |   90% x 90%      | 5%  |
    |     |   main carrier   |     |
    +-----+------------------+-----+
    | 5%  |       90%        | 5%  |
    +-----+------------------+-----+

9 geometric pieces, ONE owner. Still purely sub-cell math + a flat
embedding -- no ramps, no cylinders, no artwork, no side geometry. Once
this is proven, applying already-proven fractional pieces to a ramp/fold
embedding (Phase C) or a cylindrical wrap (Phase D) is "embed
already-proven geometry," not a new topology question.
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
    EMBEDDING_FLAT_FRACTIONAL,
)
from trixel.pixel_geometry.embedding_v1 import embed_flat_fractional
from trixel.pixel_geometry.fractional_geometry_v1 import (
    FractionalPiece,
    ONE,
    ZERO,
    partition_cell_grid,
    piece_area,
    pieces_partition_unit_square,
    pieces_share_owner,
)

CHECKS: list[bool] = []
OWNER = (0, 0)


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_CELL_GRID_PARTITION][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def main() -> int:
    footprint = build_footprint(1, 1, [["PIXEL_A"]])
    low, high = Fraction(1, 20), Fraction(19, 20)
    u_boundaries = [ZERO, low, high, ONE]
    v_boundaries = [ZERO, low, high, ONE]
    # row-major: piece_ids[vi][ui]
    piece_ids = [
        ["nw_corner", "n_edge", "ne_corner"],
        ["w_edge", "main", "e_edge"],
        ["sw_corner", "s_edge", "se_corner"],
    ]

    pieces = partition_cell_grid(OWNER, u_boundaries, v_boundaries, piece_ids)
    by_id = {p.piece_id: p for p in pieces}

    report(
        "ONE_LOGICAL_CELL_OWNER",
        len(cell_addresses(footprint)) == 1
        and cell_addresses(footprint)[0] == OWNER
        and pieces_share_owner(pieces, OWNER),
    )
    report("NINE_GEOMETRIC_PIECES_EXIST", len(pieces) == 9)

    # Exact shared boundaries on both axes -- every piece in a column
    # reads the identical u_boundaries element; every piece in a row
    # reads the identical v_boundaries element.
    report(
        "COLUMN_PIECES_SHARE_EXACT_U_BOUNDARY_OBJECTS",
        by_id["nw_corner"].u_min is by_id["w_edge"].u_min is by_id["sw_corner"].u_min == ZERO
        and by_id["n_edge"].u_min is by_id["main"].u_min is by_id["s_edge"].u_min is low
        and by_id["ne_corner"].u_min is by_id["e_edge"].u_min is by_id["se_corner"].u_min is high,
    )
    report(
        "ROW_PIECES_SHARE_EXACT_V_BOUNDARY_OBJECTS",
        by_id["nw_corner"].v_min is by_id["n_edge"].v_min is by_id["ne_corner"].v_min == ZERO
        and by_id["w_edge"].v_min is by_id["main"].v_min is by_id["e_edge"].v_min is low
        and by_id["sw_corner"].v_min is by_id["s_edge"].v_min is by_id["se_corner"].v_min is high,
    )

    # The four interior intersection points, each reached by exactly the
    # same (u, v) Fraction pair from every piece that touches it.
    intersections_ok = True
    for (u_val, v_val), touching in {
        (low, low): [("nw_corner", "u_max", "v_max"), ("n_edge", "u_min", "v_max"), ("w_edge", "u_max", "v_min"), ("main", "u_min", "v_min")],
        (high, low): [("n_edge", "u_max", "v_max"), ("ne_corner", "u_min", "v_max"), ("main", "u_max", "v_min"), ("e_edge", "u_min", "v_min")],
        (low, high): [("w_edge", "u_max", "v_max"), ("main", "u_min", "v_max"), ("sw_corner", "u_max", "v_min"), ("s_edge", "u_min", "v_min")],
        (high, high): [("main", "u_max", "v_max"), ("e_edge", "u_min", "v_max"), ("s_edge", "u_max", "v_min"), ("se_corner", "u_min", "v_min")],
    }.items():
        for piece_id, u_attr, v_attr in touching:
            piece = by_id[piece_id]
            if getattr(piece, u_attr) != u_val or getattr(piece, v_attr) != v_val:
                intersections_ok = False
    report(
        "FOUR_INTERIOR_INTERSECTIONS_SHARED_EXACTLY_BY_ALL_TOUCHING_PIECES",
        intersections_ok,
    )

    report(
        "PIECES_TILE_UNIT_SQUARE_NO_GAP_NO_OVERLAP",
        pieces_partition_unit_square(pieces),
    )
    total_area = sum((piece_area(p) for p in pieces), ZERO)
    report(
        "EXACT_AREA_SUM_EQUALS_EXACTLY_ONE",
        total_area == Fraction(1, 1),
        f"sum={total_area!r} (exact Fraction equality, not an epsilon comparison)",
    )
    expected_areas = {
        "nw_corner": low * low, "n_edge": (high - low) * low, "ne_corner": (ONE - high) * low,
        "w_edge": low * (high - low), "main": (high - low) * (high - low), "e_edge": (ONE - high) * (high - low),
        "sw_corner": low * (ONE - high), "s_edge": (high - low) * (ONE - high), "se_corner": (ONE - high) * (ONE - high),
    }
    report(
        "PER_PIECE_AREAS_MATCH_EXACT_EXPECTED_FRACTIONS",
        all(piece_area(by_id[pid]) == area for pid, area in expected_areas.items()),
        f"main area={piece_area(by_id['main'])!r} (expected {expected_areas['main']!r})",
    )

    piece_positions = embed_flat_fractional(footprint, pieces)
    compiled = compile_footprint_fractional(
        footprint, {OWNER: pieces}, piece_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL
    )

    report(
        "COMPILED_PROVENANCE_HAS_NINE_ENTRIES_ALL_OWNED_BY_CELL_A",
        len(compiled["primitive_provenance"]) == 9
        and all(p["cell_address"] == [0, 0] for p in compiled["primitive_provenance"]),
    )
    report(
        "EVERY_PIECE_HAS_ITS_OWN_PROVENANCE_ENTRY",
        {p["piece_id"] for p in compiled["primitive_provenance"]} == set(by_id),
    )
    report(
        "DISPOSITION_IS_FRACTIONAL_SUBDIVISION_NOT_A_NEW_CELL",
        compiled["dispositions"] == {OWNER: DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION},
    )
    report(
        "CELL_LEVEL_ADJACENCY_UNTOUCHED",
        compiled["compiled_adjacency"] == source_adjacency(footprint),
    )
    report(
        "NO_WELDING_THIRTY_SIX_INDEPENDENT_VERTICES",
        len(compiled["positions"]) == 36,
        f"got {len(compiled['positions'])} (9 pieces x 4 corners each, never deduplicated)",
    )

    # Spot-check one interior intersection in world space: main.nw,
    # n_edge.sw, w_edge.ne, and nw_corner.se must all equal the same
    # world position (low, 0.0, low) despite being four distinct
    # vertices in four distinct pieces.
    def corners(piece_id: str) -> tuple:
        idx = list(by_id).index(piece_id) * 4
        return tuple(compiled["positions"][idx : idx + 4])

    main_nw = corners("main")[0]
    n_edge_sw = corners("n_edge")[2]
    w_edge_ne = corners("w_edge")[1]
    nw_corner_se = corners("nw_corner")[3]
    report(
        "INTERIOR_INTERSECTION_WORLD_COORDINATE_MATCHES_ACROSS_FOUR_DISTINCT_PIECES",
        main_nw == n_edge_sw == w_edge_ne == nw_corner_se,
        f"main.nw={main_nw} n_edge.sw={n_edge_sw} w_edge.ne={w_edge_ne} nw_corner.se={nw_corner_se}",
    )

    report(
        "NO_NEW_SOURCE_PIXELS_CREATED",
        cell_addresses(footprint) == [OWNER] and len(cell_addresses(footprint)) == 1,
    )

    # Trivial partition (single [0,1] x [0,1] piece) still collapses to
    # the existing baseline semantics -- re-proven here specifically
    # against the 2D-capable code path, not just Phase A's own gate.
    from trixel.pixel_geometry.compiler_v1 import compile_footprint
    from trixel.pixel_geometry.contracts_v1 import EMBEDDING_FLAT
    from trixel.pixel_geometry.embedding_v1 import embed_flat
    from trixel.pixel_geometry.fractional_geometry_v1 import trivial_partition

    trivial = trivial_partition(OWNER)
    trivial_positions = embed_flat_fractional(footprint, trivial)
    trivial_compiled = compile_footprint_fractional(
        footprint, {OWNER: trivial}, trivial_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL
    )
    baseline_positions = embed_flat(footprint)
    baseline_compiled = compile_footprint(footprint, baseline_positions, embedding_id=EMBEDDING_FLAT)
    report(
        "TRIVIAL_PARTITION_STILL_COLLAPSES_TO_BASELINE_SEMANTICS",
        trivial_compiled["positions"] == baseline_compiled["positions"]
        and trivial_compiled["indices"] == baseline_compiled["indices"]
        and trivial_compiled["dispositions"] == baseline_compiled["dispositions"]
        and trivial_compiled["compiled_adjacency"] == baseline_compiled["compiled_adjacency"],
    )

    # Toxic controls -- malformed 2D partitions must fail closed.
    toxic_ok = True
    try:
        partition_cell_grid(OWNER, [0.0, 1.0], [ZERO, ONE], [["a"]])  # float u-boundary
        toxic_ok = False
    except ValueError:
        pass
    try:
        partition_cell_grid(OWNER, [ZERO, ONE], [ZERO, ONE], [["a", "b"]])  # wrong grid shape
        toxic_ok = False
    except ValueError:
        pass
    try:
        # Duplicate piece_ids across the grid.
        partition_cell_grid(OWNER, [ZERO, low, ONE], [ZERO, low, ONE], [["x", "x"], ["y", "z"]])
        toxic_ok = False
    except ValueError:
        pass
    try:
        # Gapped 2D partition passed directly to the compiler (bypassing
        # the constructor's own validation).
        gapped = [
            FractionalPiece(OWNER, "a", ZERO, Fraction(1, 4), ZERO, ONE),
            FractionalPiece(OWNER, "b", Fraction(1, 2), ONE, ZERO, ONE),
        ]
        compile_footprint_fractional(
            footprint, {OWNER: gapped}, piece_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL
        )
        toxic_ok = False
    except ValueError:
        pass
    report("TOXIC_MALFORMED_2D_PARTITIONS_REJECTED", toxic_ok)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_CELL_GRID_PARTITION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
