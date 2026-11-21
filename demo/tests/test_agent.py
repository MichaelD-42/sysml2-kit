import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from explorer import agent, server
from tests import support
from tests.support import vehicle

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"
BUILT_IN = {"Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"}


class ToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = vehicle()

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()

    def test_element(self):
        self.assertEqual(
            json.loads(agent.element(self.graph, "PC-001"))["node"]["key"], "PC-001"
        )
        self.assertIn("error", json.loads(agent.element(self.graph, "NOPE-1")))

    def test_cypher_is_a_stub(self):
        # read-only Cypher on Relate comes with Task 2; until then every query is an error
        for q in ("CREATE (n) RETURN n", "RETURN 1 AS one"):
            self.assertIn("error", json.loads(agent.cypher(self.graph, q)))

    def test_semantic_search(self):
        hits = json.loads(agent.semantic_search(self.graph, support._embedder, "motor"))
        self.assertIsInstance(hits, list)
        self.assertTrue(hits)


def deny_or_allow(options, name):
    result = asyncio.run(options.can_use_tool(name, {}, None))
    return result.behavior


class OptionsTest(unittest.TestCase):
    def setUp(self):
        self.options = agent.options(VEHICLE, None, None)

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
        project = Path(sysml["args"][sysml["args"].index("--project") + 1])
        # the vehicle's own model and the platform's, through the platform symlink
        self.assertTrue((project / "vehicle" / "model").is_dir())
        self.assertTrue((project / "edrive-platform" / "model").is_dir())
        self.assertIn("read-only", self.options.system_prompt)


class ModelRootTest(unittest.TestCase):
    def tree(self, platform_at):
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        project, platform = tmp / "a" / "vehicle", tmp / platform_at
        (project / "model").mkdir(parents=True)
        (platform / "model").mkdir(parents=True)
        (project / "platform").symlink_to(platform)
        return project

    def test_sibling_platform_uses_parent(self):
        project = self.tree("a/edrive")
        self.assertEqual(agent.model_root(project), project.parent)

    def test_distant_platform_falls_back_to_model(self):
        project = self.tree("b/c/edrive")
        self.assertEqual(agent.model_root(project), project / "model")


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
        app = server.create_app(graph, None, VEHICLE, agent_factory=fake)
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
