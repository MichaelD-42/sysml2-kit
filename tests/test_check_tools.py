"""The SessionStart check: say when the model is in a subdirectory, where the sysml MCP server cannot see it."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parent.parent / "plugins/sysml-rflp/scripts/check_tools.py"
)


def run(project):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    ).stdout


class CheckToolsTest(unittest.TestCase):
    def test_a_model_in_a_subdirectory_says_where_to_start_claude(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "car/model").mkdir(parents=True)
            (Path(root) / "car/model/trace.sysml").write_text("package Trace;\n")
            self.assertIn(f"start Claude in {Path(root) / 'car'}", run(root))

    def test_a_model_at_the_root_needs_no_hint(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "model").mkdir()
            (Path(root) / "model/trace.sysml").write_text("package Trace;\n")
            self.assertNotIn("start Claude in", run(root))

    def test_a_model_directory_without_sysml_is_not_an_rflp_project(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "model").mkdir()
            (Path(root) / "model/user.py").write_text("class User: ...\n")
            self.assertEqual(run(root), "")


if __name__ == "__main__":
    unittest.main()
