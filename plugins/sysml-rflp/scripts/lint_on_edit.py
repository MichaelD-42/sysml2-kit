"""PostToolUse: after a .sysml file is written, run `sysml check` on its project's model/ and report errors to Claude."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

event = json.load(sys.stdin)
path = Path((event.get("tool_input") or {}).get("file_path") or "")
if path.suffix != ".sysml" or not shutil.which("sysml"):
    sys.exit(0)
model = next((p for p in path.resolve().parents if p.name == "model"), None)
if model is None:
    sys.exit(0)
result = subprocess.run(["sysml", "--color", "never", "check", str(model)], capture_output=True, text=True)
if result.returncode != 0:
    print(f"sysml check {model} failed after editing {path.name}:\n{result.stdout}{result.stderr}", file=sys.stderr)
    sys.exit(2)  # feeds stderr back to Claude
