// Side panels: hierarchy tree, search, ask, and the compliance table.
// Every key is rendered as <a data-key>; main.js turns a click on one into setFocus.
import * as api from "./api.js";
import { esc } from "./render.js";

// what the agent cites: need ids (PC-101, SSW-PC-002), uids, test result ids
const KEY_SHAPED = /^[A-Z]+(-[A-Z]+)*-\d+$|^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$|^testresult__\S+$/;
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
    const marks = `${n.again ? ' <span class="kind">expanded above</span>' : ""}${n.domain ? ` <span class="domain d-${esc(n.domain)}">${esc(n.domain)}</span>` : ""}${n.class ? ` <span class="req-class">${esc(n.class)}</span>` : ""}${n.platform ? ' <span class="kind">platform</span>' : ""}`;
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
  // a collapsed section opens for the focus itself, not for what is linked to it
  const section = el.closest("details");
  if (hits.length && section) section.open = true;
  for (const k of linked) {
    const li = rows.find((x) => x.dataset.tree === k && !x.parentElement.closest(`li[data-tree="${CSS.escape(key)}"]`));
    if (li) li.classList.add("linked"), openUp(li);
  }
  hits[0]?.scrollIntoView({ block: "nearest" });
}

/** Keep each collapsible tree section's open state per viewer. */
export function rememberSections(sections) {
  for (const d of sections) {
    const key = `section:${d.dataset.section}`;
    try {
      if (localStorage.getItem(key) === "closed") d.open = false;
    } catch {}
    d.addEventListener("toggle", () => {
      try {
        localStorage.setItem(key, d.open ? "open" : "closed");
      } catch {}
    });
  }
}

export function mountSearch(el, names) {
  el.innerHTML = `<label for="q">Search elements and needs</label>
    <input id="q" type="search" autocomplete="off" placeholder="PC-101, housing, actuation force">
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

export function mountAsk(el, knownKeys, names) {
  el.innerHTML = `<div class="log" aria-live="polite"></div>
    <form><label for="ask-q">Ask about the product</label>
    <textarea id="ask-q" rows="3" placeholder="Which constraints apply to the driver switch's housing and where do they come from?"></textarea>
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
  const ctrs = view.ctrs ?? [];
  const links = (ks) => ks.map((k) => keyLink(k)).join(", ");
  const statements = (ss) => (ss ?? []).map(([k, v]) => `${keyLink(k)} ${esc(v)}`).join(", ");
  const row = (key) => `<tr data-row="${esc(key)}"${key === focus ? ' class="focus"' : ""}>`;
  el.innerHTML = `<table class="compliance"><caption>Compliance of the RFQ's customer requirements</caption>
    <thead><tr><th scope="col">CRS</th><th scope="col">Title</th><th scope="col">Class</th><th scope="col">Features</th><th scope="col">Reuse</th>
    <th scope="col">Partial</th><th scope="col">Statements</th><th scope="col">Domains</th></tr></thead>
    <tbody>${rows.map((r) => `${row(r.crs)}
      <td>${keyLink(r.crs)}</td><td>${esc(r.title)}</td><td>${esc(r.class)}</td><td>${links(r.features ?? [])}</td><td>${esc(r.reuse)}</td>
      <td>${r.partial ? "partial" : "full"}</td><td>${statements(r.statements)}</td>
      <td>${(r.domains ?? []).map((d) => `<span class="domain d-${esc(d)}">${esc(d)}</span>`).join(" ")}</td></tr>`).join("")}
    </tbody></table>
    ${ctrs.length ? `<table class="compliance"><caption>Customer test requirements and the tests that implement them</caption>
    <thead><tr><th scope="col">CTR</th><th scope="col">Title</th><th scope="col">Purpose</th><th scope="col">Method</th>
    <th scope="col">Implemented by</th><th scope="col">Statements</th></tr></thead>
    <tbody>${ctrs.map((r) => `${row(r.ctr)}
      <td>${keyLink(r.ctr)}</td><td>${esc(r.title)}</td><td>${esc(r.purpose)}</td><td>${esc(r.method)}</td>
      <td>${links(r.implemented_by ?? [])}</td><td>${statements(r.statements)}</td></tr>`).join("")}
    </tbody></table>` : ""}
    ${view.findings?.length ? `<h3>Findings</h3><ul class="findings">${view.findings.map((f) => `<li>${esc(typeof f === "string" ? f : JSON.stringify(f))}</li>`).join("")}</ul>` : ""}`;
}

/** Calls link(a, b) and link(b, a) for every node in RFLP trees and each element in its `uses`. */
export function usesLinks(roots, link) {
  const walk = (n) => ((n.uses ?? []).forEach((k) => (link(n.key, k), link(k, n.key))), n.children.forEach(walk));
  roots.forEach(walk);
}

/** Inspector HTML for links [{rel, key, name}]: one line per relation, each key a focus link. */
export function linkList(links) {
  const byRel = new Map();
  for (const l of links) byRel.set(l.rel, [...(byRel.get(l.rel) ?? []), keyLink(l.key, l.name)]);
  return [...byRel].map(([rel, ks]) => `<p class="links"><span class="rel">${esc(rel)}</span> ${ks.join(", ")}</p>`).join("");
}

/** Inspector HTML for a meta-model need type or link: its count, the rules on it, its instances. */
export function instanceList(item) {
  const type = (k) => k.replace(/^type:/, "");
  const title = item.src ? `${type(item.src)} ${item.type.toLowerCase()} ${type(item.dst)}` : `${item.name} «${item.kind}»`;
  const count = `${item.count} instance${item.count === 1 ? "" : "s"}${item.unused ? ", declared but unused" : ""}`;
  const rows = (item.instances ?? []).map((x) => `<li>${Array.isArray(x) ? `${keyLink(x[0])} → ${keyLink(x[1])}` : keyLink(x)}</li>`);
  return `<strong>${esc(title)}</strong> <span>${esc(count)}</span>
    ${item.rules?.length ? `<p>Rules: ${esc(item.rules.join(", "))}</p>` : ""}
    ${rows.length ? `<ul class="instances">${rows.join("")}</ul>` : ""}`;
}
