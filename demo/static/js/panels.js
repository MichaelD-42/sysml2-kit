// Side panels: hierarchy tree, search, Cypher, ask, and the compliance table.
// Every key is rendered as <a data-key>; main.js turns a click on one into setFocus.
import * as api from "./api.js";
import { esc } from "./render.js";

// what the agent cites: need ids (PC-001, EDU-PC-003), uids, test result ids
const KEY_SHAPED = /^(EDU-)?[A-Z]+(-[A-Z]+)*-\d+$|^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$|^testresult__\S+$/;
const UID = /^[0-9a-f]{8}-/;

export const keyLink = (key, label) =>
  `<a href="#" class="key" data-key="${esc(key)}">${esc(label ?? key)}</a>`;

/** Display name for a key: cached, else the element's name, title or expression; the key on failure. */
export async function nameOf(key, names) {
  const known = names.get(key);
  if (known && known !== key) return known;
  try {
    const { node } = await api.element(key);
    const name = node.name ?? node.title ?? node.expression ?? key;
    names.set(key, name);
    return name;
  } catch {
    return key;
  }
}

/** Fill every [data-name-of] element under `root` with that key's display name. */
export function fillNames(root, names) {
  for (const el of root.querySelectorAll("[data-name-of]"))
    nameOf(el.dataset.nameOf, names).then((name) => (el.textContent = name));
}

/** Answer text as HTML: backticked known keys become focus links (uids show their name),
 * unknown key-shaped tokens are marked unresolved. */
export function linkCitations(text, knownKeys, names = new Map()) {
  return String(text)
    .split(/```\w*\n?([\s\S]*?)```/)
    .map((part, i) => (i % 2 ? `<pre><code>${esc(part)}</code></pre>` : inline(part, knownKeys, names)))
    .join("");
}

function citation(key, names) {
  if (!UID.test(key)) return keyLink(key);
  const name = names.get(key);
  if (name && name !== key) return keyLink(key, name);
  return `<a href="#" class="key" data-key="${esc(key)}" data-name-of="${esc(key)}">${esc(key)}</a>`;
}

