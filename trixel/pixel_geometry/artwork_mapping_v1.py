"""Artwork/UV mapping: intrinsic corner address -> canonical artwork coordinate.

This module has exactly one responsibility:

    intrinsic corner address
            v
    canonical artwork coordinate (u, v)

It never looks at 3D position, embedding kind, or any Blender/renderer
concept -- that is the whole point of keeping it separate from
embedding_v1.py and compiler_v1.py. A corner's UV is a pure function of
its address and the footprint's declared width/height, nothing else.

THE KEY LAW THIS MODULE EXISTS TO ENFORCE:

    THE EMBEDDING MUST NEVER ALTER THE UV ADDRESS.

Flat and folded geometry may place a corner at different (x, y, z)
positions. They must produce identical (u, v) for the same corner
address, because the UV comes only from the address, never from a
position. Do not derive UVs from world position -- that would destroy the
entire fold-vs-stretch proof this package exists to support.
"""
from __future__ import annotations

from typing import Any

from .addressing_v1 import corner_addresses

UV = tuple[float, float]


def corner_uv(corner_x: int, corner_row: int, width: int, height: int) -> UV:
    """Canonical artwork coordinate for one corner address.

    u = corner_x / width
    v = 1.0 - (corner_row / height)

    corner_row=0 is the "top" of the footprint (v=1.0); corner_row=height
    is the "bottom" (v=0.0) -- matching the usual image convention where
    row 0 is the top of the source image.
    """
    if not (0 <= corner_x <= width):
        raise ValueError(f"corner_x out of domain: {corner_x}")
    if not (0 <= corner_row <= height):
        raise ValueError(f"corner_row out of domain: {corner_row}")
    u = corner_x / width
    v = 1.0 - (corner_row / height)
    return (u, v)


def footprint_corner_uvs(footprint: dict[str, Any]) -> dict[tuple[int, int], UV]:
    """UV for every corner address declared by the footprint, keyed the
    same way as embedding_v1's position dicts: {(x, row): (u, v)}."""
    width, height = footprint["width"], footprint["height"]
    return {
        (x, row): corner_uv(x, row, width, height)
        for x, row in corner_addresses(footprint)
    }


def uvs_are_identical(a: dict[tuple[int, int], UV], b: dict[tuple[int, int], UV], *, tol: float = 1e-12) -> bool:
    """True only if both UV maps cover exactly the same addresses and every
    UV pair matches within tolerance. Used to prove that two differently
    embedded (flat vs. folded) compilations of the same footprint carry
    identical intrinsic artwork coordinates."""
    if set(a) != set(b):
        return False
    return all(
        abs(a[key][0] - b[key][0]) <= tol and abs(a[key][1] - b[key][1]) <= tol
        for key in a
    )
