import json
import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(SCRIPTS_DIR)
PROJECT_DIR = os.path.dirname(BLENDER_DIR)
ART_DIR = os.path.join(PROJECT_DIR, "Assets", "Art")
TEXTURE_DIR = os.path.join(ART_DIR, "Textures")

M = {
    "Wood_Oak":      dict(tex="wood_oak", tile=0.9, rough=0.55, bump=0.3),
    "Wood_Walnut":   dict(tex="wood_walnut", tile=0.9, rough=0.5, bump=0.3),
    "Wood_Floor":    dict(tex="wood_floor", tile=1.44, rough=0.6),
    "Brick":         dict(tex="brick", tile=1.0, rough=0.85, bump=1.0),
    "Plaster":       dict(tex="plaster", tile=2.0, rough=0.92),
    "Pegboard":      dict(tex="pegboard", tile=0.6, rough=0.7),
    "Metal_Iron":    dict(tex="metal", tint=(0.30, 0.30, 0.32), metal=1.0, tile=0.4, rough=0.45),
    "Metal_Brass":   dict(tex="metal", tint=(0.88, 0.66, 0.30), metal=1.0, tile=0.4, rough=0.28),
    "Fabric_Navy":   dict(tex="fabric", tint=(0.16, 0.20, 0.38), tile=0.25, rough=0.95),
    "Fabric_Brown":  dict(tex="fabric", tint=(0.38, 0.26, 0.17), tile=0.25, rough=0.95),
    "Fabric_Red":    dict(tex="fabric", tint=(0.55, 0.11, 0.11), tile=0.25, rough=0.9),
    "Fabric_Rug":    dict(tex="fabric", tint=(0.52, 0.22, 0.13), tile=0.35, rough=0.95),
    "Fabric_Cream":  dict(tex="fabric", tint=(0.92, 0.88, 0.78), tile=0.25, rough=0.95),
    "Leather":       dict(tex="leather", tint=(0.45, 0.27, 0.15), tile=0.3, rough=0.6),
    "Skin":          dict(color=(0.93, 0.71, 0.57), rough=0.55),
    "Hair_White":    dict(color=(0.93, 0.92, 0.89), rough=0.85),
    "Wax":           dict(color=(0.96, 0.92, 0.82), rough=0.5),
    "Enamel_Red":    dict(tex="enamel", tint=(0.78, 0.10, 0.08), tile=0.3, rough=0.25),
    "Enamel_Blue":   dict(tex="enamel", tint=(0.10, 0.26, 0.66), tile=0.3, rough=0.25),
    "Enamel_Yellow": dict(tex="enamel", tint=(0.96, 0.72, 0.10), tile=0.3, rough=0.25),
    "Enamel_Green":  dict(tex="enamel", tint=(0.12, 0.44, 0.26), tile=0.3, rough=0.25),
    "Enamel_Cream":  dict(tex="enamel", tint=(0.95, 0.90, 0.78), tile=0.3, rough=0.3),
    "Enamel_Black":  dict(tex="enamel", tint=(0.04, 0.04, 0.045), tile=0.3, rough=0.25),
    "Enamel_White":  dict(tex="enamel", tint=(0.93, 0.93, 0.91), tile=0.3, rough=0.25),
    "Enamel_Orange": dict(tex="enamel", tint=(0.96, 0.46, 0.10), tile=0.3, rough=0.25),
    "Enamel_Pink":   dict(tex="enamel", tint=(0.95, 0.58, 0.68), tile=0.3, rough=0.25),
    "Felt_Green":    dict(tex="fabric", tint=(0.27, 0.48, 0.22), tile=0.2, rough=0.95),
    "Felt_Grey":     dict(tex="fabric", tint=(0.58, 0.57, 0.58), tile=0.12, rough=0.95),
    "Gravel":        dict(tex="plaster", tint=(0.52, 0.5, 0.47), tile=0.25, rough=0.95, bump=1.0),
    "Slate":         dict(tex="plaster", tint=(0.13, 0.17, 0.15), tile=0.7, rough=0.95, bump=0.25),
    "Plastic_Dark":  dict(color=(0.09, 0.09, 0.1), rough=0.45),
    "Plastic_Light": dict(color=(0.86, 0.86, 0.84), rough=0.4),
    "Glass":         dict(color=(0.85, 0.92, 1.0), rough=0.05, alpha=0.18),
    "Emissive_Warm": dict(color=(1.0, 0.86, 0.6), emission=(1.0, 0.78, 0.45), strength=8.0),
    "Flame":         dict(color=(1.0, 0.55, 0.15), emission=(1.0, 0.48, 0.10), strength=12.0),
    "Embers":        dict(tex="embers", emission_tex=True, strength=3.0, tile=0.4),
    "NightSky":      dict(tex="night_sky", emission_tex=True, strength=1.4, fit=True),
}


