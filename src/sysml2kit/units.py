"""The standard library's measurement units as a table: each unit's factor and powers of base units.

A model export leaves the library out (with it, it is near 1 GB), so the bridge reads the library's
units from this table. `python -m sysml2kit.units [sysml]` regenerates it from the library the given
`sysml` carries, by the library's own definitions (`unitConversion`, unit expressions); element ids
are derived from qualified names, so they match the ids a model export refers to.
"""

import json
import subprocess
import sys
import tempfile
from importlib import resources
from pathlib import Path

TABLE = "units.json"
# what the evaluator reads; the rest (derived memberships, mostly) is dropped while reading
KEEP = {
    "@id",
    "@type",
    "owner",
    "owningRelatedElement",
    "ownedRelatedElement",
    "ownedRelationship",
    "ownedElement",
    "name",
    "qualifiedName",
    "specific",
    "general",
    "value",
    "referent",
    "operator",
    "body",
    "representedElement",
}


def table():
    """{unit @id: {"name", "factor", "base": {base unit @id: exponent}}}"""
    return json.loads(resources.files("sysml2kit").joinpath(TABLE).read_text())


def elements(path):
    """The export's elements one at a time, with only the keys in KEEP."""
    text = Path(path).read_text(encoding="utf-8")
    decoder, i = json.JSONDecoder(), text.index("[") + 1
    while True:
        while text[i] in " \t\r\n,":
            i += 1
        if text[i] == "]":
            return
        element, i = decoder.raw_decode(text, i)
        yield {k: v for k, v in element.items() if k in KEEP}


def generate(sysml="sysml"):
    from sysml2kit.constraints import Model, Unevaluable
    from sysml2kit.needs import normalize

    with tempfile.TemporaryDirectory() as tmp:
        source, out = Path(tmp) / "empty.sysml", Path(tmp) / "library.json"
        source.write_text("package UnitsTable;\n")
        subprocess.run(
            [sysml, "export", "--include-library", str(source), "-o", str(out)],
            check=True,
            capture_output=True,
        )
        model = Model(normalize(list(elements(out))), units={})
    units = {}
    for unit in model.measurement_units():
        try:
            factor, base = model.reduce(unit)
        except Unevaluable:
            continue  # a unit the library defines by something other than a conversion or unit expression
        units[unit] = {"name": model.qualified(unit), "factor": factor, "base": base}
    return dict(sorted(units.items(), key=lambda kv: kv[1]["name"]))


if __name__ == "__main__":
    units = generate(*sys.argv[1:2])
    path = Path(__file__).with_name(TABLE)
    path.write_text(json.dumps(units, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(units)} units -> {path}")
