import { useCallback, useEffect, useState } from "react";
import { get, post } from "./api";
import { colorFor } from "./colors";
import Compose from "./components/Compose";
import History from "./components/History";
import Overview from "./components/Overview";
import Queue from "./components/Queue";
import type { State } from "./types";

export default function App() {
  const [state, setState] = useState<State>();
  const [tasks, setTasks] = useState<Record<string, string>>({});
  const [recordings, setRecordings] = useState<string[]>([]);
  const [viewed, setViewed] = useState<number>();
  const [highlight, setHighlight] = useState<number>();

  const refresh = useCallback(() => get<State>("/state").then(setState).catch(() => undefined), []);
  useEffect(() => {
    refresh();
    get<Record<string, string>>("/tasks").then(setTasks);
    get<string[]>("/recordings").then(setRecordings);
    const id = setInterval(refresh, 700);
    return () => clearInterval(id);
  }, [refresh]);

  // follow the live session whenever a fork happens
  const current = state?.current_session ?? 0;
  useEffect(() => setViewed(current), [current]);

  const pick = (session: number, ts: number) => {
    setViewed(session);
    setHighlight(ts);
    setTimeout(() => {
      // scroll only the history pane (scrollIntoView would also shift the page layout)
      const box = document.getElementById("history-scroll"), el = document.getElementById(`msg-${ts}`);
      if (box && el) box.scrollTo({ top: el.offsetTop - box.offsetTop - box.clientHeight / 2 + el.clientHeight / 2, behavior: "smooth" });
    }, 50);
    setTimeout(() => setHighlight(undefined), 1800);
  };

  if (!state) return <div className="p-8 text-slate-500">Connecting to backend…</div>;
  const busy = state.running || state.busy;
  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-3 bg-slate-900 px-4 py-2 text-white">
        <h1 className="text-lg font-semibold tracking-tight">Agent Team Debugger</h1>
        <div className="ml-2 flex gap-1">
          {state.agents.map((a) => <span key={a} className="badge text-white" style={{ background: colorFor(a, state.agents) }}>{a}</span>)}
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs">
          <select className="rounded bg-slate-700 p-1" value="" disabled={busy} onChange={(e) => e.target.value && post("/recordings/load", { name: e.target.value }).then(refresh)}>
            <option value="">Load recording…</option>
            {recordings.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select className="rounded bg-slate-700 p-1" value="" disabled={busy} onChange={(e) => e.target.value && post("/task", { name: e.target.value }).then(refresh)}>
            <option value="">Start new live task…</option>
            {Object.entries(tasks).map(([k, v]) => <option key={k} value={k}>{k}: {v.slice(0, 60)}…</option>)}
          </select>
          <button className="btn !border-slate-600 !bg-slate-700 !text-white" onClick={() => post("/recordings/save", { name: `${state.task_id ?? "run"}-${Date.now()}` }).then(() => get<string[]>("/recordings").then(setRecordings))}>Save recording</button>
          <span className={`rounded-full px-2 py-0.5 ${state.running ? "bg-emerald-500" : state.busy ? "bg-amber-500" : "bg-slate-600"}`}>{state.running ? "running" : state.busy ? "stepping" : "paused"}</span>
        </div>
      </header>
      {state.task && (
        <div className="border-b border-slate-200 bg-white px-4 py-1.5 text-xs text-slate-700">
          <span className="font-semibold">Task</span> {state.recording && <span className="badge bg-slate-100">recording: {state.recording}</span>} {state.task}
        </div>
      )}
      <main className="flex min-h-0 grow gap-3 p-3">
        <div className="flex w-[380px] shrink-0 flex-col gap-3">
          <Compose targets={state.targets} disabled={state.busy} />
          <Queue queue={state.queue} running={state.running} busy={state.busy} agents={state.agents} />
        </div>
        <History sessions={state.sessions} current={current} viewed={viewed ?? current} setViewed={setViewed} agents={state.agents} highlight={highlight} />
        <Overview sessions={state.sessions} current={current} viewed={viewed ?? current} onPick={pick} />
      </main>
    </div>
  );
}
