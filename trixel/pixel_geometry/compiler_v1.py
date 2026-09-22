"""Compile an embedded footprint into canonical geometry + provenance.

This never decides adjacency or dispositions from the embedded positions
-- adjacency comes only from adjacency_v1.source_adjacency() (declared
addresses), dispositions are always PRESERVED_1_TO_1 for the trials this
package currently implements (no merge/split/cull policy exists yet).
The compiler's only geometric job is turning corner positions into
triangles and recording which cell owns which triangle.
"""
from __future__ import annotations

from typing import Any

from .addressing_v1 import cell_addresses, corner_index, validate_footprint_structure
from .adjacency_v1 import source_adjacency
from .contracts_v1 import (
    COMPILATION_ARTIFACT_CONTRACT,
    TOPOLOGY_CLOSED_WRAP_SEAM,
    TOPOLOGY_PRESERVE_EXACT,
)

Position = tuple[float, float, float]


def compile_footprint(
    footprint: dict[str, Any],
    corner_positions: dict[tuple[int, int], Position],
    *,
    embedding_id: str,
) -> dict[str, Any]:
    validate_footprint_structure(footprint)
    width, height = footprint["width"], footprint["height"]

    expected_corners = {(x, r) for r in range(height + 1) for x in range(width + 1)}
    if set(corner_positions) != expected_corners:
        raise ValueError("corner_positions must cover exactly the footprint's corner domain")

    positions: list[Position] = [None] * len(expected_corners)  # type: ignore[list-item]
    for (x, r), pos in corner_positions.items():
        positions[corner_index(x, r, width)] = pos

    indices: list[int] = []
    primitive_provenance: list[dict[str, Any]] = []
    dispositions: dict[tuple[int, int], str] = {}

    for x, r in cell_addresses(footprint):
        nw = corner_index(x, r, width)
        ne = corner_index(x + 1, r, width)
        sw = corner_index(x, r + 1, width)
        se = corner_index(x + 1, r + 1, width)
        primitive_start = len(indices) // 3
        indices.extend([nw, sw, ne, ne, sw, se])
        primitive_provenance.append(
            {
                "cell_address": [x, r],
                "primitive_start": primitive_start,
                "primitive_count": 2,
                "payload": footprint["payload"][r][x],
            }
        )
        dispositions[(x, r)] = "PRESERVED_1_TO_1"

    return {
        "contract": COMPILATION_ARTIFACT_CONTRACT,
        "embedding_id": embedding_id,
        "topology_policy": TOPOLOGY_PRESERVE_EXACT,
        "footprint_width": width,
        "footprint_height": height,
        "compiled_adjacency": source_adjacency(footprint),
        "dispositions": dispositions,
        "positions": positions,
        "indices": indices,
        "primitive_provenance": primitive_provenance,
    }


def compile_closed_wrap_footprint(
    footprint: dict[str, Any],
    corner_positions: dict[tuple[int, int], Position],
    *,
    embedding_id: str,
    seam_adjacency: dict[tuple[int, int], set[tuple[int, int]]],
) -> dict[str, Any]:
    """Like compile_footprint(), for a topology that explicitly declares
    adjacency beyond the cardinal grid (a closed cylindrical wrap's
    column-0/column-(width-1) seam). This function never invents that
    adjacency itself -- the caller must supply seam_adjacency, normally
    adjacency_v1.closed_wrap_seam_adjacency(footprint), so the declaration
    is made once, by address, in the one file that owns adjacency
    authority. All triangle/provenance/disposition geometry is identical
    to compile_footprint(); only compiled_adjacency and topology_policy
    are overridden to honestly reflect that an edge was added."""
    compiled = compile_footprint(footprint, corner_positions, embedding_id=embedding_id)
    compiled["compiled_adjacency"] = seam_adjacency
    compiled["topology_policy"] = TOPOLOGY_CLOSED_WRAP_SEAM
    return compiled


def edge_lengths(compiled: dict[str, Any]) -> list[float]:
    """Every cell edge length in the compiled geometry -- used to prove
    the declared cell_metric (1.0) held everywhere, including hinge
    crossings. Returns one length per unique cell edge (both triangle
    legs that fall on a shared cell boundary, deduplicated by construction
    since we only walk cell-grid edges here, not triangle diagonals)."""
    width, height = compiled["footprint_width"], compiled["footprint_height"]
    positions = compiled["positions"]
    lengths: list[float] = []

    def dist(a: int, b: int) -> float:
        ax, ay, az = positions[a]
        bx, by, bz = positions[b]
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5

    for r in range(height + 1):
        for x in range(width):
            lengths.append(dist(corner_index(x, r, width), corner_index(x + 1, r, width)))
    for x in range(width + 1):
        for r in range(height):
            lengths.append(dist(corner_index(x, r, width), corner_index(x, r + 1, width)))
    return lengths


def positions_by_cell_center(compiled: dict[str, Any]) -> dict[tuple[int, int], Position]:
    """Approximate cell-center positions (average of the cell's 4 corners)
    -- used only for the proximity-derived-adjacency toxic check, never for
    identity or ownership."""
    width, height = compiled["footprint_width"], compiled["footprint_height"]
    positions = compiled["positions"]
    centers: dict[tuple[int, int], Position] = {}
    for r in range(height):
        for x in range(width):
            corners = [
                positions[corner_index(x, r, width)],
                positions[corner_index(x + 1, r, width)],
                positions[corner_index(x, r + 1, width)],
                positions[corner_index(x + 1, r + 1, width)],
            ]
            cx = sum(c[0] for c in corners) / 4.0
            cy = sum(c[1] for c in corners) / 4.0
            cz = sum(c[2] for c in corners) / 4.0
            centers[(x, r)] = (cx, cy, cz)
    return centers
