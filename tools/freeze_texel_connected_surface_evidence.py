"""Freeze the HEIGHT_FIELD_CONNECTED_SURFACE policy as a permanent, addressable
tool -- sibling freeze to the existing 2026-07-18 ingress/CELL_EXTRUSION
manifest, which this repo never wrote for CONNECTED_SURFACE.

Adds exactly two things on top of the existing, untouched
render_texel_connected_surface_evidence.py: a golden .obj mesh (so the exact
geometry, not just a render, is preserved) and an evidence manifest declaring
this policy frozen -- same shape as texel_ingress_evidence_manifest.json.

Does not regenerate or alter texel_connected_surface_built_response.json,
texel_connected_surface_render.png, or texel_lattice_vs_connected.png --
those are read as already-accepted bytes, exactly as the existing ingress
manifest treats its own evidence images.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "fixtures" / "texel"

BUILT_RESPONSE_PATH = OUT_DIR / "texel_connected_surface_built_response.json"
RENDER_PATH = OUT_DIR / "texel_connected_surface_render.png"
COMPARISON_PATH = OUT_DIR / "texel_lattice_vs_connected.png"
OBJ_PATH = OUT_DIR / "texel_connected_surface_geometry.obj"
MANIFEST_PATH = OUT_DIR / "texel_connected_surface_evidence_manifest.json"

PINNED_SOURCE_SHA256 = "ab5cb28b956f418272dacb367395da958671faf7c6e096e2d5b2cf6fa4363d51"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_obj(built: dict, path: Path) -> None:
    positions = built["geometry"]["positions"]
    indices = built["geometry"]["indices"]
    colors = built["geometry"]["colors"]
    with path.open("w") as f:
        for (x, y, z), (r, g, b, a) in zip(positions, colors):
            f.write(f"v {x} {y} {z} {r} {g} {b}\n")
        for i in range(0, len(indices), 3):
            a_i, b_i, c_i = indices[i] + 1, indices[i + 1] + 1, indices[i + 2] + 1
            f.write(f"f {a_i} {b_i} {c_i}\n")


def main() -> None:
    built = json.loads(BUILT_RESPONSE_PATH.read_text(encoding="utf-8"))
    assert built.get("status") == "BUILT", built.get("errors")
    assert built.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE"

    if OBJ_PATH.exists():
        print(f"{OBJ_PATH} already exists -- leaving it untouched (frozen evidence is not regenerated)")
    else:
        write_obj(built, OBJ_PATH)
        print(f"wrote {OBJ_PATH}")

    manifest = {
        "manifest_contract": "texel_connected_surface_evidence_manifest.v1",
        "milestone": (
            "Second addressable surface policy over the same pinned Texel source "
            "as texel_ingress_evidence_manifest.json: HEIGHT_FIELD_CONNECTED_SURFACE "
            "/ SHARED_EDGE_STITCHED, frozen beside -- not replacing -- "
            "HEIGHT_FIELD_CELL_EXTRUSION / ALL_FACES_INDEPENDENT."
        ),
        "visually_accepted": "2026-09-20",
        "source_fixture": {
            "file": "texel_grass_tile_16x16.png",
            "sha256": PINNED_SOURCE_SHA256,
            "pin": "texel_grass_tile_16x16.pin.json",
        },
        "construction": {
            "request_id": built["request_id"],
            "surface_id": built["surface_id"],
            "topology_policy": "HEIGHT_FIELD_CONNECTED_SURFACE",
            "gap_fill_mode": "CONNECTED_SLAB",
            "gap_fill_adjacency_policy": "SHARED_EDGE_STITCHED",
            "built_response": "texel_connected_surface_built_response.json",
            "built_response_sha256": sha256_of(BUILT_RESPONSE_PATH),
            "golden_geometry_obj": "texel_connected_surface_geometry.obj",
            "golden_geometry_obj_sha256": sha256_of(OBJ_PATH),
            "note": (
                "This is a distinct, permanently addressable construction policy, "
                "not an improved replacement for HEIGHT_FIELD_CELL_EXTRUSION -- both "
                "remain independently callable by declaring construction.topology_policy "
                "in the request. A future improvement is a new topology_policy/gap_fill "
                "name, never an edit to this one or to ALL_FACES_INDEPENDENT."
            ),
        },
        "evidence_images": {
            "stitched_render": {
                "file": "texel_connected_surface_render.png",
                "sha256": sha256_of(RENDER_PATH),
            },
            "lattice_vs_connected_comparison": {
                "file": "texel_lattice_vs_connected.png",
                "sha256": sha256_of(COMPARISON_PATH),
            },
        },
        "regeneration": (
            "tools/render_texel_connected_surface_evidence.py regenerates the "
            "built_response/render/comparison from the pinned source and the "
            "accepted lattice bytes; tools/freeze_texel_connected_surface_evidence.py "
            "(this file) adds only the golden .obj and this manifest on top, without "
            "altering either."
        ),
        "closure": (
            "These exact files and hashes are the accepted evidence for "
            "HEIGHT_FIELD_CONNECTED_SURFACE. Do not rerender to replace them; a future "
            "improvement is a new topology_policy/gap_fill name, not an edit to this one."
        ),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
