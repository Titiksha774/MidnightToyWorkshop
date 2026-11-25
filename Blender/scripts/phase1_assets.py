import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workshop_lib as w

OUT_DIR = os.path.join(w.BLENDER_DIR, "Phase1")

ROOM_WIDTH, ROOM_DEPTH, ROOM_HEIGHT, ROOM_WALL, ROOM_DOOR_X = 6.0, 5.6, 3.0, 0.15, -1.2
RENDER_DIR = os.path.join(OUT_DIR, "Renders")


def build_workshop_room():
    root = w.empty("WorkshopRoom")
    W, D, H, T = ROOM_WIDTH, ROOM_DEPTH, ROOM_HEIGHT, ROOM_WALL
    hw, hd = W / 2, D / 2
    wain = 1.0

    w.box("Floor", (W + 2 * T, D + 2 * T, 0.05), "Wood_Floor", offset=(0, 0, -0.025), parent=root)
    w.box("Ceiling", (W + 2 * T, D + 2 * T, 0.05), "Plaster", offset=(0, 0, H + 0.025), parent=root)
    beams = int(W / 0.9)
    beam = w.box("Ceiling_Beams", (0.16, D, 0.2), "Wood_Walnut", offset=(-0.45 * (beams - 1), 0, H - 0.1), parent=root)
    w.bevel(beam, 0.01)
    w.array(beam, beams, constant=(0.9, 0, 0))

    def wall(name, length, axis, side, openings=()):
        parts = []
        if axis == "x":
            y = side * (hd + T / 2)
            parts.append(w.box(f"{name}_Brick", (length, T + 0.04, wain), "Brick", offset=(0, y - side * 0.02, wain / 2), parent=root))
            if not openings:
                parts.append(w.box(f"{name}_Plaster", (length, T, H - wain), "Plaster", offset=(0, y, wain + (H - wain) / 2), parent=root))
            rail = w.box(f"{name}_Rail", (length, 0.05, 0.06), "Wood_Walnut", offset=(0, y - side * (T / 2 + 0.04), wain + 0.03), parent=root)
        else:
            x = side * (hw + T / 2)
            parts.append(w.box(f"{name}_Brick", (T + 0.04, length, wain), "Brick", offset=(x - side * 0.02, 0, wain / 2), parent=root))
            parts.append(w.box(f"{name}_Plaster", (T, length, H - wain), "Plaster", offset=(x, 0, wain + (H - wain) / 2), parent=root))
            rail = w.box(f"{name}_Rail", (0.05, length, 0.06), "Wood_Walnut", offset=(x - side * (T / 2 + 0.04), 0, wain + 0.03), parent=root)
        w.bevel(rail, 0.008)
        return parts

    wall("WallLeft", D + 2 * T, "y", 1)
    wall("WallRight", D + 2 * T, "y", -1)

    wall("WallWindow", W + 2 * T, "x", -1, openings=True)
    wy = -(hd + T / 2)
    win_w, sill, spring = 1.0, 1.2, 2.0
    r = win_w / 2
    side_w = (W + 2 * T - win_w) / 2
    for s in (-1, 1):
        w.box(f"WallWindow_Plaster_{'L' if s > 0 else 'R'}", (side_w, T, H - wain), "Plaster",
              offset=(s * (win_w / 2 + side_w / 2), wy, wain + (H - wain) / 2), parent=root)
    w.box("WallWindow_Plaster_Below", (win_w, T, sill - wain), "Plaster", offset=(0, wy, wain + (sill - wain) / 2), parent=root)
    arch = [(-r, spring)] + [(-r * math.cos(math.pi * i / 16), spring + r * math.sin(math.pi * i / 16)) for i in range(1, 16)] \
        + [(r, spring), (r, H), (-r, H)]
    w.prism("WallWindow_Plaster_Arch", arch, T, "Plaster", offset=(0, wy + T / 2, 0), parent=root)

    for s in (-1, 1):
        jamb = w.box("Window_Jamb", (0.06, T + 0.04, spring - sill), "Wood_Walnut",
                     offset=(s * (r - 0.03), wy, sill + (spring - sill) / 2), parent=root)
        w.bevel(jamb, 0.005)
    trim = w.torus("Window_ArchTrim", r - 0.03, 0.03, "Wood_Walnut", rotation=(90, 0, 0), offset=(0, wy - T / 2 - 0.01, spring),
                   major_segments=24, minor_segments=8, arc=180, parent=root)
    sill_board = w.box("Window_Sill", (win_w + 0.2, 0.22, 0.04), "Wood_Oak", offset=(0, wy - 0.05, sill - 0.02), parent=root)
    w.bevel(sill_board, 0.008)
    w.box("Window_Mullion_V", (0.035, 0.04, spring + r - sill), "Wood_Walnut", offset=(0, wy, sill + (spring + r - sill) / 2), parent=root)
    w.box("Window_Mullion_H", (win_w, 0.04, 0.035), "Wood_Walnut", offset=(0, wy, 1.6), parent=root)
    glass_pts = [(-r, sill), (r, sill), (r, spring)] + \
        [(r * math.cos(math.pi * i / 16), spring + r * math.sin(math.pi * i / 16)) for i in range(1, 16)] + [(-r, spring)]
    w.prism("Window_Glass", glass_pts, 0.006, "Glass", offset=(0, wy + 0.003, 0), parent=root)
    w.box("Window_NightView", (3.2, 0.02, 2.4), "NightSky", offset=(0, -(hd + T + 0.6), 1.9), parent=root)

    dy = hd + T / 2
    door_x, door_w, door_h = ROOM_DOOR_X, 0.9, 2.05
    left_len = (W + 2 * T) / 2 + door_x - door_w / 2
    right_len = (W + 2 * T) / 2 - door_x - door_w / 2
    for name, length, cx in (("L", left_len, -(W + 2 * T) / 2 + left_len / 2), ("R", right_len, (W + 2 * T) / 2 - right_len / 2)):
        w.box(f"WallDoor_Brick_{name}", (length, T + 0.04, wain), "Brick", offset=(cx, dy + 0.02, wain / 2), parent=root)
        w.box(f"WallDoor_Plaster_{name}", (length, T, H - wain), "Plaster", offset=(cx, dy, wain + (H - wain) / 2), parent=root)
        rail = w.box(f"WallDoor_Rail_{name}", (length, 0.05, 0.06), "Wood_Walnut", offset=(cx, dy - T / 2 - 0.04, wain + 0.03), parent=root)
        w.bevel(rail, 0.008)
    w.box("WallDoor_Plaster_Above", (door_w, T, H - door_h), "Plaster", offset=(door_x, dy, door_h + (H - door_h) / 2), parent=root)
    for s in (-1, 1):
        w.box("Door_Frame_Side", (0.07, T + 0.06, door_h), "Wood_Walnut", offset=(door_x + s * (door_w / 2 - 0.035), dy, door_h / 2), parent=root)
    w.box("Door_Frame_Top", (door_w, T + 0.06, 0.07), "Wood_Walnut", offset=(door_x, dy, door_h - 0.035), parent=root)
    door = w.box("Door_Planks", (door_w - 0.14, 0.04, door_h - 0.07), "Wood_Oak", offset=(door_x, dy - 0.02, (door_h - 0.07) / 2), parent=root)
    w.bevel(door, 0.004)
    for z in (0.35, 1.7):
        w.box("Door_Brace", (door_w - 0.18, 0.025, 0.1), "Wood_Walnut", offset=(door_x, dy - 0.05, z), parent=root)
        w.box("Door_Hinge", (0.18, 0.012, 0.035), "Metal_Iron", offset=(door_x + door_w / 2 - 0.16, dy - 0.07, z), parent=root)
    w.sphere("Door_Handle", 0.03, "Metal_Brass", offset=(door_x - door_w / 2 + 0.14, dy - 0.08, 1.0), segments=16, parent=root)

    rug = w.box("Rug", (1.3, 1.9, 0.012), "Fabric_Rug", offset=(1.7, -0.15, 0.006), parent=root)
    w.bevel(rug, 0.2, segments=6)
    border = w.box("Rug_Border", (1.36, 1.96, 0.008), "Fabric_Cream", offset=(1.7, -0.15, 0.004), parent=root)
    w.bevel(border, 0.22, segments=6)
    return root, "Environment", None


