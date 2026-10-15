"""逐帧Render icon-cloud-intro.blend frame by frame; motion blur only where shutter_table says (the rush, frames 55–57). 逐帧渲染:每帧按 shutter_table 打开/关闭运动模糊(只有冲镜三帧开)。
用法:Blender -b icon-cloud-intro.blend -P render_blender.py -- <out_dir> [f0-f1]"""
import bpy, sys, os
argv = sys.argv[sys.argv.index("--") + 1:]; out = argv[0]; a, b = map(int, (argv[1] if len(argv) > 1 else "0-99").split("-"))
sc = bpy.context.scene; tab = sc.get("shutter_table", {}); os.makedirs(out, exist_ok=True)
sc.render.image_settings.file_format = "PNG"
for f in range(a, b + 1):
    v = float(tab.get(str(f), 0.0)); sc.render.use_motion_blur = v > 0.01
    if v > 0.01: sc.render.motion_blur_shutter = v
    sc.frame_set(f); sc.render.filepath = os.path.join(out, f"{f:06d}.png"); bpy.ops.render.render(write_still=True)
