"""Blender evidence viewer for the first pixel_geometry / connected-
terrain integration: lower grass+dirt terrain, a declared-angle ramp,
upper grass+dirt terrain.

Run with:

    blender --background --python tools/render_terrain_ramp_integration_evidence.py

Blender is only the evidence viewer -- the proof itself is
trixel/gates/gate_pixel_geometry_terrain_ramp_integration_v1.py, run on
plain Python before this script exists to be invoked. Imports the single
combined OBJ written by tools/export_terrain_ramp_integration_evidence.py
exactly as it is on disk (flat Kd materials, no textures, no
subdivision/smoothing/displacement) and renders one plain view.
"""
from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
SCENE_OBJ = FIXTURES / "terrain_ramp_integration.obj"
OUT_PATH = FIXTURES / "terrain_ramp_integration_render.png"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_collection in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for block in list(block_collection):
            if block.users == 0:
                block_collection.remove(block)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main() -> int:
    if not SCENE_OBJ.exists():
        raise FileNotFoundError(f"missing {SCENE_OBJ} -- run tools/export_terrain_ramp_integration_evidence.py first")

    clear_scene()
    bpy.ops.wm.obj_import(filepath=str(SCENE_OBJ), forward_axis="Y", up_axis="Z")

    target = Vector((0.0, 2.25, -3.1))  # scene bounding-box center

    light_data = bpy.data.lights.new(name="sun", type="SUN")
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new(name="sun", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = (30.0, 40.0, 20.0)
    look_at(light_obj, target)

    world = bpy.data.worlds.new("evidence_world") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    if world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.75, 0.8, 0.85, 1.0)

    camera_data = bpy.data.cameras.new("evidence_camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 22.0
    camera_obj = bpy.data.objects.new("evidence_camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = target + Vector((25.0, 30.0, 20.0))
    look_at(camera_obj, target)
    bpy.context.scene.camera = camera_obj

    scene = bpy.context.scene
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT_PATH)
    scene.render.image_settings.file_format = "PNG"

    bpy.ops.render.render(write_still=True)
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
