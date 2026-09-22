#!/usr/bin/env python3
"""Sixth terrain-lane composition proof: close-proximity toxic ramps.

independent distant ramps          PROVEN, FROZEN (min separation 15.9 units)
shared-terrain hub                 PROVEN, FROZEN (one shared terrain artifact)
close-proximity toxic ramps        THIS PROOF
taper / topology mutation          later -- a different topology problem

Every prior composition proof made independence easy by keeping the
pieces apart. This one makes proximity actively misleading: ramp A and
ramp B are placed using EACH RAMP'S OWN DEFAULT, ALREADY-FROZEN placement
-- no artificial adversarial offset, no shift at all. That default
placement alone produces exact-position coincidences between the two
ramps' vertices (measured, not assumed), because both single-ramp proofs
independently anchor their near edge close to world origin. The two ramps
declare no relationship to each other whatsoever.

Same ramp geometry (8 cells, required rise 5.0), same attachment-
transform machinery (ramp_position_to_world, unmodified), same frozen
embedding. Only positioning is toxic: instead of separating scene B by a
large offset (as the independent multi-ramp proof did) or deriving a
shift from a shared hub (as the hub proof did), this proof applies NO
shift at all, letting the two ramps' own honest definitions collide.

The required result is not "they end up far apart" -- it is that even
though they are provably close (in fact, exactly coincident at several
points), nothing in the declared or compiled adjacency graphs ever
treats them as neighbors.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import corner_index
from trixel.pixel_geometry.adjacency_v1 import source_adjacency
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.terrain_ramp_integration_v1 import ramp_position_to_world

import export_terrain_ramp_integration_evidence as scene_a_tool
import export_terrain_ramp_rotated_orientation_evidence as scene_b_tool

FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
OUT_OBJ = FIXTURES / "ramp_close_proximity.obj"
OUT_MANIFEST = FIXTURES / "ramp_close_proximity_manifest.json"

RAMP_A_COLOR = [0.55, 0.35, 0.20, 1.0]  # brown -- ramp A
RAMP_B_COLOR = [0.20, 0.35, 0.55, 1.0]  # blue -- ramp B, so the two are visually distinct


def build_ramp_a() -> dict[str, Any]:
    """Ramp A, EXACTLY as the integer-rise control defines it -- same
    embedding call, same offsets, no shift at all."""
    footprint, positions, ramp_info = scene_a_tool.build_ramp()
    return {
        "footprint": footprint,
        "positions": positions,
        "ramp_info": ramp_info,
        "rotation_degrees": 90.0,
        "offset_kwargs": dict(path_x_offset=scene_a_tool.PATH_X_OFFSET, ramp_z_offset=scene_a_tool.ramp_z_offset()),
        "hinge_corner_x": scene_a_tool.HINGE_CORNER_X,
    }


def build_ramp_b() -> dict[str, Any]:
    """Ramp B, EXACTLY as the rotated-orientation proof defines it -- same
    embedding call, same offsets, no shift at all."""
    footprint, positions, ramp_info = scene_b_tool.build_ramp()
    return {
        "footprint": footprint,
        "positions": positions,
        "ramp_info": ramp_info,
        "rotation_degrees": 0.0,
        "offset_kwargs": dict(path_x_offset=scene_b_tool.RAMP_X_OFFSET, ramp_z_offset=scene_b_tool.PATH_Z_OFFSET),
        "hinge_corner_x": scene_b_tool.HINGE_CORNER_X,
    }


def world_points(ramp: dict[str, Any]) -> list[tuple[float, float, float]]:
    return [
        ramp_position_to_world(pos, rotation_degrees=ramp["rotation_degrees"], **ramp["offset_kwargs"])
        for pos in ramp["positions"].values()
    ]


def world_cell_centers(ramp: dict[str, Any], label: str) -> dict[tuple[str, int, int], tuple[float, float, float]]:
    """Cell-center world positions, keyed with a ramp label so ramp A's
    and ramp B's cell addresses (which numerically overlap -- both
    footprints are the same 9x2 shape) can never collide as dict keys."""
    footprint = ramp["footprint"]
    width, height = footprint["width"], footprint["height"]
    positions = ramp["positions"]
    centers: dict[tuple[str, int, int], tuple[float, float, float]] = {}
    for r in range(height):
        for x in range(width):
            corners = [positions[(x, r)], positions[(x + 1, r)], positions[(x, r + 1)], positions[(x + 1, r + 1)]]
            local_center = tuple(sum(c[i] for c in corners) / 4.0 for i in range(3))
            world_center = ramp_position_to_world(local_center, rotation_degrees=ramp["rotation_degrees"], **ramp["offset_kwargs"])
            centers[(label, x, r)] = world_center
    return centers


def declared_adjacency_labeled(ramp: dict[str, Any], label: str) -> dict[tuple[str, int, int], set[tuple[str, int, int]]]:
    """ramp's own source_adjacency(), relabeled with `label` so it can be
    combined with another ramp's without key collision. Never includes a
    cross-ramp entry -- there is no code path here that could add one."""
    raw = source_adjacency(ramp["footprint"])
    return {(label, x, r): {(label, nx, nr) for nx, nr in neighbors} for (x, r), neighbors in raw.items()}


def build_scene() -> dict[str, Any]:
    ramp_a = build_ramp_a()
    ramp_b = build_ramp_b()

    compiled_a = compile_footprint(ramp_a["footprint"], ramp_a["positions"], embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    compiled_b = compile_footprint(ramp_b["footprint"], ramp_b["positions"], embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)

    return {"ramp_a": ramp_a, "ramp_b": ramp_b, "compiled_a": compiled_a, "compiled_b": compiled_b}


def _write_obj(scene: dict[str, Any]) -> None:
    lines: list[str] = [f"mtllib {OUT_OBJ.with_suffix('.mtl').name}", "o ramp_close_proximity"]
    vertex_offset = 1
    face_blocks: list = []

    for key, material, compiled_key in (("ramp_a", "ramp_a_flat", "compiled_a"), ("ramp_b", "ramp_b_flat", "compiled_b")):
        ramp = scene[key]
        footprint = ramp["footprint"]
        width = footprint["width"]
        ordered = sorted(ramp["positions"], key=lambda addr: corner_index(addr[0], addr[1], width))
        index = {addr: vertex_offset + i for i, addr in enumerate(ordered)}
        for addr in ordered:
            world = ramp_position_to_world(ramp["positions"][addr], rotation_degrees=ramp["rotation_degrees"], **ramp["offset_kwargs"])
            lines.append(f"v {world[0]} {world[1]} {world[2]}")
        compiled = scene[compiled_key]
        for prov in compiled["primitive_provenance"]:
            if prov["cell_address"][0] < ramp["hinge_corner_x"]:
                continue
            start = prov["primitive_start"] * 3
            tri_a = compiled["indices"][start : start + 3]
            tri_b = compiled["indices"][start + 3 : start + 6]
            face_blocks.append((material, [tuple(index[ordered[i]] for i in tri_a), tuple(index[ordered[i]] for i in tri_b)]))
        vertex_offset += len(ordered)

    for material, tris in face_blocks:
        lines.append(f"usemtl {material}")
        for a, b, c in tris:
            lines.append(f"f {a} {b} {c}")

    OUT_OBJ.write_text("\n".join(lines) + "\n")

    mtl_lines = []
    for name, color in (("ramp_a_flat", RAMP_A_COLOR), ("ramp_b_flat", RAMP_B_COLOR)):
        mtl_lines.append(f"newmtl {name}")
        mtl_lines.append(f"Kd {color[0]} {color[1]} {color[2]}")
        mtl_lines.append("illum 1")
    OUT_OBJ.with_suffix(".mtl").write_text("\n".join(mtl_lines) + "\n")


def main() -> int:
    scene = build_scene()

    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_obj(scene)

    points_a, points_b = world_points(scene["ramp_a"]), world_points(scene["ramp_b"])
    min_distance = min(sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 for a in points_a for b in points_b)
    exact_coincidences = sum(
        1 for a in points_a for b in points_b if all(abs(a[i] - b[i]) <= 1e-9 for i in range(3))
    )

    manifest = {
        "ramp_a": {"far_segment_cells": scene_a_tool.FAR_SEGMENT_CELLS, "required_rise": scene_a_tool.REQUIRED_RISE, "rotation_degrees": 90.0},
        "ramp_b": {"far_segment_cells": scene_b_tool.FAR_SEGMENT_CELLS, "required_rise": scene_b_tool.REQUIRED_RISE, "rotation_degrees": 0.0},
        "min_distance_between_ramps": min_distance,
        "exact_coincidence_count": exact_coincidences,
        "obj": OUT_OBJ.name,
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {OUT_OBJ}")
    print(f"wrote {OUT_MANIFEST}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
