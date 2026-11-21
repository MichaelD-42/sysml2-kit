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


if __name__ == "__main__":
    unittest.main()
