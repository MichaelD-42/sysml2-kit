import unittest
from pathlib import Path

from explorer import cypher
from tests.support import driver_or_skip, load_project

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"


class CypherTest(unittest.TestCase):
    def setUp(self):
        self.driver = driver_or_skip(self)

    def count_x(self):
        return self.driver.execute_query("MATCH (n:X) RETURN count(n) AS c")[0][0]["c"]

    def test_writes_are_rejected(self):
        # the read-access transaction refuses each write; LOAD CSV is not covered here
        for q in (
            "CREATE (n:X) RETURN n",
            "MERGE (n:X) RETURN n",
            "MATCH (n) DETACH DELETE n",
            "MATCH (n:Node) SET n.x = 1 RETURN count(n)",
        ):
            with self.subTest(q=q), self.assertRaises(cypher.CypherError):
                cypher.run_read(self.driver, q)
        self.assertEqual(self.count_x(), 0)
        self.assertGreater(
            self.driver.execute_query("MATCH (n) RETURN count(n) AS c")[0][0]["c"], 0
        )

    def test_truncates(self):
        r = cypher.run_read(self.driver, "UNWIND range(1, 600) AS i RETURN i")
        self.assertEqual((len(r["rows"]), r["truncated"]), (500, True))
        r = cypher.run_read(self.driver, "UNWIND range(1, 3) AS i RETURN i")
        self.assertEqual((r["columns"], r["truncated"]), (["i"], False))

    def test_serialises_nodes_and_relationships(self):
        r = cypher.run_read(
            self.driver,
            "MATCH (a:Node)-[r:OWNS]->(b:Node) RETURN a, r, b LIMIT 1",
        )
        a, rel, b = r["rows"][0]
        self.assertEqual(set(a), {"key", "name", "kind"})
        self.assertEqual(rel, {"type": "OWNS", "src": a["key"], "dst": b["key"]})

    def test_examples_run(self):
        load_project(self.driver, VEHICLE)
        for ex in cypher.EXAMPLES:
            with self.subTest(ex["title"]):
                r = cypher.run_read(self.driver, ex["query"], ex.get("params"))
                self.assertTrue(r["rows"])


if __name__ == "__main__":
    unittest.main()
