// Records the Phase 2 demo video as a series of Playwright screen captures (no audio), then concatenates them.
// Usage: node scripts/demo.mjs scripts/demo.config.json
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = path.resolve(cfg.out);
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1600, height: 1000 };
const APP = "http://127.0.0.1:8000/";
const api = (p, body) => fetch(`${APP}api${p}`, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}).then((r) => r.json());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await chromium.launch();
const files = [];

async function segment(name, fn) {
  const ctx = await browser.newContext({ viewport: SIZE, recordVideo: { dir: OUT, size: SIZE } });
  const page = await ctx.newPage();
  await fn(page);
  const video = page.video();
  await ctx.close();
  const dst = path.join(OUT, `${String(files.length).padStart(2, "0")}-${name}.webm`);
  fs.renameSync(await video.path(), dst);
  files.push(dst);
  console.log("segment", dst);
}

const CARD_CSS = `body{margin:0;font-family:-apple-system,Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;display:flex;align-items:center;justify-content:center;height:100vh}
.card{max-width:1180px;padding:48px}.card h1{font-size:44px;margin:0 0 18px;line-height:1.15}.card h2{font-size:30px;color:#a5b4fc;margin:0 0 22px;font-weight:600}
.card p,.card li{font-size:25px;line-height:1.45;color:#e2e8f0}.card li{margin:8px 0}.small{font-size:19px;color:#94a3b8}.tag{display:inline-block;background:#4338ca;border-radius:8px;padding:4px 12px;font-size:19px;margin-bottom:14px}`;
const card = async (page, html, ms) => { await page.setContent(`<style>${CARD_CSS}</style><div class="card">${html}</div>`); await sleep(ms); };

async function cap(page, text, ms = 4000) {
  await page.evaluate((t) => {
    let el = document.getElementById("demo-cap");
    if (!el) {
      el = document.createElement("div"); el.id = "demo-cap";
      el.style.cssText = "position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1200px;background:rgba(15,23,42,.92);color:#fff;font:600 22px/1.35 -apple-system,Helvetica,sans-serif;padding:12px 22px;border-radius:12px;z-index:99999;box-shadow:0 8px 30px rgba(0,0,0,.35);text-align:center";
      document.body.appendChild(el);
    }
    el.textContent = t;
  }, text);
  await sleep(ms);
}
const openApp = async (page) => { await page.goto(APP); await page.waitForSelector("#history-scroll"); await sleep(600); };
const scrollHistory = async (page, by, steps = 6, pause = 350) => { for (let i = 0; i < steps; i++) { await page.evaluate((d) => document.getElementById("history-scroll").scrollBy({ top: d, behavior: "smooth" }), by); await sleep(pause); } };
const waitIdle = async (maxMs = 240000) => { const t0 = Date.now(); while (Date.now() - t0 < maxMs) { const s = await api("/state"); if (!s.running && !s.busy && s.queue.length === 0) return s; await sleep(1500); } return api("/state"); };

// ---------- 1. intro + problem cards ----------
await segment("intro", async (page) => {
  await card(page, cfg.cards.title, 9000);
  for (const c of cfg.cards.problem) await card(page, c, 11000);
});

// ---------- 2. C1 history, compose, queue ----------
await api("/recordings/load", { name: cfg.recording });
await segment("c1-history", async (page) => {
  await openApp(page);
  await cap(page, `Recorded failing run loaded (${cfg.recording}) — replayed from the saved history and checkpoints, no model calls.`, 5000);
  await cap(page, "C1 · Message history: every runtime message as a card — sender → recipient/topic, message type, payload. Tool calls and results included.", 2500);
  await scrollHistory(page, 600, 8, 650);
  await page.locator("text=show more").first().click().catch(() => {});
  await cap(page, "Long payloads expand in place. Colour of the left bar = sending agent.", 3500);
  await scrollHistory(page, 2500, 8, 350);
  await cap(page, `After ${cfg.messages} messages the run ends without the answer. Expected: ${cfg.expected}.`, 5000);
});

await segment("c1-compose", async (page) => {
  await openApp(page);
  await cap(page, "C1 · Sending: compose a broadcast (group topic) or a direct message to one agent; it lands in the runtime queue.", 1500);
  await page.selectOption("select >> nth=2", "GroupChatMessage");
  await page.fill("textarea", cfg.composeText);
  await sleep(1200);
  await page.click("text=Send to queue");
  await sleep(1500);
  await cap(page, "C1 · Execution control: Run processes the queue continuously, Step processes exactly one message, Drop discards the next one.", 4500);
  await page.click("button:has-text('Drop')");
  await cap(page, "Dropped — the queue is empty again and the agents never saw the message.", 3500);
});

