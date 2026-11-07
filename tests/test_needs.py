import tempfile
import unittest

from sysml2kit.needs import BridgeError, convert, source_locations


def el(id_, type_, short=None, name=None, owner=None, **fields):
    e = {
        "@id": id_,
        "@type": type_,
        "declaredShortName": short,
        "shortName": short,
        "name": name,
        "qualifiedName": f"P::{name}" if name else None,
        "owner": {"@id": owner} if owner else None,
        "documentation": [],
    }
    e.update(fields)
    return e


def ids(*names):
    return [{"@id": n} for n in names]


def model(**overrides):
    """A small RFLP model, keyed by @id; overrides replace or drop (None) elements."""
    elements = {
        "pkg": el("pkg", "Package", name="P"),
        "uc": el("uc", "UseCaseUsage", "UC-1", "commute", owner="pkg"),
        "perform": el(
            "perform",
            "PerformActionUsage",
            owner="uc",
            ownedReferenceSubsetting=ids("rs"),
        ),
        "rs": {
            "@id": "rs",
            "@type": "ReferenceSubsetting",
            "referencedFeature": {"@id": "f2"},
        },
        "md": el(
            "md",
            "MetadataUsage",
            owner="uc",
            type=ids("realizes"),
            annotatedElement=ids("uc"),
            ownedElement=ids("lit1", "seq"),
        ),
        "realizes": {
            **el("realizes", "MetadataDefinition", name="Realizes"),
            "qualifiedName": "Trace::Realizes",
        },
        "lit1": {"@id": "lit1", "@type": "LiteralString", "value": "CRS-1"},
        "seq": el("seq", "OperatorExpression", ownedElement=ids("lit2", "lit3")),
        "lit2": {"@id": "lit2", "@type": "LiteralString", "value": "CRS-2"},
        "lit3": {"@id": "lit3", "@type": "LiteralString", "value": "CRS-3"},
        "sr": el(
            "sr",
            "RequirementUsage",
            "SR-1",
            "mass",
            owner="pkg",
            documentation=ids("doc"),
        ),
        "doc": {"@id": "doc", "@type": "Documentation", "body": "Light."},
        "f1": el("f1", "ActionUsage", "F-1", "operate", owner="pkg"),
        "f2": el("f2", "ActionUsage", "F-2", "propel", owner="f1"),
        "lc1": el("lc1", "PartUsage", "LC-1", "vehicle", owner="pkg"),
        "lc2": el("lc2", "PartUsage", "LC-2", "powertrain", owner="lc1"),
        "li": el("li", "PortUsage", "LI-1", "powerIn", owner="lc2"),
        "alloc": el(
            "alloc", "AllocationUsage", owner="pkg", relatedFeature=ids("f2", "lc2")
        ),
        "sat": el(
            "sat",
            "SatisfyRequirementUsage",
            owner="pkg",
            satisfyingFeature={"@id": "lc1"},
            satisfiedRequirement={"@id": "sr"},
        ),
        "stc": el(
            "stc",
            "VerificationCaseUsage",
            "STC-1",
            "weigh",
            owner="pkg",
            verifiedRequirement=ids("sr"),
        ),
        # implicit feature inheriting a short name (e.g. an allocation end): not a need
        "end": {
            **el("end", "Feature", None, "propel", owner="alloc"),
            "shortName": "F-2",
        },
    }
    elements.update(overrides)
    return [e for e in elements.values() if e is not None]


def needs_of(elements, locations=None):
    return convert(elements, locations or {})["versions"][""]["needs"]


