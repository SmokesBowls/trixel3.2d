"""Cardinal adjacency, derived ONLY from declared cell addresses.

This is the authority the doctrine's NO_PROXIMITY_DERIVED_ADJACENCY
invariant protects: two cells are neighbors if and only if their
addresses are cardinally adjacent in the source grid. Nothing here ever
looks at a 3D position. compiled_adjacency_matches_source() is the
function every embedding trial must pass -- if an embedding changes this
result, it silently performed an undeclared topology operation.
"""
from __future__ import annotations

from .addressing_v1 import cell_addresses


def source_adjacency(footprint: dict) -> dict[tuple[int, int], set[tuple[int, int]]]:
    width, height = footprint["width"], footprint["height"]
    adjacency: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for x, y in cell_addresses(footprint):
        neighbors = set()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                neighbors.add((nx, ny))
        adjacency[(x, y)] = neighbors
    return adjacency


def compiled_adjacency_matches_source(
    footprint: dict, compiled_adjacency: dict[tuple[int, int], set[tuple[int, int]]]
) -> bool:
    """The one check every embedding trial (flat/rigid/hinge-fold) must
    satisfy: whatever the compiler emits as adjacency must be byte-for-byte
    the same as source_adjacency(), regardless of what 3D positions the
    embedding produced. No embedding in this package is authorized to add
    or remove an edge from this graph -- that would require an explicit
    topology policy, which trials 1/2/2.5 never declare."""
    return compiled_adjacency == source_adjacency(footprint)


def closed_wrap_seam_adjacency(footprint: dict) -> dict[tuple[int, int], set[tuple[int, int]]]:
    """Declared adjacency for a closed cylindrical wrap: the SAME cardinal
    source_adjacency() every other trial uses, PLUS one explicit extra
    edge per row joining the last column to the first column.

    This is the only place any cylinder trial is authorized to add an edge
    beyond the cardinal grid, and it is declared here BY ADDRESS, before
    any embedding runs -- exactly the same discipline source_adjacency()
    itself follows. It never looks at a 3D position, so it cannot be
    confused with the proximity-derived adjacency
    no_proximity_derived_adjacency() exists to catch."""
    width, height = footprint["width"], footprint["height"]
    if width < 3:
        raise ValueError(f"closed wrap needs at least 3 columns; REJECT for width={width}")
    adjacency = {addr: set(neighbors) for addr, neighbors in source_adjacency(footprint).items()}
    for row in range(height):
        first, last = (0, row), (width - 1, row)
        adjacency[first].add(last)
        adjacency[last].add(first)
    return adjacency


def compiled_adjacency_matches_closed_wrap(
    footprint: dict, compiled_adjacency: dict[tuple[int, int], set[tuple[int, int]]]
) -> bool:
    """The closed-wrap analogue of compiled_adjacency_matches_source(): what
    the compiler emits for a cylindrical specimen must be byte-for-byte the
    SAME declared closed_wrap_seam_adjacency(), regardless of what 3D
    positions the embedding produced."""
    return compiled_adjacency == closed_wrap_seam_adjacency(footprint)


def no_proximity_derived_adjacency(
    positions_by_cell: dict[tuple[int, int], tuple[float, float, float]],
    declared_adjacency: dict[tuple[int, int], set[tuple[int, int]]],
    *,
    proximity_tolerance: float,
) -> list[tuple[tuple[int, int], tuple[int, int], float]]:
    """Toxic check: find any pair of cells that ended up spatially close
    after embedding but are NOT declared neighbors. A non-empty result
    does not mean adjacency was wrongly inferred (nothing here infers
    anything) -- it means the embedding placed unrelated cells close
    enough that a naive geometry-only pipeline *could* have been tempted
    to weld them, which this package must never do. Returns the
    offending pairs with their distance for inspection."""
    offenders = []
    cells = list(positions_by_cell)
    for i, a in enumerate(cells):
        for b in cells[i + 1 :]:
            if b in declared_adjacency.get(a, set()):
                continue
            if a == b:
                continue
            ax, ay, az = positions_by_cell[a]
            bx, by, bz = positions_by_cell[b]
            distance = ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5
            if distance <= proximity_tolerance:
                offenders.append((a, b, distance))
    return offenders
