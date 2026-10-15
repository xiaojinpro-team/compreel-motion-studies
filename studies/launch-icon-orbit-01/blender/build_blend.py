"""Icon Cloud Intro · Blender builder (MIT)
Same motion as the web version (samples.json, screen-space samples per frame) converted to real 3D: a perspective camera pulling back,
every icon an image plane facing the lens with its own depth over time, title as Blender text, Cycles motion blur on the rush.
Usage: blender -b -P build_blend.py -- <study_dir> [--line1 Introducing] [--line2 LaunchReel]

(中文)Blender 版构建脚本
把网页版同一套运动(samples.json,逐帧屏幕空间采样)换算成真 3D:透视相机推拉 + 每个图标是一块面向镜头的图片平面(深度 z 随时间变化),
标题用文字对象,冲镜段用 Blender 自带运动模糊(快门逐帧关键帧)。
用法:Blender -b -P build_blend.py -- <template_dir> [--line1 Introducing] [--line2 LaunchReel] [--render f0-f1]
"""
import bpy, json, math, os, sys
argv = sys.argv[sys.argv.index("--") + 1:]
TD = argv[0]; opt = dict(zip(argv[1::2], argv[2::2]))
LINE1 = opt.get("--line1", "Introducing"); LINE2 = opt.get("--line2", "LaunchReel")
C1 = opt.get("--line1Color", "000000"); C2 = opt.get("--line2Color", "D2412A")
S = json.load(open(f"{TD}/samples.json")); W, H = S["size"]; FPS = S["fps"]; times = S["times"]
U = 0.01                               # 1 px = 0.01 Blender unit
FOV = 40.0; F = (H / 2) / math.tan(math.radians(FOV / 2))   # focal length in px (same as motion-kit)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = W, H, FPS
sc.frame_start, sc.frame_end = 0, 99
sc.render.engine = "CYCLES"           # Cycles: correct alpha + motion blur on every surface (EEVEE Next left artefacts on scaled alpha cards)
sc.cycles.samples = 24; sc.cycles.use_denoising = False; sc.cycles.transparent_max_bounces = 64; sc.cycles.max_bounces = 2
sc.cycles.use_adaptive_sampling = False; sc.cycles.pixel_filter_type = "BLACKMAN_HARRIS"; sc.cycles.filter_width = 1.2
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = "GPU"
except Exception: pass
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
lin = lambda h: tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4))
# world = flat background colour #F3F3F5
w = bpy.data.worlds.new("bg"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*lin("F3F3F5"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
# camera: looks down -Z at the z=0 "screen plane"; distance animated
cd = bpy.data.cameras.new("cam"); cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24; cd.lens = 12 / math.tan(math.radians(FOV / 2)); cd.clip_start = 0.01; cd.clip_end = 1000
cam = bpy.data.objects.new("Camera", cd); sc.collection.objects.link(cam); sc.camera = cam
idx = {L["id"]: L for L in S["layers"]}
t46 = times.index(46); icon = idx["icon"]; s_icon46 = icon["samples"][t46][2]
def cam_dist(i, t):
    if t >= 58: return F
    return F * s_icon46 / max(icon["samples"][i][2], 1e-6)
for i, t in enumerate(times):
    cam.location = (0, 0, cam_dist(i, t) * U); cam.keyframe_insert("location", frame=t)
def unlit_material(name, img_path=None, rgb=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader"); mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    op = nt.nodes.new("ShaderNodeValue"); op.name = "opacity"; op.outputs[0].default_value = 1.0
    if img_path:
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(img_path); tex.interpolation = "Cubic"
        nt.links.new(tex.outputs["Color"], em.inputs["Color"]); nt.links.new(tex.outputs["Alpha"], mul.inputs[0])
    else:
        em.inputs["Color"].default_value = (*rgb, 1); mul.inputs[0].default_value = 1.0
    nt.links.new(op.outputs[0], mul.inputs[1]); nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
    # dithered (alpha-hashed) surfaces get EEVEE motion blur; blended ones do not
    if hasattr(m, "surface_render_method"): m.surface_render_method = "DITHERED"
    else: m.blend_method = "HASHED"
    return m, op
def plane(name, w_px, h_px, anchor, mat):
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (w_px * U, h_px * U, 1); bpy.ops.object.transform_apply(scale=True)
    ax, ay = anchor; o.data.transform(__import__("mathutils").Matrix.Translation(((0.5 - ax) * w_px * U, -(0.5 - ay) * h_px * U, 0)))
    o.data.materials.append(mat)
    if hasattr(o, "visible_shadow"): o.visible_shadow = False
    return o
cards = []
for L in S["layers"]:
    if L["id"] in ("bg",) or L["id"].startswith("title_"): continue
    tex = f"{TD}/canvas2d/textures/{L['texture']}.png"
    img = bpy.data.images.load(tex); tw, th = img.size
    if L["id"] == "bg_gradient":
        m, op = unlit_material("gradient", tex); o = plane("gradient", W, H, [0.5, 0.5], m); o.location = (0, 0, -0.5 * U)
        for i, t in enumerate(times): op.outputs[0].default_value = L["samples"][i][5]; op.outputs[0].keyframe_insert("default_value", frame=t)
        continue
    sx46 = L["samples"][t46][2]
    m, op = unlit_material(L["id"], tex); o = plane(L["id"], tw * sx46, th * sx46, L["anchor"], m); cards.append(o)
    for i, t in enumerate(times):
        x, y, sx, sy, rot, opac = L["samples"][i]
        k = max(sx / sx46, 1e-4); D = cam_dist(i, t); d = F / k; z = D - d          # card depth so that its screen scale is k
        o.location = ((x - W / 2) * d / F * U, -(y - H / 2) * d / F * U, z * U); o.rotation_euler = (0, 0, math.radians(-rot))
        o.keyframe_insert("location", frame=t); o.keyframe_insert("rotation_euler", frame=t)
        op.outputs[0].default_value = max(0.0, min(1.0, opac)); op.outputs[0].keyframe_insert("default_value", frame=t)
# titles: text objects on the screen plane (camera is home from frame 58)
fnt = bpy.data.fonts.load(f"{TD}/canvas2d/fonts/Inter-SemiBold-NoOverlap.ttf")   # overlaps removed: Blender fills curves even-odd
def title(name, text, hexcol, L):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = text; cu.font = fnt; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o)
    # size so that "Introducing" is ~786 px wide like the web page (measured once, then reused for line2)
    cu.size = 1.0; bpy.context.view_layer.update(); probe = bpy.data.curves.new("probe", "FONT"); probe.body = "Introducing"; probe.font = fnt
    po = bpy.data.objects.new("probe", probe); sc.collection.objects.link(po); bpy.context.view_layer.update()
    pw = po.dimensions.x; bpy.data.objects.remove(po); cu.size = 764 * U / pw   # ink width of "Introducing" on the web page
    m, op = unlit_material(name, rgb=lin(hexcol)); o.data.materials.append(m)
    if hasattr(m, "surface_render_method"): m.surface_render_method = "DITHERED"   # text glyphs self-overlap: blended mode breaks letters such as "R"
    for i, t in enumerate(times):
        x, y, sx, sy, rot, opac = L["samples"][i]
        o.location = ((x - W / 2) * U, -(y - 10 - H / 2) * U, 0.2 * U); o.keyframe_insert("location", frame=t)   # -10 px: Blender centres on the glyph box
        op.outputs[0].default_value = max(0.0, min(1.0, opac)); op.outputs[0].keyframe_insert("default_value", frame=t)
title("title_line1", LINE1, C1, idx["title_line1"]); title("title_line2", LINE2, C2, idx["title_line2"])
# linear interpolation everywhere (samples are dense)
for a in bpy.data.actions:
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
for m in bpy.data.materials:
    if m.node_tree and m.node_tree.animation_data and m.node_tree.animation_data.action:
        for fc in m.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# motion blur only on the rush (shutter keyed per frame, same values as the web timeline)
sc.render.use_motion_blur = True
shut = {f: 0.0 for f in range(0, 100)}; shut.update({55: 0.40, 56: 0.62, 57: 0.68})
for f, v in shut.items(): sc.render.motion_blur_shutter = max(v, 0.0001); sc.render.keyframe_insert("motion_blur_shutter", frame=f)
if hasattr(sc.eevee, "motion_blur_steps"): sc.eevee.motion_blur_steps = 8
if hasattr(sc.eevee, "taa_render_samples"): sc.eevee.taa_render_samples = 64
sc.render.film_transparent = False
for k in ("use_shadows", "use_raytracing", "use_gtao", "use_bloom", "use_ssr"):
    if hasattr(sc.eevee, k): setattr(sc.eevee, k, False)
# per-frame shutter table (EEVEE ignores animated shutter in batch renders): render_blender.py applies it frame by frame
sc["shutter_table"] = {str(f): v for f, v in shut.items()}
bpy.ops.file.pack_all()   # textures + font inside the .blend: the file is self-contained
bpy.ops.wm.save_as_mainfile(filepath=f"{TD}/blender/icon-cloud-intro.blend")
if "--render" in opt:
    a, b = map(int, opt["--render"].split("-")); sc.frame_start, sc.frame_end = a, b
    sc.render.image_settings.file_format = "PNG"; sc.render.filepath = f"{TD}/blender/frames/"
    bpy.ops.render.render(animation=True)
print("BUILD OK", len(cards), "cards")
