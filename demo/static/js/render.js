// SVG for a positioned view (from layout.fromElk). Nodes and ports carry data-key; main.js
// delegates click (focus) and double-click (drill down) from the canvas.

export const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const STRUCTURE = new Set(["composition", "boundary", "interfaces"]);

/** The view a double-click on `node` drills into from view `current`. */
export function drillKind(node, current) {
  if (node.kind === "ActionUsage") return "activity";
  if (node.kind === "UseCaseUsage") return "usecases";
  if (/Part|Port|Reference/.test(node.kind)) return STRUCTURE.has(current) ? current : "composition";
  return "trace";
}

const MARKERS = `<defs>
  <marker id="m-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk-fill"/></marker>
  <marker id="m-open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" class="mk-line"/></marker>
  <marker id="m-hollow" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" orient="auto-start-reverse"><path d="M0,0 L12,6 L0,12 z" class="mk-hollow"/></marker>
  <marker id="m-diamond" viewBox="0 0 14 8" refX="1" refY="4" markerWidth="13" markerHeight="8" orient="auto-start-reverse"><path d="M0,4 L7,0 L14,4 L7,8 z" class="mk-fill"/></marker>
</defs>`;

function edgeMarkers(type) {
  if (type === "FLOW") return 'marker-end="url(#m-arrow)"';
  if (type === "SUCCESSION") return 'marker-end="url(#m-open)"';
  if (type === "SPECIALIZES") return 'marker-end="url(#m-hollow)"';
  if (type === "OWNS") return 'marker-start="url(#m-diamond)"';
  if (type === "CONNECTS" || type === "ACTOR") return "";
  return 'marker-end="url(#m-open)"'; // need links
}

const domainClass = (d) => (d ? ` d-${esc(d)}` : "");

function text(x, y, s, cls, anchor = "start") {
  return `<text x="${x}" y="${y}" class="${cls}" text-anchor="${anchor}">${esc(s)}</text>`;
}

function body(n, top) {
  const out = [];
  let y = top;
  if (n.lines.length || n.tags.length) {
    out.push(`<line x1="${n.x}" x2="${n.x + n.width}" y1="${y}" y2="${y}" class="divider"/>`);
    y += 4;
  }
  for (const l of n.lines) out.push(text(n.x + 10, (y += 15) - 3, l, "t-attr"));
  for (const l of n.tags) out.push(text(n.x + 10, (y += 14) - 3, l, "t-tag"));
  return out.join("");
}

function shape(n) {
  const cx = n.x + n.width / 2;
  if (n.shape === "actor") {
    const y = n.y + 4;
    return `<g class="actor"><circle cx="${cx}" cy="${y + 8}" r="8"/>
      <path d="M${cx},${y + 16} v20 M${cx - 13},${y + 23} h26 M${cx},${y + 36} l-11,15 M${cx},${y + 36} l11,15"/></g>
      ${text(cx, n.y + n.height - 4, n.name, "t-name", "middle")}`;
  }
  if (n.shape === "usecase") {
    return `<ellipse cx="${cx}" cy="${n.y + n.height / 2}" rx="${n.width / 2}" ry="${n.height / 2}" class="box"/>
      ${text(cx, n.y + n.height / 2 - 4, n.header, "t-kw", "middle")}
      ${text(cx, n.y + n.height / 2 + 12, n.name, "t-name", "middle")}`;
  }
  const rx = n.shape === "action" ? 12 : 2;
  const frame = n.shape === "frame";
  return `<rect x="${n.x}" y="${n.y}" width="${n.width}" height="${n.height}" rx="${rx}" class="box${frame ? " frame" : ""}"/>
    ${frame ? `<path d="M${n.x},${n.y + 40} h${Math.min(n.width, Math.max(n.header.length, n.name.length) * 7.5 + 20)} l10,-10 v-30" class="tab"/>` : ""}
    ${text(n.x + 10, n.y + 16, n.header, "t-kw")}
    ${text(n.x + 10, n.y + 33, n.name, "t-name")}
    ${frame ? "" : body(n, n.y + 42)}`;
}

function node(n, focus) {
  const cls = `n s-${n.shape}${domainClass(n.domain)}${n.key === focus ? " focus" : ""}${n.selected === false ? " unselected" : ""}`;
  return `<g class="${cls}" data-key="${esc(n.key)}" tabindex="0" role="button" aria-label="${esc(`${n.header} ${n.name}`)}"><title>${esc(n.name)} (Enter: focus, Shift+Enter: drill down)</title>${shape(n)}</g>`;
}

function port(p, domain, focus) {
  const label = p.label
    ? text(p.label.x, p.label.y + p.label.height - 2, p.name, "t-port")
    : "";
  return `<g class="p${domainClass(domain)}${p.key === focus ? " focus" : ""}" data-key="${esc(p.key)}" tabindex="0" role="button" aria-label="port ${esc(p.name)}">
    <rect x="${p.x}" y="${p.y}" width="${p.width}" height="${p.height}" class="port"/>${label}</g>`;
}

function edge(e, domain) {
  if (e.points.length < 2) return "";
  const d = e.points.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" ");
  const label = e.label ? text(e.label.x, e.label.y + e.label.height - 2, e.label.text, "t-edge") : "";
  return `<g class="e e-${esc(e.type)}${domainClass(domain)}"><path d="${d}" ${edgeMarkers(e.type)}/>${label}</g>`;
}

// a V-model level: its title, and a dashed slot where the right leg has no tests at this level
function band(b, view) {
  const slot = b.empty
    ? `<rect x="${view.width - 24 - b.indent - 220}" y="${b.y + 30}" width="220" height="40" class="slot"/>
       ${text(view.width - 24 - b.indent - 110, b.y + 55, "no tests at this level", "t-tag", "middle")}`
    : "";
  return `<g class="band"><line x1="0" x2="${view.width}" y1="${b.y}" y2="${b.y}" class="band-rule"/>
    ${text(24 + b.indent, b.y + 18, b.title, "t-band")}${slot}</g>`;
}

/** SVG markup for a positioned view; the focus element is highlighted. */
export function svg(view, focus) {
  const domains = new Map(view.nodes.map((n) => [n.key, n.domain]));
  for (const p of view.ports) domains.set(p.key, p.domain ?? domains.get(p.owner));
  const nodes = [...view.nodes].sort((a, b) => a.depth - b.depth);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${view.width} ${view.height}" width="${view.width}" height="${view.height}" role="img" aria-label="diagram">
    ${MARKERS}
    ${(view.bands ?? []).map((b) => band(b, view)).join("")}
    ${nodes.map((n) => node(n, focus)).join("")}
    ${view.edges.map((e) => edge(e, domains.get(e.src) ?? domains.get(e.dst))).join("")}
    ${view.ports.map((p) => port(p, domains.get(p.key), focus)).join("")}
  </svg>`;
}
