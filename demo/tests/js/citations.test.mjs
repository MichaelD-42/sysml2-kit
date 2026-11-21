import { test } from "node:test";
import assert from "node:assert/strict";
import { linkCitations } from "../../static/js/panels.js";

test("linkCitations links known keys and marks unknown ones unresolved", () => {
  // the brief's `NOPE` is not key-shaped under fix-round finding 1 (`SATISFIES` must not be marked); XX-999 is
  const html = linkCitations("see `PC-001` and `XX-999`", new Set(["PC-001"]));
  assert.match(html, /<a [^>]*data-key="PC-001"[^>]*>PC-001<\/a>/);
  assert.match(html, /<code class="unresolved"[^>]*>XX-999<\/code>/);
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

test("linkCitations marks only key-shaped unknown tokens unresolved", () => {
  assert.doesNotMatch(linkCitations("`peakTorque` via `SATISFIES` in `kW`", new Set()), /unresolved/);
  for (const k of ["XX-999", "EDU-PC-042", "0f561658-cb71-5ea1-8678-1a2ed8245dce", "testresult__system__x"])
    assert.match(linkCitations(`\`${k}\``, new Set()), /class="unresolved"/, k);
});

test("linkCitations labels a cited uid with its known name", () => {
  const uid = "9685cf06-3907-5bc0-a5cc-6899080f1420";
  const html = linkCitations(`\`${uid}\``, new Set([uid]), new Map([[uid, "accelerationTime <= 10 [s]"]]));
  assert.match(html, new RegExp(`data-key="${uid}"[^>]*>accelerationTime &lt;= 10 \\[s\\]</a>`));
});
