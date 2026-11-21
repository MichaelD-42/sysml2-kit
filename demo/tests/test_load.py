import unittest
from pathlib import Path

from explorer import load
from tests.support import driver_or_skip

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"


def count(driver, query="MATCH (n) RETURN count(n) AS c"):
    return driver.execute_query(query)[0][0]["c"]


class WriteTest(unittest.TestCase):
    def test_write_replaces_the_graph(self):
        driver = driver_or_skip(self)
        graph = load.read_project(VEHICLE)
        for _ in range(2):  # the second write must not double it
            load.write(graph, driver)
            self.assertEqual(
                count(driver, "MATCH (n:Node) RETURN count(n) AS c"), len(graph.nodes)
            )
        self.assertEqual(
            count(driver, "MATCH (:Node)-[r]->(:Node) RETURN count(r) AS c"),
            len(graph.edges),
        )

    def test_write_leaves_other_data_alone(self):
        driver = driver_or_skip(self)
        driver.execute_query("CREATE (:NotOurs {tag: 'keep'})")
        self.addCleanup(driver.execute_query, "MATCH (n:NotOurs) DELETE n")
        load.write(load.read_project(VEHICLE), driver)
        self.assertEqual(count(driver, "MATCH (n:NotOurs) RETURN count(n) AS c"), 1)


if __name__ == "__main__":
    unittest.main()
