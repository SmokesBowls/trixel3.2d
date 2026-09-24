#!/usr/bin/env python3
"""Fractional geometry, Phase C -- proven fractional pieces on an
EXISTING non-flat embedding.

acf321e  Phase A -- 1D fractional subdivision inside one cell (flat)
529ec78  Phase B -- 2D fractional subdivision inside one cell (flat)
THIS     Phase C -- the SAME 3x3 fractional partition, embedded on the
                    already-proven declared-angle ramp/fold

The question this gate answers, and only this question: can the exact
same 3x3 fractional partition survive embedding onto the existing
declared ramp/fold without changing ownership, adjacency, provenance, or
exact shared-boundary relationships? No new geometry system is invented
-- embed_declared_angle_ramp_fold_fractional() is a strict sibling of
the frozen embed_declared_angle_ramp_fold(), reproducing its exact
per-point formula at fractional x instead of inventing a new rule.
"""
from __future__ import annotations

import math
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
)
from trixel.pixel_geometry.fractional_geometry_v1 import (
    ONE,
    ZERO,
    partition_cell_grid,
    pieces_share_owner,
    trivial_partition,
)
from trixel.pixel_geometry.ramp_geometry_v1 import solve_ramp_run_and_angle

CHECKS: list[bool] = []

HINGE_X = 2
FAR_SEGMENT_CELLS = 2  # width (4) - HINGE_X (2)
REQUIRED_RISE = 1.0
OWNER = (3, 0)  # entirely beyond the hinge (owner_x=3 >= HINGE_X=2) -- genuinely non-flat


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_RAMP_FOLD_EMBEDDING][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def close3(a: tuple, b: tuple, tol: float = 1e-9) -> bool:
    return all(close(x, y, tol) for x, y in zip(a, b))


def main() -> int:
    footprint = build_footprint(4, 1, [["A", "B", "C", "D"]])
    solved = solve_ramp_run_and_angle(FAR_SEGMENT_CELLS, REQUIRED_RISE)
    theta = math.radians(solved.angle_degrees)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    # The frozen whole-cell embedding -- our control for extent/plane checks.
    frozen_positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_X, angle_degrees=solved.angle_degrees)

    low, high = Fraction(1, 20), Fraction(19, 20)
    boundaries = [ZERO, low, high, ONE]
    piece_ids = [
        ["nw_corner", "n_edge", "ne_corner"],
        ["w_edge", "main", "e_edge"],
        ["sw_corner", "s_edge", "se_corner"],
    ]
    pieces = partition_cell_grid(OWNER, boundaries, boundaries, piece_ids)
    by_id = {p.piece_id: p for p in pieces}

    report(
        "ONE_LOGICAL_CELL_OWNER_NINE_PIECES",
        OWNER in cell_addresses(footprint) and pieces_share_owner(pieces, OWNER) and len(pieces) == 9,
    )

    # compile_footprint_fractional compiles every cell in the footprint --
    # cells absent from cell_partitions default to the trivial partition,
    # so they need embedded positions too, not just OWNER's 9 pieces.
    other_cells_trivial = [
        piece for addr in cell_addresses(footprint) if addr != OWNER for piece in trivial_partition(addr)
    ]
    piece_positions = embed_declared_angle_ramp_fold_fractional(
        footprint, pieces + other_cells_trivial, hinge_corner_x=HINGE_X, angle_degrees=solved.angle_degrees
    )
    compiled = compile_footprint_fractional(
        footprint, {OWNER: pieces}, piece_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD_FRACTIONAL
    )

    # The footprint has 4 cells total; compile_footprint_fractional
    # compiles all of them (the other 3 default to their own trivial
    # partition), so every OWNER-specific check below is scoped to just
    # OWNER's slice of the compiled output, not the whole footprint.
    owner_provenance = [p for p in compiled["primitive_provenance"] if p["cell_address"] == [3, 0]]
    report(
        "PROVENANCE_NINE_ENTRIES_SAME_OWNER",
        len(owner_provenance) == 9 and {p["piece_id"] for p in owner_provenance} == set(by_id),
    )
    report(
        "DISPOSITION_IS_FRACTIONAL_SUBDIVISION_NOT_A_NEW_CELL",
        compiled["dispositions"][OWNER] == DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION,
    )
    report(
        "CELL_LEVEL_ADJACENCY_UNTOUCHED",
        compiled["compiled_adjacency"] == source_adjacency(footprint),
    )
    # Each piece (trivial or fractional) always contributes exactly 4
    # fresh vertices, in compile order -- so OWNER's vertex block starts
    # right where its first provenance entry's primitives do.
    owner_vertex_base = owner_provenance[0]["primitive_start"] * 2
    owner_positions = compiled["positions"][owner_vertex_base : owner_vertex_base + 36]
    report(
        "NO_WELDING_THIRTY_SIX_INDEPENDENT_VERTICES",
        len(owner_positions) == 36,
        f"got {len(owner_positions)} (9 pieces x 4 corners each, never deduplicated)",
    )

    # Total embedded extent matches the existing whole-cell ramp exactly:
    # the 3x3 grid's four outer corners must equal the frozen function's
    # own corners for this same cell.
    extent_ok = (
        close3(piece_positions[(OWNER, ZERO, ZERO)], frozen_positions[(3, 0)])
        and close3(piece_positions[(OWNER, ONE, ZERO)], frozen_positions[(4, 0)])
        and close3(piece_positions[(OWNER, ZERO, ONE)], frozen_positions[(3, 1)])
        and close3(piece_positions[(OWNER, ONE, ONE)], frozen_positions[(4, 1)])
    )
    report("TOTAL_EXTENT_MATCHES_FROZEN_WHOLE_CELL_RAMP_CORNERS", extent_ok)

    # The trivial ([0,1] x [0,1]) partition must collapse to the SAME
    # positions the frozen embed_declared_angle_ramp_fold already produces
    # for this cell -- the Phase-C analogue of Phase A's 1.0 baseline
    # regression, now against a non-flat control.
    trivial = trivial_partition(OWNER)
    trivial_positions = embed_declared_angle_ramp_fold_fractional(
        footprint, trivial, hinge_corner_x=HINGE_X, angle_degrees=solved.angle_degrees
    )
    trivial_ok = (
        close3(trivial_positions[(OWNER, ZERO, ZERO)], frozen_positions[(3, 0)])
        and close3(trivial_positions[(OWNER, ONE, ZERO)], frozen_positions[(4, 0)])
        and close3(trivial_positions[(OWNER, ZERO, ONE)], frozen_positions[(3, 1)])
        and close3(trivial_positions[(OWNER, ONE, ONE)], frozen_positions[(4, 1)])
    )
    report("TRIVIAL_PARTITION_COLLAPSES_TO_FROZEN_RAMP_EMBEDDING", trivial_ok)

    # Every fractional corner OF OWNER'S OWN PIECES independently
    # recomputed against the SAME rotated-plane formula the frozen
    # function uses -- not just trusted from the new function's own
    # internals. (OWNER is entirely beyond the hinge, so every one of its
    # corners uses the rotated branch; the other cells' trivial corners
    # are flat-side and are out of scope for this specific check.)
    plane_ok = True
    for piece in pieces:
        for u in (piece.u_min, piece.u_max):
            for v in (piece.v_min, piece.v_max):
                actual = piece_positions[(OWNER, u, v)]
                x_local = OWNER[0] + u
                offset = float(x_local - HINGE_X)
                predicted = (float(HINGE_X) + offset * cos_t, offset * sin_t, float(OWNER[1] + v))
                if not close3(predicted, actual):
                    plane_ok = False
    report("EVERY_FRACTIONAL_CORNER_LIES_ON_THE_SAME_ROTATED_PLANE_FORMULA", plane_ok)

    # Shared boundaries still map to identical WORLD-SPACE coordinates
    # after the fold (not just in local u/v space) -- the four interior
    # intersections, each reached by a distinct vertex in each of the
    # (up to) four touching pieces.
    def corners(piece_id: str) -> tuple:
        idx = owner_vertex_base + list(by_id).index(piece_id) * 4
        return tuple(compiled["positions"][idx : idx + 4])

    intersections_world_ok = (
        close3(corners("main")[0], corners("n_edge")[2])
        and close3(corners("main")[0], corners("w_edge")[1])
        and close3(corners("main")[0], corners("nw_corner")[3])
        and close3(corners("main")[1], corners("ne_corner")[2])
        and close3(corners("main")[1], corners("n_edge")[3])
        and close3(corners("main")[1], corners("e_edge")[0])
        and close3(corners("main")[2], corners("w_edge")[3])
        and close3(corners("main")[2], corners("sw_corner")[1])
        and close3(corners("main")[2], corners("s_edge")[0])
        and close3(corners("main")[3], corners("e_edge")[2])
        and close3(corners("main")[3], corners("s_edge")[1])
        and close3(corners("main")[3], corners("se_corner")[0])
    )
    report("SHARED_BOUNDARIES_MAP_TO_IDENTICAL_WORLD_COORDINATES_AFTER_FOLD", intersections_world_ok)

    # Orientation preserved: moving from u_min to u_max within ANY piece
    # moves along the exact same rotated unit direction (cos_t, sin_t, 0),
    # scaled by exactly that piece's own u-width -- never flipped, never
    # re-derived per piece.
    orientation_ok = True
    for piece in pieces:
        nw = piece_positions[(OWNER, piece.u_min, piece.v_min)]
        ne = piece_positions[(OWNER, piece.u_max, piece.v_min)]
        sw = piece_positions[(OWNER, piece.u_min, piece.v_max)]
        se = piece_positions[(OWNER, piece.u_max, piece.v_max)]
        u_width = float(piece.u_max - piece.u_min)
        expected_top = (u_width * cos_t, u_width * sin_t, 0.0)
        expected_bottom = (u_width * cos_t, u_width * sin_t, 0.0)
        actual_top = (ne[0] - nw[0], ne[1] - nw[1], ne[2] - nw[2])
        actual_bottom = (se[0] - sw[0], se[1] - sw[1], se[2] - sw[2])
        if not (close3(actual_top, expected_top) and close3(actual_bottom, expected_bottom)):
            orientation_ok = False
    report("PIECE_ORIENTATION_PRESERVED_ACROSS_ALL_NINE_PIECES", orientation_ok)

    report(
        "NO_NEW_SOURCE_PIXELS_CREATED",
        cell_addresses(footprint) == [(0, 0), (1, 0), (2, 0), (3, 0)],
    )

    # Toxic controls -- same domain rules as the frozen function.
    toxic_ok = True
    for bad_hinge in (0, footprint["width"], -1, footprint["width"] + 3):
        try:
            embed_declared_angle_ramp_fold_fractional(
                footprint, pieces, hinge_corner_x=bad_hinge, angle_degrees=solved.angle_degrees
            )
            toxic_ok = False
        except ValueError:
            pass
    try:
        embed_declared_angle_ramp_fold_fractional(
            footprint, pieces, hinge_corner_x=1.5, angle_degrees=solved.angle_degrees
        )
        toxic_ok = False
    except ValueError:
        pass
    try:
        out_of_domain = partition_cell_grid((99, 99), boundaries, boundaries, piece_ids)
        embed_declared_angle_ramp_fold_fractional(
            footprint, out_of_domain, hinge_corner_x=HINGE_X, angle_degrees=solved.angle_degrees
        )
        toxic_ok = False
    except ValueError:
        pass
    report("TOXIC_MALFORMED_HINGE_AND_OUT_OF_DOMAIN_OWNER_REJECTED", toxic_ok)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_RAMP_FOLD_EMBEDDING][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
