"""SessionStart: in an RFLP project, say which pipeline tools are missing and whether the MCP server can see the model."""

import os
import shutil
import sys
from pathlib import Path

project = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
nested = [trace.parent.parent for trace in project.glob("*/model/trace.sysml")]
if not (project / "model/trace.sysml").is_file():
    if not nested:
        sys.exit(0)
    # the plugin starts `sysml mcp --project model`, relative to where Claude was started
    print(
        f"sysml-rflp: the model is in a subdirectory; start Claude in {' or '.join(map(str, nested))} "
        "so the sysml MCP server (find, relations, outline) sees it."
    )
missing = [
    tool
    for tool in ("sysml", "sysml2kit", "test-reports", "sphinx-build")
    if not shutil.which(tool)
]
if missing:
    print(
        f"sysml-rflp: missing on PATH: {', '.join(missing)}. "
        "Install with `make tools` in the project (cargo for `sysml`, pip for the rest); "
        "until then `make all` and the sysml MCP server will fail."
    )
