"""Assemble the Trixel Capability Courtyard as a real, inspectable .blend
scene -- not PNG renders.

Run with:

    blender --background --python tools/build_trixel_capability_courtyard_blend.py

This imports the per-piece OBJs written by
tools/export_trixel_capability_courtyard.py's export_pieces() (each piece
its own file, so each becomes its own identifiable Blender object -- never
one fused mesh, never a manually recreated substitute), organizes them
into a "TRIXEL_CAPABILITY_COURTYARD" collection with sensible names, adds
lighting and an inspection camera, builds a separate "TRIXEL_DEBUG_OVERLAY"
collection (wireframe duplicates, seam/contact markers, ramp-local axes,
terrace world-height labels) that can be shown or hidden as one unit
without touching the clean geometry, packs every texture into the file so
it is one self-contained artifact, and saves to
fixtures/trixel_capability_courtyard.blend.

No Blender deformer is used to fake any Trixel geometry -- every mesh
comes directly from the frozen embedding functions via the OBJ files; the
only Blender-side operations here are import, rename, collection
placement, and (for the debug overlay only) a non-destructive Wireframe
modifier for visualization.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTS_DIR = REPO_ROOT / "fixtures" / "pixel_geometry" / "courtyard_parts"
OUT_BLEND = REPO_ROOT / "fixtures" / "trixel_capability_courtyard.blend"

MAIN_COLLECTION = "TRIXEL_CAPABILITY_COURTYARD"
DEBUG_COLLECTION = "TRIXEL_DEBUG_OVERLAY"

# piece file stem -> (display object name, is terrain-like for wireframe overlay)
PIECES = [
    ("hub", "Hub_CentralTerrain_12x12", True),
    ("north_ramp", "NorthRamp_DeclaredAngle", False),
    ("north_terrace", "NorthTerrace_WorldY3", True),
    ("south_ramp", "SouthRamp_FractionalRise", False),
    ("south_terrace", "SouthTerrace_WorldY2_5", True),
    ("east_ramp", "EastRamp_RotatedInstance", False),
    ("east_terrace", "EastTerrace_WorldY3", True),
    ("west_wall", "WestWall_FoldedRetaining", False),
    ("floor_demo", "RigidDemo_Floor", False),
    ("wall_demo", "RigidDemo_Wall", False),
    ("pillar", "Pillar_ClosedCylindricalWrap", False),
    ("exhibit_a", "ContactExhibit_StripA", False),
    ("exhibit_b", "ContactExhibit_StripB", False),
]

SEAM_MARKERS = [
    ("Seam_NorthRamp_Hub", (0.0, 0.0, -6.0)),
    ("Seam_NorthRamp_Terrace", (0.0, 3.0, -10.0)),
    ("Seam_SouthRamp_Hub", (0.0, 0.0, 6.0)),
    ("Seam_SouthRamp_Terrace", (0.0, 2.5, 10.330127)),
    ("Seam_EastRamp_Hub", (6.0, 0.0, 0.0)),
    ("Seam_EastRamp_Terrace", (10.0, 3.0, 0.0)),
    ("Seam_CylinderClosure", (17.0, 2.0, -6.0)),
    ("Seam_ExactContact_ZeroAdjacency", (-14.0, 0.0, 11.0)),
]

RAMP_AXES = [
    ("RampAxes_North", (0.0, 0.0, -6.0), 90.0),
    ("RampAxes_South", (0.0, 0.0, 6.0), 270.0),
    ("RampAxes_East", (6.0, 0.0, 0.0), 0.0),
]

WORLD_Y_LABELS = [
    ("WorldY_North_3_0", "WORLD Y 3.0", (-4.0, 3.0, -12.0)),
    ("WorldY_South_2_5", "WORLD Y 2.5", (-4.0, 2.5, 12.3)),
    ("WorldY_East_3_0", "WORLD Y 3.0", (10.0, 3.0, -4.5)),
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


def get_or_create_collection(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    collection = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(collection)
    return collection


def force_closest_interpolation() -> None:
    for material in bpy.data.materials:
        if material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"


def import_piece(stem: str, display_name: str, collection: bpy.types.Collection) -> bpy.types.Object:
    obj_path = PARTS_DIR / f"{stem}.obj"
    if not obj_path.exists():
        raise FileNotFoundError(f"missing {obj_path} -- run tools/export_trixel_capability_courtyard.py first")
    before = set(bpy.data.objects.keys())
    bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis="Y", up_axis="Z")
    new_names = set(bpy.data.objects.keys()) - before
    if len(new_names) != 1:
        raise RuntimeError(f"expected exactly one new object importing {obj_path}, got {new_names}")
    obj = bpy.data.objects[next(iter(new_names))]
    obj.name = display_name
    obj.data.name = display_name + "_mesh"
    # Move from whatever collection the importer linked it into, into ours.
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def build_main_geometry(main_collection: bpy.types.Collection) -> dict[str, bpy.types.Object]:
    imported: dict[str, bpy.types.Object] = {}
    for stem, display_name, _ in PIECES:
        imported[stem] = import_piece(stem, display_name, main_collection)
    return imported


def add_lighting(collection: bpy.types.Collection, target: Vector) -> None:
    def look_at(obj: bpy.types.Object, at: Vector) -> None:
        direction = at - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    key_data = bpy.data.lights.new(name="Light_Key", type="SUN")
    key_data.energy = 3.0
    key_data.angle = math.radians(2.0)
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

    world = bpy.data.worlds.new("Courtyard_Sky") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1.0)
            bg.inputs[1].default_value = 0.9


def add_inspection_camera(collection: bpy.types.Collection, target: Vector) -> bpy.types.Object:
    def look_at(obj: bpy.types.Object, at: Vector) -> None:
        direction = at - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("Camera_Inspection")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 42.0
    camera_obj = bpy.data.objects.new("Camera_Inspection", camera_data)
    collection.objects.link(camera_obj)
    camera_obj.location = target + Vector((14.0, 46.0, 18.0))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj
    return camera_obj


def add_debug_overlay(debug_collection: bpy.types.Collection, main_objects: dict[str, bpy.types.Object]) -> None:
    # Cell outlines: wireframe DUPLICATES of the terrain-like pieces,
    # non-destructive (Wireframe modifier only, source mesh untouched),
    # so hiding this collection leaves the clean geometry exactly as-is.
    for stem, display_name, is_terrain in PIECES:
        if not is_terrain:
            continue
        source = main_objects[stem]
        dup = source.copy()
        dup.data = source.data.copy()
        dup.name = f"Wireframe_{display_name}"
        modifier = dup.modifiers.new(name="cell_outline", type="WIREFRAME")
        modifier.thickness = 0.03
        modifier.use_replace = False
        debug_collection.objects.link(dup)

    # Seam / contact-point markers: small spheres at each declared
    # attachment edge, the cylinder's closure, and the exact-contact point.
    for name, pos in SEAM_MARKERS:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=pos, segments=8, ring_count=6)
        created = bpy.context.active_object
        created.name = name
        created.data.name = name + "_mesh"
        for coll in list(created.users_collection):
            coll.objects.unlink(created)
        debug_collection.objects.link(created)

    # Ramp-local axes: an Empty (plain axes) at each ramp's hinge/attachment
    # origin, rotated to match that ramp's declared world orientation.
    for name, pos, rotation_degrees in RAMP_AXES:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = "ARROWS"
        empty.empty_display_size = 1.5
        empty.location = pos
        empty.rotation_euler = (0.0, math.radians(rotation_degrees), 0.0)
        debug_collection.objects.link(empty)

    # Terrace world-height labels.
    for name, text, pos in WORLD_Y_LABELS:
        curve_data = bpy.data.curves.new(name=name + "_curve", type="FONT")
        curve_data.body = text
        curve_data.size = 0.9
        curve_data.align_x = "CENTER"
        obj = bpy.data.objects.new(name, curve_data)
        obj.location = pos
        obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))
        debug_collection.objects.link(obj)


def main() -> int:
    clear_everything()

    main_collection = get_or_create_collection(MAIN_COLLECTION)
    debug_collection = get_or_create_collection(DEBUG_COLLECTION)

    main_objects = build_main_geometry(main_collection)
    force_closest_interpolation()

    target = Vector((2.0, 0.0, 1.0))
    add_lighting(main_collection, target)
    add_inspection_camera(main_collection, target)

    add_debug_overlay(debug_collection, main_objects)
    debug_collection.hide_viewport = False
    debug_collection.hide_render = False

    # Self-contained artifact: pack every external image into the .blend.
    bpy.ops.file.pack_all()

    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print(f"saved {OUT_BLEND}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