def _texture_path(tex, kind):
    path = os.path.join(TEXTURE_DIR, f"{tex}_{kind}.png")
    return path if os.path.exists(path) else None


def write_material_json():
    out = []
    for name, d in M.items():
        tex = d.get("tex")
        out.append({
            "name": name,
            "albedo": f"Assets/Art/Textures/{tex}_albedo.png" if tex else "",
            "normal": f"Assets/Art/Textures/{tex}_normal.png" if tex and _texture_path(tex, "normal") else "",
            "tint": list(d.get("tint", d.get("color", (1, 1, 1)))),
            "metallic": d.get("metal", 0.0),
            "smoothness": round(1.0 - d.get("rough", 0.5), 3),
            "emission": [c * d.get("strength", 0) for c in d.get("emission", (0, 0, 0))],
            "emissionFromAlbedo": d.get("emission_tex", False),
            "emissionStrength": d.get("strength", 0.0) if d.get("emission_tex") else 0.0,
            "alpha": d.get("alpha", 1.0),
            "bump": d.get("bump", 0.5),
        })
    path = os.path.join(ART_DIR, "Materials", "materials.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"materials": out}, f, indent=1)


def _socket(node, identifier, outputs=False):
    for s in (node.outputs if outputs else node.inputs):
        if s.identifier == identifier:
            return s
    raise KeyError(identifier)


def srgb_to_linear(color):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in color)


