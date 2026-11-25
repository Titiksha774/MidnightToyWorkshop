import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

import phase1_assets as assets
import workshop_lib as w

LAYOUT = [
    ("WorkshopRoom", (0.0, 0.0, 0.6), 0),
    ("Workbench", (0.0, 0.0, 0.75), 180),
    ("ToolWall", (-1.6, 1.55, 3.4), 180),
    ("CuckooClock", (1.5, 1.95, 3.4), 180),
    ("ShelfUnit", (2.98, 0.0, 1.6), -90),
    ("Fireplace", (-2.98, 0.0, 0.9), 90),
    ("Armchair", (-2.05, 0.0, -0.35), -40),
    ("DeskLamp", (0.2, 0.9, 1.1), -150),
    ("Toymaker", (1.15, 0.0, 0.95), -130),
]

LIGHTS = [
    dict(name="Moonlight", type="Directional", position=(0, 2.8, 3.4), rotation=(28, 165, 0),
         color=(0.62, 0.72, 1.0), power=1.2, intensity=0.45),
    dict(name="Desk Lamp Light", type="Point", position=(0.41, 1.21, 1.21), color=(1.0, 0.78, 0.5),
         power=35, intensity=2.2, range=3.5),
    dict(name="Fire Light", type="Point", position=(-1.85, 0.4, 0.55), color=(1.0, 0.55, 0.22),
         power=90, intensity=3.0, range=5.0),
    dict(name="Candle Light L", type="Point", position=(-1.88, 1.6, 0.0), color=(1.0, 0.7, 0.4),
         power=3, intensity=0.4, range=1.5),
    dict(name="Candle Light R", type="Point", position=(-1.88, 1.6, 1.1), color=(1.0, 0.7, 0.4),
         power=3, intensity=0.4, range=1.5),
]


def room_entry():
    return {"width": assets.ROOM_WIDTH, "depth": assets.ROOM_DEPTH, "height": assets.ROOM_HEIGHT,
            "wall": assets.ROOM_WALL, "doorX": assets.ROOM_DOOR_X, "centre": list(LAYOUT[0][1])}


def to_blender(p):
    x, y, z = p
    return Vector((-x, -z, y))


def place(root, position, yaw):
    root.location = to_blender(position)
    root.rotation_euler = (0, 0, math.radians(-yaw))


def add_light(spec):
    kind = {"Directional": "SUN", "Point": "POINT"}[spec["type"]]
    data = bpy.data.lights.new(spec["name"], kind)
    data.color = w.srgb_to_linear(spec["color"])
    data.energy = spec["power"]
    if kind == "POINT":
        data.shadow_soft_size = 0.05
    obj = bpy.data.objects.new(spec["name"], data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = to_blender(spec["position"])
    if kind == "SUN":
        direction = Vector((0.15, 1.0, -0.55)).normalized()
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        data.angle = math.radians(2)
    return obj


def camera(name, eye_unity, target_unity, lens=24):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = 0.02
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    eye, target = to_blender(eye_unity), to_blender(target_unity)
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    data.dof.use_dof = True
    data.dof.focus_distance = (target - eye).length
    data.dof.aperture_fstop = 5.6
    return cam


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    w.reset()
    for name, position, yaw in LAYOUT:
        root, _, anim = assets.BUILDERS[name]()
        place(root, position, yaw)
        if anim is not None:
            anim[0].animation_data.action = anim[1][0]
    bpy.context.view_layer.update()
    lamp = bpy.data.objects["DeskLamp"].matrix_world
    fire = bpy.data.objects["Fireplace"].matrix_world
    anchors = {
        "Desk Lamp Light": lamp @ Vector((0.33, 0.01, 0.29)),
        "Fire Light": fire @ Vector((0.0, -0.3, 0.38)),
        "Candle Light L": fire @ Vector((0.55, -0.32, 1.6)),
        "Candle Light R": fire @ Vector((-0.55, -0.32, 1.6)),
    }
    for spec in LIGHTS:
        if spec["name"] in anchors:
            b = anchors[spec["name"]]
            spec["position"] = (round(-b.x, 3), round(b.z, 3), round(-b.y, 3))
        add_light(spec)

    world = bpy.data.worlds.new("Night")
    bpy.context.scene.world = world
    world.color = (0.004, 0.005, 0.012)
    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (0.004, 0.005, 0.012, 1)
    bpy.context.scene.frame_set(1)

    shots = [
        ("Hero_PlayerView", camera("Hero_PlayerView", (0.0, 1.62, -0.75), (0.15, 1.05, 1.6), lens=22)),
        ("Hero_Wide", camera("Hero_Wide", (1.75, 1.85, -1.55), (-0.7, 0.95, 1.2), lens=18)),
        ("Hero_Fireside", camera("Hero_Fireside", (-0.2, 1.25, -1.2), (-1.9, 0.75, 0.6), lens=28)),
    ]

    layout = {
        "room": room_entry(),
        "assets": [{"asset": n, "fbx": f"Assets/Art/{'Characters' if n == 'Toymaker' else 'Environment'}/{n}.fbx",
                    "position": list(p), "yaw": yaw} for n, p, yaw in LAYOUT],
        "lights": [{k: (list(v) if isinstance(v, tuple) else v) for k, v in spec.items() if k != "power"} for spec in LIGHTS],
    }
    with open(os.path.join(w.ART_DIR, "workshop_layout.json"), "w") as f:
        json.dump(layout, f, indent=1)

    out_dir = os.path.join(w.BLENDER_DIR, "Phase1")
    if "--no-render" not in args:
        for name, cam in shots:
            bpy.context.scene.camera = cam
            w.render_still(os.path.join(out_dir, "Renders", f"{name}.png"), samples=256)
    bpy.context.scene.camera = shots[0][1]
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "Workshop_Assembly.blend"))
    print("ASSEMBLY saved, triangles:", w.triangle_count(list(bpy.context.scene.objects)))


if __name__ == "__main__":
    main()
