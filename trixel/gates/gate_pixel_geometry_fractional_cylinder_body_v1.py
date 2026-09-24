#!/usr/bin/env python3
"""Fractional geometry, Phase D -- fractional pieces on the cylindrical
body, away from the declared seam.

acf321e  A    1D fractional subdivision (flat)
529ec78  B    2D fractional subdivision (flat)
67c29b5  C    fractional pieces on the declared ramp/fold
023273a  C.5  exact fractional hinge contact
THIS     D    fractional pieces on the closed cylindrical wrap, one cell
              well away from the column-0 / column-(N-1) seam

Invariant this phase establishes:

    fractional subdivision refines the parent cell's proven geometry;
    it does not redefine that geometry.

The ramp mapping is affine over each cell, so its formula could be
evaluated at fractional x directly (Phase C). The cylinder's trig
formula is NOT affine over a cell -- it is only authoritative at the
integer corners of an N-sided polygon. Fractional points therefore
interpolate inside the parent cell's flat face. Re-sampling the analytic
circle instead is kept here as a toxic control and is measured to leave
the face and stretch the metric.

Seam contact is deliberately NOT tested here -- that is Phase D.5.
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
from trixel.pixel_geometry.adjacency_v1 import closed_wrap_seam_adjacency, source_adjacency
from trixel.pixel_geometry.compiler_v1 import (
    compile_closed_wrap_footprint,
    compile_closed_wrap_footprint_fractional,
)
from trixel.pixel_geometry.contracts_v1 import (
    DISPOSITION_PRESERVED_1_TO_1,
    DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION,
    EMBEDDING_CYLINDRICAL_CLOSED_WRAP,
    EMBEDDING_CYLINDRICAL_CLOSED_WRAP_FRACTIONAL,
    TOPOLOGY_CLOSED_WRAP_SEAM,
)
from trixel.pixel_geometry.embedding_v1 import (
    embed_cylindrical_closed_wrap,
    embed_cylindrical_closed_wrap_fractional,
)
from trixel.pixel_geometry.fractional_geometry_v1 import (
    ONE,
    ZERO,
    partition_cell_grid,
    pieces_share_owner,
    trivial_partition,
)

CHECKS: list[bool] = []

WIDTH = 8
HEIGHT = 3
OWNER = (4, 1)  # columns 3/5 on either side, seam is between columns 0 and 7


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_CYLINDER_BODY][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= tol


def close3(a: tuple, b: tuple, tol: float = 1e-12) -> bool:
    return all(close(x, y, tol) for x, y in zip(a, b))


def sub(a: tuple, b: tuple) -> tuple:
    return tuple(x - y for x, y in zip(a, b))


def dot(a: tuple, b: tuple) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a: tuple, b: tuple) -> tuple:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a: tuple) -> float:
    return math.sqrt(dot(a, a))


def main() -> int:
    labels = [[f"{chr(65 + r)}{x}" for x in range(WIDTH)] for r in range(HEIGHT)]
    footprint = build_footprint(WIDTH, HEIGHT, labels)
    seam = closed_wrap_seam_adjacency(footprint)

    frozen = embed_cylindrical_closed_wrap(footprint)
    frozen_compiled = compile_closed_wrap_footprint(
        footprint, frozen, embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, seam_adjacency=seam
    )
    ox, orow = OWNER
    f_nw, f_ne = frozen[(ox, orow)], frozen[(ox + 1, orow)]
    f_sw, f_se = frozen[(ox, orow + 1)], frozen[(ox + 1, orow + 1)]

    low, high = Fraction(1, 20), Fraction(19, 20)
    boundaries = [ZERO, low, high, ONE]
    piece_ids = [
        ["nw_corner", "n_edge", "ne_corner"],
        ["w_edge", "main", "e_edge"],
        ["sw_corner", "s_edge", "se_corner"],
    ]
    pieces = partition_cell_grid(OWNER, boundaries, boundaries, piece_ids)
    by_id = {p.piece_id: p for p in pieces}
    report("ONE_OWNER_NINE_PIECES", pieces_share_owner(pieces, OWNER) and len(pieces) == 9)

    others = [p for addr in cell_addresses(footprint) if addr != OWNER for p in trivial_partition(addr)]
    positions = embed_cylindrical_closed_wrap_fractional(footprint, pieces + others)
    compiled = compile_closed_wrap_footprint_fractional(
        footprint,
        {OWNER: pieces},
        positions,
        embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP_FRACTIONAL,
        seam_adjacency=seam,
    )

    owner_prov = [p for p in compiled["primitive_provenance"] if p["cell_address"] == list(OWNER)]
    report(
        "PROVENANCE_NINE_ENTRIES_ALL_OWNED_BY_THE_ORIGINAL_CELL",
        len(owner_prov) == 9
        and [p["piece_id"] for p in owner_prov] == [p.piece_id for p in pieces]
        and all(p["payload"] == labels[orow][ox] for p in owner_prov),
    )
    report(
        "DISPOSITIONS_OWNER_FRACTIONAL_EVERY_OTHER_CELL_1_TO_1",
        compiled["dispositions"][OWNER] == DISPOSITION_PRESERVED_FRACTIONAL_SUBDIVISION
        and all(
            v == DISPOSITION_PRESERVED_1_TO_1 for k, v in compiled["dispositions"].items() if k != OWNER
        )
        and len(compiled["dispositions"]) == WIDTH * HEIGHT,
    )

    # Topology: identical to the frozen cylinder's compiled topology, seam
    # edges included, and nothing new.
    report(
        "COMPILED_ADJACENCY_IDENTICAL_TO_FROZEN_CYLINDER_TOPOLOGY",
        compiled["compiled_adjacency"] == frozen_compiled["compiled_adjacency"] == seam
        and compiled["topology_policy"] == frozen_compiled["topology_policy"] == TOPOLOGY_CLOSED_WRAP_SEAM,
    )
    cardinal = source_adjacency(footprint)
    seam_edges = {
        (a, b) for a, ns in compiled["compiled_adjacency"].items() for b in ns if b not in cardinal[a]
    }
    expected_seam_edges = {((0, r), (WIDTH - 1, r)) for r in range(HEIGHT)} | {
        ((WIDTH - 1, r), (0, r)) for r in range(HEIGHT)
    }
    report(
        "NO_NEW_SEAM_RELATION_ONLY_THE_DECLARED_ONE_EDGE_PER_ROW",
        seam_edges == expected_seam_edges,
        f"{len(seam_edges)} directed seam edges",
    )
    report(
        "OWNER_IS_AWAY_FROM_THE_SEAM",
        compiled["compiled_adjacency"][OWNER] == {(ox - 1, orow), (ox + 1, orow), (ox, orow - 1), (ox, orow + 1)}
        and all(OWNER not in e for e in seam_edges),
    )

    owner_base = owner_prov[0]["primitive_start"] * 2
    report(
        "NO_WELDING_NO_MERGE_SPLIT_OR_CULL",
        len(compiled["positions"]) == (WIDTH * HEIGHT - 1) * 4 + 36
        and len(compiled["primitive_provenance"]) == (WIDTH * HEIGHT - 1) + 9,
        f"{len(compiled['positions'])} vertices, {len(compiled['primitive_provenance'])} provenance entries",
    )

    # Trivial partition reproduces the frozen whole-cell cylinder EXACTLY
    # (==, not a tolerance) -- for every cell in the footprint.
    all_trivial = [p for addr in cell_addresses(footprint) for p in trivial_partition(addr)]
    trivial_positions = embed_cylindrical_closed_wrap_fractional(footprint, all_trivial)
    trivial_exact = all(
        trivial_positions[((x, r), ZERO, ZERO)] == frozen[(x, r)]
        and trivial_positions[((x, r), ONE, ZERO)] == frozen[(x + 1, r)]
        and trivial_positions[((x, r), ZERO, ONE)] == frozen[(x, r + 1)]
        and trivial_positions[((x, r), ONE, ONE)] == frozen[(x + 1, r + 1)]
        for x, r in cell_addresses(footprint)
    )
    report("TRIVIAL_PARTITION_REPRODUCES_FROZEN_CYLINDER_CORNERS_EXACTLY", trivial_exact)
    report(
        "NINE_PIECE_OUTER_EXTENT_EQUALS_FROZEN_CELL_CORNERS_EXACTLY",
        positions[(OWNER, ZERO, ZERO)] == f_nw
        and positions[(OWNER, ONE, ZERO)] == f_ne
        and positions[(OWNER, ZERO, ONE)] == f_sw
        and positions[(OWNER, ONE, ONE)] == f_se,
    )

    # Every fractional corner independently checked against the parent
    # face: on its plane, and at the affine position the exact (u, v)
    # address names.
    normal = cross(sub(f_ne, f_nw), sub(f_sw, f_nw))
    unit_normal = tuple(c / norm(normal) for c in normal)
    on_face = True
    at_address = True
    for piece in pieces:
        for u in (piece.u_min, piece.u_max):
            for v in (piece.v_min, piece.v_max):
                p = positions[(OWNER, u, v)]
                if not close(dot(sub(p, f_nw), unit_normal), 0.0):
                    on_face = False
                expected = tuple(
                    f_nw[i] + float(u) * (f_ne[i] - f_nw[i]) + float(v) * (f_sw[i] - f_nw[i]) for i in range(3)
                )
                if not close3(p, expected):
                    at_address = False
    report("EVERY_FRACTIONAL_CORNER_LIES_ON_THE_PARENT_CELL_FACE", on_face)
    report("EVERY_FRACTIONAL_CORNER_SITS_AT_ITS_EXACT_ADDRESS_ON_THE_FACE", at_address)

    # Metric: every sub-edge has length exactly its exact width/height x 1.0.
    metric_ok = True
    u_row_total = 0.0
    for piece in pieces:
        nw = positions[(OWNER, piece.u_min, piece.v_min)]
        ne = positions[(OWNER, piece.u_max, piece.v_min)]
        sw = positions[(OWNER, piece.u_min, piece.v_max)]
        if not close(norm(sub(ne, nw)), float(piece.u_max - piece.u_min)):
            metric_ok = False
        if not close(norm(sub(sw, nw)), float(piece.v_max - piece.v_min)):
            metric_ok = False
        if piece.v_min == ZERO:
            u_row_total += norm(sub(ne, nw))
    report(
        "METRIC_PRESERVED_EVERY_SUB_EDGE_EQUALS_ITS_EXACT_EXTENT",
        metric_ok and close(u_row_total, 1.0),
        f"top-row sub-edge sum={u_row_total!r}",
    )

    def corners(piece_id: str) -> tuple:
        idx = owner_base + list(by_id).index(piece_id) * 4
        return tuple(compiled["positions"][idx : idx + 4])

    shared_ok = (
        corners("main")[0] == corners("n_edge")[2] == corners("w_edge")[1] == corners("nw_corner")[3]
        and corners("main")[1] == corners("n_edge")[3] == corners("e_edge")[0] == corners("ne_corner")[2]
        and corners("main")[2] == corners("w_edge")[3] == corners("s_edge")[0] == corners("sw_corner")[1]
        and corners("main")[3] == corners("e_edge")[2] == corners("s_edge")[1] == corners("se_corner")[0]
    )
    report("SHARED_FRACTIONAL_BOUNDARIES_MAP_TO_IDENTICAL_WORLD_POSITIONS", shared_ok)

    u_dir = sub(f_ne, f_nw)
    v_dir = sub(f_sw, f_nw)
    orientation_ok = True
    for piece in pieces:
        nw, ne, sw, _se = corners(piece.piece_id)
        uw, vh = float(piece.u_max - piece.u_min), float(piece.v_max - piece.v_min)
        if not close3(sub(ne, nw), tuple(uw * c for c in u_dir)):
            orientation_ok = False
        if not close3(sub(sw, nw), tuple(vh * c for c in v_dir)):
            orientation_ok = False
    report("PIECE_ORIENTATION_MATCHES_PARENT_FACE_AXES", orientation_ok)

    # TOXIC CONTROL (local to this gate, never production): re-sample the
    # analytic circle at fractional x. It must be measured to leave the
    # proven face and stretch the metric.
    angle_increment = 2.0 * math.pi / WIDTH
    radius = 1.0 / (2.0 * math.sin(math.pi / WIDTH))

    def circle_sample(u: Fraction, v: Fraction) -> tuple:
        theta = float(ox + u) * angle_increment
        return (radius * math.sin(theta), radius * (1.0 - math.cos(theta)), float(orow + v))

    strip = by_id["nw_corner"]  # u in [0, 1/20]: a 5% strip
    strip_len = norm(sub(circle_sample(strip.u_max, ZERO), circle_sample(strip.u_min, ZERO)))
    strip_stretch = strip_len / float(strip.u_max - strip.u_min)
    expected_strip_stretch = 2.0 * radius * math.sin(float(strip.u_max - strip.u_min) * math.pi / WIDTH) / float(
        strip.u_max - strip.u_min
    )
    off_face = abs(dot(sub(circle_sample(low, ZERO), f_nw), unit_normal))
    report(
        "TOXIC_CIRCLE_RESAMPLING_STRETCHES_THE_METRIC",
        strip_stretch > 1.01 and close(strip_stretch, expected_strip_stretch, tol=1e-9),
        f"5% strip stretch={strip_stretch:.6f} (analytic {expected_strip_stretch:.6f})",
    )
    report(
        "TOXIC_CIRCLE_RESAMPLING_LEAVES_THE_PROVEN_FACE",
        off_face > 1e-3,
        f"u=1/20 point is {off_face:.6f} off the parent face",
    )

    toxic_ok = True
    try:
        embed_cylindrical_closed_wrap_fractional(footprint, partition_cell_grid((WIDTH, 0), boundaries, boundaries, piece_ids))
        toxic_ok = False
    except ValueError:
        pass
    try:
        narrow = build_footprint(2, 1, [["a", "b"]])
        embed_cylindrical_closed_wrap_fractional(narrow, trivial_partition((0, 0)))
        toxic_ok = False
    except ValueError:
        pass
    report("TOXIC_OUT_OF_DOMAIN_OWNER_AND_TOO_FEW_COLUMNS_REJECTED", toxic_ok)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_CYLINDER_BODY][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
