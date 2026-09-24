"""Embedding functions: intrinsic corner addresses -> 3D positions.

Every function here takes ONLY corner addresses as input and returns a
position per address. None of them may look at, or change, cell
addresses, payload, or adjacency -- per the doctrine's Immutability
Invariant (3.2_trixel_doctrine.md section 5.2), embedding may only change
extrinsic placement, never intrinsic identity.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Callable

from .addressing_v1 import corner_addresses
from .fractional_geometry_v1 import FractionalPiece

Position = tuple[float, float, float]
FractionalCornerKey = tuple[tuple[int, int], Fraction, Fraction]


def embed_flat(footprint: dict) -> dict[tuple[int, int], Position]:
    """Identity embedding: the footprint lies flat on the X-Z plane,
    Y=0, one world unit per cell (matches the declared cell_metric of 1.0
    used throughout this package)."""
    return {(x, r): (float(x), 0.0, float(r)) for x, r in corner_addresses(footprint)}


def embed_rigid(
    local_positions: dict[tuple[int, int], Position],
    *,
    translation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation_axis: str | None = None,
    rotation_degrees: float = 0.0,
) -> dict[tuple[int, int], Position]:
    """Whole-footprint rigid transform: one rotation about one declared
    axis through the origin, then one translation. Applied identically to
    every corner -- this can never change relative distances between
    corners, so it can never change the cell metric or adjacency."""
    theta = math.radians(rotation_degrees)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    def rotate(p: Position) -> Position:
        x, y, z = p
        if rotation_axis is None or rotation_degrees == 0.0:
            return (x, y, z)
        if rotation_axis == "x":
            return (x, y * cos_t - z * sin_t, y * sin_t + z * cos_t)
        if rotation_axis == "y":
            return (x * cos_t + z * sin_t, y, -x * sin_t + z * cos_t)
        if rotation_axis == "z":
            return (x * cos_t - y * sin_t, x * sin_t + y * cos_t, z)
        raise ValueError(f"rotation_axis must be x, y, or z, got {rotation_axis!r}")

    tx, ty, tz = translation
    return {
        address: (rx + tx, ry + ty, rz + tz)
        for address, p in local_positions.items()
        for rx, ry, rz in (rotate(p),)
    }


def embed_hard_90_degree_hinge_fold(
    footprint: dict, *, hinge_corner_x: int
) -> dict[tuple[int, int], Position]:
    """Split the footprint at an existing cell boundary and rotate the far
    side 90 degrees around the shared hinge line.

    hinge_corner_x must land exactly on a corner index strictly between 0
    and width (i.e. on an existing cell boundary, never through the
    middle of a cell) -- REJECT_EMBEDDING for anything else, matching the
    doctrine's requirement that topology-relevant decisions be explicit,
    never inferred or silently snapped.

    Near side (corner_x <= hinge_corner_x): stays on the flat plane,
    position = (x, 0, r).
    Far side (corner_x >= hinge_corner_x): rotates so the distance beyond
    the hinge becomes height instead of horizontal extension,
    position = (hinge_corner_x, x - hinge_corner_x, r).

    Both formulas agree exactly at corner_x == hinge_corner_x (offset is
    zero), which is what makes the hinge corner samples shared rather than
    duplicated -- proven, not merely asserted, by
    gate_pixel_geometry_hinge_fold_v1.py comparing both formulas directly
    at every hinge address.

    Every step along x moves exactly one unit along a single axis (X on
    the near side, Y on the far side) and every step along r moves exactly
    one unit along Z on both sides, so the declared cell_metric of 1.0 is
    preserved everywhere, including edges that cross the hinge -- no
    scaling, no UV stretching.
    """
    width = footprint["width"]
    if isinstance(hinge_corner_x, bool) or not isinstance(hinge_corner_x, int):
        raise ValueError("hinge_corner_x must be an int")
    if not (0 < hinge_corner_x < width):
        raise ValueError(
            f"hinge_corner_x must land on an existing cell boundary strictly "
            f"between 0 and {width}; REJECT_EMBEDDING for {hinge_corner_x}"
        )

    positions: dict[tuple[int, int], Position] = {}
    for x, r in corner_addresses(footprint):
        if x <= hinge_corner_x:
            positions[(x, r)] = (float(x), 0.0, float(r))
        else:
            offset = x - hinge_corner_x
            positions[(x, r)] = (float(hinge_corner_x), float(offset), float(r))
    return positions


def embed_cylindrical_closed_wrap(footprint: dict) -> dict[tuple[int, int], Position]:
    """Fold a footprint into a closed N-column cylindrical wrap: one exact
    hinge per column boundary, angle = 360/N degrees per boundary, radius
    chosen so every column-to-column chord equals the declared cell_metric
    of 1.0 EXACTLY:

        radius = 1 / (2 * sin(pi / N))

    This is the only order of operations this function is authorized to
    use -- the radius is derived FROM the declared 1.0 metric, never
    chosen first and forced onto the cells. Picking a radius first and
    letting the cells stretch to fit it is exactly the toxic case
    gate_pixel_geometry_cylindrical_wrap_v1.py's toxic control rejects; no
    parameter of this function permits that path.

    Corner x=0 and corner x=width land at EXACTLY the same 3D position for
    every row -- that is the explicit, provable seam closure. They remain
    distinct corner ADDRESSES (each with its own UV per artwork_mapping_
    v1's law that UV never depends on position) whose positions merely
    coincide; the seam's declared ADJACENCY comes only from
    adjacency_v1.closed_wrap_seam_adjacency(), never from this coincidence
    -- this function has no opinion about adjacency at all, matching every
    other embedding in this module.

    theta(x) = x * (2*pi/N); position = (R*sin(theta), R*(1-cos(theta)), r)
    -- theta(0) = 0 gives (0, 0, r), matching embed_flat's column-0 origin
    convention exactly, so a cylinder and a flat sheet start from the same
    place before curving away.
    """
    width = footprint["width"]
    if width < 3:
        raise ValueError(f"cylindrical wrap needs at least 3 columns; REJECT_EMBEDDING for width={width}")

    angle_increment = 2.0 * math.pi / width
    radius = 1.0 / (2.0 * math.sin(math.pi / width))

    positions: dict[tuple[int, int], Position] = {}
    for x, r in corner_addresses(footprint):
        theta = x * angle_increment
        positions[(x, r)] = (radius * math.sin(theta), radius * (1.0 - math.cos(theta)), float(r))
    return positions


def embed_declared_angle_ramp_fold(
    footprint: dict, *, hinge_corner_x: int, angle_degrees: float
) -> dict[tuple[int, int], Position]:
    """Generalizes embed_hard_90_degree_hinge_fold to an arbitrary declared
    angle instead of a hardwired 90 degrees. angle_degrees=90.0 reproduces
    that function's output exactly -- proven directly by
    gate_pixel_geometry_declared_angle_ramp_v1.py, which compares both
    formulas at every corner rather than trusting this docstring.

    The far side beyond the hinge is a RIGID rotation of a flat strip by
    angle_degrees around the hinge line -- the same rotation
    embed_rigid() performs, restricted to the corners beyond the hinge.
    A rotation never stretches anything, for ANY angle, so this function
    has no angle it is unsafe to accept on that basis. What it does NOT
    do is answer whether a given angle_degrees actually reaches whatever
    rise a caller needs -- that is
    ramp_geometry_v1.solve_ramp_run_and_angle()'s job, deliberately kept
    separate: this function only knows how to build the geometry once an
    angle has already been determined to be reachable.

    hinge_corner_x must land exactly on an existing cell boundary, same
    domain rule as embed_hard_90_degree_hinge_fold -- REJECT_EMBEDDING
    otherwise.
    """
    width = footprint["width"]
    if isinstance(hinge_corner_x, bool) or not isinstance(hinge_corner_x, int):
        raise ValueError("hinge_corner_x must be an int")
    if not (0 < hinge_corner_x < width):
        raise ValueError(
            f"hinge_corner_x must land on an existing cell boundary strictly "
            f"between 0 and {width}; REJECT_EMBEDDING for {hinge_corner_x}"
        )

    theta = math.radians(angle_degrees)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    positions: dict[tuple[int, int], Position] = {}
    for x, r in corner_addresses(footprint):
        if x <= hinge_corner_x:
            positions[(x, r)] = (float(x), 0.0, float(r))
        else:
            offset = x - hinge_corner_x
            positions[(x, r)] = (
                float(hinge_corner_x) + offset * cos_t,
                offset * sin_t,
                float(r),
            )
    return positions


def embed_flat_fractional(
    footprint: dict, pieces: list[FractionalPiece]
) -> dict[FractionalCornerKey, Position]:
    """Fractional sibling of embed_flat(): embeds every distinct sub-cell
    corner referenced by `pieces` on the SAME flat X-Z plane, Y=0, using
    the same one-world-unit-per-cell convention embed_flat() uses --
    cell_origin plus local fraction, floated only at this boundary:

        world_x = float(owner_x + u)
        world_z = float(owner_row + v)

    Corners are keyed by (owner_cell, u, v) rather than an integer corner
    address, because an interior fractional corner (0 < u < 1) is not
    part of addressing_v1's integer lattice at all -- it belongs only to
    the cell that owns it, never shared with a neighboring cell (this
    package still performs no welding/deduplication). Two pieces that
    share a boundary (piece_a.u_max == piece_b.u_min -- the SAME Fraction
    value by construction, see fractional_geometry_v1.partition_cell_u_
    axis) collapse to the SAME dict key here, so both get the identical
    embedded position computed exactly once -- never computed twice,
    matched approximately, or welded after the fact.

    When every piece is exactly the trivial [0,1] x [0,1] partition
    (fractional_geometry_v1.trivial_partition), every corner key's (u, v)
    is an integer in {0, 1}, and this function reproduces embed_flat()'s
    corresponding position EXACTLY: Fraction arithmetic on integers is
    exact, and float() of a small integer-valued Fraction is exact too,
    so there is no rounding gap between the two paths at the trivial
    partition -- this is what makes the 1.0-baseline regression provable
    byte-for-byte rather than only approximately.
    """
    width, height = footprint["width"], footprint["height"]
    positions: dict[FractionalCornerKey, Position] = {}
    for piece in pieces:
        owner_x, owner_row = piece.owner_cell
        if not (0 <= owner_x < width and 0 <= owner_row < height):
            raise ValueError(f"owner_cell out of footprint domain: {piece.owner_cell}")
        for u in (piece.u_min, piece.u_max):
            for v in (piece.v_min, piece.v_max):
                key = (piece.owner_cell, u, v)
                if key not in positions:
                    positions[key] = (float(owner_x + u), 0.0, float(owner_row + v))
    return positions


def embed_declared_angle_ramp_fold_fractional(
    footprint: dict,
    pieces: list[FractionalPiece],
    *,
    hinge_corner_x: int,
    angle_degrees: float,
) -> dict[FractionalCornerKey, Position]:
    """Fractional sibling of embed_declared_angle_ramp_fold(): embeds every
    distinct sub-cell corner referenced by `pieces` using the SAME
    per-point formula the frozen function applies to integer corner
    addresses, evaluated at a continuous local x = owner_x + u instead of
    only at integer x:

        if x <= hinge_corner_x: (x, 0, r)
        else: (hinge_corner_x + offset*cos(theta), offset*sin(theta), r)
            where offset = x - hinge_corner_x

    That formula was already point-wise and already a continuous rigid
    rotation (never a per-cell lookup), so evaluating it at more points
    invents no new geometry rule -- this function's entire content is
    reproducing the frozen math at fractional x, not extending it.
    hinge_corner_x must land on an existing cell boundary, the same
    domain rule embed_declared_angle_ramp_fold enforces -- REJECT_
    EMBEDDING otherwise. No cell interior straddles the hinge because the
    hinge lies on an integer cell boundary. Cells adjacent to the hinge
    may contain corners exactly on the hinge line; those points use the
    flat branch while the remaining points on the folded-side cell use
    the rotated branch. The two formulas coincide exactly at offset == 0
    (proven directly, not just asserted, by
    gate_pixel_geometry_fractional_hinge_contact_v1.py), so a piece whose
    own u range starts exactly at the hinge is still a single planar
    quad, never internally kinked between the two formulas.
    """
    width, height = footprint["width"], footprint["height"]
    if isinstance(hinge_corner_x, bool) or not isinstance(hinge_corner_x, int):
        raise ValueError("hinge_corner_x must be an int")
    if not (0 < hinge_corner_x < width):
        raise ValueError(
            f"hinge_corner_x must land on an existing cell boundary strictly "
            f"between 0 and {width}; REJECT_EMBEDDING for {hinge_corner_x}"
        )

    theta = math.radians(angle_degrees)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    positions: dict[FractionalCornerKey, Position] = {}
    for piece in pieces:
        owner_x, owner_row = piece.owner_cell
        if not (0 <= owner_x < width and 0 <= owner_row < height):
            raise ValueError(f"owner_cell out of footprint domain: {piece.owner_cell}")
        for u in (piece.u_min, piece.u_max):
            for v in (piece.v_min, piece.v_max):
                key = (piece.owner_cell, u, v)
                if key in positions:
                    continue
                x_local = owner_x + u  # exact Fraction arithmetic
                if x_local <= hinge_corner_x:
                    positions[key] = (float(x_local), 0.0, float(owner_row + v))
                else:
                    offset = float(x_local - hinge_corner_x)
                    positions[key] = (
                        float(hinge_corner_x) + offset * cos_t,
                        offset * sin_t,
                        float(owner_row + v),
                    )
    return positions
