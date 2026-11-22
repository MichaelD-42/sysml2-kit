import asyncio
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from explorer import agent, server
from tests import support
from tests.support import RFQ, rfq

BUILT_IN = {"Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"}


class ToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = rfq()

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()

    def test_element(self):
        self.assertEqual(
            json.loads(agent.element(self.graph, "PC-101"))["node"]["key"], "PC-101"
        )
        self.assertIn("error", json.loads(agent.element(self.graph, "NOPE-1")))

    def test_cypher(self):
        self.assertIn(
            "error", json.loads(agent.cypher(self.graph, "CREATE (n) RETURN n"))
        )
        self.assertIn("error", json.loads(agent.cypher(self.graph, "NOT CYPHER")))
        result = json.loads(agent.cypher(self.graph, "RETURN 1 AS one"))
        self.assertEqual(result["rows"], [[1]])

    def test_prompt_queries_run(self):
        # the prompt's Cypher guidance must stay valid against the graph it describes
        blocks = re.findall(r"```cypher\n(.*?)```", agent.PROMPT.read_text(), re.DOTALL)
        self.assertGreaterEqual(len(blocks), 6)
        for query in blocks:
            with self.subTest(query):
                query = query.replace("$key", "'PC-101'")
                self.assertTrue(self.graph.read_only(query, None, 100, 10)["rows"])

    def test_semantic_search(self):
        hits = json.loads(
            agent.semantic_search(self.graph, support._embedder, "housing")
        )
        self.assertIsInstance(hits, list)
        self.assertTrue(hits)


def deny_or_allow(options, name):
    result = asyncio.run(options.can_use_tool(name, {}, None))
    return result.behavior


class OptionsTest(unittest.TestCase):
    def setUp(self):
        self.options = agent.options(RFQ, None, None)

    def test_permissions(self):
        self.assertEqual(deny_or_allow(self.options, "Bash"), "deny")
        self.assertEqual(deny_or_allow(self.options, "mcp__kit__cypher"), "allow")
        self.assertEqual(deny_or_allow(self.options, "mcp__sysml__find"), "allow")
        for name in ("mcp__sysml__generate_rust", "mcp__sysml__import_rust"):
            self.assertEqual(deny_or_allow(self.options, name), "deny")
        self.assertFalse(BUILT_IN & set(self.options.allowed_tools))
        self.assertTrue(
            all(
                t.startswith(("mcp__kit__", "mcp__sysml__"))
                for t in self.options.allowed_tools
            )
        )
        self.assertEqual(self.options.max_turns, 12)

    def test_servers(self):
        self.assertEqual(set(self.options.mcp_servers), {"kit", "sysml"})
        sysml = self.options.mcp_servers["sysml"]
        args = sysml["args"]
        roots = [Path(args[i + 1]).name for i, a in enumerate(args) if a == "--project"]
        # the RFQ's own model and the platform's, which sits beside it
        self.assertEqual(roots, ["window-switch-rfq", "window-switch-platform"])
        self.assertIn("read-only", self.options.system_prompt)


class ModelRootTest(unittest.TestCase):
    def tree(self, platform_at):
        """A project in tmp/a/rfq whose Makefile names the platform at tmp/<platform_at>."""
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        project, platform = tmp / "a" / "rfq", tmp / platform_at
        (project / "model").mkdir(parents=True)
        (platform / "model").mkdir(parents=True)
        relative = os.path.relpath(platform, project)
        (project / "Makefile").write_text(f"PLATFORM := {relative}\n")
        return project

    def test_a_platform_anywhere_is_a_second_root(self):
        for at in ("a/platform", "a/rfq/platform", "b/c/platform"):
            with self.subTest(at=at):
                project = self.tree(at)
                self.assertEqual(
                    agent.model_roots(project),
                    [project, (project / ".." / ".." / at).resolve()],
                )

    def test_without_a_platform_only_the_project(self):
        project = self.tree("a/platform")
        (project / "Makefile").write_text("PLATFORM := nowhere\n")
        self.assertEqual(agent.model_roots(project), [project])


class FailingClient:
    def __init__(self, options):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, question):
        pass

    async def receive_response(self):
        raise RuntimeError("boom")
        yield


class NoResultClient(FailingClient):
    async def receive_response(self):
        return
        yield


class FakeGraph:
    def __init__(self, error=None):
        self.error = error

    def query(self, cypher, **params):
        if self.error:
            raise self.error
        return [{"1": 1}]


async def collect(stream):
    return [e async for e in stream]


class AskTest(unittest.TestCase):
    def test_exception_is_one_error_event(self):
        events = asyncio.run(collect(agent.ask(None, "q", client=FailingClient)))
        self.assertEqual(events, [{"type": "error", "message": "boom"}])

    def test_stream_without_result_is_an_error(self):
        events = asyncio.run(collect(agent.ask(None, "q", client=NoResultClient)))
        self.assertEqual([e["type"] for e in events], ["error"])

    def post(self, graph, fake):
        app = server.create_app(graph, None, RFQ, agent_factory=fake)
        r = TestClient(app, base_url="http://127.0.0.1").post(
            "/api/ask", json={"question": "hi"}
        )
        self.assertEqual(r.headers["content-type"].split(";")[0], "text/event-stream")
        return [
            json.loads(line[5:])
            for line in r.text.splitlines()
            if line.startswith("data:")
        ]

    def test_endpoint_without_graph_is_one_error(self):
        async def fake(question):
            raise AssertionError("agent must not start")
            yield

        data = self.post(FakeGraph(OSError("database closed")), fake)
        self.assertEqual(data, [{"type": "error", "message": "database closed"}])

    def test_endpoint_streams_events(self):
        async def fake(question):
            yield {"type": "text", "text": question}
            yield {"type": "done"}

        data = self.post(FakeGraph(), fake)
        self.assertEqual(data, [{"type": "text", "text": "hi"}, {"type": "done"}])


if __name__ == "__main__":
    unittest.main()
