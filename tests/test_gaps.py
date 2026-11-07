import json
import unittest
from pathlib import Path

from sysml2kit.gaps import RULE_LAYERS, gaps

ROOT = Path(__file__).resolve().parent.parent


def violation(rule, msg="Too few"):
    return {
        "type": "sn_schema_violation",
        "details": {"schema_path": f"{rule}[3] > validate", "validation_msg": msg},
    }


NEEDS = {
    "CRS-001": {"docname": "customer/requirements", "lineno": 4, "source": None},
    "SR-003": {"docname": "model", "lineno": 27, "source": "model/r.sysml:14"},
    "STC-004": {"docname": "model", "lineno": 40, "source": "model/t.sysml:9"},
}
VIOLATIONS = {
    "validation_warnings": {
        "STC-004": [violation("systest-verifies")],
        "SR-003": [violation("sysreq-satisfied"), violation("sysreq-verified")],
        "CRS-001": [violation("crs-satisfied", "No SR")],
    }
}


class GapsTest(unittest.TestCase):
    def test_all_gaps_in_layer_order_with_locations(self):
        self.assertEqual(
            gaps(VIOLATIONS, NEEDS),
            [
                (
                    "R",
                    "crs-satisfied",
                    "CRS-001",
                    "docs/customer/requirements.rst:4",
                    "No SR",
                ),
                ("L", "sysreq-satisfied", "SR-003", "model/r.sysml:14", "Too few"),
                ("V", "sysreq-verified", "SR-003", "model/r.sysml:14", "Too few"),
                ("V", "systest-verifies", "STC-004", "model/t.sysml:9", "Too few"),
            ],
        )

    def test_a_layer_keeps_its_own_and_earlier_rules(self):
        self.assertEqual(
            [g[1] for g in gaps(VIOLATIONS, NEEDS, "L")],
            ["crs-satisfied", "sysreq-satisfied"],
        )

    def test_a_rule_without_a_layer_is_always_reported(self):
        custom = {"validation_warnings": {"SR-003": [violation("house-rule")]}}
        self.assertEqual(
            gaps(custom, NEEDS, "R"),
            [("?", "house-rule", "SR-003", "model/r.sysml:14", "Too few")],
        )

    def test_no_violations_no_gaps(self):
        self.assertEqual(gaps({"validation_warnings": {}}, NEEDS), [])

    def test_every_rule_in_the_schema_has_a_layer(self):
        schemas = json.loads(
            (
                ROOT / "plugins/sysml-rflp/templates/project/docs/schemas.json"
            ).read_text()
        )["schemas"]
        self.assertEqual(sorted(RULE_LAYERS), sorted(s["id"] for s in schemas))


if __name__ == "__main__":
    unittest.main()
