"""Evaluate a constraint against the attribute values its owner states.

`sysml export` gives a constraint's body only as text, so this parses the small expression language
the kit's constraints use: `and`, `or`, `not`, comparisons, numbers with a unit in brackets, strings,
booleans and feature chains (`a.b`). Anything else is reported as not evaluated, never guessed.
"""

import json
import re

TOKEN = re.compile(
    r"\s*(?:(?P<num>\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
    r'|(?P<str>"(?:\\.|[^"\\])*")'
    r"|(?P<unit>\[[^\]]*\])"
    r"|(?P<name>'[^']*'|[A-Za-z_]\w*)"
    r"|(?P<op>==|!=|<=|>=|[<>()\.-]))"
)
COMPARE = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


class Unevaluable(Exception):
    pass


def tokens(text):
    out, pos = [], 0
    text = text.rstrip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Unevaluable(f"cannot read {text[pos:].strip()!r}")
        out.append((m.lastgroup, m.group(m.lastgroup)))
        pos = m.end()
    return out


def evaluate(text, lookup):
    """True or False; `lookup(chain)` gives the value text of a feature chain or raises Unevaluable."""
    result = _Parser(tokens(text), lookup).run()
    if not isinstance(result, bool):
        raise Unevaluable(f"{text!r} is not a boolean")
    return result


class _Parser:
    def __init__(self, toks, lookup, depth=0):
        self.toks, self.i, self.lookup, self.depth = toks, 0, lookup, depth

    def run(self):
        value = self.or_()
        if self.i < len(self.toks):
            raise Unevaluable(f"unexpected {self.toks[self.i][1]!r}")
        return value

    def peek(self, *values):
        return self.i < len(self.toks) and self.toks[self.i][1] in values

    def take(self):
        if self.i >= len(self.toks):
            raise Unevaluable("unexpected end")
        self.i += 1
        return self.toks[self.i - 1]

    def or_(self):
        value = self.and_()
        while self.peek("or"):
            self.take()
            value = _bool(value) | _bool(self.and_())
        return value

    def and_(self):
        value = self.not_()
        while self.peek("and"):
            self.take()
            value = _bool(value) & _bool(self.not_())
        return value

    def not_(self):
        if self.peek("not"):
            self.take()
            return not _bool(self.not_())
        return self.compare()

    def compare(self):
        left = self.primary()
        if not self.peek(*COMPARE):
            return left
        op = self.take()[1]
        right = self.primary()
        if isinstance(left, tuple) and isinstance(right, tuple):
            if left[1] != right[1]:
                raise Unevaluable(f"units differ: {left[1]} and {right[1]}")
            left, right = left[0], right[0]
        elif isinstance(left, tuple) or isinstance(right, tuple):
            raise Unevaluable("a quantity compared with a plain value")
        try:
            return COMPARE[op](left, right)
        except TypeError as err:
            raise Unevaluable(f"cannot compare {left!r} {op} {right!r}") from err

    def primary(self):
        kind, text = self.take()
        if text == "(":
            value = self.or_()
            if not self.peek(")"):
                raise Unevaluable("missing )")
            self.take()
            return value
        if text == "-":
            value = self.primary()
            if isinstance(value, tuple):
                return (-value[0], value[1])
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise Unevaluable("minus before a non-number")
            return -value
        if kind == "num":
            return self.unit(float(text) if re.search(r"[.eE]", text) else int(text))
        if kind == "str":
            return re.sub(r"\\(.)", r"\1", text[1:-1])
        if kind == "name" and text in ("true", "false"):
            return text == "true"
        if kind == "name" and text not in ("and", "or", "not"):
            chain = [text.strip("'")]
            while self.peek("."):
                self.take()
                k, t = self.take()
                if k != "name":
                    raise Unevaluable(f"unexpected {t!r} in a feature chain")
                chain.append(t.strip("'"))
            if self.depth > 5:
                raise Unevaluable("values refer to each other too deeply")
            return self.unit(
                _Parser(
                    tokens(self.lookup(tuple(chain))), self.lookup, self.depth + 1
                ).run()
            )
        raise Unevaluable(f"unexpected {text!r}")

    def unit(self, value):
        if self.i < len(self.toks) and self.toks[self.i][0] == "unit":
            if isinstance(value, (tuple, bool, str)):
                raise Unevaluable("a unit after a non-number")
            return (value, re.sub(r"\s+", "", self.take()[1][1:-1]))
        return value


