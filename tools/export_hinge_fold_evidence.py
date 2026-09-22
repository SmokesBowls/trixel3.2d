"""Export the Trial 2.5 hinge-fold result as a real .obj for Blender
inspection. Fixed side (columns A,B) and folded side (columns C,D) are
written as separate named groups with distinct vertex colors, so the fold
itself -- not just the gate's TRUE/FALSE lines -- is directly visible.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from trixel.pixel_geometry.addressing_v1 import build_footprint, cell_addresses, corner_index
from trixel.pixel_geometry.compiler_v1 import compile_footprint
from trixel.pixel_geometry.embedding_v1 import embed_hard_90_degree_hinge_fold
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_HARD_90_DEGREE_HINGE_FOLD

OUT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "fixtures" / "pixel_geometry" / "hinge_fold_4x4.obj"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

HINGE_X = 2
FIXED_COLOR = (0.85, 0.35, 0.35)   # columns A, B
FOLDED_COLOR = (0.35, 0.55, 0.85)  # columns C, D

labels = [["A", "B", "C", "D"], ["E", "F", "G", "H"], ["I", "J", "K", "L"], ["M", "N", "O", "P"]]
footprint = build_footprint(4, 4, labels)
positions = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_X)
compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD)

width = footprint["width"]
with OUT_PATH.open("w") as f:
    # Write ALL vertices once (both groups reference the same vertex pool by index).
    for (px, pr), pos in sorted(positions.items(), key=lambda item: corner_index(item[0][0], item[0][1], width)):
        color = FIXED_COLOR if px <= HINGE_X else FOLDED_COLOR
        f.write(f"v {pos[0]} {pos[1]} {pos[2]} {color[0]} {color[1]} {color[2]}\n")

    fixed_faces = []
    folded_faces = []
    for prov in compiled["primitive_provenance"]:
        cx, cr = prov["cell_address"]
        start = prov["primitive_start"] * 3
        tri_a = compiled["indices"][start : start + 3]
        tri_b = compiled["indices"][start + 3 : start + 6]
        target = fixed_faces if cx < HINGE_X else folded_faces
        target.append(tuple(i + 1 for i in tri_a))
        target.append(tuple(i + 1 for i in tri_b))

    f.write("g fixed_side_A_B\n")
    for a, b, c in fixed_faces:
        f.write(f"f {a} {b} {c}\n")
    f.write("g folded_side_C_D\n")
    for a, b, c in folded_faces:
        f.write(f"f {a} {b} {c}\n")

print(f"wrote {OUT_PATH}")
print(f"fixed_side triangles: {len(fixed_faces)}, folded_side triangles: {len(folded_faces)}")
print("labels: A B | C D  /  E F | G H  /  I J | K L  /  M N | O P  -- hinge between columns 1 and 2")
