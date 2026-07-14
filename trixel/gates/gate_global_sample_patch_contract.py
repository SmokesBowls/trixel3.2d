#!/usr/bin/env python3
"""Fail-closed acceptance gate for the neutral 16-cell global-sample patch contract."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "trixel" / "global_sample" / "schemas" / "global_sample_patch_packet_v1.schema.json"
sys.path.insert(0, str(ROOT))


def report(name: str, ok: bool) -> bool:
    print(f"[GLOBAL_SAMPLE_PATCH_GATE][{name}] {'TRUE' if ok else 'FALSE'}")
    return ok


def main() -> int:
    checks: list[bool] = [report("SCHEMA_EXISTS", SCHEMA.is_file())]
    try:
        from trixel.global_sample.patch_v1 import (
            build_patch_packet,
            cell_index,
            compile_canonical_top,
            global_sample_address,
            sample_index,
            validate_patch_packet,
        )
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"[GLOBAL_SAMPLE_PATCH_GATE][API_IMPORTABLE] FALSE — {exc}")
        report("ALL_GATES", False)
        return 1
    checks.append(report("API_IMPORTABLE", True))
    if not SCHEMA.is_file():
        report("ALL_GATES", False)
        return 1

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    packet = build_patch_packet(
        patch_address=[-2, 3],
        elevation_at=lambda x, z: x * 0.25 + z * 0.5,
        terrain_recipe="example.neutral",
        art_region={
            "texture_path": "res://example.png",
            "pixel_origin": [16, 32],
            "pixel_dimensions": [16, 16],
        },
    )
    validate_patch_packet(packet, schema)
    checks.extend(
        [
            report("PACKET_VALID", True),
            report("SAMPLE_ORDER_LOCKED", sample_index(16, 16) == 288),
            report("CELL_DOMAIN_LOCKED", cell_index(15, 15) == 255),
            report("GLOBAL_ADDRESS_NEGATIVE_PATCH", global_sample_address([-2, 3], 16, 0) == (-16, 48)),
            report("SHARED_EDGE_ADDRESS", global_sample_address([0, 0], 16, 7) == global_sample_address([1, 0], 0, 7)),
        ]
    )
    compiled = compile_canonical_top(packet)
    checks.extend(
        [
            report("TOP_POSITIONS_289", len(compiled["positions"]) == 289),
            report("TOP_TRIANGLES_512", len(compiled["indices"]) // 3 == 512),
            report("TOP_INDICES_1536", len(compiled["indices"]) == 1536),
        ]
    )

    bad_art_region_rejected = False
    try:
        build_patch_packet(
            patch_address=[0, 0],
            elevation_at=lambda x, z: 0.0,
            terrain_recipe="example.neutral",
            art_region={"pixel_dimensions": [16, 16]},
        )
    except ValueError:
        bad_art_region_rejected = True
    checks.append(report("BUILDER_REJECTS_INCOMPLETE_ART_REGION", bad_art_region_rejected))

    for name, mutation in (
        ("REJECT_16X16_CORNER_SAMPLES", ("sample_dimensions", [16, 16])),
        ("REJECT_450_TRIANGLE_HISTORY", ("canonical_topology", {"top_position_count": 256, "top_triangle_count": 450, "top_index_count": 1350})),
        ("REJECT_ART_AS_SAMPLES", ("sample_layout", "art_pixels")),
        ("REJECT_GENERATED_CLIFF_CLAIM", ("render_surfaces", {"top": {"source": "canonical_topology"}, "cliffs": {"status": "generated"}, "bottom": {"status": "not_generated"}})),
    ):
        candidate = copy.deepcopy(packet)
        candidate[mutation[0]] = mutation[1]
        try:
            validate_patch_packet(candidate, schema)
            rejected = False
        except (ValueError, jsonschema.ValidationError):
            rejected = True
        checks.append(report(name, rejected))

    all_ok = all(checks)
    report("ALL_GATES", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