def _bool(value):
    if not isinstance(value, bool):
        raise Unevaluable(f"{value!r} is not a boolean")
    return value


SPECIALIZATIONS = (
    "Subsetting",
    "Redefinition",
    "ReferenceSubsetting",
    "Subclassification",
    "FeatureTyping",
)


class Model:
    """Name lookup and attribute values over `sysml export` elements."""

    def __init__(self, elements):
        self.by_id = {e["@id"]: e for e in elements}
        self.children, self.generals, self.specifics = {}, {}, {}
        self.text, self.results = {}, {}
        for e in elements:
            owner = (e.get("owner") or {}).get("@id")
            if owner and e.get("name") and not e["@type"].endswith("Membership"):
                self.children.setdefault(owner, []).append(e["@id"])
            if e["@type"] in SPECIALIZATIONS:
                specific = (e.get("specific") or {}).get("@id")
                general = (e.get("general") or {}).get("@id")
                if specific and general:
                    self.generals.setdefault(specific, []).append(general)
                    self.specifics.setdefault(general, []).append(specific)
            if e["@type"] == "ResultExpressionMembership":
                # a relationship's owner is its owningRelatedElement; sysml 0.1.4 also wrote `owner`
                constraint = (
                    e.get("owningRelatedElement") or e.get("owner") or {}
                ).get("@id")
                if constraint:
                    self.results[constraint] = e
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

    def feature(self, context, name):
        """The nearest feature called `name` that context owns or inherits."""
        for element in self.closure(context):
            for child in self.children.get(element, []):
                if self.by_id[child].get("name") == name:
                    return child
        raise Unevaluable(f"{name} not found")

    def value(self, feature):
        """The text of the nearest value the feature or what it redefines states."""
        for element in self.closure(feature):
            for rel in self.by_id.get(element, {}).get("ownedRelationship") or []:
                fv = self.by_id.get(rel["@id"], {})
                if fv.get("@type") == "FeatureValue" and fv.get("value"):
                    body = self.literal(fv["value"]["@id"])
                    if body:
                        return body
        raise Unevaluable(f"{self.by_id[feature].get('name')} has no value")

    def literal(self, expression):
        """Text of a value expression; a bare literal carries no textual representation."""
        e = self.by_id.get(expression, {})
        if e.get("@type") == "LiteralString":
            return json.dumps(e["value"])
        if e.get("@type") == "LiteralBoolean":
            return "true" if e["value"] else "false"
        if e.get("@type") in ("LiteralInteger", "LiteralRational"):
            return str(e["value"])
        return self.text.get(expression)

    def body(self, constraint):
        membership = self.results.get(constraint, {})
        for owned in membership.get("ownedRelatedElement") or []:
            if owned["@id"] in self.text:
                return self.text[owned["@id"]]
        raise Unevaluable("no body")

    def contexts(self, constraint):
        """Where the constraint applies: its owner and everything that specializes the owner, as a
        specialization inherits its general's features; not where a nearer constraint redefines it."""
        owner = self.by_id[constraint]["owner"]["@id"]
        name = self.by_id[constraint].get("name")
        return [
            c
            for c in self.closure(owner, self.specifics)
            if not name or self.feature(c, name) == constraint
        ]

    def check(self, constraint, context=None):
        """(holds, text, {chain: value text}) for a constraint in a context, by default its owner."""
        text = self.body(constraint)
        start = context or self.by_id[constraint]["owner"]["@id"]
        values = {}

        def lookup(chain):
            context = start
            for name in chain:
                context = self.feature(context, name)
            values[".".join(chain)] = self.value(context)
            return values[".".join(chain)]

        return evaluate(text, lookup), text, values
