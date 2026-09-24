"""Sub-cell fractional geometry: exact rational partitions inside one
cell's [0,1] x [0,1] ownership domain.

addressing_v1.py owns the integer cell/corner lattice -- pixel ownership,
source-pixel identity, and cardinal adjacency all live there and are
never touched by this module. This module owns a SECOND coordinate
system, strictly BELOW one cell, for legal geometric coordinates inside
that cell's unit square. Boundaries are exact fractions.Fraction values,
not floats -- so two adjoining pieces share a boundary because they read
the identical Fraction object/value, never because two independently
computed floats happened to land close enough to snap together.

This module knows:
    - the owning cell_address (an ordinary addressing_v1 address; never
      minted here, never altered)
    - exact local boundaries inside [0, 1] on one axis
    - piece identity and order
    - source-cell provenance (owner_cell, carried on every piece)

This module does NOT know, and must never import:
    - world-space position (embedding_v1's job)
    - rendering, textures, Blender, Godot
    - mesh welding/deduplication -- there is none here; pieces that share
      a boundary value are never merged into one vertex or one cell just
      because their coordinates agree. PROXIMITY MUST NEVER IMPLY
      TOPOLOGY, the same law adjacency_v1.py enforces at the cell level,
      applies here one level down: this module never compares pieces
      across different owner_cells at all.

A partition never creates a new logical cell. Every piece it produces
still declares owner_cell exactly as given; multiple pieces sharing one
owner_cell is the entire point (one pixel, many geometric facets).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

ZERO = Fraction(0, 1)
ONE = Fraction(1, 1)


@dataclass(frozen=True)
class FractionalPiece:
    """One geometric piece inside a single cell's [0,1] x [0,1] ownership
    domain.

    owner_cell: an ordinary addressing_v1 cell address (x, row). Multiple
        pieces may declare the SAME owner_cell -- that is required, not
        incidental: it is how "one pixel owns multiple geometric pieces"
        is represented.
    piece_id: caller-declared identity for this piece within its cell
        (e.g. "cut_low", "main", "cut_high"); unique within one cell's
        partition, meaningless across different cells.
    u_min, u_max: exact local bounds along the cell's u (column) axis,
        0 <= u_min < u_max <= 1.
    v_min, v_max: exact local bounds along the cell's v (row) axis,
        0 <= v_min < v_max <= 1. The first proof only partitions u, so
        every piece it produces has v_min=ZERO, v_max=ONE (the full row
        span) -- but the field exists on every piece so a future two-axis
        partition needs no new data structure.
    """

    owner_cell: tuple[int, int]
    piece_id: str
    u_min: Fraction
    u_max: Fraction
    v_min: Fraction
    v_max: Fraction


def trivial_partition(owner_cell: tuple[int, int], *, piece_id: str = "main") -> list[FractionalPiece]:
    """The whole cell as a single piece, spanning [0,1] x [0,1] exactly --
    the no-op partition the fractional path must collapse to when no
    subdivision is declared. This is what a cell absent from a caller's
    partition map defaults to."""
    return [FractionalPiece(owner_cell, piece_id, ZERO, ONE, ZERO, ONE)]


def is_trivial_piece(piece: FractionalPiece) -> bool:
    """True only if this single piece spans the entire [0,1] x [0,1]
    domain on BOTH axes -- used to decide whether a cell's disposition is
    the ordinary PRESERVED_1_TO_1 or the new fractional-subdivision
    disposition, independent of whatever piece_id string the caller
    chose. Every trivial_partition() piece already spans both axes
    fully, so this generalization from the first (u-only) proof changes
    nothing for any Phase A partition."""
    return piece.u_min == ZERO and piece.u_max == ONE and piece.v_min == ZERO and piece.v_max == ONE


def _validate_axis_boundaries(boundaries: list[Fraction], axis_name: str) -> None:
    """Shared validation for one axis' boundary list -- used by both the
    1D (u-only) and 2D (u and v independently) partition constructors so
    the SHARED BOUNDARY RULE's preconditions are enforced identically on
    every axis, in exactly one place."""
    if len(boundaries) < 2:
        raise ValueError(f"need at least two {axis_name} boundaries (0 and 1)")
    if not all(isinstance(b, Fraction) for b in boundaries):
        raise ValueError(f"{axis_name} boundaries must be exact fractions.Fraction values, not floats")
    if boundaries[0] != ZERO or boundaries[-1] != ONE:
        raise ValueError(f"{axis_name} boundaries must start at exactly 0 and end at exactly 1")
    if any(boundaries[i] >= boundaries[i + 1] for i in range(len(boundaries) - 1)):
        raise ValueError(f"{axis_name} boundaries must be strictly increasing")


def partition_cell_u_axis(
    owner_cell: tuple[int, int],
    boundaries: list[Fraction],
    piece_ids: list[str],
) -> list[FractionalPiece]:
    """Partition one cell along its u axis only (v stays the full [0,1]
    span -- the only axis the first proof needed).

    boundaries must be an exact, strictly increasing list of
    fractions.Fraction starting at ZERO and ending at ONE, e.g.
    [ZERO, Fraction(1, 20), Fraction(19, 20), ONE]. Each adjoining pair of
    pieces derives its shared edge from the SAME boundaries[i] element --
    piece[i].u_max and piece[i+1].u_min are read from the identical list
    entry, never recomputed independently, so they can never disagree.
    This is the SHARED BOUNDARY RULE: one boundary, computed once,
    referenced by both pieces on either side of it.
    """
    _validate_axis_boundaries(boundaries, "u")
    if len(piece_ids) != len(boundaries) - 1:
        raise ValueError("need exactly one piece_id per boundary interval")
    if len(set(piece_ids)) != len(piece_ids):
        raise ValueError("piece_ids must be unique within one cell's partition")

    return [
        FractionalPiece(owner_cell, piece_ids[i], boundaries[i], boundaries[i + 1], ZERO, ONE)
        for i in range(len(boundaries) - 1)
    ]


def partition_cell_grid(
    owner_cell: tuple[int, int],
    u_boundaries: list[Fraction],
    v_boundaries: list[Fraction],
    piece_ids: list[list[str]],
) -> list[FractionalPiece]:
    """Partition one cell independently along BOTH axes -- the 2D
    generalization of partition_cell_u_axis. u_boundaries and
    v_boundaries are each validated exactly like partition_cell_u_axis's
    single boundary list (exact, strictly increasing Fractions from 0 to
    1). The SHARED BOUNDARY RULE applies on both axes at once: every
    piece in the same column reads the identical u_boundaries element,
    every piece in the same row reads the identical v_boundaries
    element, and a piece at a grid corner shares BOTH an exact u
    boundary and an exact v boundary with its diagonal neighbor -- so
    every interior intersection point is reached by exactly the same
    Fraction pair from every piece that touches it, never recomputed.

    piece_ids[vi][ui] is the piece_id for the piece spanning
    u_boundaries[ui]..u_boundaries[ui+1] and v_boundaries[vi]..
    v_boundaries[vi+1] -- row-major (v outer, u inner), matching how
    footprint payload rows are already addressed elsewhere in this
    package (payload[row][x]).
    """
    _validate_axis_boundaries(u_boundaries, "u")
    _validate_axis_boundaries(v_boundaries, "v")
    rows, cols = len(v_boundaries) - 1, len(u_boundaries) - 1
    if len(piece_ids) != rows or any(len(row) != cols for row in piece_ids):
        raise ValueError(f"piece_ids must be a {rows} x {cols} grid matching the boundaries")
    flat_ids = [pid for row in piece_ids for pid in row]
    if len(set(flat_ids)) != len(flat_ids):
        raise ValueError("piece_ids must be unique within one cell's partition")

    return [
        FractionalPiece(
            owner_cell,
            piece_ids[vi][ui],
            u_boundaries[ui],
            u_boundaries[ui + 1],
            v_boundaries[vi],
            v_boundaries[vi + 1],
        )
        for vi in range(rows)
        for ui in range(cols)
    ]


def piece_u_width(piece: FractionalPiece) -> Fraction:
    return piece.u_max - piece.u_min


def piece_v_height(piece: FractionalPiece) -> Fraction:
    return piece.v_max - piece.v_min


def piece_area(piece: FractionalPiece) -> Fraction:
    return piece_u_width(piece) * piece_v_height(piece)


def pieces_share_owner(pieces: list[FractionalPiece], owner_cell: tuple[int, int]) -> bool:
    return bool(pieces) and all(p.owner_cell == owner_cell for p in pieces)


def pieces_partition_unit_interval(pieces: list[FractionalPiece]) -> bool:
    """True only if the given pieces (which must all declare the same
    owner_cell) cover exactly [0, 1] along u with no gap and no overlap --
    checked by EXACT fractions.Fraction equality throughout, never a
    float tolerance comparison. 1D-specific (assumes every piece spans
    the full v range); see pieces_partition_unit_square for the general
    2D check."""
    if not pieces:
        return False
    if len({p.owner_cell for p in pieces}) != 1:
        return False
    ordered = sorted(pieces, key=lambda p: p.u_min)
    if ordered[0].u_min != ZERO or ordered[-1].u_max != ONE:
        return False
    for a, b in zip(ordered, ordered[1:]):
        if a.u_max != b.u_min:
            return False
    total = sum((piece_u_width(p) for p in ordered), ZERO)
    return total == ONE


def pieces_partition_unit_square(pieces: list[FractionalPiece]) -> bool:
    """True only if the given pieces (which must all declare the same
    owner_cell) exactly tile [0,1] x [0,1] with no gap and no overlap --
    the 2D generalization of pieces_partition_unit_interval, and a strict
    superset of what it checks (a 1D partition is just a 2D partition
    with exactly one v band, and this function proves that case too).

    Reconstructs the distinct u and v boundary values FROM the pieces
    themselves, then demands the pieces be EXACTLY the full grid those
    boundaries imply -- one piece per (u-band, v-band) cell, no fewer, no
    more, no duplicate rectangle. This is a direct, exact proof of full
    coverage without gaps or overlaps (every expected grid cell is
    present exactly once), not an area-sum heuristic."""
    if not pieces:
        return False
    if len({p.owner_cell for p in pieces}) != 1:
        return False
    u_values = sorted({p.u_min for p in pieces} | {p.u_max for p in pieces})
    v_values = sorted({p.v_min for p in pieces} | {p.v_max for p in pieces})
    if u_values[0] != ZERO or u_values[-1] != ONE:
        return False
    if v_values[0] != ZERO or v_values[-1] != ONE:
        return False
    expected_cells = {
        (u_values[ui], u_values[ui + 1], v_values[vi], v_values[vi + 1])
        for ui in range(len(u_values) - 1)
        for vi in range(len(v_values) - 1)
    }
    actual_cells = {(p.u_min, p.u_max, p.v_min, p.v_max) for p in pieces}
    if len(actual_cells) != len(pieces):
        return False
    return actual_cells == expected_cells
