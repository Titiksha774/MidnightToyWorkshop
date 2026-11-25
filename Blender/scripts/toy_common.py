import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

BLENDER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BLENDER_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "Assets")
PALETTE_PNG = os.path.join(ASSETS_DIR, "Materials", "ToyPalette.png")

GRID = 8
CELL = 32

PALETTE = [
    ("wood_light", "C8925A"), ("wood_dark", "7A4E2D"), ("brick", "A8452F"), ("brick_alt", "B95A3E"),
    ("mortar", "8C8378"), ("grass", "5E9E4A"), ("train_blue", "2F6DB5"), ("yellow", "F2C230"),
    ("red", "D23B2F"), ("black", "2A2A2E"), ("white", "F2EEE6"), ("metal", "9AA3AD"),
    ("skin", "E9B994"), ("lamp_green", "2F7D5B"), ("cream", "F5E3B3"), ("hat_brown", "4A3426"),
    ("floor", "6B4A33"), ("floor_alt", "7C5A3F"), ("rail", "5A5F66"), ("gold", "D9A93B"),
    ("navy", "2B3A5C"), ("bulb", "FFF3C4"), ("apron", "8FA6B8"), ("orange", "E07B2E"),
]
COLOR_INDEX = {name: i for i, (name, _) in enumerate(PALETTE)}


