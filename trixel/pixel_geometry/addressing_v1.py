"""Immutable footprint addressing: cells and their corner samples.

A footprint of width W x height H cells has (W+1) x (H+1) corner samples
(same cell-corners convention as trixel/global_sample/patch_v1.py, applied
here to an arbitrary W x H rather than the fixed 16x16). Cell and corner
addresses are the footprint's intrinsic identity and never change under
any embedding -- only the corner samples' 3D positions change.
"""
from __future__ import annotations

from typing import Any


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def build_footprint(width: int, height: int, payload: list[list[Any]]) -> dict[str, Any]:
    """Build an immutable footprint definition.

    payload[y][x] is the intrinsic per-cell content (label/color/etc.) --
    it travels with the cell address through every embedding and is never
    regenerated from geometry.
    """
    width = _positive_int(width, "width")
    height = _positive_int(height, "height")
    if len(payload) != height or any(len(row) != width for row in payload):
        raise ValueError(f"payload must be exactly {height} rows of {width} cells")
    return {
        "contract": "trixel.footprint_definition.v1",
        "width": width,
        "height": height,
        "payload": [list(row) for row in payload],
    }


def cell_index(x: int, y: int, width: int) -> int:
    if not (0 <= x < width):
        raise ValueError(f"cell x out of domain: {x}")
    return y * width + x


def corner_index(x: int, y: int, width: int) -> int:
    """Corner samples run 0..width inclusive (one more than cell count)."""
    if not (0 <= x <= width):
        raise ValueError(f"corner x out of domain: {x}")
    return y * (width + 1) + x


def cell_addresses(footprint: dict[str, Any]) -> list[tuple[int, int]]:
    width, height = footprint["width"], footprint["height"]
    return [(x, y) for y in range(height) for x in range(width)]


def corner_addresses(footprint: dict[str, Any]) -> list[tuple[int, int]]:
    width, height = footprint["width"], footprint["height"]
    return [(x, y) for y in range(height + 1) for x in range(width + 1)]


def validate_footprint_structure(footprint: dict[str, Any]) -> None:
    if footprint.get("contract") != "trixel.footprint_definition.v1":
        raise ValueError("unsupported footprint contract")
    width, height = footprint.get("width"), footprint.get("height")
    _positive_int(width, "width")
    _positive_int(height, "height")
    payload = footprint.get("payload")
    if not isinstance(payload, list) or len(payload) != height:
        raise ValueError("payload row count must equal height")
    if any(not isinstance(row, list) or len(row) != width for row in payload):
        raise ValueError("every payload row must contain exactly width cells")
    addresses = cell_addresses(footprint)
    if len(addresses) != width * height or len(set(addresses)) != len(addresses):
        raise ValueError("cell addresses must be unique and cover the declared domain exactly")
