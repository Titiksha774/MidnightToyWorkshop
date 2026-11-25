import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toy_common as t


def build_workbench():
    root = t.empty("Workbench")
    top = t.box("Workbench_Top", (1.6, 0.8, 0.06), offset=(0, 0, 0.87), color="wood_light", parent=root)
    t.bevel(top, 0.008)

    leg = t.box("Workbench_Legs", (0.07, 0.07, 0.84), offset=(0.72, 0.32, 0.42), color="wood_dark", parent=root)
    t.mirror(leg, x=True, y=True)
    t.bevel(leg, 0.006)

    shelf = t.box("Workbench_Shelf", (1.44, 0.64, 0.03), offset=(0, 0, 0.22), color="wood_dark", parent=root)
    t.bevel(shelf, 0.005)
    return root, "Workshop"


def build_brick_wall():
    root = t.empty("BrickWall")
    length, height, depth, gap = 0.4, 0.15, 0.2, 0.02
    start_x = -1.5 + length / 2
    brick_a = t.box("BrickA", (length, depth, height), offset=(start_x, 0, height / 2), color="brick")
    brick_b = t.box("BrickB", (length, depth, height),
                    offset=(start_x + (length + gap) / 2, 0, height * 1.5 + gap), color="brick_alt")
    bricks = t.join("BrickWall_Bricks", [brick_a, brick_b], parent=root)
    t.bevel(bricks, 0.015)
    t.array(bricks, 7, constant=(length + gap, 0, 0))
    t.array(bricks, 7, constant=(0, 0, 2 * (height + gap)))

    t.box("BrickWall_Mortar", (3.15, 0.14, 2.38), offset=(0.08, 0.04, 1.19), color="mortar", parent=root)
    return root, "Workshop"


def build_floor_boards():
    root = t.empty("FloorBoards")
    width, length, thick = 0.18, 4.0, 0.025
    plank_a = t.box("PlankA", (width, length, thick), offset=(-2 + width / 2, 0, thick / 2), color="floor")
    plank_b = t.box("PlankB", (width, length, thick), offset=(-2 + width * 1.5 + 0.004, 0, thick / 2), color="floor_alt")
    planks = t.join("FloorBoards_Planks", [plank_a, plank_b], parent=root)
    t.bevel(planks, 0.004, segments=1)
    t.array(planks, 11, constant=(2 * (width + 0.004), 0, 0))
    return root, "Workshop"


def build_desk_lamp():
    root = t.empty("DeskLamp")
    base = t.cylinder("DeskLamp_Base", 0.08, 0.025, offset=(0, 0, 0.0125), color="lamp_green", parent=root)
    t.bevel(base, 0.006)
    t.rod("DeskLamp_ArmLower", (0, 0, 0.02), (0.06, 0, 0.32), 0.008, parent=root)
    t.sphere("DeskLamp_Joint", 0.016, location=(0.06, 0, 0.32), color="metal", parent=root)
    t.rod("DeskLamp_ArmUpper", (0.06, 0, 0.32), (0.25, 0, 0.36), 0.008, parent=root)

    shade = t.cylinder("DeskLamp_Shade", 0.075, 0.11, radius_top=0.025, rotation=(0, -35, 0),
                       location=(0.29, 0, 0.32), segments=16, color="lamp_green", parent=root)
    t.subdivision(shade, levels=2)
    t.sphere("DeskLamp_Bulb", 0.026, location=(0.31, 0, 0.29), color="bulb", parent=root)
    return root, "Workshop"


def build_turntable():
    root = t.empty("Turntable")
    base = t.cylinder("Turntable_Base", 0.17, 0.03, offset=(0, 0, 0.015), segments=32, color="wood_dark", parent=root)
    t.bevel(base, 0.008)
    plate = t.cylinder("Turntable_Plate", 0.155, 0.018, location=(0, 0, 0.039), segments=32, color="red", parent=root)
    t.bevel(plate, 0.005, segments=3)
    knob = t.sphere("Turntable_Knob", 0.012, location=(0, 0, 0.05), color="gold", parent=plate)
    knob.location = (0, 0, 0.011)
    return root, "Workshop"


