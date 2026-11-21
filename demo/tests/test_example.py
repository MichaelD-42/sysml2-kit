"""The enriched vehicle example (with its platform) carries what the demo shows: attributes,
constraints, flows, the drive-unit assembly and the vehicle context."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"
export = []


def setUpModule():
    if not shutil.which("sysml"):
        raise unittest.SkipTest("`sysml` is not on PATH")
    # the vehicle Makefile's selection: model/ and the platform's model without its trace.sysml
    files = sorted(VEHICLE.glob("model/**/*.sysml")) + sorted(
        p
        for p in VEHICLE.glob("platform/model/**/*.sysml")
        if p != VEHICLE / "platform/model/trace.sysml"
    )
    with tempfile.TemporaryFile("w+") as out:
        subprocess.run(["sysml", "export", *map(str, files)], stdout=out, check=True)
        out.seek(0)
        export.extend(json.load(out))


def index(elements):
    return {e["@id"]: e for e in elements}


def element(elements, qualified_name):
    return next(e for e in elements if e.get("qualifiedName") == qualified_name)


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


def requirement_constraints(elements, qualified_name):
    e = element(elements, qualified_name)
    return [
        r
        for r in owned(elements, e, "ownedRelationship")
        if r["@type"] == "RequirementConstraintMembership"
    ]


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
    return {
        e["name"]
        for e in owned(elements, element(elements, qualified_name))
        if e["@type"] == "PartUsage"
    }


def connections_touching(elements, qualified_name):
    """Connectors with an end on the element or on a feature chain through it (`driveUnit.hvIn`)."""
    target = element(elements, qualified_name)["@id"]
    kinds = {
        "ConnectionUsage",
        "InterfaceUsage",
        "FlowUsage",
        "BindingConnectorAsUsage",
    }
    touching = 0
    for connector in elements:
        if connector["@type"] not in kinds:
            continue
        ends = [r["@id"] for r in connector.get("relatedFeature") or []]
        for end in owned(elements, connector):
            ends += [c["@id"] for c in end.get("chainingFeature") or []]
        touching += target in ends
    return touching


class EnrichedExampleTest(unittest.TestCase):
    def test_attributes_with_units(self):
        values = texts_of_attribute_values(export, "EDrivePhysical::motor::motor80kW")
        self.assertIn("ratedPower", values)
        self.assertRegex(values["ratedPower"], r"^80 \[kW\]$")

    def test_constraints(self):
        self.assertTrue(named(export, "ConstraintUsage", "peakTorqueLimit"))
        self.assertTrue(named(export, "ConstraintUsage", "coolantDerating"))

    def test_requirement_constraint_on_sr005(self):
        self.assertTrue(
            requirement_constraints(export, "VehicleRequirements::acceleration")
        )

    def test_drive_unit_boundary(self):
        self.assertEqual(
            port_names(export, "VehiclePhysical::vehicleAssembly::driveUnit"),
            {"hvIn", "canBus", "coolantIn", "coolantOut", "mount"},
        )
        self.assertGreaterEqual(
            connections_touching(export, "VehiclePhysical::vehicleAssembly::driveUnit"),
            5,
        )

    def test_context(self):
        self.assertEqual(
            part_names(export, "VehicleContext::vehicleContext"),
            {"vehicle", "driver", "passenger", "trailer", "chargingStation", "road"},
        )

    def test_flows(self):
        self.assertGreaterEqual(
            count(export, "FlowUsage") + count(export, "SuccessionFlowUsage"), 3
        )


if __name__ == "__main__":
    unittest.main()
