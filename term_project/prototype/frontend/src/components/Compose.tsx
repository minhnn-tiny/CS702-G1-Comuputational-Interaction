import { useState } from "react";
import { post } from "../api";

const TYPES = [
  { v: "GroupChatMessage", label: "GroupChatMessage (text broadcast to agents)" },
  { v: "GroupChatRequestPublish", label: "GroupChatRequestPublish (ask one agent to respond)" },
  { v: "GroupChatStart", label: "GroupChatStart (new task for the orchestrator)" },
];

export default function Compose({ targets, disabled }: { targets: string[]; disabled: boolean }) {
  const [type, setType] = useState(TYPES[0].v);
  const [target, setTarget] = useState("group");
  const [source, setSource] = useState("user");
  const [content, setContent] = useState("");
  const [err, setErr] = useState<string>();
  const needsContent = type !== "GroupChatRequestPublish";
  const send = () =>
    post("/send", { type, target, content, source })
      .then(() => { setContent(""); setErr(undefined); })
      .catch((e) => setErr(String(e.message)));
  return (
    <section className="panel">
      <div className="panel-title">Send message</div>
      <div className="space-y-2 p-3 text-sm">
        <label className="block">
          <span className="text-xs text-slate-500">Type</span>
          <select className="mt-0.5 w-full rounded border border-slate-300 p-1" value={type} onChange={(e) => setType(e.target.value)}>
            {TYPES.map((t) => <option key={t.v} value={t.v}>{t.label}</option>)}
          </select>
        </label>
        <div className="flex gap-2">
          <label className="block grow">
            <span className="text-xs text-slate-500">To (topic)</span>
            <select className="mt-0.5 w-full rounded border border-slate-300 p-1" value={target} onChange={(e) => setTarget(e.target.value)} disabled={type === "GroupChatStart"}>
              {targets.map((t) => <option key={t}>{t}</option>)}
            </select>
          </label>
          <label className="block w-28">
            <span className="text-xs text-slate-500">Source</span>
            <input className="mt-0.5 w-full rounded border border-slate-300 p-1" value={source} onChange={(e) => setSource(e.target.value)} />
          </label>
        </div>
        {needsContent && (
          <textarea className="h-24 w-full rounded border border-slate-300 p-1.5 font-mono text-xs" placeholder="content" value={content} onChange={(e) => setContent(e.target.value)} />
        )}
        <div className="flex items-center gap-2">
          <button className="btn btn-primary" disabled={disabled || (needsContent && !content.trim())} onClick={send}>Send to queue</button>
          {err && <span className="text-xs text-red-600">{err}</span>}
        </div>
      </div>
    </section>
  );
}
