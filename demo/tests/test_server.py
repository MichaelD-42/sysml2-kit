import shutil
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from explorer import server
from tests import support
from tests.support import RFQ, rfq

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def client(app):
    return TestClient(app, base_url="http://127.0.0.1")


def node_count(graph):
    return graph.query("MATCH (n) RETURN count(n) AS c")[0]["c"]


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.graph = rfq()
        self.addCleanup(self.graph.close)
        self.client = client(server.create_app(self.graph, support._embedder, RFQ))

    def test_view_errors(self):
        self.assertEqual(
            self.client.get("/api/view/trace?focus=NOPE-1").status_code, 404
        )
        self.assertEqual(self.client.get("/api/view/nope").status_code, 400)

    def test_element(self):
        r = self.client.get("/api/element/PC-101")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json()["node"]["qualifiedName"],
            "SeatSwitchRfqPhysical::vehicleSeatSwitches::driverSwitch::driverHousing",
        )
        self.assertEqual(self.client.get("/api/element/NOPE-1").status_code, 404)

    def test_tree_search_keys_compliance(self):
        self.assertTrue(self.client.get("/api/tree").json())
        reqs = self.client.get("/api/tree?kind=requirements").json()
        self.assertIn("Customer requirements", [g["name"] for g in reqs])
        # each tree is rooted at its product
        self.assertEqual(
            self.client.get("/api/tree?kind=rflp").json()[0]["key"], "LC-100"
        )
        self.assertEqual(
            self.client.get("/api/tree?kind=platform").json()[0]["key"], "SSW-LC-001"
        )
        self.assertEqual(self.client.get("/api/tree?kind=nope").status_code, 400)
        self.assertTrue(self.client.get("/api/view/vmodel").json()["nodes"])
        hits = self.client.get("/api/search?q=driver housing&k=3").json()
        self.assertTrue(hits)
        self.assertIn("PC-101", self.client.get("/api/keys").json())
        compliance = self.client.get("/api/view/compliance").json()
        self.assertTrue(compliance["rows"])
        self.assertTrue(compliance["ctrs"])

    def test_search_k_is_validated(self):
        self.assertEqual(self.client.get("/api/search?q=housing&k=0").status_code, 422)
        self.assertEqual(self.client.get("/api/search?q=housing&k=51").status_code, 422)

    def test_foreign_host_rejected(self):
        r = self.client.get("/api/keys", headers={"Host": "attacker.example"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.get("/api/keys").status_code, 200)
        self.assertEqual(
            self.client.get(
                "/api/keys", headers={"Host": "localhost:8000"}
            ).status_code,
            200,
        )

    def test_posts_need_json(self):
        for path, body in (
            ("/api/reload", "{}"),
            ("/api/ask", '{"question": "hi"}'),
        ):
            with self.subTest(path=path):
                r = self.client.post(
                    path, content=body, headers={"Content-Type": "text/plain"}
                )
                self.assertEqual(r.status_code, 415)

    def test_no_cypher_endpoint(self):
        self.assertEqual(self.client.get("/api/cypher").status_code, 404)
        self.assertEqual(self.client.get("/api/cypher/examples").status_code, 404)
        # the static mount takes every path that is not a route and allows only GET and HEAD
        r = self.client.post("/api/cypher", json={"query": "RETURN 1 AS one"})
        self.assertEqual(r.status_code, 405)

    def copy_projects(self, tmp):
        ignore = shutil.ignore_patterns("build", "_build", "_generated")
        for name in ("seat-switch-rfq", "seat-switch-platform"):
            shutil.copytree(
                EXAMPLES / name, Path(tmp) / name, symlinks=True, ignore=ignore
            )
        return Path(tmp) / "seat-switch-rfq"

    def test_reload_failure_keeps_graph(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_projects(tmp)
            next(project.glob("model/**/*.sysml")).write_text("package { broken ;;")
            before = node_count(self.graph)
            c = client(server.create_app(self.graph, support._embedder, project))
            r = c.post("/api/reload", json={})
            self.assertEqual(r.status_code, 422)
            self.assertTrue(r.json()["error"])
            self.assertEqual(node_count(self.graph), before)

    def test_reload_success(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_projects(tmp)
            before = node_count(self.graph)
            c = client(server.create_app(self.graph, support._embedder, project))
            r = c.post("/api/reload", json={})
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(node_count(self.graph), before)
            self.assertEqual(r.json()["nodes"], before)

    def test_reload_load_failure_is_500(self):
        before = node_count(self.graph)
        c = client(server.create_app(self.graph, support._embedder, RFQ))
        with (
            mock.patch.object(server.subprocess, "run") as run,
            mock.patch.object(
                server.load, "load", side_effect=OSError("no needs.json")
            ),
        ):
            run.return_value.returncode = 0
            r = c.post("/api/reload", json={})
        self.assertEqual((r.status_code, r.json()), (500, {"error": "no needs.json"}))
        self.assertEqual(node_count(self.graph), before)

    def test_concurrent_reload_rejected(self):
        app = server.create_app(self.graph, support._embedder, RFQ)
        c = client(app)
        app.state.reload_lock.acquire()
        try:
            self.assertEqual(c.post("/api/reload", json={}).status_code, 409)
        finally:
            app.state.reload_lock.release()


if __name__ == "__main__":
    unittest.main()
