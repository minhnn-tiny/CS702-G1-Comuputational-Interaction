export const get = <T,>(path: string) => fetch(`/api${path}`).then((r) => r.json() as Promise<T>);

type Listener = (msg: string) => void;
const listeners = new Set<Listener>();
/** Subscribe to API failures (the App shows them as toasts). */
export const onError = (fn: Listener) => { listeners.add(fn); return () => { listeners.delete(fn); }; };

export const post = async (path: string, body?: unknown) => {
  let r: Response;
  try {
    r = await fetch(`/api${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    const msg = "Backend unreachable";
    listeners.forEach((l) => l(msg));
    throw new Error(msg);
  }
  if (!r.ok) {
    const msg = (await r.json().catch(() => ({}))).detail ?? r.statusText;
    listeners.forEach((l) => l(msg));
    throw new Error(msg);
  }
  return r.json();
};

/** Fire-and-forget study log entry (UI-side events: flags, clicks, panel use). */
export const log = (event: string, data: Record<string, unknown> = {}) => { post("/log", { event, data }).catch(() => undefined); };