// ---------- 3. C3 overview ----------
await segment("c3-overview", async (page) => {
  await openApp(page);
  await cap(page, "C3 · Overview: one column per session, one rectangle per message in order. Legend buttons filter.", 3500);
  for (const [v, t] of [["sender", "Colour by sender: orchestrator / Coder / Executor / WebSearcher / user."], ["recipient", "Colour by recipient topic or agent."], ["type", "Colour by message type — tool calls stand out from text."]]) {
    await page.selectOption("aside select", v);
    await cap(page, t, 3000);
  }
  const rects = page.locator("svg rect.cursor-pointer");
  const n = await rects.count();
  for (const i of [3, Math.floor(n / 2), n - 3]) { await rects.nth(i).hover(); await sleep(1100); }
  await cap(page, "Hover shows the message; click scrolls the history to it.", 1000);
  await rects.nth(cfg.overviewClickIndex ?? Math.floor(n / 2)).click();
  await sleep(2500);
  await page.locator("aside ul button").first().click();
  await cap(page, "Legend filter dims every other message type.", 2500);
  await page.locator("aside ul button").first().click();
});

// ---------- 4. C2 reset and edit ----------
await segment("c2-edit", async (page) => {
  await openApp(page);
  await page.evaluate((ts) => { const box = document.getElementById("history-scroll"), el = document.getElementById(`msg-${ts}`); box.scrollTop = el.offsetTop - box.offsetTop - 120; }, cfg.edit.timestamp);
  await cap(page, `C2 · The mistake starts at t=${cfg.edit.timestamp}: ${cfg.edit.why}`, 6000);
  const art = page.locator(`#msg-${cfg.edit.timestamp}`);
  await art.locator("button:has-text('Edit & revert')").click();
  await sleep(800);
  const original = await art.locator("textarea").inputValue();
  const keepUpTo = cfg.edit.keepUpTo ? original.indexOf(cfg.edit.keepUpTo) : -1;
  await art.locator("textarea").fill(keepUpTo >= 0 ? original.slice(0, keepUpTo) + cfg.edit.text : cfg.edit.text);
  await art.locator("textarea").evaluate((el) => { el.scrollTop = el.scrollHeight; });
  await cap(page, "Edit the message in place …", 3500);
  await art.locator("button:has-text('Save edit & revert')").click();
  await sleep(1800);
  await cap(page, `Reset-and-edit: every agent's state is restored from the checkpoint taken before t=${cfg.edit.timestamp}, the edited message is re-published, and a new session (S1) forks off — the old branch stays viewable.`, 7000);
  await page.click("button:has-text('Step')");
  await cap(page, "Step: the runtime processes just this one message (live model call) …", 2000);
});
await waitIdle(180000);
await segment("c2-step-result", async (page) => {
  await openApp(page);
  await scrollHistory(page, 2000, 3, 300);
  await cap(page, "Step processed the edited broadcast; the orchestrator's request-to-speak now waits in the queue. Run continues the branch to completion.", 4000);
  await page.click("button:has-text('Run')");
  await sleep(2500);
});
const finalState = await waitIdle(900000);
const finalText = (finalState.sessions.at(-1).messages.filter((m) => m.sender === 'MagenticOneOrchestrator' && m.recipient === 'group' && m.type === 'TextMessage').at(-1) || {}).content || '';
const steered = cfg.expectedNumber.split('|').every((p) => finalText.replace(/,/g, '').includes(p));
console.log('steered ok:', steered, finalText.slice(0, 200));
await segment("c2-result", async (page) => {
  await openApp(page);
  await scrollHistory(page, 3000, 4, 300);
  await cap(page, steered ? "Steered branch finished. " + cfg.resultCaption : cfg.resultCaptionFail, 6000);
  await page.selectOption("aside select", "sender");
  await cap(page, "Overview now shows both sessions; the amber marker is the fork point. Session tabs switch between branches.", 4500);
  await page.click("button:has-text('session 0')");
  await cap(page, "The original failing branch is still browsable for comparison.", 4000);
});
fs.writeFileSync(path.join(OUT, "final-state.json"), JSON.stringify(finalState, null, 2));

// ---------- 5. outro ----------
await segment("outro", async (page) => { for (const c of cfg.cards.outro) await card(page, c, 10000); });
await browser.close();

// ---------- concat ----------
const list = path.join(OUT, "list.txt");
fs.writeFileSync(list, files.map((f) => `file '${f}'`).join("\n"));
const mp4 = path.resolve(cfg.mp4);
execFileSync("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", list, "-vf", "scale=1600:1000,fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-movflags", "+faststart", mp4], { stdio: "inherit" });
console.log("wrote", mp4);
