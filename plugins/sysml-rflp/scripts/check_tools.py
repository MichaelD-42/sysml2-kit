"""SessionStart: in an RFLP project, say which pipeline tools are missing (silent when all are there)."""
import os
import shutil
import sys
from pathlib import Path

project = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
if not (project / "model").is_dir() and not list(project.glob("*/model/trace.sysml")):
    sys.exit(0)
missing = [tool for tool in ("sysml", "sysml2kit", "test-reports", "sphinx-build") if not shutil.which(tool)]
if missing:
    print(
        f"sysml-rflp: missing on PATH: {', '.join(missing)}. "
        "Install with `make tools` in the project (cargo for `sysml`, pip for the rest); "
        "until then `make all` and the sysml MCP server will fail."
    )
