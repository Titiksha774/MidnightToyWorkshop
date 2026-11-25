import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix, Vector

import phase1_assembly as p1
import phase1_assets
import phase2_toys as toys
import phase3_assets
import workshop_lib as w

TOY_SPOTS = {
    "ToyTown": (None, (2.42, 0.0, -0.5), -90),
    "SteamTrain": ("ToyTown", (0.0, -toys.TRACK_B, toys.RAIL_TOP), 90),
    "ToySoldier": ("ToyTown", (0.17, 0.3, toys.TOWN_TOP + 0.022), 0),
    "MusicBox": ("Fireplace", (0.0, -0.46, 1.36), 0),
    "JackInTheBox": ("ShelfUnit", (0.33, -0.18, 0.1 + 0.0125 + 2 * 0.44), 0),
    "WindUpMouse": (None, (-1.85, 0.012, 0.4), -130),
    "Chalkboard": (None, (-1.25, 0.0, 1.65), 145),
}

BUILDERS = {**{name: (builder, "Toys") for name, builder in toys.BUILDERS.items()},
            "Chalkboard": (phase3_assets.build_chalkboard, "Environment")}

EXTRA_LIGHTS = [
    dict(name="Toy Town Light", type="Point", position=(0, 0, 0), color=(1.0, 0.8, 0.55), power=14, intensity=1.3,
         range=2.2),
]


def unity_from_matrix(m):
    loc = m.translation
    yaw = -math.degrees(m.to_euler("XYZ").z)
    return [round(-loc.x, 4), round(loc.z, 4), round(-loc.y, 4)], round(yaw, 2)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    w.reset()
    placed = {}
    for name, position, yaw in p1.LAYOUT:
        root, _, anim = phase1_assets.BUILDERS[name]()
        p1.place(root, position, yaw)
        if anim is not None:
            anim[0].animation_data.action = anim[1][0]
        placed[name] = root
    bpy.context.view_layer.update()

    toy_entries = []
    for name, (host, position, yaw) in TOY_SPOTS.items():
        builder, category = BUILDERS[name]
        root, (rig, actions) = builder()
        rig.animation_data.action = actions[0]
        if host is None:
            p1.place(root, position, yaw)
        else:
            root.matrix_world = (placed[host].matrix_world @ Matrix.Translation(position) @
                                 Matrix.Rotation(math.radians(yaw), 4, "Z"))
        bpy.context.view_layer.update()
        placed[name] = root
        unity_pos, unity_yaw = unity_from_matrix(root.matrix_world)
        toy_entries.append({"asset": name, "fbx": f"Assets/Art/{category}/{name}.fbx", "position": unity_pos, "yaw": unity_yaw})

    lamp, fire, town = (placed[n].matrix_world for n in ("DeskLamp", "Fireplace", "ToyTown"))
    anchors = {
        "Desk Lamp Light": lamp @ Vector((0.33, 0.01, 0.29)),
        "Fire Light": fire @ Vector((0.0, -0.3, 0.38)),
        "Candle Light L": fire @ Vector((0.55, -0.32, 1.6)),
        "Candle Light R": fire @ Vector((-0.55, -0.32, 1.6)),
        "Toy Town Light": town @ Vector((0.0, -0.12, 1.45)),
    }
    lights = [dict(spec) for spec in p1.LIGHTS + EXTRA_LIGHTS]
    for spec in lights:
        if spec["name"] in anchors:
            b = anchors[spec["name"]]
            spec["position"] = (round(-b.x, 3), round(b.z, 3), round(-b.y, 3))
        p1.add_light(spec)

    world = bpy.data.worlds.new("Night")
    bpy.context.scene.world = world
    world.color = (0.004, 0.005, 0.012)
    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (0.004, 0.005, 0.012, 1)
    bpy.context.scene.frame_set(9)

    def unity_of(name, local=(0, 0, 0)):
        p = placed[name].matrix_world @ Vector(local)
        return (-p.x, p.z, -p.y)

    shots = [
        ("Hero_ToyTown", p1.camera("Hero_ToyTown", (0.62, 1.42, -0.2), unity_of("ToyTown", (0, 0, 0.8)), lens=24)),
        ("Hero_TrainCloseUp", p1.camera("Hero_TrainCloseUp", unity_of("ToyTown", (0.18, -0.55, 0.95)),
                                        unity_of("SteamTrain", (0, 0, 0.06)), lens=40)),
        ("Hero_Mantel", p1.camera("Hero_Mantel", (-1.05, 1.55, 0.2), unity_of("MusicBox", (0, 0, 0.08)), lens=40)),
        ("Hero_JackShelf", p1.camera("Hero_JackShelf", unity_of("ShelfUnit", (0.15, -0.85, 1.25)),
                                     unity_of("JackInTheBox", (0, 0, 0.15)), lens=40)),
        ("Hero_Mouse", p1.camera("Hero_Mouse", (-0.75, 0.32, -0.45), unity_of("WindUpMouse", (0, 0, 0.03)), lens=45)),
        ("Hero_Phase2_Wide", p1.camera("Hero_Phase2_Wide", (-0.9, 1.75, -1.45), (0.9, 0.8, 0.35), lens=18)),
    ]

    layout = {
        "room": p1.room_entry(),
        "assets": [{"asset": n, "fbx": f"Assets/Art/{'Characters' if n == 'Toymaker' else 'Environment'}/{n}.fbx",
                    "position": list(p), "yaw": yaw} for n, p, yaw in p1.LAYOUT] + toy_entries,
        "lights": [{k: (list(v) if isinstance(v, tuple) else v) for k, v in spec.items() if k != "power"}
                   for spec in lights],
    }
    with open(os.path.join(w.ART_DIR, "workshop_layout.json"), "w") as f:
        json.dump(layout, f, indent=1)
    print("LAYOUT written:", [e["asset"] for e in toy_entries])

    out_dir = os.path.join(w.BLENDER_DIR, "Phase2")
    if "--no-render" not in args:
        for name, cam in shots:
            bpy.context.scene.camera = cam
            w.render_still(os.path.join(out_dir, "Renders", f"{name}.png"), samples=256)
    bpy.context.scene.camera = shots[0][1]
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "Workshop_Phase2.blend"))
    print("ASSEMBLY saved, triangles:", w.triangle_count(list(bpy.context.scene.objects)))


if __name__ == "__main__":
    main()
