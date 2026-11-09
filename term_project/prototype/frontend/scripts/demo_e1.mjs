// Records a narrated walkthrough (Phase 3 backup video / Phase 4 demo video) as Playwright screen captures.
// Same contract as demo.mjs: captions and title cards show exactly the lines in the narration file named by the
// config, each held for its synthesised clip's duration (timing.json from synth.py); cue times are logged for
// assemble.py. The config's "segments" list selects which scenes to record, so one script serves both videos.
//
// Usage: node scripts/demo_e1.mjs scripts/<config>.json      (needs ./run.sh on :8000; the Step scene makes one model call)
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const LINES = JSON.parse(fs.readFileSync(path.resolve(path.dirname(process.argv[2]), cfg.narration), "utf8")).lines;
const TIMING = JSON.parse(fs.readFileSync(path.resolve(cfg.clips, "timing.json"), "utf8"));
const OUT = path.resolve(cfg.out);
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1600, height: 1000 };
const APP = "http://127.0.0.1:8000/";
const api = (p, body) => fetch(`${APP}api${p}`, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}).then((r) => r.json());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await chromium.launch();
const files = [], cues = [];
let segName = "", segStart = 0;
const want = (name) => cfg.segments.includes(name);

async function segment(name, fn) {
  if (!want(name)) return;
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
const EXTRA = cfg.capExtra ?? 500;
const hold = (id, extra = EXTRA) => sleep(TIMING[id] * 1000 + extra);
const CARD_CSS = `body{margin:0;font-family:-apple-system,Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;display:flex;align-items:center;justify-content:center;height:100vh}
.card{max-width:1180px;padding:48px}.card h1{font-size:40px;margin:0 0 22px;line-height:1.2;color:#fff}.card p{font-size:27px;line-height:1.5;color:#e2e8f0;margin:0}.tag{display:inline-block;background:#4338ca;border-radius:8px;padding:4px 12px;font-size:19px;margin-bottom:16px}`;
async function card(page, id, heading) {
  await page.setContent(`<style>${CARD_CSS}</style><div class="card"><span class="tag">${cfg.tag}</span><h1>${heading}</h1><p>${LINES[id]}</p></div>`);
  mark(id); await hold(id, Math.max(EXTRA, 400));
}
async function cap(page, id, extra = EXTRA) {
  await page.evaluate((t) => {
    let el = document.getElementById("demo-cap");
    if (!el) {
      el = document.createElement("div"); el.id = "demo-cap";
      el.style.cssText = "position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1240px;background:rgba(15,23,42,.93);color:#fff;font:600 22px/1.35 -apple-system,Helvetica,sans-serif;padding:12px 22px;border-radius:12px;z-index:99999;box-shadow:0 8px 30px rgba(0,0,0,.35);text-align:center";
      document.body.appendChild(el);
    }
    el.textContent = t;
  }, LINES[id]);
  mark(id); await hold(id, extra);
}
const openApp = async (page, q = "") => { await page.goto(APP + q); await page.waitForSelector("#history-scroll"); await sleep(600); };
const scrollHistory = async (page, by, steps = 6, pause = 350) => { for (let i = 0; i < steps; i++) { await page.evaluate((d) => document.getElementById("history-scroll").scrollBy({ top: d, behavior: "smooth" }), by); await sleep(pause); } };
const scrollTo = async (page, ts) => page.evaluate((ts) => { const box = document.getElementById("history-scroll"), el = document.getElementById(`msg-${ts}`); if (el) box.scrollTop = el.offsetTop - box.offsetTop - 120; }, ts);
const waitIdle = async (maxMs = 180000) => { const t0 = Date.now(); while (Date.now() - t0 < maxMs) { const s = await api("/state"); if (!s.running && !s.busy) return s; await sleep(1000); } return api("/state"); };

// ---------- intro cards ----------
await segment("intro", async (page) => {
  await card(page, "title", cfg.title);
  if (LINES.problem) await card(page, "problem", "The problem");
  if (LINES.users) await card(page, "users", "Target users, goal and tasks");
  if (LINES.components) await card(page, "components", "What we built");
});

// ---------- C1: history + failing run ----------
await api("/recordings/load", { name: cfg.recording });
await segment("c1", async (page) => {
  await openApp(page, "?cond=full");
  await cap(page, "loaded");
  if (LINES.cards) { const p = cap(page, "cards", 200); await sleep(2000); await scrollHistory(page, 600, 5, 650); await p; }
  const q = cap(page, "fail", 300);
  await scrollHistory(page, 2500, cfg.failScrollSteps ?? 8, 300); await q;
});

// ---------- C1: compose + queue (+ queue editing) ----------
await segment("queue", async (page) => {
  await openApp(page, "?cond=full");
  const p = cap(page, "send", 300);
  await sleep(1000);
  await page.selectOption("select >> nth=2", "GroupChatMessage");
  await page.fill("textarea", cfg.composeText);
  await sleep(1200);
  await page.click("text=Send to queue");
  await p;
  await cap(page, "controls");
  if (LINES.queueedit) {
    const q = cap(page, "queueedit", 300);
    await page.click("button[title='Edit this queued message before it is processed']");
    await sleep(600);
    await page.fill("ul textarea", cfg.composeText + " Use the offset parameter to read every chunk.");
    await sleep(900);
    await page.click("ul button:has-text('Save')");
    await q;
  }
  await page.click("button:has-text('Drop')");
  await cap(page, "dropped");
});

// ---------- C3: overview ----------
await segment("overview", async (page) => {
  await openApp(page, "?cond=full");
  await cap(page, "overview");
  for (const [v, id] of [["sender", "sender"], ["type", "type"]]) if (LINES[id]) { await page.selectOption("aside select", v); await cap(page, id); }
  const rects = page.locator("svg rect.cursor-pointer");
  const n = await rects.count();
  if (LINES.hover) {
    const p = cap(page, "hover", 300);
    for (const i of [3, Math.floor(n / 2), n - 3]) { await rects.nth(i).hover(); await sleep(900); }
    await rects.nth(cfg.overviewClickIndex ?? Math.floor(n / 2)).click();
    await p;
  }
});

// ---------- E1: suspects + context + edit ----------
await segment("e1", async (page) => {
  await openApp(page, "?cond=e1");
  await cap(page, "e1intro");
  const p = cap(page, "suspects", 300);
  await sleep(800);
  await page.locator("aside ol li button").first().hover();
  await sleep(1200);
  await p;
  await page.locator("aside ol li button").nth(cfg.suspectIndex ?? 1).click();
  const q = cap(page, "context", 300);
  await sleep(1200);
  await page.evaluate(() => { const a = document.querySelectorAll("aside")[1]?.querySelector(".overflow-y-auto"); if (a) a.scrollBy({ top: 600, behavior: "smooth" }); });
  await sleep(1200);
  await page.evaluate(() => { const a = document.querySelectorAll("aside")[1]?.querySelector(".overflow-y-auto"); if (a) a.scrollBy({ top: 900, behavior: "smooth" }); });
  await q;
  await page.click("aside button:has-text('Edit this message')");
  await sleep(700);
  const art = page.locator(`#msg-${cfg.edit.timestamp}`);
  await cap(page, "prefill");
  await art.locator("textarea").fill(cfg.edit.text);
  await art.locator("textarea").evaluate((el) => { el.scrollTop = 0; });
  await cap(page, "editing");
  await art.locator("button:has-text('Save edit & revert')").click();
  await sleep(1500);
  await cap(page, "reset");
  if (LINES.step) {
    const p = cap(page, "step", 300);
    await page.click("button:has-text('Step')");  // 1: the edited broadcast (no model call)
    await sleep(2500);
    await page.click("button:has-text('Step')");  // 2: the orchestrator's request-to-speak -> WebSearcher model call
    await p;
  }
});
if (want("e1")) await waitIdle();
await segment("stepped", async (page) => {
  await openApp(page, "?cond=e1");
  await scrollHistory(page, 2000, 3, 300);
  await cap(page, "stepped");
});

// ---------- result from the saved steered branch ----------
await api("/recordings/load", { name: cfg.steeredRecording });
await segment("result", async (page) => {
  await openApp(page, "?cond=e1");
  await scrollHistory(page, 3000, 4, 300);
  await page.selectOption("aside select", "sender");
  await cap(page, "result");
  if (LINES.both) await cap(page, "both");
  if (LINES.original) { await page.click("button:has-text('session 0')"); await cap(page, "original"); }
});

// ---------- study mode / outro ----------
await segment("study", async (page) => {
  await openApp(page, "?p=P0&cond=reduced");
  await cap(page, "study");
});
await segment("outro", async (page) => { await card(page, "status", cfg.outroHeading ?? "Status"); await sleep(1500); });
await browser.close();
fs.writeFileSync(path.join(OUT, "cues.json"), JSON.stringify({ files: files.map((f) => path.basename(f)), cues }, null, 2));

const list = path.join(OUT, "list.txt");
fs.writeFileSync(list, files.map((f) => `file '${f}'`).join("\n"));
const mp4 = path.resolve(cfg.mp4);
execFileSync("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", list, "-vf", "scale=1600:1000,fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-movflags", "+faststart", mp4], { stdio: "inherit" });
console.log("wrote", mp4);
