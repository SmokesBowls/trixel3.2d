"""Blender evidence viewer for the pixel-art fold-vs-stretch proof.

Run with:

    blender --background --python tools/render_pixel_art_fold_stretch_evidence.py

Blender is ONLY the evidence viewer here -- it never decides anything
about fold vs. stretch (that is entirely trixel/gates/gate_pixel_geometry_
artwork_fold_v1.py, running on plain Python before this script is ever
invoked). This script:

  - imports the three OBJs exported by tools/export_pixel_art_fold_stretch_
    evidence.py exactly as they are on disk (their vt coordinates, their
    positions, their triangulation)
  - sets every image texture node to nearest-neighbor ("Closest")
    interpolation -- no Linear, Cubic, or Smart
  - adds NO subdivision, NO smoothing modifier, NO displacement, NO UV
    unwrap, NO automatic texture projection
  - arranges the three objects side by side (rigid translation only, for
    viewing convenience) and renders one comparison PNG

If any of the three OBJs, the shared .mtl, or the shared PNG are missing,
this script exits with an error rather than silently rendering nothing --
run tools/export_pixel_art_fold_stretch_evidence.py first.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"

SPECIMENS = [
    ("pixel_art_flat", FIXTURES / "pixel_art_flat_16x16.obj", 0.0, "FLAT"),
    ("pixel_art_hard_fold", FIXTURES / "pixel_art_folded_16x16.obj", 24.0, "HARD FOLD"),
    ("pixel_art_diagonal_stretch", FIXTURES / "pixel_art_diagonal_stretch_16x16.obj", 48.0, "FORCED STRETCH"),
]
OUT_PATH = FIXTURES / "pixel_art_fold_stretch_comparison.png"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_collection in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves):
        for block in list(block_collection):
            if block.users == 0:
                block_collection.remove(block)


def import_obj(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing {path} -- run tools/export_pixel_art_fold_stretch_evidence.py first")
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis="Y", up_axis="Z")


def force_closest_interpolation(obj: bpy.types.Object) -> None:
    for slot in obj.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"


def add_label(text: str, x: float) -> None:
    curve_data = bpy.data.curves.new(name=f"label_{text}", type="FONT")
    curve_data.body = text
    curve_data.size = 1.6
    label_obj = bpy.data.objects.new(name=f"label_{text}", object_data=curve_data)
    bpy.context.collection.objects.link(label_obj)
    label_obj.location = (x, -3.0, -2.5)
    label_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main() -> int:
    clear_scene()

    imported = []
    for expected_name, path, offset_x, label in SPECIMENS:
        before = set(bpy.data.objects.keys())
        import_obj(path)
        after = set(bpy.data.objects.keys())
        new_names = after - before
        if not new_names:
            raise RuntimeError(f"import of {path} produced no new objects")
        for name in new_names:
            obj = bpy.data.objects[name]
            obj.location.x += offset_x
            force_closest_interpolation(obj)
            imported.append(obj)
        add_label(label, offset_x + 6.0)

    target = Vector((32.0, 4.0, 8.0))  # roughly the center of the whole 3-specimen layout

    # Simple sun light, angled so the fold's out-of-plane face is lit too.
    light_data = bpy.data.lights.new(name="sun", type="SUN")
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new(name="sun", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = (40.0, -60.0, 70.0)
    look_at(light_obj, target)

    # World background: flat light gray so the diagnostic palette reads clearly.
    world = bpy.data.worlds.new("evidence_world") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.85, 0.85, 0.85, 1.0)

    # Camera: orthographic, viewed from a diagonal (isometric-style) angle
    # with components on all three axes so the hard fold's turn into Y is
    # actually visible (not edge-on) and every specimen fits in frame.
    camera_data = bpy.data.cameras.new("evidence_camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 90.0
    camera_obj = bpy.data.objects.new("evidence_camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = target + Vector((70.0, -85.0, 55.0))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj

    scene = bpy.context.scene
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 800
    scene.render.filepath = str(OUT_PATH)
    scene.render.image_settings.file_format = "PNG"

    bpy.ops.render.render(write_still=True)
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
