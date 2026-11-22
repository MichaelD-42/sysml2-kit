import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { toElk, fromElk } from "../../static/js/layout.js";

const node = (key, kind, parent = null, extra = {}) => ({
  key, name: key, kind, parent, compartments: { attributes: [], ports: [] }, ...extra,
});

test("toElk nests a port under its part", () => {
  const g = toElk({
    kind: "boundary",
    nodes: [node("P", "PartUsage"), node("q", "PortUsage", "P")],
    edges: [],
  });
  assert.deepEqual(g.children.map((c) => c.id), ["P"]);
  assert.deepEqual(g.children[0].ports.map((p) => p.id), ["q"]);
  assert.equal(g.children[0].children, undefined);
});

test("toElk turns compartment ports into ELK ports, once per key", () => {
  const ports = [{ key: "q", name: "hvIn" }];
  const g = toElk({
    kind: "composition",
    nodes: [
      node("P", "PartUsage", null, { compartments: { attributes: [], ports } }),
      node("R", "PartUsage", null, { compartments: { attributes: [], ports } }),
    ],
    edges: [],
  });
  assert.deepEqual(g.children[0].ports.map((p) => p.id), ["q"]);
  assert.deepEqual(g.children[1].ports, []);
});

test("toElk nests an action under its frame and drops edges with unknown ends", () => {
  const g = toElk({
    kind: "activity",
    nodes: [node("F", "ActionUsage"), node("a", "ActionUsage", "F"), node("b", "ActionUsage", "F")],
    edges: [
      { src: "a", dst: "b", type: "SUCCESSION", label: null },
      { src: "a", dst: "gone", type: "FLOW", label: null },
    ],
  });
  assert.deepEqual(g.children.map((c) => c.id), ["F"]);
  assert.deepEqual(g.children[0].children.map((c) => c.id), ["a", "b"]);
  assert.deepEqual(g.edges.map((e) => [e.sources[0], e.targets[0]]), [["a", "b"]]);
});

test("fromElk keeps keys and makes nested coordinates absolute", () => {
  const laid = {
    id: "root", x: 0, y: 0, width: 300, height: 200,
    children: [{
      id: "F", x: 10, y: 20, width: 200, height: 100, meta: { name: "frame" },
      ports: [{ id: "p", x: 195, y: 40, width: 10, height: 10 }],
      children: [{ id: "a", x: 30, y: 40, width: 50, height: 20, meta: { name: "a" } }],
    }],
    edges: [{
      id: "e0", container: "F", meta: { type: "FLOW" },
      sections: [{ startPoint: { x: 80, y: 50 }, endPoint: { x: 195, y: 45 } }],
    }],
  };
  const out = fromElk(laid);
  assert.deepEqual(out.nodes.map((n) => [n.key, n.x, n.y, n.name]), [["F", 10, 20, "frame"], ["a", 40, 60, "a"]]);
  assert.deepEqual(out.ports.map((p) => [p.key, p.owner, p.x, p.y]), [["p", "F", 205, 60]]);
  assert.deepEqual(out.edges[0].points, [{ x: 90, y: 70 }, { x: 205, y: 65 }]);
  assert.equal(out.edges[0].type, "FLOW");
});

test("ELK lays out a toElk graph and fromElk returns every key", async () => {
  const ELK = createRequire(import.meta.url)("../../static/vendor/elk.bundled.js");
  const view = {
    kind: "boundary",
    nodes: [
      node("U", "PartUsage"), node("u1", "PortUsage", "U"),
      node("M", "PartUsage", "U", { compartments: { attributes: [{ name: "mass", value: 46, unit: "kg" }], ports: [] } }),
      node("m1", "PortUsage", "M"), node("B", "PartUsage"), node("b1", "PortUsage", "B"),
    ],
    edges: [
      { src: "m1", dst: "u1", type: "CONNECTS", label: "Coolant" },
      { src: "b1", dst: "u1", type: "FLOW", label: null },
    ],
  };
  const out = fromElk(await new ELK().layout(toElk(view)));
  assert.deepEqual(out.nodes.map((n) => n.key).sort(), ["B", "M", "U"]);
  assert.deepEqual(out.ports.map((p) => p.key).sort(), ["b1", "m1", "u1"]);
  assert.equal(out.edges.length, 2);
  const m = out.nodes.find((n) => n.key === "M"), u = out.nodes.find((n) => n.key === "U");
  assert.ok(m.x > u.x && m.x + m.width < u.x + u.width, "the child sits inside its frame");
  for (const e of out.edges) assert.ok(e.points.length >= 2);
});

test("toElk shows an attribute without a value as its name only", () => {
  const g = toElk({
    kind: "trace",
    nodes: [node("R", "RequirementUsage", null, { compartments: { attributes: [{ name: "t", value: "", unit: null }, { name: "u", value: null, unit: null }], ports: [] } })],
    edges: [],
  });
  assert.deepEqual(g.children[0].meta.lines, ["t", "u"]);
});

test("toElk frames meta-model layers in RFLP order and boxes types without an id", () => {
  const g = toElk({
    kind: "metamodel",
    nodes: [
      { key: "layer:V", name: "V · Verification", kind: "layer", parent: null, count: 1 },
      { key: "layer:R", name: "R · Requirements", kind: "layer", parent: null, count: 1 },
      { key: "type:crs", name: "Customer requirement", kind: "crs", parent: "layer:R", count: 1, rules: ["crs-class"] },
      { key: "type:ctr", name: "Customer test requirement", kind: "ctr", parent: "layer:V", count: 1, rules: [] },
    ],
    edges: [],
  });
  assert.equal(g.layoutOptions["elk.partitioning.activate"], "true");
  assert.deepEqual(g.children.map((c) => [c.id, c.layoutOptions["elk.partitioning.partition"], c.meta.shape]),
    [["layer:V", "4", "frame"], ["layer:R", "0", "frame"]]);
  const crs = g.children[1].children[0].meta;
  assert.equal(crs.header, "«crs»");
  assert.deepEqual(crs.tags, ["1 instance", "rule crs-class"]);
});

test("toElk says how many of a meta-model type's instances are platform", () => {
  const g = toElk({
    kind: "metamodel",
    nodes: [{ key: "type:sysreq", name: "System requirement", kind: "sysreq", parent: null, count: 25, platform: 21, rules: [] }],
    edges: [],
  });
  assert.deepEqual(g.children[0].meta.tags, ["25 instances (21 platform)"]);
});
