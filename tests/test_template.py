"""Each example must be the project template plus content; shared files may not drift apart."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "plugins/sysml-rflp/templates/project"
EXAMPLES = [
    ROOT / "examples/vehicle",
    ROOT / "examples/edrive-platform",
    ROOT / "examples/seat-switch-platform",
]
SAME = [
    "docs/ubproject.toml",
    "docs/schemas.json",
    "docs/traceability.rst",
    "docs/compliance.md",
    "model/trace.sysml",
    ".gitignore",
]


class TemplateSyncTest(unittest.TestCase):
    def test_shared_files_are_identical(self):
        for example in EXAMPLES:
            for name in SAME:
                self.assertEqual(
                    (TEMPLATE / name).read_text(),
                    (example / name).read_text(),
                    f"{example.name}/{name}",
                )

    def test_makefile_differs_only_in_diagrams(self):
        def strip(path):
            return re.sub(r"^DIAGRAMS :=.*$", "", path.read_text(), flags=re.MULTILINE)

        for example in EXAMPLES:
            self.assertEqual(
                strip(TEMPLATE / "Makefile"), strip(example / "Makefile"), example.name
            )


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
