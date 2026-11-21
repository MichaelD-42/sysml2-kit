import { test } from "node:test";
import assert from "node:assert/strict";
import { createFocus, breadcrumb } from "../../static/js/state.js";

test("setFocus notifies subscribers once per change and not for the same key", () => {
  const focus = createFocus();
  const seen = [];
  focus.subscribe((key) => seen.push(key));
  focus.setFocus("PC-001");
  focus.setFocus("PC-001");
  focus.setFocus("LC-001");
  assert.deepEqual(seen, ["PC-001", "LC-001"]);
  assert.equal(focus.get(), "LC-001");
});

test("back returns to the previous focus", () => {
  const focus = createFocus();
  focus.setFocus("A");
  focus.setFocus("B");
  focus.back();
  assert.equal(focus.get(), "A");
  focus.back();
  assert.equal(focus.get(), "A");
});

test("breadcrumb walks the owner path from the root down", () => {
  const parents = new Map([["motor", "driveUnit"], ["driveUnit", "vehicle"], ["vehicle", "Pkg"]]);
  assert.deepEqual(breadcrumb("motor", parents), ["Pkg", "vehicle", "driveUnit", "motor"]);
  assert.deepEqual(breadcrumb("CRS-001", parents), ["CRS-001"]);
});
