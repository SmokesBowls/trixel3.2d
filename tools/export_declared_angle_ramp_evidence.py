#!/usr/bin/env python3
"""Export the declared-angle ramp specimen as a real .obj, reusing the
same 16x16 diagnostic artwork, .mtl, and UV addresses as the fold-vs-
stretch and cylinder proofs -- same source pixels, same UV addresses,
same cell metric, only the embedding differs.

The angle used is not guessed: it is the output of
ramp_geometry_v1.solve_ramp_run_and_angle(), computed for the same
worked example (8 cells beyond the hinge, required rise 5.0) proven by
gate_pixel_geometry_declared_angle_ramp_v1.py.

Writes:
    fixtures/pixel_geometry/pixel_art_declared_angle_ramp_16x16.obj
    fixtures/pixel_geometry/pixel_art_declared_angle_ramp_manifest.json

Reuses (does not rewrite):
    fixtures/pixel_geometry/pixel_fold_diagnostic_16x16.png
    fixtures/pixel_geometry/pixel_art_fold_stretch.mtl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold
from trixel.pixel_geometry.ramp_geometry_v1 import solve_ramp_run_and_angle

FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
ART_PATH = FIXTURES / "pixel_fold_diagnostic_16x16.png"
MTL_PATH = FIXTURES / "pixel_art_fold_stretch.mtl"  # shared, not rewritten
RAMP_OBJ = FIXTURES / "pixel_art_declared_angle_ramp_16x16.obj"
MANIFEST_PATH = FIXTURES / "pixel_art_declared_angle_ramp_manifest.json"

SIZE = 16
HINGE_X = 8
FAR_SEGMENT_CELLS = SIZE - HINGE_X
REQUIRED_RISE = 5.0
MTL_NAME = "pixel_art_diagnostic"


def write_obj(
    path: Path,
    footprint: dict,
    positions: dict[tuple[int, int], tuple[float, float, float]],
    uv_map: dict[tuple[int, int], tuple[float, float]],
    compiled: dict,
    *,
    group_name: str,
) -> None:
    width = footprint["width"]
    ordered_addresses = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    vertex_index = {addr: i + 1 for i, addr in enumerate(ordered_addresses)}

    lines: list[str] = [f"mtllib {MTL_PATH.name}", f"o {group_name}"]
    for addr in ordered_addresses:
        x, y, z = positions[addr]
        lines.append(f"v {x} {y} {z}")
    for addr in ordered_addresses:
        u, v = uv_map[addr]
        lines.append(f"vt {u} {v}")

    lines.append(f"usemtl {MTL_NAME}")
    lines.append(f"g {group_name}")

    indices = compiled["indices"]
    for i in range(0, len(indices), 3):
        tri = indices[i : i + 3]
        face_addrs = [ordered_addresses[t] for t in tri]
        refs = " ".join(f"{vertex_index[a]}/{vertex_index[a]}" for a in face_addrs)
        lines.append(f"f {refs}")

    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    if not ART_PATH.exists():
        print(f"missing {ART_PATH} -- run tools/generate_pixel_geometry_diagnostic_art.py first")
        return 1
    if not MTL_PATH.exists():
        print(f"missing {MTL_PATH} -- run tools/export_pixel_art_fold_stretch_evidence.py first")
        return 1

    art_image = Image.open(ART_PATH).convert("RGB")
    if art_image.size != (SIZE, SIZE):
        print(f"diagnostic art must be {SIZE}x{SIZE}, got {art_image.size}")
        return 1

    payload = [[art_image.getpixel((x, row)) for x in range(SIZE)] for row in range(SIZE)]
    footprint = build_footprint(SIZE, SIZE, payload)
    uv_map = footprint_corner_uvs(footprint)

    solved = solve_ramp_run_and_angle(FAR_SEGMENT_CELLS, REQUIRED_RISE)
    positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_X, angle_degrees=solved.angle_degrees)
    compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    write_obj(RAMP_OBJ, footprint, positions, uv_map, compiled, group_name="pixel_art_declared_angle_ramp")

    edges = edge_lengths(compiled)
    manifest = {
        "artwork": ART_PATH.name,
        "artwork_width": SIZE,
        "artwork_height": SIZE,
        "cell_metric": 1.0,
        "hinge_corner_x": HINGE_X,
        "far_segment_cells": FAR_SEGMENT_CELLS,
        "required_rise": REQUIRED_RISE,
        "solved": {
            "angle_degrees": solved.angle_degrees,
            "run": solved.run,
            "chain_length": solved.chain_length,
        },
        "ramp": {
            "obj": RAMP_OBJ.name,
            "max_edge_length": max(edges),
            "uv_changed": not uvs_are_identical(uv_map, footprint_corner_uvs(footprint)),
        },
        "mtl": MTL_PATH.name,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {RAMP_OBJ}")
    print(f"wrote {MANIFEST_PATH}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
