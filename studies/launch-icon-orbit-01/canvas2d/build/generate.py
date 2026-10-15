"""Icon Cloud Intro · parametric motion generator (no per-frame data).
Motion = items locked on a 9×5 grid + an eased camera pull-back + each item settling from a depth Z onto the grid
(one shared ease) + each item's own spin + a radial rush outwards with per-frame shutter.
Usage: python3 generate.py <slot_map.json> <icons_dir> <out_dir> [motion_params.json]

参数化运动生成器(不含逐帧数据)
运动 = 物件固定在网格点上 + 相机推拉(平滑缓动)+ 每个物件从镜头前深度 Z 缓动落到网格平面(全局同一条缓动)+ 冲镜(全局外扩函数)
用法:python3 generate.py <slot_map.json> <icons_dir> <out_render_dir> [motion_params.json]
"""
import json, sys, os, math, shutil
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__))
SM, ICONS, OUT = sys.argv[1:4]; PP = sys.argv[4] if len(sys.argv) > 4 else f"{H}/motion_params.json"
M = json.load(open(PP)); smap = json.load(open(SM)); os.makedirs(f"{OUT}/textures", exist_ok=True)
C = np.array(M["grid"]["center"], float); DX, DY = M["grid"]["dx"], M["grid"]["dy"]
def bez(u, x1, y1, x2, y2):
    s = np.linspace(0, 1, 512); bx = 3*(1-s)**2*s*x1 + 3*(1-s)*s*s*x2 + s**3; by = 3*(1-s)**2*s*y1 + 3*(1-s)*s*s*y2 + s**3
    return float(np.interp(min(max(u, 0.0), 1.0), bx, by))
def ease(spec, u):
    if spec == "linear": return min(max(u, 0.0), 1.0)
    return bez(u, *spec["bezier"])
def seg_value(segs, f):
    s = next((s for s in segs if s["f0"] <= f <= s["f1"]), segs[0] if f < segs[0]["f0"] else segs[-1])
    u = (min(max(f, s["f0"]), s["f1"]) - s["f0"]) / max(s["f1"] - s["f0"], 1e-9); e = ease(s["ease"], u)
    if s.get("space") == "log": return math.exp(math.log(s["from"]) + (math.log(s["to"]) - math.log(s["from"])) * e)
    return s["from"] + (s["to"] - s["from"]) * e
def camera_dn(f): return seg_value(M["camera_dn"], min(f, 46)) / seg_value(M["camera_dn"], 46)
SE = M["settle_ease"]
def depth(slot, f):
    t0, t1 = slot["t0"], slot["t1"]; return slot["Z"] * (1 - ease(SE, (f - t0) / (t1 - t0)))
def interp_tab(tab, f, before=0.0):
    ks = sorted((float(k), v) for k, v in tab.items()); xs = [k for k, _ in ks]; ys = [v for _, v in ks]
    if f <= xs[0]: return before if f < xs[0] else ys[0]
    if f >= xs[-1]: return ys[-1] + (ys[-1] - ys[-2]) * (f - xs[-1]) if len(ys) > 1 else ys[-1]
    return float(np.interp(f, xs, ys))
def rush(f, r):
    if f <= 54: return 1.0
    A = interp_tab(M["rush"]["A"], f); return math.exp(A * (r / 1000.0) ** M["rush"]["p"])
def spin(slot, f):
    """item's own rotation (deg, clockwise), measured per slot; slots without "rot" stay still"""
    R = slot.get("rot")
    if not R: return 0.0
    c = R["poly"]; a, b = R["t_from"], R["t_to"]; ff = min(max(f, a), b)
    v = float(np.polyval(c, ff - 46))
    if f > b: v += R["slope_after"] * (f - b)
    return v
def opacity(f): return 1.0 if f <= 55 else max(0.0, min(1.0, interp_tab(M["opacity"], f)))
def content_box(p):
    a = np.asarray(Image.open(p).convert("RGBA"))[..., 3]; ys, xs = np.where(a > 40)
    return xs.min(), xs.max(), ys.min(), ys.max(), a.shape[1], a.shape[0]
FS = list(range(0, 54)) + [54 + i * 0.25 for i in range(0, 17)]
layers = [dict(id="bg", texture="bg", anchor=[0.5, 0.5], frames=[dict(f=0, x=960, y=540, sx=1, sy=1, rot=0, opacity=1)]),
          dict(id="bg_gradient", texture="gradient", anchor=[0.5, 0.5], frames=[dict(f=f, x=960, y=540, sx=1, sy=1, rot=0, opacity=v) for f, v in ((0, 0), (57, 0), (58, 0.05), (64, 0.35), (70, 0.65), (78, 1.0), (99, 1.0))])]
