export const get = <T,>(path: string) => fetch(`/api${path}`).then((r) => r.json() as Promise<T>);
export const post = async (path: string, body?: unknown) => {
  const r = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!r.ok) throw new Error((await r.json()).detail ?? r.statusText);
  return r.json();
};