def build_parts_tray():
    root = t.empty("PartsTray")
    w, d, h, wall = 0.42, 0.26, 0.04, 0.008
    pieces = [
        t.box("Bottom", (w, d, wall), offset=(0, 0, wall / 2), color="wood_light"),
        t.box("WallFront", (w, wall, h), offset=(0, -d / 2 + wall / 2, h / 2), color="wood_light"),
        t.box("WallBack", (w, wall, h), offset=(0, d / 2 - wall / 2, h / 2), color="wood_light"),
        t.box("WallLeft", (wall, d, h), offset=(-w / 2 + wall / 2, 0, h / 2), color="wood_light"),
        t.box("WallRight", (wall, d, h), offset=(w / 2 - wall / 2, 0, h / 2), color="wood_light"),
    ]
    tray = t.join("PartsTray_Box", pieces, parent=root)
    t.bevel(tray, 0.002, segments=1)
    divider = t.box("PartsTray_Dividers", (0.006, d - 2 * wall, h * 0.85),
                    offset=(-w / 2 + w / 4, 0, h * 0.85 / 2), color="wood_dark", parent=root)
    t.array(divider, 3, constant=(w / 4, 0, 0))
    return root, "Workshop"


def build_town_base():
    root = t.empty("TownBase")
    board = t.box("TownBase_Board", (1.0, 0.62, 0.02), offset=(0, 0, 0.01), color="wood_dark", parent=root)
    t.bevel(board, 0.006)
    grass = t.box("TownBase_Grass", (0.97, 0.59, 0.01), offset=(0, 0, 0.025), color="grass", parent=root)
    t.bevel(grass, 0.003, segments=1)
    return root, "Town"


def build_train_track():
    root = t.empty("TrainTrack")
    oval = t.oval_curve("TrackPath", 0.42, 0.25)
    oval.parent = root

    sleepers = t.box("TrainTrack_Sleepers", (0.012, 0.12, 0.006), offset=(0, 0, 0.003), color="wood_dark", parent=root)
    t.array(sleepers, 0, relative=(3.0, 0, 0), fit_curve=oval)
    t.curve_deform(sleepers, oval)

    rail_a = t.box("RailA", (0.02, 0.008, 0.008), offset=(0, -0.045, 0.01), color="rail")
    rail_b = t.box("RailB", (0.02, 0.008, 0.008), offset=(0, 0.045, 0.01), color="rail")
    rails = t.join("TrainTrack_Rails", [rail_a, rail_b], parent=root)
    t.array(rails, 0, relative=(1.0, 0, 0), fit_curve=oval, merge=True)
    t.curve_deform(rails, oval)
    return root, "Town"


def build_picket_fence():
    root = t.empty("PicketFence")
    post = t.box("PicketFence_Posts", (0.012, 0.012, 0.06), offset=(0, 0, 0.03), color="white", parent=root)
    t.bevel(post, 0.002, segments=1)
    t.array(post, 10, relative=(2.5, 0, 0))
    length = 0.012 * 2.5 * 9 + 0.012
    for name, z in (("PicketFence_RailLower", 0.02), ("PicketFence_RailUpper", 0.045)):
        rail = t.box(name, (length, 0.006, 0.008), offset=(length / 2 - 0.006, 0.008, z), color="white", parent=root)
        t.bevel(rail, 0.0015, segments=1)
    return root, "Town"


def build_toy_train():
    s = 0.05
    root = t.empty("ToyTrain")
    body = t.box("Train_Body", (4 * s, 1.6 * s, 1 * s), location=(0, 0, 1.1 * s), color="train_blue", parent=root)
    t.bevel(body, 0.004)
    cabin = t.box("Train_Cabin", (1.2 * s, 1.4 * s, 1.4 * s), location=(1 * s, 0, 2.3 * s), color="yellow", parent=root)
    t.bevel(cabin, 0.003)
    roof = t.box("Train_Roof", (1.5 * s, 1.6 * s, 0.15 * s), location=(1 * s, 0, 3.05 * s), color="red", parent=root)
    t.bevel(roof, 0.002)
    chimney = t.cylinder("Train_Chimney", 0.011, 0.035, location=(-1.2 * s, 0, 1.6 * s + 0.0175),
                         segments=16, color="red", parent=root)
    t.bevel(chimney, 0.002)
    bumper = t.box("Train_Bumper", (0.01, 1.7 * s, 0.4 * s), location=(-2.1 * s, 0, 0.7 * s), color="red", parent=root)
    t.bevel(bumper, 0.002)

    radius, thickness = 0.45 * s, 0.27 * s
    for name, x in (("Train_Wheels_Front", -1.2 * s), ("Train_Wheels_Rear", 1.2 * s)):
        centre = (x, 0, radius)
        wheel = t.cylinder("Wheel", radius, thickness, location=centre, rotation=(90, 0, 0),
                           offset=(0, -0.9 * s, 0), segments=20, color="black")
        hub = t.cylinder("Hub", radius * 0.4, thickness * 1.2, location=centre, rotation=(90, 0, 0),
                         offset=(0, -0.9 * s, 0), segments=12, color="red")
        axle = t.cylinder("Axle", 0.003, 0.9 * s, location=centre, rotation=(90, 0, 0),
                          offset=(0, -0.45 * s, 0), segments=8, color="metal")
        wheel_set = t.join(name, [wheel, hub, axle], location=centre, parent=root)
        t.mirror(wheel_set, x=False, y=True)
    return root, "Toys"


