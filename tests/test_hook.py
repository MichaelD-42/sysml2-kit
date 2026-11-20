"""The PostToolUse lint hook: in a project with a platform, lint and bridge against the platform too."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "plugins/sysml-rflp/scripts/lint_on_edit.py"
)
# records each call's arguments, one line per call; `export` must print something to write
STUB = '#!/bin/sh\necho "${0##*/} $*" >> "$STUB_LOG"\necho "{}"\n'


def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("package P;\n")


class LintHookTest(unittest.TestCase):
    def test_hook_includes_platform_model(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for name in ["model/a.sysml", "platform/model/p.sysml"]:
                touch(root / "project" / name)
            touch(root / "project/platform/model/trace.sysml")
            for tool in ["sysml", "sysml2kit"]:
                (root / "bin" / tool).parent.mkdir(exist_ok=True)
                (root / "bin" / tool).write_text(STUB)
                (root / "bin" / tool).chmod(0o755)
            log = root / "calls.log"
            event = {"tool_input": {"file_path": str(root / "project/model/a.sysml")}}
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(event),
                env={**os.environ, "PATH": str(root / "bin"), "STUB_LOG": str(log)},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            check, export, bridge = log.read_text().splitlines()
            self.assertIn("check", check)
            self.assertIn("platform/model/p.sysml", check)
            self.assertTrue(export.endswith("model/a.sysml platform/model/p.sysml"))
            self.assertTrue(bridge.endswith("--platform platform/model/p.sysml"))
            # the platform's own trace.sysml would be a second package Trace
            self.assertNotIn("platform/model/trace.sysml", check + export + bridge)


if __name__ == "__main__":
    unittest.main()
