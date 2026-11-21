import json
import unittest
from pathlib import Path

from explorer import graph

FIXTURES = Path(__file__).parent / "fixtures"


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        export = json.loads((FIXTURES / "model.json").read_text())
        needs = json.loads((FIXTURES / "needs.json").read_text())
        cls.graph = graph.build(export, needs["versions"]["1"]["needs"])

    def edges(self, type):
        return {(e.src, e.dst) for e in self.graph.edges if e.type == type}

    def by_name(self, name):
        return next(n for n in self.graph.nodes.values() if n.props.get("name") == name)

    def test_attribute_value_and_unit(self):
        props = self.by_name("ratedPower").props
        self.assertEqual((props["value"], props["unit"]), (80, "kW"))

    def test_string_attribute_keeps_value_and_no_unit(self):
        props = self.by_name("ipRating").props
        self.assertEqual(props["value"], "IP67")
        self.assertNotIn("unit", {k for k, v in props.items() if v is not None})

    def test_implied_subsetting_has_no_edge(self):
        m50, m80, motor = self.by_name("m50").key, self.by_name("m80").key, "PC-001"
        self.assertNotIn((m50, motor), self.edges("SPECIALIZES"))
        self.assertIn((m80, motor), self.edges("SPECIALIZES"))

    def test_specializes_from_needs_and_export_is_deduplicated(self):
        self.assertEqual(
            [
                e
                for e in self.graph.edges
                if e.type == "SPECIALIZES" and e.src == "PC-001"
            ],
            [graph.Edge("PC-001", "SPECIALIZES", "PC-000")],
        )

    def test_requirement_requires_constraint_with_expression(self):
        ((src, dst),) = self.edges("REQUIRES")
        self.assertEqual(src, "SR-001")
        self.assertEqual(
            self.graph.nodes[dst].props["expression"], "peakTorque <= 310 [N*m]"
        )

    def test_subject(self):
        self.assertEqual({s for s, _ in self.edges("SUBJECT")}, {"SR-001"})

    def test_physical_component_labels(self):
        self.assertEqual(
            self.graph.nodes["PC-001"].labels,
            ["Node", "Element", "PartUsage", "Need", "physical"],
        )
        props = self.graph.nodes["PC-001"].props
        self.assertEqual(
            (props["layer"], props["domain"], props["source"]),
            ("P", "EE", "phys.sysml:3"),
        )

    def test_variation_flag(self):
        self.assertIs(self.graph.nodes["PC-001"].props["isVariation"], True)

    def test_every_node_has_the_common_label(self):
        self.assertTrue(all(n.labels[0] == "Node" for n in self.graph.nodes.values()))

    def test_customer_requirement_is_need_only(self):
        self.assertEqual(self.graph.nodes["CRS-001"].labels, ["Node", "Need", "crs"])

    def test_succession_flow_connects_performs(self):
        convert, produce = self.by_name("convert").key, self.by_name("produce").key
        self.assertEqual(self.edges("SUCCESSION"), {(convert, produce)})
        flows = [e for e in self.graph.edges if e.type == "FLOW"]
        self.assertEqual(
            sorted((e.src, e.dst, e.props["item"]) for e in flows),
            [(convert, produce, "Heat"), (convert, produce, "Power")],
        )
        self.assertEqual(
            self.edges("CONNECTS"),
            {(self.by_name("pack").key, self.by_name("m80").key)},
        )
        self.assertEqual(
            self.edges("PERFORMS"),
            {(self.by_name("pack").key, self.by_name("drive").key)},
        )

    def test_typed_by(self):
        self.assertIn(
            (self.by_name("m80").key, self.by_name("Motor").key), self.edges("TYPED_BY")
        )

    def test_need_links_become_edges_and_back_fields_do_not(self):
        self.assertIn(("PC-001", "LC-001"), self.edges("ALLOCATED_TO"))
        self.assertIn(("SR-001", "CRS-001"), self.edges("SATISFIES"))
        self.assertFalse([e for e in self.graph.edges if e.type.endswith("_BACK")])

    def test_owns(self):
        self.assertIn(("PC-001", self.by_name("m80").key), self.edges("OWNS"))

    def test_search_text_includes_linked_needs_and_attributes(self):
        self.assertIn(
            "The drive shall give 50 km range.",
            self.graph.nodes["LC-001"].props["searchText"],
        )
        self.assertIn("The drive unit.", self.graph.nodes["PC-001"].props["searchText"])
        self.assertIn("80 kW", self.by_name("m80").props["searchText"])
        self.assertIn(
            "Permanent-magnet drive motor.",
            self.graph.nodes["PC-001"].props["searchText"],
        )


if __name__ == "__main__":
    unittest.main()
