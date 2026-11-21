// View JSON <-> ELK graph. Both directions are pure; main.js runs ELK in between.

const DOWN = new Set(["composition", "variants"]);
const PORT_VIEWS = new Set(["boundary", "interfaces", "composition"]);
const NEED_LINKS = new Set(["SATISFIES", "ALLOCATED_TO", "VERIFIES", "REALIZES", "MATCHES", "PARTIAL_MATCHES", "ANSWERS", "TESTS", "REQUIRES"]);
const PORT = 10;

export const textWidth = (s, px = 12) => String(s ?? "").length * px * 0.6;

/** SysML-style keyword for a node kind: ActionUsage -> action, PartDefinition -> part def. */
export function keyword(kind) {
  if (!kind || /^[a-z]/.test(kind)) return kind ?? ""; // need types (crs, acctest) are already words
  return kind
    .replace(/Usage$/, "")
    .replace(/Definition$/, " def")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .toLowerCase();
}

function describe(node, actors, compound) {
  const shape = compound
    ? "frame"
    : actors.has(node.key)
      ? "actor"
      : node.kind === "UseCaseUsage"
        ? "usecase"
        : node.kind === "ActionUsage"
          ? "action"
          : "block";
  const { attributes = [], ports = [] } = node.compartments ?? {};
  const lines = attributes.map((a) => (a.value == null ? a.name : `${a.name} = ${a.value}${a.unit ? ` ${a.unit}` : ""}`));
  if (node.kind === "InterfaceDefinition") lines.push(...ports.map((p) => `end ${p.name}`));
  const tags = [];
  if (node.platform) tags.push("platform");
  if (node.reuse) tags.push(`reuse: ${node.reuse}`);
  if (node.selected === true && node.variant) tags.push("selected");
  if (node.selected === false) tags.push("not selected");
  if (node.lane) tags.push(`allocated to ${node.lane.name}`);
  const id = node.shortName ?? (/^[0-9a-f]{8}-/.test(node.key) ? null : node.key);
  const header = [`«${keyword(node.kind)}»`, id, node.domain].filter(Boolean).join(" ");
  return { ...node, shape, header, lines, tags };
}

function size(meta) {
  if (meta.shape === "actor") return [Math.max(48, textWidth(meta.name) + 10), 74];
  if (meta.shape === "usecase") return [Math.max(textWidth(meta.name, 13), textWidth(meta.header, 11)) + 60, 58];
  const width = Math.max(110, textWidth(meta.header, 11) + 24, textWidth(meta.name, 13) + 24,
    ...[...meta.lines, ...meta.tags].map((l) => textWidth(l, 11) + 24));
  const body = meta.lines.length * 15 + meta.tags.length * 14;
  return [width, 42 + body + (body ? 8 : 0)];
}

const elkPort = (key, name, domain) => ({
  id: key,
  meta: { domain },
  width: PORT,
  height: PORT,
  labels: name ? [{ text: name, width: textWidth(name, 10), height: 12 }] : [],
});

