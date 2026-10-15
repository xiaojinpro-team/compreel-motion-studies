"""samples.json (screen space) → ae/ae_data.json (3D camera + 3D layers).
Camera at (960,540,-D) looking at (960,540,0), zoom = focal of a 40° vertical field of view; a card's depth z = d - D where d = F / (its scale ÷ its settled scale).
python3 tools/make_ae_data.py samples.json ae/ae_data.json canvas2d/textures"""
import json, sys, math
from PIL import Image
sp, outp, texdir = sys.argv[1:4]
S = json.load(open(sp)); W, H = S["size"]; F = (H / 2) / math.tan(math.radians(20)); times = S["times"]
idx = {L["id"]: L for L in S["layers"]}; t46 = times.index(46); s_icon46 = idx["icon"]["samples"][t46][2]
D = lambda i, t: F if t >= 58 else F * s_icon46 / max(idx["icon"]["samples"][i][2], 1e-6)
cl = lambda v: max(0.0, min(100.0, v))
out = dict(fps=S["fps"], size=S["size"], zoom=F, times=times, camera=[round(-D(i, t), 3) for i, t in enumerate(times)], layers=[])
for L in S["layers"]:
    lid = L["id"]
    if lid == "bg": continue
    if lid.startswith("title_"): out["layers"].append(dict(id=lid, kind="text", samples=[[round(s[0], 2), round(s[1], 2), round(cl(s[5] * 100), 2)] for s in L["samples"]])); continue
    tw, th = Image.open(f"{texdir}/{L['texture']}.png").size
    if lid == "bg_gradient": out["layers"].append(dict(id=lid, kind="plate", texture=L["texture"] + ".png", size=[tw, th], samples=[[round(cl(s[5] * 100), 2)] for s in L["samples"]])); continue
    sx46 = L["samples"][t46][2]; ax, ay = L["anchor"]; rows = []
    for i, t in enumerate(times):
        x, y, sx, sy, rot, op = L["samples"][i]; k = max(sx / sx46, 1e-4); d = F / k; z = d - D(i, t)
        rows.append([round(W / 2 + (x - W / 2) * d / F, 3), round(H / 2 + (y - H / 2) * d / F, 3), round(z, 3), round(rot, 3), round(cl(op * 100), 2)])
    out["layers"].append(dict(id=lid, kind="card", texture=L["texture"] + ".png", size=[tw, th], anchor=[ax * tw, ay * th], scale=round(sx46 * 100, 5), samples=rows))
json.dump(out, open(outp, "w")); print("ae_data:", len(out["layers"]), "layers")
