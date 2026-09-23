"""Visualize the corrected first 3.2d visual-object proof as two real,
inspectable .blend renders.

Render A (edit_propagation): the flat, hinge-folded, and ramp-raised
embodiments, all AFTER the single-trixel edit, side by side -- proving
the SAME edit made once on the editable TrixelSurface shows up identically
in every different 3D embodiment, without ever touching an image file.

Render B (before_after_density): the flat embodiment three times --
before the edit, after the edit, and after the edit plus an 8x8 -> 32x32
density change -- proving the edit is visible, and that density is a pure
raster-resolution choice independent of geometry.

Run with:

    python3 tools/build_trixel_surface_identity_proof.py
    blender --background --python tools/build_trixel_surface_identity_proof_blend.py
"""
from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "trixel_surface_identity_proof"
EMBODIMENTS_DIR = OUT_DIR / "embodiments"

OUT_BLEND = REPO_ROOT / "fixtures" / "trixel_surface_identity_proof.blend"
RENDER_A = OUT_DIR / "edit_propagation_across_embodiments.png"
RENDER_B = OUT_DIR / "before_after_and_density.png"

GAP = 10.0  # 8-unit-wide footprint; 10 leaves a clean gap


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


def add_lighting_and_camera(collection: bpy.types.Collection, target: Vector, ortho_scale: float, cam_name: str) -> None:
    def look_at(obj: bpy.types.Object, at: Vector) -> None:
        direction = at - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    key_data = bpy.data.lights.new(name=f"Light_Key_{cam_name}", type="SUN")
    key_data.energy = 3.0
    key_obj = bpy.data.objects.new(name=f"Light_Key_{cam_name}", object_data=key_data)
    collection.objects.link(key_obj)
    key_obj.location = target + Vector((10.0, 16.0, 8.0))
    look_at(key_obj, target)

    fill_data = bpy.data.lights.new(name=f"Light_Fill_{cam_name}", type="SUN")
    fill_data.energy = 0.6
    fill_obj = bpy.data.objects.new(name=f"Light_Fill_{cam_name}", object_data=fill_data)
    collection.objects.link(fill_obj)
    fill_obj.location = target + Vector((-8.0, 6.0, -8.0))
    look_at(fill_obj, target)

    world = bpy.data.worlds.new("Identity_Sky") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.6, 0.6, 0.62, 1.0)
            bg.inputs[1].default_value = 1.0

    camera_data = bpy.data.cameras.new(cam_name)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ortho_scale
    camera_obj = bpy.data.objects.new(cam_name, camera_data)
    collection.objects.link(camera_obj)
    camera_obj.location = target + Vector((0.0, 20.0, 0.001))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj


def render_scene(out_path: Path) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 700
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"saved {out_path}")


def build_render_a() -> None:
    clear_everything()
    collection = get_or_create_collection("EDIT_PROPAGATION_ACROSS_EMBODIMENTS")
    after_dir = EMBODIMENTS_DIR / "after_edit"
    import_piece(after_dir / "flat.obj", "Flat_AfterEdit", collection, offset_x=0.0)
    import_piece(after_dir / "hinge.obj", "Hinge_AfterEdit", collection, offset_x=GAP)
    import_piece(after_dir / "ramp.obj", "Ramp_AfterEdit", collection, offset_x=2 * GAP)
    force_closest_interpolation()

    target = Vector((GAP, 1.5, 4.0))
    add_lighting_and_camera(collection, target, ortho_scale=34.0, cam_name="Camera_EditPropagation")
    render_scene(RENDER_A)


def build_render_b() -> None:
    clear_everything()
    collection = get_or_create_collection("BEFORE_AFTER_AND_DENSITY")
    import_piece(EMBODIMENTS_DIR / "before_edit" / "flat.obj", "Flat_BeforeEdit", collection, offset_x=0.0)
    import_piece(EMBODIMENTS_DIR / "after_edit" / "flat.obj", "Flat_AfterEdit", collection, offset_x=GAP)
    import_piece(EMBODIMENTS_DIR / "after_density32" / "flat.obj", "Flat_AfterEdit_Density32", collection, offset_x=2 * GAP)
    force_closest_interpolation()

    target = Vector((GAP, 0.0, 4.0))
    add_lighting_and_camera(collection, target, ortho_scale=30.0, cam_name="Camera_BeforeAfterDensity")
    render_scene(RENDER_B)


def main() -> int:
    for stage in ("before_edit", "after_edit", "after_density32"):
        for name in ("flat", "hinge", "ramp"):
            path = EMBODIMENTS_DIR / stage / f"{name}.obj"
            if not path.exists():
                raise FileNotFoundError(f"missing {path} -- run tools/build_trixel_surface_identity_proof.py first")

    build_render_a()
    build_render_b()

    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print(f"saved {OUT_BLEND}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
