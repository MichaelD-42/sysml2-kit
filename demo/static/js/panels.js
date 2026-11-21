// Side panels: hierarchy tree, search, Cypher, ask, and the compliance table.
// Every key is rendered as <a data-key>; main.js turns a click on one into setFocus.
import * as api from "./api.js";
import { esc } from "./render.js";

const ID = /^\S+$/;

export const keyLink = (key, label) =>
  `<a href="#" class="key" data-key="${esc(key)}">${esc(label ?? key)}</a>`;

/** Answer text as HTML: backticked known keys become focus links, unknown ids are marked. */
export function linkCitations(text, knownKeys) {
  return String(text)
    .split(/```\w*\n?([\s\S]*?)```/)
    .map((part, i) => (i % 2 ? `<pre><code>${esc(part)}</code></pre>` : inline(part, knownKeys)))
    .join("");
}

function inline(text, knownKeys) {
  return text
    .split(/`([^`]*)`/)
    .map((part, i) => {
      if (i % 2 === 0) return esc(part);
      if (knownKeys.has(part)) return keyLink(part);
      return ID.test(part)
        ? `<code class="unresolved" title="not found in the model">${esc(part)}</code>`
        : `<code>${esc(part)}</code>`;
    })
    .join("");
}

export function renderTree(el, roots) {
  const item = (n, depth) => {
    const kids = n.children ?? [];
    const open = depth < 1;
    return `<li data-tree="${esc(n.key)}">
      ${kids.length ? `<button type="button" class="twisty" aria-expanded="${open}" aria-label="expand ${esc(n.name)}"></button>` : '<span class="twisty-gap"></span>'}
      ${keyLink(n.key, n.name)} <span class="kind">${esc(n.kind)}</span>
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

/** Mark `key` in the tree, opening its ancestors. */
export function revealInTree(el, key) {
  el.querySelectorAll("li.current").forEach((li) => li.classList.remove("current"));
  const li = [...el.querySelectorAll("li[data-tree]")].find((x) => x.dataset.tree === key);
  if (!li) return;
  li.classList.add("current");
  for (let up = li.parentElement.closest("li"); up; up = up.parentElement.closest("li")) {
    up.querySelector(":scope > .twisty")?.setAttribute("aria-expanded", "true");
    up.querySelector(":scope > ul").hidden = false;
  }
  li.scrollIntoView({ block: "nearest" });
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
            ${h.owner ? `<span class="owner">in ${esc(names.get(h.owner) ?? h.owner)}</span>` : ""}</li>`)
          .join("");
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
  query.onkeydown = (e) => e.key === "Enter" && (e.ctrlKey || e.metaKey) && go();
}

export function mountAsk(el, knownKeys) {
  el.innerHTML = `<div class="log" aria-live="polite"></div>
    <form><label for="ask-q">Ask about the product</label>
    <textarea id="ask-q" rows="3" placeholder="Which constraints apply to the drive motor, and where do they come from?"></textarea>
    <div class="row"><button type="submit" class="primary">Ask</button></div></form>`;
  const [log, form, input, send] = [".log", "form", "textarea", "button"].map((s) => el.querySelector(s));
  input.onkeydown = (e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), form.requestSubmit());
  form.onsubmit = async (e) => {
    e.preventDefault();
    const question = input.value.trim();
    if (!question || send.disabled) return;
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
          answer.innerHTML = linkCitations(texts.join("\n\n"), knownKeys);
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
