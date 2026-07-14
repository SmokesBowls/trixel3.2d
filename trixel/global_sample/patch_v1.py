"""Neutral 16x16-cell / 17x17-corner global-sample patch authority."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import jsonschema

PATCH_CONTRACT_ID = "trixel.global_sample_patch.v1"
CELL_COUNT = 16
SAMPLE_COUNT = 17
TOP_POSITION_COUNT = 289
TOP_TRIANGLE_COUNT = 512
TOP_INDEX_COUNT = 1536


def _bounded_integer(value: Any, minimum: int, maximum: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in [{minimum}, {maximum}]")
    return value


def _integer_pair(value: Any, name: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must contain exactly two integers")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        raise ValueError(f"{name} must contain exactly two integers")
    return value[0], value[1]


def cell_index(local_cell_x: int, local_cell_z: int) -> int:
    x = _bounded_integer(local_cell_x, 0, CELL_COUNT - 1, "local_cell_x")
    z = _bounded_integer(local_cell_z, 0, CELL_COUNT - 1, "local_cell_z")
    return z * CELL_COUNT + x


def sample_index(local_sample_x: int, local_sample_z: int) -> int:
    x = _bounded_integer(local_sample_x, 0, SAMPLE_COUNT - 1, "local_sample_x")
    z = _bounded_integer(local_sample_z, 0, SAMPLE_COUNT - 1, "local_sample_z")
    return z * SAMPLE_COUNT + x


def global_sample_address(
    patch_address: list[int] | tuple[int, int],
    local_sample_x: int,
    local_sample_z: int,
) -> tuple[int, int]:
    patch_x, patch_z = _integer_pair(patch_address, "patch_address")
    x = _bounded_integer(local_sample_x, 0, SAMPLE_COUNT - 1, "local_sample_x")
    z = _bounded_integer(local_sample_z, 0, SAMPLE_COUNT - 1, "local_sample_z")
    return patch_x * CELL_COUNT + x, patch_z * CELL_COUNT + z


def validate_patch_structure(packet: dict[str, Any]) -> None:
    """Validate generic geometry semantics without imposing a domain contract ID."""
    _integer_pair(packet.get("patch_address"), "patch_address")
    if packet.get("cell_dimensions") != [CELL_COUNT, CELL_COUNT]:
        raise ValueError("global-sample patch v1 requires 16x16 logical cells")
    if packet.get("sample_dimensions") != [SAMPLE_COUNT, SAMPLE_COUNT]:
        raise ValueError("cell-corner sampling requires 17x17 samples")
    if packet.get("sample_layout") != "cell_corners":
        raise ValueError("artwork pixels must not be interpreted as corner samples")
    if packet.get("sample_order") != "row_major_local_z_then_local_x":
        raise ValueError("sample order must be local-Z rows, then local-X columns")
    if packet.get("art_dimensions") != [CELL_COUNT, CELL_COUNT]:
        raise ValueError("logical artwork region must be exactly 16x16")
    art_region = packet.get("art_region")
    if not isinstance(art_region, dict) or art_region.get("pixel_dimensions") != [CELL_COUNT, CELL_COUNT]:
        raise ValueError("one patch must reference exactly one 16x16 art region")
    texture_path = art_region.get("texture_path")
    pixel_origin = art_region.get("pixel_origin")
    if not isinstance(texture_path, str) or not texture_path:
        raise ValueError("art_region.texture_path must be a non-empty string")
    if (
        not isinstance(pixel_origin, (list, tuple))
        or len(pixel_origin) != 2
        or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in pixel_origin)
    ):
        raise ValueError("art_region.pixel_origin must contain two non-negative integers")
    samples = packet.get("elevation_samples")
    if not isinstance(samples, list) or len(samples) != SAMPLE_COUNT * SAMPLE_COUNT:
        raise ValueError("elevation_samples must contain exactly 289 values")
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) for value in samples):
        raise ValueError("elevation_samples must contain only finite numbers")
    expected_topology = {
        "top_position_count": TOP_POSITION_COUNT,
        "top_triangle_count": TOP_TRIANGLE_COUNT,
        "top_index_count": TOP_INDEX_COUNT,
    }
    if packet.get("canonical_topology") != expected_topology:
        raise ValueError("canonical top-surface counts do not conform to v1")
    expected_surfaces = {
        "top": {"source": "canonical_topology"},
        "cliffs": {"status": "not_generated"},
        "bottom": {"status": "not_generated"},
    }
    if packet.get("render_surfaces") != expected_surfaces:
        raise ValueError("v1 packets declare the canonical top only")


def validate_patch_packet(packet: dict[str, Any], schema: dict[str, Any]) -> None:
    jsonschema.Draft7Validator.check_schema(schema)
    jsonschema.validate(instance=packet, schema=schema)
    if packet.get("contract_id") != PATCH_CONTRACT_ID:
        raise ValueError("unsupported global-sample patch contract")
    validate_patch_structure(packet)


def build_patch_packet(
    patch_address: list[int] | tuple[int, int],
    elevation_at: Callable[[int, int], float],
    terrain_recipe: str,
    art_region: dict[str, Any],
) -> dict[str, Any]:
    """Build one patch solely from global sample addresses and presentation refs."""
    patch_x, patch_z = _integer_pair(patch_address, "patch_address")
    if not isinstance(terrain_recipe, str) or not terrain_recipe:
        raise ValueError("terrain_recipe must be a non-empty string")
    samples: list[float] = []
    for local_z in range(SAMPLE_COUNT):
        for local_x in range(SAMPLE_COUNT):
            global_x, global_z = global_sample_address([patch_x, patch_z], local_x, local_z)
            value = elevation_at(global_x, global_z)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"non-finite elevation at global sample {(global_x, global_z)}")
            samples.append(float(value))
    packet = {
        "contract_id": PATCH_CONTRACT_ID,
        "patch_address": [patch_x, patch_z],
        "cell_dimensions": [CELL_COUNT, CELL_COUNT],
        "sample_dimensions": [SAMPLE_COUNT, SAMPLE_COUNT],
        "sample_layout": "cell_corners",
        "sample_order": "row_major_local_z_then_local_x",
        "art_dimensions": [CELL_COUNT, CELL_COUNT],
        "art_region": dict(art_region),
        "elevation_samples": samples,
        "terrain_recipe": terrain_recipe,
        "canonical_topology": {
            "top_position_count": TOP_POSITION_COUNT,
            "top_triangle_count": TOP_TRIANGLE_COUNT,
            "top_index_count": TOP_INDEX_COUNT,
        },
        "render_surfaces": {
            "top": {"source": "canonical_topology"},
            "cliffs": {"status": "not_generated"},
            "bottom": {"status": "not_generated"},
        },
    }
    validate_patch_structure(packet)
    return packet


def compile_canonical_top(packet: dict[str, Any]) -> dict[str, list[Any]]:
    """Compile canonical top positions/indices only; never add cliffs or bottoms."""
    validate_patch_structure(packet)
    samples = packet["elevation_samples"]
    positions = [
        [float(local_x), float(samples[sample_index(local_x, local_z)]), float(local_z)]
        for local_z in range(SAMPLE_COUNT)
        for local_x in range(SAMPLE_COUNT)
    ]
    indices: list[int] = []
    for local_z in range(CELL_COUNT):
        for local_x in range(CELL_COUNT):
            north_west = sample_index(local_x, local_z)
            north_east = sample_index(local_x + 1, local_z)
            south_west = sample_index(local_x, local_z + 1)
            south_east = sample_index(local_x + 1, local_z + 1)
            indices.extend([north_west, north_east, south_west, north_east, south_east, south_west])
    if len(positions) != TOP_POSITION_COUNT or len(indices) != TOP_INDEX_COUNT:
        raise ValueError("compiler failed canonical topology proof")
    return {"positions": positions, "indices": indices}
