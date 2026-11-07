"""PostToolUse: after a .sysml file is written, check its project's model/ and report problems to Claude.

`sysml check` for the language, then the bridge (`sysml export` + `sysml2kit needs`) for what only
`make docs` would find otherwise: duplicate ids, link ends without a short name, requirement texts.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)


event = json.load(sys.stdin)
path = Path((event.get("tool_input") or {}).get("file_path") or "")
if path.suffix != ".sysml" or not shutil.which("sysml"):
    sys.exit(0)
model = next((p for p in path.resolve().parents if p.name == "model"), None)
if model is None:
    sys.exit(0)
result = run("sysml", "--color", "never", "check", str(model), cwd=model.parent)
if result.returncode != 0:
    print(
        f"sysml check {model} failed after editing {path.name}:\n{result.stdout}{result.stderr}",
        file=sys.stderr,
    )
    sys.exit(2)  # feeds stderr back to Claude
if not shutil.which("sysml2kit"):
    sys.exit(0)
# the Makefile's file list and relative paths, so locations read model/...:line as in the docs
files = sorted(str(p.relative_to(model.parent)) for p in model.rglob("*.sysml"))
with tempfile.TemporaryDirectory() as tmp:
    export = run("sysml", "export", *files, cwd=model.parent)
    if export.returncode != 0:
        print(f"sysml export failed:\n{export.stderr}", file=sys.stderr)
        sys.exit(2)
    (Path(tmp) / "model.json").write_text(export.stdout)
    bridge = run(
        "sysml2kit",
        "needs",
        str(Path(tmp) / "model.json"),
        str(Path(tmp) / "needs.json"),
        *files,
        cwd=model.parent,
    )
if bridge.returncode != 0 or bridge.stderr:
    print(
        f"sysml2kit after editing {path.name} (fix before `make docs`):\n{bridge.stderr}",
        file=sys.stderr,
    )
    sys.exit(2)
