// Records the Phase 2 demo video as Playwright screen captures and concatenates them with ffmpeg.
// Captions and title cards show exactly the narration lines in scripts/narration.json; each stays on screen
// for the duration of its synthesised clip (timing.json from scripts/synth.py), and every caption's start time
// is logged so scripts/assemble.py can lay the audio and the WebVTT on the same timeline.
//
// Usage: node scripts/demo.mjs scripts/demo.config.json
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const LINES = JSON.parse(fs.readFileSync(path.resolve(path.dirname(process.argv[2]), "narration.json"), "utf8")).lines;
const TIMING = JSON.parse(fs.readFileSync(path.resolve(cfg.clips, "timing.json"), "utf8"));
const OUT = path.resolve(cfg.out);
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1600, height: 1000 };
const APP = "http://127.0.0.1:8000/";
const api = (p, body) => fetch(`${APP}api${p}`, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}).then((r) => r.json());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await chromium.launch();
const files = [];
const cues = []; // { id, segment, t } with t = seconds since the segment's recording started
let segName = "", segStart = 0;

async function segment(name, fn) {
  const ctx = await browser.newContext({ viewport: SIZE, recordVideo: { dir: OUT, size: SIZE } });
  const page = await ctx.newPage();
  segName = name; segStart = Date.now();
  await fn(page);
  const video = page.video();
  await ctx.close();
  const dst = path.join(OUT, `${String(files.length).padStart(2, "0")}-${name}.webm`);
  fs.renameSync(await video.path(), dst);
  files.push(dst);
  console.log("segment", dst);
}
const mark = (id) => cues.push({ id, segment: segName, t: (Date.now() - segStart) / 1000 });
const hold = (id, extra = 600) => sleep(TIMING[id] * 1000 + extra);

const CARD_CSS = `body{margin:0;font-family:-apple-system,Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;display:flex;align-items:center;justify-content:center;height:100vh}
.card{max-width:1180px;padding:48px}.card h1{font-size:40px;margin:0 0 22px;line-height:1.2;color:#fff}.card p{font-size:27px;line-height:1.5;color:#e2e8f0;margin:0}.tag{display:inline-block;background:#4338ca;border-radius:8px;padding:4px 12px;font-size:19px;margin-bottom:16px}`;
async function card(page, id, heading) {
  await page.setContent(`<style>${CARD_CSS}</style><div class="card"><span class="tag">${cfg.tag}</span><h1>${heading}</h1><p>${LINES[id]}</p></div>`);
  mark(id);
  await hold(id, 900);
}
async function cap(page, id, extra = 600) {
  await page.evaluate((t) => {
    let el = document.getElementById("demo-cap");
    if (!el) {
      el = document.createElement("div"); el.id = "demo-cap";
      el.style.cssText = "position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1240px;background:rgba(15,23,42,.93);color:#fff;font:600 22px/1.35 -apple-system,Helvetica,sans-serif;padding:12px 22px;border-radius:12px;z-index:99999;box-shadow:0 8px 30px rgba(0,0,0,.35);text-align:center";
      document.body.appendChild(el);
    }
    el.textContent = t;
  }, LINES[id]);
  mark(id);
  await hold(id, extra);
}
const openApp = async (page) => { await page.goto(APP); await page.waitForSelector("#history-scroll"); await sleep(600); };
const scrollHistory = async (page, by, steps = 6, pause = 350) => { for (let i = 0; i < steps; i++) { await page.evaluate((d) => document.getElementById("history-scroll").scrollBy({ top: d, behavior: "smooth" }), by); await sleep(pause); } };
const waitIdle = async (maxMs = 120000) => { const t0 = Date.now(); while (Date.now() - t0 < maxMs) { const s = await api("/state"); if (!s.running && !s.busy) return s; await sleep(1000); } return api("/state"); };

// ---------- 1. intro cards ----------
await segment("intro", async (page) => {
  await card(page, "title", "Interactive Debugging and Steering of Multi-Agent AI Systems");
  await card(page, "problem", "The problem");
  await card(page, "users", "Target users, goal and tasks");
  await card(page, "components", "Prototype: three components from the paper");
});

