"""SessionStart: in an RFLP project, say which pipeline tools are missing and whether the MCP server can see the model."""

import os
import re
import shutil
import sys
from pathlib import Path

project = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
nested = [trace.parent.parent for trace in project.glob("*/model/trace.sysml")]
if not (project / "model/trace.sysml").is_file():
    if not nested:
        sys.exit(0)
    # the plugin starts the server with `make -s mcp`, relative to where Claude was started
    print(
        f"sysml-rflp: the model is in a subdirectory; start Claude in {' or '.join(map(str, nested))} "
        "so the sysml MCP server (find, relations, outline) sees it."
    )
makefile = project / "Makefile"
if makefile.is_file() and not re.search(r"^mcp:", makefile.read_text(), re.MULTILINE):
    print(
        "sysml-rflp: the Makefile has no `mcp` target, so the sysml MCP server (find, relations, outline) "
        "does not start; copy the Makefile from the plugin's template and keep your DIAGRAMS and PLATFORM lines."
    )
missing = [
    tool
    for tool in ("make", "sysml", "sysml2kit", "test-reports", "sphinx-build")
    if not shutil.which(tool)
]
if missing:
    print(
        f"sysml-rflp: missing on PATH: {', '.join(missing)}. "
        "Install with `make tools` in the project (cargo for `sysml`, pip for the rest); "
        "until then `make all` and the sysml MCP server will fail."
    )
