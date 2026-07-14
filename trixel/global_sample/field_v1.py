"""Neutral rectangular field assembly over authoritative global sample addresses."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import jsonschema

from .patch_v1 import (
    CELL_COUNT,
    PATCH_CONTRACT_ID,
    SAMPLE_COUNT,
    TOP_INDEX_COUNT,
    TOP_POSITION_COUNT,
    TOP_TRIANGLE_COUNT,
    build_patch_packet,
    global_sample_address,
    sample_index,
    validate_patch_structure,
)

FIELD_CONTRACT_ID = "trixel.global_sample_patch_field.v1"


def _positive_pair(value: Any, name: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must contain exactly two positive integers")
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in value):
        raise ValueError(f"{name} must contain exactly two positive integers")
    return value[0], value[1]


def _integer_pair(value: Any, name: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must contain exactly two integers")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        raise ValueError(f"{name} must contain exactly two integers")
    return value[0], value[1]


def _derived_topology(width: int, height: int) -> dict[str, int]:
    chunks = width * height
    return {
        "chunk_count": chunks,
        "chunk_local_top_position_count": chunks * TOP_POSITION_COUNT,
        "top_triangle_count": chunks * TOP_TRIANGLE_COUNT,
        "top_index_count": chunks * TOP_INDEX_COUNT,
        "unique_global_sample_count": (width * CELL_COUNT + 1) * (height * CELL_COUNT + 1),
        "neighbor_boundary_count": (width - 1) * height + (height - 1) * width,
    }


def assemble_field_packet(
    field_patch_dimensions: list[int] | tuple[int, int],
    field_patch_origin: list[int] | tuple[int, int],
    elevation_algorithm_id: str,
    material_id: str,
    texture_path: str,
) -> dict[str, Any]:
    """Declare a deterministic rectangular patch registry in Z-major/X-major order."""
    width, height = _positive_pair(field_patch_dimensions, "field_patch_dimensions")
    origin_x, origin_z = _integer_pair(field_patch_origin, "field_patch_origin")
    for value, name in ((elevation_algorithm_id, "elevation_algorithm_id"), (material_id, "material_id"), (texture_path, "texture_path")):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string")
    patches = [
        {"patch_address": [origin_x + x, origin_z + z], "material_id": material_id}
        for z in range(height)
        for x in range(width)
    ]
    return {
        "contract_id": FIELD_CONTRACT_ID,
        "patch_contract_id": PATCH_CONTRACT_ID,
        "field_patch_origin": [origin_x, origin_z],
        "field_patch_dimensions": [width, height],
        "patch_cell_dimensions": [CELL_COUNT, CELL_COUNT],
        "field_cell_dimensions": [width * CELL_COUNT, height * CELL_COUNT],
        "global_sample_dimensions": [width * CELL_COUNT + 1, height * CELL_COUNT + 1],
        "elevation_authority": {
            "source": "global_sample_coordinates",
            "algorithm_id": elevation_algorithm_id,
            "address_space": "global_sample_xz",
        },
        "materials": {
            material_id: {
                "texture_path": texture_path,
                "logical_art_dimensions": [CELL_COUNT, CELL_COUNT],
            }
        },
        "patches": patches,
        "canonical_field_topology": _derived_topology(width, height),
        "geometry_policy": {
            "chunk_surface": "canonical_top_only",
            "skirts": False,
            "cliffs": False,
            "bottoms": False,
            "seam_geometry": False,
        },
    }


def validate_field_packet(packet: dict[str, Any], schema: dict[str, Any]) -> None:
    jsonschema.Draft7Validator.check_schema(schema)
    jsonschema.validate(instance=packet, schema=schema)
    if packet.get("contract_id") != FIELD_CONTRACT_ID or packet.get("patch_contract_id") != PATCH_CONTRACT_ID:
        raise ValueError("unsupported global-sample field contract")
    width, height = _positive_pair(packet.get("field_patch_dimensions"), "field_patch_dimensions")
    origin_x, origin_z = _integer_pair(packet.get("field_patch_origin"), "field_patch_origin")
    if packet.get("patch_cell_dimensions") != [CELL_COUNT, CELL_COUNT]:
        raise ValueError("field patch cell dimensions must be 16x16")
    if packet.get("field_cell_dimensions") != [width * CELL_COUNT, height * CELL_COUNT]:
        raise ValueError("field cell dimensions do not derive from patch dimensions")
    if packet.get("global_sample_dimensions") != [width * CELL_COUNT + 1, height * CELL_COUNT + 1]:
        raise ValueError("global sample dimensions do not derive from cell dimensions")
    expected_addresses = {
        (origin_x + x, origin_z + z) for z in range(height) for x in range(width)
    }
    records = packet.get("patches", [])
    addresses = [tuple(record["patch_address"]) for record in records]
    if len(addresses) != width * height or set(addresses) != expected_addresses:
        raise ValueError("patch registry must cover its rectangular address domain exactly once")
    materials = packet.get("materials", {})
    if any(record["material_id"] not in materials for record in records):
        raise ValueError("every patch material must resolve through the field registry")
    if any(material.get("logical_art_dimensions") != [CELL_COUNT, CELL_COUNT] for material in materials.values()):
        raise ValueError("every material must expose one 16x16 logical art region")
    if packet.get("canonical_field_topology") != _derived_topology(width, height):
        raise ValueError("canonical field topology counts are not derived correctly")


def generate_field_patch_packets(
    field_packet: dict[str, Any],
    elevation_at: Callable[[int, int], float],
) -> list[dict[str, Any]]:
    """Generate each patch independently from its address and shared elevation function."""
    packets: list[dict[str, Any]] = []
    materials = field_packet["materials"]
    for record in field_packet["patches"]:
        material_id = record["material_id"]
        material = materials[material_id]
        packets.append(
            build_patch_packet(
                patch_address=record["patch_address"],
                elevation_at=elevation_at,
                terrain_recipe=material_id,
                art_region={
                    "texture_path": material["texture_path"],
                    "pixel_origin": [0, 0],
                    "pixel_dimensions": [CELL_COUNT, CELL_COUNT],
                },
            )
        )
    return packets


def collect_unique_global_samples(
    patch_packets: Iterable[dict[str, Any]],
) -> dict[tuple[int, int], float]:
    """Merge local corners by global address and fail on any value disagreement."""
    unique: dict[tuple[int, int], float] = {}
    for packet in patch_packets:
        validate_patch_structure(packet)
        for local_z in range(SAMPLE_COUNT):
            for local_x in range(SAMPLE_COUNT):
                address = global_sample_address(packet["patch_address"], local_x, local_z)
                value = float(packet["elevation_samples"][sample_index(local_x, local_z)])
                if address in unique and unique[address] != value:
                    raise ValueError(f"conflicting elevations for global sample address {address}")
                unique[address] = value
    return unique


def validate_field_patch_set(
    field_packet: dict[str, Any],
    patch_packets: Iterable[dict[str, Any]],
) -> dict[tuple[int, int], float]:
    """Prove exact rectangular coverage and shared values for a field's patch set."""
    packets = list(patch_packets)
    expected_records = {
        tuple(record["patch_address"]): record["material_id"]
        for record in field_packet["patches"]
    }
    addresses = [tuple(packet.get("patch_address", [])) for packet in packets]
    if len(packets) != len(expected_records) or len(set(addresses)) != len(addresses):
        raise ValueError("field patch set must contain each declared patch exactly once")
    if set(addresses) != set(expected_records):
        raise ValueError("field patch set does not match the declared address domain")
    for packet in packets:
        validate_patch_structure(packet)
        address = tuple(packet["patch_address"])
        if packet.get("terrain_recipe") != expected_records[address]:
            raise ValueError(f"patch material does not match field registry at {address}")
    unique = collect_unique_global_samples(packets)
    expected_unique = field_packet["canonical_field_topology"]["unique_global_sample_count"]
    if len(unique) != expected_unique:
        raise ValueError("field patch set does not cover the declared global sample domain")
    return unique


def iter_neighbor_pairs(
    field_packet: dict[str, Any],
) -> Iterable[tuple[list[int], list[int], str]]:
    """Yield each east/west and north/south boundary exactly once."""
    width, height = _positive_pair(field_packet["field_patch_dimensions"], "field_patch_dimensions")
    origin_x, origin_z = _integer_pair(field_packet["field_patch_origin"], "field_patch_origin")
    addresses = {tuple(record["patch_address"]) for record in field_packet["patches"]}
    for offset_z in range(height):
        for offset_x in range(width):
            x, z = origin_x + offset_x, origin_z + offset_z
            if (x, z) not in addresses:
                raise ValueError(f"missing field patch address {(x, z)}")
            if offset_x + 1 < width:
                yield [x, z], [x + 1, z], "x"
            if offset_z + 1 < height:
                yield [x, z], [x, z + 1], "z"
