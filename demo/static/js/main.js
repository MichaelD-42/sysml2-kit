// Wires the page: one focus element, the views that apply to it laid out by ELK, and the side panels.
import * as api from "./api.js";
import { focus, setFocus, breadcrumb, history } from "./state.js";
import { toElk, fromElk, layoutV, keyword } from "./layout.js";
import { svg, esc, drillKind, offered, viewsFor } from "./render.js";
import * as panels from "./panels.js";

const KINDS = {
  context: "System context",
  boundary: "System boundary",
  interfaces: "Interfaces",
  activity: "Activity",
  composition: "Composition",
  variants: "Variants",
  usecases: "Use cases",
  trace: "Traceability",
  compliance: "Compliance",
  vmodel: "V-model",
  metamodel: "Meta-model",
};
const $ = (s) => document.querySelector(s);
const elk = new globalThis.ELK();
const names = new Map(); // key -> display name
const parents = new Map(); // key -> owner key
const knownKeys = new Set();
const current = { kind: "context", keys: new Set(), view: null };
let token = 0;
let scale = 1;

const related = new Map(); // key -> keys linked to it through a requirement or a platform use (both directions)
const reqLinks = new Map(); // requirement key -> its links [{rel, key, name}]
const TREES = ["#req-tree", "#rflp-tree", "#plat-tree"];

async function loadModel() {
  const [roots, reqs, rflp, platform, keys] = await Promise.all([
    api.tree(), api.tree("requirements"), api.tree("rflp"), api.tree("platform"), api.keys(),
  ]);
  names.clear(), parents.clear(), knownKeys.clear();
  keys.forEach((k) => knownKeys.add(k));
  const walk = (n, parent) => {
    names.set(n.key, n.name);
    if (parent) parents.set(n.key, parent);
    n.children.forEach((c) => walk(c, n.key));
  };
  roots.forEach((r) => walk(r, null));
  related.clear(), reqLinks.clear();
  const link = (a, b) => (related.has(a) || related.set(a, new Set()), related.get(a).add(b));
  for (const g of reqs)
    for (const r of g.children) {
      reqLinks.set(r.key, r.links);
      for (const l of r.links) link(r.key, l.key), link(l.key, r.key);
    }
  // a project element and the platform element it uses mark each other
  panels.usesLinks([...rflp, ...platform], link);
  const named = (n) => (n.key && !names.has(n.key) && names.set(n.key, n.name), (n.children ?? []).forEach(named));
  [...reqs, ...rflp, ...platform, ...[...reqLinks.values()].flat()].forEach(named);
  panels.renderTree($("#req-tree"), reqs);
  panels.renderTree($("#rflp-tree"), rflp);
  panels.renderTree($("#plat-tree"), platform);
}

// the focus in every tree, plus what it is linked to through a requirement or a platform use
function revealTrees(key) {
  for (const id of TREES) panels.revealInTree($(id), key, related.get(key) ?? new Set());
}

// unnamed elements (a requirement's constraint) are labelled by their expression
async function label(nodes) {
  await Promise.all(
    nodes
      .filter((n) => n.name === n.key && /^[0-9a-f]{8}-/.test(n.key))
      .map(async (n) => {
        n.name = await panels.nameOf(n.key, names); // stays the uid if the fetch fails
      }),
  );
}

// the tabs for `kinds` (all views until there is a focus)
function renderTabs(kinds = Object.keys(KINDS)) {
  $("#kinds").innerHTML = kinds
    .map((k) => `<button type="button" role="tab" id="tab-${k}" aria-controls="canvas" data-kind="${k}">${esc(KINDS[k])}</button>`)
    .join("");
  markTab(current.kind);
}

function tabs() {
  const nav = $("#kinds");
  renderTabs();
  nav.onclick = (e) => {
    const b = e.target.closest("[data-kind]");
    if (b) show(b.dataset.kind, focus.get());
  };
  nav.onkeydown = (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (!step) return;
    const all = [...nav.children];
    const next = all[(all.indexOf(document.activeElement) + step + all.length) % all.length];
    next.focus();
    next.click();
  };
}

function markTab(kind) {
  for (const b of $("#kinds").children) {
    const on = b.dataset.kind === kind;
    b.setAttribute("aria-selected", on);
    b.tabIndex = on ? 0 : -1;
  }
}

