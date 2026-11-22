"""The seat-switch RFQ (with its platform) carries what the demo shows: attributes, constraints,
flows, the position switches, the variant selection and the switch context."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from sysml2kit.needs import normalize, platform_dir

RFQ = Path(__file__).resolve().parents[2] / "examples" / "seat-switch-rfq"
export = []


def setUpModule():
    if not shutil.which("sysml"):
        raise unittest.SkipTest("`sysml` is not on PATH")
    # the RFQ Makefile's selection: model/ and the platform's model without its trace.sysml
    platform = platform_dir(RFQ) / "model"
    files = sorted(RFQ.glob("model/**/*.sysml")) + sorted(
        p for p in platform.glob("**/*.sysml") if p != platform / "trace.sysml"
    )
    with tempfile.TemporaryFile("w+") as out:
        subprocess.run(["sysml", "export", *map(str, files)], stdout=out, check=True)
        out.seek(0)
        export.extend(normalize(json.load(out)))


def index(elements):
    return {e["@id"]: e for e in elements}


def element(elements, qualified_name):
    found = [e for e in elements if e.get("qualifiedName") == qualified_name]
    assert found, f"no element {qualified_name} in the export"
    return found[0]


def owned(elements, e, key="ownedElement"):
    by_id = index(elements)
    return [by_id[r["@id"]] for r in e.get(key) or [] if r["@id"] in by_id]


def texts_of_attribute_values(elements, qualified_name):
    """Attribute name -> textual form of its value, for the attributes the element owns."""
    texts = {}
    for attribute in owned(elements, element(elements, qualified_name)):
        if attribute["@type"] != "AttributeUsage":
            continue
        for value in owned(elements, attribute):
            if value["@type"] == "FeatureValue":
                for expression in owned(elements, value):
                    for text in owned(elements, expression, "textualRepresentation"):
                        texts[attribute["name"]] = text["body"]
    return texts


def named(elements, kind, name):
    return [e for e in elements if e["@type"] == kind and e.get("name") == name]


def count(elements, kind):
    return sum(e["@type"] == kind for e in elements)


def port_names(elements, qualified_name):
    """Names of the ports the element owns or inherits."""
    by_id = index(elements)
    features = element(elements, qualified_name).get("feature") or []
    return {
        by_id[f["@id"]]["name"]
        for f in features
        if by_id.get(f["@id"], {}).get("@type") == "PortUsage"
    }


def part_names(elements, qualified_name):
    """Names of the parts the element owns."""
    return {
        e["name"]
        for e in owned(elements, element(elements, qualified_name))
        if e["@type"] == "PartUsage"
    }


def specialized(elements, qualified_name):
    """Qualified names of what the element subsets or redefines."""
    by_id = index(elements)
    return {
        by_id.get(r["subsettedFeature"]["@id"], {}).get("qualifiedName")
        for r in owned(elements, element(elements, qualified_name), "ownedRelationship")
        if r["@type"] in ("Subsetting", "Redefinition")
    }


class EnrichedExampleTest(unittest.TestCase):
    def test_attributes_with_units(self):
        values = texts_of_attribute_values(export, "SeatSwitchPhysical::SwitchAssembly")
        self.assertRegex(values["actuationForce"], r"^4.5 \[N\]$")
        self.assertRegex(values["mass"], r"^48 \[g\]$")

    def test_constraints(self):
        self.assertTrue(named(export, "ConstraintUsage", "actuationForceLimits"))
        self.assertTrue(named(export, "ConstraintUsage", "driverHousingSide"))

    def test_seat_positions(self):
        self.assertEqual(
            part_names(export, "SeatSwitchRfqPhysical::vehicleSeatSwitches"),
            {"driverSwitch", "coDriverSwitch", "rearLeftSwitch", "rearRightSwitch"},
        )

    def test_variant_selection(self):
        self.assertIn(
            "SeatSwitchPhysical::housing::housingLH",
            specialized(
                export,
                "SeatSwitchRfqPhysical::vehicleSeatSwitches::driverSwitch::driverHousing",
            ),
        )
        self.assertIn(
            "SeatSwitchPhysical::housing::housingRH",
            specialized(
                export,
                "SeatSwitchRfqPhysical::vehicleSeatSwitches::coDriverSwitch::coDriverHousing",
            ),
        )

    def test_assembly_boundary(self):
        self.assertEqual(
            port_names(export, "SeatSwitchPhysical::SwitchAssembly"),
            {"lin", "supply", "ground"},
        )

    def test_context(self):
        self.assertEqual(
            part_names(export, "SeatSwitchRfqContext::seatSwitchContext"),
            {
                "OEM_SeatSwitch",
                "seatHarness",
                "seat",
                "seatControlUnit",
                "occupant",
                "technician",
                "workshopTester",
                "endOfLineTester",
            },
        )

    def test_flows(self):
        self.assertGreaterEqual(count(export, "FlowUsage"), 2)


if __name__ == "__main__":
    unittest.main()
