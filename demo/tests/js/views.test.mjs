import { test } from "node:test";
import assert from "node:assert/strict";
import { viewsFor, offered, drillKind } from "../../static/js/render.js";

// element props as /api/element returns them for seat-switch ids
const usecase = { key: "UC-101", kind: "UseCaseUsage", layer: "R" };
const feature = { key: "FEAT-102", kind: "ActionUsage", layer: "F" };
const fn = { key: "SSW-F-001", kind: "ActionUsage", layer: "F" };
const logical = { key: "LC-101", kind: "PartUsage", layer: "L" };
const physical = { key: "PC-101", kind: "PartUsage", layer: "P" };
const swUnit = { key: "SSW-PC-035", kind: "PartUsage", layer: "P", domain: "SW" };
const connector = { key: "SSW-PC-022", kind: "PartUsage", layer: "P", domain: "EE" };
const pin = { key: "SSW-PI-007", kind: "PortUsage", layer: "P" };
const crs = { key: "CRS-301", layer: "R" };
const constraint = { key: "CON-101", kind: "ConstraintUsage", layer: "R" };
const ctr = { key: "CTR-003", layer: "V" };

test("viewsFor offers the views that apply to each element type", () => {
  assert.deepEqual(viewsFor(usecase), ["usecases", "trace"]);
  for (const n of [feature, fn]) assert.deepEqual(viewsFor(n), ["activity", "trace"], n.key);
  assert.deepEqual(viewsFor(logical), ["context", "boundary", "interfaces", "composition", "trace"]);
  for (const n of [physical, swUnit, connector])
    assert.deepEqual(viewsFor(n), ["boundary", "interfaces", "composition", "variants", "trace"], n.key);
  assert.deepEqual(viewsFor(pin), ["boundary", "interfaces", "trace"]);
  for (const n of [crs, constraint, ctr]) assert.deepEqual(viewsFor(n), ["trace", "vmodel"], n.key);
  assert.deepEqual(viewsFor({ key: "SeatSwitchPhysical", kind: "Package" }), ["trace"]);
});

test("offered adds compliance, the V-model and the meta-model, in tab order", () => {
  const order = ["context", "boundary", "interfaces", "activity", "composition", "variants", "usecases", "trace", "compliance", "vmodel", "metamodel"];
  assert.deepEqual(offered(usecase, order), ["usecases", "trace", "compliance", "vmodel", "metamodel"]);
  assert.deepEqual(offered(crs, order), ["trace", "compliance", "vmodel", "metamodel"]);
});

test("drillKind keeps an offered view and otherwise opens the element's first view", () => {
  assert.equal(drillKind(physical, "boundary"), "boundary");
  assert.equal(drillKind(physical, "context"), "boundary");
  assert.equal(drillKind(logical, "context"), "context");
  assert.equal(drillKind(feature, "composition"), "activity");
  assert.equal(drillKind(usecase, "trace"), "trace");
  assert.equal(drillKind(usecase, "context"), "usecases");
  assert.equal(drillKind(crs, "compliance"), "trace");
});
