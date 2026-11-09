import { useState } from "react";
import { post } from "../api";
import { colorFor } from "../colors";
import type { QueueMsg } from "../types";

interface Props { queue: QueueMsg[]; running: boolean; busy: boolean; agents: string[] }

function Item({ m, i, idle, agents }: { m: QueueMsg; i: number; idle: boolean; agents: string[] }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(m.content);
  const editable = m.type === "TextMessage" && idle;
  return (
    <li className="mb-1 rounded border border-slate-200 p-2">
      <div className="flex items-center gap-1">
        <span className="font-mono text-slate-400">{i === 0 ? "next" : `#${i}`}</span>
        <span className="badge text-white" style={{ background: colorFor(m.sender, agents) }}>{m.sender}</span>
        <span className="text-slate-400">→</span>
        <span className="badge bg-slate-100">{m.recipient ?? "?"}</span>
        <span className="ml-auto font-mono text-slate-500">{m.type}</span>
        {editable && !editing && <button className="btn !px-1 !py-0 text-[10px]" title="Edit this queued message before it is processed" onClick={() => { setDraft(m.content); setEditing(true); }}>✎</button>}
        {idle && <button className="btn !px-1 !py-0 text-[10px]" title="Remove this message from the queue" onClick={() => post("/queue/edit", { index: i, content: null }).catch(() => undefined)}>✕</button>}
      </div>
      {editing ? (
        <div className="mt-1 space-y-1">
          <textarea className="h-24 w-full rounded border border-amber-300 bg-amber-50 p-1 font-mono text-[11px]" value={draft} onChange={(e) => setDraft(e.target.value)} autoFocus />
          <div className="flex gap-1">
            <button className="btn btn-primary !py-0 text-[11px]" onClick={() => post("/queue/edit", { index: i, content: draft }).then(() => setEditing(false)).catch(() => undefined)}>Save</button>
            <button className="btn !py-0 text-[11px]" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        m.content && <div className="mt-1 line-clamp-2 whitespace-pre-wrap text-slate-600">{m.content}</div>
      )}
    </li>
  );
}

export default function Queue({ queue, running, busy, agents }: Props) {
  const idle = !running && !busy;
  return (
    <section className="panel flex min-h-0 grow flex-col">
      <div className="panel-title">
        <span>Message queue <span className="ml-1 rounded-full bg-slate-200 px-2 text-xs">{queue.length}</span></span>
        <div className="flex gap-1">
          {running ? (
            <button className="btn" onClick={() => post("/stop")}>■ Stop</button>
          ) : (
            <button className="btn btn-primary" disabled={busy} onClick={() => post("/run")}>▶ Run</button>
          )}
          <button className="btn" disabled={!idle || !queue.length} onClick={() => post("/step")}>{busy ? "…" : "Step"}</button>
          <button className="btn" disabled={!idle || !queue.length} onClick={() => post("/drop")}>Drop</button>
        </div>
      </div>
      <ul className="min-h-0 grow overflow-y-auto p-2 text-xs">
        {queue.length === 0 && <li className="p-2 italic text-slate-400">{running ? "Agents are working…" : busy ? "Processing one message…" : "Queue empty."}</li>}
        {queue.map((m, i) => <Item key={`${i}-${m.type}-${m.content.slice(0, 20)}`} m={m} i={i} idle={idle} agents={agents} />)}
      </ul>
    </section>
  );
}
