import json
import unittest
from pathlib import Path

from sysml2kit.constraints import Model, Unevaluable
from sysml2kit.needs import normalize

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return Model(normalize(json.loads((FIXTURES / f"{name}.json").read_text())))


def named(model, name):
    return next(
        e["@id"]
        for e in model.by_id.values()
        if e["@type"] == "ConstraintUsage" and e.get("name") == name
    )


class EvaluateTest(unittest.TestCase):
    """Constraints evaluated from the expression tree `sysml export` writes (fixtures/expressions.sysml)."""

    @classmethod
    def setUpClass(cls):
        cls.model = load("expressions")

    def check(self, name):
        return self.model.check(named(self.model, name))

    def test_holds(self):
        for name in (
            "holdsMass",
            "holdsForce",
            "holdsTemp",
            "holdsIp",
            "holdsCycles",
            "holdsLum",
            "holdsChain",
            "holdsNotOr",
            "holdsBool",
        ):
            with self.subTest(name=name):
                self.assertTrue(self.check(name)[0])

    def test_violated(self):
        for name in ("failsMass", "failsCycles", "failsIp"):
            with self.subTest(name=name):
                self.assertFalse(self.check(name)[0])

    def test_reports_text_and_values(self):
        self.assertEqual(
            self.check("failsMass"), (False, "mass <= 40 [g]", {"mass": "48 [g]"})
        )
        self.assertEqual(self.check("holdsChain")[2], {"a.nad": "33", "b.nad": "34"})

    def test_different_units_are_not_compared(self):
        with self.assertRaisesRegex(Unevaluable, r"units differ: g and kg"):
            self.check("unitsDiffer")

    def test_missing_value(self):
        with self.assertRaisesRegex(Unevaluable, "unset has no value"):
            self.check("noValue")

    def test_unsupported_operator(self):
        with self.assertRaisesRegex(Unevaluable, r"operator '\*'"):
            self.check("arithmetic")


class InheritedTest(unittest.TestCase):
    """A constraint holds for every part that inherits it, with that part's own values."""

    def setUp(self):
        self.model = load("inherited_constraint")

    def results(self):
        constraint = next(
            e["@id"]
            for e in self.model.by_id.values()
            if e.get("declaredShortName") == "CON-1"
        )
        return {
            self.model.by_id[c].get("name"): self.model.check(constraint, c)[0]
            for c in self.model.contexts(constraint)
        }

    def test_checked_in_every_inheriting_part(self):
        # `own` redefines the constraint, so the inherited one does not apply there
        self.assertEqual(self.results(), {"Rated": True, "weak": False, "fine": True})
