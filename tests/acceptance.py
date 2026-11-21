"""Acceptance test: build examples/edrive-platform and examples/vehicle, then break them in specific ways and check each break is caught.

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
PLATFORM = EXAMPLE.parent / "edrive-platform"
TOOLS = {
    k: os.environ[k]
    for k in ("SYSML", "SYSML2KIT", "TEST_REPORTS", "SPHINXBUILD")
    if k in os.environ
}


def build(target, edit=None, example=EXAMPLE):
    """Copy the example, apply edit(project_dir), run make target; return (exit code, output, project dir)."""
    work = Path(tempfile.mkdtemp(prefix="sysml2kit-acc-")) / example.name
    shutil.copytree(
        example, work, ignore=shutil.ignore_patterns("build", "_build", "_generated")
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
PLATFORM_MUTATIONS = [
    (
        "platform: a physical part without its domain keyword fails the bridge",
        "all",
        replace(
            "model/physical/components.sysml",
            "#Mechanical part <'EDU-PC-006'> housing",
            "part <'EDU-PC-006'> housing",
        ),
        r"EDU-PC-006: a logical component's id starts with LC-",
    ),
]

MUTATIONS = [
    (
        "broken model reference fails lint",
        "lint",
        replace(
            "model/logical/architecture.sysml",
            "allocate propulsion.propel",
            "allocate propulsion.propell",
        ),
        r"propell::convertPower` resolves to nothing",
    ),
    (
        "trace metadata to a missing customer requirement fails the build",
        "all",
        replace("docs/customer/requirements.md", ":id: CRS-002", ":id: CRS-009"),
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
            "perform trailerTransport;",
            "",
        ),
        r"usecase-realized",
    ),
    (
        "unallocated leaf function violates function-allocated",
        "all",
        replace(
            "model/logical/architecture.sysml",
            "allocate occupantSeating.carryOccupants to vehicle.cabin;",
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
    (
        "a commercial requirement without its compliance statement is not answered",
        "all",
        lambda work: (work / "docs/customer/statements.md").write_text(
            "# Compliance statements\n"
        ),
        r"CRS-004: not answered",
    ),
    (
        "a commercial requirement not marked as such must have a system requirement",
        "all",
        replace("docs/customer/requirements.md", ":scope: commercial\n", ""),
        r"CRS-004.*\n.*\n.*\n.*crs-satisfied",
    ),
    (
        "a customer requirement without a class violates crs-class",
        "all",
        replace("docs/customer/requirements.md", ":class: functional\n", ""),
        r"CRS-001\n\s+Schema path:\s+crs-class",
    ),
    (
        "a constraint satisfying no requirement violates constraint-satisfies",
        "all",
        replace(
            "docs/customer/requirements.md",
            "whichever comes first.\n:::\n",
            "whichever comes first.\n:::\n\n:::{constraint} Unused limit\n:id: CON-099\n\nA limit.\n:::\n",
        ),
        r"CON-099 > satisfies\n\s+Schema path:\s+constraint-satisfies",
    ),
    (
        "a compliance statement without a compliance value violates cst-compliance",
        "all",
        replace("docs/customer/statements.md", ":compliance: comply\n", ""),
        r"cst-compliance",
    ),
    (
        "leaf logical component without a physical component violates logical-allocated",
        "all",
        replace(
            "model/physical/components.sysml", "allocate vehicle.cabin to body;", ""
        ),
        r"logical-allocated",
    ),
    (
        "partial match without its gap system requirement fails the compliance table",
        "all",
        replace(
            "model/requirements/system_requirements.sysml",
            '@Satisfies { need = "CRS-003"; }',
            "",
        ),
        r"CRS-003: partial match without a system requirement stating the gap",
    ),
    (
        "a customer requirement without an acceptance test is not verified",
        "all",
        replace(
            "docs/acceptance/tests.rst",
            ":verifies: CRS-003, UC-001",
            ":verifies: UC-001",
        ),
        r"CRS-003: not verified \(no acceptance test, no implemented CTR applying to it\)",
    ),
    (
        "a feature without its #Feature keyword fails the bridge",
        "all",
        replace(
            "model/functional/features.sysml",
            "#Feature action <'FEAT-002'> propulsion",
            "action <'FEAT-002'> propulsion",
        ),
        r"FEAT-002: a function's id starts with F-",
    ),
]


def mutations(cases, example):
    failures = 0
    for name, target, edit, expected in cases:
        code, out, _ = build(target, edit, example)
        ok = code != 0 and re.search(expected, out)
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures += 1
            print(f"     exit {code}; expected /{expected}/ in output:\n{out[-2000:]}")
    return failures


def platform():
    """The e-drive product line builds clean on its own (PRQ in the CRS role), and a break is caught."""
    code, out, _ = build("all", example=PLATFORM)
    failed = report("platform baseline: make all", code == 0, out)
    return failed + mutations(PLATFORM_MUTATIONS, PLATFORM)


def main():
    # the platform reports on its own, so a broken vehicle build does not hide its result
    failures = platform()
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
            f"_images/{n}.svg" in html for n in ("vehicle", "propulsion")
        ),
        "use cases link to their needs": 'href="#UC-001"' in html,
        **compliance_rows(work / "docs/_generated/compliance.md"),
        **links_resolve(work / "docs/_build/html"),
    }
    for name, ok in checks.items():
        print(f"{'ok  ' if ok else 'FAIL'} baseline: {name}")
        failures += not ok
    failures += mutations(MUTATIONS, EXAMPLE)
    failures += information()
    return 1 if failures + incremental(work) + hook(work) else 0


def information():
    """An information CRS is no coverage obligation: no SR, a partial match without a gap SR, still green."""

    def edit(work):
        replace(
            "docs/customer/requirements.md",
            ":class: non-functional\n",
            ":class: information\n",
        )(work)
        replace(
            "model/requirements/system_requirements.sysml",
            '@Satisfies { need = "CRS-003"; }',
            '@Satisfies { need = "CRS-001"; }',
        )(work)

    code, out, _ = build("all", edit)
    return report(
        "an information requirement without a system requirement builds clean",
        code == 0,
        out,
    )


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


def compliance_rows(table):
    """The compliance table has a variant, a new, a partial and a statement-only row."""
    text = table.read_text() if table.exists() else ""
    rows = text.split("\n\n")[0].splitlines()[
        2:
    ]  # the requirements table, not the CTR one
    cells = [[c.strip() for c in row.strip("|").split("|")] for row in rows]
    return {
        f"compliance table has a {kind} row": any(test(c) for c in cells)
        for kind, test in {
            "variant": lambda c: c[4] == "variant",
            "new": lambda c: c[4] == "new",
            "partial": lambda c: c[5] == "yes",
            "statement-only": lambda c: not c[3] and "CST-001" in c[6],
        }.items()
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
        "allocate propulsion.propel",
        "allocate propulsion.propell",
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
        broken.returncode == 2
        and "propell::convertPower` resolves to nothing" in broken.stderr,
        f"exit {broken.returncode}: {broken.stderr}",
    ) + report("lint hook ignores non-SysML files", other.returncode == 0, other.stderr)
    original = target.read_text().replace("propulsion.propell", "propulsion.propel")
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
