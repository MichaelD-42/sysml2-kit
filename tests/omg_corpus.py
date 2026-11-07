"""Run the OMG SysML-v2-Release corpus through the pipeline: check, export, bridge, use case renderer.

The OMG examples are valid SysML v2, so `sysml check` must be clean on each folder. They do not follow
our id conventions, so the bridge may refuse them (BridgeError) - but it must not crash.
Run: python tests/omg_corpus.py [path/to/SysML-v2-Release]   (clones the pinned tag when no path is given)
"""

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sysml2kit.needs import BridgeError, convert  # noqa: E402
from sysml2kit.render import use_case_svg, use_cases  # noqa: E402

RELEASE_TAG = "2026-09.1"
SYSML = os.environ.get("SYSML", "sysml")


def main():
    if len(sys.argv) > 1:
        release = Path(sys.argv[1])
    else:
        release = Path(tempfile.mkdtemp()) / "release"
        subprocess.run(
            [
                "git",
                "clone",
                "-q",
                "--depth",
                "1",
                "--branch",
                RELEASE_TAG,
                "https://github.com/Systems-Modeling/SysML-v2-Release.git",
                str(release),
            ],
            check=True,
        )
    failures = 0
    for folder in ("training", "validation", "examples"):
        root = release / "sysml" / "src" / folder
        check = subprocess.run(
            [SYSML, "--color", "never", "check", str(root)],
            capture_output=True,
            text=True,
        )
        summary = (
            check.stdout.strip().splitlines()[-1]
            if check.stdout.strip()
            else check.stderr.strip()
        )
        ok = check.returncode == 0
        print(f"{'ok  ' if ok else 'FAIL'} check {folder}: {summary}")
        failures += not ok
        files = sorted(str(p) for p in root.rglob("*.sysml"))
        export = subprocess.run(
            [SYSML, "export", *files], capture_output=True, text=True
        )
        if export.returncode != 0:
            print(f"FAIL export {folder}: {export.stderr[-500:]}")
            failures += 1
            continue
        elements = json.loads(export.stdout)
        try:
            needs = convert(elements, {})["versions"][""]["needs"]
            bridge = f"{len(needs)} needs"
        except BridgeError as err:
            bridge = f"refused ({len(str(err).splitlines())} findings)"
        diagrams = use_cases(elements)
        for subject, cases in diagrams:
            ET.fromstring(use_case_svg(subject, cases))  # must be well-formed
        print(
            f"ok   export/bridge/render {folder}: {len(elements)} elements, bridge {bridge}, {len(diagrams)} use case diagrams"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
