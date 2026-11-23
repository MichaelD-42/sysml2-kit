"""Evaluate a constraint from the expression tree `sysml export` writes.

The standard parser has already resolved every name: a feature reference names its referent. This walks
the tree in a context (the constraint's owner, or a part that inherits it) and takes each referenced
feature's value from the nearest redefinition that context sees. It covers literals, `and`, `or`, `xor`,
`not`, comparisons, unary minus and quantities (`5 [N]`); anything else is reported as not evaluated,
never guessed. Quantities in different units are converted as the standard library defines the units
(a `unitConversion` by prefix or by convention, or a unit expression such as `kg*m/s^2`), down to a
factor and powers of base units; library units come from the table in `units.py`.
"""

import json
import math
from collections import namedtuple

from sysml2kit.units import table

COMPARE = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}
LOGIC = {
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
    "xor": lambda a, b: a != b,
}
LITERALS = ("LiteralInteger", "LiteralRational", "LiteralString", "LiteralBoolean")
# unit: what identifies the unit (the library elements it names); shown: its text; expression: its @id
Quantity = namedtuple("Quantity", "number unit shown expression")
MR = "MeasurementReferences::"
KELVIN = "SI::kelvin"


class Unevaluable(Exception):
    pass


SPECIALIZATIONS = (
    "Subsetting",
    "Redefinition",
    "ReferenceSubsetting",
    "Subclassification",
    "FeatureTyping",
)


