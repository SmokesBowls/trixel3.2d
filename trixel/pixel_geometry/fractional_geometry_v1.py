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
    """True only if this single piece spans the entire [0,1] u-range --
    used to decide whether a cell's disposition is the ordinary
    PRESERVED_1_TO_1 or the new fractional-subdivision disposition,
    independent of whatever piece_id string the caller chose."""
    return piece.u_min == ZERO and piece.u_max == ONE


def partition_cell_u_axis(
    owner_cell: tuple[int, int],
    boundaries: list[Fraction],
    piece_ids: list[str],
) -> list[FractionalPiece]:
    """Partition one cell along its u axis only (v stays the full [0,1]
    span -- the only axis this first proof needs).

    boundaries must be an exact, strictly increasing list of
    fractions.Fraction starting at ZERO and ending at ONE, e.g.
    [ZERO, Fraction(1, 20), Fraction(19, 20), ONE]. Each adjoining pair of
    pieces derives its shared edge from the SAME boundaries[i] element --
    piece[i].u_max and piece[i+1].u_min are read from the identical list
    entry, never recomputed independently, so they can never disagree.
    This is the SHARED BOUNDARY RULE: one boundary, computed once,
    referenced by both pieces on either side of it.
    """
    if len(boundaries) < 2:
        raise ValueError("need at least two boundaries (0 and 1)")
    if not all(isinstance(b, Fraction) for b in boundaries):
        raise ValueError("boundaries must be exact fractions.Fraction values, not floats")
    if boundaries[0] != ZERO or boundaries[-1] != ONE:
        raise ValueError("boundaries must start at exactly 0 and end at exactly 1")
    if any(boundaries[i] >= boundaries[i + 1] for i in range(len(boundaries) - 1)):
        raise ValueError("boundaries must be strictly increasing")
    if len(piece_ids) != len(boundaries) - 1:
        raise ValueError("need exactly one piece_id per boundary interval")
    if len(set(piece_ids)) != len(piece_ids):
        raise ValueError("piece_ids must be unique within one cell's partition")

    return [
        FractionalPiece(owner_cell, piece_ids[i], boundaries[i], boundaries[i + 1], ZERO, ONE)
        for i in range(len(boundaries) - 1)
    ]


def piece_u_width(piece: FractionalPiece) -> Fraction:
    return piece.u_max - piece.u_min


def pieces_share_owner(pieces: list[FractionalPiece], owner_cell: tuple[int, int]) -> bool:
    return bool(pieces) and all(p.owner_cell == owner_cell for p in pieces)


def pieces_partition_unit_interval(pieces: list[FractionalPiece]) -> bool:
    """True only if the given pieces (which must all declare the same
    owner_cell) cover exactly [0, 1] along u with no gap and no overlap --
    checked by EXACT fractions.Fraction equality throughout, never a
    float tolerance comparison."""
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