// ---------- 2. C1 history, compose, queue ----------
await api("/recordings/load", { name: cfg.recording });
await segment("c1-history", async (page) => {
  await openApp(page);
  await cap(page, "loaded");
  const p = cap(page, "cards", 200);
  await sleep(2500); await scrollHistory(page, 600, 6, 650); await p;
  await page.locator("text=show more").first().click().catch(() => {});
  await cap(page, "expand");
  const q = cap(page, "fail", 400);
  await scrollHistory(page, 2500, 8, 350); await q;
});

await segment("c1-compose", async (page) => {
  await openApp(page);
  const p = cap(page, "send", 300);
  await sleep(1200);
  await page.selectOption("select >> nth=2", "GroupChatMessage");
  await page.fill("textarea", cfg.composeText);
  await sleep(1500);
  await page.click("text=Send to queue");
  await p;
  await cap(page, "controls");
  await page.click("button:has-text('Drop')");
  await cap(page, "dropped");
});

// ---------- 3. C3 overview ----------
await segment("c3-overview", async (page) => {
  await openApp(page);
  await cap(page, "overview");
  for (const [v, id] of [["sender", "sender"], ["recipient", "recipient"], ["type", "type"]]) {
    await page.selectOption("aside select", v);
    await cap(page, id);
  }
  const rects = page.locator("svg rect.cursor-pointer");
  const n = await rects.count();
  const p = cap(page, "hover", 300);
  for (const i of [3, Math.floor(n / 2), n - 3]) { await rects.nth(i).hover(); await sleep(1000); }
  await rects.nth(cfg.overviewClickIndex ?? Math.floor(n / 2)).click();
  await p;
  await page.locator("aside ul button").first().click();
  await cap(page, "legend");
  await page.locator("aside ul button").first().click();
});

// ---------- 4. C2 reset and edit ----------
await segment("c2-edit", async (page) => {
  await openApp(page);
  await page.evaluate((ts) => { const box = document.getElementById("history-scroll"), el = document.getElementById(`msg-${ts}`); box.scrollTop = el.offsetTop - box.offsetTop - 120; }, cfg.edit.timestamp);
  await cap(page, "mistake");
  const art = page.locator(`#msg-${cfg.edit.timestamp}`);
  await art.locator("button:has-text('Edit & revert')").click();
  await sleep(800);
  const original = await art.locator("textarea").inputValue();
  const keepUpTo = cfg.edit.keepUpTo ? original.indexOf(cfg.edit.keepUpTo) : -1;
  await art.locator("textarea").fill(keepUpTo >= 0 ? original.slice(0, keepUpTo) + cfg.edit.text : cfg.edit.text);
  await art.locator("textarea").evaluate((el) => { el.scrollTop = el.scrollHeight; });
  await cap(page, "editing");
  await art.locator("button:has-text('Save edit & revert')").click();
  await sleep(1500);
  await cap(page, "reset");
  await page.click("button:has-text('Step')");
  await cap(page, "step");
});
await waitIdle();
await segment("c2-step-result", async (page) => {
  await openApp(page);
  await scrollHistory(page, 2000, 3, 300);
  await cap(page, "stepped");
});
// The finished steered branch is shown from its own recording (saved from a live run) so the video does not
// depend on a fresh multi-minute model run.
await api("/recordings/load", { name: cfg.steeredRecording });
await segment("c2-result", async (page) => {
  await openApp(page);
  await scrollHistory(page, 3000, 4, 300);
  await cap(page, "result");
  await page.selectOption("aside select", "sender");
  await cap(page, "both");
  await page.click("button:has-text('session 0')");
  await cap(page, "original");
});

// ---------- 5. outro ----------
await segment("outro", async (page) => { await card(page, "status", "Status"); });
await browser.close();
fs.writeFileSync(path.join(OUT, "cues.json"), JSON.stringify({ files: files.map((f) => path.basename(f)), cues }, null, 2));

// ---------- concat ----------
const list = path.join(OUT, "list.txt");
fs.writeFileSync(list, files.map((f) => `file '${f}'`).join("\n"));
const mp4 = path.resolve(cfg.mp4);
execFileSync("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", list, "-vf", "scale=1600:1000,fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-movflags", "+faststart", mp4], { stdio: "inherit" });
console.log("wrote", mp4);
