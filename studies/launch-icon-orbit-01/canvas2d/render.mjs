// Render all 100 frames to PNG with headless Chrome:  npm install && node render.mjs [outDir] [query]
// e.g. node render.mjs frames "line2=MyApp"   then: ffmpeg -framerate 24 -i frames/%06d.png -pix_fmt yuv420p intro.mp4
import { chromium } from "playwright-core";
import http from "node:http"; import fs from "node:fs"; import path from "node:path"; import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url)); const out = path.resolve(process.argv[2] || "frames"); const query = process.argv[3] || "";
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".png": "image/png", ".ttf": "font/ttf" };
const srv = http.createServer((q, r) => { const p = path.join(here, decodeURIComponent(new URL(q.url, "http://x").pathname)); if (!p.startsWith(here) || !fs.existsSync(p)) { r.writeHead(404); return r.end(); } r.writeHead(200, { "Content-Type": types[path.extname(p)] || "application/octet-stream" }); fs.createReadStream(p).pipe(r); }).listen(0, "127.0.0.1");
await new Promise((r) => srv.on("listening", r));
const chrome = process.env.CHROME_PATH || (process.platform === "darwin" ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : undefined);
const b = await chromium.launch(chrome ? { executablePath: chrome } : {});
const page = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(`http://127.0.0.1:${srv.address().port}/index.html?${query}`); await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
fs.mkdirSync(out, { recursive: true });
for (let f = 0; f < 100; f++) { await page.evaluate((f) => window.renderAt(f), f); await page.locator("#stage").screenshot({ path: path.join(out, String(f).padStart(6, "0") + ".png") }); }
await b.close(); srv.close(); console.log("wrote 100 frames to", out);
