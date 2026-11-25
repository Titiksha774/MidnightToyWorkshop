import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

import workshop_lib as w

OUT_DIR = os.path.join(w.BLENDER_DIR, "Phase3")
RENDER_DIR = os.path.join(OUT_DIR, "Renders")
UI_DIR = os.path.join(w.ART_DIR, "UI")

BOARD_W, BOARD_H = 0.86, 0.62
BOARD_CENTRE_Z = 1.3
BOARD_TILT = 12.0
BOARD_FACE_Y = -0.11


def build_chalkboard():
    root = w.empty("Chalkboard")
    rig = w.armature("Chalkboard", [("Root", (0, 0, 0), (0, 0, 0.2), None),
                                    ("Board", (0, 0, 0.75), (0, 0, 1.0), "Root")], parent=root)

    leg = w.rod("Easel_FrontLeg", (0.36, 0.0, 0.0), (0.27, 0.0, 1.78), 0.016, "Wood_Oak", segments=10, parent=root)
    w.mirror(leg, mirror_object=root)
    back_leg = w.rod("Easel_BackLeg", (0.0, 0.42, 0.0), (0.0, 0.03, 1.72), 0.015, "Wood_Oak", segments=10, parent=root)
    w.box("Easel_CrossBar", (0.66, 0.025, 0.03), "Wood_Oak", offset=(0, 0.0, 0.45), parent=root)
    peg = w.rod("Easel_Pegs", (0.31, 0.0, 0.925), (0.31, -0.2, 0.925), 0.01, "Wood_Walnut", segments=10, parent=root)
    w.mirror(peg, mirror_object=root)
    w.box("Easel_Top", (0.6, 0.04, 0.04), "Wood_Walnut", offset=(0, 0.01, 1.74), parent=root)
    w.cylinder("Easel_Hinge", 0.012, 0.06, "Metal_Brass", rotation=(90, 0, 0), offset=(0, 0.02, 1.72), segments=12,
               parent=root)

    pivot = w.empty("Board_Pivot", (0, BOARD_FACE_Y, BOARD_CENTRE_Z), parent=root)
    pivot.rotation_euler = (math.radians(-BOARD_TILT), 0, 0)
    bpy.context.view_layer.update()
    half_h = BOARD_H / 2
    parts = [w.box("Board_Slate", (BOARD_W, 0.012, BOARD_H), "Slate", offset=(0, 0.006, 0), parent=pivot)]
    for name, z in (("Board_FrameTop", half_h + 0.0225), ("Board_FrameBottom", -half_h - 0.0225)):
        bar = w.box(name, (BOARD_W + 0.09, 0.026, 0.045), "Wood_Walnut", offset=(0, 0.004, z), parent=pivot)
        w.bevel(bar, 0.004)
        parts.append(bar)
    frame_v = w.box("Board_FrameSides", (0.045, 0.026, BOARD_H), "Wood_Walnut", offset=(BOARD_W / 2 + 0.0225, 0.004, 0),
                    parent=pivot)
    w.mirror(frame_v)
    w.bevel(frame_v, 0.004)
    parts += [frame_v,
              w.box("Board_Tray", (BOARD_W, 0.07, 0.012), "Wood_Walnut", offset=(0, -0.03, -half_h - 0.05), parent=pivot),
              w.box("Board_TrayLip", (BOARD_W, 0.008, 0.022), "Wood_Walnut", offset=(0, -0.062, -half_h - 0.045),
                    parent=pivot)]
    for k, (x, length, mat) in enumerate(((-0.2, 0.07, "Enamel_White"), (-0.1, 0.05, "Enamel_Yellow"),
                                          (0.0, 0.06, "Enamel_Pink"))):
        parts.append(w.cylinder(f"Chalk{k}", 0.0055, length, mat, rotation=(0, 90, 8 * k),
                                offset=(x, -0.035, -half_h - 0.038), segments=10, parent=pivot))
    eraser = w.box("Eraser", (0.11, 0.045, 0.025), "Wood_Oak", offset=(0.22, -0.032, -half_h - 0.03), rotation=(0, 0, -6),
                   parent=pivot)
    w.bevel(eraser, 0.004)
    felt = w.box("Eraser_Felt", (0.112, 0.047, 0.008), "Fabric_Navy", offset=(0.22, -0.032, -half_h - 0.044),
                 rotation=(0, 0, -6), parent=pivot)
    parts += [eraser, felt]
    star = [((0.025 if i % 2 == 0 else 0.01) * math.cos(math.radians(90 + 36 * i)),
             (0.025 if i % 2 == 0 else 0.01) * math.sin(math.radians(90 + 36 * i))) for i in range(10)]
    parts.append(w.prism("Board_Doodle", star, 0.001, "Enamel_White", offset=(0.34, -0.0005, 0.23), parent=pivot))
    w.attach(parts, rig, "Board")

    wobble = w.make_action(rig, "Wobble", [(1, {}), (5, {"Board": (-3, 0, 1.5)}), (10, {"Board": (2, 0, -1)}),
                                           (15, {"Board": (-1, 0, 0.5)}), (20, {})])
    still = w.make_action(rig, "Still", [(1, {}), (12, {})])
    rig.animation_data.action = still
    return root, (rig, [still, wobble])


