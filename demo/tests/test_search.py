import unittest

from explorer.search import Embedder, neighbourhood, search
from tests.support import vehicle


class SearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = vehicle()
        cls.embedder = Embedder()

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()

    def keys(self, q, k=10):
        return [h["key"] for h in search(self.graph, self.embedder, q, k)]

    def test_exact_key_comes_first(self):
        for key in ("PC-001", "EDU-PC-003"):
            self.assertEqual(self.keys(key)[0], key)

    def test_natural_query_finds_the_limit(self):
        hits = search(self.graph, self.embedder, "what limits motor torque", 5)
        self.assertIn("peakTorqueLimit", [h["name"] for h in hits])
        self.assertEqual(
            set(hits[0]),
            {"key", "name", "kind", "shortName", "owner", "score", "snippet"},
        )

    def test_lucene_syntax_does_not_raise(self):
        self.assertIsInstance(self.keys("torque AND ("), list)

    def test_neighbourhood(self):
        n = neighbourhood(self.graph, "PC-001")
        self.assertEqual(n["node"]["key"], "PC-001")
        self.assertTrue(n["edges"])
        self.assertNotIn("embedding", n["node"])


if __name__ == "__main__":
    unittest.main()
