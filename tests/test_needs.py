import tempfile
import unittest

from sysml2kit.needs import BridgeError, convert, source_locations, text_findings


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


def keyword(id_, meta, target):
    """`#Meta` on `target`: a MetadataUsage typed by Trace::<meta>."""
    return {
        id_: el(
            id_, "MetadataUsage", type=ids(f"def{meta}"), annotatedElement=ids(target)
        ),
        f"def{meta}": {
            **el(f"def{meta}", "MetadataDefinition", name=meta),
            "qualifiedName": f"Trace::{meta}",
        },
    }


class KeywordTest(unittest.TestCase):
    def test_feature_keyword_makes_a_feature(self):
        n = needs_of(
            model(
                feat=el("feat", "ActionUsage", "FEAT-1", "drive", owner="pkg"),
                f1=el("f1", "ActionUsage", "F-1", "operate", owner="feat"),
                f2=el("f2", "ActionUsage", "F-2", "propel", owner="pkg"),
                **keyword("kw", "Feature", "feat"),
            )
        )
        self.assertEqual(n["FEAT-1"]["type"], "feature")
        self.assertEqual(n["F-1"]["type"], "function")
        self.assertEqual(n["F-1"]["owned_by"], ["FEAT-1"])
        self.assertTrue(n["F-1"]["leaf"])

    def test_domain_keyword_makes_a_physical_component(self):
        n = needs_of(
            model(
                pc=el("pc", "PartUsage", "PC-1", "board", owner="pkg"),
                pi=el("pi", "PortUsage", "PI-1", "bus", owner="pc"),
                **keyword("k1", "Electrical", "pc"),
                **keyword("k2", "Mechanical", "pi"),
            )
        )
        self.assertEqual((n["PC-1"]["type"], n["PC-1"]["domain"]), ("physical", "EE"))
        self.assertEqual(
            (n["PI-1"]["type"], n["PI-1"]["domain"]), ("physinterface", "ME")
        )

    def test_two_domains_is_an_error(self):
        with self.assertRaises(BridgeError) as cm:
            needs_of(
                model(
                    pc=el("pc", "PartUsage", "PC-1", "board", owner="pkg"),
                    **keyword("k1", "Electrical", "pc"),
                    **keyword("k2", "Software", "pc"),
                )
            )
        msg = str(cm.exception)
        self.assertIn("PC-1", msg)
        self.assertIn("Trace::Electrical", msg)
        self.assertIn("Trace::Software", msg)

    def test_prefix_must_match_type(self):
        with self.assertRaisesRegex(
            BridgeError, "LC-1: a physical component's id starts with PC-"
        ):
            needs_of(
                model(
                    lc1=el("lc1", "PartUsage", "LC-1", "board", owner="pkg"),
                    **keyword("k1", "Electrical", "lc1"),
                )
            )
        n = needs_of(
            model(
                pc=el("pc", "PartUsage", "PLT1-PC-1", "board", owner="pkg"),
                **keyword("k1", "Electrical", "pc"),
            )
        )
        self.assertEqual(n["PLT1-PC-1"]["type"], "physical")

    def test_unresolved_metadata_type_is_ignored(self):
        n = needs_of(
            model(
                pc=el("pc", "PartUsage", "PC-1", "board", owner="pkg"),
                **keyword("k1", "Electrical", "pc"),
                k2=el(
                    "k2", "MetadataUsage", type=ids("gone"), annotatedElement=ids("pc")
                ),
            )
        )
        self.assertEqual(n["PC-1"]["domain"], "EE")

    def test_untagged_model_converts_as_before(self):
        n = needs_of(model())
        self.assertEqual(n["LC-1"]["type"], "component")
        self.assertEqual({v["domain"] for v in n.values()}, {""})


class TextFindingsTest(unittest.TestCase):
    def findings(self, text, type_="sysreq"):
        need = {"id": "SR-1", "type": type_, "content": text, "source": "m.sysml:3"}
        return text_findings({"SR-1": need})

    def test_one_shall_and_no_vague_terms_is_clean(self):
        self.assertEqual(
            self.findings("The vehicle shall drive 120 km; faster is fine."), []
        )

    def test_shall_count(self):
        self.assertEqual(
            self.findings("The vehicle drives 120 km."),
            ["SR-1 (m.sysml:3): 0 'shall' in the text; state exactly one"],
        )
        self.assertIn("2 'shall'", self.findings("It shall go and shall stop.")[0])

    def test_vague_terms(self):
        self.assertEqual(
            self.findings("It shall be fast, user-friendly, etc. and TBD."),
            [
                "SR-1 (m.sysml:3): vague term 'etc.'",
                "SR-1 (m.sysml:3): vague term 'fast'",
                "SR-1 (m.sysml:3): vague term 'TBD'",
                "SR-1 (m.sysml:3): vague term 'user-friendly'",
            ],
        )

    def test_only_system_requirements_are_checked(self):
        self.assertEqual(self.findings("Drives fast.", "function"), [])


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