def build_wind_up_key():
    root = t.empty("WindUpKey")
    t.cylinder("WindUpKey_Shaft", 0.004, 0.035, rotation=(0, 90, 0), offset=(0.0175, 0, 0),
               segments=10, color="gold", parent=root)
    lobe = t.torus("WindUpKey_Handle", 0.011, 0.0035, rotation=(90, 0, 0), offset=(0.042, 0, 0.011),
                   color="gold", parent=root)
    t.mirror(lobe, x=False, z=True)
    return root, "Toys"


def build_toymaker():
    root = t.empty("Toymaker")

    robe = t.cylinder("Toymaker_Body", 0.27, 0.9, radius_top=0.19, offset=(0, 0, 0.45), segments=32,
                      color="navy", parent=root, smooth=True)
    t.bevel(robe, 0.03, segments=3)
    apron = t.box("Toymaker_Apron", (0.26, 0.02, 0.5), offset=(0, 0, 0.25), color="apron", parent=root)
    apron.location = (0, -0.272, 0.12)
    apron.rotation_euler = (-0.085, 0, 0)
    t.bevel(apron, 0.008)

    head_center = (0, 0, 1.08)
    head = t.sphere("Head", 0.16, offset=head_center, segments=20, color="skin")
    nose = t.sphere("Nose", 0.035, offset=(0, -0.155, 1.07), segments=12, color="skin")
    beard = t.sphere("Beard", 0.12, offset=(0, -0.08, 0.98), scale=(1.0, 0.7, 0.8), segments=16, color="white")
    eye_l = t.sphere("EyeL", 0.018, offset=(0.055, -0.14, 1.12), segments=10, color="black")
    eye_r = t.sphere("EyeR", 0.018, offset=(-0.055, -0.14, 1.12), segments=10, color="black")
    brim = t.cylinder("HatBrim", 0.19, 0.03, offset=(0, 0, 1.2), segments=20, color="hat_brown")
    crown = t.cylinder("HatTop", 0.12, 0.14, offset=(0, 0, 1.285), segments=20, color="hat_brown")
    head_obj = t.join("Toymaker_Head", [head, nose, beard, eye_l, eye_r, brim, crown],
                      location=head_center, parent=root, smooth=True)
    t.subdivision(head_obj, levels=1)

    shoulder = (0.22, 0, 0.84)
    ball = t.sphere("Shoulder", 0.06, offset=shoulder, segments=16, color="navy")
    sleeve = t.rod("Arm", shoulder, (0.31, -0.06, 0.5), 0.05, segments=16, color="navy")
    hand = t.sphere("Hand", 0.055, offset=(0.315, -0.065, 0.46), segments=16, color="skin")
    arms = t.join("Toymaker_Arms", [ball, sleeve, hand], parent=root, smooth=True)
    t.mirror(arms, x=True, merge=False)
    return root, "Characters"


BUILDERS = {
    "Workbench": build_workbench,
    "BrickWall": build_brick_wall,
    "FloorBoards": build_floor_boards,
    "DeskLamp": build_desk_lamp,
    "Turntable": build_turntable,
    "PartsTray": build_parts_tray,
    "TownBase": build_town_base,
    "TrainTrack": build_train_track,
    "PicketFence": build_picket_fence,
    "ToyTrain": build_toy_train,
    "WindUpKey": build_wind_up_key,
    "Toymaker": build_toymaker,
}


def main():
    names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDERS)
    total = 0
    for name in names:
        t.reset()
        root, category = BUILDERS[name]()
        total += t.finish(root, category)
    print(f"TOTAL {total} tris for {len(names)} assets")


if __name__ == "__main__":
    main()
