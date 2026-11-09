# Agent Team Debugger — CS702 term project

Re-implementation of the three AGDebugger features (Epperson et al., CHI 2025) on AutoGen 0.7.5, plus an extension:

- **C1** message history, sending, execution control (Run / Step / Drop) and queue editing;
- **C2** reset-and-edit with session forking on real per-message checkpoints;
- **C3** overview visualisation (one column per session, one rectangle per message, three colour encodings, fork and
  suspect markers, hover, click, legend filter);
- **E1** error-anchored context assembly: one judge pass ranks up to five suspect messages; the context panel shows
  the flagged message, who said what to that agent, the preceding tool calls, warnings and the judge's evidence, and
  opens the editor on that message pre-filled with a suggested edit.

The team under debug is a Magentic-One orchestrator with a Coder, a local code Executor and a WebSearcher. The
searcher has two web modes, chosen per task: a cached 30-page corpus (`backend/agdbg/corpus.json`, reproducible) and
live English Wikipedia (MediaWiki search + plain-text extracts read in 3000-character chunks, GAIA-style questions).

## Requirements

- macOS or Linux; Python 3.12 and [`uv`](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`);
  Node 22 or newer (Vite 8 requires it); ffmpeg (videos only); graphviz `dot` (figures only).
- `ANTHROPIC_API_KEY` in `prototype/.env` or the repository-root `.env`, with credits on the account. Needed for live
  runs, the live Step after an edit, and the judge. Browsing a recording, and the E1 panel on the study recordings
  (suspects are stored in them), need no key.
- The agents' Executor runs model-written code as a local subprocess in `AGDBG_WORKDIR` (default `prototype/workdir`),
  which is deleted and recreated whenever a task or recording is loaded: point it only at disposable storage.
- Tested with the versions in `backend/requirements.txt` and `frontend/package-lock.json` (`uv pip install` resolves
  `requirements.txt`; `npm ci` installs the locked front-end set).

## Run

```bash
cd term_project/prototype
./run.sh          # first run: creates .venv, installs, builds the UI; then serves everything at http://127.0.0.1:8000
./run.sh --dev    # same, plus the Vite dev server with hot reload at http://127.0.0.1:5173
./run.sh --build  # force a UI rebuild
```

Offline smoke check (no key needed): open http://127.0.0.1:8000/?cond=full, **Load recording… →
t13_fy_ratio_STEERED_E1**; you should see two session tabs, a fork marker at t=25 in the overview, and 6651.7 at the
end of session 1. Open `?cond=reduced` in a second tab: no overview, no edit buttons. Open `?cond=e1`: five numbered
suspects. Press **Edit & revert** on any text card, then **Cancel**: nothing changes; **Reset here** forks session 2
with the same prefix (no model call until you press Step or Run).

In the UI: **Load recording…** opens a saved run (replay, no model calls); **Start new live task…** runs one of the
29 benchmark tasks live. `Run` / `Stop` / `Step` / `Drop` control the runtime queue (`Stop` keeps the queued
messages, so `Step` or `Run` resumes the branch); queued text messages can be edited (✎) or removed (✕) before they
are processed. Every message card has **⚑ flag** (study log), **Edit & revert**
and **Reset here**. The overview on the right is clickable. **Find suspects** in the error-context panel runs the
judge on the viewed session (about 30 s with Claude Opus); suspects then appear in the panel, the overview and on the
cards, and **Edit this message & revert** jumps into the editor.

Study mode is selected from the URL: `?p=<participant>&cond=reduced|full|e1&trial=<letter>`. `reduced` hides
reset/edit and the overview (the paper's baseline), `full` is the paper's feature set, `e1` adds the context panel
and the suspect cues (they appear in no other condition). The condition is read from each tab's URL. Every API action
(with the full text of edits and sent messages) and UI event is appended to `logs/<participant>.jsonl`. The study
materials are in [`study/`](study/README.md).

## Command-line tools (`cd backend`, use `../.venv/bin/python`)

```bash
python -m agdbg.record t2_revenue                 # one live run -> recordings/t2_revenue.pkl, prints PASS/FAIL
python -m agdbg.harvest --seeds 2 --jobs 4        # every task twice, 4 in parallel; logs in recordings/harvest_logs/
python -m agdbg.judge t13_fy_ratio_FAIL --save    # run the E1 judge on session 0 of a recording and store the result in it
# The stored suspects in the study recordings were produced with the current prompt (18 Oct 2026), which forbids
# stating or deriving the answer in reasons and suggestions.
python -m agdbg.steer t13_fy_ratio_FAIL 25 edit.txt NAME [--repeat 3]   # headless reset-and-edit at t=25, continue live, save
python -m agdbg.dump t13_fy_ratio_FAIL            # print a recording as text (used to code ground-truth error lists)
```

Tasks and expected answers live in `backend/agdbg/tasks.py`: 13 corpus tasks (`t*`) and 16 live-Wikipedia tasks
(`w*`, `wt*`). Environment knobs: `AGDBG_MODEL` (team model, default `claude-haiku-5-5`), `AGDBG_EFFORT` (default
`low`), `AGDBG_SEARCH_ITERS` (WebSearcher tool calls per turn, default 4), `AGDBG_JUDGE_MODEL` (default
`claude-opus-5-5`), `AGDBG_WORKDIR` (executor working directory). Recordings used in the study:
`t13_fy_ratio_FAIL`, `t13_fy_ratio_FAIL_2`, `wt2_mongolia_rank_FAIL` (natural failures of the Haiku team, with stored
judge results) and the steered branches `t13_fy_ratio_STEERED` (plan edit at t=9) and `t13_fy_ratio_STEERED_E1`
(instruction edit at t=25). `recordings/harvest/` and `recordings/archive/` hold bulk runs and are not tracked.

## Layout

```
backend/agdbg/
  llm.py        AutoGen ChatCompletionClient on the Anthropic SDK (reasoning replay, retries, error capture)
  team.py       the agent team + corpus / Wikipedia tools
  recorder.py   intervention handler: timestamps + checkpoint before every message
  manager.py    sessions, run/step/drop, queue editing, reset-and-edit, judge, recordings
  judge.py      E1 judge pass (ranked suspects with reasons and suggested edits)
  study.py      per-participant JSON-lines log
  serialize.py  JSON views and text-level message editing
  app.py        FastAPI routes (/api/*), serves frontend/dist
  tasks.py, corpus.json, record.py, harvest.py, steer.py, dump.py
frontend/src/   React + Tailwind UI: components/{Compose,Queue,History,Overview,ContextPanel,Toast}.tsx, context.ts (E1 assembly)
study/          consent form, facilitator script, task sheets, questionnaires, ground-truth error lists, data templates, analyze.py
recordings/     saved runs (*.pkl: history + per-message checkpoints + sessions + suspects)
logs/           study logs (not tracked)
```

## Demo videos (`frontend/scripts/`)

One narration file per video holds the text used for on-screen captions, spoken narration and the transcript.
`synth.py` synthesises each line (macOS `say` or an edge-tts neural voice) and records its duration; `demo_e1.mjs`
records the UI with Playwright, holding each caption for its clip's duration; `assemble.py` lays the clips and a
WebVTT on that timeline and muxes the narrated mp4. `./run.sh` must be serving on :8000 (the Step scene makes one
model call).

```bash
cd frontend
python3 scripts/synth.py scripts/narration_phase3.json ../../phase3/narration_clips
node scripts/demo_e1.mjs scripts/phase3.config.json
python3 scripts/assemble.py scripts/phase3.config.json           # -> ../../phase3/phase3_demo_backup{_narrated.mp4,.vtt,_transcript.md}
python3 scripts/synth.py scripts/narration_final.json ../../phase4/narration_clips
node scripts/demo_e1.mjs scripts/final.config.json
python3 scripts/assemble.py scripts/final.config.json            # -> ../../phase4/final_demo{_narrated.mp4,.vtt,_transcript.md}
```

`demo.mjs` / `demo.config.json` / `narration.json` are the Phase 2 video (kept for reference).
