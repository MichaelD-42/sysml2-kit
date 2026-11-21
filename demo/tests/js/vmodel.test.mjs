import { test } from "node:test";
import assert from "node:assert/strict";
import { layoutV } from "../../static/js/layout.js";

const n = (key, level, side, extra = {}) => ({
  key, name: key, kind: "crs", level, side, compartments: { attributes: [], ports: [] }, ...extra,
});
const view = {
  kind: "vmodel",
  nodes: [n("CRS-1", 1, "left"), n("ATC-1", 1, "right"), n("SR-1", 2, "left"), n("STC-1", 2, "right"),
    n("F-1", 3, "left"), n("LC-1", 4, "left"), n("PC-1", 5, "bottom")],
  edges: [{ src: "SR-1", dst: "CRS-1", type: "SATISFIES" }, { src: "STC-1", dst: "SR-1", type: "VERIFIES" }],
  empty: [3, 4],
};

test("layoutV places levels top-down with the left leg left of the right leg", () => {
  const out = layoutV(view);
  const at = Object.fromEntries(out.nodes.map((x) => [x.key, x]));
  assert.ok(at["CRS-1"].y < at["SR-1"].y && at["SR-1"].y < at["F-1"].y && at["LC-1"].y < at["PC-1"].y);
  assert.ok(at["CRS-1"].x + at["CRS-1"].width < at["ATC-1"].x);
  assert.ok(at["SR-1"].x > at["CRS-1"].x, "the left leg steps inwards going down");
  const mid = out.width / 2;
  assert.ok(Math.abs(at["PC-1"].x + at["PC-1"].width / 2 - mid) < 1, "the bottom is centred");
});

test("layoutV draws edges between box borders and marks empty right levels", () => {
  const out = layoutV(view);
  assert.equal(out.edges.length, 2);
  for (const e of out.edges) assert.equal(e.points.length, 2);
  assert.deepEqual(out.bands.filter((b) => b.empty).map((b) => b.level), [3, 4]);
  assert.deepEqual(out.ports, []);
});

test("layoutV leaves out links that skip a level on the same leg and shows a result by its outcome", () => {
  const out = layoutV({
    ...view,
    nodes: [...view.nodes, n("R-1", 1, "right", { result: "passed", kind: "testresult" })],
    edges: [...view.edges, { src: "F-1", dst: "CRS-1", type: "MATCHES" }, { src: "R-1", dst: "ATC-1", type: "TESTS" }],
  });
  assert.ok(!out.edges.some((e) => e.src === "F-1"));
  assert.ok(out.edges.some((e) => e.src === "R-1"));
  assert.equal(out.nodes.find((x) => x.key === "R-1").header, "«result» passed");
});

test("layoutV tags a feature with the requirements it matches and never draws bottom links as across", () => {
  const out = layoutV({
    ...view,
    nodes: [...view.nodes, n("FEAT-1", 3, "left")],
    edges: [...view.edges, { src: "FEAT-1", dst: "CRS-1", type: "MATCHES" }, { src: "FEAT-1", dst: "CRS-1", type: "PARTIAL_MATCHES" },
      { src: "PC-1", dst: "SR-1", type: "SATISFIES" }],
  });
  assert.ok(out.nodes.find((x) => x.key === "FEAT-1").tags.includes("matches CRS-1 (partial)"));
  assert.ok(!out.edges.some((e) => e.src === "PC-1"));
  assert.ok(!out.edges.some((e) => e.type === "PARTIAL_MATCHES"));
});

test("layoutV puts a customer test requirement on the right leg with the test that implements it", () => {
  const out = layoutV({
    ...view,
    nodes: [...view.nodes, n("CTR-1", 1, "right", { kind: "ctr" })],
    edges: [...view.edges, { src: "STC-1", dst: "CTR-1", type: "IMPLEMENTS" }],
  });
  const ctr = out.nodes.find((x) => x.key === "CTR-1");
  assert.ok(ctr.x > out.width / 2 && ctr.y < out.nodes.find((x) => x.key === "STC-1").y);
  assert.ok(out.edges.some((e) => e.type === "IMPLEMENTS"));
});

test("layoutV tags a customer test requirement with the requirements it applies to instead of drawing the lines", () => {
  const out = layoutV({
    ...view,
    nodes: [...view.nodes, n("CTR-1", 1, "right", { kind: "ctr" })],
    edges: [...view.edges, { src: "CTR-1", dst: "CRS-1", type: "APPLIES_TO" }],
  });
  assert.ok(out.nodes.find((x) => x.key === "CTR-1").tags.includes("applies to CRS-1"));
  assert.ok(!out.edges.some((e) => e.type === "APPLIES_TO"));
});
