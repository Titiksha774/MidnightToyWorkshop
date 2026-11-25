import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

import build_assets
import phase1_assets
import phase2_toys
import phase3_assets
import workshop_lib as w

OUT = os.path.join(w.BLENDER_DIR, "Showcase")


def camera(eye, target, lens):
    data = bpy.data.cameras.new("Showcase Camera")
    data.lens = lens
    data.clip_start = 0.02
    data.clip_end = 100
    cam = bpy.data.objects.new("Showcase Camera", data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def area_light(name, location, energy, size, colour=(1.0, 0.9, 0.78)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = energy
    light.size = size
    light.color = colour
    obj = bpy.data.objects.new(name, light)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def soft_world(strength=0.6):
    world = bpy.data.worlds.new("Showcase")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.32, 0.3, 0.29, 1)
    bg.inputs["Strength"].default_value = strength


def hide_ceiling():
    for obj in bpy.data.objects:
        if obj.name.startswith(("Ceiling", "Window_NightView")):
            obj.hide_render = True


def render_single(name):
    w.reset()
    root, _ = build_assets.BUILDERS[name]()
    w.studio(w.asset_objects(root), fstop=14.0)
    w.render_still(os.path.join(OUT, f"{name}.png"))


def render_room():
    w.reset()
    phase1_assets.build_workshop_room()
    hide_ceiling()
    soft_world(0.4)
    area_light("Top", (0, -0.2, 6.0), 900, 5.0)
    area_light("Side", (2.5, 3.5, 4.0), 250, 3.0, (0.8, 0.88, 1.0))
    camera((-2.6, 4.2, 6.4), (0.2, -0.6, 0.2), 20)
    w.render_still(os.path.join(OUT, "WorkshopRoom.png"), samples=160)


def render_workshop():
    hide_ceiling()
    area_light("Top", (0, -0.2, 6.0), 700, 5.0)
    shots = [("All_Assets_Workshop", (-2.6, 4.2, 6.4), (0.2, -0.6, 0.3), 20),
             ("All_Assets_Workshop_2", (2.9, -4.9, 5.6), (-0.2, 0.3, 0.4), 20)]
    for name, eye, target, lens in shots:
        camera(eye, target, lens)
        w.render_still(os.path.join(OUT, f"{name}.png"), samples=192)


def place(root, x, y, z=0.0, yaw=0.0):
    root.location = (x, y, z)
    root.rotation_euler = (0, 0, math.radians(yaw))


def render_lineup():
    w.reset()
    roots = []

    def add(builder, x, y, z=0.0, yaw=0.0):
        result = builder()
        root = result[0]
        if len(result) == 2 and isinstance(result[1], tuple):
            result[1][0].animation_data.action = result[1][1][0]
        elif len(result) == 3 and result[2] is not None:
            result[2][0].animation_data.action = result[2][1][0]
        place(root, x, y, z, yaw)
        roots.append(root)
        return root

    add(phase1_assets.build_shelf_unit, -3.9, 0.7)
    add(phase1_assets.build_fireplace, -2.35, 0.7)
    add(phase1_assets.build_tool_wall, -0.75, 0.7, 1.1)
    add(phase1_assets.build_cuckoo_clock, 0.55, 0.7, 1.5)
    add(phase3_assets.build_chalkboard, 1.6, 0.55)
    add(phase1_assets.build_armchair, -3.6, -0.9, yaw=15)
    add(phase1_assets.build_workbench, -1.3, -0.7)
    add(phase2_toys.build_toy_town, 1.0, -0.8)
    add(phase1_assets.build_toymaker, 2.75, -0.6, yaw=-15)

    top = 0.9
    add(lambda: build_assets.BUILDERS["PartsTray"](), -1.95, -0.6, top)
    add(lambda: build_assets.BUILDERS["Turntable"](), -0.7, -0.75, top)
    add(phase2_toys.build_steam_train, -0.7, -0.75, top + 0.048, yaw=90)
    add(phase1_assets.build_desk_lamp, -1.15, -0.45, top, yaw=-30)
    add(phase2_toys.build_music_box, -1.45, -0.85, top, yaw=10)
    add(phase2_toys.build_jack_in_the_box, -1.0, -0.9, top, yaw=-10)
    town_top = phase2_toys.TOWN_TOP
    add(phase2_toys.build_toy_soldier, 1.2, -0.5, town_top + 0.022)
    add(phase2_toys.build_wind_up_mouse, 0.65, -1.05, town_top, yaw=30)

    objects = [o for r in roots for o in w.asset_objects(r)]
    bpy.context.scene.frame_set(9)
    cam = w.studio(objects, angle=(0.15, -1.0, 0.38), lens=35, fstop=40.0)
    lo, hi = w.world_bounds(objects)
    centre = (lo + hi) / 2
    cam.location = centre + (cam.location - centre) * 0.62
    cam.data.dof.focus_distance = (cam.location - centre).length
    w.render_still(os.path.join(OUT, "All_Assets_Lineup.png"), samples=192)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    os.makedirs(OUT, exist_ok=True)
    for job in args:
        if job == "room":
            render_room()
        elif job == "workshop":
            render_workshop()
        elif job == "lineup":
            render_lineup()
        else:
            render_single(job)
        print("RENDERED", job)


if __name__ == "__main__":
    main()