def _hex_to_rgba(hex_code):
    return tuple(int(hex_code[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def palette_image():
    size = GRID * CELL
    if not os.path.exists(PALETTE_PNG):
        os.makedirs(os.path.dirname(PALETTE_PNG), exist_ok=True)
        image = bpy.data.images.new("ToyPalette", size, size, alpha=False)
        pixels = [0.0] * (size * size * 4)
        for index in range(GRID * GRID):
            rgba = _hex_to_rgba(PALETTE[index][1]) if index < len(PALETTE) else (1, 0, 1, 1)
            cx, cy = index % GRID, index // GRID
            for y in range(cy * CELL, (cy + 1) * CELL):
                row = (size - 1 - y) * size
                for x in range(cx * CELL, (cx + 1) * CELL):
                    pixels[(row + x) * 4:(row + x) * 4 + 4] = rgba
        image.pixels = pixels
        image.filepath_raw = PALETTE_PNG
        image.file_format = "PNG"
        image.save()
        bpy.data.images.remove(image)
    return bpy.data.images.load(PALETTE_PNG, check_existing=True)


def palette_material():
    material = bpy.data.materials.get("ToyPalette")
    if material is not None:
        return material

    material = bpy.data.materials.new("ToyPalette")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.6
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = palette_image()
    texture.interpolation = "Closest"
    material.node_tree.links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    return material


def uv_for(color):
    index = COLOR_INDEX[color]
    cx, cy = index % GRID, index // GRID
    return ((cx + 0.5) / GRID, 1.0 - (cy + 0.5) / GRID)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"


def empty(name, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.05
    obj.location = location
    obj.parent = parent
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _object_from_bmesh(name, bm, location, color, parent, smooth):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.parent = parent
    bpy.context.scene.collection.objects.link(obj)
    paint(obj, color)
    if smooth:
        mesh.shade_smooth()
    return obj


def box(name, size, location=(0, 0, 0), offset=(0, 0, 0), color="wood_light", parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts)
    return _object_from_bmesh(name, bm, location, color, parent, smooth=False)


def cylinder(name, radius, depth, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0),
             segments=24, radius_top=None, color="wood_light", parent=None, smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius_top is None else radius_top, depth=depth)
    _rotate_and_offset(bm, rotation, offset)
    return _object_from_bmesh(name, bm, location, color, parent, smooth)


def sphere(name, radius, location=(0, 0, 0), offset=(0, 0, 0), scale=(1, 1, 1), segments=16,
           color="wood_light", parent=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=max(8, segments // 2), radius=radius)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts)
    return _object_from_bmesh(name, bm, location, color, parent, smooth)


def torus(name, major_radius, minor_radius, location=(0, 0, 0), offset=(0, 0, 0), rotation=(0, 0, 0),
          major_segments=20, minor_segments=8, color="gold", parent=None):
    bm = bmesh.new()
    for i in range(major_segments):
        a = 2 * math.pi * i / major_segments
        for j in range(minor_segments):
            b = 2 * math.pi * j / minor_segments
            r = major_radius + minor_radius * math.cos(b)
            bm.verts.new((r * math.cos(a), r * math.sin(a), minor_radius * math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(major_segments):
        for j in range(minor_segments):
            i2, j2 = (i + 1) % major_segments, (j + 1) % minor_segments
            bm.faces.new([bm.verts[i * minor_segments + j], bm.verts[i2 * minor_segments + j],
                          bm.verts[i2 * minor_segments + j2], bm.verts[i * minor_segments + j2]])
    _rotate_and_offset(bm, rotation, offset)
    return _object_from_bmesh(name, bm, location, color, parent, smooth=True)


def rod(name, start, end, radius, segments=12, color="metal", parent=None):
    start, end = Vector(start), Vector(end)
    direction = end - start
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius,
                          depth=direction.length)
    bmesh.ops.translate(bm, vec=Vector((0, 0, direction.length / 2)), verts=bm.verts)
    rot = Vector((0, 0, 1)).rotation_difference(direction.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    return _object_from_bmesh(name, bm, start, color, parent, smooth=True)


def _rotate_and_offset(bm, rotation, offset):
    if any(rotation):
        rx, ry, rz = (math.radians(a) for a in rotation)
        matrix = (Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X"))
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts)


def paint(obj, color):
    mesh = obj.data
    if not mesh.materials:
        mesh.materials.append(palette_material())
    uv_layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    u, v = uv_for(color)
    for loop_uv in uv_layer.data:
        loop_uv.uv = (u, v)


def join(name, objects, location=(0, 0, 0), parent=None, smooth=False):
    bm = bmesh.new()
    to_local = Matrix.Translation(-Vector(location))
    for obj in objects:
        mesh = obj.data.copy()
        mesh.transform(to_local @ obj.matrix_basis)
        bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
    for obj in objects:
        old_mesh = obj.data
        bpy.data.objects.remove(obj)
        bpy.data.meshes.remove(old_mesh)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.parent = parent
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(palette_material())
    if smooth:
        mesh.shade_smooth()
    return obj


def bevel(obj, width, segments=2):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    return mod


def mirror(obj, x=True, y=False, z=False, merge=True, clipping=False):
    mod = obj.modifiers.new("Mirror", "MIRROR")
    mod.use_axis = (x, y, z)
    mod.use_mirror_merge = merge
    mod.use_clip = clipping
    return mod


def array(obj, count, relative=None, constant=None, fit_curve=None, merge=False):
    mod = obj.modifiers.new("Array", "ARRAY")
    if fit_curve is not None:
        mod.fit_type = "FIT_CURVE"
        mod.curve = fit_curve
    else:
        mod.count = count
    mod.use_relative_offset = relative is not None
    if relative is not None:
        mod.relative_offset_displace = relative
    mod.use_constant_offset = constant is not None
    if constant is not None:
        mod.constant_offset_displace = constant
    mod.use_merge_vertices = merge
    return mod


def subdivision(obj, levels=2, render_levels=None):
    mod = obj.modifiers.new("Subdivision", "SUBSURF")
    mod.subdivision_type = "CATMULL_CLARK"
    mod.levels = levels
    mod.render_levels = levels if render_levels is None else render_levels
    obj.data.shade_smooth()
    return mod


def curve_deform(obj, curve_obj):
    mod = obj.modifiers.new("Curve", "CURVE")
    mod.object = curve_obj
    mod.deform_axis = "POS_X"
    return mod


def oval_curve(name, radius_x, radius_y, location=(0, 0, 0)):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(3)
    k = 0.5523
    points = [(radius_x, 0), (0, radius_y), (-radius_x, 0), (0, -radius_y)]
    tangents = [(0, radius_y * k), (-radius_x * k, 0), (0, -radius_y * k), (radius_x * k, 0)]
    for point, (x, y), (tx, ty) in zip(spline.bezier_points, points, tangents):
        point.co = (x, y, 0)
        point.handle_left_type = point.handle_right_type = "FREE"
        point.handle_left = (x - tx, y - ty, 0)
        point.handle_right = (x + tx, y + ty, 0)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _asset_objects(root):
    return [root] + list(root.children_recursive)


def triangle_count(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for obj in objects:
        if obj.type != "MESH":
            continue
        mesh = obj.evaluated_get(depsgraph).to_mesh()
        total += sum(len(p.vertices) - 2 for p in mesh.polygons)
        obj.evaluated_get(depsgraph).to_mesh_clear()
    return total


def _world_bounds(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners = []
    for obj in objects:
        if obj.type == "MESH":
            evaluated = obj.evaluated_get(depsgraph)
            corners += [evaluated.matrix_world @ Vector(c) for c in evaluated.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return low, high


def export_fbx(root, category):
    path = os.path.join(ASSETS_DIR, "Models", category, root.name + ".fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in _asset_objects(root):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"MESH", "EMPTY"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        path_mode="STRIP",
        bake_anim=False,
    )
    return path


def add_preview_camera_and_light(objects):
    low, high = _world_bounds(objects)
    center = (low + high) / 2
    size = max((high - low).length, 0.05)

    camera_data = bpy.data.cameras.new("Camera")
    camera_data.lens = 50
    camera_data.clip_start = 0.001
    camera_data.clip_end = 100
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    direction = Vector((0.9, -1.4, 0.8)).normalized()
    camera.location = center + direction * size * 1.55
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    bpy.context.scene.collection.objects.link(sun)

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.18, 0.18, 0.2)
    if world.node_tree is None and hasattr(world, "use_nodes"):
        world.use_nodes = True
    if world.node_tree is not None:
        background = world.node_tree.nodes.get("Background")
        if background is not None:
            background.inputs["Color"].default_value = (0.18, 0.18, 0.2, 1)
            background.inputs["Strength"].default_value = 1.0


def render_preview(path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 500
    scene.render.film_transparent = False
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 16
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def finish(root, category):
    objects = _asset_objects(root)
    tris = triangle_count(objects)
    fbx_path = export_fbx(root, category)

    out_dir = os.path.join(BLENDER_DIR, category)
    os.makedirs(out_dir, exist_ok=True)
    add_preview_camera_and_light(objects)
    preview = os.path.join(out_dir, root.name + "_preview.png")
    render_preview(preview)

    blend_path = os.path.join(out_dir, root.name + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"ASSET {root.name:<14} {tris:>6} tris  ->  {os.path.relpath(fbx_path, PROJECT_DIR)}")
    return tris
