import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSSE } from "../../static/js/api.js";

test("parseSSE returns whole events and keeps the partial rest", () => {
  const { events, rest } = parseSSE('data: {"type":"text","text":"a"}\n\ndata: {"type":"done"}\n\ndata: {"ty');
  assert.deepEqual(events, [{ type: "text", text: "a" }, { type: "done" }]);
  assert.equal(rest, 'data: {"ty');
});
