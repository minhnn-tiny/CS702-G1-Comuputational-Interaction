# Agent Team Debugger — CS702 term project prototype (Phase 2)

Re-implementation of the three AGDebugger features (Epperson et al., CHI 2025) on AutoGen 0.7.5:
message history / sending / stepping, reset-and-edit with session forking, and the overview visualisation.
The team under debug is a Magentic-One orchestrator with a Coder, a local code Executor and a WebSearcher.
The searcher has two web modes, chosen per task: a cached 30-page corpus (`backend/agdbg/corpus.json`, fully
reproducible) and live English Wikipedia (MediaWiki search + plain-text extracts read in 3000-character chunks,
for GAIA-style questions).

## Requirements

- Python 3.12 (`uv` is used to create `.venv`), Node 20+
- `ANTHROPIC_API_KEY` in `prototype/.env` or the repository-root `.env` (only needed for live runs; browsing a
  recording needs no key)

## Run

```bash
./run.sh          # builds the UI once, then serves everything at http://127.0.0.1:8000
./run.sh --dev    # same, plus the Vite dev server with hot reload at http://127.0.0.1:5173
```

In the UI: **Load recording…** to open a saved failing run (replay, no model calls), or **Start new live task…**
to run one of the benchmark tasks live. `Run` / `Stop` / `Step` / `Drop` control the runtime queue; every
message card has **Edit & revert** and **Reset here**; the right-hand overview is clickable.

## Record runs from the command line

```bash
cd backend
../.venv/bin/python -m agdbg.record t2_revenue              # one run -> recordings/t2_revenue.pkl, prints PASS/FAIL
../.venv/bin/python -m agdbg.harvest --seeds 2 --jobs 4     # every task twice, 4 in parallel; logs in recordings/harvest_logs/
../.venv/bin/python -m agdbg.harvest --seeds 3 t7_fy_visitors t8_pre_anniversary
```

Tasks and expected answers live in `backend/agdbg/tasks.py`: 13 corpus tasks (`t*`: stale, conflicting or
near-duplicate-entity sources, financial-year and anniversary arithmetic, two coding tasks over files placed in the
executor's working directory) and 11 live-Wikipedia tasks (`w*`: GAIA-style multi-hop questions). Environment knobs:
`AGDBG_MODEL` (default `claude-haiku-5-5`, the team under debug; `claude-opus-5-5` was used for the harvest
comparison), `AGDBG_EFFORT` (reasoning effort, default `low`), `AGDBG_SEARCH_ITERS` (WebSearcher tool calls per turn, default 4). `recordings/archive/` holds earlier runs
made with a weakened (one-tool-call) searcher; `recordings/harvest_logs/` has one log per harvested run.

## Layout

```
backend/agdbg/
  llm.py        AutoGen ChatCompletionClient on the Anthropic SDK
  team.py       the agent team + cached web tools
  recorder.py   intervention handler: timestamps + checkpoint before every message
  manager.py    sessions, run/step/drop, reset-and-edit, recordings
  serialize.py  JSON views and text-level message editing
  app.py        FastAPI routes (/api/*), serves frontend/dist
frontend/src/   React + Tailwind UI; components/Overview.tsx is the D3-style session map
recordings/     saved runs (*.pkl: history + per-message checkpoints); harvest/ and archive/ hold the bulk runs
```
