import re
import unittest
from pathlib import Path

from explorer import views
from tests.support import driver_or_skip, load_project

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"
NEEDS = VEHICLE / "build" / "needs" / "needs.json"


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
