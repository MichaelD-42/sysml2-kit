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
  const lines = attributes.map((a) => (a.value == null || a.value === "" ? a.name : `${a.name} = ${a.value}${a.unit ? ` ${a.unit}` : ""}`));
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

const V_LEVELS = ["Customer requirements · acceptance", "System · system tests", "Features and functions", "Logical components", "Physical components"];

/** Where a straight line from rect a's centre towards rect b's centre leaves a. */
function border(a, b) {
  const cx = a.x + a.width / 2, cy = a.y + a.height / 2;
  const dx = b.x + b.width / 2 - cx, dy = b.y + b.height / 2 - cy;
  const t = Math.min(dx ? a.width / 2 / Math.abs(dx) : Infinity, dy ? a.height / 2 / Math.abs(dy) : Infinity);
  return { x: cx + dx * t, y: cy + dy * t };
}

/** V-model geometry: level bands top-down, the left leg stepping inwards, tests on the right, parts at the bottom. */
export function layoutV(view) {
  const GAP = 14, STEP = 70, PAD = 24, LEG = 560, BAND = 30;
  const metas = (view.nodes ?? []).map((n) => {
    const meta = describe(n, new Set(), false);
    // a test result shows its outcome, not its generated id
    if (n.result !== undefined) Object.assign(meta, { header: `«result» ${n.result ?? "no outcome"}`, outcome: n.result });
    const [width, height] = size(meta);
    return { ...meta, shape: "block", width, height, depth: 0 };
  });
  const rows = (items, maxWidth) => {
    // wrap items into rows no wider than maxWidth; returns [{items, width, height}]
    const out = [];
    for (const it of items) {
      const row = out.at(-1);
      if (row && row.width + GAP + it.width <= maxWidth) {
        row.items.push(it), (row.width += GAP + it.width), (row.height = Math.max(row.height, it.height));
      } else out.push({ items: [it], width: it.width, height: it.height });
    }
    return out;
  };
  const width = PAD * 2 + LEG * 2 + STEP * 2;
  const bands = [];
  let y = PAD;
  for (let level = 1; level <= 5; level++) {
    const top = y;
    y += BAND;
    const indent = (level - 1) * STEP;
    let bottom = y;
    if (level === 5) {
      for (const row of rows(metas.filter((m) => m.level === 5), width - PAD * 2)) {
        let x = (width - row.width) / 2;
        for (const it of row.items) Object.assign(it, { x, y }), (x += it.width + GAP);
        y += row.height + GAP;
      }
      bottom = y;
    } else {
      for (const [side, x0] of [["left", PAD + indent], ["right", null]]) {
        let yy = y;
        for (const row of rows(metas.filter((m) => m.level === level && m.side === side), LEG - indent)) {
          let x = side === "left" ? x0 : width - PAD - indent - row.width;
          for (const it of row.items) Object.assign(it, { x, y: yy }), (x += it.width + GAP);
          yy += row.height + GAP;
        }
        bottom = Math.max(bottom, yy);
      }
    }
    const empty = level < 5 && (view.empty ?? []).includes(level);
    bands.push({ level, title: V_LEVELS[level - 1], y: top, height: Math.max(bottom, y + 40) - top, indent, empty });
    y = Math.max(bottom, y + 40) + GAP;
  }
  const at = new Map(metas.map((m) => [m.key, m]));
  // only links between neighbouring levels and across the V; longer jumps are in the trace view
  const near = (a, b) => Math.abs(a.level - b.level) <= 1 || a.side !== b.side;
  const edges = (view.edges ?? [])
    .filter((e) => at.has(e.src) && at.has(e.dst) && near(at.get(e.src), at.get(e.dst)))
    .map((e, i) => {
      const a = at.get(e.src), b = at.get(e.dst);
      return { ...e, key: `e${i}`, points: [border(a, b), border(b, a)], label: null };
    });
  return { width, height: y + PAD, nodes: metas, ports: [], edges, bands, leg: LEG };
}
