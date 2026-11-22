import { test } from "node:test";
import assert from "node:assert/strict";
import { viewsFor, drillKind, MENU } from "../../static/js/render.js";
import { usesLinks } from "../../static/js/panels.js";

// element props as /api/element returns them for window-switch ids
const usecase = { key: "UC-101", kind: "UseCaseUsage", layer: "R" };
const feature = { key: "FEAT-102", kind: "ActionUsage", layer: "F" };
const fn = { key: "WSW-F-001", kind: "ActionUsage", layer: "F" };
const logical = { key: "LC-101", kind: "PartUsage", layer: "L" };
const physical = { key: "PC-101", kind: "PartUsage", layer: "P" };
const swUnit = { key: "WSW-PC-021", kind: "PartUsage", layer: "P", domain: "SW" };
const connector = { key: "WSW-PC-015", kind: "PartUsage", layer: "P", domain: "EE" };
const pin = { key: "WSW-PI-005", kind: "PortUsage", layer: "P" };
const crs = { key: "CRS-301", layer: "R", class: "non-functional" };
const sysreq = { key: "SR-101", kind: "RequirementUsage", layer: "R" };
const constraint = { key: "CON-101", kind: "ConstraintUsage", layer: "R" };
const ctr = { key: "CTR-003", layer: "V" };

test("viewsFor gives each element type its own views and the scoped big-picture ones", () => {
  assert.deepEqual(viewsFor(usecase), { own: ["usecases"], context: ["vmodel"] });
  for (const n of [feature, fn]) assert.deepEqual(viewsFor(n), { own: ["trace"], context: ["interfaces"] }, n.key);
  assert.deepEqual(viewsFor(logical), { own: ["context", "composition", "allocation"], context: ["interfaces", "vmodel"] });
  for (const n of [physical, swUnit, connector])
    assert.deepEqual(viewsFor(n), { own: ["composition", "variants"], context: ["interfaces", "vmodel"] }, n.key);
  assert.deepEqual(viewsFor(pin), { own: ["interfaces"], context: [] });
  assert.deepEqual(viewsFor(crs), { own: ["trace"], context: ["vmodel", "compliance"] });
  for (const n of [constraint, ctr, sysreq]) assert.deepEqual(viewsFor(n), { own: ["trace"], context: ["vmodel"] }, n.key);
  assert.deepEqual(viewsFor({ key: "WindowSwitchPhysical", kind: "Package" }), { own: ["trace"], context: [] });
});

test("the model-wide views are the menu, not element tabs", () => {
  assert.deepEqual(MENU, ["product", "compliance", "vmodel", "metamodel"]);
});

test("drillKind keeps a view the element has and otherwise opens its first own view", () => {
  assert.equal(drillKind(physical, "interfaces"), "interfaces");
  assert.equal(drillKind(physical, "context"), "composition");
  assert.equal(drillKind(logical, "context"), "context");
  assert.equal(drillKind(feature, "composition"), "trace");
  assert.equal(drillKind(feature, "interfaces"), "interfaces");
  assert.equal(drillKind(usecase, "context"), "usecases");
  assert.equal(drillKind(crs, "product"), "trace");
});

test("usesLinks links project and platform elements both ways", () => {
  const seen = [];
  usesLinks([{ key: "PC-101", uses: ["WSW-PC-004"], children: [{ key: "x", children: [] }] }], (a, b) => seen.push([a, b]));
  assert.deepEqual(seen, [["PC-101", "WSW-PC-004"], ["WSW-PC-004", "PC-101"]]);
});
