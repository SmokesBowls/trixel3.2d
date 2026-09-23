"""Assemble the recipe-pixel-binding proof as a real, inspectable .blend
scene: the BEFORE (flat per-cell Kd color, the courtyard hub's current
appearance) and AFTER (real per-cell recipe-rendered pixel tiles, bound
via UV into one shared atlas) objects, placed side by side so the ONLY
visible difference is whether a real pixel surface is bound to each cell
-- the mesh underneath is identical (proven by the gate, not just by eye).

Run with:

    python3 tools/build_recipe_bound_hub_proof.py
    blender --background --python tools/build_recipe_bound_hub_proof_blend.py
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
PROOF_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "recipe_bound_hub"
OUT_BLEND = REPO_ROOT / "fixtures" / "trixel_recipe_bound_hub_proof.blend"
OUT_RENDER = PROOF_DIR / "hub_before_after_comparison.png"

MAIN_COLLECTION = "TRIXEL_RECIPE_BOUND_HUB_PROOF"
GAP_X = 14.0  # hub is 12 units wide; 14 leaves a clean 2-unit gap


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


def import_piece(obj_path: Path, display_name: str, collection: bpy.types.Collection, offset_x: float) -> bpy.types.Object:
    before = set(bpy.data.objects.keys())
    bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis="Y", up_axis="Z")
    new_names = set(bpy.data.objects.keys()) - before
    if len(new_names) != 1:
        raise RuntimeError(f"expected exactly one new object importing {obj_path}, got {new_names}")
    obj = bpy.data.objects[next(iter(new_names))]
    obj.name = display_name
    obj.data.name = display_name + "_mesh"
    obj.location.x += offset_x
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
    key_obj.location = (20.0, 30.0, 15.0)
    look_at(key_obj, target)

    fill_data = bpy.data.lights.new(name="Light_Fill", type="SUN")
    fill_data.energy = 0.6
    fill_obj = bpy.data.objects.new(name="Light_Fill", object_data=fill_data)
    collection.objects.link(fill_obj)
    fill_obj.location = (-15.0, 12.0, -15.0)
    look_at(fill_obj, target)

    world = bpy.data.worlds.new("Proof_Sky") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.6, 0.6, 0.62, 1.0)
            bg.inputs[1].default_value = 1.0

    camera_data = bpy.data.cameras.new("Camera_BeforeAfter")
    camera_data.type = "ORTHO"
    # Combined scene spans X:[0, GAP_X + 12] = 26 world units; ortho_scale
    # governs the HORIZONTAL extent here (sensor_fit=AUTO, resolution_x >
    # resolution_y), so it must comfortably exceed 26, not just the width
    # of one hub -- 24 clipped the second hub down to a sliver.
    camera_data.ortho_scale = 34.0
    camera_obj = bpy.data.objects.new("Camera_BeforeAfter", camera_data)
    collection.objects.link(camera_obj)
    camera_obj.location = target + Vector((0.0, 24.0, 0.001))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj


def main() -> int:
    before_obj = PROOF_DIR / "hub_before_flat_color.obj"
    after_obj = PROOF_DIR / "hub_after_recipe_pixels.obj"
    if not before_obj.exists() or not after_obj.exists():
        raise FileNotFoundError("run tools/build_recipe_bound_hub_proof.py first")

    clear_everything()
    main_collection = get_or_create_collection(MAIN_COLLECTION)

    import_piece(before_obj, "Hub_Before_FlatColor", main_collection, offset_x=0.0)
    import_piece(after_obj, "Hub_After_RecipePixels", main_collection, offset_x=GAP_X)
    force_closest_interpolation()

    target = Vector(((GAP_X + 12.0) / 2.0, 0.0, 6.0))
    add_lighting_and_camera(main_collection, target)

    bpy.ops.file.pack_all()
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print(f"saved {OUT_BLEND}")

    scene = bpy.context.scene
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT_RENDER)
    bpy.ops.render.render(write_still=True)
    print(f"saved {OUT_RENDER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
