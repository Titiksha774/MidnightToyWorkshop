import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

import workshop_lib as w

PROTOTYPE_MATERIALS = {
    "Turntable_Base": "Wood_Walnut",
    "Turntable_Plate": "Enamel_Red",
    "Turntable_Knob": "Metal_Brass",
    "PartsTray_Box": "Wood_Oak",
    "PartsTray_Dividers": "Wood_Walnut",
}


def texture_prototype_parts():
    changed = False
    for obj in bpy.data.objects:
        name = PROTOTYPE_MATERIALS.get(obj.name)
        if obj.type != "MESH" or name is None:
            continue
        obj.data.materials.clear()
        obj.data.materials.append(w.mat(name))
        w.box_uv(obj)
        changed = True
    return changed


def show_textures_in_viewport():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out_path, render_path = args[0], (args[1] if len(args) > 1 else None)
    textured = texture_prototype_parts()
    show_textures_in_viewport()
    bpy.ops.file.pack_all()
    if textured and render_path:
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        for light in [o for o in bpy.data.objects if o.type == "LIGHT"]:
            light.hide_render = True
        w.studio(meshes, fstop=14.0)
        w.render_still(render_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    missing = [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]
    print("SUBMISSION", os.path.basename(out_path), "unpacked images:", missing)


if __name__ == "__main__":
    main()
