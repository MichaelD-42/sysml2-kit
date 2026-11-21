import { test } from "node:test";
import assert from "node:assert/strict";
import { instanceList } from "../../static/js/panels.js";

test("instanceList lists a link's instance pairs as focus links, with its rules", () => {
  const html = instanceList({
    src: "type:constraint", dst: "type:crs", type: "SATISFIES", count: 1, unused: false,
    rules: ["crs-satisfied"], instances: [["CON-101", "CRS-<1>"]],
  });
  assert.match(html, /<strong>constraint satisfies crs<\/strong>/);
  assert.match(html, /1 instance</);
  assert.match(html, /Rules: crs-satisfied/);
  assert.match(html, /data-key="CON-101"[^>]*>CON-101<\/a> → <a [^>]*data-key="CRS-&lt;1&gt;"/);
});

test("instanceList marks an unused link and lists a type's instances", () => {
  assert.match(instanceList({ src: "type:sysreq", dst: "type:prq", type: "SATISFIES", count: 0, unused: true, rules: [], instances: [] }),
    /0 instances, declared but unused/);
  const html = instanceList({ key: "type:crs", name: "Customer <req>", kind: "crs", count: 2, rules: ["crs-class"], instances: ["CRS-1", "CRS-2"] });
  assert.match(html, /Customer &lt;req&gt; «crs»/);
  assert.equal(html.match(/<li>/g).length, 2);
});
