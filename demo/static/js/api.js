// The explorer's HTTP API. Errors come back as JSON {error}; they are thrown as Error(message).

async function json(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error ?? `${response.status} ${response.statusText}`);
  return body;
}

export const get = (path) => fetch(path).then(json);
export const post = (path, body) =>
  fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  }).then(json);

export const tree = (kind = "packages") => get(`/api/tree?kind=${kind}`);
export const keys = () => get("/api/keys");
export const element = (key) => get(`/api/element/${encodeURIComponent(key)}`);
export const view = (kind, focus) =>
  get(`/api/view/${kind}` + (focus ? `?focus=${encodeURIComponent(focus)}` : ""));
export const search = (q, k = 10) => get(`/api/search?q=${encodeURIComponent(q)}&k=${k}`);
export const reload = () => post("/api/reload", {});

/** Whole server-sent events in `buffer` (as parsed JSON data) and the unfinished rest. */
export function parseSSE(buffer) {
  const chunks = buffer.split("\n\n");
  const rest = chunks.pop();
  const events = chunks
    .map((c) => c.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim()).join("\n"))
    .filter(Boolean)
    .map((d) => JSON.parse(d));
  return { events, rest };
}

/** POST /api/ask and call onEvent for each event; resolves when the stream ends. */
export async function ask(question, onEvent, signal) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
  if (!response.ok) await json(response);
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    const parsed = parseSSE(buffer + value);
    buffer = parsed.rest;
    parsed.events.forEach(onEvent);
  }
}