def rel(id_, type_, specific, general, **fields):
    return el(
        id_, type_, specific={"@id": specific}, general={"@id": general}, **fields
    )


def matches(id_, target, need="CRS-1", partial=None):
    """`@Matches { need = ...; partial = ...; }` on `target`."""
    children = {f"{id_}s": {"@id": f"{id_}s", "@type": "LiteralString", "value": need}}
    if partial is not None:
        children[f"{id_}b"] = {
            "@id": f"{id_}b",
            "@type": "LiteralBoolean",
            "value": partial,
        }
    return {
        id_: el(
            id_,
            "MetadataUsage",
            type=ids("defMatches"),
            annotatedElement=ids(target),
            ownedElement=ids(*children),
        ),
        "defMatches": {
            **el("defMatches", "MetadataDefinition", name="Matches"),
            "qualifiedName": "Trace::Matches",
        },
        **children,
    }


class PlatformVariantTest(unittest.TestCase):
    def test_platform_flag_from_source_file(self):
        n = convert(
            model(
                pc=el("pc", "PartUsage", "PLT1-PC-1", "board", owner="pkg"),
                **keyword("kw", "Electrical", "pc"),
            ),
            {"PLT1-PC-1": "platform/model/p.sysml:3", "LC-1": "model/a.sysml:1"},
            platform_files={"platform/model/p.sysml"},
        )["versions"][""]["needs"]
        self.assertTrue(n["PLT1-PC-1"]["platform"])
        self.assertFalse(n["LC-1"]["platform"])

    def test_platform_needs_drop_outside_links(self):
        elements = model(
            feat=el("feat", "ActionUsage", "PLT1-FEAT-1", "drive", owner="pkg"),
            md=el(
                "md",
                "MetadataUsage",
                owner="feat",
                type=ids("realizes"),
                annotatedElement=ids("feat"),
                ownedElement=ids("lit1"),
            ),
            **keyword("kw", "Feature", "feat"),
            **matches("m", "feat"),
        )
        locations = {"PLT1-FEAT-1": "p.sysml:1"}
        n = convert(elements, locations, platform_files={"p.sysml"})
        n = n["versions"][""]["needs"]["PLT1-FEAT-1"]
        self.assertEqual((n["realizes"], n["matches"]), ([], []))
        # a model need keeps them
        full = needs_of(elements, locations)["PLT1-FEAT-1"]
        self.assertEqual((full["realizes"], full["matches"]), (["CRS-1"], ["CRS-1"]))

    def test_variant_member_is_marked(self):
        n = needs_of(
            model(
                vm=el("vm", "VariantMembership", owner="pkg"),
                pc=el(
                    "pc",
                    "PartUsage",
                    "PC-1",
                    "board",
                    owner="pkg",
                    owningRelationship={"@id": "vm"},
                ),
                **keyword("kw", "Electrical", "pc"),
            )
        )
        self.assertTrue(n["PC-1"]["variant"])
        self.assertFalse(n["LC-1"]["variant"])


class SpecializesMatchesTest(unittest.TestCase):
    def test_specializes_from_subsetting_redefinition_typing(self):
        n = needs_of(
            model(
                a=el("a", "PartUsage", "LC-3", "a", owner="pkg"),
                r1=rel("r1", "Redefinition", "lc2", "lc1"),
                r2=rel("r2", "Subsetting", "a", "lc1"),
                r3=rel("r3", "Subclassification", "lc1", "a"),
                r4=rel("r4", "FeatureTyping", "li", "lc1"),
                implied=rel("implied", "Subsetting", "lc1", "lc2", isImplied=True),
                nameless=rel("nameless", "Subsetting", "lc1", "unnamed"),
                unnamed=el("unnamed", "PartUsage", None, "u", owner="pkg"),
            )
        )
        self.assertEqual(n["LC-2"]["specializes"], ["LC-1"])
        self.assertEqual(n["LC-3"]["specializes"], ["LC-1"])
        self.assertEqual(n["LC-1"]["specializes"], ["LC-3"])
        self.assertEqual(n["LI-1"]["specializes"], ["LC-1"])

    def test_matches_and_partial(self):
        feat = el("feat", "ActionUsage", "FEAT-1", "drive", owner="pkg")
        n = needs_of(
            model(feat=feat, **keyword("kw", "Feature", "feat"), **matches("m", "feat"))
        )["FEAT-1"]
        self.assertEqual((n["matches"], n["partial_matches"]), (["CRS-1"], []))
        n = needs_of(
            model(
                feat=feat,
                **keyword("kw", "Feature", "feat"),
                **matches("m", "feat", partial=True),
            )
        )["FEAT-1"]
        self.assertEqual((n["matches"], n["partial_matches"]), (["CRS-1"], ["CRS-1"]))

    def test_matches_on_a_non_feature_is_an_error(self):
        with self.assertRaisesRegex(
            BridgeError, "only a feature matches a customer requirement"
        ):
            needs_of(model(**matches("m", "uc")))


if __name__ == "__main__":
    unittest.main()