def controller(side):
    s = side
    root = w.empty(f"Controller_{'R' if s > 0 else 'L'}")
    head = w.cylinder("Head", 0.038, 0.03, "Plastic_Dark", offset=(0, 0, 0.0), segments=40, parent=root)
    w.bevel(head, 0.01, 4)
    face = w.cylinder("Face", 0.033, 0.002, "Plastic_Light", offset=(0, 0, 0.0155), segments=40, parent=root)
    w.rod("Handle", (s * 0.004, 0.012, -0.004), (s * 0.012, 0.075, -0.085), 0.021, "Plastic_Dark",
          radius_end=0.017, segments=32, parent=root)
    w.sphere("Handle_End", 0.017, "Plastic_Dark", offset=(s * 0.012, 0.075, -0.085), segments=24, parent=root)
    stick_pos = (-s * 0.009, -0.006, 0.018)
    w.cylinder("Thumbstick_Base", 0.011, 0.004, "Plastic_Dark", offset=stick_pos, segments=24, parent=root)
    w.cylinder("Thumbstick_Stem", 0.0035, 0.008, "Plastic_Dark", offset=(stick_pos[0], stick_pos[1], 0.023),
               segments=12, parent=root)
    w.cylinder("Thumbstick_Cap", 0.0095, 0.004, "Plastic_Dark", offset=(stick_pos[0], stick_pos[1], 0.0285),
               segments=24, parent=root)
    btn_a = (s * 0.014, -0.012, 0.0175)
    btn_b = (s * 0.006, 0.009, 0.0175)
    w.cylinder("Button_Lower", 0.0055, 0.004, "Plastic_Dark", offset=btn_a, segments=20, parent=root)
    w.cylinder("Button_Upper", 0.0055, 0.004, "Plastic_Dark", offset=btn_b, segments=20, parent=root)
    menu = (-s * 0.02, 0.016, 0.017)
    w.cylinder("Button_Menu", 0.0032, 0.003, "Plastic_Dark", offset=menu, segments=16, parent=root)
    trigger = w.box("Trigger", (0.014, 0.012, 0.022), "Plastic_Light", offset=(0, -0.03, -0.02), rotation=(-25, 0, 0),
                    parent=root)
    w.bevel(trigger, 0.004, 3)
    grip_pos = (-s * 0.0135, 0.045, -0.048)
    grip = w.box("Grip", (0.008, 0.03, 0.035), "Plastic_Light", offset=grip_pos, rotation=(-40, 0, 0), parent=root)
    w.bevel(grip, 0.003, 3)
    points = {"thumbstick": (stick_pos[0], stick_pos[1], 0.031), "trigger": (0, -0.04, -0.02),
              "grip": (grip_pos[0] - s * 0.004, grip_pos[1], grip_pos[2]), "menu": (menu[0], menu[1], 0.019),
              "buttons": (btn_a[0], btn_a[1], 0.02)}
    return root, points


def render_controller_art():
    w.reset()
    pairs = []
    for side, x in ((-1, -0.075), (1, 0.075)):
        root, points = controller(side)
        root.location = (x, 0, 0)
        root.rotation_euler = (math.radians(12), 0, math.radians(side * 28))
        pairs.append((side, root, points))
    bpy.context.view_layer.update()

    objects = [o for _, r, _ in pairs for o in w.asset_objects(r)]
    cam = w.studio(objects, angle=(0, -1.0, 0.3), lens=85, fstop=40)
    for obj in bpy.data.collections["Studio"].objects:
        if obj.name == "Backdrop":
            obj.hide_render = True
    scene = bpy.context.scene
    scene.render.film_transparent = True
    bpy.context.view_layer.update()
    width, height = 1600, 900
    scene.render.resolution_x, scene.render.resolution_y = width, height

    callouts = {}
    for side, root, points in pairs:
        hand = "right" if side > 0 else "left"
        for name, local in points.items():
            co = world_to_camera_view(scene, cam, root.matrix_world @ Vector(local))
            callouts[f"{hand}_{name}"] = [round(co.x, 4), round(co.y, 4)]
    os.makedirs(UI_DIR, exist_ok=True)
    with open(os.path.join(UI_DIR, "controller_callouts.json"), "w") as f:
        json.dump({"width": width, "height": height, "points": callouts}, f, indent=1)

    w.render_still(os.path.join(UI_DIR, "Controllers.png"), samples=96, width=width, height=height)
    w.render_still(os.path.join(RENDER_DIR, "ControllerArt.png"), samples=96, width=width, height=height)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "ControllerArt.blend"))
    print("ASSET ControllerArt  callouts:", sorted(callouts))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render = "--no-render" not in args
    names = [a for a in args if not a.startswith("--")] or ["Chalkboard", "ControllerArt"]
    os.makedirs(RENDER_DIR, exist_ok=True)
    w.write_material_json()
    if "Chalkboard" in names:
        w.reset()
        root, (rig, actions) = build_chalkboard()
        objects = w.asset_objects(root)
        tris = w.triangle_count(objects)
        w.export_fbx(root, "Environment", animated=True)
        if render:
            w.studio(objects, angle=(0.6, -1.0, 0.25), fstop=10.0)
            w.render_still(os.path.join(RENDER_DIR, "Chalkboard.png"))
            last = w.queue_actions_for_preview(rig, actions)
            w.render_video(os.path.join(RENDER_DIR, "Chalkboard_animations.mp4"), 1, last)
            rig.animation_data.action = actions[0]
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "Chalkboard.blend"))
        print(f"ASSET Chalkboard {tris:>6} tris  anims: {[a.name for a in actions]}")
    if "ControllerArt" in names and render:
        render_controller_art()


if __name__ == "__main__":
    main()
