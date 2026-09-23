"""Open the SAVED fixtures/trixel_capability_courtyard.blend fresh (not
the in-memory scene from the build script) and report on it -- collections,
objects, whether pieces are visible/correctly oriented, texture pack
status, and any external file dependencies.

Run with:

    blender --background --python tools/inspect_trixel_capability_courtyard_blend.py
"""
from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
BLEND_PATH = REPO_ROOT / "fixtures" / "trixel_capability_courtyard.blend"


def main() -> int:
    if not BLEND_PATH.exists():
        print(f"MISSING: {BLEND_PATH}")
        return 1

    bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

    print(f"=== {BLEND_PATH} ===")
    print()
    print("--- collections ---")
    for collection in bpy.data.collections:
        objs = sorted(o.name for o in collection.objects)
        print(f"{collection.name} ({len(objs)} objects, hide_viewport={collection.hide_viewport}, hide_render={collection.hide_render})")
        for name in objs:
            print(f"    {name}")
    print()

    print("--- per-object bounding boxes (world space) ---")
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        if obj.type != "MESH":
            print(f"{obj.name:40s} type={obj.type} location={tuple(round(c, 2) for c in obj.location)}")
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        zs = [c[2] for c in corners]
        print(
            f"{obj.name:40s} X:[{min(xs):.2f},{max(xs):.2f}] "
            f"Y:[{min(ys):.2f},{max(ys):.2f}] Z:[{min(zs):.2f},{max(zs):.2f}] "
            f"verts={len(obj.data.vertices)}"
        )
    print()

    print("--- images: packed vs external ---")
    for image in bpy.data.images:
        packed = image.packed_file is not None
        print(f"{image.name:40s} packed={packed} filepath={image.filepath!r} size={tuple(image.size)}")
    print()

    print("--- external file dependencies (unpacked only) ---")
    missing_or_external = [img for img in bpy.data.images if img.packed_file is None and img.filepath]
    if not missing_or_external:
        print("(none -- all images packed into the .blend)")
    else:
        for img in missing_or_external:
            abs_path = bpy.path.abspath(img.filepath)
            exists = Path(abs_path).exists()
            print(f"{img.name}: {img.filepath} -> {abs_path} (exists={exists})")
    print()

    print("--- active camera / scene ---")
    scene = bpy.context.scene
    print(f"active camera: {scene.camera.name if scene.camera else None}")
    print(f"world: {scene.world.name if scene.world else None}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
