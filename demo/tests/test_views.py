import re
import unittest

from explorer import db, load, views
from explorer.graph import Edge, Graph, Node
from tests.support import RFQ, rfq

NEEDS = RFQ / "build" / "needs" / "needs.json"


def part(key, qualified, platform=None, kind="PartUsage"):
    labels = ["Node", "Element", kind]
    props = {"key": key, "name": qualified.split("::")[-1], "qualifiedName": qualified}
    return Node(key, labels, props | {"kind": kind, "platform": platform})


class DefaultFocusTest(unittest.TestCase):
    """The first top-level project part, by key."""

    def test_falls_back_to_a_top_level_project_part(self):
        graph = db.Graph()
        self.addCleanup(graph.close)
        nodes = [
            part("pkg", "Shop", kind="Package"),
            part("A-1", "Shop::platformBench", platform=True),
            part("A-2", "Shop::bench::vice"),
            part("B-1", "Shop::bench"),
            part("C-1", "Shop::lathe"),
        ]
        owns = [("pkg", "A-1"), ("pkg", "B-1"), ("pkg", "C-1"), ("B-1", "A-2")]
        load.write(
            Graph({n.key: n for n in nodes}, [Edge(a, "OWNS", b) for a, b in owns]),
            graph,
        )
        for kind in ("context", "boundary", "interfaces", "composition"):
            with self.subTest(kind=kind):
                self.assertEqual(views.view(graph, kind, None)["focus"], "B-1")


class ViewsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = rfq()

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()

    def view(self, kind, focus=None):
        v = views.view(self.graph, kind, focus, NEEDS)
        self.assertEqual(bool(v["reason"]), not v["nodes"])
        return v

    def names(self, v):
        return {n["name"] for n in v["nodes"]}

    def test_context_default(self):
        v = self.view("context")
        self.assertEqual(v["focus"], "LC-100")
        self.assertLessEqual(
            {
                "seat",
                "seatControlUnit",
                "occupant",
                "workshopTester",
                "endOfLineTester",
            },
            self.names(v),
        )

    def test_boundary_of_the_driver_switch(self):
        v = self.view("boundary", "LC-101")
        ports = {n["name"] for n in v["nodes"] if n["parent"] == "LC-101"}
        self.assertLessEqual({"lin", "supply"}, ports)

    def test_activity(self):
        v = self.view("activity", "SSW-FEAT-001")
        edges = {(e["src"], e["dst"], e["type"]) for e in v["edges"]}
        self.assertIn(("SSW-F-001", "SSW-F-002", "SUCCESSION"), edges)
        self.assertIn(
            ("FLOW", "KeyState"), {(e["type"], e["label"]) for e in v["edges"]}
        )

    def test_activity_without_actions(self):
        v = self.view("activity", "PC-101")
        self.assertEqual(v["nodes"], [])
        self.assertTrue(v["reason"])

    def test_variants_mark_the_rfq_selection(self):
        v = self.view("variants", "SeatSwitchPhysical::housing")
        selected = {n["key"]: n.get("selected") for n in v["nodes"]}
        self.assertTrue(selected["SSW-PC-002"])
        self.assertTrue(selected["SSW-PC-003"])
        self.assertTrue(selected["PC-101"])
        self.assertIn(
            ("PC-101", "SSW-PC-002", "SPECIALIZES"),
            {(e["src"], e["dst"], e["type"]) for e in v["edges"]},
        )
        v = self.view("variants", "SSW-PC-011")
        selected = {n["key"]: n.get("selected") for n in v["nodes"]}
        self.assertTrue(selected["SSW-PC-015"])
        self.assertFalse(selected["SSW-PC-012"])

    def test_trace(self):
        keys = {n["key"] for n in self.view("trace", "CRS-301")["nodes"]}
        self.assertLessEqual({"CON-101", "STC-101", "CTR-003"}, keys)

    def test_trace_stops_at_other_requirements(self):
        # CTR-003 also applies to CRS-302
        keys = {n["key"] for n in self.view("trace", "CRS-301")["nodes"]}
        self.assertNotIn("CRS-302", keys)

    def test_trace_shows_the_constraint(self):
        v = self.view("trace", "CRS-301")
        kinds = {n["key"]: n["kind"] for n in v["nodes"]}
        self.assertEqual(kinds["CON-101"], "ConstraintUsage")
        self.assertIn(
            ("CON-101", "CRS-301", "SATISFIES"),
            {(e["src"], e["dst"], e["type"]) for e in v["edges"]},
        )

    def test_trace_default_has_links(self):
        self.assertEqual(self.view("trace")["focus"], "CRS-201")

    def test_context_draws_each_thing_once(self):
        v = self.view("context")
        names = [n["name"] for n in v["nodes"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual([n["key"] for n in v["nodes"]].count(v["focus"]), 1)

    def test_usecase_actors_once(self):
        names = [n["name"] for n in self.view("usecases")["nodes"]]
        self.assertEqual(len(names), len(set(names)))

    def test_defaults_prefer_the_project_over_the_platform(self):
        # the project feature with the most actions, so the default is not a single box
        self.assertEqual(self.view("activity")["focus"], "FEAT-102")
        self.assertEqual(self.view("usecases")["focus"], "UC-101")
        self.assertEqual(self.view("variants")["focus"], "SSW-PC-001")

    def test_compliance(self):
        # two tables: customer requirements, then customer test requirements
        crs, ctr = (
            (RFQ / "docs" / "_generated" / "compliance.md").read_text().split("\n\n")
        )
        first = re.compile(r"^\| \{need\}`([^`]+)`", re.MULTILINE)
        v = self.view("compliance")
        self.assertEqual([r["crs"] for r in v["rows"]], first.findall(crs))
        self.assertEqual([r["ctr"] for r in v["ctrs"]], first.findall(ctr))
        row = next(r for r in v["rows"] if r["crs"] == "CRS-301")
        self.assertEqual(row["class"], "non-functional")
        self.assertEqual(row["constraints"], ["CON-101"])
        ctr003 = next(r for r in v["ctrs"] if r["ctr"] == "CTR-003")
        self.assertEqual(ctr003["implemented_by"], ["STC-101"])
        self.assertIn("CTR-003", {n["key"] for n in v["nodes"]})

    def test_every_default_renders(self):
        for kind in views.KINDS:
            with self.subTest(kind=kind):
                self.assertTrue(self.view(kind)["nodes"])

    def test_tree(self):
        roots = views.tree(self.graph)
        self.assertIn("SeatSwitchRfqPhysical", [r["name"] for r in roots])
        self.assertEqual({r["kind"] for r in roots}, {"Package"})

    def requirement(self, group, key):
        groups = {g["name"]: g for g in views.requirements_tree(self.graph)}
        return next(c for c in groups[group]["children"] if c["key"] == key)

    def test_requirements_tree_groups_and_classes(self):
        groups = views.requirements_tree(self.graph)
        self.assertEqual(
            [g["name"] for g in groups][:3],
            [
                "Customer requirements",
                "Customer test requirements",
                "System requirements",
            ],
        )
        self.assertIsNone(groups[0]["key"])
        crs = self.requirement("Customer requirements", "CRS-304")
        self.assertEqual(crs["class"], "non-functional")
        links = {(c["rel"], c["key"]) for c in crs["children"]}
        self.assertIn(("satisfied by (partial)", "CON-104"), links)
        self.assertNotIn(("satisfied by", "CON-104"), links)
        self.assertIn(("satisfied by", "SR-119"), links)
        self.assertIn(("test requirement", "CTR-002"), links)

    def test_requirements_tree_lists_what_implements_a_ctr(self):
        ctr = self.requirement("Customer test requirements", "CTR-003")
        self.assertEqual(ctr["kind"], "ctr")
        links = {(c["rel"], c["key"]) for c in ctr["children"]}
        self.assertIn(("implemented by", "STC-101"), links)
        self.assertLessEqual(
            {("applies to", "CRS-301"), ("applies to", "CRS-302")}, links
        )
        atc = self.requirement("Acceptance tests", "ATC-106")
        self.assertIn(
            ("implements", "CTR-009"), {(c["rel"], c["key"]) for c in atc["children"]}
        )

    def test_rflp_tree_follows_the_chain(self):
        def paths(nodes, prefix=()):
            for n in nodes:
                here = prefix + (n["key"],)
                yield here
                yield from paths(n["children"], here)

        all_paths = set(paths(views.rflp_tree(self.graph)))
        self.assertIn(("UC-102", "FEAT-102", "F-101", "LC-101", "PC-101"), all_paths)
        self.assertIn(("UC-102", "FEAT-102", "F-101", "LC-101", "PC-102"), all_paths)
        roots = [n["key"] for n in views.rflp_tree(self.graph)]
        self.assertLess(roots.index("UC-104"), roots.index("SSW-UC-001"))

    def test_vmodel_levels_and_sides(self):
        v = views.view(self.graph, "vmodel", None)
        at = {n["key"]: (n["level"], n["side"]) for n in v["nodes"]}
        self.assertEqual(at["CRS-301"], (1, "left"))
        self.assertEqual(at["ATC-101"], (1, "right"))
        self.assertEqual(at["CTR-003"], (1, "right"))
        self.assertEqual(at["SR-101"], (2, "left"))
        self.assertEqual(at["CON-101"], (2, "left"))
        self.assertEqual(at["STC-101"], (2, "right"))
        self.assertEqual(at["FEAT-102"], (3, "left"))
        self.assertEqual(at["LC-101"], (4, "left"))
        self.assertEqual(at["PC-101"], (5, "bottom"))
        self.assertNotIn("SSW-FEAT-001", at)
        edges = {(e["src"], e["dst"], e["type"]) for e in v["edges"]}
        self.assertIn(("STC-101", "CTR-003", "IMPLEMENTS"), edges)
        self.assertIn(("ATC-106", "CTR-009", "IMPLEMENTS"), edges)
        self.assertIn(("CON-101", "CRS-301", "SATISFIES"), edges)
        self.assertIn(("STC-102", "CON-103", "VERIFIES"), edges)
        self.assertIn(("CTR-003", "CRS-301", "APPLIES_TO"), edges)
        self.assertEqual(v["empty"], [3, 4])

    def test_vmodel_of_another_focus_is_the_whole_v(self):
        v = views.view(self.graph, "vmodel", "LC-101")
        self.assertEqual(v["focus"], "LC-101")
        self.assertIn("CRS-201", {n["key"] for n in v["nodes"]})

    def test_vmodel_of_one_requirement(self):
        keys = {n["key"] for n in views.view(self.graph, "vmodel", "CRS-301")["nodes"]}
        self.assertLessEqual({"CTR-003", "STC-101"}, keys)
        self.assertNotIn("CRS-302", keys)
        self.assertNotIn("CTR-001", keys)

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            views.view(self.graph, "nope", None)

    def test_unknown_focus(self):
        with self.assertRaises(KeyError):
            views.view(self.graph, "trace", "NOPE-1")


if __name__ == "__main__":
    unittest.main()
