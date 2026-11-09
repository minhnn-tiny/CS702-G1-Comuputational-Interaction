import { log, post } from "../api";
import { colorFor } from "../colors";
import { assemble } from "../context";
import type { Judgement, Msg, Session, Suspect } from "../types";

interface Props {
  session: Session; judgement?: Judgement; judging: boolean; selected?: Suspect; agents: string[]; canEdit: boolean;
  onSelect: (s: Suspect | undefined) => void; onJump: (ts: number) => void; onEdit: (s: Suspect) => void;
}

function Snippet({ m, agents, onJump, label }: { m: Msg; agents: string[]; onJump: (ts: number) => void; label?: string }) {
  return (
    <button className="block w-full rounded border border-slate-200 bg-white p-1.5 text-left hover:bg-slate-50" onClick={() => onJump(m.timestamp)}>
      <div className="flex items-center gap-1 text-[10px]">
        {label && <span className="badge bg-slate-100">{label}</span>}
        <span className="font-mono text-slate-400">t={m.timestamp}</span>
        <span className="badge text-white" style={{ background: colorFor(m.sender, agents) }}>{m.sender}</span>
        <span className="text-slate-400">→ {m.recipient ?? "—"}</span>
        <span className="ml-auto font-mono text-slate-400">{m.type.replace("Event", "")}</span>
      </div>
      <div className="mt-0.5 line-clamp-3 whitespace-pre-wrap font-mono text-[10px] text-slate-600">{m.content || "(no text)"}</div>
    </button>
  );
}

export default function ContextPanel({ session, judgement, judging, selected, agents, canEdit, onSelect, onJump, onEdit }: Props) {
  const ctx = selected ? assemble(session.messages, selected) : undefined;
  return (
    <aside className="panel flex min-h-0 w-80 shrink-0 flex-col">
      <div className="panel-title">
        <span>Error context <span className="ml-1 text-[10px] font-normal text-slate-400">session {session.id}</span></span>
        <button className="btn btn-primary !py-0.5 text-xs" disabled={judging || !session.messages.length} title="Ask the judge model to rank the messages most likely to have caused the failure" onClick={() => post("/judge", { session: session.id }).catch(() => undefined)}>
          {judging ? "Judging…" : judgement ? "Re-run judge" : "Find suspects"}
        </button>
      </div>
      <div className="min-h-0 grow space-y-2 overflow-y-auto p-2 text-xs">
        {!judgement && !judging && <p className="text-slate-500">No suspects yet. <b>Find suspects</b> runs one model pass over this session and ranks up to five messages that most likely derailed it. Click a suspect to see its context.</p>}
        {judging && <p className="animate-pulse text-slate-500">Reading {session.messages.length} messages…</p>}
        {judgement && (
          <>
            <p className="rounded bg-slate-50 p-2 text-slate-700">{judgement.summary}</p>
            <ol className="space-y-1">
              {judgement.suspects.map((s) => (
                <li key={s.timestamp}>
                  <button className={`w-full rounded border p-1.5 text-left ${selected?.timestamp === s.timestamp ? "border-rose-400 bg-rose-50" : "border-slate-200 hover:bg-slate-50"}`} onClick={() => { onSelect(selected?.timestamp === s.timestamp ? undefined : s); onJump(s.timestamp); log("suspect_open", { timestamp: s.timestamp, rank: s.rank }); }}>
                    <div className="flex items-center gap-1"><span className="badge bg-rose-600 text-white">#{s.rank}</span><span className="font-mono text-slate-400">t={s.timestamp}</span><span className="font-semibold">{s.category}</span>{!s.editable && <span className="ml-auto text-[10px] text-slate-400">not editable</span>}</div>
                    <div className="mt-0.5 line-clamp-3 text-slate-600">{s.reason}</div>
                  </button>
                </li>
              ))}
            </ol>
            {selected && ctx && (
              <div className="space-y-2 border-t border-slate-200 pt-2">
                <div className="font-semibold">Context for t={selected.timestamp}</div>
                <Snippet m={ctx.target} agents={agents} onJump={onJump} label="flagged" />
                <p className="text-slate-700">{selected.reason}</p>
                {ctx.chain.length > 0 && <><div className="text-[10px] font-semibold uppercase text-slate-400">Who said what to this agent</div>{ctx.chain.map((m) => <Snippet key={m.timestamp} m={m} agents={agents} onJump={onJump} />)}</>}
                {ctx.tools.length > 0 && <><div className="text-[10px] font-semibold uppercase text-slate-400">Preceding tool calls</div>{ctx.tools.map((m) => <Snippet key={m.timestamp} m={m} agents={agents} onJump={onJump} />)}</>}
                {ctx.warnings.length > 0 && <><div className="text-[10px] font-semibold uppercase text-slate-400">Warnings in this window</div>{ctx.warnings.map((m) => <Snippet key={m.timestamp} m={m} agents={agents} onJump={onJump} label="warning" />)}</>}
                {ctx.evidence.length > 0 && <><div className="text-[10px] font-semibold uppercase text-slate-400">Evidence cited by the judge</div>{ctx.evidence.map((m) => <Snippet key={m.timestamp} m={m} agents={agents} onJump={onJump} />)}</>}
                <div className="rounded border border-rose-200 bg-rose-50 p-2 text-rose-900"><span className="font-semibold">Suggested edit:</span> {selected.suggestion}</div>
                {selected.editable && canEdit && <button className="btn btn-primary w-full" onClick={() => onEdit(selected)}>✎ Edit this message &amp; revert</button>}
                {selected.editable && !canEdit && <p className="text-[10px] text-slate-400">Switch to the live session to edit.</p>}
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
}
