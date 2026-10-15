// Screenshot of the current UI state for the report figure.
import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1.5 });
await p.goto("http://127.0.0.1:8000/");
await p.waitForSelector("#history-scroll");
await p.waitForTimeout(1500);
await p.evaluate(() => document.getElementById("history-scroll").scrollTo({ top: 1e9 }));
await p.selectOption("aside select", "sender");
await p.waitForTimeout(800);
await p.screenshot({ path: process.argv[2] });
await b.close();
