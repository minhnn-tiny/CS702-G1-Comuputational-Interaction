import { useMemo, useState } from "react";
import { log } from "../api";
import { colorFor, field } from "../colors";
import type { ColorField, Msg, Session, Suspect } from "../types";

interface Props { sessions: Session[]; current: number; viewed: number; onPick: (session: number, timestamp: number) => void; suspects: Record<number, Record<number, Suspect>>; onSuspect?: (session: number, s: Suspect) => void }

const CELL = 14, GAP = 3, COL = 34, TOP = 26, LEFT = 8;

export default function Overview({ sessions, current, viewed, onPick, suspects, onSuspect }: Props) {
  const [color, setColor] = useState<ColorField>("type");
  const [filter, setFilter] = useState<string>();
  const [hover, setHover] = useState<{ m: Msg; x: number; y: number; s?: Suspect }>();

  // Layout: one column per session. A forked session shares its parent's prefix (the messages before the reset
  // point), so its column shows only the messages from the fork on, starting at the row of the message it replaced.
  const layout = useMemo(() => {
    const offset: number[] = [], own: Msg[][] = [];
    sessions.forEach((s, i) => {
      if (s.reset_from == null || i === 0) { offset[i] = 0; own[i] = s.messages; return; }
      const parent = own[i - 1];
      const row = parent.findIndex((m) => m.timestamp >= s.reset_from!);
      offset[i] = offset[i - 1] + (row < 0 ? parent.length : row);
      own[i] = s.messages.filter((m) => m.timestamp >= s.reset_from!);
    });
    const rows = Math.max(1, ...sessions.map((_, i) => offset[i] + own[i].length));
    return { offset, rows, own };
  }, [sessions]);

  const domain = useMemo(
    () => Array.from(new Set(sessions.flatMap((s) => s.messages.map((m) => field(m, color))))).sort(),
    [sessions, color],
  );
  const width = LEFT + sessions.length * COL + 8;
  const height = TOP + layout.rows * (CELL + GAP) + 8;

  return (
    <aside className="panel flex min-h-0 w-60 shrink-0 flex-col">
      <div className="panel-title">
        <span>Overview</span>
        <select className="rounded border border-slate-300 p-0.5 text-xs" value={color} onChange={(e) => { setColor(e.target.value as ColorField); setFilter(undefined); log("overview_color", { by: e.target.value }); }}>
          <option value="type">colour: type</option>
          <option value="sender">colour: sender</option>
          <option value="recipient">colour: recipient</option>
        </select>
      </div>
      <div className="relative flex min-h-0 grow gap-2 overflow-auto p-2">
        <svg width={width} height={height} className="shrink-0 select-none">
          {sessions.map((s, i) => {
            const x = LEFT + i * COL;
            const y0 = TOP + layout.offset[i] * (CELL + GAP);
            const sus = suspects[s.id] ?? {};
            return (
              <g key={s.id}>
                <text x={x + CELL / 2} y={12} textAnchor="middle" fontSize={10} fontWeight={i === viewed ? 700 : 400} fill={i === current ? "#4338ca" : "#64748b"}>S{s.id}</text>
                {i === viewed && <rect x={x - 3} y={TOP - 3} width={CELL + 6} height={height - TOP} rx={3} fill="#eef2ff" />}
                {s.reset_from != null && i > 0 && (
                  <g>
                    <path d={`M${x - COL + CELL} ${y0 + CELL / 2} H${x - 6} V${y0 - 1}`} stroke="#f59e0b" strokeWidth={1.5} fill="none" />
                    <circle cx={x - 6} cy={y0 + CELL / 2} r={3} fill="#f59e0b" />
                  </g>
                )}
                {layout.own[i].map((m, j) => {
                  const v = field(m, color);
                  const dim = filter != null && filter !== v;
                  const sp = sus[m.timestamp];
                  const y = y0 + j * (CELL + GAP);
                  return (
                    <g key={m.timestamp}>
                      <rect
                        x={x} y={y} width={CELL} height={CELL} rx={2}
                        fill={colorFor(v, domain)} opacity={dim ? 0.15 : 1}
                        stroke={sp ? "#e11d48" : hover?.m === m ? "#000" : "none"} strokeWidth={sp ? 2 : 1}
                        className="cursor-pointer"
                        onMouseEnter={(e) => setHover({ m, x: e.clientX, y: e.clientY, s: sp })}
                        onMouseLeave={() => setHover(undefined)}
                        onClick={() => { onPick(s.id, m.timestamp); log("overview_click", { session: s.id, timestamp: m.timestamp, suspect: sp?.rank }); if (sp) onSuspect?.(s.id, sp); }}
                      />
                      {sp && <text x={x + CELL + 3} y={y + CELL - 3} fontSize={9} fontWeight={700} fill="#e11d48" className="pointer-events-none">#{sp.rank}</text>}
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
        <ul className="sticky top-0 self-start text-[11px]">
          {domain.map((v) => (
            <li key={v}>
              <button className={`flex items-center gap-1 ${filter === v ? "font-bold" : ""}`} onClick={() => { setFilter(filter === v ? undefined : v); log("overview_filter", { value: v }); }}>
                <span className="inline-block h-3 w-3 rounded-sm" style={{ background: colorFor(v, domain) }} />
                <span className="truncate">{v}</span>
              </button>
            </li>
          ))}
          {Object.keys(suspects).length > 0 && <li className="mt-2 flex items-center gap-1 text-rose-600"><span className="inline-block h-3 w-3 rounded-sm border-2 border-rose-600" /> suspect</li>}
        </ul>
      </div>
      {hover && (
        <div className="pointer-events-none fixed z-50 max-w-xs rounded border border-slate-300 bg-white p-2 text-xs shadow-lg" style={{ left: Math.max(8, hover.x - 330), top: hover.y + 12 }}>
          <div className="font-semibold">t={hover.m.timestamp} · {hover.m.type}</div>
          <div className="text-slate-500">{hover.m.sender} → {hover.m.recipient ?? "—"}</div>
          {hover.s && <div className="mt-1 text-rose-700">suspect #{hover.s.rank} · {hover.s.category}: {hover.s.reason.slice(0, 160)}{hover.s.reason.length > 160 ? "…" : ""}</div>}
          <div className="mt-1 line-clamp-4 whitespace-pre-wrap text-slate-700">{hover.m.content}</div>
        </div>
      )}
    </aside>
  );
}
