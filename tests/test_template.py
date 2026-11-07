"""The vehicle example must be the project template plus content; shared files may not drift apart."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "plugins/sysml-rflp/templates/project"
EXAMPLE = ROOT / "examples/vehicle"
SAME = ["docs/ubproject.toml", "docs/schemas.json", "docs/traceability.rst", "model/trace.sysml", ".gitignore"]


class TemplateSyncTest(unittest.TestCase):
    def test_shared_files_are_identical(self):
        for name in SAME:
            self.assertEqual((TEMPLATE / name).read_text(), (EXAMPLE / name).read_text(), name)

    def test_makefile_differs_only_in_diagrams(self):
        def strip(path):
            return re.sub(r"^DIAGRAMS :=.*$", "", path.read_text(), flags=re.M)
        self.assertEqual(strip(TEMPLATE / "Makefile"), strip(EXAMPLE / "Makefile"))


if __name__ == "__main__":
    unittest.main()