class ConvertTest(unittest.TestCase):
    def test_links(self):
        n = needs_of(model())
        self.assertEqual(n["F-2"]["realizes"], ["UC-1"])
        self.assertEqual(n["F-2"]["allocated_to"], ["LC-2"])
        self.assertEqual(n["LC-1"]["satisfies"], ["SR-1"])
        self.assertEqual(n["STC-1"]["verifies"], ["SR-1"])
        self.assertEqual(n["UC-1"]["realizes"], ["CRS-1", "CRS-2", "CRS-3"])

    def test_types_content_ownership(self):
        n = needs_of(model(), {"SR-1": "model/r.sysml:3"})
        self.assertEqual(
            {k: v["type"] for k, v in n.items()},
            {
                "UC-1": "usecase",
                "SR-1": "sysreq",
                "F-1": "function",
                "F-2": "function",
                "LC-1": "component",
                "LC-2": "component",
                "LI-1": "interface",
                "STC-1": "systest",
            },
        )
        self.assertEqual(n["SR-1"]["content"], "Light.")
        self.assertEqual(n["SR-1"]["source"], "model/r.sysml:3")
        self.assertEqual(n["F-2"]["owned_by"], ["F-1"])

    def test_leaf_counts_children_of_the_same_type_only(self):
        n = needs_of(model())
        self.assertFalse(n["F-1"]["leaf"])
        self.assertTrue(n["F-2"]["leaf"])
        self.assertFalse(n["LC-1"]["leaf"])
        self.assertTrue(
            n["LC-2"]["leaf"], "owning a port does not make a component a non-leaf"
        )

    def assertBridgeError(self, elements, fragment):
        with self.assertRaises(BridgeError) as caught:
            convert(elements, {})
        self.assertIn(fragment, str(caught.exception))

    def test_duplicate_id(self):
        self.assertBridgeError(
            model(lc2=el("lc2", "PartUsage", "LC-1", "other", owner="lc1")),
            "duplicate id LC-1",
        )

    def test_link_end_without_short_name(self):
        self.assertBridgeError(
            model(lc1=el("lc1", "PartUsage", None, "vehicle", owner="pkg")),
            "satisfies end P::vehicle has no short name",
        )

    def test_unmapped_kind(self):
        self.assertBridgeError(
            model(x=el("x", "ConnectionUsage", "C-1", "c", owner="pkg")),
            "no need type for ConnectionUsage",
        )

    def test_trace_metadata_on_element_without_short_name(self):
        self.assertBridgeError(
            model(uc=el("uc", "UseCaseUsage", None, "commute", owner="pkg")),
            "annotated element has no short name",
        )

    def test_same_named_metadata_from_another_library_is_not_a_trace_link(self):
        other = {
            **el("realizes", "MetadataDefinition", name="Realizes"),
            "qualifiedName": "Profile::Realizes",
        }
        self.assertEqual(needs_of(model(realizes=other))["UC-1"]["realizes"], [])

    def test_doc_text_is_plain_text_not_rst(self):
        doc = {
            "@id": "doc",
            "@type": "Documentation",
            "body": r"See note_ and *all | `x` \ y.",
        }
        self.assertEqual(
            needs_of(model(doc=doc))["SR-1"]["content"],
            r"See note\_ and \*all \| \`x\` \\ y.",
        )


class SourceLocationsTest(unittest.TestCase):
    def test_quoted_and_plain_short_names(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sysml", delete=False) as f:
            f.write("package X {\n    part def <'B-001'> A;\n    part <p1> b : A;\n}\n")
        self.assertEqual(
            source_locations([f.name]), {"B-001": f"{f.name}:2", "p1": f"{f.name}:3"}
        )

    def test_mentions_in_comments_are_not_declarations(self):
        files = []
        for text in (
            "package Trace {\n    doc /*\n     * e.g. use case <'UC-001'> x;\n     */\n    // or <'UC-001'>\n}\n",
            "package U {\n\n    use case <'UC-001'> commute;\n}\n",
        ):
            with tempfile.NamedTemporaryFile("w", suffix=".sysml", delete=False) as f:
                f.write(text)
            files.append(f.name)
        self.assertEqual(source_locations(files), {"UC-001": f"{files[1]}:3"})

    def test_a_declaration_inside_a_multi_line_note_is_not_the_declaration(self):
        text = "package P {\n    //* old:\n        requirement <'SR-9'> gone;\n    */\n    requirement <'SR-9'> kept;\n}\n"
        with tempfile.NamedTemporaryFile("w", suffix=".sysml", delete=False) as f:
            f.write(text)
        self.assertEqual(source_locations([f.name]), {"SR-9": f"{f.name}:5"})

    def test_comment_markers_inside_strings_do_not_hide_declarations(self):
        text = "package P {\n    attribute u = \"http://x\"; requirement <'SR-1'> r;\n    attribute v = \"/*\";\n    requirement <'SR-2'> s;\n}\n"
        with tempfile.NamedTemporaryFile("w", suffix=".sysml", delete=False) as f:
            f.write(text)
        self.assertEqual(
            source_locations([f.name]),
            {"SR-1": f"{f.name}:2", "SR-2": f"{f.name}:4"},
        )


if __name__ == "__main__":
    unittest.main()