class Model:
    """Feature values and constraint evaluation over `sysml export` elements."""

    def __init__(self, elements, units=None):
        """`units`: the library's unit table (`units.table()`, the default), {} for none."""
        self.units = table() if units is None else units
        self.reduced = {}
        self.by_id = {e["@id"]: e for e in elements}
        self.owned, self.generals, self.specifics, self.redefines = {}, {}, {}, {}
        self.text, self.results = {}, {}
        for e in elements:
            owner = (e.get("owner") or {}).get("@id")
            if owner:
                self.owned.setdefault(owner, []).append(e["@id"])
            if e["@type"] in SPECIALIZATIONS:
                specific = (e.get("specific") or {}).get("@id")
                general = (e.get("general") or {}).get("@id")
                if specific and general:
                    self.generals.setdefault(specific, []).append(general)
                    self.specifics.setdefault(general, []).append(specific)
                    if e["@type"] == "Redefinition":
                        self.redefines.setdefault(specific, []).append(general)
            if e["@type"] == "ResultExpressionMembership":
                # a relationship's owner is its owningRelatedElement; sysml 0.1.4 also wrote `owner`
                owner = (e.get("owningRelatedElement") or e.get("owner") or {}).get(
                    "@id"
                )
                if owner and e.get("ownedRelatedElement"):
                    self.results[owner] = e["ownedRelatedElement"][0]["@id"]
            if e["@type"] == "TextualRepresentation" and e.get("representedElement"):
                self.text[e["representedElement"]["@id"]] = e.get("body", "")

    def closure(self, start, edges=None):
        """start, then what it specializes (or, given `self.specifics`, what specializes it), nearest first."""
        seen, order = {start}, [start]
        for element in order:
            for g in (self.generals if edges is None else edges).get(element, []):
                if g not in seen:
                    seen.add(g)
                    order.append(g)
        return order

    def name(self, element):
        return self.by_id.get(element, {}).get("name") or element

    def qualified(self, element):
        if element in self.by_id:
            return self.by_id[element].get("qualifiedName")
        return self.units.get(element, {}).get("name")

    def member(self, owner, qualified):
        """The feature of `owner` that is or redefines the library feature `qualified`, nearest first."""
        for element in self.closure(owner):
            for child in self.owned.get(element, []):
                if any(
                    self.qualified(r) == qualified
                    for r in self.closure(child, self.redefines)
                ):
                    return child
        return None

    def measurement_units(self):
        return [
            e["@id"]
            for e in self.by_id.values()
            if e["@type"] == "AttributeUsage"
            and any(
                self.qualified(g) == MR + "MeasurementUnit"
                for g in self.closure(e["@id"])
            )
        ]

    def reduce(self, unit):
        """(factor, {base unit @id: exponent}) of a unit, by the library's definition of it."""
        if unit in self.reduced:
            if self.reduced[unit] is None:
                raise Unevaluable(f"unit {self.name(unit)} is defined by itself")
            return self.reduced[unit]
        if unit not in self.by_id:
            if unit in self.units:
                return self.units[unit]["factor"], self.units[unit]["base"]
            raise Unevaluable("a unit neither in the export nor in the library's units")
        self.reduced[unit] = None
        self.reduced[unit] = result = self._reduce(unit)
        return result

    def _reduce(self, unit):
        if any(
            self.qualified(g) == MR + "DimensionOneUnit" for g in self.closure(unit)
        ):
            return 1.0, {}
        conversion = self.member(unit, MR + "MeasurementUnit::unitConversion")
        try:
            reference = self.referent(
                self.member(conversion, MR + "UnitConversion::referenceUnit")
            )
        except Unevaluable:
            reference = None  # the library's own declaration, no conversion stated
        if reference:
            prefix = self.member(conversion, MR + "ConversionByPrefix::prefix")
            if prefix and self.has_value(prefix):
                factor = self.member(
                    self.referent(prefix), MR + "UnitPrefix::conversionFactor"
                )
            else:
                factor = self.member(
                    conversion, MR + "UnitConversion::conversionFactor"
                )
            f, base = self.reduce(reference)
            return self.number(self.value(factor)) * f, base
        if self.has_value(unit):
            return self.algebra(self.value(unit))
        return 1.0, {unit: 1}

    def has_value(self, feature):
        try:
            self.value(feature)
        except Unevaluable:
            return False
        return True

    def referent(self, feature):
        """The element a feature's value refers to (`referenceUnit = g` gives g)."""
        if feature is None:
            raise Unevaluable("no such feature")
        e = self.by_id[self.value(feature)]
        if e["@type"] != "FeatureReferenceExpression":
            raise Unevaluable(f"{self.name(feature)} does not refer to an element")
        return e["referent"]["@id"]

    def algebra(self, expression):
        """(factor, {base unit @id: exponent}) of a unit expression (`kg*m/s^2`) or a number."""
        e = self.by_id[expression]
        if e["@type"] in ("LiteralInteger", "LiteralRational"):
            return float(e["value"]), {}
        if e["@type"] == "FeatureReferenceExpression":
            return self.reduce(e["referent"]["@id"])
        if e["@type"] != "OperatorExpression":
            raise Unevaluable(f"unit {self.shown(expression)} not evaluated")
        op, args = e["operator"], [self.algebra(a) for a in self.arguments(expression)]
        if op == "-" and len(args) == 1 and not args[0][1]:
            return -args[0][0], {}
        if op in ("*", "/") and len(args) == 2:
            sign = 1 if op == "*" else -1
            (f, a), (g, b) = args
            base = dict(a)
            for k, v in b.items():
                base[k] = base.get(k, 0) + sign * v
            return f * g**sign, {k: v for k, v in base.items() if v}
        if op in ("^", "**") and len(args) == 2 and not args[1][1]:
            (f, a), (n, _) = args
            return f**n, {k: v * n for k, v in a.items()}
        raise Unevaluable(f"unit operator {op!r} not evaluated")

    def number(self, expression):
        factor, base = self.algebra(expression)
        if base:
            raise Unevaluable(f"{self.shown(expression)} is not a number")
        return factor

    def resolve(self, context, feature):
        """The feature as `context` sees it: the nearest redefinition of it that context owns or inherits."""
        owner = (self.by_id[feature].get("owner") or {}).get("@id")
        if owner is None or self.by_id[owner]["@type"] in ("Package", "Namespace"):
            return feature  # a package-level feature is the same in every context
        types = self.closure(context)
        if owner not in types:
            # a nested feature (`a.nad`): see its owner from the context first
            return self.resolve(self.resolve(context, owner), feature)
        for element in types:
            for child in self.owned.get(element, []):
                if feature in self.closure(child, self.redefines):
                    return child
        return feature

    def value(self, feature):
        """The value expression of the feature, or of the nearest feature it redefines."""
        for element in self.closure(feature, self.redefines):
            for rel in self.by_id.get(element, {}).get("ownedRelationship") or []:
                fv = self.by_id.get(rel["@id"], {})
                if fv.get("@type") == "FeatureValue" and fv.get("value"):
                    return fv["value"]["@id"]
        raise Unevaluable(f"{self.name(feature)} has no value")

    def shown(self, expression):
        """Text of a value expression; a bare literal carries no textual representation."""
        e = self.by_id[expression]
        if e["@type"] == "LiteralString":
            return json.dumps(e["value"])
        if e["@type"] == "LiteralBoolean":
            return "true" if e["value"] else "false"
        if e["@type"] in LITERALS:
            return str(e["value"])
        return self.text.get(expression, "?")

    def arguments(self, expression):
        out = []
        for rel in self.by_id[expression].get("ownedRelationship") or []:
            pm = self.by_id.get(rel["@id"], {})
            if pm.get("@type") != "ParameterMembership":
                continue
            parameter = self.by_id[pm["ownedRelatedElement"][0]["@id"]]
            out.append(self.value(parameter["@id"]))
        return out

    def unit(self, expression):
        """What identifies a unit expression: the library elements it names, and how it combines them."""
        e = self.by_id[expression]
        if e["@type"] == "FeatureReferenceExpression":
            return e["referent"]["@id"]
        if e["@type"] == "OperatorExpression":
            return (e["operator"], *map(self.unit, self.arguments(expression)))
        if e["@type"] in LITERALS:
            return e["value"]
        raise Unevaluable(f"unit {self.shown(expression)} not evaluated")

    def evaluate(self, expression, context, values, depth=0):
        e = self.by_id[expression]
        kind = e["@type"]
        if kind in LITERALS:
            return e["value"]
        if kind == "Expression" and expression in self.results:
            return self.evaluate(self.results[expression], context, values, depth)
        if kind == "FeatureReferenceExpression":
            if depth > 5:
                raise Unevaluable("values refer to each other too deeply")
            value = self.value(self.resolve(context, e["referent"]["@id"]))
            values[self.text.get(expression, self.name(e["referent"]["@id"]))] = (
                self.shown(value)
            )
            # shortcut: a value expression is evaluated in the constraint's context, not its feature's
            # owner; upgrade when a value refers to features of a nested part
            return self.evaluate(value, context, values, depth + 1)
        if kind != "OperatorExpression":
            raise Unevaluable(f"{kind} not evaluated")
        op, args = e["operator"], self.arguments(expression)

        def arg(i):
            return self.evaluate(args[i], context, values, depth)

        if op == "[" and len(args) == 2:
            number = arg(0)
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise Unevaluable("a unit after a non-number")
            shown = self.shown(args[1]).strip("'")
            return Quantity(number, self.unit(args[1]), shown, args[1])
        if op == "-" and len(args) == 1:
            value = arg(0)
            if isinstance(value, Quantity):
                return value._replace(number=-value.number)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise Unevaluable("minus before a non-number")
            return -value
        if op == "not" and len(args) == 1:
            return not _bool(arg(0))
        if op in LOGIC and len(args) == 2:
            return LOGIC[op](_bool(arg(0)), _bool(arg(1)))
        if op in COMPARE and len(args) == 2:
            return self.compare(op, arg(0), arg(1))
        raise Unevaluable(f"operator {op!r} not evaluated")

    def body(self, constraint):
        result = self.results.get(constraint)
        if result is None:
            raise Unevaluable("no body")
        return result

    def contexts(self, constraint):
        """Where the constraint applies: its owner and everything that specializes the owner, as a
        specialization inherits its general's features; not where a nearer constraint redefines it."""
        owner = self.by_id[constraint]["owner"]["@id"]
        return [
            c
            for c in self.closure(owner, self.specifics)
            if self.resolve(c, constraint) == constraint
        ]

    def check(self, constraint, context=None):
        """(holds, text, {reference: value text}) for a constraint in a context, by default its owner."""
        body = self.body(constraint)
        values = {}
        start = context or self.by_id[constraint]["owner"]["@id"]
        holds = _bool(self.evaluate(body, start, values))
        return holds, self.text.get(body, "?"), values

    def compare(self, op, left, right):
        if isinstance(left, Quantity) and isinstance(right, Quantity):
            if left.unit == right.unit:
                left, right = left.number, right.number
            else:
                left, right = self.convert(left, right)
        elif isinstance(left, Quantity) or isinstance(right, Quantity):
            raise Unevaluable("a quantity compared with a plain value")
        try:
            return COMPARE[op](left, right)
        except TypeError as err:
            raise Unevaluable(f"cannot compare {left!r} {op} {right!r}") from err

    def convert(self, left, right):
        """Both numbers in base units; equal within rounding counts as equal."""
        (f, a), (g, b) = self.algebra(left.expression), self.algebra(right.expression)
        if a != b:
            raise Unevaluable(f"dimensions differ: {left.shown} and {right.shown}")
        if any(self.qualified(k) == KELVIN for k in a):
            # the library converts by factor only, as for temperature differences: no offset
            raise Unevaluable(f"temperatures in {left.shown} and {right.shown}")
        x, y = left.number * f, right.number * g
        return (x, x) if math.isclose(x, y, rel_tol=1e-9) else (x, y)


def _bool(value):
    if not isinstance(value, bool):
        raise Unevaluable(f"{value!r} is not a boolean")
    return value
