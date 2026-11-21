import re
import unittest
from pathlib import Path

from explorer import load, views
from explorer.graph import Edge, Graph, Node
from tests.support import driver_or_skip, load_project

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"
NEEDS = VEHICLE / "build" / "needs" / "needs.json"


def part(key, qualified, platform=None, kind="PartUsage"):
    labels = ["Node", "Element", kind]
    props = {"key": key, "name": qualified.split("::")[-1], "qualifiedName": qualified}
    return Node(key, labels, props | {"kind": kind, "platform": platform})


class DefaultFocusTest(unittest.TestCase):
    """A project without VehicleLogical::vehicle: the first top-level project part."""

    def test_falls_back_to_a_top_level_project_part(self):
        driver = driver_or_skip(self)
        nodes = [
            part("pkg", "Shop", kind="Package"),
            part("A-1", "Shop::platformBench", platform=True),
            part("A-2", "Shop::bench::vice"),
            part("B-1", "Shop::bench"),
            part("C-1", "Shop::lathe"),
        ]
        owns = [("pkg", "A-1"), ("pkg", "B-1"), ("pkg", "C-1"), ("B-1", "A-2")]
        graph = Graph({n.key: n for n in nodes}, [Edge(a, "OWNS", b) for a, b in owns])
        load.write(graph, driver)
        for kind in ("context", "boundary", "interfaces", "composition"):
            with self.subTest(kind=kind):
                self.assertEqual(views.view(driver, kind, None)["focus"], "B-1")


class ViewsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        case = unittest.TestCase()
        try:
            cls.driver = driver_or_skip(case)
        except unittest.SkipTest as skip:
            raise unittest.SkipTest(str(skip))
        load_project(cls.driver, VEHICLE)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

    def view(self, kind, focus=None):
        v = views.view(self.driver, kind, focus, NEEDS)
        self.assertEqual(bool(v["reason"]), not v["nodes"])
        return v

    def names(self, v):
        return {n["name"] for n in v["nodes"]}

    def test_context_default(self):
        v = self.view("context")
        self.assertLessEqual(
            {"driver", "trailer", "chargingStation", "road"}, self.names(v)
        )

    def test_boundary_of_drive_unit(self):
        v = self.view("boundary", "VehiclePhysical::vehicleAssembly::driveUnit")
        ports = {n["name"] for n in v["nodes"] if n["parent"] == v["focus"]} & {
            "hvIn",
            "canBus",
            "coolantIn",
            "coolantOut",
            "mount",
        }
        self.assertEqual(len(ports), 5)
        self.assertLessEqual(
            {"tractionBattery", "vehicleControlUnit", "coolingCircuit", "ladderFrame"},
            self.names(v),
        )

    def test_activity(self):
        v = self.view("activity", "F-002")
        edges = {(e["src"], e["dst"], e["type"]) for e in v["edges"]}
        self.assertIn(("F-006", "F-007", "SUCCESSION"), edges)
        self.assertIn(
            ("FLOW", "ElectricPower"), {(e["type"], e["label"]) for e in v["edges"]}
        )

    def test_activity_without_actions(self):
        v = self.view("activity", "PC-001")
        self.assertEqual(v["nodes"], [])
        self.assertTrue(v["reason"])

    def test_variants(self):
        v = self.view("variants", "EDU-PC-001")
        selected = {n["key"]: n.get("selected") for n in v["nodes"]}
        self.assertTrue(selected["EDU-PC-003"])
        self.assertFalse(selected["EDU-PC-002"])

    def test_trace(self):
        keys = {n["key"] for n in self.view("trace", "CRS-003")["nodes"]}
        self.assertLessEqual({"SR-005", "LC-007", "PC-001", "STC-005"}, keys)

    def test_trace_stops_at_other_requirements(self):
        keys = {n["key"] for n in self.view("trace", "CRS-001")["nodes"]}
        self.assertNotIn("CRS-002", keys)

    def test_trace_shows_the_constraint(self):
        v = self.view("trace", "CRS-003")
        kinds = {n["key"]: n["kind"] for n in v["nodes"]}
        required = [e["dst"] for e in v["edges"] if e["type"] == "REQUIRES"]
        self.assertEqual(
            [e["src"] for e in v["edges"] if e["type"] == "REQUIRES"], ["SR-005"]
        )
        self.assertEqual(kinds[required[0]], "ConstraintUsage")

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
        self.assertEqual(self.view("activity")["focus"], "FEAT-002")
        self.assertEqual(self.view("usecases")["focus"], "UC-001")

    def test_compliance(self):
        table = (VEHICLE / "docs" / "_generated" / "compliance.md").read_text()
        expected = re.findall(r"^\| \{need\}`([^`]+)`", table, re.MULTILINE)
        rows = self.view("compliance")["rows"]
        self.assertEqual([r["crs"] for r in rows], expected)

    def test_every_default_renders(self):
        for kind in views.KINDS:
            with self.subTest(kind=kind):
                self.assertTrue(self.view(kind)["nodes"])

    def test_tree(self):
        roots = views.tree(self.driver)
        self.assertIn("VehiclePhysical", [r["name"] for r in roots])
        self.assertEqual({r["kind"] for r in roots}, {"Package"})

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            views.view(self.driver, "nope", None)

    def test_unknown_focus(self):
        with self.assertRaises(KeyError):
            views.view(self.driver, "trace", "NOPE-1")


if __name__ == "__main__":
    unittest.main()
