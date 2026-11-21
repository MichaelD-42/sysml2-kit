import unittest

from explorer import cypher
from tests.support import vehicle


class CypherTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = vehicle()

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()

    def test_run_read_is_a_stub(self):
        # read-only Cypher on Relate comes with Task 2; until then every query is an error
        with self.assertRaises(cypher.CypherError):
            cypher.run_read(self.graph, "RETURN 1 AS one")

    def test_examples_run(self):
        for ex in cypher.EXAMPLES:
            with self.subTest(ex["title"]):
                self.assertTrue(
                    self.graph.query(ex["query"], **(ex.get("params") or {}))
                )


if __name__ == "__main__":
    unittest.main()
