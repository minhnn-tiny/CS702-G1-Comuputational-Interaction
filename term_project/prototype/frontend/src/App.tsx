import { useCallback, useEffect, useMemo, useState } from "react";
import { get, log, post } from "./api";
import { colorFor } from "./colors";
import Compose from "./components/Compose";
import ContextPanel from "./components/ContextPanel";
import History from "./components/History";
import Overview from "./components/Overview";
import Queue from "./components/Queue";
import Toast from "./components/Toast";
import type { Condition, EditRequest, State, Suspect } from "./types";

const params = new URLSearchParams(window.location.search);
const COND = (["reduced", "full", "e1"].includes(params.get("cond") ?? "") ? params.get("cond") : null) as Condition | null;
const PARTICIPANT = params.get("p");

export default function App() {
  const [state, setState] = useState<State>();
  const [tasks, setTasks] = useState<Record<string, { task: string; web: string }>>({});
  const [recordings, setRecordings] = useState<string[]>([]);
  const [viewed, setViewed] = useState<number>();
  const [highlight, setHighlight] = useState<number>();
  const [selected, setSelected] = useState<Suspect>();
  const [editRequest, setEditRequest] = useState<EditRequest>();
  const [offline, setOffline] = useState(false);

  const refresh = useCallback(() => get<State>("/state").then((s) => { setState(s); setOffline(false); }).catch(() => setOffline(true)), []);
  useEffect(() => {
    (COND || PARTICIPANT ? post("/session", { participant: PARTICIPANT, condition: COND, trial: params.get("trial") }).catch(() => undefined) : Promise.resolve()).then(refresh);
    get<Record<string, { task: string; web: string }>>("/tasks").then(setTasks).catch(() => undefined);
    get<string[]>("/recordings").then(setRecordings).catch(() => undefined);
    const id = setInterval(refresh, 700);
    return () => clearInterval(id);
  }, [refresh]);

  // follow the live session whenever a fork happens
  const current = state?.current_session ?? 0;
  useEffect(() => { setViewed(current); setSelected(undefined); }, [current]);
  useEffect(() => { setSelected(undefined); setEditRequest(undefined); }, [state?.recording, state?.task_id]);

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

  // The condition shown is the one in this tab's URL (so two tabs can show different conditions); the server's value is
  // only the fallback and what the log records.
  const condition: Condition = COND ?? state?.condition ?? "e1";
  const view = viewed ?? current;
  const bySession = useMemo(() => {
    const out: Record<number, Record<number, Suspect>> = {};
    for (const [sid, j] of Object.entries(state?.suspects ?? {})) out[Number(sid)] = Object.fromEntries(j.suspects.map((s) => [s.timestamp, s]));
    return out;
  }, [state?.suspects]);
  const shown = condition === "e1" ? bySession : {};  // E1 cues never reach the reduced / full conditions
  const openSuspect = (session: number, s: Suspect) => { setSelected(s); pick(session, s.timestamp); };
  const requestEdit = (s: Suspect) => { pick(view, s.timestamp); setEditRequest({ timestamp: s.timestamp, hint: s.suggestion, nonce: Date.now() }); log("edit_from_context", { timestamp: s.timestamp, rank: s.rank }); };

  if (!state) return <div className="p-8 text-slate-500">{offline ? "Backend not reachable on /api — is ./run.sh running?" : "Connecting to backend…"}</div>;
  const busy = state.running || state.busy || state.judging;
  const recKey = `${state.recording ?? state.task_id ?? "none"}`;
  const session = state.sessions[view] ?? state.sessions[state.sessions.length - 1];
  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-3 bg-slate-900 px-4 py-2 text-white">
        <h1 className="whitespace-nowrap text-lg font-semibold tracking-tight">Agent Team Debugger</h1>
        <div className="ml-2 flex gap-1">
          {state.agents.map((a) => <span key={a} className="badge text-white" style={{ background: colorFor(a, state.agents) }}>{a}</span>)}
        </div>
        {(PARTICIPANT || COND) && <span className="badge bg-slate-700 text-slate-200" title="study condition">{PARTICIPANT ? `${state.participant} · ` : ""}{condition}</span>}
        <div className="ml-auto flex items-center gap-2 text-xs">
          <select className="rounded bg-slate-700 p-1" value="" disabled={busy} onChange={(e) => e.target.value && post("/recordings/load", { name: e.target.value }).then(refresh).catch(() => undefined)}>
            <option value="">Load recording…</option>
            {recordings.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select className="rounded bg-slate-700 p-1" value="" disabled={busy} onChange={(e) => e.target.value && post("/task", { name: e.target.value }).then(refresh).catch(() => undefined)}>
            <option value="">Start new live task…</option>
            {Object.entries(tasks).map(([k, v]) => <option key={k} value={k}>{k} [{v.web}]: {v.task.slice(0, 60)}…</option>)}
          </select>
          <button className="btn whitespace-nowrap !border-slate-600 !bg-slate-700 !text-white" onClick={() => { const name = window.prompt("Recording name", `${state.task_id ?? "run"}-${new Date().toISOString().slice(0, 16).replace(/[-:T]/g, "")}`); if (name) post("/recordings/save", { name }).then(() => get<string[]>("/recordings").then(setRecordings)).catch(() => undefined); }}>Save recording</button>
          <span className={`rounded-full px-2 py-0.5 ${state.running ? "bg-emerald-500" : state.busy || state.judging ? "bg-amber-500" : offline ? "bg-red-500" : "bg-slate-600"}`}>{offline ? "offline" : state.running ? "running" : state.busy ? "stepping" : state.judging ? "judging" : "paused"}</span>
        </div>
      </header>
      {state.task && (
        <div className="border-b border-slate-200 bg-white px-4 py-1.5 text-xs text-slate-700">
          <span className="font-semibold">Task</span> {state.recording && <span className="badge bg-slate-100">recording: {state.recording}</span>} <span className="badge bg-slate-100">{state.web}</span> {state.task}
        </div>
      )}
      {state.errors.length > 0 && (
        <div className="border-b border-red-200 bg-red-50 px-4 py-1 text-xs text-red-800">
          <span className="font-semibold">Last model-call error</span> ({state.errors[state.errors.length - 1].model}): {state.errors[state.errors.length - 1].error} — that message was consumed without a reply; use Reset here on it (or Edit &amp; revert) to retry it.
        </div>
      )}
      <main className="flex min-h-0 min-w-0 grow gap-3 overflow-hidden p-3">
        <div className="flex w-[340px] shrink-0 flex-col gap-3">
          <Compose targets={state.targets} disabled={state.busy} />
          <Queue queue={state.queue} running={state.running} busy={state.busy} agents={state.agents} />
        </div>
        <History sessions={state.sessions} current={current} viewed={view} setViewed={setViewed} agents={state.agents} highlight={highlight} condition={condition} suspects={shown[view] ?? {}} editRequest={editRequest} onSuspect={(s) => openSuspect(view, s)} recKey={recKey} />
        {condition !== "reduced" && <Overview sessions={state.sessions} current={current} viewed={view} onPick={pick} suspects={shown} onSuspect={openSuspect} />}
        {condition === "e1" && session && (
          <ContextPanel session={session} judgement={state.suspects[String(session.id)]} judging={state.judging} selected={selected} agents={state.agents} canEdit={view === current} onSelect={setSelected} onJump={(ts) => pick(view, ts)} onEdit={requestEdit} />
        )}
      </main>
      <Toast />
    </div>
  );
}
