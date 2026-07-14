#!/usr/bin/env python3
"""Fail-closed pair and rectangular-field gate for global-sample assembly."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
PATCH_SCHEMA = ROOT / "trixel" / "global_sample" / "schemas" / "global_sample_patch_packet_v1.schema.json"
FIELD_SCHEMA = ROOT / "trixel" / "global_sample" / "schemas" / "global_sample_field_packet_v1.schema.json"
sys.path.insert(0, str(ROOT))


def report(name: str, ok: bool) -> bool:
    print(f"[GLOBAL_SAMPLE_FIELD_GATE][{name}] {'TRUE' if ok else 'FALSE'}")
    return ok


def main() -> int:
    checks = [report("PATCH_SCHEMA_EXISTS", PATCH_SCHEMA.is_file()), report("FIELD_SCHEMA_EXISTS", FIELD_SCHEMA.is_file())]
    try:
        from trixel.global_sample.field_v1 import (
            assemble_field_packet,
            collect_unique_global_samples,
            generate_field_patch_packets,
            iter_neighbor_pairs,
            validate_field_packet,
            validate_field_patch_set,
        )
        from trixel.global_sample.patch_v1 import global_sample_address, sample_index, validate_patch_packet
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"[GLOBAL_SAMPLE_FIELD_GATE][API_IMPORTABLE] FALSE — {exc}")
        report("ALL_GATES", False)
        return 1
    checks.append(report("API_IMPORTABLE", True))
    if not PATCH_SCHEMA.is_file() or not FIELD_SCHEMA.is_file():
        report("ALL_GATES", False)
        return 1

    patch_schema = json.loads(PATCH_SCHEMA.read_text(encoding="utf-8"))
    field_schema = json.loads(FIELD_SCHEMA.read_text(encoding="utf-8"))
    elevation_at = lambda x, z: float(x * 1000 + z)

    pair_field = assemble_field_packet(
        field_patch_dimensions=[2, 1],
        field_patch_origin=[4, -3],
        elevation_algorithm_id="example.address_height.v1",
        material_id="example.neutral",
        texture_path="res://example.png",
    )
    validate_field_packet(pair_field, field_schema)
    pair = generate_field_patch_packets(pair_field, elevation_at)
    west, east = pair
    address_ok = all(global_sample_address(west["patch_address"], 16, z) == global_sample_address(east["patch_address"], 0, z) for z in range(17))
    value_ok = all(west["elevation_samples"][sample_index(16, z)] == east["elevation_samples"][sample_index(0, z)] for z in range(17))
    validate_field_patch_set(pair_field, pair)
    checks.extend(
        [
            report("PAIR_PATCH_COUNT_2", len(pair) == 2),
            report("PAIR_17_SHARED_ADDRESSES", address_ok),
            report("PAIR_17_SHARED_VALUES", value_ok),
            report("PAIR_UNIQUE_SAMPLES_561", len(collect_unique_global_samples(pair)) == 33 * 17),
        ]
    )
    conflict = copy.deepcopy(east)
    conflict["elevation_samples"][sample_index(0, 8)] += 1.0
    try:
        collect_unique_global_samples([west, conflict])
        rejected = False
    except ValueError:
        rejected = True
    checks.append(report("CONFLICT_FAILS_CLOSED", rejected))

    for name, candidate in (
        ("MISSING_PATCH_FAILS_CLOSED", [west]),
        ("DUPLICATE_PATCH_FAILS_CLOSED", [west, west]),
    ):
        try:
            validate_field_patch_set(pair_field, candidate)
            candidate_rejected = False
        except ValueError:
            candidate_rejected = True
        checks.append(report(name, candidate_rejected))

    field = assemble_field_packet(
        field_patch_dimensions=[8, 8],
        field_patch_origin=[0, 0],
        elevation_algorithm_id="example.address_height.v1",
        material_id="example.neutral",
        texture_path="res://example.png",
    )
    validate_field_packet(field, field_schema)
    patches = generate_field_patch_packets(field, elevation_at)
    patch_valid = True
    for packet in patches:
        try:
            validate_patch_packet(packet, patch_schema)
        except (ValueError, jsonschema.ValidationError):
            patch_valid = False
    checks.extend(
        [
            report("FIELD_PACKET_VALID", True),
            report("FIELD_PATCHES_64", len(patches) == 64),
            report("ALL_PATCHES_VALID", patch_valid),
            report("UNIQUE_GLOBAL_SAMPLES_16641", len(collect_unique_global_samples(patches)) == 129 * 129),
            report("NEIGHBOR_BOUNDARIES_112", len(list(iter_neighbor_pairs(field))) == 112),
            report("DECLARED_COUNTS_DERIVED", field["canonical_field_topology"] == {"chunk_count": 64, "chunk_local_top_position_count": 18496, "top_triangle_count": 32768, "top_index_count": 98304, "unique_global_sample_count": 16641, "neighbor_boundary_count": 112}),
        ]
    )

    bad = copy.deepcopy(field)
    bad["global_sample_dimensions"] = [128, 129]
    try:
        validate_field_packet(bad, field_schema)
        bad_rejected = False
    except (ValueError, jsonschema.ValidationError):
        bad_rejected = True
    checks.append(report("BAD_DERIVED_DIMENSIONS_FAIL_CLOSED", bad_rejected))

    all_ok = all(checks)
    report("ALL_GATES", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
