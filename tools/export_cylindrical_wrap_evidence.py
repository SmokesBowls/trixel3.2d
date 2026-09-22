#!/usr/bin/env python3
"""Export the closed cylindrical wrap specimen as a real .obj, reusing the
exact same 16x16 diagnostic artwork, .mtl, and UV addresses as the
fold-vs-stretch proof (tools/export_pixel_art_fold_stretch_evidence.py) --
same source pixels, same UV addresses, same cell metric, only the
embedding differs.

Writes:
    fixtures/pixel_geometry/pixel_art_cylinder_16x16.obj
    fixtures/pixel_geometry/pixel_art_cylindrical_wrap_manifest.json

Reuses (does not rewrite):
    fixtures/pixel_geometry/pixel_fold_diagnostic_16x16.png
    fixtures/pixel_geometry/pixel_art_fold_stretch.mtl
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.adjacency_v1 import closed_wrap_seam_adjacency
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import compile_closed_wrap_footprint
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_CYLINDRICAL_CLOSED_WRAP
from trixel.pixel_geometry.embedding_v1 import embed_cylindrical_closed_wrap

FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
ART_PATH = FIXTURES / "pixel_fold_diagnostic_16x16.png"
MTL_PATH = FIXTURES / "pixel_art_fold_stretch.mtl"  # shared with the fold-vs-stretch proof, not rewritten
CYLINDER_OBJ = FIXTURES / "pixel_art_cylinder_16x16.obj"
MANIFEST_PATH = FIXTURES / "pixel_art_cylindrical_wrap_manifest.json"

SIZE = 16
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

    positions = embed_cylindrical_closed_wrap(footprint)
    seam_adjacency = closed_wrap_seam_adjacency(footprint)
    compiled = compile_closed_wrap_footprint(
        footprint, positions, embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, seam_adjacency=seam_adjacency
    )
    write_obj(CYLINDER_OBJ, footprint, positions, uv_map, compiled, group_name="pixel_art_cylindrical_wrap")

    width = footprint["width"]

    def dist(a, b):
        ax, ay, az = positions[a]
        bx, by, bz = positions[b]
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5

    horizontal_edges = [
        dist((x, r), (x + 1, r)) for r in range(footprint["height"] + 1) for x in range(width)
    ]
    vertical_edges = [
        dist((x, r), (x, r + 1)) for x in range(width + 1) for r in range(footprint["height"])
    ]
    seam_gap = max(
        max(abs(a - b) for a, b in zip(positions[(0, row)], positions[(width, row)]))
        for row in range(footprint["height"] + 1)
    )

    manifest = {
        "artwork": ART_PATH.name,
        "artwork_width": SIZE,
        "artwork_height": SIZE,
        "cell_metric": 1.0,
        "columns": width,
        "angle_increment_degrees": 360.0 / width,
        "cylinder": {
            "obj": CYLINDER_OBJ.name,
            "radius": 1.0 / (2.0 * math.sin(math.pi / width)),
            "max_horizontal_edge_length": max(horizontal_edges),
            "max_vertical_edge_length": max(vertical_edges),
            "seam_position_gap": seam_gap,
            "uv_changed": not uvs_are_identical(uv_map, footprint_corner_uvs(footprint)),
            "seam_declared_neighbors": True,
        },
        "mtl": MTL_PATH.name,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {CYLINDER_OBJ}")
    print(f"wrote {MANIFEST_PATH}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
