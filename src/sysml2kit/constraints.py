"""Evaluate a constraint from the expression tree `sysml export` writes.

The standard parser has already resolved every name: a feature reference names its referent. This walks
the tree in a context (the constraint's owner, or a part that inherits it) and takes each referenced
feature's value from the nearest redefinition that context sees. It covers literals, `and`, `or`, `xor`,
`not`, comparisons, unary minus and quantities (`5 [N]`); anything else is reported as not evaluated,
never guessed. Quantities compare only in the same unit, the unit being the library element they name.
"""

import json
from collections import namedtuple

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
# unit: what identifies the unit (the library elements it names); shown: its text, for messages
Quantity = namedtuple("Quantity", "number unit shown")


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

    def __init__(self, elements):
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
            return Quantity(number, self.unit(args[1]), self.shown(args[1]).strip("'"))
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
            return _compare(op, arg(0), arg(1))
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


def _compare(op, left, right):
    if isinstance(left, Quantity) and isinstance(right, Quantity):
        if left.unit != right.unit:
            raise Unevaluable(f"units differ: {left.shown} and {right.shown}")
        left, right = left.number, right.number
    elif isinstance(left, Quantity) or isinstance(right, Quantity):
        raise Unevaluable("a quantity compared with a plain value")
    try:
        return COMPARE[op](left, right)
    except TypeError as err:
        raise Unevaluable(f"cannot compare {left!r} {op} {right!r}") from err


def _bool(value):
    if not isinstance(value, bool):
        raise Unevaluable(f"{value!r} is not a boolean")
    return value