function inline(text, knownKeys, names) {
  return text
    .split(/`([^`]*)`/)
    .map((part, i) => {
      if (i % 2 === 0) return esc(part);
      if (knownKeys.has(part)) return citation(part, names);
      return KEY_SHAPED.test(part)
        ? `<code class="unresolved" title="not found in the model">${esc(part)}</code>`
        : `<code>${esc(part)}</code>`;
    })
    .join("");
}

// test result and uid keys are generated, not ids a reader cites
const GENERATED = /^(testresult__|[0-9a-f]{8}-)/;

export function renderTree(el, roots) {
  const item = (n, depth) => {
    const kids = n.children ?? [];
    const open = depth < 1;
    const label = n.key
      ? `${n.rel ? `<span class="rel">${esc(n.rel)}</span> ` : ""}${keyLink(n.key, n.name)}${n.key !== n.name && !GENERATED.test(n.key) ? ` <span class="id">${esc(n.key)}</span>` : ""}`
      : `<span class="group">${esc(n.name)}</span>`;
    const marks = `${n.domain ? ` <span class="domain d-${esc(n.domain)}">${esc(n.domain)}</span>` : ""}${n.platform ? ' <span class="kind">platform</span>' : ""}`;
    return `<li data-tree="${esc(n.key ?? "")}">
      ${kids.length ? `<button type="button" class="twisty" aria-expanded="${open}" aria-label="expand ${esc(n.name)}"></button>` : '<span class="twisty-gap"></span>'}
      ${label}${n.key && !n.rel ? ` <span class="kind">${esc(n.kind)}</span>` : ""}${marks}
      ${kids.length ? `<ul${open ? "" : " hidden"}>${kids.map((c) => item(c, depth + 1)).join("")}</ul>` : ""}
    </li>`;
  };
  el.innerHTML = `<ul class="tree">${roots.map((r) => item(r, 0)).join("")}</ul>`;
  el.onclick = (e) => {
    const t = e.target.closest(".twisty");
    if (!t) return;
    const open = t.getAttribute("aria-expanded") !== "true";
    t.setAttribute("aria-expanded", open);
    t.parentElement.querySelector(":scope > ul").hidden = !open;
  };
}

const openUp = (li) => {
  for (let up = li.parentElement.closest("li"); up; up = up.parentElement.closest("li")) {
    up.querySelector(":scope > .twisty")?.setAttribute("aria-expanded", "true");
    up.querySelector(":scope > ul").hidden = false;
  }
};

/** Mark every row of `key` (opening its ancestors) and, more lightly, the first row of each linked key. */
export function revealInTree(el, key, linked = new Set()) {
  el.querySelectorAll("li.current, li.linked").forEach((li) => li.classList.remove("current", "linked"));
  const rows = [...el.querySelectorAll("li[data-tree]")];
  const hits = rows.filter((x) => x.dataset.tree === key);
  hits.forEach((li) => (li.classList.add("current"), openUp(li)));
  for (const k of linked) {
    const li = rows.find((x) => x.dataset.tree === k && !x.parentElement.closest(`li[data-tree="${CSS.escape(key)}"]`));
    if (li) li.classList.add("linked"), openUp(li);
  }
  hits[0]?.scrollIntoView({ block: "nearest" });
}

export function mountSearch(el, names) {
  el.innerHTML = `<label for="q">Search elements and needs</label>
    <input id="q" type="search" autocomplete="off" placeholder="PC-001, cooling, peak torque">
    <p class="status" aria-live="polite"></p><ul class="hits"></ul>`;
  const input = el.querySelector("input");
  const status = el.querySelector(".status");
  const hits = el.querySelector(".hits");
  let timer;
  let latest = 0;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const q = input.value.trim();
      const mine = ++latest;
      if (!q) return void ((hits.innerHTML = ""), (status.textContent = ""));
      try {
        const found = await api.search(q);
        if (mine !== latest) return;
        status.textContent = `${found.length} hits`;
        hits.innerHTML = found
          .map((h) => `<li>${keyLink(h.key, h.name ?? h.key)}
            <span class="kind">${esc(h.kind)}</span>${h.shortName ? ` <span class="id">${esc(h.shortName)}</span>` : ""}
            ${h.owner ? `<span class="owner">in <span data-name-of="${esc(h.owner)}">${esc(names.get(h.owner) ?? "…")}</span></span>` : ""}</li>`)
          .join("");
        fillNames(hits, names);
      } catch (e) {
        status.innerHTML = `<span class="error">${esc(e.message)}</span>`;
      }
    }, 200);
  });
}

function cell(v, knownKeys) {
  if (v === null || v === undefined) return '<span class="none">–</span>';
  if (Array.isArray(v)) return v.map((x) => cell(x, knownKeys)).join(", ");
  if (typeof v === "object") return v.key ? keyLink(v.key, v.name ?? v.key) : esc(JSON.stringify(v));
  return knownKeys.has(String(v)) ? keyLink(String(v)) : esc(v);
}

export async function mountCypher(el, knownKeys) {
  el.innerHTML = `<label for="cy-example">Example</label><select id="cy-example"></select>
    <label for="cy-query">Read-only Cypher</label><textarea id="cy-query" rows="7" spellcheck="false"></textarea>
    <div class="row"><button type="button" class="primary">Run</button><span class="status" aria-live="polite"></span></div>
    <div class="result"></div>`;
  const [select, query, run, status, result] = ["select", "textarea", "button", ".status", ".result"].map((s) => el.querySelector(s));
  const examples = await api.examples();
  select.innerHTML = examples.map((x, i) => `<option value="${i}">${esc(x.title)}</option>`).join("");
  const pick = () => (query.value = examples[select.value]?.query ?? "");
  select.onchange = pick;
  pick();
  const go = async () => {
    run.disabled = true;
    status.textContent = "running";
    try {
      const { columns, rows } = await api.cypher(query.value);
      status.textContent = `${rows.length} rows`;
      result.innerHTML = `<table><thead><tr>${columns.map((c) => `<th scope="col">${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${rows.map((r) => `<tr>${r.map((v) => `<td>${cell(v, knownKeys)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    } catch (e) {
      status.textContent = "";
      result.innerHTML = `<p class="error">${esc(e.message)}</p>`;
    } finally {
      run.disabled = false;
    }
  };
  run.onclick = go;
  // block bodies: an on-handler that returns false cancels the key, so nothing could be typed
  query.onkeydown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) go();
  };
}

export function mountAsk(el, knownKeys, names) {
  el.innerHTML = `<div class="log" aria-live="polite"></div>
    <form><label for="ask-q">Ask about the product</label>
    <textarea id="ask-q" rows="3" placeholder="Which constraints apply to the drive motor, and where do they come from?"></textarea>
    <div class="row"><button type="submit" class="primary">Ask</button></div></form>`;
  const [log, form, input, send] = [".log", "form", "textarea", "button"].map((s) => el.querySelector(s));
  input.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) e.preventDefault(), form.requestSubmit();
  };
  form.onsubmit = async (e) => {
    e.preventDefault();
    const question = input.value.trim() || input.placeholder; // empty box: ask the example
    if (send.disabled) return;
    const turn = document.createElement("div");
    turn.className = "turn";
    turn.innerHTML = `<p class="question">${esc(question)}</p><ul class="tools"></ul><div class="answer"></div><p class="error" hidden></p>`;
    log.append(turn);
    const [tools, answer, error] = [".tools", ".answer", ".error"].map((s) => turn.querySelector(s));
    const fail = (message) => ((error.hidden = false), (error.textContent = message));
    const texts = [];
    let ended = false;
    send.disabled = input.disabled = true;
    answer.textContent = "thinking";
    answer.classList.add("pending");
    try {
      await api.ask(question, (ev) => {
        if (ev.type === "text") {
          texts.push(ev.text);
          answer.classList.remove("pending");
          answer.innerHTML = linkCitations(texts.join("\n\n"), knownKeys, names);
          fillNames(answer, names);
        } else if (ev.type === "tool") {
          tools.insertAdjacentHTML("beforeend", `<li><span class="tool">${esc(ev.name.replace(/^mcp__\w+?__/, ""))}</span> ${esc(ev.summary)}</li>`);
        } else if (ev.type === "error") {
          ended = true;
          fail(ev.message);
        } else if (ev.type === "done") ended = true;
        turn.scrollIntoView({ block: "end" });
      });
      if (!ended) fail("the answer stream ended early");
    } catch (err) {
      fail(err.message);
    } finally {
      if (!texts.length) answer.remove();
      send.disabled = input.disabled = false;
      input.value = "";
      input.focus();
    }
  };
}

export function renderCompliance(el, view, focus) {
  const rows = view.rows ?? [];
  const links = (ks) => ks.map((k) => keyLink(k)).join(", ");
  el.innerHTML = `<table class="compliance"><caption>Compliance of the RFQ's customer requirements</caption>
    <thead><tr><th scope="col">CRS</th><th scope="col">Title</th><th scope="col">Features</th><th scope="col">Reuse</th>
    <th scope="col">Partial</th><th scope="col">Statements</th><th scope="col">Domains</th></tr></thead>
    <tbody>${rows.map((r) => `<tr data-row="${esc(r.crs)}"${r.crs === focus ? ' class="focus"' : ""}>
      <td>${keyLink(r.crs)}</td><td>${esc(r.title)}</td><td>${links(r.features ?? [])}</td><td>${esc(r.reuse)}</td>
      <td>${r.partial ? "partial" : "full"}</td><td>${(r.statements ?? []).map(([k, v]) => `${keyLink(k)} ${esc(v)}`).join(", ")}</td>
      <td>${(r.domains ?? []).map((d) => `<span class="domain d-${esc(d)}">${esc(d)}</span>`).join(" ")}</td></tr>`).join("")}
    </tbody></table>
    ${view.findings?.length ? `<h3>Findings</h3><ul class="findings">${view.findings.map((f) => `<li>${esc(typeof f === "string" ? f : JSON.stringify(f))}</li>`).join("")}</ul>` : ""}`;
}