/** ELK graph for a view: nested children from `parent`, ports as ELK ports, edges. */
export function toElk(view) {
  const nodes = view.nodes ?? [];
  const byKey = new Map(nodes.map((n) => [n.key, n]));
  const isPort = (n) => n.kind === "PortUsage" && byKey.has(n.parent) && byKey.get(n.parent).kind !== "PortUsage";
  const actors = new Set((view.edges ?? []).filter((e) => e.type === "ACTOR").map((e) => e.src));
  const parentOf = (n) => (byKey.has(n.parent) && n.parent !== n.key && !isPort(byKey.get(n.parent)) ? n.parent : null);
  const hasChildren = new Set(nodes.filter((n) => !isPort(n)).map(parentOf).filter(Boolean));

  const used = new Set();
  const portsOf = new Map(nodes.map((n) => [n.key, []]));
  const addPort = (owner, key, name, domain) => {
    // shortcut: a port shared by two parts (typed by one definition) is drawn on the first only
    if (used.has(key)) return;
    used.add(key);
    portsOf.get(owner).push(elkPort(key, name, domain));
  };
  for (const n of nodes) if (isPort(n)) addPort(n.parent, n.key, n.name, n.domain);
  for (const n of nodes) {
    if (!PORT_VIEWS.has(view.kind) || isPort(n) || n.kind === "InterfaceDefinition") continue;
    for (const p of n.compartments?.ports ?? []) if (!byKey.has(p.key)) addPort(n.key, p.key, p.name);
  }

  const elk = new Map();
  for (const n of nodes) {
    if (isPort(n)) continue;
    const compound = hasChildren.has(n.key);
    const meta = describe(n, actors, compound);
    const item = { id: n.key, meta, ports: portsOf.get(n.key), layoutOptions: {} };
    if (compound) {
      item.layoutOptions["elk.padding"] = "[top=48,left=18,bottom=18,right=18]";
      item.layoutOptions["elk.portLabels.placement"] = "INSIDE";
      item.layoutOptions["elk.nodeSize.constraints"] = "PORTS PORT_LABELS MINIMUM_SIZE";
      item.layoutOptions["elk.nodeSize.minimum"] = `(${size(meta)[0]}, 60)`;
    } else {
      [item.width, item.height] = size(meta);
      if (item.ports.length) item.layoutOptions["elk.nodeSize.constraints"] = "PORTS MINIMUM_SIZE";
      item.layoutOptions["elk.nodeSize.minimum"] = `(${item.width}, ${item.height})`;
    }
    elk.set(n.key, item);
  }
  const root = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": DOWN.has(view.kind) ? "DOWN" : "RIGHT",
      "elk.hierarchyHandling": "INCLUDE_CHILDREN",
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.portLabels.placement": "OUTSIDE",
      "elk.spacing.nodeNode": "28",
      "elk.layered.spacing.nodeNodeBetweenLayers": "56",
      "elk.spacing.edgeLabel": "4",
      "elk.padding": "[top=16,left=16,bottom=16,right=16]",
    },
    children: [],
  };
  for (const n of nodes) {
    if (isPort(n)) continue;
    const parent = parentOf(n);
    const into = parent ? elk.get(parent) : root;
    (into.children ??= []).push(elk.get(n.key));
  }
  const ids = new Set([...elk.keys(), ...used]);
  root.edges = (view.edges ?? [])
    .filter((e) => ids.has(e.src) && ids.has(e.dst))
    .map((e, i) => {
      const text = e.label ?? (NEED_LINKS.has(e.type) ? e.type.toLowerCase().replace("_", " ") : null);
      return {
        id: `e${i}`,
        sources: [e.src],
        targets: [e.dst],
        meta: e,
        labels: text ? [{ text, width: textWidth(text, 10), height: 12 }] : [],
      };
    });
  return root;
}

/** Flat positioned shapes in absolute coordinates from a laid-out ELK graph. */
export function fromElk(laid) {
  const out = { width: laid.width, height: laid.height, nodes: [], ports: [], edges: [] };
  const origin = new Map([[laid.id, { x: 0, y: 0 }]]);
  const edges = [];
  const walk = (parent, ox, oy, depth) => {
    for (const e of parent.edges ?? []) edges.push(e);
    for (const c of parent.children ?? []) {
      const x = ox + c.x;
      const y = oy + c.y;
      origin.set(c.id, { x, y });
      out.nodes.push({ ...c.meta, key: c.id, x, y, width: c.width, height: c.height, depth });
      for (const p of c.ports ?? []) {
        const label = p.labels?.[0];
        out.ports.push({
          ...p.meta,
          key: p.id,
          owner: c.id,
          name: label?.text,
          x: x + p.x,
          y: y + p.y,
          width: p.width,
          height: p.height,
          label: label && { x: x + p.x + label.x, y: y + p.y + label.y, width: label.width, height: label.height },
        });
      }
      walk(c, x, y, depth + 1);
    }
  };
  walk(laid, 0, 0, 0);
  for (const e of edges) {
    // ELK gives edge coordinates relative to the edge's container
    const o = origin.get(e.container) ?? { x: 0, y: 0 };
    const at = (p) => ({ x: o.x + p.x, y: o.y + p.y });
    const s = e.sections?.[0];
    const label = e.labels?.[0];
    out.edges.push({
      ...e.meta,
      key: e.id,
      points: s ? [s.startPoint, ...(s.bendPoints ?? []), s.endPoint].map(at) : [],
      label: label?.x !== undefined ? { text: label.text, ...at(label), width: label.width, height: label.height } : null,
    });
  }
  return out;
}