def mat(name):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    d = M[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nt = material.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = d.get("rough", 0.5)
    bsdf.inputs["Metallic"].default_value = d.get("metal", 0.0)
    tint = srgb_to_linear(d.get("tint", d.get("color", (1, 1, 1))))

    if "tex" in d:
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(_texture_path(d["tex"], "albedo"), check_existing=True)
        img.location = (-700, 300)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        _socket(mix, "Factor_Float").default_value = 1.0
        _socket(mix, "B_Color").default_value = (*tint, 1)
        nt.links.new(img.outputs["Color"], _socket(mix, "A_Color"))
        nt.links.new(_socket(mix, "Result_Color", outputs=True), bsdf.inputs["Base Color"])
        if d.get("emission_tex"):
            nt.links.new(img.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = d["strength"]
        normal_path = _texture_path(d["tex"], "normal")
        if normal_path and not d.get("emission_tex"):
            nimg = nt.nodes.new("ShaderNodeTexImage")
            nimg.image = bpy.data.images.load(normal_path, check_existing=True)
            nimg.image.colorspace_settings.name = "Non-Color"
            nimg.location = (-700, -100)
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = d.get("bump", 0.5)
            nt.links.new(nimg.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        bsdf.inputs["Base Color"].default_value = (*tint, 1)

    if "emission" in d:
        bsdf.inputs["Emission Color"].default_value = (*srgb_to_linear(d["emission"]), 1)
        bsdf.inputs["Emission Strength"].default_value = d["strength"]
    if "alpha" in d:
        bsdf.inputs["Transmission Weight"].default_value = 1.0
        bsdf.inputs["Alpha"].default_value = max(d["alpha"], 0.35)
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "BLENDED"
    return material


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.render.fps = 24


def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.1
    obj.location = location
    return link(obj, parent)


def _finish_mesh(name, bm, material, location, parent, smooth, uv_rotate=False):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    link(obj, parent)
    mesh.materials.append(mat(material))
    if M[material].get("fit"):
        fit_uv(obj)
    else:
        box_uv(obj, uv_rotate)
    if smooth:
        mesh.shade_smooth()
    return obj


def _transform(bm, rotation=(0, 0, 0), offset=(0, 0, 0), scale=None):
    if scale is not None:
        bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    if any(rotation):
        rx, ry, rz = (math.radians(a) for a in rotation)
        m = Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts)


def box(name, size, material, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0), parent=None,
        uv_rotate=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    _transform(bm, rotation, offset, scale=size)
    return _finish_mesh(name, bm, material, location, parent, False, uv_rotate)


def cylinder(name, radius, depth, material, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0),
             segments=24, radius_top=None, parent=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius_top is None else radius_top, depth=depth)
    _transform(bm, rotation, offset)
    obj = _finish_mesh(name, bm, material, location, parent, False)
    if smooth:
        auto_smooth(obj)
    return obj


def sphere(name, radius, material, location=(0, 0, 0), offset=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0),
           segments=24, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=max(8, segments // 2), radius=radius)
    _transform(bm, rotation, offset, scale=scale)
    return _finish_mesh(name, bm, material, location, parent, True)


def torus(name, major, minor, material, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0),
          major_segments=24, minor_segments=10, arc=360.0, parent=None):
    bm = bmesh.new()
    closed = arc >= 360.0
    rings = major_segments if closed else major_segments + 1
    for i in range(rings):
        a = math.radians(arc) * i / major_segments
        for j in range(minor_segments):
            b = 2 * math.pi * j / minor_segments
            r = major + minor * math.cos(b)
            bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(major_segments):
        i2 = (i + 1) % rings
        for j in range(minor_segments):
            j2 = (j + 1) % minor_segments
            bm.faces.new([bm.verts[i * minor_segments + j], bm.verts[i2 * minor_segments + j],
                          bm.verts[i2 * minor_segments + j2], bm.verts[i * minor_segments + j2]])
    _transform(bm, rotation, offset)
    return _finish_mesh(name, bm, material, location, parent, True)


def rod(name, start, end, radius, material, segments=12, radius_end=None, parent=None):
    start, end = Vector(start), Vector(end)
    direction = end - start
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius_end is None else radius_end, depth=direction.length)
    bmesh.ops.translate(bm, vec=Vector((0, 0, direction.length / 2)), verts=bm.verts)
    rot = Vector((0, 0, 1)).rotation_difference(direction.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    obj = _finish_mesh(name, bm, material, start, parent, False)
    auto_smooth(obj)
    return obj


def prism(name, points, depth, material, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0), parent=None,
          plane="XZ"):
    bm = bmesh.new()
    if plane == "XZ":
        back = [bm.verts.new((x, 0, z)) for x, z in points]
    else:
        back = [bm.verts.new((x, y, 0)) for x, y in points]
    face = bm.faces.new(back)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    vec = Vector((0, -depth, 0)) if plane == "XZ" else Vector((0, 0, depth))
    bmesh.ops.translate(bm, vec=vec, verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _transform(bm, rotation, offset)
    return _finish_mesh(name, bm, material, location, parent, False)


def lathe(name, profile, material, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0), segments=24,
          parent=None, smooth=True):
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segments),
                                        r * math.sin(2 * math.pi * i / segments), z)) for i in range(segments)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segments):
            i2 = (i + 1) % segments
            if len(a) == 1:
                bm.faces.new([a[0], b[i], b[i2]])
            elif len(b) == 1:
                bm.faces.new([a[i], a[i2], b[0]])
            else:
                bm.faces.new([a[i], a[i2], b[i2], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _transform(bm, rotation, offset)
    obj = _finish_mesh(name, bm, material, location, parent, False)
    if smooth:
        auto_smooth(obj)
    return obj


def curved_panel(name, profile, arc, material, centre_angle=-90.0, segments=12, parent=None):
    bm = bmesh.new()
    rows = []
    for r, z in profile:
        row = []
        for i in range(segments + 1):
            a = math.radians(centre_angle - arc / 2 + arc * i / segments)
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        for i in range(segments):
            bm.faces.new([a[i], a[i + 1], b[i + 1], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _finish_mesh(name, bm, material, (0, 0, 0), parent, True)
    return obj


def tube(name, points, radius, material, location=(0, 0, 0), parent=None, cyclic=False, resolution=2):
    cu = bpy.data.curves.new(name + "_Path", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = resolution
    cu.use_fill_caps = not cyclic
    spline = cu.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (co[0], co[1], co[2], 1.0)
    spline.use_cyclic_u = cyclic
    tmp = bpy.data.objects.new(name + "_Tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    mesh = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    mesh.name = name
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    link(obj, parent)
    mesh.materials.clear()
    mesh.materials.append(mat(material))
    box_uv(obj)
    mesh.shade_smooth()
    return obj


def path_curve(name, points, location=(0, 0, 0), parent=None, cyclic=True):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    spline = cu.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (co[0], co[1], co[2], 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, cu)
    obj.location = location
    return link(obj, parent)


def follow_curve(obj, curve_obj, spacing):
    a = obj.modifiers.new("Array", "ARRAY")
    a.fit_type = "FIT_CURVE"
    a.curve = curve_obj
    a.relative_offset_displace = (spacing, 0, 0)
    c = obj.modifiers.new("Curve", "CURVE")
    c.object = curve_obj
    c.deform_axis = "POS_X"
    return a, c


def squash(obj, scale, centre=(0, 0, 0)):
    c = Vector(centre)
    for v in obj.data.vertices:
        v.co = c + Vector(a * b for a, b in zip(v.co - c, scale))
    box_uv(obj)


def array_around(obj, count, axis, angle=None):
    pivot = bpy.data.objects.new(obj.name + "_ArrayStep", None)
    pivot.empty_display_size = 0.02
    link(pivot, obj)
    step = math.radians(angle if angle is not None else 360.0 / count)
    pivot.rotation_euler = tuple(step if a == axis else 0.0 for a in "XYZ")
    m = obj.modifiers.new("ArrayRound", "ARRAY")
    m.count = count
    m.use_relative_offset = False
    m.use_object_offset = True
    m.offset_object = pivot
    return m


def auto_smooth(obj, angle=40):
    mesh = obj.data
    mesh.shade_smooth()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle):
            e.smooth = False
    bm.to_mesh(mesh)
    bm.free()


def box_uv(obj, rotate=False):
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        tile = M[mesh.materials[poly.material_index].name].get("tile", 1.0)
        n = poly.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if axis == 0:
                u, v = co.y, co.z
            elif axis == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            if rotate:
                u, v = v, u
            uv.data[li].uv = (u / tile, v / tile)


def fit_uv(obj):
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    xs = [v.co.x for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    for li, loop in enumerate(mesh.loops):
        co = mesh.vertices[loop.vertex_index].co
        uv.data[li].uv = ((co.x - min(xs)) / (max(xs) - min(xs)), (co.z - min(zs)) / (max(zs) - min(zs)))


def bevel(obj, width, segments=2):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    return m


def mirror(obj, x=True, y=False, z=False, mirror_object=None, merge=True):
    m = obj.modifiers.new("Mirror", "MIRROR")
    m.use_axis = (x, y, z)
    m.mirror_object = mirror_object
    m.use_mirror_merge = merge
    return m


def array(obj, count, relative=None, constant=None, offset_object=None, merge=False):
    m = obj.modifiers.new("Array", "ARRAY")
    m.count = count
    m.use_relative_offset = relative is not None
    if relative is not None:
        m.relative_offset_displace = relative
    m.use_constant_offset = constant is not None
    if constant is not None:
        m.constant_offset_displace = constant
    if offset_object is not None:
        m.use_object_offset = True
        m.offset_object = offset_object
    m.use_merge_vertices = merge
    return m


def subdivision(obj, levels=2):
    m = obj.modifiers.new("Subdivision", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    obj.data.shade_smooth()
    return m


def solidify(obj, thickness):
    m = obj.modifiers.new("Solidify", "SOLIDIFY")
    m.thickness = thickness
    return m


def armature(name, bones, parent=None, location=(0, 0, 0)):
    data = bpy.data.armatures.new(name + "_Rig")
    data.display_type = "STICK"
    arm = bpy.data.objects.new(name + "_Rig", data)
    arm.location = location
    link(arm, parent)
    arm.show_in_front = True
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for bone_name, head, tail, parent_name in bones:
        eb = data.edit_bones.new(bone_name)
        eb.head, eb.tail = head, tail
        if parent_name:
            eb.parent = data.edit_bones[parent_name]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return arm


def attach(objects, arm, bone):
    bpy.context.view_layer.update()
    for obj in objects:
        world = obj.matrix_world.copy()
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = bone
        bpy.context.view_layer.update()
        obj.matrix_world = world


def _bone_order(arm):
    def depth(b):
        d = 0
        while b.parent:
            b, d = b.parent, d + 1
        return d
    return sorted(arm.pose.bones, key=lambda pb: depth(pb.bone))


def set_pose(arm, rotations=None, offsets=None, scales=None):
    rotations, offsets, scales = rotations or {}, offsets or {}, scales or {}
    world_delta = {}
    for pb in _bone_order(arm):
        own = Euler([math.radians(a) for a in rotations.get(pb.name, (0, 0, 0))], "XYZ").to_matrix()
        parent = world_delta.get(pb.parent.name) if pb.parent else Matrix.Identity(3)
        delta = parent @ own
        world_delta[pb.name] = delta
        if pb.parent:
            head = pb.parent.matrix @ (pb.parent.bone.matrix_local.inverted() @ pb.bone.matrix_local).translation
        else:
            head = pb.bone.head_local.copy()
        head += Vector(offsets.get(pb.name, (0, 0, 0)))
        rest_rot = pb.bone.matrix_local.to_3x3()
        pb.matrix = Matrix.Translation(head) @ (delta @ rest_rot).to_4x4()
        pb.scale = scales.get(pb.name, (1, 1, 1))
        bpy.context.view_layer.update()


def keyframe(arm, frame, previous):
    for pb in arm.pose.bones:
        q = pb.rotation_quaternion.copy()
        last = previous.get(pb.name)
        if last is not None and last.dot(q) < 0:
            q.negate()
            pb.rotation_quaternion = q
        previous[pb.name] = q
        pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
        pb.keyframe_insert("location", frame=frame, group=pb.name)
        pb.keyframe_insert("scale", frame=frame, group=pb.name)


def make_action(arm, name, keys):
    arm.animation_data_create()
    action = bpy.data.actions.new(f"{name}")
    action.use_fake_user = True
    arm.animation_data.action = action
    previous = {}
    for key in keys:
        frame, rotations = key[0], key[1]
        offsets = key[2] if len(key) > 2 else None
        scales = key[3] if len(key) > 3 else None
        set_pose(arm, rotations, offsets, scales)
        keyframe(arm, frame, previous)
    set_pose(arm)
    return action


def asset_objects(root):
    return [root] + list(root.children_recursive)


def export_fbx(root, category, animated=False):
    path = os.path.join(ART_DIR, category, root.name + ".fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in asset_objects(root):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True,
        object_types={"MESH", "EMPTY", "ARMATURE"},
        use_mesh_modifiers=True, mesh_smooth_type="FACE",
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", bake_space_transform=False,
        add_leaf_bones=False, armature_nodetype="NULL",
        bake_anim=animated, bake_anim_use_all_actions=animated, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
        path_mode="STRIP",
    )
    return path


def triangle_count(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for obj in objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(depsgraph)
            mesh = ev.to_mesh()
            total += sum(len(p.vertices) - 2 for p in mesh.polygons)
            ev.to_mesh_clear()
    return total


def world_bounds(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    pts = []
    for obj in objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(depsgraph)
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def use_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            devices = [d for d in prefs.devices if d.type == kind]
            if devices:
                for d in prefs.devices:
                    d.use = d.type == kind
                return kind
        except TypeError:
            continue
    return None


def _color_management(scene):
    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "AgX - Punchy", "None"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue


def studio(objects, collection_name="Studio", angle=(0.75, -1.0, 0.42), lens=60, fstop=4.0):
    lo, hi = world_bounds(objects)
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.05)
    coll = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(coll)

    def add(obj):
        coll.objects.link(obj)
        return obj

    size = radius * 12
    bm = bmesh.new()
    pts = [(-size, -size, 0), (size, -size, 0), (size, size * 0.3, 0), (-size, size * 0.3, 0)]
    v = [bm.verts.new(p) for p in pts]
    bm.faces.new(v)
    edge = [e for e in bm.edges if e.verts[0].co.y > 0 and e.verts[1].co.y > 0][0]
    ext = bmesh.ops.extrude_edge_only(bm, edges=[edge])
    bmesh.ops.translate(bm, vec=(0, size * 0.3, size), verts=[x for x in ext["geom"] if isinstance(x, bmesh.types.BMVert)])
    mesh = bpy.data.meshes.new("Backdrop")
    bm.to_mesh(mesh)
    bm.free()
    backdrop = add(bpy.data.objects.new("Backdrop", mesh))
    backdrop.location = (center.x, center.y, lo.z)
    b = backdrop.modifiers.new("Curve", "BEVEL")
    b.width = size * 0.35
    b.segments = 12
    mesh.shade_smooth()
    mat_backdrop = bpy.data.materials.new("Backdrop")
    mat_backdrop.use_nodes = True
    bsdf = next(n for n in mat_backdrop.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.32, 0.30, 0.29, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    mesh.materials.append(mat_backdrop)

    def area(name, loc, energy, color, size_m):
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.color = color
        light.size = size_m
        obj = add(bpy.data.objects.new(name, light))
        obj.location = loc
        direction = center - Vector(loc)
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return obj

    r = radius
    area("Key", center + Vector((-2.2 * r, -2.4 * r, 2.6 * r)), 260 * r * r, (1.0, 0.93, 0.85), 2.0 * r)
    area("Fill", center + Vector((2.6 * r, -1.8 * r, 1.2 * r)), 70 * r * r, (0.80, 0.88, 1.0), 2.5 * r)
    area("Rim", center + Vector((0.8 * r, 2.8 * r, 2.4 * r)), 200 * r * r, (1.0, 0.95, 0.9), 1.2 * r)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam_data.clip_start = 0.005
    cam_data.clip_end = 200
    cam = add(bpy.data.objects.new("Camera", cam_data))
    direction = Vector(angle).normalized()
    vertical_fov = 2 * math.atan((36 * 9 / 16) / (2 * lens))
    distance = radius / math.sin(vertical_fov / 2) * 0.85
    cam.location = center + direction * distance
    cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = distance
    cam_data.dof.aperture_fstop = fstop * max(radius, 0.1) * 4
    bpy.context.scene.camera = cam

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.05, 0.05, 0.06)
    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
            bg.inputs["Strength"].default_value = 0.5
    return cam


def render_still(path, samples=128, width=1920, height=1080):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU" if use_gpu() else "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    _color_management(scene)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_video(path, frame_start, frame_end, width=1280, height=720):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.frame_start, scene.frame_end = frame_start, frame_end
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    _color_management(scene)
    scene.render.filepath = path
    bpy.ops.render.render(animation=True)


def queue_actions_for_preview(arm, actions, gap=8):
    track = arm.animation_data.nla_tracks.new()
    track.name = "Preview"
    frame = 1
    for action in actions:
        start = int(action.frame_range[0])
        strip = track.strips.new(action.name, frame, action)
        frame = int(strip.frame_end) + gap
    arm.animation_data.action = None
    return frame
