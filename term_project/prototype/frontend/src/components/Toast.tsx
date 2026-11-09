import { useEffect, useState } from "react";
import { onError } from "../api";

export default function Toast() {
  const [msgs, setMsgs] = useState<{ id: number; text: string }[]>([]);
  useEffect(() => onError((text) => {
    const id = Date.now() + Math.random();
    setMsgs((m) => [...m, { id, text }]);
    setTimeout(() => setMsgs((m) => m.filter((x) => x.id !== id)), 6000);
  }), []);
  if (!msgs.length) return null;
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex max-w-md flex-col gap-2">
      {msgs.map((m) => (
        <div key={m.id} className="pointer-events-auto rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-800 shadow-lg">
          <span className="font-semibold">Error</span> {m.text}
          <button className="ml-2 text-red-500 hover:underline" onClick={() => setMsgs((x) => x.filter((y) => y.id !== m.id))}>dismiss</button>
        </div>
      ))}
    </div>
  );
}
