#!/usr/bin/env python3
"""Trial 1 -- Flat 4x4 identity proof for trixel.pixel_geometry.v1."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, cell_addresses
from trixel.pixel_geometry.adjacency_v1 import compiled_adjacency_matches_source, source_adjacency
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.embedding_v1 import embed_flat
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_FLAT

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FLAT][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def main() -> int:
    labels = [
        ["A", "B", "C", "D"],
        ["E", "F", "G", "H"],
        ["I", "J", "K", "L"],
        ["M", "N", "O", "P"],
    ]
    footprint = build_footprint(4, 4, labels)

    addresses = cell_addresses(footprint)
    report("SIXTEEN_UNIQUE_ADDRESSES", len(addresses) == 16 and len(set(addresses)) == 16)

    adjacency = source_adjacency(footprint)
    degree_counts = sorted(len(v) for v in adjacency.values())
    expected_degrees = sorted([2, 2, 2, 2] + [3] * 8 + [4, 4, 4, 4])
    report(
        "DEGREE_DISTRIBUTION_2x4_3x8_4x4",
        degree_counts == expected_degrees,
        f"got {degree_counts}",
    )

    positions = embed_flat(footprint)
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_FLAT)
    report(
        "COMPILED_ADJACENCY_MATCHES_SOURCE",
        compiled_adjacency_matches_source(footprint, compiled["compiled_adjacency"]),
    )
    report("SIXTEEN_PRESERVED_DISPOSITIONS", len(compiled["dispositions"]) == 16)
    report(
        "ALL_DISPOSITIONS_PRESERVED_1_TO_1",
        all(v == "PRESERVED_1_TO_1" for v in compiled["dispositions"].values()),
    )
    report(
        "ARTWORK_PAYLOAD_STAYS_AT_ITS_ADDRESS",
        all(
            prim["payload"] == labels[prim["cell_address"][1]][prim["cell_address"][0]]
            for prim in compiled["primitive_provenance"]
        ),
    )
    report(
        "EVERY_PRIMITIVE_HAS_PROVENANCE",
        len(compiled["primitive_provenance"]) == 16
        and all("cell_address" in p for p in compiled["primitive_provenance"]),
    )

    # Toxic cases -- each must fail closed.
    toxic_ok = True
    try:
        build_footprint(4, 4, [row[:3] for row in labels])  # omitted cell
        toxic_ok = False
    except ValueError:
        pass
    try:
        build_footprint(4, 4, labels + [["X", "X", "X", "X"]])  # wrong row count
        toxic_ok = False
    except ValueError:
        pass
    try:
        build_footprint(0, 4, [])  # non-positive width
        toxic_ok = False
    except ValueError:
        pass
    report("TOXIC_MALFORMED_PAYLOADS_REJECTED", toxic_ok)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FLAT][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