async function show(kind, key) {
  const mine = ++token;
  current.kind = kind;
  markTab(kind);
  const canvas = $("#canvas");
  canvas.setAttribute("aria-busy", "true");
  const note = $("#note");
  try {
    let view = await api.view(kind, kind === "compliance" || kind === "metamodel" ? null : key);
    let why = "";
    if (view.reason && key) {
      // the focus has no such view: show the default one and say why
      const { node } = await api.element(key).catch(() => ({ node: {} }));
      const fitting = viewsFor(node).find((k) => k !== kind) ?? kind;
      const name = await panels.nameOf(key, names);
      const reason = view.reason.startsWith(key) ? name + view.reason.slice(key.length) : view.reason;
      why = `${esc(reason)}; showing the default ${esc(KINDS[kind].toLowerCase())}.
        ${fitting !== kind ? `<button type="button" data-open="${fitting}" data-with="focus">${esc(KINDS[fitting])} of ${esc(name)}</button>` : ""}`;
      view = await api.view(kind, null);
    }
    if (mine !== token) return;
    note.innerHTML = why;
    if (view.unused_links?.length) note.textContent = `Declared links with no instance: ${view.unused_links.join(", ")}`;
    await label(view.nodes);
    if (mine !== token) return;
    current.view = view;
    current.keys = new Set(view.nodes.flatMap((n) => [n.key, ...(n.compartments?.ports ?? []).map((p) => p.key)]));
    view.nodes.forEach((n) => names.has(n.key) || names.set(n.key, n.name));
    if (kind === "compliance") {
      panels.renderCompliance(canvas, view, focus.get());
    } else if (view.reason) {
      canvas.innerHTML = `<div class="empty"><p>${esc(view.reason)}.</p></div>`;
    } else {
      const laid = kind === "vmodel" ? layoutV(view) : fromElk(await elk.layout(toElk(view)));
      if (mine !== token) return;
      current.laid = laid;
      canvas.innerHTML = svg(laid, focus.get());
      fit(laid.width < canvas.clientWidth ? 1 : Math.max(0.8, canvas.clientWidth / laid.width));
    }
    if (!focus.get() && view.focus) setFocus(view.focus);
  } catch (e) {
    if (mine === token) canvas.innerHTML = `<div class="empty"><p class="error">${esc(e.message)}</p></div>`;
  } finally {
    if (mine === token) canvas.removeAttribute("aria-busy");
  }
}

function fit(s) {
  scale = s;
  const el = $("#canvas svg");
  if (el) el.style.width = `${current.laid.width * scale}px`, (el.style.height = `${current.laid.height * scale}px`);
}

function highlight(key) {
  for (const el of document.querySelectorAll("#canvas .focus")) el.classList.remove("focus");
  for (const el of document.querySelectorAll("#canvas [data-key], #canvas [data-row]"))
    if ((el.dataset.key ?? el.dataset.row) === key && !el.matches("a")) el.classList.add("focus");
}

// the inspector and breadcrumb for an element from /api/element; a requirement lists its links,
// any other element the requirements linked to it
function inspect(key, found) {
  const crumbs = $("#breadcrumb");
  const info = $("#inspector");
  try {
    if (found.error) throw found.error;
    const { node, edges } = found;
    const owner = edges.find((e) => e.type === "OWNS" && e.direction === "in");
    if (owner && !parents.has(key)) parents.set(key, owner.other), names.set(owner.other, owner.name ?? owner.other);
    const name = (node.kind === "UseCaseUsage" && node.title) || (node.name ?? node.title ?? node.expression ?? key);
    names.set(key, name);
    const links = reqLinks.get(key) ?? [...(related.get(key) ?? [])].filter((k) => reqLinks.has(k)).map((k) => ({ rel: "requirements", key: k, name: names.get(k) ?? k }));
    crumbs.innerHTML = breadcrumb(key, parents)
      .map((k) => (k === key ? `<span aria-current="true">${esc(name)}</span>` : panels.keyLink(k, names.get(k) ?? k)))
      .join('<span class="sep" aria-hidden="true">/</span>');
    const value = node.value !== undefined ? `${node.value}${node.unit ? ` ${node.unit}` : ""}` : null;
    // a need from a document has no metaclass, so no keyword
    info.innerHTML = `<strong>${esc(name)}</strong> ${node.kind ? `<span class="kind">«${esc(keyword(node.kind))}»</span>` : ""}
      ${node.shortName || !/^[0-9a-f]{8}-/.test(key) ? `<span class="id">${esc(node.shortName ?? key)}</span>` : ""}
      ${node.domain ? `<span class="domain d-${esc(node.domain)}">${esc(node.domain)}</span>` : ""}
      ${value ? `<span>= ${esc(value)}</span>` : ""}${node.expression ? `<span>${esc(node.expression)}</span>` : ""}
      ${node.doc || node.content ? `<p>${esc(node.doc ?? node.content)}</p>` : ""}${panels.linkList(links)}`;
  } catch (e) {
    info.innerHTML = `<p class="error">${esc(e.message)}</p>`;
  }
}

