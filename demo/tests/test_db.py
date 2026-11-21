import threading
import unittest

from explorer import db


class GraphTest(unittest.TestCase):
    def setUp(self):
        self.graph = db.Graph()
        self.addCleanup(self.graph.close)

    def count(self):
        return self.graph.query("MATCH (n) RETURN count(n) AS c")[0]["c"]

    def test_query_returns_rows_as_dicts(self):
        self.assertEqual(self.graph.query("RETURN 1 AS x"), [{"x": 1}])

    def test_query_from_another_thread(self):
        rows = []
        t = threading.Thread(
            target=lambda: rows.append(self.graph.query("RETURN $v AS v", v=2))
        )
        t.start()
        t.join()
        self.assertEqual(rows, [[{"v": 2}]])

    def test_failed_write_rolls_back(self):
        def statements(run):
            run("CREATE (:X)", {})
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            self.graph.write(statements)
        self.assertEqual(self.count(), 0)

    def test_write_commits(self):
        self.graph.write(
            lambda run: run("UNWIND $xs AS x CREATE (:X {x: x})", {"xs": [1, 2]})
        )
        self.assertEqual(self.count(), 2)

    def test_close_twice(self):
        self.graph.close()
        self.graph.close()


class ReadOnlyTest(unittest.TestCase):
    def setUp(self):
        self.graph = db.Graph()
        self.addCleanup(self.graph.close)
        self.graph.query(
            "CREATE (:Node {key: 'a', name: 'A', embedding: [0.5]})"
            "-[:OWNS {n: 1}]->(:Node {key: 'b'})"
        )

    def read(self, cypher, limit=500):
        return self.graph.read_only(cypher, None, limit, 10)

    def state(self):
        nodes = self.graph.query("MATCH (n) RETURN count(n) AS c")[0]["c"]
        return nodes, self.graph.query("SHOW INDEXES")

    def test_writes_are_rejected(self):
        before = self.state()
        for q in (
            "CREATE (n:X) RETURN n",
            "MERGE (n:X) RETURN n",
            "MATCH (n:Node) SET n.x = 1",
            "MATCH (n:Node) DETACH DELETE n",
            "CREATE INDEX i FOR (n:X) ON (n.y)",
            "CALL db.createLabel('Z')",
        ):
            with self.subTest(q), self.assertRaises(db.ReadOnlyError):
                self.read(q)
        self.assertEqual(self.state(), before)

    def test_rows_are_truncated_at_the_limit(self):
        result = self.read("UNWIND range(1, 600) AS i RETURN i")
        self.assertEqual(result["columns"], ["i"])
        self.assertEqual(len(result["rows"]), 500)
        self.assertEqual(result["rows"][0], [1])
        self.assertTrue(result["truncated"])
        self.assertFalse(self.read("RETURN 1 AS one")["truncated"])

    def test_values_are_plain_json(self):
        result = self.read(
            "MATCH (a)-[r]->(b) RETURN a, r, [b] AS bs, {r: r} AS m, b.key AS k"
        )
        a, r, bs, m, k = result["rows"][0]
        self.assertEqual(a, {"key": "a", "name": "A"})
        self.assertEqual(r, {"type": "OWNS", "src": "a", "dst": "b"})
        self.assertEqual(bs, [{"key": "b"}])
        self.assertEqual(m, {"r": r})
        self.assertEqual(k, "b")


if __name__ == "__main__":
    unittest.main()
