import { useState } from "react";
import { post } from "../api";
import { colorFor } from "../colors";
import type { Msg, Session } from "../types";

interface Props { sessions: Session[]; current: number; viewed: number; setViewed: (s: number) => void; agents: string[]; highlight?: number }

function Card({ m, agents, canEdit, flash }: { m: Msg; agents: string[]; canEdit: boolean; flash: boolean }) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(m.content);
  const [err, setErr] = useState<string>();
  const long = m.content.length > 400 || m.content.split("\n").length > 8;
  const act = (content: string | null) =>
    post("/edit", { timestamp: m.timestamp, content }).then(() => setEditing(false)).catch((e) => setErr(e.message));
  return (
    <article id={`msg-${m.timestamp}`} className={`panel scroll-mt-2 border-l-4 transition-shadow ${flash ? "ring-2 ring-amber-400" : ""}`} style={{ borderLeftColor: colorFor(m.sender, agents) }}>
      <header className="flex flex-wrap items-center gap-1.5 px-3 pt-2 text-xs">
        <span className="font-mono text-slate-400">t={m.timestamp}</span>
        <span className="badge text-white" style={{ background: colorFor(m.sender, agents) }}>{m.sender}</span>
        <span className="text-slate-400">{m.kind === "publish" ? "⇉" : m.kind === "send" ? "→" : "↩"}</span>
        <span className="badge bg-slate-100">{m.recipient ?? "—"}</span>
        <span className="badge border border-slate-200 font-mono">{m.type}</span>
        {m.source && m.source !== m.sender && <span className="text-slate-400">source: {m.source}</span>}
        <span className="ml-auto flex gap-1">
          {canEdit && m.editable && !editing && (
            <>
              <button className="btn !py-0 text-[11px]" title="Edit this message, revert the team to just before it and continue in a new session" onClick={() => { setDraft(m.content); setEditing(true); }}>✎ Edit &amp; revert</button>
              <button className="btn !py-0 text-[11px]" title="Revert the team to just before this message and re-send it unchanged" onClick={() => act(null)}>↺ Reset here</button>
            </>
          )}
        </span>
      </header>
      <div className="px-3 pb-2 pt-1">
        {editing ? (
          <div className="space-y-1">
            <textarea className="h-40 w-full rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs" value={draft} onChange={(e) => setDraft(e.target.value)} autoFocus />
            <div className="flex gap-1">
              <button className="btn btn-primary !py-0.5 text-xs" onClick={() => act(draft)}>Save edit &amp; revert</button>
              <button className="btn !py-0.5 text-xs" onClick={() => setEditing(false)}>Cancel</button>
              {err && <span className="text-xs text-red-600">{err}</span>}
            </div>
          </div>
        ) : (
          <pre className={`whitespace-pre-wrap break-words font-mono text-xs text-slate-700 ${!open && long ? "max-h-28 overflow-hidden" : ""}`}>{m.content || <span className="italic text-slate-400">(no text payload)</span>}</pre>
        )}
        {long && !editing && (
          <button className="mt-1 text-[11px] text-indigo-700 hover:underline" onClick={() => setOpen(!open)}>{open ? "show less" : "show more"}</button>
        )}
      </div>
    </article>
  );
}

export default function History({ sessions, current, viewed, setViewed, agents, highlight }: Props) {
  const s = sessions[viewed] ?? sessions[sessions.length - 1];
  return (
    <section className="flex min-h-0 grow flex-col">
      <div className="mb-2 flex items-center gap-2 text-sm">
        <span className="font-semibold">Message history</span>
        <div className="flex gap-1">
          {sessions.map((x) => (
            <button key={x.id} className={`btn !py-0.5 text-xs ${x.id === viewed ? "btn-primary" : ""}`} onClick={() => setViewed(x.id)}>
              session {x.id}{x.id === current ? " (live)" : ""}
            </button>
          ))}
        </div>
        {s?.reset_from != null && <span className="text-xs text-slate-500">forked from t={s.reset_from}</span>}
        <span className="ml-auto text-xs text-slate-500">{s?.messages.length ?? 0} messages</span>
      </div>
      <div id="history-scroll" className="min-h-0 grow space-y-2 overflow-y-auto pr-1">
        {s?.messages.map((m) => <Card key={m.timestamp} m={m} agents={agents} canEdit={viewed === current} flash={highlight === m.timestamp} />)}
        {!s?.messages.length && <div className="p-6 text-center text-sm italic text-slate-400">No messages yet. Load a recording or start a task.</div>}
      </div>
    </section>
  );
}