async function onFocus(key) {
  $("#back").disabled = !history.length;
  revealTrees(key);
  const found = await api.element(key).catch((error) => ({ error }));
  if (focus.get() !== key) return;
  inspect(key, found);
  // only the views that apply to the element; a view it was picked in stays offered
  const node = found.node ?? {};
  const inView = current.keys.has(key);
  const kinds = offered(node, Object.keys(KINDS));
  renderTabs(Object.keys(KINDS).filter((k) => kinds.includes(k) || (inView && k === current.kind)));
  // in the V a customer requirement (level 1, left leg) narrows the view to its chain
  const crs = current.kind === "vmodel" && current.view?.nodes.some((n) => n.key === key && n.level === 1 && n.side === "left");
  if (crs && key !== current.view.focus) show(current.kind, key);
  else if (current.kind === "compliance" || current.kind === "metamodel" || inView) highlight(key);
  else show(kinds.includes(current.kind) ? current.kind : drillKind(node, current.kind), key);
}

// a meta-model type or link lists its instances in the inspector; its boxes are not elements
function pick(el) {
  const item = el.dataset.edge
    ? current.laid.edges.find((x) => x.key === el.dataset.edge)
    : current.view.nodes.find((x) => x.key === el.dataset.key);
  if (item) $("#inspector").innerHTML = panels.instanceList(item);
}

function wire() {
  // every key link and diagram element moves the focus
  document.addEventListener("click", (e) => {
    const meta = current.kind === "metamodel" && e.target.closest("#canvas [data-key], #canvas [data-edge]");
    if (meta) return e.preventDefault(), pick(meta);
    const el = e.target.closest("[data-key]");
    if (el) e.preventDefault(), setFocus(el.dataset.key);
    const open = e.target.closest("[data-open]");
    if (open) show(open.dataset.open, open.dataset.with ? focus.get() : null);
  });
  const canvas = $("#canvas");
  const drill = (el) => {
    if (current.kind === "metamodel") return;
    const n = current.view.nodes.find((x) => x.key === el.dataset.key) ?? { kind: "PortUsage" };
    const kind = drillKind(n, current.kind);
    setFocus(el.dataset.key);
    show(kind, el.dataset.key);
  };
  canvas.addEventListener("dblclick", (e) => {
    const el = e.target.closest("g[data-key]");
    if (el) drill(el);
  });
  canvas.addEventListener("keydown", (e) => {
    const el = e.target.closest("g[data-key], g[data-edge]");
    if (!el || e.key !== "Enter") return;
    if (current.kind === "metamodel") return pick(el);
    e.shiftKey ? drill(el) : setFocus(el.dataset.key);
  });
  $("#back").onclick = () => focus.back();
  $("#zoom-in").onclick = () => fit(scale * 1.25);
  $("#zoom-out").onclick = () => fit(scale / 1.25);
  $("#zoom-fit").onclick = () => {
    const c = $("#canvas");
    if (current.laid) fit(Math.min(c.clientWidth / current.laid.width, c.clientHeight / current.laid.height));
  };
  $("#reload").onclick = async (e) => {
    const status = $("#reload-status");
    e.target.disabled = true;
    status.textContent = "rebuilding the model";
    try {
      const { nodes, edges } = await api.reload();
      status.textContent = `loaded ${nodes} nodes, ${edges} edges`;
      await loadModel();
      if (focus.get()) revealTrees(focus.get());
      await show(current.kind, focus.get());
    } catch (err) {
      status.textContent = "";
      console.error(`reload failed: ${err.message}`);
    } finally {
      e.target.disabled = false;
    }
  };
  $("#theme").onclick = () => {
    const root = document.documentElement;
    const now = root.dataset.theme ?? (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    root.dataset.theme = now === "light" ? "dark" : "light";
    try {
      localStorage.setItem("theme", document.documentElement.dataset.theme);
    } catch {}
  };
  const side = $("#side-tabs");
  side.onclick = (e) => {
    const b = e.target.closest("[data-panel]");
    if (!b) return;
    for (const t of side.children) t.setAttribute("aria-selected", t === b);
    for (const p of document.querySelectorAll(".side-panel")) p.hidden = p.id !== b.dataset.panel;
  };
}

tabs();
wire();
focus.subscribe(onFocus);
await loadModel();
panels.mountSearch($("#search"), names);
panels.mountAsk($("#ask"), knownKeys, names);
await show("context", null);
