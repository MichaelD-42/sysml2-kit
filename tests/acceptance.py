"""Acceptance test: build examples/window-switch-platform and examples/window-switch-rfq, then break them in specific ways and check each break is caught.

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
from contextlib import contextmanager
from pathlib import Path

from sysml2kit.needs import platform_dir

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "window-switch-rfq"
PLATFORM = EXAMPLE.parent / "window-switch-platform"
TOOLS = {
    k: os.environ[k]
    for k in ("SYSML", "SYSML2KIT", "TEST_REPORTS", "SPHINXBUILD")
    if k in os.environ
}


@contextmanager
def build(target, edit=None, example=EXAMPLE):
    """Copy the example, apply edit(project_dir), run make target; yield (exit code, output, project dir), then remove the copy."""
    ignore = shutil.ignore_patterns("build", "_build", "_generated")
    with tempfile.TemporaryDirectory(prefix="sysml2kit-acc-") as tmp:
        work = Path(tmp) / example.name
        shutil.copytree(example, work, ignore=ignore)
        # a platform the Makefile names beside the project is copied to the same place beside the copy
        platform = platform_dir(example).resolve()
        if platform.is_dir() and not platform.is_relative_to(example.resolve()):
            shutil.copytree(
                platform,
                (work / os.path.relpath(platform, example)).resolve(),
                ignore=ignore,
            )
        if edit:
            edit(work)
        args = ["make", "-C", str(work), target]
        args += [f"{k}={v}" for k, v in TOOLS.items()]
        result = subprocess.run(args, check=False, capture_output=True, text=True)
        yield result.returncode, result.stdout + result.stderr, work


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
            "#Mechanical part <'WSW-PC-003'> seal",
            "part <'WSW-PC-003'> seal",
        ),
        r"WSW-PC-003: a logical component's id starts with LC-",
    ),
    (
        "platform: a SW component without a logical component violates swcomponent-used",
        "all",
        replace(
            "model/physical/components.sysml",
            "    allocate ACME_WindowSwitch.illumination to switchFirmware.illuminationControl;\n",
            "",
        ),
        r"Need path:\s+WSW-PC-023\b.*\n\s+Schema path:\s+swcomponent-used",
    ),
    (
        "platform: a rated value outside the platform's own limit fails the bridge",
        "all",
        replace(
            "model/physical/components.sysml",
            "durabilityCycles : Integer = 100000",
            "durabilityCycles : Integer = 90000",
        ),
        r"WSW-CON-002: does not hold",
    ),
]

MUTATIONS = [
    (
        "broken model reference fails lint",
        "lint",
        replace(
            "model/physical/components.sysml",
            "driverDoorSwitch.driverKeyModule;",
            "driverDoorSwitch.driverKeyModul;",
        ),
        r"driverKeyModul` resolves to nothing",
    ),
    (
        "trace metadata to a missing customer requirement fails the build",
        "all",
        replace("docs/customer/requirements.md", ":id: CRS-402", ":id: CRS-999"),
        r"unknown outgoing link 'CRS-402'",
    ),
    (
        "system requirement without a satisfying component violates sysreq-satisfied",
        "all",
        replace(
            "model/logical/architecture.sysml",
            "satisfy partNumberLabel by OEM_WindowSwitch.enclosure;",
            "",
        ),
        r"Need path:\s+SR-106\b.*\n\s+Schema path:\s+sysreq-satisfied",
    ),
    (
        "use case performing no function violates usecase-realized",
        "all",
        replace(
            "model/requirements/use_cases.sysml",
            "        perform nightDesign;\n    }\n}",
            "    }\n}",
        ),
        r"Need path:\s+UC-103\b.*\n\s+Schema path:\s+usecase-realized",
    ),
    (
        "unallocated leaf function violates function-allocated",
        "all",
        replace(
            "model/functional/features.sysml",
            "        doc /* Two-stage window keys, four in the driver door and one in the passenger door. */\n",
            "        doc /* Two-stage window keys, four in the driver door and one in the passenger door. */\n"
            "        action <'F-199'> offerExtraKey;\n",
        ),
        r"Need path:\s+F-199\b.*\n\s+Schema path:\s+function-allocated",
    ),
    (
        "system requirement without a test violates sysreq-verified",
        "all",
        replace(
            "model/verification/system_tests.sysml",
            "objective { verify childLockTelltale; }",
            "",
        ),
        r"Need path:\s+SR-102\b.*\n\s+Schema path:\s+sysreq-verified",
    ),
    (
        "test result for an unknown test case fails the build",
        "all",
        replace("test-results/junit.xml", 'value="STC-104"', 'value="STC-199"'),
        r"unknown outgoing link 'STC-199'",
    ),
    (
        "two diagrams ending in the same name fail instead of overwriting each other",
        "render",
        replace(
            "Makefile",
            "DIAGRAMS := WindowSwitchRfqPhysical::vehicleDoorSwitches",
            "DIAGRAMS := WindowSwitchRfqPhysical::vehicleDoorSwitches Other::vehicleDoorSwitches",
        ),
        r"more than one entry ends in vehicleDoorSwitches",
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
            "part <'LC-100'> OEM_WindowSwitch",
            "part OEM_WindowSwitch",
        ),
        r"OEM_WindowSwitch has no short name",
    ),
    (
        "a commercial requirement without its compliance statement is not answered",
        "all",
        replace("docs/customer/statements.md", ":answers: CRS-901\n", ""),
        r"CRS-901: not answered",
    ),
    (
        "a commercial requirement not marked as such must have a system requirement",
        "all",
        replace("docs/customer/requirements.md", ":scope: commercial\n", ""),
        r"Need path:\s+CRS-901\b.*\n\s+Schema path:\s+crs-satisfied",
    ),
    (
        "a customer requirement without a class violates crs-class",
        "all",
        replace("docs/customer/requirements.md", ":class: functional\n", ""),
        r"Need path:\s+CRS-201\b.*\n\s+Schema path:\s+crs-class",
    ),
    (
        "a constraint satisfying no requirement violates constraint-satisfies",
        "all",
        replace(
            "docs/customer/requirements.md",
            "whichever comes first.\n:::\n",
            "whichever comes first.\n:::\n\n:::{constraint} Unused limit\n:id: CON-199\n\nA limit.\n:::\n",
        ),
        r"Need path:\s+CON-199\b.*\n\s+Schema path:\s+constraint-satisfies",
    ),
    (
        "a compliance statement without a compliance value violates cst-compliance",
        "all",
        replace("docs/customer/statements.md", ":compliance: comply\n", ""),
        r"Need path:\s+CST-002\b.*\n\s+Schema path:\s+cst-compliance",
    ),
    (
        "leaf logical component without a physical component violates logical-allocated",
        "all",
        replace(
            "model/logical/architecture.sysml",
            "The vehicle's window switch as a whole. */\n",
            "The vehicle's window switch as a whole. */\n        part <'LC-199'> extraUnit;\n",
        ),
        r"Need path:\s+LC-199\b.*\n\s+Schema path:\s+logical-allocated",
    ),
    (
        "a platform variation the project selects no variant of fails the compliance table",
        "all",
        lambda work: (work / "model/physical/components.sysml").write_text(
            re.sub(
                r":> WindowSwitchPhysical::keyModule::\w+",
                ":> WindowSwitchPhysical::keyModule",
                (work / "model/physical/components.sysml").read_text(),
            )
        ),
        r"CRS-201: variation WSW-PC-004 reached without a selected variant",
    ),
    (
        "partial match without a system requirement stating what is met fails the compliance table",
        "all",
        replace(
            "model/requirements/system_requirements.sysml",
            '        @Satisfies { need = "CRS-203"; }\n',
            "",
        ),
        r"CRS-203: partial match without a system requirement stating what is met",
    ),
    (
        "a matched requirement's system requirement satisfied outside the feature's chain fails the compliance table",
        "all",
        replace(
            "model/logical/architecture.sysml",
            "satisfy windowKeyStages by OEM_WindowSwitch.keySensing;",
            "satisfy windowKeyStages by OEM_WindowSwitch.illumination;",
        ),
        r"CRS-201: system requirement SR-101 is satisfied outside the chain of its matching features",
    ),
    (
        "a constraint its part's values break fails the bridge",
        "all",
        replace("model/physical/components.sysml", "mass <= 50 [g]", "mass <= 40 [g]"),
        r"CON-108: does not hold: mass <= 40 \[g\] \(mass = 42 \[g\]\)",
    ),
    (
        "two door positions coded to one node address break the vehicle's constraint",
        "all",
        replace("model/physical/components.sysml", "nad = 43;", "nad = 42;"),
        r"CON-109: does not hold",
    ),
    (
        "a platform rating that no longer meets this RFQ's limit fails the bridge",
        "all",
        replace(
            "../window-switch-platform/model/physical/components.sysml",
            "mass : MassValue = 42 [g]",
            "mass : MassValue = 55 [g]",
        ),
        r"CON-108: does not hold: mass <= 50 \[g\] \(mass = 55 \[g\]\)",
    ),
    (
        "partial constraint satisfaction without a partial compliance statement fails the compliance table",
        "all",
        replace(
            "docs/customer/statements.md",
            ":answers: CRS-302\n:compliance: partial",
            ":answers: CRS-302\n:compliance: comply",
        ),
        r"CRS-302: partial, but no partial compliance statement answers it",
    ),
    (
        "a customer requirement without an acceptance test is not verified",
        "all",
        replace(
            "docs/acceptance/tests.md",
            ":verifies: CRS-201, CRS-202, CRS-401",
            ":verifies: CRS-201, CRS-401",
        ),
        r"CRS-202: not verified \(no acceptance test, no implemented CTR applying to it\)",
    ),
    (
        "a feature without its #Feature keyword fails the bridge",
        "all",
        replace(
            "model/functional/features.sysml",
            "#Feature action <'FEAT-102'> childLock",
            "action <'FEAT-102'> childLock",
        ),
        r"FEAT-102: a function's id starts with F-",
    ),
    (
        "a customer test requirement without an implementing test violates ctr-implemented",
        "all",
        replace(
            "model/verification/system_tests.sysml",
            '@Implements { need = "CTR-002"; }',
            "",
        ),
        r"Need path:\s+CTR-002\b.*\n\s+Schema path:\s+ctr-implemented",
    ),
    (
        "a non-functional requirement whose constraint is a bare attribute is not answered (crs-satisfied)",
        "all",
        replace(
            "model/physical/components.sysml",
            "constraint <'CON-107'> quiescentCurrentLimit {\n"
            '            @Satisfies { need = "CRS-504"; }\n'
            "            doc /* With the LIN bus asleep, the switch shall draw at most 100 µA. */\n"
            "            quiescentCurrent <= 0.0001 [A]\n"
            "        }",
            "attribute quiescentCurrentLimit = 0.0001 [A];",
        ),
        r"CRS-504: not answered[\s\S]*Need path:\s+CRS-504\b.*\n\s+Schema path:\s+crs-satisfied",
    ),
    (
        "an acceptance test verifying and implementing nothing violates acctest-verifies",
        "all",
        replace("docs/acceptance/tests.md", ":implements: CTR-004\n", ""),
        r"Need path:\s+ATC-104\b.*\n\s+Schema path:\s+acctest-verifies",
    ),
    (
        "a system test implementing no customer test requirement violates systest-implements",
        "all",
        replace(
            "model/verification/system_tests.sysml",
            '@Implements { need = "CTR-003"; }',
            '@Implements { need = "CRS-503"; }',
        ),
        r"Need path:\s+STC-104\b.*\n\s+Schema path:\s+systest-implements",
    ),
    (
        "a constraint without a system test violates constraint-verified",
        "all",
        replace(
            "model/verification/system_tests.sysml",
            '@Verifies { need = "CON-112"; }',
            "",
        ),
        r"Need path:\s+CON-112\b.*\n\s+Schema path:\s+constraint-verified",
    ),
    (
        "a commercial customer test requirement with a test but no statement is not answered",
        "all",
        replace(
            "docs/customer/test-requirements.md",
            ":id: CTR-005\n",
            ":id: CTR-005\n:scope: commercial\n",
        ),
        r"CTR-005: not answered",
    ),
    (
        "an RFQ feature specializing a platform feature fails the bridge",
        "all",
        replace(
            "model/functional/features.sysml",
            # another platform feature, so no inherited function name collides with the RFQ's own
            "#Feature action <'FEAT-103'> nightDesign {",
            "#Feature action <'FEAT-103'> nightDesign :> WindowSwitchFeatures::childLock {",
        ),
        r"FEAT-103: specializes the platform's WSW-FEAT-002",
    ),
    (
        "#Modified on a part of its own fails the bridge",
        "all",
        replace(
            "model/physical/components.sysml",
            "#Mechanical part <'PC-113'>",
            "#Mechanical #Modified part <'PC-113'>",
        ),
        r"PC-113: #Modified needs a platform part to modify",
    ),
]


def mutations(cases, example):
    failures = 0
    for name, target, edit, expected in cases:
        with build(target, edit, example) as (code, out, _):
            ok = code != 0 and re.search(expected, out)
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures += 1
            print(f"     exit {code}; expected /{expected}/ in output:\n{out[-2000:]}")
    return failures


def platform():
    """The window-switch product line builds clean on its own (PRQ in the CRS role), and a break is caught."""
    with build("all", example=PLATFORM) as (code, out, _):
        failed = report("platform baseline: make all", code == 0, out)
    return failed + mutations(PLATFORM_MUTATIONS, PLATFORM)


def main():
    # the platform reports on its own, so a broken RFQ build does not hide its result
    failures = platform()
    with build("all") as (code, out, work):
        if code != 0:
            print(f"FAIL baseline: make all exited {code}\n{out[-3000:]}")
            return 1
        html = (work / "docs/_build/html/model.html").read_text()
        checks = {
            "SR-106 shows its satisfying component": re.search(
                r'id="SR-106".*?satisfied by.*?LC-106', html, re.DOTALL
            ),
            "SR-106 shows its system test": re.search(
                r'id="SR-106".*?verified by.*?STC-111', html, re.DOTALL
            ),
            "internal diagrams are embedded": "_images/vehicleDoorSwitches.svg" in html,
            "use cases link to their needs": 'href="#UC-101"' in html,
            "a use case is titled by its objective": "The occupant wants to open or close a window"
            in html,
            **compliance_rows(work / "docs/_generated/compliance.md"),
            **links_resolve(work / "docs/_build/html"),
        }
        for name, ok in checks.items():
            print(f"{'ok  ' if ok else 'FAIL'} baseline: {name}")
            failures += not ok
        failures += mutations(MUTATIONS, EXAMPLE)
        failures += information()
        failures += all_new()
        return 1 if failures + incremental(work) + hook(work) else 0


def information():
    """An information CRS is no coverage obligation: a partial satisfaction without a partial statement, still green."""

    def edit(work):
        replace(
            "docs/customer/requirements.md",
            ":id: CRS-302\n:class: non-functional\n",
            ":id: CRS-302\n:class: information\n",
        )(work)
        replace(
            "docs/customer/statements.md",
            ":answers: CRS-302\n:compliance: partial",
            ":answers: CRS-302\n:compliance: comply",
        )(work)

    with build("all", edit) as (code, out, _):
        return report(
            "an information requirement met in part without a partial statement builds clean",
            code == 0,
            out,
        )


def all_new():
    """A component realized by new parts only is new in the realization table, and the build stays green."""

    def edit(work):
        path = work / "model/physical/components.sysml"
        text = path.read_text()
        for target in (
            "WindowSwitchPhysical::housing;",
            "WindowSwitchPhysical::seal;",
            "oemWindowSwitch.oemKeyCaps;",
        ):
            text = text.replace(f"    allocate OEM_WindowSwitch.enclosure to {target}\n", "")
        # the modified caps go too, or they would be a part without a logical component
        text = re.sub(r"        #Mechanical #Modified part <'PC-112'>.*?\n        \}\n", "", text, flags=re.DOTALL)
        path.write_text(text)

    with build("all", edit) as (code, out, work):
        table = (work / "docs/_generated/compliance.md").read_text() if code == 0 else ""
        return report(
            "a component realized by new parts only is new",
            re.search(r"^\| \{need\}`LC-106` \| enclosure \| new \|", table, re.MULTILINE),
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
    """The compliance table has a full, a partial-reuse, a partial and a statement-only row; the realization
    table shows the enclosure partly realized by a modified and a new part."""
    text = table.read_text() if table.exists() else ""
    rows = text.split("\n\n")[0].splitlines()[
        2:
    ]  # the requirements table, not the CTR one
    cells = [[c.strip() for c in row.strip("|").split("|")] for row in rows]
    enclosure = re.search(r"^\| \{need\}`LC-106` .*$", text, re.MULTILINE)
    return {
        "realization table: LC-106 partial, modified PC-112, new PC-113": bool(enclosure)
        and "| partial |" in enclosure[0]
        and "`PC-112` oemKeyCaps (modified WSW-PC-002)" in enclosure[0]
        and "`PC-113` partNumberLabel (new)" in enclosure[0],
        **{
            f"compliance table has a {kind} row": any(test(c) for c in cells)
        for kind, test in {
            "full": lambda c: c[4] == "full",
            "partial reuse": lambda c: c[4] == "partial",
            "partial": lambda c: c[5] == "yes",
            "statement-only": lambda c: not c[3] and "CST-001" in c[6],
            }.items()
        },
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
        original.replace("subject OEM_WindowSwitch :>", "subject switches :>")
    )  # every use case
    result = subprocess.run(remake, check=False, capture_output=True, text=True)
    out = result.stdout + result.stderr
    failed = report(
        "a renamed subject's old diagram is gone, so the page pointing at it fails",
        result.returncode != 0
        and "usecases-OEM_WindowSwitch.svg" in out
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
    target = work / "model/physical/components.sysml"
    replace(
        "model/physical/components.sysml",
        "driverDoorSwitch.driverKeyModule;",
        "driverDoorSwitch.driverKeyModul;",
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
        and "driverKeyModul` resolves to nothing" in broken.stderr,
        f"exit {broken.returncode}: {broken.stderr}",
    ) + report("lint hook ignores non-SysML files", other.returncode == 0, other.stderr)
    original = target.read_text().replace("driverKeyModul;", "driverKeyModule;")
    target.write_text(original)
    clean = run(target)
    failed += report(
        "lint hook passes a clean model", clean.returncode == 0, clean.stderr
    )
    # in another position's namespace, so `sysml check` accepts it and only the bridge sees the clash
    target.write_text(
        original.replace(
            "<'PC-104'> passengerBacklight", "<'PC-102'> passengerBacklight"
        )
    )
    duplicate = run(target)
    failed += report(
        "lint hook reports a bridge error (duplicate id) that `sysml check` accepts",
        duplicate.returncode == 2 and "duplicate id PC-102" in duplicate.stderr,
        f"exit {duplicate.returncode}: {duplicate.stderr}",
    )
    target.write_text(original)
    requirements = work / "model/requirements/system_requirements.sysml"
    replace(
        "model/requirements/system_requirements.sysml",
        "shall carry the OEM part number of its door",
        "shall be TBD",
    )(work)
    vague = run(requirements)
    return failed + report(
        "lint hook reports a vague requirement text",
        vague.returncode == 2 and "SR-106" in vague.stderr and "'TBD'" in vague.stderr,
        f"exit {vague.returncode}: {vague.stderr}",
    )


if __name__ == "__main__":
    sys.exit(main())
