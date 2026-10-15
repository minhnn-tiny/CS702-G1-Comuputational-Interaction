import { post } from "../api";
import { colorFor } from "../colors";
import type { QueueMsg } from "../types";

interface Props { queue: QueueMsg[]; running: boolean; busy: boolean; agents: string[] }

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
        {queue.length === 0 && <li className="p-2 italic text-slate-400">{running ? "Agents are working…" : "Queue empty."}</li>}
        {queue.map((m, i) => (
          <li key={i} className="mb-1 rounded border border-slate-200 p-2">
            <div className="flex items-center gap-1">
              <span className="font-mono text-slate-400">{i === 0 ? "next" : `#${i}`}</span>
              <span className="badge text-white" style={{ background: colorFor(m.sender, agents) }}>{m.sender}</span>
              <span className="text-slate-400">→</span>
              <span className="badge bg-slate-100">{m.recipient ?? "?"}</span>
              <span className="ml-auto font-mono text-slate-500">{m.type}</span>
            </div>
            {m.content && <div className="mt-1 line-clamp-2 whitespace-pre-wrap text-slate-600">{m.content}</div>}
          </li>
        ))}
      </ul>
    </section>
  );
}