def card(lid, label, foot, posfn):
    src = f"{ICONS}/{label}.png"; dst = f"{OUT}/textures/{label}.png"
    if not os.path.exists(dst) or not os.path.samefile(src, dst): shutil.copy(src, dst)
    x0, x1, y0, y1, W, Hh = content_box(src); cw, ch = x1 - x0, y1 - y0
    base = (min(foot["foot_w"] / cw, foot["foot_h"] / ch) * 1.08) if lid != "icon" else foot["foot_w"] / cw
    fr = []
    for f in FS:
        x, y, k, op, *rest = posfn(f); rot = rest[0] if rest else 0.0
        fr.append(dict(f=f, x=round(x, 3), y=round(y, 3), sx=round(base * k, 6), sy=round(base * k, 6), rot=round(rot, 3), opacity=round(op, 4)))
    fr.append(dict(fr[-1], f=58.25, opacity=0))
    return dict(id=lid, texture=label, anchor=[(x0 + x1) / 2 / W, (y0 + y1) / 2 / Hh], frames=fr)
sizes = M["slot_size_px"]
def icon_pos(f):
    k = 1 / camera_dn(f) if f <= 54 else interp_tab({"54": 1.0, **M["icon_growth"]}, f)
    op = opacity(f) * (max(0.0, 1 - (f - 56)) if f > 56 else 1.0); return C[0], C[1], k, op
L_icon = card("icon", smap["icon"], sizes["icon"], icon_pos)
objs = []
for sid, slot in M["slots"].items():
    if sid not in smap: continue
    g = np.array([slot["col"] * DX, slot["row"] * DY]); r = float(np.hypot(*g))
    def pos(f, g=g, r=r, slot=slot):
        den = camera_dn(f) - depth(slot, f)
        if den <= 0.03: return C[0] + g[0] * 40, C[1] + g[1] * 40, 1.0, 0.0      # still behind the lens
        q = rush(f, r); p = C + g * q / den; return p[0], p[1], q ** M["rush"]["scale_exponent"] / den, opacity(f), spin(slot, f)
    objs.append((slot["Z"], card(sid, smap[sid], sizes[sid], pos)))
layers.append(L_icon); layers += [L for _, L in sorted(objs, key=lambda x: x[0])]          # nearer (bigger Z) drawn later
def seg(f0, f1, a, b, e): return {"f0": f0, "f1": f1, "from": a, "to": b, "ease": e}
layers.append(dict(id="title_line1", texture="title_line1", anchor=[0.5, 0.5], frames=[dict(f=0, x=960, y=486, sx=1, sy=1, rot=0, opacity=0)],
  segments=dict(y=[seg(60, 72, 486, 471, {"bezier": [0.2, 0.7, 0.3, 1]}), seg(72, 92, 471, 471, "linear"), seg(92, 99, 471, 430, {"bezier": [0.6, 0, 0.9, 0.6]})],
                opacity=[seg(59, 60, 0, 0.25, "linear"), seg(60, 72, 0.25, 1, "linear"), seg(72, 99, 1, 1, "linear")])))
layers.append(dict(id="title_line2", texture="title_line2", anchor=[0.5, 0.5], frames=[dict(f=0, x=960, y=691, sx=1, sy=1, rot=0, opacity=0)],
  segments=dict(y=[seg(73, 83, 691, 634, {"bezier": [0.2, 0.8, 0.3, 1]}), seg(83, 92, 634, 634, "linear"), seg(92, 99, 634, 612, {"bezier": [0.6, 0, 0.9, 0.6]})],
                opacity=[seg(72, 73, 0, 0.15, "linear"), seg(73, 83, 0.15, 1, {"bezier": [0.3, 0.3, 0.6, 1]}), seg(83, 99, 1, 1, "linear")])))
sh = M["shutter"]
doc = dict(schema="xjp.motion-keys.v1", fps=24, size=[1920, 1080], interp="catmull",
  timeline=dict(shutter=[dict(f=0, value=0), dict(f=54, value=0)] + [dict(f=int(k), value=round(v, 3)) for k, v in sorted(sh.items())] + [dict(f=58, value=0)]), layers=layers)
json.dump(doc, open(f"{OUT}/keys.json", "w"), separators=(",", ":")); print(len(layers), "layers ->", OUT)
