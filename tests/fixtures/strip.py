"""Drop the derived membership and feature lists from a `sysml export` fixture; the evaluator never reads them.

python tests/fixtures/strip.py tests/fixtures/<name>.json
"""

import json
import sys

DERIVED = {
    "membership",
    "member",
    "inheritedMembership",
    "inheritedFeature",
    "feature",
    "featureMembership",
    "importedMembership",
    "input",
    "output",
    "directedFeature",
}

for path in sys.argv[1:]:
    with open(path) as f:
        elements = json.load(f)
    for e in elements:
        for key in DERIVED & e.keys():
            del e[key]
    with open(path, "w") as f:
        json.dump(elements, f, separators=(",", ":"), ensure_ascii=False)