def build_workbench():
    root = w.empty("Workbench")
    top = w.box("Bench_Top", (1.8, 0.8, 0.07), "Wood_Oak", offset=(0, 0, 0.865), parent=root, uv_rotate=True)
    w.bevel(top, 0.01, 3)
    leg = w.box("Bench_Legs", (0.09, 0.09, 0.83), "Wood_Walnut", offset=(0.83, 0.33, 0.415), parent=root)
    w.mirror(leg, x=True, y=True)
    w.bevel(leg, 0.008)
    side_rail = w.box("Bench_SideRails", (0.04, 0.6, 0.1), "Wood_Walnut", offset=(0.83, 0, 0.77), parent=root)
    w.mirror(side_rail, x=True)
    back_rail = w.box("Bench_BackRail", (1.6, 0.04, 0.12), "Wood_Walnut", offset=(0, 0.35, 0.77), parent=root)
    w.bevel(back_rail, 0.005)
    shelf = w.box("Bench_Shelf", (1.66, 0.66, 0.03), "Wood_Oak", offset=(0, 0, 0.18), parent=root, uv_rotate=True)
    w.bevel(shelf, 0.006)
    stretcher = w.box("Bench_Stretchers", (0.05, 0.6, 0.05), "Wood_Walnut", offset=(0.83, 0, 0.16), parent=root)
    w.mirror(stretcher, x=True)
    w.box("Bench_DrawerCase", (1.66, 0.62, 0.015), "Wood_Walnut", offset=(0, 0.02, 0.68), parent=root)
    for x in (-0.28, 0.28):
        w.box("Bench_DrawerDivider", (0.02, 0.62, 0.13), "Wood_Walnut", offset=(x, 0.02, 0.755), parent=root)

    w.box("Bench_Ruler", (0.5, 0.04, 0.004), "Wood_Oak", offset=(-0.45, -0.25, 0.902), rotation=(0, 0, 8), parent=root, uv_rotate=True)
    pencil = w.cylinder("Bench_Pencil", 0.005, 0.17, "Enamel_Yellow", rotation=(0, 90, 20), offset=(0.6, -0.28, 0.906), segments=6, parent=root)

    vice = w.empty("Vice", (0.72, -0.36, 0.9), parent=root)
    w.box("Vice_Body", (0.16, 0.12, 0.08), "Metal_Iron", offset=(0, 0, 0.04), parent=vice)
    w.box("Vice_JawFixed", (0.18, 0.025, 0.06), "Metal_Iron", offset=(0, -0.07, 0.09), parent=vice)
    w.box("Vice_JawMoving", (0.18, 0.025, 0.06), "Metal_Iron", offset=(0, -0.13, 0.09), parent=vice)
    w.rod("Vice_Screw", (0, -0.05, 0.05), (0, -0.25, 0.05), 0.01, "Metal_Iron", parent=vice)
    w.rod("Vice_Handle", (-0.09, -0.25, 0.05), (0.09, -0.25, 0.05), 0.007, "Metal_Brass", parent=vice)
    for s in (-1, 1):
        w.sphere("Vice_HandleEnd", 0.014, "Metal_Brass", offset=(s * 0.09, -0.25, 0.05), segments=12, parent=vice)

    bones = [("Root", (0, 0, 0), (0, 0, 0.2), None)]
    drawer_x = (-0.56, 0.0, 0.56)
    for i, x in enumerate(drawer_x):
        bones.append((f"Drawer_{i + 1}", (x, -0.3, 0.755), (x, -0.4, 0.755), "Root"))
    rig = w.armature("Workbench", bones, parent=root)
    for i, x in enumerate(drawer_x):
        front = w.box(f"Drawer{i + 1}_Front", (0.52, 0.025, 0.12), "Wood_Oak", offset=(x, -0.33, 0.755), parent=root, uv_rotate=True)
        w.bevel(front, 0.006)
        tray = w.box(f"Drawer{i + 1}_Box", (0.48, 0.55, 0.09), "Wood_Walnut", offset=(x, -0.04, 0.75), parent=root)
        knob = w.sphere(f"Drawer{i + 1}_Knob", 0.018, "Metal_Brass", offset=(x, -0.355, 0.755), segments=14, parent=root)
        w.attach([front, tray, knob], rig, f"Drawer_{i + 1}")

    out = (0, -0.3, 0)
    open_action = w.make_action(rig, "Open", [
        (1, {}),
        (8, {}, {"Drawer_1": out}),
        (14, {}, {"Drawer_1": out, "Drawer_2": out}),
        (20, {}, {"Drawer_1": out, "Drawer_2": out, "Drawer_3": out}),
    ])
    close_action = w.make_action(rig, "Close", [
        (1, {}, {"Drawer_1": out, "Drawer_2": out, "Drawer_3": out}),
        (16, {}),
    ])
    rig.animation_data.action = open_action
    return root, "Environment", (rig, [open_action, close_action])


