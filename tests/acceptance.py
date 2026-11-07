"""Acceptance test: build examples/vehicle, then break it in specific ways and check each break is caught.

Tools are taken from PATH, or from SYSML, SYSML2KIT, TEST_REPORTS, SPHINXBUILD (passed on to make).
Run: python tests/acceptance.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "vehicle"
TOOLS = {
    k: os.environ[k]
    for k in ("SYSML", "SYSML2KIT", "TEST_REPORTS", "SPHINXBUILD")
    if k in os.environ
}


def build(target, edit=None):
    """Copy the example, apply edit(project_dir), run make target; return (exit code, output, project dir)."""
    work = Path(tempfile.mkdtemp(prefix="sysml2kit-acc-")) / "vehicle"
    shutil.copytree(
        EXAMPLE, work, ignore=shutil.ignore_patterns("build", "_build", "_generated")
    )
    if edit:
        edit(work)
    args = ["make", "-C", str(work), target] + [f"{k}={v}" for k, v in TOOLS.items()]
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr, work


def replace(relpath, old, new):
    def edit(work):
        path = work / relpath
        text = path.read_text()
        assert old in text, f"{relpath}: {old!r} not found; the mutation is stale"
        path.write_text(text.replace(old, new, 1))

    return edit


# (description, make target, edit, regex the output must match)
MUTATIONS = [
    (
        "broken model reference fails lint",
        "lint",
        replace(
            "model/logical/architecture.sysml",
            "allocate operateVehicle.propel",
            "allocate operateVehicle.propell",
        ),
        r"propell` resolves to nothing",
    ),
    (
        "trace metadata to a missing customer requirement fails the build",
        "all",
        replace("docs/customer/requirements.rst", ":id: CRS-002", ":id: CRS-009"),
        r"unknown outgoing link 'CRS-002'",
    ),
    (
        "system requirement without a satisfying component violates sysreq-satisfied",
        "all",
        replace("model/logical/architecture.sysml", "satisfy curbMass by vehicle;", ""),
        r"sysreq-satisfied",
    ),
    (
        "use case performing no function violates usecase-realized",
        "all",
        replace(
            "model/requirements/use_cases.sysml",
            "perform operateVehicle.secureForTransport;",
            "",
        ),
        r"usecase-realized",
    ),
    (
        "unallocated leaf function violates function-allocated",
        "all",
        replace(
            "model/logical/architecture.sysml",
            "allocate operateVehicle.carryOccupants to vehicle.cabin;",
            "",
        ),
        r"function-allocated",
    ),
    (
        "system requirement without a test violates sysreq-verified",
        "all",
        replace(
            "model/verification/system_tests.sysml",
            "objective { verify tieDownPoints; }",
            "",
        ),
        r"sysreq-verified",
    ),
    (
        "test result for an unknown test case fails the build",
        "all",
        replace("test-results/junit.xml", 'value="STC-004"', 'value="STC-099"'),
        r"unknown outgoing link 'STC-099'",
    ),
    (
        "two diagrams ending in the same name fail instead of overwriting each other",
        "render",
        replace(
            "Makefile",
            "DIAGRAMS := VehicleLogical::vehicle",
            "DIAGRAMS := VehicleLogical::vehicle Other::vehicle",
        ),
        r"more than one entry ends in vehicle",
    ),
    (
        "a model file name with a space fails with what to rename",
        "lint",
        lambda work: (work / "model/my parts.sysml").write_text("package Spaced;\n"),
        r"must not contain spaces; rename: model/my parts\.sysml",
    ),
    (
        "satisfy end without a short name fails the bridge",
        "all",
        replace(
            "model/logical/architecture.sysml",
            "part <'LC-005'> chassis",
            "part chassis",
        ),
        r"has no short name",
    ),
]


def main():
    failures = 0
    code, out, work = build("all")
    if code != 0:
        print(f"FAIL baseline: make all exited {code}\n{out[-3000:]}")
        return 1
    html = (work / "docs/_build/html/model.html").read_text()
    checks = {
        "SR-003 shows its satisfying component": re.search(
            r'id="SR-003".*?satisfied by.*?LC-001', html, re.DOTALL
        ),
        "SR-003 shows its system test": re.search(
            r'id="SR-003".*?verified by.*?STC-003', html, re.DOTALL
        ),
        "internal diagrams are embedded": all(
            f"_images/{n}.svg" in html for n in ("vehicle", "operateVehicle")
        ),
        "use cases link to their needs": 'href="#UC-001"' in html,
        **links_resolve(work / "docs/_build/html"),
    }
    for name, ok in checks.items():
        print(f"{'ok  ' if ok else 'FAIL'} baseline: {name}")
        failures += not ok
    for name, target, edit, expected in MUTATIONS:
        code, out, _ = build(target, edit)
        ok = code != 0 and re.search(expected, out)
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures += 1
            print(f"     exit {code}; expected /{expected}/ in output:\n{out[-2000:]}")
    return 1 if failures + incremental(work) + hook(work) else 0


def links_resolve(html_dir):
    """The inlined trace graph links every box to an anchor that exists on its page."""
    page = (html_dir / "traceability.html").read_text()
    links = re.findall(
        r'<a href="([^"#]+\.html)#([^"]+)">\s*<rect class="s2k-box"', page
    )
    dead = [
        f"{doc}#{need}"
        for doc, need in links
        if f'id="{need}"' not in (html_dir / doc).read_text()
    ]
    return {
        f"trace graph links {len(links)} needs, none dead {dead}": len(links) > 20
        and not dead
    }


def report(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}")
    if not ok:
        print(f"     {detail[-2000:]}")
    return not ok


def incremental(work):
    """Deleting a file between two builds must take its needs out of the docs (make cannot see deletions)."""
    remake = ["make", "-C", str(work), "all"] + [f"{k}={v}" for k, v in TOOLS.items()]
    use_cases = work / "model/requirements/use_cases.sysml"
    original = use_cases.read_text()
    use_cases.write_text(
        original.replace("subject vehicle;", "subject car;")
    )  # every use case
    result = subprocess.run(remake, check=False, capture_output=True, text=True)
    out = result.stdout + result.stderr
    failed = report(
        "a renamed subject's old diagram is gone, so the page pointing at it fails",
        result.returncode != 0
        and "usecases-vehicle.svg" in out
        and "No such file or directory" in out,
        out,
    )
    use_cases.write_text(original)
    (work / "test-results/junit.xml").unlink()
    result = subprocess.run(remake, check=False, capture_output=True, text=True)
    stale = "testresult" in (work / "docs/_generated/results-needs.json").read_text()
    failed += report(
        "deleted test results disappear on rebuild",
        result.returncode == 0 and not stale,
        result.stdout + result.stderr,
    )
    (work / "model/verification/system_tests.sysml").unlink()
    result = subprocess.run(remake, check=False, capture_output=True, text=True)
    out = result.stdout + result.stderr
    return failed + report(
        "deleted model file fails the rebuild (sysreq-verified)",
        result.returncode != 0 and "sysreq-verified" in out,
        out,
    )


def hook(work):
    """The plugin's PostToolUse hook reports `sysml check` errors with exit code 2, and ignores other files."""
    script = EXAMPLE.parent.parent / "plugins/sysml-rflp/scripts/lint_on_edit.py"
    target = work / "model/logical/architecture.sysml"
    replace(
        "model/logical/architecture.sysml",
        "allocate operateVehicle.propel",
        "allocate operateVehicle.propell",
    )(work)

    def run(path):
        event = json.dumps(
            {"tool_name": "Edit", "tool_input": {"file_path": str(path)}}
        )
        return subprocess.run(
            [sys.executable, str(script)],
            input=event,
            check=False,
            capture_output=True,
            text=True,
        )

    broken, other = run(target), run(work / "docs/index.rst")
    failed = report(
        "lint hook reports a broken model with exit 2",
        broken.returncode == 2 and "propell` resolves to nothing" in broken.stderr,
        f"exit {broken.returncode}: {broken.stderr}",
    ) + report("lint hook ignores non-SysML files", other.returncode == 0, other.stderr)
    original = target.read_text().replace(
        "operateVehicle.propell", "operateVehicle.propel"
    )
    target.write_text(original)
    clean = run(target)
    failed += report(
        "lint hook passes a clean model", clean.returncode == 0, clean.stderr
    )
    target.write_text(original.replace("<'LC-005'> chassis", "<'LC-004'> chassis"))
    duplicate = run(target)
    failed += report(
        "lint hook reports a bridge error (duplicate id) that `sysml check` accepts",
        duplicate.returncode == 2 and "duplicate id LC-004" in duplicate.stderr,
        f"exit {duplicate.returncode}: {duplicate.stderr}",
    )
    target.write_text(original)
    requirements = work / "model/requirements/system_requirements.sysml"
    replace(
        "model/requirements/system_requirements.sysml",
        "shall not exceed 1800 kg",
        "shall be TBD",
    )(work)
    vague = run(requirements)
    return failed + report(
        "lint hook reports a vague requirement text",
        vague.returncode == 2 and "SR-003" in vague.stderr and "'TBD'" in vague.stderr,
        f"exit {vague.returncode}: {vague.stderr}",
    )


if __name__ == "__main__":
    sys.exit(main())
