import unittest

from explorer import db, load
from tests.support import RFQ


def count(graph, query="MATCH (n) RETURN count(n) AS c"):
    return graph.query(query)[0]["c"]


class WriteTest(unittest.TestCase):
    def setUp(self):
        self.graph = db.Graph()
        self.addCleanup(self.graph.close)

    def test_write_replaces_the_graph(self):
        graph = load.read_project(RFQ)
        for _ in range(2):  # the second write must not double it
            load.write(graph, self.graph)
            self.assertEqual(
                count(self.graph, "MATCH (n:Node) RETURN count(n) AS c"),
                len(graph.nodes),
            )
        self.assertEqual(
            count(self.graph, "MATCH (:Node)-[r]->(:Node) RETURN count(r) AS c"),
            len(graph.edges),
        )

    def test_write_leaves_other_data_alone(self):
        self.graph.query("CREATE (:NotOurs {tag: 'keep'})")
        load.write(load.read_project(RFQ), self.graph)
        self.assertEqual(count(self.graph, "MATCH (n:NotOurs) RETURN count(n) AS c"), 1)


if __name__ == "__main__":
    unittest.main()
