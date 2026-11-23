import json
import unittest
from pathlib import Path

from sysml2kit.constraints import Model, Unevaluable, evaluate
from sysml2kit.needs import normalize

VALUES = {
    ("mass",): "48 [g]",
    ("force",): "4.5 [N]",
    ("minTemp",): "-40 ['°C']",
    ("ip",): '"IP5K4"',
    ("cycles",): "200000",
    ("lum",): "20 [cd / m^2]",
    ("a", "nad"): "33",
    ("b", "nad"): "34",
    ("ok",): "true",
}


def lookup(chain):
    if chain not in VALUES:
        raise Unevaluable(f"{'.'.join(chain)} has no value")
    return VALUES[chain]


class EvaluateTest(unittest.TestCase):
    def test_holds(self):
        for text in (
            "mass <= 60 [g]",
            "force >= 3.0 [N] and force <= 6.5 [N]",
            "minTemp <= -40 ['°C']",
            'ip == "IP5K4"',
            "cycles >= 200000",
            "lum >= 8 [cd/m^2] and lum <= 40 [cd/m^2]",
            "a.nad != b.nad",
            "not (mass > 60 [g]) or cycles < 1",
            "ok",
        ):
            with self.subTest(text=text):
                self.assertTrue(evaluate(text, lookup))

    def test_violated(self):
        for text in ("mass <= 40 [g]", "cycles >= 300000", 'ip == "IP6K9K"'):
            with self.subTest(text=text):
                self.assertFalse(evaluate(text, lookup))

    def test_different_units_are_not_compared(self):
        with self.assertRaisesRegex(Unevaluable, r"units differ: g and kg"):
            evaluate("mass <= 0.06 [kg]", lookup)

    def test_missing_value(self):
        with self.assertRaisesRegex(Unevaluable, "c.nad has no value"):
            evaluate("a.nad != c.nad", lookup)

    def test_unsupported_syntax(self):
        with self.assertRaises(Unevaluable):
            evaluate("mass->size() == 1", lookup)

    def test_a_comparison_must_give_a_boolean(self):
        with self.assertRaisesRegex(Unevaluable, "not a boolean"):
            evaluate("mass", lookup)


if __name__ == "__main__":
    unittest.main()


class InheritedTest(unittest.TestCase):
    """A constraint holds for every part that inherits it, with that part's own values."""

    def setUp(self):
        path = Path(__file__).parent / "fixtures" / "inherited_constraint.json"
        self.model = Model(normalize(json.loads(path.read_text())))

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
