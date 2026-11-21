import { test } from "node:test";
import assert from "node:assert/strict";
import { renderTree } from "../../static/js/panels.js";

test("renderTree escapes names, relations and groups, and hides generated ids", () => {
  const el = {};
  renderTree(el, [{
    key: null, name: "<b>Group</b>", kind: "group",
    children: [{ key: "CRS-1", name: "<img src=x onerror=alert(1)>", kind: "crs", children: [
      { key: "SR-1", name: "range", kind: "RequirementUsage", rel: "satisfied <by>", children: [] },
      { key: "testresult__a__b_x1", name: "run", kind: null, rel: "result", children: [] },
    ] }],
  }]);
  assert.ok(!el.innerHTML.includes("<img"));
  assert.ok(!el.innerHTML.includes("<b>"));
  assert.ok(el.innerHTML.includes("satisfied &lt;by&gt;"));
  assert.ok(!el.innerHTML.includes('class="id">testresult__'));
  assert.ok(el.innerHTML.includes('class="id">SR-1'));
});
