"""The vehicle example must be the project template plus content; shared files may not drift apart."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "plugins/sysml-rflp/templates/project"
EXAMPLE = ROOT / "examples/vehicle"
SAME = [
    "docs/ubproject.toml",
    "docs/schemas.json",
    "docs/traceability.rst",
    "model/trace.sysml",
    ".gitignore",
]


class TemplateSyncTest(unittest.TestCase):
    def test_shared_files_are_identical(self):
        for name in SAME:
            self.assertEqual(
                (TEMPLATE / name).read_text(), (EXAMPLE / name).read_text(), name
            )

    def test_makefile_differs_only_in_diagrams(self):
        def strip(path):
            return re.sub(r"^DIAGRAMS :=.*$", "", path.read_text(), flags=re.MULTILINE)

        self.assertEqual(strip(TEMPLATE / "Makefile"), strip(EXAMPLE / "Makefile"))


class ReleaseVersionTest(unittest.TestCase):
    def test_package_plugin_and_template_pin_name_one_version(self):
        package = re.search(
            r'^version = "(.+)"', (ROOT / "pyproject.toml").read_text(), re.MULTILINE
        )[1]
        plugin = json.loads(
            (ROOT / "plugins/sysml-rflp/.claude-plugin/plugin.json").read_text()
        )["version"]
        pin = re.search(
            r"sysml2-kit@v(\S+)", (TEMPLATE / "requirements.txt").read_text()
        )[1]
        self.assertEqual((package, plugin, pin), (package, package, package))


if __name__ == "__main__":
    unittest.main()
