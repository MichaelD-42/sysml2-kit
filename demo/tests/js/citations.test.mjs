import { test } from "node:test";
import assert from "node:assert/strict";
import { linkCitations } from "../../static/js/panels.js";

test("linkCitations links known keys and marks unknown ones unresolved", () => {
  const html = linkCitations("see `PC-001` and `NOPE`", new Set(["PC-001"]));
  assert.match(html, /<a [^>]*data-key="PC-001"[^>]*>PC-001<\/a>/);
  assert.match(html, /<code class="unresolved"[^>]*>NOPE<\/code>/);
  assert.doesNotMatch(html, /`/);
});

test("linkCitations escapes HTML and leaves code that is not an id alone", () => {
  const html = linkCitations("<b> `peakTorque <= 310 [N*m]`", new Set());
  assert.match(html, /^&lt;b&gt; <code>peakTorque &lt;= 310 \[N\*m\]<\/code>$/);
});

test("linkCitations keeps fenced code blocks whole", () => {
  const html = linkCitations("run\n```cypher\nMATCH (n {key: 'PC-001'}) RETURN n\n```\ndone", new Set(["PC-001"]));
  assert.equal(html, "run\n<pre><code>MATCH (n {key: &#39;PC-001&#39;}) RETURN n\n</code></pre>\ndone");
});
