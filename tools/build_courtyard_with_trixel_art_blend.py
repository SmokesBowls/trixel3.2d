"""Assemble the courtyard-with-real-art scene as an inspectable .blend and
render it, mirroring tools/build_trixel_capability_courtyard_blend.py's
own conventions exactly (forward_axis=Y, up_axis=Z import, Closest
interpolation, packed textures, angled-overhead strategy camera).

Run with:

    python3 tools/bind_trixel_art_to_courtyard.py
    blender --background --python tools/build_courtyard_with_trixel_art_blend.py
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTS_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "courtyard_with_trixel_art"
OUT_BLEND = REPO_ROOT / "fixtures" / "trixel_capability_courtyard_with_art.blend"
OUT_RENDER = PARTS_DIR / "courtyard_with_art_render.png"

MAIN_COLLECTION = "TRIXEL_CAPABILITY_COURTYARD_WITH_ART"

PIECES = [
    "hub", "north_ramp", "north_terrace", "south_ramp", "south_terrace",
    "east_ramp", "east_terrace", "west_wall", "floor_demo", "wall_demo", "pillar",
]


def clear_everything() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for block_collection in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.lights, bpy.data.cameras):
        for block in list(block_collection):
            if block.users == 0:
                block_collection.remove(block)


def get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def force_closest_interpolation() -> None:
    for material in bpy.data.materials:
        if material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"


def import_piece(stem: str, collection: bpy.types.Collection) -> bpy.types.Object:
    obj_path = PARTS_DIR / f"{stem}.obj"
    before = set(bpy.data.objects.keys())
    bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis="Y", up_axis="Z")
    new_names = set(bpy.data.objects.keys()) - before
    if len(new_names) != 1:
        raise RuntimeError(f"expected exactly one new object importing {obj_path}, got {new_names}")
    obj = bpy.data.objects[next(iter(new_names))]
    obj.name = stem
    obj.data.name = stem + "_mesh"
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def add_lighting_and_camera(collection: bpy.types.Collection, target: Vector) -> None:
    def look_at(obj: bpy.types.Object, at: Vector) -> None:
        direction = at - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    key_data = bpy.data.lights.new(name="Light_Key", type="SUN")
    key_data.energy = 3.0
    key_obj = bpy.data.objects.new(name="Light_Key", object_data=key_data)
    collection.objects.link(key_obj)
    key_obj.location = (30.0, 45.0, 20.0)
    look_at(key_obj, target)

    fill_data = bpy.data.lights.new(name="Light_Fill", type="SUN")
    fill_data.energy = 0.7
    fill_obj = bpy.data.objects.new(name="Light_Fill", object_data=fill_data)
    collection.objects.link(fill_obj)
    fill_obj.location = (-25.0, 20.0, -20.0)
    look_at(fill_obj, target)

    world = bpy.data.worlds.new("Courtyard_Art_Sky") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1.0)
            bg.inputs[1].default_value = 0.9

    camera_data = bpy.data.cameras.new("Camera_Inspection")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 42.0
    camera_obj = bpy.data.objects.new("Camera_Inspection", camera_data)
    collection.objects.link(camera_obj)
    camera_obj.location = target + Vector((14.0, 46.0, 18.0))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj


def main() -> int:
    for stem in PIECES:
        if not (PARTS_DIR / f"{stem}.obj").exists():
            raise FileNotFoundError(f"missing {stem}.obj -- run tools/bind_trixel_art_to_courtyard.py first")

    clear_everything()
    main_collection = get_or_create_collection(MAIN_COLLECTION)
    for stem in PIECES:
        import_piece(stem, main_collection)
    force_closest_interpolation()

    target = Vector((2.0, 0.0, 1.0))
    add_lighting_and_camera(main_collection, target)

    bpy.ops.file.pack_all()
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print(f"saved {OUT_BLEND}")

    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1440
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT_RENDER)
    bpy.ops.render.render(write_still=True)
    print(f"saved {OUT_RENDER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
