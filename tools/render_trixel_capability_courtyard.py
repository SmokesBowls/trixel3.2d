"""Blender evidence viewer for the Trixel Capability Courtyard.

Run with:

    blender --background --python tools/render_trixel_capability_courtyard.py -- --clean
    blender --background --python tools/render_trixel_capability_courtyard.py -- --debug

Blender is only the evidence viewer -- the geometry itself comes from
tools/export_trixel_capability_courtyard.py and is verified by
trixel/gates/gate_pixel_geometry_capability_courtyard_v1.py, both run on
plain Python before this script exists to be invoked.

--clean renders the courtyard as a finished-looking environment: real
recipe-rendered textures (grass/dirt/stone/cracked-rock) plus the
diagnostic strip on the pillar, two lights (key + fill), a soft sky
background. No real-time player controller or collision exists in this
toolchain (deliberately -- see the proof doc for why), so this is the
closest approximation available inside trixel3.2d: a composed, lit,
angled-overhead "strategy game" style establishing shot rather than a
walkable first-person view, chosen because the courtyard's ~32x28 unit
footprint cannot be read from a single ground-level shot.

--debug renders the same geometry with wireframe forced on every mesh and
text labels marking each attachment seam, the cylinder seam, and each
terrace's world Y -- an approximation of the "F1 toggle" idea using two
renders instead of a live toggle.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
SCENE_OBJ = FIXTURES / "trixel_capability_courtyard.obj"
CLEAN_OUT = FIXTURES / "trixel_capability_courtyard_clean.png"
DEBUG_OUT = FIXTURES / "trixel_capability_courtyard_debug.png"

# (text, world position) -- kept short since Blender's default font has no
# guaranteed line-wrap in this pipeline.
DEBUG_LABELS = [
    ("HUB 12x12 built-once", (0.0, 0.6, 0.0)),
    ("N RAMP rise=3 run=4", (2.3, 1.8, -8.0)),
    ("WORLD Y 3.0", (-3.8, 3.3, -12.0)),
    ("S RAMP rise=2.5 run=4.33", (2.3, 1.5, 8.0)),
    ("WORLD Y 2.5", (-3.8, 2.8, 12.3)),
    ("E RAMP same impl rot=0", (7.6, 1.8, 2.3)),
    ("WEST WALL fold+rigid180", (-6.8, 0.5, 6.5)),
    ("FLOOR/WALL same footprint", (-9.5, 1.2, 7.5)),
    ("PILLAR seam ->", (17.0, 4.4, -6.0)),
    ("CONTACT EXHIBIT dist=0", (-13.0, 3.3, 10.3)),
    ("SEAM", (0.0, 0.4, -6.5)),
    ("SEAM", (0.0, 0.4, 6.5)),
    ("SEAM", (6.5, 0.4, 0.0)),
]


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_collection in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves):
        for block in list(block_collection):
            if block.users == 0:
                block_collection.remove(block)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def force_closest_interpolation() -> None:
    for material in bpy.data.materials:
        if material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"


def add_label(text: str, position: tuple[float, float, float]) -> None:
    curve_data = bpy.data.curves.new(name=f"label_{text[:12]}", type="FONT")
    curve_data.body = text
    curve_data.size = 0.9
    curve_data.align_x = "CENTER"
    label_obj = bpy.data.objects.new(name=f"label_{text[:12]}", object_data=curve_data)
    bpy.context.collection.objects.link(label_obj)
    label_obj.location = position
    label_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))  # face up, readable from the overview camera


def add_wireframe() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        modifier = obj.modifiers.new(name="wire", type="WIREFRAME")
        modifier.thickness = 0.015
        modifier.use_replace = False


def main() -> int:
    debug = "--debug" in sys.argv

    if not SCENE_OBJ.exists():
        raise FileNotFoundError(f"missing {SCENE_OBJ} -- run tools/export_trixel_capability_courtyard.py first")

    clear_scene()
    bpy.ops.wm.obj_import(filepath=str(SCENE_OBJ), forward_axis="Y", up_axis="Z")
    force_closest_interpolation()

    if debug:
        for text, pos in DEBUG_LABELS:
            add_label(text, pos)
        add_wireframe()

    # Scene bounding box is roughly X:[-14,18], Z:[-14,14] -- an angled
    # overhead "strategy game" shot centered a little west of the hub so
    # the whole layout (including the pillar and west-side exhibits) fits.
    target = Vector((2.0, 0.0, 1.0))

    key_light = bpy.data.lights.new(name="key", type="SUN")
    key_light.energy = 3.0
    key_light.angle = math.radians(2.0)
    key_obj = bpy.data.objects.new(name="key", object_data=key_light)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (30.0, 45.0, 20.0)
    look_at(key_obj, target)

    fill_light = bpy.data.lights.new(name="fill", type="SUN")
    fill_light.energy = 0.7
    fill_obj = bpy.data.objects.new(name="fill", object_data=fill_light)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-25.0, 20.0, -20.0)
    look_at(fill_obj, target)

    world = bpy.data.worlds.new("courtyard_sky") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1.0)
            bg.inputs[1].default_value = 0.9

    camera_data = bpy.data.cameras.new("overview_camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 42.0
    camera_obj = bpy.data.objects.new("overview_camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)
    # Angled-overhead: mostly-Y offset (looking down) with a modest X/Z tilt
    # for depth, matching the framing already proven to read cleanly.
    camera_obj.location = target + Vector((14.0, 46.0, 18.0))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj

    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1440
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(DEBUG_OUT if debug else CLEAN_OUT)

    bpy.ops.render.render(write_still=True)
    print(f"wrote {scene.render.filepath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