def build_tool_wall():
    root = w.empty("ToolWall")
    w.box("Pegboard", (1.3, 0.02, 0.85), "Pegboard", offset=(0, -0.03, 0), parent=root)
    frame_h = w.box("Pegboard_FrameH", (1.36, 0.035, 0.04), "Wood_Walnut", offset=(0, -0.035, 0.445), parent=root)
    w.mirror(frame_h, x=False, z=True)
    frame_v = w.box("Pegboard_FrameV", (0.04, 0.035, 0.85), "Wood_Walnut", offset=(0.66, -0.035, 0), parent=root)
    w.mirror(frame_v, x=True)

    def peg(x, z):
        w.rod("Peg", (x, -0.04, z), (x, -0.1, z + 0.01), 0.004, "Metal_Brass", parent=root)

    peg(-0.5, 0.25)
    w.rod("Hammer_Handle", (-0.5, -0.07, -0.12), (-0.5, -0.07, 0.2), 0.014, "Wood_Oak", parent=root)
    head = w.box("Hammer_Head", (0.13, 0.035, 0.035), "Metal_Iron", offset=(-0.5, -0.07, 0.21), parent=root)
    w.bevel(head, 0.004)
    peg(-0.18, 0.3)
    blade = [(-0.35, 0.0), (0.05, 0.02), (0.05, 0.13), (-0.35, 0.08)]
    w.prism("Saw_Blade", blade, 0.002, "Metal_Iron", offset=(-0.08, -0.06, 0.12), parent=root)
    tooth = w.prism("Saw_Teeth", [(-0.35, 0.0), (-0.343, -0.008), (-0.336, 0.0)], 0.002, "Metal_Iron",
                    offset=(-0.08, -0.06, 0.12), parent=root)
    w.array(tooth, 28, constant=(0.0143, 0, 0.0007))
    w.box("Saw_Handle", (0.1, 0.025, 0.11), "Wood_Walnut", offset=(-0.0, -0.065, 0.195), parent=root)
    for i, colour in enumerate(("Enamel_Red", "Enamel_Yellow", "Enamel_Blue")):
        x = 0.12 + i * 0.07
        peg(x, 0.3)
        w.cylinder(f"Screwdriver{i}_Handle", 0.016, 0.1, colour, offset=(x, -0.07, 0.22), segments=8, parent=root)
        w.rod(f"Screwdriver{i}_Shaft", (x, -0.07, 0.17), (x, -0.07, 0.0), 0.004, "Metal_Iron", parent=root)
    peg(0.42, 0.28)
    arm_l = w.rod("Pliers_Arm", (0.42, -0.07, 0.26), (0.46, -0.07, 0.05), 0.007, "Metal_Iron", parent=root)
    w.mirror(arm_l, x=True, mirror_object=w.empty("PliersCentre", (0.42, -0.07, 0), parent=root))
    grip = w.rod("Pliers_Grip", (0.445, -0.07, 0.15), (0.462, -0.07, 0.05), 0.011, "Enamel_Red", parent=root)
    w.mirror(grip, x=True, mirror_object=w.empty("PliersCentre2", (0.42, -0.07, 0), parent=root))
    peg(-0.45, -0.15)
    w.box("Wrench_Bar", (0.022, 0.01, 0.24), "Metal_Iron", offset=(-0.45, -0.065, -0.3), parent=root)
    w.torus("Wrench_Ring", 0.022, 0.007, "Metal_Iron", rotation=(90, 0, 0), offset=(-0.45, -0.065, -0.16), parent=root)
    for i, x in enumerate((0.1, 0.18)):
        peg(x, -0.12)
        w.rod(f"Brush{i}_Handle", (x, -0.07, -0.13), (x, -0.07, -0.3), 0.008, "Wood_Oak", parent=root)
        w.cylinder(f"Brush{i}_Ferrule", 0.01, 0.03, "Metal_Brass", offset=(x, -0.07, -0.315), segments=10, parent=root)
        w.cylinder(f"Brush{i}_Bristles", 0.012, 0.04, "Fabric_Brown", radius_top=0.009, offset=(x, -0.07, -0.35),
                   segments=10, parent=root)
    peg(0.45, -0.1)
    w.rod("Drill_Crank1", (0.45, -0.07, -0.12), (0.45, -0.07, -0.2), 0.006, "Metal_Iron", parent=root)
    w.rod("Drill_Crank2", (0.45, -0.07, -0.2), (0.52, -0.07, -0.24), 0.006, "Metal_Iron", parent=root)
    w.rod("Drill_Crank3", (0.52, -0.07, -0.24), (0.45, -0.07, -0.3), 0.006, "Metal_Iron", parent=root)
    w.cylinder("Drill_Knob", 0.02, 0.04, "Wood_Walnut", offset=(0.45, -0.07, -0.1), segments=12, parent=root)
    w.cylinder("Drill_Chuck", 0.014, 0.05, "Metal_Brass", offset=(0.45, -0.07, -0.33), segments=12, parent=root)
    return root, "Environment", None


