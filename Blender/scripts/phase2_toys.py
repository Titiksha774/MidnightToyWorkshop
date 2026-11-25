import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

import workshop_lib as w

OUT_DIR = os.path.join(w.BLENDER_DIR, "Phase2")
RENDER_DIR = os.path.join(OUT_DIR, "Renders")

TOWN_TOP = 0.765
TRACK_A, TRACK_B = 0.44, 0.22
RAIL_GAP = 0.042
RAIL_TOP = TOWN_TOP + 0.012


def frames(first, last, step):
    return range(first, last + 1, step)


def ellipse(a, b, n=128, offset=0.0, z=0.0):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = a * math.cos(t), b * math.sin(t)
        nx, ny = b * math.cos(t), a * math.sin(t)
        length = math.hypot(nx, ny)
        pts.append((x + offset * nx / length, y + offset * ny / length, z))
    return pts


def ring_strip(name, a, b, inner, outer, z, material, parent, n=128):
    import bmesh
    bm = bmesh.new()
    vin = [bm.verts.new(p) for p in ellipse(a, b, n, -inner, z)]
    vout = [bm.verts.new(p) for p in ellipse(a, b, n, outer, z)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([vin[i], vin[j], vout[j], vout[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return w._finish_mesh(name, bm, material, (0, 0, 0), parent, False)


def star_points(r_out, r_in, n=5, start=90):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(start + 180 * i / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def puff(i):
    return lambda t: (
        (0, 0.02 * t, 0.055 * t),
        0.03 + 1.2 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6,
    )


def build_steam_train():
    root = w.empty("SteamTrain")
    AXLES = (-0.06, 0.0, 0.06)
    WR, WX, RC = 0.022, 0.044, 0.011
    BOILER_Z, CHIMNEY = 0.086, (0, -0.105)

    bones = [("Root", (0, 0, 0), (0, 0, 0.03), None), ("Body", (0, 0, 0.05), (0, 0, 0.1), "Root")]
    for i, y in enumerate(AXLES):
        bones.append((f"Axle_{i + 1}", (-0.05, y, WR), (0.05, y, WR), "Root"))
    bones += [("Rods", (0, 0, WR + RC), (0, 0, WR + RC + 0.02), "Root"),
              ("Piston", (0, -0.08, 0.032), (0, -0.06, 0.032), "Root"),
              ("Key", (0, 0.13, 0.095), (0, 0.16, 0.095), "Body")]
    for i in range(3):
        bones.append((f"Smoke_{i + 1}", (CHIMNEY[0], CHIMNEY[1], 0.168), (CHIMNEY[0], CHIMNEY[1], 0.19), "Body"))
    rig = w.armature("SteamTrain", bones, parent=root)

    body = []
    add = body.append
    frames_obj = w.box("Frames", (0.006, 0.2, 0.022), "Enamel_Black", offset=(0.032, 0, 0.03), parent=root)
    w.mirror(frames_obj)
    plate = w.box("Footplate", (0.114, 0.272, 0.007), "Enamel_Black", offset=(0, -0.005, 0.0505), parent=root)
    w.bevel(plate, 0.0015)
    add(plate)
    lining = w.box("Footplate_Lining", (0.002, 0.272, 0.004), "Enamel_Yellow", offset=(0.0575, -0.005, 0.0505), parent=root)
    w.mirror(lining)
    add(lining)

    boiler = w.cylinder("Boiler", 0.032, 0.15, "Enamel_Green", rotation=(90, 0, 0), offset=(0, -0.055, BOILER_Z),
                        segments=32, parent=root)
    add(boiler)
    bands = w.torus("Boiler_Bands", 0.0325, 0.0022, "Metal_Brass", rotation=(90, 0, 0), offset=(0, -0.1, BOILER_Z),
                    major_segments=32, minor_segments=6, parent=root)
    w.array(bands, 3, constant=(0, 0.045, 0))
    add(bands)
    add(w.cylinder("Smokebox", 0.034, 0.03, "Enamel_Black", rotation=(90, 0, 0), offset=(0, -0.12, BOILER_Z),
                   segments=32, parent=root))
    add(w.cylinder("Smokebox_Door", 0.026, 0.004, "Metal_Iron", rotation=(90, 0, 0), offset=(0, -0.136, BOILER_Z),
                   segments=28, parent=root))
    add(w.sphere("Smokebox_Handle", 0.004, "Metal_Brass", offset=(0, -0.139, BOILER_Z), segments=10, parent=root))
    add(w.lathe("Chimney", [(0, 0), (0.012, 0), (0.0105, 0.034), (0.016, 0.044), (0.017, 0.05), (0.013, 0.05),
                            (0.013, 0.046), (0, 0.046)], "Enamel_Black", offset=(CHIMNEY[0], CHIMNEY[1], 0.112), parent=root))
    add(w.torus("Chimney_Rim", 0.0165, 0.002, "Metal_Brass", offset=(CHIMNEY[0], CHIMNEY[1], 0.161), minor_segments=6,
                parent=root))
    add(w.lathe("Dome", [(0, 0), (0.013, 0), (0.013, 0.008), (0.011, 0.016), (0.006, 0.021), (0, 0.022)],
                "Metal_Brass", offset=(0, -0.045, 0.112), parent=root))
    add(w.cylinder("Whistle", 0.003, 0.016, "Metal_Brass", offset=(0, 0.008, 0.124), segments=10, parent=root))
    add(w.sphere("Whistle_Top", 0.0045, "Metal_Brass", offset=(0, 0.008, 0.133), segments=10, parent=root))

    cab = w.box("Cab", (0.104, 0.085, 0.07), "Enamel_Green", offset=(0, 0.065, 0.089), parent=root)
    w.bevel(cab, 0.002)
    add(cab)
    side_window = w.box("Cab_SideWindows", (0.002, 0.034, 0.026), "Enamel_Black", offset=(0.0525, 0.062, 0.106), parent=root)
    w.mirror(side_window)
    add(side_window)
    spectacle = w.cylinder("Cab_FrontWindows", 0.0085, 0.002, "Enamel_Black", rotation=(90, 0, 0),
                           offset=(0.028, 0.0215, 0.108), segments=16, parent=root)
    w.mirror(spectacle)
    add(spectacle)
    window_rim = w.torus("Cab_WindowRims", 0.0088, 0.0012, "Metal_Brass", rotation=(90, 0, 0), offset=(0.028, 0.021, 0.108),
                         major_segments=16, minor_segments=4, parent=root)
    w.mirror(window_rim)
    add(window_rim)
    roof = w.box("Cab_Roof", (0.118, 0.105, 0.006), "Enamel_Black", offset=(0, 0.066, 0.128), parent=root)
    w.bevel(roof, 0.0025)
    add(roof)
    plate_obj = w.box("Cab_NamePlates", (0.0015, 0.032, 0.01), "Metal_Brass", offset=(0.0525, 0.065, 0.074), parent=root)
    w.mirror(plate_obj)
    add(plate_obj)
    add(w.box("Bunker", (0.1, 0.022, 0.03), "Enamel_Black", offset=(0, 0.115, 0.068), parent=root))
    for k, (x, y) in enumerate(((-0.02, 0.112), (0.0, 0.118), (0.02, 0.113), (-0.008, 0.108), (0.012, 0.121))):
        add(w.sphere(f"Coal{k}", 0.008, "Enamel_Black", offset=(x, y, 0.084), scale=(1, 1, 0.6), segments=8, parent=root))

    for side, y in (("Front", -0.138), ("Rear", 0.13)):
        add(w.box(f"BufferBeam_{side}", (0.112, 0.008, 0.016), "Enamel_Red", offset=(0, y, 0.043), parent=root))
        s = -1 if side == "Front" else 1
        buffer = w.cylinder(f"Buffers_{side}", 0.0045, 0.012, "Metal_Iron", rotation=(90, 0, 0),
                            offset=(0.035, y + s * 0.009, 0.043), segments=12, parent=root)
        w.mirror(buffer)
        add(buffer)
        head = w.cylinder(f"BufferHeads_{side}", 0.0075, 0.002, "Metal_Iron", rotation=(90, 0, 0),
                          offset=(0.035, y + s * 0.016, 0.043), segments=16, parent=root)
        w.mirror(head)
        add(head)
    bar = w.box("Cowcatcher_Bars", (0.004, 0.004, 0.032), "Metal_Iron", offset=(-0.04, -0.148, 0.022), rotation=(-40, 0, 0),
                parent=root)
    w.array(bar, 9, constant=(0.01, 0, 0))
    add(bar)
    add(w.box("Cowcatcher_Rail", (0.092, 0.004, 0.004), "Metal_Iron", offset=(0, -0.157, 0.01), parent=root))
    lamp = w.cylinder("Lamps", 0.006, 0.012, "Enamel_Black", offset=(0.028, -0.13, 0.06), segments=12, parent=root)
    w.mirror(lamp)
    add(lamp)
    lens = w.sphere("Lamp_Lenses", 0.0045, "Emissive_Warm", offset=(0.028, -0.136, 0.061), segments=10, parent=root)
    w.mirror(lens)
    add(lens)
    w.attach(body, rig, "Body")
    w.attach([frames_obj], rig, "Root")

    for i, y in enumerate(AXLES):
        centre = (0, y, WR)
        parts = [
            w.cylinder(f"Wheel{i + 1}", WR - 0.002, 0.007, "Enamel_Red", location=centre, offset=(WX, 0, 0),
                       rotation=(0, 90, 0), segments=28, parent=root),
            w.torus(f"Wheel{i + 1}_Tyre", WR - 0.0015, 0.0025, "Metal_Iron", location=centre, offset=(WX, 0, 0),
                    rotation=(0, 90, 0), major_segments=28, minor_segments=6, parent=root),
            w.cylinder(f"Wheel{i + 1}_Hub", 0.0055, 0.011, "Metal_Brass", location=centre, offset=(WX + 0.001, 0, 0),
                       rotation=(0, 90, 0), segments=12, parent=root),
            w.cylinder(f"Wheel{i + 1}_CrankPin", 0.0022, 0.012, "Metal_Brass", location=centre,
                       offset=(WX + 0.004, 0, RC), rotation=(0, 90, 0), segments=8, parent=root),
        ]
        spoke = w.box(f"Wheel{i + 1}_Spokes", (0.002, 0.0028, WR * 0.78), "Enamel_Black", location=centre,
                      offset=(WX + 0.0036, 0, WR * 0.42), parent=root)
        w.array_around(spoke, 8, "X")
        parts.append(spoke)
        for p in parts:
            w.mirror(p)
        w.attach(parts, rig, f"Axle_{i + 1}")

    rods = w.box("CouplingRods", (0.003, 0.13, 0.005), "Metal_Iron", location=(0, 0, WR + RC), offset=(WX + 0.009, 0, 0),
                 parent=root)
    w.mirror(rods)
    w.attach([rods], rig, "Rods")
    cylinders = w.cylinder("Cylinders", 0.011, 0.03, "Enamel_Black", rotation=(90, 0, 0), offset=(0.05, -0.105, 0.032),
                           segments=16, parent=root)
    w.mirror(cylinders)
    w.attach([cylinders], rig, "Root")
    piston = w.cylinder("PistonRods", 0.0018, 0.032, "Metal_Iron", rotation=(90, 0, 0), offset=(0.052, -0.078, 0.032),
                        segments=8, parent=root)
    w.mirror(piston)
    crosshead = w.box("Crossheads", (0.005, 0.008, 0.007), "Metal_Brass", offset=(0.052, -0.062, 0.032), parent=root)
    w.mirror(crosshead)
    w.attach([piston, crosshead], rig, "Piston")

    shaft = w.cylinder("Key_Shaft", 0.0025, 0.03, "Metal_Brass", rotation=(90, 0, 0), offset=(0, 0.12, 0.095),
                       segments=10, parent=root)
    lobe = w.sphere("Key_Lobes", 0.012, "Metal_Brass", offset=(0.012, 0.136, 0.095), scale=(1, 0.25, 0.7), segments=14,
                    parent=root)
    w.mirror(lobe)
    w.attach([shaft, lobe], rig, "Key")

    for i in range(3):
        cx, cy = CHIMNEY
        cluster = [w.sphere(f"Smoke{i + 1}_{k}", r, "Fabric_Cream", offset=(cx + dx, cy + dy, 0.17 + dz), segments=12,
                            parent=root)
                   for k, (r, dx, dy, dz) in enumerate(((0.012, 0, 0, 0), (0.009, 0.009, 0.003, -0.003),
                                                         (0.008, -0.008, -0.002, 0.002)))]
        w.attach(cluster, rig, f"Smoke_{i + 1}")

    def smoke_pose(t_base, peak=1.0, rise=1.0):
        offsets, scales = {}, {}
        for i in range(3):
            t = (t_base + i / 3) % 1.0
            off, s = puff(i)(t)
            offsets[f"Smoke_{i + 1}"] = tuple(c * rise for c in off)
            s = 0.03 + (s - 0.03) * peak
            scales[f"Smoke_{i + 1}"] = (s, s, s)
        return offsets, scales

    drive_keys = []
    for f in frames(1, 49, 2):
        u = (f - 1) / 48
        phi = 720 * u
        r = math.radians(phi)
        pose = {f"Axle_{k + 1}": (phi, 0, 0) for k in range(3)}
        pose["Key"] = (0, -360 * u, 0)
        pose["Body"] = (0, 1.2 * math.sin(4 * math.pi * u), 0)
        offsets, scales = smoke_pose(2 * u)
        offsets["Rods"] = (0, -RC * math.sin(r), RC * math.cos(r) - RC)
        offsets["Piston"] = (0, -RC * math.sin(r), 0)
        offsets["Body"] = (0, 0, 0.0012 * math.sin(8 * math.pi * u))
        drive_keys.append((f, pose, offsets, scales))
    drive = w.make_action(rig, "Drive", drive_keys)

    hidden = {f"Smoke_{i + 1}": (0.03, 0.03, 0.03) for i in range(3)}

    def whistle_key(frame, hop, puffs):
        offsets = {"Root": (0, 0, hop)}
        scales = dict(hidden)
        for i, (z, s) in enumerate(puffs):
            offsets[f"Smoke_{i + 1}"] = (0, 0.01 * z / 0.1, z)
            scales[f"Smoke_{i + 1}"] = (s, s, s)
        return (frame, {}, offsets, scales)

    whistle = w.make_action(rig, "Whistle", [
        whistle_key(1, 0.0, [(0, 0.03)] * 3),
        whistle_key(4, 0.007, [(0.02, 1.5), (0, 0.03), (0, 0.03)]),
        whistle_key(8, 0.0, [(0.05, 1.8), (0.02, 1.3), (0, 0.03)]),
        whistle_key(13, 0.004, [(0.08, 1.5), (0.05, 1.6), (0.02, 1.2)]),
        whistle_key(18, 0.0, [(0.11, 0.7), (0.08, 1.3), (0.05, 1.5)]),
        whistle_key(26, 0.0, [(0.13, 0.03), (0.11, 0.5), (0.08, 1.0)]),
        whistle_key(36, 0.0, [(0.13, 0.03), (0.13, 0.03), (0.13, 0.03)]),
    ])
    idle_keys = []
    for f in frames(1, 49, 4):
        u = (f - 1) / 48
        offsets, scales = smoke_pose(u, peak=0.55, rise=0.7)
        idle_keys.append((f, {"Key": (0, 0, 0)}, offsets, scales))
    idle = w.make_action(rig, "Idle", idle_keys)
    stopped = w.make_action(rig, "Stopped", [(1, {}, {}, hidden), (12, {}, {}, hidden)])
    rig.animation_data.action = drive
    return root, (rig, [drive, whistle, idle, stopped])


def build_music_box():
    root = w.empty("MusicBox")
    W, D, T = 0.2, 0.13, 0.008
    Z0, Z1, FLOOR = 0.012, 0.112, 0.04
    BX, BY = 0.045, -0.01

    bones = [("Root", (0, 0, 0), (0, 0, 0.03), None),
             ("Lid", (-W / 2, D / 2, Z1), (W / 2, D / 2, Z1), "Root"),
             ("Ballerina", (BX, BY, 0.061), (BX, BY, 0.12), "Root"),
             ("Drum", (-0.08, 0.015, 0.062), (-0.02, 0.015, 0.062), "Root"),
             ("Crank", (W / 2, 0, 0.065), (W / 2 + 0.03, 0, 0.065), "Root")]
    rig = w.armature("MusicBox", bones, parent=root)

    front = w.box("Box_FrontBack", (W, T, Z1 - Z0), "Wood_Walnut", offset=(0, -D / 2 + T / 2, (Z0 + Z1) / 2), parent=root,
                  uv_rotate=True)
    w.mirror(front, x=False, y=True)
    w.bevel(front, 0.0015)
    side = w.box("Box_Sides", (T, D - 2 * T, Z1 - Z0), "Wood_Walnut", offset=(W / 2 - T / 2, 0, (Z0 + Z1) / 2), parent=root)
    w.mirror(side)
    w.box("Box_Bottom", (W, D, FLOOR - Z0), "Wood_Walnut", offset=(0, 0, (Z0 + FLOOR) / 2), parent=root)
    plinth = w.box("Box_Plinth", (W + 0.012, D + 0.012, 0.01), "Wood_Walnut", offset=(0, 0, Z0 + 0.005), parent=root)
    w.bevel(plinth, 0.003, 2)
    trim = w.box("Trim_FrontBack", (W + 0.004, 0.003, 0.004), "Metal_Brass", offset=(0, D / 2 + 0.0005, Z1 - 0.003), parent=root)
    w.mirror(trim, x=False, y=True)
    trim_side = w.box("Trim_Sides", (0.003, D, 0.004), "Metal_Brass", offset=(W / 2 + 0.0005, 0, Z1 - 0.003), parent=root)
    w.mirror(trim_side)
    foot = w.sphere("Feet", 0.008, "Metal_Brass", offset=(W / 2 - 0.016, D / 2 - 0.016, 0.008), segments=12, parent=root)
    w.mirror(foot, x=True, y=True)
    w.box("Front_Plaque", (0.06, 0.002, 0.03), "Enamel_Cream", offset=(0, -D / 2 - 0.0008, 0.062), parent=root)
    w.box("Front_Keyhole", (0.004, 0.002, 0.009), "Enamel_Black", offset=(0, -D / 2 - 0.0015, 0.062), parent=root)
    plaque_rim = w.torus("Front_PlaqueRim", 0.02, 0.0012, "Metal_Brass", rotation=(90, 0, 0),
                         offset=(0, -D / 2 - 0.0012, 0.062), major_segments=24, minor_segments=4, parent=root)
    w.squash(plaque_rim, (1.6, 1, 0.85), centre=(0, -D / 2, 0.062))
    rosette = w.cylinder("Side_Rosettes", 0.012, 0.002, "Metal_Brass", rotation=(0, 90, 0), offset=(W / 2 + 0.001, 0, 0.065),
                         segments=20, parent=root)
    w.mirror(rosette)
    w.box("Velvet", (W - 2 * T, D - 2 * T, 0.002), "Fabric_Red", offset=(0, 0, FLOOR + 0.001), parent=root)
    w.box("Divider", (0.004, D - 2 * T, 0.05), "Wood_Walnut", offset=(-0.005, 0, FLOOR + 0.025), parent=root)
    w.box("Mechanism_Glass", (0.085, D - 2 * T, 0.002), "Glass", offset=(-0.0495, 0, 0.088), parent=root)

    w.box("Mechanism_Bedplate", (0.08, 0.1, 0.004), "Metal_Brass", offset=(-0.05, 0, FLOOR + 0.002), parent=root)
    drum_c = (-0.05, 0.015, 0.062)
    drum = w.cylinder("Drum", 0.011, 0.055, "Metal_Brass", location=drum_c, rotation=(0, 90, 0), segments=24, parent=root)
    pins = w.sphere("Drum_Pins", 0.0016, "Metal_Iron", location=drum_c, offset=(-0.022, 0, 0.0112), segments=6, parent=root)
    w.array(pins, 8, constant=(0.0062, 0, 0))
    w.array_around(pins, 12, "X")
    w.attach([drum, pins], rig, "Drum")
    bracket = w.box("Drum_Brackets", (0.004, 0.012, 0.022), "Metal_Brass", location=drum_c, offset=(0.031, 0, -0.008),
                    parent=root)
    w.mirror(bracket)
    w.box("Comb_Base", (0.07, 0.012, 0.012), "Metal_Iron", offset=(-0.05, -0.03, 0.05), parent=root)
    teeth = w.box("Comb_Teeth", (0.0032, 0.03, 0.0012), "Metal_Iron", location=(-0.05, 0, 0), offset=(-0.032, -0.012, 0.0566),
                  parent=root)
    w.array(teeth, 13, constant=(0.0053, 0, 0))
    w.cylinder("Spring_Barrel", 0.012, 0.014, "Metal_Brass", offset=(-0.076, 0.044, 0.05), segments=20, parent=root)

    w.cylinder("Pedestal", 0.012, 0.02, "Metal_Brass", offset=(BX, BY, FLOOR + 0.01), segments=20, parent=root)
    loc = (BX, BY, 0)
    dancer = [
        w.cylinder("Stage_Mirror", 0.02, 0.002, "Metal_Iron", location=loc, offset=(0, 0, 0.061), segments=24, parent=root),
        w.tube("Leg_Standing", [(0, 0, 0.063), (0, 0, 0.097)], 0.0022, "Enamel_Pink", location=loc, parent=root),
        w.tube("Leg_Raised", [(0, 0, 0.095), (0, 0.012, 0.099), (0, 0.026, 0.106)], 0.002, "Enamel_Pink", location=loc,
               parent=root),
        w.sphere("Shoe", 0.0028, "Enamel_Pink", location=loc, offset=(0, 0, 0.063), scale=(1, 1.3, 1), segments=8, parent=root),
        w.lathe("Tutu", [(0.004, 0.094), (0.021, 0.097), (0.023, 0.099), (0.0215, 0.1005), (0.004, 0.103)], "Fabric_Cream",
                location=loc, segments=28, parent=root),
        w.lathe("Bodice", [(0, 0.098), (0.0058, 0.099), (0.0063, 0.107), (0.0052, 0.113), (0.003, 0.117), (0, 0.1175)],
                "Enamel_Pink", location=loc, segments=16, parent=root),
        w.cylinder("Neck", 0.0018, 0.006, "Skin", location=loc, offset=(0, 0, 0.119), segments=8, parent=root),
        w.sphere("Head", 0.0055, "Skin", location=loc, offset=(0, 0, 0.1245), segments=14, parent=root),
        w.sphere("Hair", 0.0058, "Wood_Walnut", location=loc, offset=(0, 0.0012, 0.1258), scale=(1, 1, 0.82), segments=14,
                 parent=root),
        w.sphere("Bun", 0.0028, "Wood_Walnut", location=loc, offset=(0, 0.002, 0.1312), segments=10, parent=root),
    ]
    arm = w.tube("Arms", [(0.005, 0, 0.1155), (0.012, 0, 0.124), (0.011, 0, 0.133), (0.004, 0, 0.138)], 0.0014, "Skin",
                 location=loc, parent=root)
    w.mirror(arm)
    dancer.append(arm)
    w.attach(dancer, rig, "Ballerina")

    lid = w.box("Lid", (W + 0.008, D + 0.006, 0.016), "Wood_Walnut", offset=(0, 0, Z1 + 0.008), parent=root, uv_rotate=True)
    w.bevel(lid, 0.003, 2)
    lid_parts = [
        lid,
        w.box("Lid_Lining", (W - 0.02, D - 0.02, 0.001), "Fabric_Red", offset=(0, 0, Z1 - 0.0004), parent=root),
        w.cylinder("Lid_Oval", 0.035, 0.001, "Enamel_Cream", offset=(0, 0, Z1 + 0.0165), segments=32, parent=root),
        w.prism("Lid_Star", star_points(0.022, 0.009), 0.0012, "Metal_Brass", offset=(0, 0, Z1 + 0.0168), plane="XY",
                parent=root),
        w.box("Lid_Clasp", (0.016, 0.003, 0.012), "Metal_Brass", offset=(0, -D / 2 - 0.004, Z1 + 0.004), parent=root),
    ]
    w.squash(lid_parts[2], (1.5, 1, 1), centre=(0, 0, Z1 + 0.0165))
    w.attach(lid_parts, rig, "Lid")

    cz = 0.065
    crank = [
        w.cylinder("Crank_Shaft", 0.003, 0.016, "Metal_Brass", rotation=(0, 90, 0), offset=(W / 2 + 0.008, 0, cz), segments=10,
                   parent=root),
        w.box("Crank_Arm", (0.003, 0.005, 0.024), "Metal_Brass", offset=(W / 2 + 0.016, 0, cz + 0.01), parent=root),
        w.cylinder("Crank_Knob", 0.0035, 0.012, "Enamel_Cream", rotation=(0, 90, 0), offset=(W / 2 + 0.022, 0, cz + 0.019),
                   segments=10, parent=root),
    ]
    w.attach(crank, rig, "Crank")

    play_keys = []
    for f in frames(1, 49, 4):
        u = (f - 1) / 48
        play_keys.append((f, {"Lid": (-100, 0, 0), "Ballerina": (0, 0, 360 * u), "Drum": (-360 * u, 0, 0),
                              "Crank": (720 * u, 0, 0)}))
    play = w.make_action(rig, "Play", play_keys)
    folded = (-90, 0, 0)
    open_action = w.make_action(rig, "Open", [
        (1, {"Ballerina": folded}),
        (10, {"Lid": (-60, 0, 0), "Ballerina": folded}),
        (18, {"Lid": (-100, 0, 0), "Ballerina": (-40, 0, 0)}),
        (24, {"Lid": (-100, 0, 0)}),
    ])
    close_action = w.make_action(rig, "Close", [
        (1, {"Lid": (-100, 0, 0)}),
        (10, {"Lid": (-100, 0, 0), "Ballerina": folded}),
        (20, {"Lid": (-8, 0, 0), "Ballerina": folded}),
        (24, {"Ballerina": folded}),
    ])
    closed = w.make_action(rig, "Closed", [(1, {"Ballerina": folded}), (12, {"Ballerina": folded})])
    rig.animation_data.action = play
    return root, (rig, [play, open_action, close_action, closed])


def build_jack_in_the_box():
    root = w.empty("JackInTheBox")
    S, H = 0.12, 0.13
    SPRING0, SPRING1 = 0.008, 0.175
    bones = [("Root", (0, 0, 0), (0, 0, 0.03), None),
             ("Lid", (-S / 2, S / 2, H), (S / 2, S / 2, H), "Root"),
             ("Crank", (S / 2, 0, 0.045), (S / 2 + 0.03, 0, 0.045), "Root"),
             ("Spring", (0, 0, SPRING0), (0, 0, SPRING1), "Root"),
             ("Jack", (0, 0, SPRING1), (0, 0, 0.21), "Root"),
             ("Head", (0, 0, 0.228), (0, 0, 0.3), "Jack")]
    rig = w.armature("JackInTheBox", bones, parent=root)

    w.box("Box_Bottom", (S, S, 0.008), "Wood_Oak", offset=(0, 0, 0.004), parent=root)
    fb = w.box("Panels_FrontBack", (S - 0.012, 0.005, H - 0.008), "Enamel_Red", offset=(0, S / 2 - 0.0025, H / 2 + 0.004),
               parent=root)
    w.mirror(fb, x=False, y=True)
    lr = w.box("Panels_Sides", (0.005, S - 0.012, H - 0.008), "Enamel_Blue", offset=(S / 2 - 0.0025, 0, H / 2 + 0.004),
               parent=root)
    w.mirror(lr)
    post = w.box("Corner_Posts", (0.012, 0.012, H), "Wood_Oak", offset=(S / 2 - 0.006, S / 2 - 0.006, H / 2), parent=root)
    w.mirror(post, x=True, y=True)
    w.bevel(post, 0.002)
    rim = w.box("Top_Rim", (S, 0.008, 0.006), "Wood_Oak", offset=(0, S / 2 - 0.004, H - 0.003), parent=root)
    w.mirror(rim, x=False, y=True)
    star_fb = w.prism("Stars_FrontBack", star_points(0.03, 0.013), 0.0015, "Enamel_Yellow", offset=(0, -S / 2, 0.066),
                      parent=root)
    w.mirror(star_fb, x=False, y=True)
    star_lr = w.prism("Stars_Sides", star_points(0.019, 0.008), 0.0015, "Enamel_White", offset=(S / 2, 0, 0.098),
                      rotation=(0, 0, 90), parent=root)
    w.mirror(star_lr)

    lid = w.box("Lid", (S + 0.006, S + 0.006, 0.012), "Enamel_Green", offset=(0, 0, H + 0.006), parent=root)
    w.bevel(lid, 0.002, 2)
    knob = w.sphere("Lid_Knob", 0.006, "Metal_Brass", offset=(0, -S / 2 - 0.006, H + 0.006), segments=12, parent=root)
    w.attach([lid, knob], rig, "Lid")

    cz = 0.045
    w.attach([
        w.cylinder("Crank_Hub", 0.008, 0.004, "Metal_Brass", rotation=(0, 90, 0), offset=(S / 2 + 0.002, 0, cz), segments=16,
                   parent=root),
        w.cylinder("Crank_Shaft", 0.003, 0.014, "Metal_Brass", rotation=(0, 90, 0), offset=(S / 2 + 0.007, 0, cz),
                   segments=10, parent=root),
        w.box("Crank_Arm", (0.003, 0.005, 0.032), "Metal_Brass", offset=(S / 2 + 0.013, 0, cz + 0.013), parent=root),
        w.cylinder("Crank_Handle", 0.0042, 0.016, "Enamel_Red", rotation=(0, 90, 0), offset=(S / 2 + 0.02, 0, cz + 0.026),
                   segments=12, parent=root),
    ], rig, "Crank")

    turns, radius = 8, 0.022
    helix = [(radius * math.cos(2 * math.pi * t / 16), radius * math.sin(2 * math.pi * t / 16),
              SPRING0 + (SPRING1 - SPRING0 + 0.004) * t / (turns * 16)) for t in range(turns * 16 + 1)]
    spring = w.tube("Spring", helix, 0.0022, "Metal_Iron", parent=root, resolution=1)
    w.attach([spring], rig, "Spring")

    jack = [
        w.lathe("Jack_Body", [(0, 0.17), (0.028, 0.172), (0.03, 0.19), (0.026, 0.212), (0, 0.214)], "Enamel_Red",
                segments=24, parent=root),
        w.torus("Jack_Stripe", 0.0298, 0.002, "Enamel_Yellow", offset=(0, 0, 0.19), major_segments=24, minor_segments=5,
                parent=root),
        w.lathe("Jack_Ruff", [(0.006, 0.211), (0.032, 0.217), (0.034, 0.2205), (0.032, 0.223), (0.006, 0.229)],
                "Fabric_Cream", segments=28, parent=root),
    ]
    pom = w.sphere("Jack_PomPoms", 0.0045, "Enamel_Yellow", offset=(0, -0.029, 0.178), segments=10, parent=root)
    w.array(pom, 3, constant=(0, 0.0012, 0.012))
    jack.append(pom)
    arm = w.tube("Jack_Arms", [(0.025, 0, 0.205), (0.04, -0.006, 0.198), (0.046, -0.014, 0.186)], 0.0055, "Enamel_Yellow",
                 parent=root)
    w.mirror(arm)
    glove = w.sphere("Jack_Gloves", 0.0075, "Enamel_White", offset=(0.047, -0.016, 0.182), segments=12, parent=root)
    w.mirror(glove)
    jack += [arm, glove]
    w.attach(jack, rig, "Jack")

    head = [
        w.sphere("Head", 0.028, "Skin", offset=(0, 0, 0.255), segments=24, parent=root),
        w.sphere("Nose", 0.0068, "Enamel_Red", offset=(0, -0.0275, 0.254), segments=12, parent=root),
        w.torus("Smile", 0.012, 0.0018, "Enamel_Red", offset=(0, -0.0255, 0.249), rotation=(-90, 20, 0), arc=140,
                major_segments=14, minor_segments=5, parent=root),
        w.sphere("Hat_Cap", 0.0285, "Enamel_Yellow", offset=(0, 0.002, 0.266), scale=(1.02, 1.02, 0.62), segments=20,
                 parent=root),
    ]
    for name, r, mat, off in (("Eyes", 0.0032, "Enamel_Black", (0.0095, -0.0245, 0.263)),
                              ("Cheeks", 0.0052, "Enamel_Pink", (0.0165, -0.021, 0.249))):
        part = w.sphere(name, r, mat, offset=off, segments=10, parent=root)
        w.mirror(part)
        head.append(part)
    horn = w.cylinder("Hat_Horns", 0.014, 0.05, "Enamel_Blue", radius_top=0.002, rotation=(0, 50, 0),
                      offset=(0.018, 0, 0.288), segments=16, parent=root)
    w.mirror(horn)
    bell = w.sphere("Hat_Bells", 0.0055, "Metal_Brass", offset=(0.0372, 0, 0.305), segments=12, parent=root)
    w.mirror(bell)
    head += [horn, bell]
    w.attach(head, rig, "Head")

    span = SPRING1 - SPRING0

    def spring_pose(s, jack_scale=1.0, head_rot=(0, 0, 0), lid=0.0, crank=0.0, jack_rot=(0, 0, 0)):
        return ({"Lid": (lid, 0, 0), "Crank": (crank, 0, 0), "Head": head_rot, "Jack": jack_rot},
                {"Jack": (0, 0, span * (s - 1))},
                {"Spring": (1, s, 1), "Jack": (jack_scale,) * 3})

    squashed = 0.2
    idle_keys = []
    for f in frames(1, 49, 4):
        p = 2 * math.pi * (f - 1) / 48
        idle_keys.append((f, *spring_pose(1 + 0.025 * math.sin(2 * p), lid=-115, jack_rot=(0, 6 * math.sin(p), 0),
                                          head_rot=(4 * math.cos(2 * p), 0, 6 * math.sin(p)))))
    idle = w.make_action(rig, "Idle", idle_keys)
    pop = w.make_action(rig, "Pop", [
        (1, *spring_pose(squashed, 0.6)),
        (3, *spring_pose(squashed, 0.6, lid=-40)),
        (5, *spring_pose(0.8, 0.9, lid=-125)),
        (8, *spring_pose(1.18, lid=-112, head_rot=(0, 10, 0))),
        (12, *spring_pose(0.88, lid=-117, head_rot=(0, -15, 0))),
        (16, *spring_pose(1.08, lid=-115, head_rot=(0, 12, 0))),
        (20, *spring_pose(0.95, lid=-115, head_rot=(0, -8, 0))),
        (25, *spring_pose(1.03, lid=-115, head_rot=(0, 5, 0))),
        (32, *spring_pose(1.0, lid=-115)),
        (40, *spring_pose(1.0, lid=-115)),
    ])
    crank_keys = [(f, *spring_pose(squashed, 0.6, crank=360 * (f - 1) / 48)) for f in frames(1, 49, 4)]
    crank = w.make_action(rig, "Crank", crank_keys)
    rig.animation_data.action = idle
    return root, (rig, [idle, pop, crank])


def build_toy_soldier():
    root = w.empty("ToySoldier")
    bones = [("Root", (0, 0, 0), (0, 0, 0.03), None),
             ("Body", (0, 0, 0.075), (0, 0, 0.13), "Root"),
             ("Head", (0, 0, 0.138), (0, 0, 0.2), "Body"),
             ("Key", (0, 0.026, 0.11), (0, 0.05, 0.11), "Body")]
    for s, side in ((1, "L"), (-1, "R")):
        bones += [(f"Arm.{side}", (s * 0.03, 0, 0.13), (s * 0.033, -0.002, 0.085), "Body"),
                  (f"Leg.{side}", (s * 0.014, 0, 0.075), (s * 0.014, 0, 0.012), "Root")]
    rig = w.armature("ToySoldier", bones, parent=root)

    for s, side in ((1, "L"), (-1, "R")):
        x = s * 0.0135
        leg = [w.cylinder(f"Leg.{side}_Mesh", 0.0095, 0.066, "Enamel_Blue", offset=(x, 0, 0.044), segments=14, parent=root),
               w.box(f"Leg.{side}_Stripe", (0.0015, 0.004, 0.062), "Enamel_Red", offset=(x + s * 0.0094, 0, 0.044),
                     parent=root)]
        boot = w.box(f"Boot.{side}", (0.021, 0.034, 0.013), "Enamel_Black", offset=(x, -0.005, 0.0065), parent=root)
        w.bevel(boot, 0.004, 2)
        leg.append(boot)
        w.attach(leg, rig, f"Leg.{side}")

    body = [
        w.lathe("Tunic", [(0, 0.07), (0.026, 0.07), (0.0275, 0.084), (0.025, 0.11), (0.022, 0.13), (0.012, 0.138),
                          (0, 0.139)], "Enamel_Red", segments=24, parent=root),
        w.torus("Belt", 0.0272, 0.0028, "Enamel_White", offset=(0, 0, 0.082), major_segments=24, minor_segments=5,
                parent=root),
        w.box("Buckle", (0.01, 0.003, 0.008), "Metal_Brass", offset=(0, -0.0295, 0.082), parent=root),
        w.cylinder("Neck", 0.008, 0.012, "Skin", offset=(0, 0, 0.14), segments=12, parent=root),
    ]
    buttons = w.sphere("Buttons", 0.0024, "Metal_Brass", offset=(0.0075, -0.0255, 0.094), scale=(1, 0.6, 1), segments=8,
                       parent=root)
    w.array(buttons, 3, constant=(0, 0.001, 0.012))
    w.mirror(buttons)
    epaulette = w.cylinder("Epaulettes", 0.009, 0.004, "Metal_Brass", rotation=(0, 20, 0), offset=(0.024, 0, 0.134),
                           segments=16, parent=root)
    w.mirror(epaulette)
    sash = w.box("Sash", (0.006, 0.002, 0.062), "Enamel_White", offset=(0, -0.0262, 0.106), rotation=(0, 32, 0), parent=root)
    body += [buttons, epaulette, sash]
    w.attach(body, rig, "Body")

    head = [
        w.sphere("Head_Mesh", 0.017, "Skin", offset=(0, 0, 0.155), segments=20, parent=root),
        w.sphere("Nose", 0.0035, "Skin", offset=(0, -0.017, 0.154), segments=8, parent=root),
        w.lathe("Busby", [(0, 0.163), (0.0185, 0.163), (0.0195, 0.19), (0.0175, 0.205), (0.01, 0.211), (0, 0.212)],
                "Enamel_Black", segments=24, parent=root),
        w.torus("Busby_Band", 0.019, 0.0015, "Metal_Brass", offset=(0, 0, 0.166), major_segments=24, minor_segments=4,
                parent=root),
        w.torus("Chin_Strap", 0.0172, 0.0011, "Metal_Brass", offset=(0, 0, 0.157), rotation=(-90, 0, 0), arc=180,
                major_segments=16, minor_segments=4, parent=root),
        w.sphere("Plume", 0.006, "Enamel_Red", offset=(0.016, -0.004, 0.198), scale=(0.6, 0.6, 1.5), segments=10, parent=root),
        w.cylinder("Badge", 0.004, 0.002, "Metal_Brass", rotation=(90, 0, 0), offset=(0, -0.0192, 0.18), segments=12,
                   parent=root),
    ]
    for name, r, mat, off, scale in (("Eyes", 0.0025, "Enamel_Black", (0.0065, -0.0155, 0.159), (1, 1, 1)),
                                     ("Cheeks", 0.0036, "Enamel_Pink", (0.0105, -0.0135, 0.151), (1, 1, 1)),
                                     ("Moustache", 0.005, "Enamel_Black", (0.0055, -0.0162, 0.1495), (1.2, 0.5, 0.5))):
        part = w.sphere(name, r, mat, offset=off, scale=scale, segments=10, parent=root)
        w.mirror(part)
        head.append(part)
    w.attach(head, rig, "Head")

    for s, side in ((1, "L"), (-1, "R")):
        arm = [w.tube(f"Arm.{side}_Mesh", [(s * 0.03, 0, 0.132), (s * 0.033, -0.002, 0.09)], 0.0075, "Enamel_Red",
                      parent=root),
               w.torus(f"Cuff.{side}", 0.0074, 0.0022, "Enamel_White", offset=(s * 0.033, -0.002, 0.09), minor_segments=5,
                       parent=root),
               w.sphere(f"Glove.{side}", 0.0085, "Enamel_White", offset=(s * 0.0335, -0.003, 0.081), segments=12,
                        parent=root)]
        if side == "L":
            arm += [w.cylinder("Rifle_Barrel", 0.0025, 0.085, "Metal_Iron", offset=(0.042, -0.008, 0.115), segments=8,
                               parent=root),
                    w.box("Rifle_Stock", (0.006, 0.012, 0.036), "Wood_Walnut", offset=(0.042, -0.008, 0.062), parent=root)]
        w.attach(arm, rig, f"Arm.{side}")

    shaft = w.cylinder("Key_Shaft", 0.0025, 0.016, "Metal_Brass", rotation=(90, 0, 0), offset=(0, 0.033, 0.11), segments=10,
                       parent=root)
    lobe = w.sphere("Key_Lobes", 0.009, "Metal_Brass", offset=(0.009, 0.042, 0.11), scale=(1, 0.25, 0.7), segments=12,
                    parent=root)
    w.mirror(lobe)
    w.attach([shaft, lobe], rig, "Key")

    idle = w.make_action(rig, "Idle", [
        (f, {"Body": (0, 1.5 * math.sin(2 * math.pi * (f - 1) / 48), 0),
             "Head": (2 * math.sin(4 * math.pi * (f - 1) / 48), 0, 10 * math.sin(2 * math.pi * (f - 1) / 48)),
             "Arm.R": (0, -3 * math.sin(2 * math.pi * (f - 1) / 48), 0)})
        for f in frames(1, 49, 6)])
    march_keys = []
    for f in frames(1, 25, 3):
        p = 2 * math.pi * (f - 1) / 24
        swing = math.sin(p)
        march_keys.append((f, {"Leg.L": (-28 * swing, 0, 0), "Leg.R": (28 * swing, 0, 0),
                               "Arm.R": (-24 * swing, 0, 0), "Arm.L": (5 * swing, 0, 0),
                               "Body": (0, 3 * swing, 0), "Head": (0, -2 * swing, 0), "Key": (0, -360 * (f - 1) / 24, 0)},
                           {"Root": (0, 0, 0.004 * abs(swing))}))
    march = w.make_action(rig, "March", march_keys)

    shoulder = Vector((-0.03, 0, 0.13))
    rest_dir = Vector((-0.033, -0.002, 0.085)) - shoulder
    brow = Vector((-0.013, -0.018, 0.168))
    q = rest_dir.normalized().rotation_difference((brow - shoulder).normalized())
    salute_rot = tuple(math.degrees(a) for a in q.to_euler("XYZ"))
    saluting = {"Arm.R": salute_rot, "Head": (-6, 0, 0)}
    salute = w.make_action(rig, "Salute", [(1, {}), (8, saluting), (12, {**saluting, "Body": (-3, 0, 0)}),
                                           (28, saluting), (36, {})])
    fall = w.make_action(rig, "Fall", [
        (1, {}),
        (6, {"Root": (-10, 0, 0), "Arm.L": (0, -20, 0), "Arm.R": (0, 20, 0)}),
        (11, {"Root": (12, 0, 0), "Arm.L": (0, -40, 0), "Arm.R": (0, 40, 0)}),
        (19, {"Root": (90, 0, 0), "Arm.L": (-120, -30, 0), "Arm.R": (-120, 30, 0)}, {"Root": (0, 0, 0.027)}),
        (23, {"Root": (83, 0, 0), "Arm.L": (-110, -20, 0), "Arm.R": (-110, 20, 0)}, {"Root": (0, 0, 0.031)}),
        (27, {"Root": (90, 0, 0), "Arm.L": (-120, -30, 0), "Arm.R": (-120, 30, 0), "Leg.L": (-15, 0, 0)},
         {"Root": (0, 0, 0.027)}),
        (31, {"Root": (90, 0, 0), "Arm.L": (-120, -30, 0), "Arm.R": (-120, 30, 0), "Leg.R": (-15, 0, 0),
              "Key": (0, -90, 0)}, {"Root": (0, 0, 0.027)}),
        (40, {"Root": (90, 0, 0), "Arm.L": (-120, -30, 0), "Arm.R": (-120, 30, 0), "Key": (0, -130, 0)},
         {"Root": (0, 0, 0.027)}),
    ])
    lying = {"Root": (90, 0, 0), "Arm.L": (-120, -30, 0), "Arm.R": (-120, 30, 0), "Key": (0, -130, 0)}
    get_up = w.make_action(rig, "GetUp", [
        (1, lying, {"Root": (0, 0, 0.027)}),
        (8, {**lying, "Arm.L": (-40, -10, 0), "Arm.R": (-40, 10, 0)}, {"Root": (0, 0, 0.03)}),
        (15, {"Root": (55, 0, 0), "Arm.L": (-10, -15, 0), "Arm.R": (-10, 15, 0), "Leg.L": (20, 0, 0)},
         {"Root": (0, 0, 0.022)}),
        (21, {"Root": (12, 0, 0), "Leg.L": (8, 0, 0)}, {"Root": (0, 0, 0.004)}),
        (25, {"Root": (-5, 0, 0)}),
        (30, {"Root": (2, 0, 0), "Head": (0, 0, 8)}),
        (36, {}),
    ])
    rig.animation_data.action = idle
    return root, (rig, [idle, march, salute, fall, get_up])


def build_wind_up_mouse():
    root = w.empty("WindUpMouse")
    BZ = 0.03
    bones = [("Root", (0, 0, 0), (0, 0, 0.02), None),
             ("Body", (0, 0.0, 0.015), (0, -0.03, 0.03), "Root"),
             ("Key", (0, 0.015, 0.05), (0, 0.015, 0.08), "Body"),
             ("Tail1", (0, 0.042, 0.02), (0, 0.07, 0.012), "Body"),
             ("Tail2", (0, 0.07, 0.012), (0.004, 0.1, 0.014), "Tail1")]
    for s, side in ((1, "L"), (-1, "R")):
        bones.append((f"Ear.{side}", (s * 0.013, -0.02, 0.052), (s * 0.016, -0.02, 0.07), "Body"))
    feet = {"FL": (0.016, -0.02), "FR": (-0.016, -0.02), "BL": (0.017, 0.02), "BR": (-0.017, 0.02)}
    for name, (x, y) in feet.items():
        bones.append((f"Foot_{name}", (x, y, 0.004), (x, y - 0.012, 0.004), "Root"))
    rig = w.armature("WindUpMouse", bones, parent=root)

    body = w.lathe("Body_Mesh", [(0, 0), (0.012, 0.002), (0.024, 0.015), (0.029, 0.035), (0.026, 0.055), (0.017, 0.072),
                                 (0.008, 0.082), (0, 0.086)], "Felt_Grey", rotation=(90, 0, 0), offset=(0, 0.04, BZ),
                   segments=32, parent=root)
    w.squash(body, (1, 1, 0.85), centre=(0, 0, BZ))
    parts = [body,
             w.sphere("Nose", 0.0042, "Enamel_Pink", offset=(0, -0.0465, 0.031), segments=10, parent=root)]
    eye = w.sphere("Eyes", 0.0042, "Enamel_Black", offset=(0.0105, -0.034, 0.042), segments=10, parent=root)
    w.mirror(eye)
    parts.append(eye)
    whiskers = [w.tube(f"Whiskers{k}", [(0.005, -0.043, 0.032), (0.03, -0.048 + 0.004 * k, 0.037 - 0.005 * k)], 0.0004,
                       "Enamel_Black", parent=root, resolution=0) for k in range(3)]
    for wh in whiskers:
        w.mirror(wh)
    parts += whiskers
    w.attach(parts, rig, "Body")

    for s, side in ((1, "L"), (-1, "R")):
        ear = [w.cylinder(f"Ear.{side}_Mesh", 0.012, 0.003, "Felt_Grey", rotation=(80, 0, s * 25),
                          offset=(s * 0.014, -0.02, 0.06), segments=16, parent=root),
               w.cylinder(f"Ear.{side}_Inner", 0.0085, 0.001, "Enamel_Pink", rotation=(80, 0, s * 25),
                          offset=(s * 0.0143, -0.0216, 0.0598), segments=16, parent=root)]
        w.attach(ear, rig, f"Ear.{side}")
    w.attach([w.tube("Tail1_Mesh", [(0, 0.04, 0.02), (0, 0.055, 0.015), (0, 0.07, 0.012)], 0.0022, "Enamel_Pink",
                     parent=root)], rig, "Tail1")
    w.attach([w.tube("Tail2_Mesh", [(0, 0.07, 0.012), (0.001, 0.085, 0.012), (0.004, 0.1, 0.015), (0.009, 0.108, 0.019)],
                     0.0018, "Enamel_Pink", parent=root)], rig, "Tail2")
    for name, (x, y) in feet.items():
        w.attach([w.sphere(f"Foot_{name}_Mesh", 0.005, "Enamel_Pink", offset=(x, y - 0.003, 0.004), scale=(1, 1.4, 0.6),
                           segments=10, parent=root)], rig, f"Foot_{name}")
    key = [w.cylinder("Key_Shaft", 0.002, 0.016, "Metal_Brass", offset=(0, 0.015, 0.06), segments=8, parent=root)]
    lobe = w.sphere("Key_Lobes", 0.008, "Metal_Brass", offset=(0.008, 0.015, 0.072), scale=(1, 0.3, 0.7), segments=12,
                    parent=root)
    w.mirror(lobe)
    key.append(lobe)
    w.attach(key, rig, "Key")

    sniff_keys = []
    for f in frames(1, 49, 2):
        u = (f - 1) / 48
        sniffing = 0 <= (f - 1) % 24 < 12
        nod = -5 - 3 * math.sin(2 * math.pi * (f - 1) / 4) if sniffing else -1
        twitch = 18 if (f - 1) in (30, 32) else 0
        sniff_keys.append((f, {"Body": (nod, 0, 3 * math.sin(2 * math.pi * u)),
                               "Ear.L": (0, -twitch, 0), "Ear.R": (0, twitch * 0.5, 0),
                               "Tail1": (0, 0, 12 * math.sin(2 * math.pi * u)),
                               "Tail2": (0, 0, 18 * math.sin(2 * math.pi * u - 0.8))}))
    sniff = w.make_action(rig, "Sniff", sniff_keys)
    scurry_keys = []
    for f in frames(1, 13, 2):
        p = 2 * math.pi * (f - 1) / 12
        step = lambda ph: (0, -0.005 * math.sin(p + ph), 0.003 * max(0.0, math.cos(p + ph)))
        scurry_keys.append((f, {"Body": (2 * math.sin(2 * p), 0, 0), "Tail1": (0, 0, 18 * math.sin(p)),
                                "Tail2": (0, 0, 28 * math.sin(p - 1)), "Key": (0, 0, -360 * (f - 1) / 12),
                                "Ear.L": (0, -6 * math.sin(2 * p), 0), "Ear.R": (0, 6 * math.sin(2 * p), 0)},
                            {"Foot_FL": step(0), "Foot_BR": step(0), "Foot_FR": step(math.pi), "Foot_BL": step(math.pi),
                             "Body": (0, 0, 0.0015 * abs(math.sin(p)))}))
    scurry = w.make_action(rig, "Scurry", scurry_keys)
    rig.animation_data.action = sniff
    return root, (rig, [sniff, scurry])


def gable(name, length, depth, height, material, location, parent):
    return w.prism(name, [(-depth / 2, 0), (depth / 2, 0), (0, height)], length, material, location=location,
                   offset=(-length / 2, 0, 0), rotation=(0, 0, 90), parent=parent)


def pitched_roof(name, length, depth, pitch, material, location, parent, overhang=0.006):
    half = depth / 2 + overhang
    slope = half / math.cos(math.radians(pitch))
    rise = (depth / 2) * math.tan(math.radians(pitch))
    board = w.box(name, (length + 2 * overhang, slope, 0.005), material, location=location,
                  offset=(0, half / 2, rise - (half / 2) * math.tan(math.radians(pitch)) + 0.0025),
                  rotation=(-pitch, 0, 0), parent=parent)
    w.mirror(board, x=False, y=True)
    return rise


def house(name, x, y, walls, roof_mat, root, size=(0.07, 0.055, 0.05)):
    sx, sy, sz = size
    z0 = TOWN_TOP
    parts = [w.box(f"{name}_Walls", size, walls, offset=(x, y, z0 + sz / 2), parent=root)]
    w.bevel(parts[0], 0.002)
    loc = (x, y, z0 + sz)
    rise = pitched_roof(f"{name}_Roof", sx, sy, 38, roof_mat, loc, root)
    gable(f"{name}_Gable", sx - 0.002, sy - 0.002, rise, walls, loc, root)
    w.box(f"{name}_Chimney", (0.01, 0.01, 0.03), "Brick", offset=(x + sx * 0.28, y + sy * 0.15, z0 + sz + 0.03), parent=root)
    w.box(f"{name}_Door", (0.014, 0.002, 0.024), "Wood_Walnut", offset=(x, y - sy / 2 - 0.0008, z0 + 0.012), parent=root)
    win = w.box(f"{name}_Windows", (0.012, 0.002, 0.012), "Emissive_Warm", location=(x, y, 0),
                offset=(sx * 0.3, -sy / 2 - 0.0008, z0 + sz * 0.6), parent=root)
    w.mirror(win)


def build_toy_town():
    root = w.empty("ToyTown")
    top = TOWN_TOP

    tabletop = w.box("Table_Top", (1.3, 0.9, 0.04), "Wood_Oak", offset=(0, 0, 0.72), parent=root, uv_rotate=True)
    w.bevel(tabletop, 0.008, 3)
    leg = w.lathe("Table_Legs", [(0, 0), (0.028, 0), (0.03, 0.02), (0.02, 0.06), (0.024, 0.3), (0.019, 0.5), (0.03, 0.58),
                                 (0.03, 0.7), (0, 0.7)], "Wood_Walnut", offset=(0.59, 0.39, 0), segments=16, parent=root)
    w.mirror(leg, x=True, y=True)
    apron = w.box("Table_ApronsLong", (1.14, 0.02, 0.07), "Wood_Walnut", offset=(0, 0.39, 0.665), parent=root)
    w.mirror(apron, x=False, y=True)
    apron_s = w.box("Table_ApronsShort", (0.02, 0.76, 0.07), "Wood_Walnut", offset=(0.59, 0, 0.665), parent=root)
    w.mirror(apron_s)

    w.box("Board", (1.22, 0.82, 0.025), "Felt_Green", offset=(0, 0, top - 0.0125), parent=root)
    edge = w.box("Board_EdgeLong", (1.26, 0.02, 0.035), "Wood_Walnut", offset=(0, 0.42, top - 0.0075), parent=root)
    w.mirror(edge, x=False, y=True)
    w.bevel(edge, 0.003)
    edge_s = w.box("Board_EdgeShort", (0.02, 0.82, 0.035), "Wood_Walnut", offset=(0.62, 0, top - 0.0075), parent=root)
    w.mirror(edge_s)

    ring_strip("Track_Ballast", TRACK_A, TRACK_B, 0.062, 0.062, top + 0.001, "Gravel", root)
    path = w.path_curve("Track_Path", ellipse(TRACK_A, TRACK_B, 128), location=(0, 0, top + 0.001), parent=root)
    sleeper = w.box("Track_Sleepers", (0.012, 0.11, 0.006), "Wood_Walnut", location=(0, 0, top + 0.001),
                    offset=(0, 0, 0.003), parent=root)
    w.follow_curve(sleeper, path, 3.0)
    for side, offset in (("Outer", RAIL_GAP), ("Inner", -RAIL_GAP)):
        w.tube(f"Track_Rail{side}", ellipse(TRACK_A, TRACK_B, 128, offset, top + 0.009), 0.003, "Metal_Iron",
               parent=root, cyclic=True, resolution=1)

    sy = 0.37
    w.box("Platform", (0.42, 0.06, 0.022), "Plaster", offset=(0, 0.305, top + 0.011), parent=root)
    w.box("Platform_Edge", (0.42, 0.006, 0.003), "Enamel_White", offset=(0, 0.277, top + 0.0225), parent=root)
    station = w.box("Station_Walls", (0.24, 0.06, 0.07), "Enamel_Cream", offset=(0, sy, top + 0.022 + 0.035), parent=root)
    w.bevel(station, 0.002)
    rise = pitched_roof("Station_Roof", 0.24, 0.06, 32, "Enamel_Red", (0, sy, top + 0.092), root)
    gable("Station_Gable", 0.236, 0.058, rise, "Enamel_Cream", (0, sy, top + 0.092), root)
    w.box("Station_Door", (0.03, 0.002, 0.045), "Wood_Walnut", offset=(0, sy - 0.0308, top + 0.0445), parent=root)
    swin = w.box("Station_Windows", (0.022, 0.002, 0.024), "Emissive_Warm", location=(0, 0, 0),
                 offset=(0.05, sy - 0.0308, top + 0.058), parent=root)
    w.array(swin, 2, constant=(0.042, 0, 0))
    w.mirror(swin)
    w.box("Station_Sign", (0.08, 0.002, 0.014), "Enamel_Black", offset=(0, sy - 0.031, top + 0.081), parent=root)
    w.cylinder("Station_Clock", 0.011, 0.003, "Enamel_Cream", rotation=(90, 0, 0), offset=(0, sy - 0.032, top + 0.104),
               segments=20, parent=root)
    post = w.cylinder("Canopy_Posts", 0.0028, 0.06, "Metal_Iron", offset=(-0.17, 0.285, top + 0.022 + 0.03), segments=8,
                      parent=root)
    w.array(post, 5, constant=(0.085, 0, 0))
    canopy = w.box("Canopy", (0.4, 0.06, 0.004), "Enamel_Green", offset=(0, 0.31, top + 0.085), rotation=(8, 0, 0),
                   parent=root)
    w.bevel(canopy, 0.0015)

    w.cylinder("Signal_Post", 0.003, 0.13, "Enamel_White", offset=(0.27, 0.29, top + 0.065), segments=8, parent=root)
    w.sphere("Signal_Lamp", 0.005, "Emissive_Warm", offset=(0.27, 0.284, top + 0.112), segments=10, parent=root)

    house("HouseA", -0.26, 0.04, "Enamel_Cream", "Enamel_Red", root)
    house("HouseB", -0.13, 0.08, "Enamel_Yellow", "Enamel_Blue", root, size=(0.06, 0.05, 0.06))
    house("HouseC", -0.12, -0.07, "Enamel_White", "Enamel_Green", root, size=(0.065, 0.05, 0.045))

    mx, my = 0.2, 0.03
    w.lathe("Windmill_Tower", [(0, 0), (0.036, 0), (0.031, 0.1), (0.023, 0.15), (0, 0.15)], "Plaster",
            offset=(mx, my, top), segments=20, parent=root)
    w.lathe("Windmill_Cap", [(0, 0), (0.027, 0), (0.024, 0.012), (0.012, 0.03), (0, 0.036)], "Enamel_Red",
            offset=(mx, my, top + 0.148), segments=20, parent=root)
    w.box("Windmill_Door", (0.016, 0.002, 0.026), "Wood_Walnut", offset=(mx, my - 0.035, top + 0.013), parent=root)
    w.box("Windmill_Window", (0.01, 0.002, 0.012), "Emissive_Warm", offset=(mx, my - 0.029, top + 0.08), rotation=(-6, 0, 0),
          parent=root)

    for k, (x, y) in enumerate(((0.33, -0.04), (0.05, 0.1), (-0.33, -0.03), (0.06, -0.09), (-0.02, 0.0))):
        w.cylinder(f"Tree{k}_Trunk", 0.005, 0.02, "Wood_Walnut", offset=(x, y, top + 0.01), segments=8, parent=root)
        w.lathe(f"Tree{k}_Leaves", [(0, 0), (0.024, 0), (0.012, 0.03), (0.019, 0.03), (0.007, 0.06), (0, 0.065)],
                "Enamel_Green", offset=(x, y, top + 0.018), segments=12, parent=root, smooth=False)
    trunk = w.cylinder("CornerTree_Trunks", 0.007, 0.04, "Wood_Walnut", offset=(0.55, 0.33, top + 0.02), segments=8,
                       parent=root)
    w.mirror(trunk, x=True, y=True)
    crown = w.sphere("CornerTree_Crowns", 0.04, "Enamel_Green", offset=(0.55, 0.33, top + 0.07), segments=14, parent=root)
    w.mirror(crown, x=True, y=True)

    pond = w.cylinder("Pond", 0.045, 0.003, "Enamel_Blue", offset=(0.08, -0.005, top + 0.0015), segments=24, parent=root)
    w.squash(pond, (1.4, 0.75, 1), centre=(0.08, -0.005, top))
    for k, (x, y) in enumerate(((0.07, -0.01), (0.1, 0.005))):
        w.sphere(f"Duck{k}", 0.005, "Enamel_Yellow", offset=(x, y, top + 0.006), scale=(1.3, 1, 0.8), segments=8, parent=root)
        w.sphere(f"Duck{k}_Head", 0.0032, "Enamel_Yellow", offset=(x - 0.005, y, top + 0.011), segments=8, parent=root)
    lamp = w.cylinder("Lamp_Posts", 0.0022, 0.07, "Metal_Iron", offset=(0.3, -0.33, top + 0.035), segments=8, parent=root)
    w.mirror(lamp)
    bulb = w.sphere("Lamp_Bulbs", 0.006, "Emissive_Warm", offset=(0.3, -0.33, top + 0.073), segments=10, parent=root)
    w.mirror(bulb)

    picket = w.box("Fence_Pickets", (0.004, 0.006, 0.026), "Enamel_White", offset=(0.585, -0.27, top + 0.013), parent=root)
    w.array(picket, 22, constant=(0, 0.026, 0))
    w.mirror(picket)
    fence_rail = w.box("Fence_Rails", (0.003, 0.56, 0.004), "Enamel_White", offset=(0.585, 0.0, top + 0.018), parent=root)
    w.mirror(fence_rail)

    hub = (mx, my - 0.03, top + 0.152)
    rig = w.armature("ToyTown", [("Root", (0, 0, 0), (0, 0, 0.2), None),
                                 ("Sails", hub, (hub[0], hub[1] - 0.03, hub[2]), "Root"),
                                 ("Signal", (0.27, 0.284, top + 0.122), (0.31, 0.284, top + 0.122), "Root")], parent=root)
    sail = [w.cylinder("Sails_Hub", 0.006, 0.01, "Wood_Walnut", location=hub, rotation=(90, 0, 0), segments=10, parent=root)]
    blade = w.box("Sails_Frames", (0.005, 0.003, 0.125), "Wood_Oak", location=hub, offset=(0, -0.006, 0.066), parent=root)
    w.array_around(blade, 4, "Y")
    cloth = w.box("Sails_Cloth", (0.032, 0.0015, 0.095), "Fabric_Cream", location=hub, offset=(0.018, -0.007, 0.078),
                  parent=root)
    w.array_around(cloth, 4, "Y")
    sail += [blade, cloth]
    w.attach(sail, rig, "Sails")
    arm = w.box("Signal_Arm", (0.045, 0.003, 0.009), "Enamel_Red", offset=(0.293, 0.282, top + 0.122), parent=root)
    w.attach([arm, w.box("Signal_Stripe", (0.004, 0.0035, 0.0092), "Enamel_White", offset=(0.305, 0.282, top + 0.122),
                         parent=root)], rig, "Signal")

    spin = w.make_action(rig, "Spin", [(f, {"Sails": (0, -90 * (f - 1) / 48, 0)}) for f in frames(1, 49, 4)])
    signal_keys = []
    for f in frames(1, 49, 4):
        lowered = 1.0 if 9 <= f <= 37 else (0.5 if f in (5, 41) else 0.0)
        signal_keys.append((f, {"Sails": (0, -90 * (f - 1) / 48, 0), "Signal": (0, -35 * lowered, 0)}))
    signal = w.make_action(rig, "Signal", signal_keys)
    rig.animation_data.action = spin
    return root, (rig, [spin, signal])


BUILDERS = {
    "SteamTrain": build_steam_train,
    "MusicBox": build_music_box,
    "JackInTheBox": build_jack_in_the_box,
    "ToySoldier": build_toy_soldier,
    "WindUpMouse": build_wind_up_mouse,
    "ToyTown": build_toy_town,
}

CAMERA = {"ToyTown": (0.55, -1.0, 0.75), "WindUpMouse": (0.9, -1.0, 0.45), "MusicBox": (0.7, -1.0, 0.6)}


def render_lineup():
    w.reset()
    spots = {"SteamTrain": (-0.34, 0.0, 30), "MusicBox": (-0.07, 0.06, -15), "JackInTheBox": (0.17, 0.08, -25),
             "ToySoldier": (0.35, -0.02, -20), "WindUpMouse": (0.05, -0.14, 25)}
    objects = []
    for name, (x, y, yaw) in spots.items():
        root, (rig, actions) = BUILDERS[name]()
        root.location = (x, y, 0)
        root.rotation_euler = (0, 0, math.radians(yaw))
        rig.animation_data.action = actions[0]
        objects += w.asset_objects(root)
    bpy.context.scene.frame_set(9)
    w.studio(objects, angle=(0.2, -1.0, 0.42), lens=50)
    w.render_still(os.path.join(RENDER_DIR, "Phase2_Lineup.png"), samples=192)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render = "--no-render" not in args
    video = "--no-video" not in args
    names = [a for a in args if not a.startswith("--")]
    if not names and "--lineup" not in args:
        names = list(BUILDERS)
    os.makedirs(RENDER_DIR, exist_ok=True)
    w.write_material_json()
    for name in names:
        w.reset()
        root, (rig, actions) = BUILDERS[name]()
        objects = w.asset_objects(root)
        tris = w.triangle_count(objects)
        w.export_fbx(root, "Toys", animated=True)
        if render:
            rig.animation_data.action = actions[0]
            bpy.context.scene.frame_set(1)
            w.studio(objects, angle=CAMERA.get(name, (0.75, -1.0, 0.42)), fstop=14.0)
            w.render_still(os.path.join(RENDER_DIR, f"{name}.png"))
            if video:
                last = w.queue_actions_for_preview(rig, actions)
                w.render_video(os.path.join(RENDER_DIR, f"{name}_animations.mp4"), 1, last)
            rig.animation_data.action = actions[0]
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, f"{name}.blend"))
        print(f"ASSET {name:<14} {tris:>6} tris  anims: {[a.name for a in actions]}")
    if "--lineup" in args:
        render_lineup()


if __name__ == "__main__":
    main()
