// Minimal keyframe player for this motion study (MIT). Reads keys.json and draws one frame onto a 2D canvas.
// Same rules as the renderer it was built with: uniform Catmull-Rom between keyed frames, eased segments,
// per-frame shutter with sub-frame accumulation for motion blur.
const clamp01 = (u) => Math.min(1, Math.max(0, u));
function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const X = (t) => ((ax * t + bx) * t + cx) * t, Y = (t) => ((ay * t + by) * t + cy) * t, dX = (t) => (3 * ax * t + 2 * bx) * t + cx;
  return (u) => {
    if (u <= 0) return 0; if (u >= 1) return 1;
    let t = u;
    for (let i = 0; i < 8; i++) { const e = X(t) - u; if (Math.abs(e) < 1e-9) return Y(t); const d = dX(t); if (Math.abs(d) < 1e-7) break; t -= e / d; }
    let lo = 0, hi = 1; t = u;
    for (let i = 0; i < 60; i++) { const x = X(t); if (Math.abs(x - u) < 1e-9) break; if (x < u) lo = t; else hi = t; t = (lo + hi) / 2; }
    return Y(t);
  };
}
const ease = (spec) => (spec === "linear" || !spec ? (u) => u : bezier(...spec.bezier));
const catmull = (p0, p1, p2, p3, u) => 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u);
const FIELDS = ["x", "y", "sx", "sy", "rot", "opacity"];
const DEFAULTS = { x: 0, y: 0, sx: 1, sy: 1, rot: 0, opacity: 1 };
function sampleFrames(fr, f, spline) {
  if (f <= fr[0].f) return { ...fr[0] };
  if (f >= fr[fr.length - 1].f) return { ...fr[fr.length - 1] };
  let lo = 0, hi = fr.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (fr[m].f <= f) lo = m; else hi = m; }
  const a = fr[lo], b = fr[hi], u = (f - a.f) / (b.f - a.f), out = {};
  for (const k of FIELDS) {
    const x = a[k] ?? b[k], y = b[k] ?? a[k];
    if (x === undefined) continue;
    out[k] = spline ? catmull(fr[Math.max(lo - 1, 0)][k], x, y, fr[Math.min(hi + 1, fr.length - 1)][k], u) : x + (y - x) * u;
  }
  return out;
}
function sampleSegments(list, f) {
  const segs = [...list].sort((p, q) => p.f0 - q.f0);
  const cover = segs.find((s, i) => f >= s.f0 && (f < s.f1 || (i === segs.length - 1 && f <= s.f1)));
  if (cover) { const p = ease(cover.ease)(clamp01((f - cover.f0) / (cover.f1 - cover.f0))); return cover.from + (cover.to - cover.from) * p; }
  if (f < segs[0].f0) return segs[0].from;
  let held = segs[0].to; for (const s of segs) if (s.f1 <= f) held = s.to; return held;
}
export function sampleLayer(layer, f, docInterp) {
  const spline = (layer.interp ?? docInterp ?? "linear") === "catmull";
  const out = layer.frames?.length ? sampleFrames(layer.frames, f, spline) : { ...DEFAULTS };
  for (const [ch, list] of Object.entries(layer.segments ?? {})) if (list?.length) out[ch] = sampleSegments(list, f);
  return out;
}
export function shutterAt(keys, f) {
  const pts = keys.timeline?.shutter; if (!pts?.length) return 0;
  if (f <= pts[0].f) return pts[0].value; if (f >= pts[pts.length - 1].f) return pts[pts.length - 1].value;
  for (let i = 0; i < pts.length - 1; i++) if (f >= pts[i].f && f <= pts[i + 1].f) return pts[i].value + (pts[i + 1].value - pts[i].value) * (f - pts[i].f) / (pts[i + 1].f - pts[i].f);
  return 0;
}
export function drawFrame(ctx, keys, tex, f) {
  const [W, H] = keys.size;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.clearRect(0, 0, W, H);
  ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
  for (const L of keys.layers) {
    const s = sampleLayer(L, f, keys.interp), img = tex[L.texture];
    if (!img || !(s.opacity > 0)) continue;
    const w = img.naturalWidth ?? img.width, h = img.naturalHeight ?? img.height;
    ctx.save(); ctx.globalAlpha = Math.min(1, s.opacity); ctx.translate(s.x, s.y); ctx.rotate((s.rot * Math.PI) / 180); ctx.scale(s.sx, s.sy);
    ctx.drawImage(img, -L.anchor[0] * w, -L.anchor[1] * h, w, h); ctx.restore();
  }
}
// Draw frame number `f` (integer) with motion blur: average `subframes` renders over the shutter window centred on f.
export function renderFrame(ctx, keys, tex, f, subframes = 24) {
  const sh = shutterAt(keys, f);
  if (!(sh > 0)) return drawFrame(ctx, keys, tex, f);
  const [W, H] = keys.size, acc = new Float32Array(W * H * 4);
  for (let i = 0; i < subframes; i++) {
    drawFrame(ctx, keys, tex, f + ((i + 0.5) / subframes - 0.5) * sh);
    const d = ctx.getImageData(0, 0, W, H).data; for (let j = 0; j < d.length; j++) acc[j] += d[j];
  }
  const out = ctx.createImageData(W, H); for (let j = 0; j < acc.length; j++) out.data[j] = Math.round(acc[j] / subframes); ctx.putImageData(out, 0, 0);
}
