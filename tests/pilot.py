"""Check the kit's models with the OMG SysML v2 Pilot Implementation, the reference implementation.

`sysml` (Rust) parses and checks the models in the pipeline; this is the conformance oracle on top of it:
the examples and the authoring patterns must parse, resolve and validate clean in the Pilot as well.
Run: python tests/pilot.py [dir]   (needs a JDK 21+; downloads the pinned kernel into dir, or a temp dir,
unless it is there already)
"""

import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PILOT_TAG = "2026-09.1"
KERNEL = "jupyter-sysml-kernel-0.63.1"
URL = f"https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/download/{PILOT_TAG}/{KERNEL}.zip"
JAVA = os.environ.get("JAVA", "java")
ROOT = Path(__file__).resolve().parent.parent
PLATFORM = ROOT / "examples" / "window-switch-platform" / "model"
RFQ = ROOT / "examples" / "window-switch-rfq" / "model"


def sysml(folder, without=()):
    return sorted(p for p in folder.rglob("*.sysml") if p not in without)


# as the Makefiles load them: an RFQ build reads the platform's model without its own copy of Trace
MODELS = {
    "platform example": sysml(PLATFORM),
    "rfq example": sysml(RFQ) + sysml(PLATFORM, without={PLATFORM / "trace.sysml"}),
    "authoring patterns": [
        ROOT / "plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml",
        ROOT / "plugins/sysml-rflp/templates/project/model/trace.sysml",
    ],
}


def kernel(folder):
    jar = folder / "sysml" / f"{KERNEL}-all.jar"
    if not jar.exists():
        archive = folder / f"{KERNEL}.zip"
        urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as z:
            z.extractall(folder)
        archive.unlink()
    return jar, folder / "sysml" / "sysml.library"


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    folder.mkdir(parents=True, exist_ok=True)
    jar, library = kernel(folder)
    failures = 0
    for name, files in MODELS.items():
        run = subprocess.run(
            [JAVA, "-cp", str(jar), str(ROOT / "tests" / "PilotCheck.java")]
            + [str(library)]
            + [str(f) for f in files],
            check=False,
            capture_output=True,
            text=True,
        )
        findings = [
            line.replace(f"{ROOT}/", "")
            for line in run.stdout.splitlines()
            if ": error: " in line or ": warning: " in line
        ]
        summary = [line for line in run.stdout.splitlines() if "error(s)" in line]
        ok = run.returncode == 0
        print(
            f"{'ok  ' if ok else 'FAIL'} {name}: {summary[-1] if summary else run.stderr[-500:]}"
        )
        for line in findings:
            print(f"     {line}")
        failures += not ok
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
