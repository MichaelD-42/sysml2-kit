import { test } from "node:test";
import assert from "node:assert/strict";
import { renderCompliance, renderTree, linkList } from "../../static/js/panels.js";

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

test("renderTree shows a requirement's class", () => {
  const el = {};
  renderTree(el, [{ key: "CRS-1", name: "force", kind: "crs", class: "non-functional", children: [] }]);
  assert.match(el.innerHTML, /<span class="req-class">non-functional<\/span>/);
});

test("renderCompliance shows classes and a table of customer test requirements", () => {
  const el = {};
  renderCompliance(el, {
    rows: [{ crs: "CRS-1", title: "force", class: "non-functional", features: [], reuse: "platform", statements: [], domains: [] }],
    ctrs: [{ ctr: "CTR-1", title: "haptics", purpose: "verification", method: "test", implemented_by: ["STC-1"], statements: [["CST-1", "partial"]] }],
  });
  assert.match(el.innerHTML, /<td>non-functional<\/td>/);
  assert.match(el.innerHTML, /<tr data-row="CTR-1">/);
  assert.match(el.innerHTML, /data-key="STC-1"/);
  assert.match(el.innerHTML, /data-key="CST-1"[^>]*>CST-1<\/a> partial/);
});

test("linkList puts one relation per line and escapes it", () => {
  const html = linkList([
    { rel: "satisfied <by>", key: "SR-119", name: "range" },
    { rel: "satisfied <by>", key: "CON-104", name: "a < b" },
    { rel: "test requirement", key: "CTR-002", name: "haptics" },
  ]);
  assert.equal(html.match(/<p class="links">/g).length, 2);
  assert.match(html, /satisfied &lt;by&gt;<\/span> <a [^>]*data-key="SR-119"[^>]*>range<\/a>, <a [^>]*data-key="CON-104"[^>]*>a &lt; b<\/a>/);
  assert.equal(linkList([]), "");
});
