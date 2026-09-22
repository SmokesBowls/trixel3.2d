#!/usr/bin/env python3
"""Export the three pixel-art fold-vs-stretch specimens as real .obj files
with texture coordinates, sharing one .mtl and one PNG, plus a manifest of
what was actually measured on the generated geometry.

Specimens (all built from the SAME 16x16 diagnostic artwork and the SAME
intrinsic corner addresses -- only the embedding differs):

  A -- FLAT                     pixel_art_flat_16x16.obj
  B -- HARD FOLD (hinge x=8)    pixel_art_folded_16x16.obj
  C -- FORCED DIAGONAL STRETCH  pixel_art_diagonal_stretch_16x16.obj (toxic,
                                  local to this tool, never a production
                                  embedding)

Every OBJ writes both `v` and `vt` and faces reference both indices
(`f v/vt v/vt v/vt`) so a viewer actually samples the shared texture
instead of only seeing flat vertex colors.
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
from trixel.pixel_geometry.contracts_v1 import (
    EMBEDDING_FLAT,
    EMBEDDING_HARD_90_DEGREE_HINGE_FOLD,
)
from trixel.pixel_geometry.embedding_v1 import embed_flat, embed_hard_90_degree_hinge_fold

FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
ART_PATH = FIXTURES / "pixel_fold_diagnostic_16x16.png"
MTL_PATH = FIXTURES / "pixel_art_fold_stretch.mtl"
MANIFEST_PATH = FIXTURES / "pixel_art_fold_stretch_manifest.json"

FLAT_OBJ = FIXTURES / "pixel_art_flat_16x16.obj"
FOLDED_OBJ = FIXTURES / "pixel_art_folded_16x16.obj"
DIAGONAL_OBJ = FIXTURES / "pixel_art_diagonal_stretch_16x16.obj"

SIZE = 16
HINGE_X = 8
MTL_NAME = "pixel_art_diagnostic"


def write_mtl() -> None:
    MTL_PATH.write_text(
        "newmtl "
        + MTL_NAME
        + "\n"
        + "Ka 1.000 1.000 1.000\n"
        + "Kd 1.000 1.000 1.000\n"
        + "Ks 0.000 0.000 0.000\n"
        + "d 1.0\n"
        + "illum 1\n"
        + f"map_Kd {ART_PATH.name}\n"
    )


def write_obj(
    path: Path,
    footprint: dict,
    positions: dict[tuple[int, int], tuple[float, float, float]],
    uv_map: dict[tuple[int, int], tuple[float, float]],
    *,
    group_name: str,
) -> None:
    width = footprint["width"]
    ordered_addresses = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
    vertex_index = {addr: i + 1 for i, addr in enumerate(ordered_addresses)}  # OBJ indices are 1-based

    lines: list[str] = []
    lines.append(f"mtllib {MTL_PATH.name}")
    lines.append(f"o {group_name}")

    for addr in ordered_addresses:
        x, y, z = positions[addr]
        lines.append(f"v {x} {y} {z}")
    for addr in ordered_addresses:
        u, v = uv_map[addr]
        lines.append(f"vt {u} {v}")

    lines.append(f"usemtl {MTL_NAME}")
    lines.append(f"g {group_name}")

    compiled = compile_footprint(footprint, positions, embedding_id=group_name)
    indices = compiled["indices"]
    for i in range(0, len(indices), 3):
        tri = indices[i : i + 3]
        face_addrs = [ordered_addresses[t] for t in tri]
        refs = " ".join(f"{vertex_index[a]}/{vertex_index[a]}" for a in face_addrs)
        lines.append(f"f {refs}")

    path.write_text("\n".join(lines) + "\n")


def max_edge_length(footprint: dict, positions: dict, embedding_id: str) -> float:
    compiled = compile_footprint(footprint, positions, embedding_id=embedding_id)
    return max(edge_lengths(compiled))


def main() -> int:
    if not ART_PATH.exists():
        print(f"missing {ART_PATH} -- run tools/generate_pixel_geometry_diagnostic_art.py first")
        return 1

    art_image = Image.open(ART_PATH).convert("RGB")
    if art_image.size != (SIZE, SIZE):
        print(f"diagnostic art must be {SIZE}x{SIZE}, got {art_image.size}")
        return 1

    payload = [[art_image.getpixel((x, row)) for x in range(SIZE)] for row in range(SIZE)]
    footprint = build_footprint(SIZE, SIZE, payload)
    uv_map = footprint_corner_uvs(footprint)

    write_mtl()

    # A -- FLAT
    flat_positions = embed_flat(footprint)
    write_obj(FLAT_OBJ, footprint, flat_positions, uv_map, group_name="pixel_art_flat")
    flat_max_edge = max_edge_length(footprint, flat_positions, EMBEDDING_FLAT)

    # B -- HARD FOLD
    fold_positions = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_X)
    write_obj(FOLDED_OBJ, footprint, fold_positions, uv_map, group_name="pixel_art_hard_fold")
    fold_max_edge = max_edge_length(footprint, fold_positions, EMBEDDING_HARD_90_DEGREE_HINGE_FOLD)
    fold_uv_changed = not uvs_are_identical(uv_map, footprint_corner_uvs(footprint))

    # C -- FORCED DIAGONAL STRETCH (toxic, local to this tool only)
    diagonal_positions = {(x, r): (float(x), float(x), float(r)) for x, r in flat_positions}
    write_obj(DIAGONAL_OBJ, footprint, diagonal_positions, uv_map, group_name="pixel_art_diagonal_stretch")
    diagonal_edges = edge_lengths(
        compile_footprint(footprint, diagonal_positions, embedding_id="toxic_forced_diagonal_stretch")
    )
    diagonal_measured_edge = max(diagonal_edges)
    diagonal_uv_changed = not uvs_are_identical(uv_map, footprint_corner_uvs(footprint))

    manifest = {
        "artwork": ART_PATH.name,
        "artwork_width": SIZE,
        "artwork_height": SIZE,
        "cell_metric": 1.0,
        "flat": {
            "obj": FLAT_OBJ.name,
            "max_edge_length": flat_max_edge,
        },
        "hard_fold": {
            "obj": FOLDED_OBJ.name,
            "hinge_corner_x": HINGE_X,
            "max_edge_length": fold_max_edge,
            "uv_changed": fold_uv_changed,
        },
        "forced_diagonal": {
            "obj": DIAGONAL_OBJ.name,
            "run": 1.0,
            "rise": 1.0,
            "measured_edge_length": diagonal_measured_edge,
            "stretch_factor": diagonal_measured_edge / 1.0,
            "uv_changed": diagonal_uv_changed,
            "status": "TOXIC_CONTROL",
        },
        "mtl": MTL_PATH.name,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"wrote {FLAT_OBJ}")
    print(f"wrote {FOLDED_OBJ}")
    print(f"wrote {DIAGONAL_OBJ}")
    print(f"wrote {MTL_PATH}")
    print(f"wrote {MANIFEST_PATH}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