def build_shelf_unit():
    root = w.empty("ShelfUnit")
    side = w.box("Shelf_Sides", (0.035, 0.36, 1.9), "Wood_Walnut", offset=(0.5, -0.18, 0.95), parent=root)
    w.mirror(side, x=True)
    w.bevel(side, 0.006)
    board = w.box("Shelf_Boards", (0.97, 0.34, 0.025), "Wood_Walnut", offset=(0, -0.18, 0.1), parent=root, uv_rotate=True)
    w.array(board, 4, constant=(0, 0, 0.44))
    w.bevel(board, 0.004)
    w.box("Shelf_Top", (1.07, 0.38, 0.03), "Wood_Walnut", offset=(0, -0.18, 1.915), parent=root, uv_rotate=True)
    w.box("Shelf_Back", (0.97, 0.012, 1.86), "Wood_Oak", offset=(0, -0.006, 0.95), parent=root)
    levels = [0.1 + 0.0125 + i * 0.44 for i in range(4)] + [1.93]

    for i, colour in enumerate(("Enamel_Red", "Enamel_Blue", "Enamel_Yellow", "Enamel_Green")):
        x = -0.33 + i * 0.2
        w.cylinder(f"Tin{i}", 0.06, 0.11, "Metal_Iron", offset=(x, -0.18, levels[0] + 0.055), segments=20, parent=root)
        w.cylinder(f"Tin{i}_Lid", 0.062, 0.012, colour, offset=(x, -0.18, levels[0] + 0.116), segments=20, parent=root)
    for i, colour in enumerate(("Enamel_Red", "Enamel_Yellow", "Enamel_Blue", "Enamel_Green", "Enamel_Orange")):
        x, z = (-0.38 + (i % 3) * 0.085, levels[1] + 0.035 + (i // 3) * 0.07)
        block = w.box(f"Block{i}", (0.07, 0.07, 0.07), colour, offset=(x + (i // 3) * 0.04, -0.17, z),
                      rotation=(0, 0, 12 * i), parent=root)
        w.bevel(block, 0.006)
    w.sphere("Ball", 0.07, "Enamel_Red", offset=(0.05, -0.17, levels[1] + 0.07), parent=root)
    w.lathe("SpinningTop", [(0, 0), (0.05, 0.05), (0.06, 0.07), (0.02, 0.09), (0.008, 0.13), (0, 0.13)],
            "Enamel_Blue", offset=(0.3, -0.17, levels[1]), parent=root)
    jar = w.cylinder("Jars", 0.055, 0.16, "Glass", offset=(-0.3, -0.17, levels[2] + 0.08), segments=20, parent=root)
    w.array(jar, 3, constant=(0.2, 0, 0))
    lid = w.cylinder("Jar_Lids", 0.058, 0.02, "Metal_Brass", offset=(-0.3, -0.17, levels[2] + 0.17), segments=20, parent=root)
    w.array(lid, 3, constant=(0.2, 0, 0))
    for i, colour in enumerate(("Enamel_Red", "Enamel_Cream", "Enamel_Blue")):
        w.cylinder(f"Jar{i}_Contents", 0.045, 0.08, colour, offset=(-0.3 + i * 0.2, -0.17, levels[2] + 0.045), segments=16, parent=root)
    for i, colour in enumerate(("Enamel_Red", "Enamel_Yellow", "Enamel_Green", "Enamel_Blue")):
        x = -0.4 + i * 0.09
        w.lathe(f"Spool{i}", [(0, 0), (0.035, 0), (0.035, 0.01), (0.022, 0.012), (0.022, 0.078), (0.035, 0.08),
                              (0.035, 0.09), (0, 0.09)], "Wood_Oak", offset=(x, -0.17, levels[3]), parent=root)
        w.cylinder(f"Spool{i}_Thread", 0.03, 0.064, colour, offset=(x, -0.17, levels[3] + 0.045), segments=16, parent=root)
    x = 0.0
    for i, (colour, height) in enumerate((("Fabric_Red", 0.26), ("Fabric_Navy", 0.3), ("Fabric_Brown", 0.24),
                                          ("Fabric_Cream", 0.28), ("Fabric_Red", 0.22))):
        thick = 0.04 + 0.01 * (i % 2)
        book = w.box(f"Book{i}", (thick, 0.22, height), colour, offset=(x, -0.15, levels[3] + height / 2), parent=root)
        w.bevel(book, 0.004)
        x += thick + 0.005
    w.sphere("Globe", 0.09, "Enamel_Blue", offset=(0.25, -0.17, levels[4] + 0.15), parent=root)
    w.cylinder("Globe_Stand", 0.05, 0.05, "Wood_Walnut", offset=(0.25, -0.17, levels[4] + 0.025), parent=root)
    return root, "Environment", None


def build_fireplace():
    root = w.empty("Fireplace")
    for s in (-1, 1):
        pier = w.box("Fire_Pier", (0.32, 0.45, 1.05), "Brick", offset=(s * 0.5, -0.225, 0.525), parent=root)
    w.box("Fire_Lintel", (1.32, 0.45, 0.25), "Brick", offset=(0, -0.225, 1.175), parent=root)
    w.box("Fire_Back", (0.7, 0.05, 1.0), "Metal_Iron", offset=(0, -0.025, 0.5), parent=root)
    w.box("Fire_Hearth", (1.5, 0.65, 0.06), "Brick", offset=(0, -0.3, 0.03), parent=root)
    w.box("Fire_Breast", (1.1, 0.35, 1.45), "Plaster", offset=(0, -0.175, 1.35 + 0.725), parent=root)
    mantel = w.box("Fire_Mantel", (1.5, 0.42, 0.06), "Wood_Walnut", offset=(0, -0.36, 1.33), parent=root, uv_rotate=True)
    w.bevel(mantel, 0.01, 3)
    corbel = w.box("Fire_Corbels", (0.06, 0.16, 0.12), "Wood_Walnut", offset=(0.6, -0.5, 1.24), parent=root)
    w.mirror(corbel, x=True)

    holder = w.cylinder("Candle_Holders", 0.035, 0.02, "Metal_Brass", offset=(0.55, -0.3, 1.37), segments=16, parent=root)
    w.mirror(holder, x=True)
    candle = w.cylinder("Candles", 0.018, 0.16, "Wax", offset=(0.55, -0.3, 1.46), segments=12, parent=root)
    w.mirror(candle, x=True)
    candle_flame = w.sphere("Candle_Flames", 0.01, "Flame", offset=(0.55, -0.3, 1.555), scale=(1, 1, 2.2), segments=10, parent=root)
    w.mirror(candle_flame, x=True)

    bar = w.box("Grate_Bars", (0.015, 0.25, 0.015), "Metal_Iron", offset=(-0.24, -0.22, 0.14), parent=root)
    w.array(bar, 9, constant=(0.06, 0, 0))
    for s in (-1, 1):
        w.box("Grate_Leg", (0.02, 0.02, 0.12), "Metal_Iron", offset=(s * 0.26, -0.22, 0.08), parent=root)
    w.box("Embers", (0.5, 0.24, 0.02), "Embers", offset=(0, -0.22, 0.155), parent=root)
    w.rod("Log1", (-0.25, -0.3, 0.2), (0.25, -0.17, 0.2), 0.045, "Wood_Walnut", segments=10, parent=root)
    w.rod("Log2", (-0.22, -0.15, 0.2), (0.24, -0.3, 0.21), 0.04, "Wood_Walnut", segments=10, parent=root)
    w.rod("Log3", (-0.15, -0.23, 0.26), (0.12, -0.2, 0.3), 0.035, "Wood_Walnut", segments=10, parent=root)

    w.cylinder("Tools_Base", 0.07, 0.02, "Metal_Iron", offset=(0.82, -0.35, 0.01), segments=16, parent=root)
    w.rod("Tools_Pole", (0.82, -0.35, 0.02), (0.82, -0.35, 0.65), 0.008, "Metal_Iron", parent=root)
    w.rod("Poker", (0.85, -0.35, 0.05), (0.84, -0.33, 0.62), 0.006, "Metal_Iron", parent=root)
    w.sphere("Tools_Knob", 0.018, "Metal_Brass", offset=(0.82, -0.35, 0.66), segments=12, parent=root)

    bones = [("Root", (0, 0, 0), (0, 0, 0.1), None)]
    flame_spots = [(-0.12, -0.22, 0.2, 0.2), (0.0, -0.24, 0.2, 0.3), (0.13, -0.21, 0.2, 0.22)]
    for i, (x, y, z, h) in enumerate(flame_spots):
        bones.append((f"Flame_{i + 1}", (x, y, z), (x, y, z + h), "Root"))
    rig = w.armature("Fireplace", bones, parent=root)
    for i, (x, y, z, h) in enumerate(flame_spots):
        pts = [(0, 0)] + [(0.07 * math.sin(math.pi * t / 10) * (1 - t / 12), h * t / 10) for t in range(1, 10)] + [(0, h)] + \
              [(-0.07 * math.sin(math.pi * t / 10) * (1 - t / 12), h * t / 10) for t in range(9, 0, -1)]
        pts = [(px, pz) for px, pz in pts]
        flames = [w.prism(f"Flame{i + 1}_{k}", pts, 0.01, "Flame", offset=(x, y + 0.005, z), rotation=(0, 0, 60 * k), parent=root)
                  for k in range(2)]
        w.attach(flames, rig, f"Flame_{i + 1}")

    def flicker(phase):
        keys = []
        for f in range(0, 49, 6):
            pose_r, pose_s = {}, {}
            for i in range(3):
                t = (f / 48.0 + phase[i]) * 2 * math.pi
                pose_r[f"Flame_{i + 1}"] = (6 * math.sin(2 * t), 7 * math.sin(t + 1), 0)
                k = 1 + 0.18 * math.sin(3 * t)
                pose_s[f"Flame_{i + 1}"] = (1 - 0.08 * math.sin(3 * t), k, 1 - 0.08 * math.sin(3 * t))
            keys.append((f + 1, pose_r, None, pose_s))
        return keys

    action = w.make_action(rig, "Flicker", flicker((0.0, 0.33, 0.66)))
    rig.animation_data.action = action
    return root, "Environment", (rig, [action])


def build_armchair():
    root = w.empty("Armchair")
    leg = w.box("Chair_Legs", (0.06, 0.06, 0.2), "Wood_Walnut", offset=(0.33, 0.3, 0.1), parent=root)
    w.mirror(leg, x=True, y=True)
    base = w.box("Chair_Base", (0.82, 0.78, 0.18), "Fabric_Red", offset=(0, 0, 0.29), parent=root)
    w.bevel(base, 0.04, 3)
    seat = w.box("Chair_SeatCushion", (0.58, 0.62, 0.14), "Fabric_Red", offset=(0, -0.04, 0.44), parent=root)
    w.bevel(seat, 0.05, 3)
    w.subdivision(seat, 1)
    back = w.box("Chair_Back", (0.78, 0.18, 0.62), "Fabric_Red", offset=(0, 0.3, 0.68), rotation=(-10, 0, 0), parent=root)
    w.bevel(back, 0.07, 3)
    w.subdivision(back, 1)
    arm = w.box("Chair_Arms", (0.13, 0.74, 0.3), "Fabric_Red", offset=(0.345, 0, 0.5), parent=root)
    w.bevel(arm, 0.06, 3)
    w.subdivision(arm, 1)
    w.mirror(arm, x=True)
    blanket = w.box("Chair_Blanket", (0.5, 0.04, 0.4), "Fabric_Cream", offset=(-0.1, 0.18, 0.62), rotation=(-12, 0, 6), parent=root)
    w.bevel(blanket, 0.02, 2)
    w.subdivision(blanket, 1)
    return root, "Environment", None


def build_desk_lamp():
    root = w.empty("DeskLamp")
    w.lathe("Lamp_Base", [(0, 0), (0.09, 0), (0.095, 0.012), (0.085, 0.03), (0.03, 0.04), (0, 0.04)], "Metal_Iron", parent=root)
    w.cylinder("Lamp_Joint1", 0.016, 0.03, "Metal_Brass", rotation=(90, 0, 0), offset=(0, 0, 0.05), segments=12, parent=root)
    w.rod("Lamp_Arm1", (0, 0, 0.05), (0.07, 0, 0.34), 0.007, "Metal_Brass", parent=root)
    w.rod("Lamp_Arm1b", (0, 0.02, 0.05), (0.07, 0.02, 0.34), 0.004, "Metal_Iron", parent=root)
    w.cylinder("Lamp_Joint2", 0.014, 0.04, "Metal_Brass", rotation=(90, 0, 0), offset=(0.07, 0.01, 0.34), segments=12, parent=root)
    w.rod("Lamp_Arm2", (0.07, 0, 0.34), (0.27, 0, 0.38), 0.007, "Metal_Brass", parent=root)
    w.rod("Lamp_Arm2b", (0.07, 0.02, 0.34), (0.27, 0.02, 0.38), 0.004, "Metal_Iron", parent=root)
    shade = w.lathe("Lamp_Shade", [(0.02, 0.0), (0.03, -0.02), (0.06, -0.08), (0.085, -0.12), (0.09, -0.125)],
                    "Enamel_Green", rotation=(0, -30, 0), offset=(0.29, 0.01, 0.39), segments=28, parent=root)
    w.solidify(shade, 0.003)
    w.sphere("Lamp_Bulb", 0.028, "Emissive_Warm", offset=(0.33, 0.01, 0.31), segments=16, parent=root)
    return root, "Environment", None


def build_cuckoo_clock():
    root = w.empty("CuckooClock")
    body = w.box("Clock_Body", (0.34, 0.15, 0.4), "Wood_Walnut", offset=(0, -0.075, 0), parent=root)
    w.bevel(body, 0.006)
    roof = w.box("Clock_Roof", (0.24, 0.24, 0.018), "Wood_Walnut", offset=(0.1, -0.09, 0.27), rotation=(0, 38, 0), parent=root)
    w.mirror(roof, x=True)
    leaf = w.sphere("Clock_RoofLeaves", 0.022, "Wood_Oak", offset=(0.02, -0.21, 0.32), scale=(1, 0.4, 0.6), segments=10, parent=root)
    w.array(leaf, 5, constant=(0.038, 0, -0.03))
    w.mirror(leaf, x=True)
    w.sphere("Clock_TopCarving", 0.035, "Wood_Oak", offset=(0, -0.13, 0.36), scale=(1, 0.5, 1), parent=root)

    w.cylinder("Clock_Face", 0.105, 0.012, "Enamel_Cream", rotation=(90, 0, 0), offset=(0, -0.156, -0.02), segments=36, parent=root)
    w.torus("Clock_FaceRim", 0.105, 0.006, "Metal_Brass", rotation=(90, 0, 0), offset=(0, -0.162, -0.02), parent=root)
    centre = w.empty("Clock_MarkCentre", (0, -0.163, -0.02), parent=root)
    pivot = w.empty("Clock_MarkStep", (0, -0.163, -0.02), parent=root)
    pivot.rotation_euler = (0, math.radians(30), 0)
    mark = w.box("Clock_HourMarks", (0.006, 0.004, 0.02), "Enamel_Black", location=(0, -0.163, -0.02), offset=(0, 0, 0.085), parent=root)
    w.array(mark, 12, offset_object=pivot)

    w.box("Clock_DoorFrame", (0.09, 0.01, 0.1), "Wood_Oak", offset=(0, -0.152, 0.13), parent=root)
    w.box("Clock_DoorHole", (0.07, 0.01, 0.08), "Enamel_Black", offset=(0, -0.153, 0.13), parent=root)

    bones = [
        ("Root", (0, 0, 0), (0, 0, 0.05), None),
        ("Hour", (0, -0.17, -0.02), (0, -0.17, 0.035), "Root"),
        ("Minute", (0, -0.175, -0.02), (0, -0.175, 0.06), "Root"),
        ("Door", (-0.035, -0.16, 0.09), (-0.035, -0.16, 0.17), "Root"),
        ("Bird", (0, -0.1, 0.13), (0, -0.16, 0.13), "Root"),
        ("Pendulum", (0, -0.12, -0.2), (0, -0.12, -0.5), "Root"),
    ]
    rig = w.armature("CuckooClock", bones, parent=root)
    hour = w.box("Clock_HourHand", (0.008, 0.003, 0.055), "Metal_Iron", offset=(0, -0.17, 0.005), parent=root)
    minute = w.box("Clock_MinuteHand", (0.006, 0.003, 0.08), "Metal_Iron", offset=(0, -0.175, 0.02), parent=root)
    hub = w.sphere("Clock_Hub", 0.008, "Metal_Brass", offset=(0, -0.178, -0.02), segments=10, parent=root)
    w.attach([hour], rig, "Hour")
    w.attach([minute, hub], rig, "Minute")
    door = w.box("Clock_Door", (0.07, 0.008, 0.08), "Wood_Oak", offset=(0, -0.162, 0.13), parent=root)
    w.attach([door], rig, "Door")
    bird_parts = [
        w.sphere("Bird_Body", 0.022, "Enamel_Blue", offset=(0, -0.11, 0.125), scale=(0.9, 1.3, 0.9), segments=14, parent=root),
        w.sphere("Bird_Head", 0.016, "Enamel_Blue", offset=(0, -0.14, 0.145), segments=12, parent=root),
        w.cylinder("Bird_Beak", 0.006, 0.02, "Enamel_Orange", radius_top=0.0, rotation=(90, 0, 0), offset=(0, -0.162, 0.145), segments=8, parent=root),
        w.sphere("Bird_Wing", 0.014, "Enamel_Yellow", offset=(0.015, -0.11, 0.128), scale=(0.4, 1.2, 0.7), segments=10, parent=root),
    ]
    w.attach(bird_parts, rig, "Bird")
    pend = [
        w.rod("Pendulum_Rod", (0, -0.12, -0.2), (0, -0.12, -0.46), 0.003, "Metal_Brass", parent=root),
        w.cylinder("Pendulum_Bob", 0.04, 0.006, "Metal_Brass", rotation=(90, 0, 0), offset=(0, -0.12, -0.48), segments=24, parent=root),
        w.sphere("Pendulum_Leaf", 0.02, "Wood_Oak", offset=(0, -0.126, -0.48), scale=(1, 0.3, 1.2), segments=10, parent=root),
    ]
    w.attach(pend, rig, "Pendulum")

    link = w.torus("Chain_Links", 0.006, 0.0015, "Metal_Iron", rotation=(0, 90, 0), offset=(0.07, -0.08, -0.21),
                   major_segments=10, minor_segments=5, parent=root)
    w.array(link, 22, constant=(0, 0, -0.01))
    w.mirror(link, x=True)
    cone = w.lathe("Weights", [(0, 0), (0.012, 0.01), (0.022, 0.03), (0.024, 0.06), (0.02, 0.09), (0.012, 0.11), (0, 0.115)],
                   "Metal_Iron", offset=(0.07, -0.08, -0.55), segments=12, parent=root)
    w.mirror(cone, x=True)

    tick = w.make_action(rig, "Tick", [
        (1, {"Pendulum": (0, -16, 0)}),
        (25, {"Pendulum": (0, 16, 0)}),
        (49, {"Pendulum": (0, -16, 0)}),
    ])
    door_open = {"Door": (0, 0, -105)}
    cuckoo = w.make_action(rig, "Cuckoo", [
        (1, {}),
        (8, door_open),
        (16, door_open, {"Bird": (0, -0.07, 0)}),
        (22, {**door_open, "Bird": (-20, 0, 0)}, {"Bird": (0, -0.07, 0)}),
        (28, door_open, {"Bird": (0, -0.07, 0)}),
        (34, {**door_open, "Bird": (-20, 0, 0)}, {"Bird": (0, -0.07, 0)}),
        (40, door_open, {"Bird": (0, -0.07, 0)}),
        (52, door_open),
        (62, {}),
    ])
    rig.animation_data.action = tick
    return root, "Environment", (rig, [tick, cuckoo])


def build_toymaker():
    root = w.empty("Toymaker")
    bones = [
        ("Root", (0, 0, 0), (0, 0, 0.15), None),
        ("Hips", (0, 0, 0.92), (0, 0, 1.02), "Root"),
        ("Spine", (0, 0, 1.02), (0, 0, 1.22), "Hips"),
        ("Chest", (0, 0, 1.22), (0, 0, 1.42), "Spine"),
        ("Neck", (0, 0, 1.42), (0, 0, 1.5), "Chest"),
        ("Head", (0, 0, 1.5), (0, 0, 1.75), "Neck"),
    ]
    for s, side in ((1, "L"), (-1, "R")):
        bones += [
            (f"UpperArm.{side}", (s * 0.22, 0, 1.4), (s * 0.27, 0, 1.12), "Chest"),
            (f"Forearm.{side}", (s * 0.27, 0, 1.12), (s * 0.3, -0.03, 0.88), f"UpperArm.{side}"),
            (f"Hand.{side}", (s * 0.3, -0.03, 0.88), (s * 0.31, -0.04, 0.78), f"Forearm.{side}"),
            (f"Thigh.{side}", (s * 0.1, 0, 0.92), (s * 0.1, 0, 0.5), "Hips"),
            (f"Shin.{side}", (s * 0.1, 0, 0.5), (s * 0.1, 0, 0.1), f"Thigh.{side}"),
            (f"Foot.{side}", (s * 0.1, 0, 0.1), (s * 0.1, -0.12, 0.05), f"Shin.{side}"),
        ]
    rig = w.armature("Toymaker", bones, parent=root)
    att = lambda bone, *objs: w.attach(list(objs), rig, bone)

    for s, side in ((1, "L"), (-1, "R")):
        att(f"Thigh.{side}", w.rod(f"Thigh.{side}_Mesh", (s * 0.1, 0, 0.94), (s * 0.1, 0, 0.5), 0.078, "Fabric_Brown",
                                   radius_end=0.068, segments=16, parent=root))
        att(f"Shin.{side}", w.rod(f"Shin.{side}_Mesh", (s * 0.1, 0, 0.52), (s * 0.1, 0, 0.1), 0.066, "Fabric_Brown",
                                  radius_end=0.056, segments=16, parent=root))
        shoe = w.box(f"Shoe.{side}", (0.11, 0.25, 0.08), "Leather", offset=(s * 0.1, -0.05, 0.045), parent=root)
        w.bevel(shoe, 0.03, 3)
        w.subdivision(shoe, 1)
        att(f"Foot.{side}", shoe)

    pelvis = w.box("Pelvis", (0.34, 0.24, 0.16), "Fabric_Brown", offset=(0, 0, 0.95), parent=root)
    w.bevel(pelvis, 0.06, 3)
    skirt = w.lathe("Coat_Skirt", [(0.24, 0.74), (0.215, 0.9), (0.2, 1.03)], "Fabric_Navy", segments=28, parent=root)
    w.solidify(skirt, 0.012)
    att("Hips", pelvis, skirt)
    waist = w.lathe("Coat_Waist", [(0, 1.0), (0.2, 1.0), (0.205, 1.12), (0.21, 1.23), (0, 1.23)], "Fabric_Navy", segments=28, parent=root)
    buttons = w.sphere("Coat_Buttons", 0.012, "Metal_Brass", offset=(0.07, -0.205, 1.35), scale=(1, 0.5, 1), segments=10, parent=root)
    w.array(buttons, 4, constant=(0, 0, -0.09))
    w.mirror(buttons, x=True)
    apron = w.curved_panel("Apron", [(0.258, 0.76), (0.235, 0.9), (0.221, 1.03), (0.224, 1.15), (0.227, 1.25), (0.22, 1.33)],
                           75, "Leather", parent=root)
    w.solidify(apron, 0.008)
    pocket = w.curved_panel("Apron_Pocket", [(0.244, 0.86), (0.236, 0.97)], 36, "Leather", segments=6, parent=root)
    w.solidify(pocket, 0.006)
    pencil = w.cylinder("Apron_Pencil", 0.006, 0.14, "Enamel_Yellow", rotation=(0, 15, 0), offset=(0.04, -0.248, 0.98), segments=6, parent=root)
    att("Spine", waist, buttons, apron, pocket, pencil)
    chest = w.lathe("Coat_Chest", [(0, 1.22), (0.21, 1.22), (0.2, 1.36), (0.15, 1.44), (0, 1.45)], "Fabric_Navy", segments=28, parent=root)
    shoulders = w.sphere("Coat_Shoulders", 0.075, "Fabric_Navy", offset=(0.2, 0, 1.37), segments=16, parent=root)
    w.mirror(shoulders, x=True)
    strap = w.box("Apron_Strap", (0.03, 0.01, 0.16), "Leather", offset=(0.1, -0.175, 1.39), rotation=(28, -12, 0), parent=root)
    w.mirror(strap, x=True)
    collar = w.torus("Collar", 0.075, 0.025, "Fabric_Cream", offset=(0, 0, 1.44), parent=root)
    att("Chest", chest, shoulders, strap, collar)
    att("Neck", w.cylinder("Neck_Mesh", 0.055, 0.12, "Skin", offset=(0, 0, 1.48), segments=16, parent=root))

    head = [
        w.sphere("Head_Mesh", 0.13, "Skin", offset=(0, 0, 1.62), scale=(1, 0.97, 1.1), segments=28, parent=root),
        w.sphere("Nose", 0.034, "Skin", offset=(0, -0.13, 1.6), scale=(0.9, 1.2, 0.95), segments=16, parent=root),
    ]
    ear = w.sphere("Ears", 0.035, "Skin", offset=(0.128, 0.0, 1.62), scale=(0.4, 0.8, 1.1), segments=12, parent=root)
    w.mirror(ear, x=True)
    eye = w.sphere("Eyes", 0.021, "Enamel_White", offset=(0.045, -0.107, 1.655), segments=14, parent=root)
    w.mirror(eye, x=True)
    pupil = w.sphere("Pupils", 0.011, "Enamel_Black", offset=(0.045, -0.125, 1.656), segments=10, parent=root)
    w.mirror(pupil, x=True)
    brow = w.box("Eyebrows", (0.05, 0.02, 0.014), "Hair_White", offset=(0.048, -0.112, 1.69), rotation=(0, 10, 0), parent=root)
    w.bevel(brow, 0.006)
    w.mirror(brow, x=True)
    lens = w.torus("Glasses_Lenses", 0.03, 0.003, "Metal_Brass", rotation=(90, 0, 0), offset=(0.048, -0.135, 1.655),
                   major_segments=20, minor_segments=6, parent=root)
    w.mirror(lens, x=True)
    bridge = w.rod("Glasses_Bridge", (-0.018, -0.137, 1.66), (0.018, -0.137, 1.66), 0.0025, "Metal_Brass", parent=root)
    temple = w.rod("Glasses_Temples", (0.078, -0.135, 1.655), (0.125, -0.02, 1.645), 0.0025, "Metal_Brass", parent=root)
    w.mirror(temple, x=True)
    moustache = w.sphere("Moustache", 0.04, "Hair_White", offset=(0.035, -0.13, 1.565), scale=(1.2, 0.5, 0.45), rotation=(0, -15, 0),
                         segments=14, parent=root)
    w.mirror(moustache, x=True)
    beard = w.sphere("Beard", 0.1, "Hair_White", offset=(0, -0.075, 1.5), scale=(1.05, 0.7, 0.85), segments=20, parent=root)
    hair = w.sphere("Hair_Sides", 0.06, "Hair_White", offset=(0.1, 0.05, 1.65), scale=(0.7, 1.1, 0.9), segments=14, parent=root)
    w.mirror(hair, x=True)
    hair_back = w.sphere("Hair_Back", 0.1, "Hair_White", offset=(0, 0.07, 1.6), scale=(1.1, 0.6, 0.8), segments=16, parent=root)
    w.subdivision(head[0], 1)
    att("Head", *head, ear, eye, pupil, brow, lens, bridge, temple, moustache, beard, hair, hair_back)

    for s, side in ((1, "L"), (-1, "R")):
        att(f"UpperArm.{side}", w.rod(f"Sleeve.{side}", (s * 0.22, 0, 1.41), (s * 0.27, 0, 1.12), 0.062, "Fabric_Navy",
                                      radius_end=0.056, segments=16, parent=root))
        fore = w.rod(f"Forearm.{side}_Mesh", (s * 0.27, 0, 1.13), (s * 0.3, -0.03, 0.9), 0.056, "Fabric_Navy",
                     radius_end=0.05, segments=16, parent=root)
        cuff = w.torus(f"Cuff.{side}", 0.05, 0.014, "Fabric_Cream", offset=(s * 0.299, -0.028, 0.905), parent=root)
        att(f"Forearm.{side}", fore, cuff)
        hand = w.box(f"Hand.{side}_Mesh", (0.06, 0.09, 0.11), "Skin", offset=(s * 0.305, -0.035, 0.83), parent=root)
        w.bevel(hand, 0.025, 3)
        w.subdivision(hand, 1)
        thumb = w.sphere(f"Thumb.{side}", 0.02, "Skin", offset=(s * 0.29, -0.08, 0.86), scale=(0.8, 0.8, 1.5), segments=10, parent=root)
        att(f"Hand.{side}", hand, thumb)

    idle = w.make_action(rig, "Idle", [
        (1, {}),
        (25, {"Chest": (-2, 0, 0), "Head": (0, 0, 4), "UpperArm.L": (0, -3, 0), "UpperArm.R": (0, 3, 0)}),
        (49, {"Chest": (1, 0, 0), "Head": (3, 0, 0)}),
        (73, {"Chest": (-2, 0, 0), "Head": (0, 0, -4), "UpperArm.L": (0, -2, 0), "UpperArm.R": (0, 2, 0)}),
        (97, {}),
    ])
    talk_arm = {"UpperArm.R": (-30, 8, 0), "Forearm.R": (-45, 0, 0), "UpperArm.L": (-12, -6, 0), "Forearm.L": (-25, 0, 0)}
    talk = w.make_action(rig, "Talk", [
        (1, {**talk_arm, "Head": (0, 0, 0)}),
        (13, {**talk_arm, "Forearm.R": (-65, 0, 10), "Head": (8, 0, 5), "Chest": (-3, 0, 0)}),
        (25, {**talk_arm, "Forearm.R": (-30, 0, -10), "Head": (-3, 0, -4), "Hand.R": (0, 0, 20)}),
        (37, {**talk_arm, "Forearm.R": (-55, 0, 0), "Forearm.L": (-45, 0, 0), "Head": (6, 0, 3)}),
        (49, {**talk_arm, "Head": (0, 0, 0)}),
    ])
    raised = {"UpperArm.R": (0, 140, 0), "Forearm.R": (0, 10, 0), "Head": (0, 0, -6)}
    wave = w.make_action(rig, "Wave", [
        (1, {}),
        (9, raised),
        (15, {**raised, "Forearm.R": (0, 35, 0)}),
        (21, {**raised, "Forearm.R": (0, -15, 0)}),
        (27, {**raised, "Forearm.R": (0, 35, 0)}),
        (33, {**raised, "Forearm.R": (0, -15, 0)}),
        (41, raised),
        (49, {}),
    ])
    pointing = {"UpperArm.R": (-80, 12, 0), "Forearm.R": (-8, 0, 0), "Hand.R": (-5, 0, 0), "Head": (8, 0, -10), "Chest": (-4, 0, -6)}
    point = w.make_action(rig, "Point", [
        (1, {}),
        (12, pointing),
        (36, {**pointing, "Forearm.R": (-12, 0, 0)}),
    ])
    up = {"UpperArm.L": (0, -150, 0), "UpperArm.R": (0, 150, 0), "Forearm.L": (0, -15, 0), "Forearm.R": (0, 15, 0),
          "Head": (-12, 0, 0), "Chest": (-5, 0, 0)}
    celebrate = w.make_action(rig, "Celebrate", [
        (1, {}),
        (8, up),
        (14, up, {"Root": (0, 0, 0.09)}),
        (20, up),
        (26, up, {"Root": (0, 0, 0.09)}),
        (32, up),
        (48, {}),
    ])
    rig.animation_data.action = idle
    return root, "Characters", (rig, [idle, talk, wave, point, celebrate])


BUILDERS = {
    "WorkshopRoom": build_workshop_room,
    "Workbench": build_workbench,
    "ToolWall": build_tool_wall,
    "ShelfUnit": build_shelf_unit,
    "Fireplace": build_fireplace,
    "Armchair": build_armchair,
    "DeskLamp": build_desk_lamp,
    "CuckooClock": build_cuckoo_clock,
    "Toymaker": build_toymaker,
}

NO_STUDIO = {"WorkshopRoom"}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render = "--no-render" not in args
    names = [a for a in args if not a.startswith("--")] or list(BUILDERS)
    os.makedirs(RENDER_DIR, exist_ok=True)
    w.write_material_json()
    for name in names:
        w.reset()
        root, category, anim = BUILDERS[name]()
        objects = w.asset_objects(root)
        tris = w.triangle_count(objects)
        w.export_fbx(root, category, animated=anim is not None)
        if render and name not in NO_STUDIO:
            w.studio(objects)
            if anim is not None:
                rig, actions = anim
                rig.animation_data.action = actions[0]
                bpy_scene_frame(1)
            w.render_still(os.path.join(RENDER_DIR, f"{name}.png"))
            if anim is not None:
                rig, actions = anim
                last = w.queue_actions_for_preview(rig, actions)
                w.render_video(os.path.join(RENDER_DIR, f"{name}_animations.mp4"), 1, last)
        w.bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, f"{name}.blend"))
        print(f"ASSET {name:<14} {tris:>6} tris  anims: {[a.name for a in anim[1]] if anim else '-'}")


def bpy_scene_frame(frame):
    w.bpy.context.scene.frame_set(frame)


if __name__ == "__main__":
    main()
