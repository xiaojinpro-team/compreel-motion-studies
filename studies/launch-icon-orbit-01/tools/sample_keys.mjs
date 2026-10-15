// Sample canvas2d/keys.json frame by frame (quarter frames around the rush) → samples.json, used by the AE and Blender builders.
// node tools/sample_keys.mjs canvas2d/keys.json samples.json
import { sampleLayer } from "../canvas2d/player.js";
import fs from "node:fs";
const [keysP, outP] = process.argv.slice(2); const K = JSON.parse(fs.readFileSync(keysP, "utf8"));
const times = []; for (let f = 0; f <= 99; f++) { times.push(f); if (f >= 53 && f < 58) for (const q of [0.25, 0.5, 0.75]) times.push(f + q); }
times.sort((a, b) => a - b);
const out = { fps: K.fps, size: K.size, times, shutter: K.timeline?.shutter, layers: K.layers.map((L) => ({ id: L.id, texture: L.texture, anchor: L.anchor, samples: times.map((f) => { const s = sampleLayer(L, f, K.interp); return [s.x, s.y, s.sx, s.sy, s.rot, s.opacity]; }) })) };
fs.writeFileSync(outP, JSON.stringify(out)); console.log(out.layers.length, "layers,", times.length, "samples each");
