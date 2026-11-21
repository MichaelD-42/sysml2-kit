import unittest
from pathlib import Path

from explorer import db, load

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"


def count(graph, query="MATCH (n) RETURN count(n) AS c"):
    return graph.query(query)[0]["c"]


class WriteTest(unittest.TestCase):
    def setUp(self):
        self.graph = db.Graph()
        self.addCleanup(self.graph.close)

    def test_write_replaces_the_graph(self):
        graph = load.read_project(VEHICLE)
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
        load.write(load.read_project(VEHICLE), self.graph)
        self.assertEqual(count(self.graph, "MATCH (n:NotOurs) RETURN count(n) AS c"), 1)


if __name__ == "__main__":
    unittest.main()
