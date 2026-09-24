#!/usr/bin/env python3
"""Fractional geometry, Phase 4 -- the 1.0-baseline regression.

Proves the new compile_footprint_fractional()/embed_flat_fractional()
path changes NOTHING when used with the trivial (no-op) partition: the
existing whole-unit 1.0 geometry stays the control, and the fractional
path must collapse onto it exactly wherever raw list identity is
achievable (a single-cell footprint has no cross-cell corner sharing to
diverge on), and by structural + coordinate equality everywhere else (a
multi-cell footprint's fractional path never welds corners across cells,
so its raw vertex list is necessarily longer than compile_footprint()'s
shared-corner array -- that is an intentional, documented difference in
REPRESENTATION, never a difference in the actual geometry it describes).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint, cell_addresses, corner_index
from trixel.pixel_geometry.adjacency_v1 import source_adjacency
from trixel.pixel_geometry.compiler_v1 import compile_footprint, compile_footprint_fractional, edge_lengths
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_FLAT, EMBEDDING_FLAT_FRACTIONAL
from trixel.pixel_geometry.embedding_v1 import embed_flat, embed_flat_fractional
from trixel.pixel_geometry.fractional_geometry_v1 import trivial_partition

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_BASELINE][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def single_cell_case() -> None:
    footprint = build_footprint(1, 1, [["PIXEL_A"]])

    positions_orig = embed_flat(footprint)
    compiled_orig = compile_footprint(footprint, positions_orig, embedding_id=EMBEDDING_FLAT)

    pieces = trivial_partition((0, 0))
    piece_positions = embed_flat_fractional(footprint, pieces)
    compiled_frac = compile_footprint_fractional(
        footprint, {}, piece_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL
    )

    report(
        "SINGLE_CELL_POSITIONS_BYTE_IDENTICAL",
        compiled_frac["positions"] == compiled_orig["positions"],
        f"orig={compiled_orig['positions']} frac={compiled_frac['positions']}",
    )
    report(
        "SINGLE_CELL_INDICES_BYTE_IDENTICAL",
        compiled_frac["indices"] == compiled_orig["indices"],
        f"orig={compiled_orig['indices']} frac={compiled_frac['indices']}",
    )
    report(
        "SINGLE_CELL_DISPOSITIONS_BYTE_IDENTICAL",
        compiled_frac["dispositions"] == compiled_orig["dispositions"],
    )
    report(
        "SINGLE_CELL_ADJACENCY_BYTE_IDENTICAL",
        compiled_frac["compiled_adjacency"] == compiled_orig["compiled_adjacency"],
    )

    prim_orig = compiled_orig["primitive_provenance"][0]
    prim_frac = compiled_frac["primitive_provenance"][0]
    shared_keys_match = all(prim_orig[k] == prim_frac[k] for k in prim_orig)
    only_new_key_is_piece_id = set(prim_frac) - set(prim_orig) == {"piece_id"}
    report(
        "SINGLE_CELL_PROVENANCE_SHARED_FIELDS_MATCH_ONLY_PIECE_ID_ADDED",
        shared_keys_match and only_new_key_is_piece_id,
        f"orig={prim_orig} frac={prim_frac}",
    )

    report(
        "SINGLE_CELL_EDGE_LENGTHS_BYTE_IDENTICAL",
        edge_lengths(compiled_orig) == edge_lengths(compiled_frac),
        f"orig={edge_lengths(compiled_orig)} frac={edge_lengths(compiled_frac)}",
    )


def multi_cell_structural_case() -> None:
    labels = [
        ["A", "B", "C", "D"],
        ["E", "F", "G", "H"],
        ["I", "J", "K", "L"],
        ["M", "N", "O", "P"],
    ]
    footprint = build_footprint(4, 4, labels)
    addresses = cell_addresses(footprint)
    width = footprint["width"]

    positions_orig = embed_flat(footprint)
    compiled_orig = compile_footprint(footprint, positions_orig, embedding_id=EMBEDDING_FLAT)

    all_pieces = [piece for x, r in addresses for piece in trivial_partition((x, r))]
    piece_positions = embed_flat_fractional(footprint, all_pieces)
    compiled_frac = compile_footprint_fractional(footprint, {}, piece_positions, embedding_id=EMBEDDING_FLAT_FRACTIONAL)

    report(
        "MULTI_CELL_SAME_PRIMITIVE_COUNT",
        len(compiled_frac["primitive_provenance"]) == len(compiled_orig["primitive_provenance"]) == 16,
    )
    report(
        "MULTI_CELL_SAME_INDEX_COUNT",
        len(compiled_frac["indices"]) == len(compiled_orig["indices"]) == 96,
    )
    report(
        "MULTI_CELL_DISPOSITIONS_BYTE_IDENTICAL",
        compiled_frac["dispositions"] == compiled_orig["dispositions"],
    )
    report(
        "MULTI_CELL_ADJACENCY_BYTE_IDENTICAL",
        compiled_frac["compiled_adjacency"] == compiled_orig["compiled_adjacency"] == source_adjacency(footprint),
    )

    payload_and_count_match = True
    coordinates_match = True
    for i, (x, r) in enumerate(addresses):
        prim_orig = compiled_orig["primitive_provenance"][i]
        prim_frac = compiled_frac["primitive_provenance"][i]
        if prim_orig["cell_address"] != prim_frac["cell_address"]:
            payload_and_count_match = False
        if prim_orig["payload"] != prim_frac["payload"]:
            payload_and_count_match = False
        if prim_orig["primitive_count"] != prim_frac["primitive_count"]:
            payload_and_count_match = False

        base = i * 4
        frac_nw, frac_ne, frac_sw, frac_se = compiled_frac["positions"][base : base + 4]
        orig_nw = compiled_orig["positions"][corner_index(x, r, width)]
        orig_ne = compiled_orig["positions"][corner_index(x + 1, r, width)]
        orig_sw = compiled_orig["positions"][corner_index(x, r + 1, width)]
        orig_se = compiled_orig["positions"][corner_index(x + 1, r + 1, width)]
        if (frac_nw, frac_ne, frac_sw, frac_se) != (orig_nw, orig_ne, orig_sw, orig_se):
            coordinates_match = False

    report("MULTI_CELL_PROVENANCE_CELL_ADDRESS_PAYLOAD_COUNT_MATCH", payload_and_count_match)
    report(
        "MULTI_CELL_PER_CELL_WORLD_COORDINATES_MATCH_EXACTLY",
        coordinates_match,
        "fractional path never shares corners across cells, so its raw "
        "positions list is longer than compile_footprint()'s; this check "
        "instead confirms every individual cell's four world-space corner "
        "coordinates are exactly identical, not merely close",
    )
    report(
        "MULTI_CELL_POSITIONS_LIST_LENGTH_DIFFERS_AS_EXPECTED",
        len(compiled_frac["positions"]) == 64 and len(compiled_orig["positions"]) == 25,
        "64 (4 independent corners x 16 cells, no cross-cell welding) vs "
        "25 (5x5 shared corner lattice) -- documented representation "
        "difference, not a geometry difference",
    )


def main() -> int:
    single_cell_case()
    multi_cell_structural_case()
    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_FRACTIONAL_BASELINE][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
