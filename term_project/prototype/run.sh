#!/usr/bin/env bash
# Start the debugger: backend API on :8000 (serves the built UI) and, with --dev, the Vite dev server on :5173.
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  uv venv -p 3.12 .venv && uv pip install -p .venv/bin/python -r backend/requirements.txt
fi
if [ ! -d frontend/node_modules ]; then (cd frontend && npm install); fi
if [ ! -d frontend/dist ] || [ "${1:-}" = "--build" ]; then (cd frontend && npm run build); fi
if [ "${1:-}" = "--dev" ]; then
  (cd frontend && npm run dev) &
fi
cd backend && exec ../.venv/bin/uvicorn agdbg.app:app --host 127.0.0.1 --port 8000
