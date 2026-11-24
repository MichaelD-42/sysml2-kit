import tempfile
import unittest
from pathlib import Path

from sysml2kit.needs import (
    BridgeError,
    convert,
    normalize,
    platform_dir,
    source_locations,
    text_findings,
)


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

    def test_use_case_objective_is_the_title(self):
        n = needs_of(
            model(
                uc=el(
                    "uc",
                    "UseCaseUsage",
                    "UC-1",
                    "commute",
                    owner="pkg",
                    ownedRelationship=ids("om"),
                ),
                om=el("om", "ObjectiveMembership", owner="uc", ownedElement=ids("obj")),
                obj=el("obj", "RequirementUsage", owner="om", documentation=ids("od")),
                od={
                    "@id": "od",
                    "@type": "Documentation",
                    "body": "The driver wants to get to work",
                },
            )
        )
        self.assertEqual(n["UC-1"]["title"], "The driver wants to get to work")
        self.assertEqual(n["UC-1"]["qualified_name"], "P::commute")
        self.assertEqual(n["F-1"]["title"], "operate")  # no objective: the name

    def test_use_case_title_in_the_sysml_0_2_export_shape(self):
        """0.2 writes owner and ownedElement as the spec derives them: a relationship has neither."""
        n = needs_of(
            model(
                uc=el(
                    "uc",
                    "UseCaseUsage",
                    "UC-1",
                    "commute",
                    owner="pkg",
                    ownedRelationship=ids("om"),
                ),
                om=el(
                    "om",
                    "ObjectiveMembership",
                    owningRelatedElement={"@id": "uc"},
                    ownedRelatedElement=ids("obj"),
                    ownedElement=[],
                ),
                obj=el("obj", "RequirementUsage", owner="uc", documentation=ids("od")),
                od={
                    "@id": "od",
                    "@type": "Documentation",
                    "body": "The driver wants to get to work",
                },
            )
        )
        self.assertEqual(n["UC-1"]["title"], "The driver wants to get to work")

    def test_platform_dir_from_the_makefile(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(platform_dir(tmp), Path(tmp) / "platform")
            (Path(tmp) / "Makefile").write_text("X := 1\nPLATFORM := ../plat\n")
            self.assertEqual(platform_dir(tmp), Path(tmp) / "../plat")

    def test_normalize_restores_owner_and_owned_elements(self):
        elements = [
            {
                "@id": "a",
                "@type": "AttributeUsage",
                "ownedRelationship": ids("fv"),
                "ownedElement": ids("x"),
            },
            {
                "@id": "fv",
                "@type": "FeatureValue",
                "owner": None,
                "ownedElement": [],
                "owningRelatedElement": {"@id": "a"},
                "ownedRelatedElement": ids("x"),
            },
            {"@id": "x", "@type": "LiteralInteger", "owner": {"@id": "a"}},
        ]
        by_id = {e["@id"]: e for e in normalize(elements)}
        self.assertEqual(by_id["fv"]["owner"], {"@id": "a"})
        self.assertEqual(by_id["fv"]["ownedElement"], ids("x"))
        self.assertEqual(by_id["a"]["ownedElement"], ids("x", "fv"))
        self.assertEqual(normalize(elements), elements, "idempotent")

    def test_a_verification_objective_is_not_the_title(self):
        n = needs_of(
            model(
                stc=el(
                    "stc",
                    "VerificationCaseUsage",
                    "STC-1",
                    "weigh",
                    owner="pkg",
                    verifiedRequirement=ids("sr"),
                    ownedRelationship=ids("om"),
                ),
                om=el(
                    "om", "ObjectiveMembership", owner="stc", ownedElement=ids("obj")
                ),
                obj=el("obj", "RequirementUsage", owner="om", documentation=ids("od")),
                od={"@id": "od", "@type": "Documentation", "body": "Check the mass"},
            )
        )
        self.assertEqual(n["STC-1"]["title"], "weigh")

    def test_leaf_counts_children_of_the_same_type_only(self):
        n = needs_of(model())
        self.assertFalse(n["F-1"]["leaf"])
        self.assertTrue(n["F-2"]["leaf"])
        self.assertFalse(n["LC-1"]["leaf"])
        self.assertTrue(
            n["LC-2"]["leaf"], "owning a port does not make a component a non-leaf"
        )

    def test_subsetting_a_composite_is_not_a_leaf(self):
        n = needs_of(
            model(
                a=el("a", "PartUsage", "LC-3", "a", owner="pkg"),
                b=el("b", "PartUsage", "LC-4", "b", owner="pkg"),
                r1=rel("r1", "Subsetting", "a", "lc1"),
                r2=rel("r2", "Subsetting", "b", "lc2"),
                # a cycle must not hang the closure
                r3=rel("r3", "Subclassification", "lc1", "a"),
            )
        )
        self.assertFalse(n["LC-3"]["leaf"], "inherits LC-1's child components")
        self.assertTrue(n["LC-4"]["leaf"], "LC-2 is a leaf, so is what subsets it")

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
            model(x=el("x", "StateUsage", "C-1", "c", owner="pkg")),
            "no need type for StateUsage",
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

    def test_doc_text_drops_the_trailing_newline(self):
        # the OMG Pilot keeps it in Documentation.body; sysml export strips it
        doc = {"@id": "doc", "@type": "Documentation", "body": "Light.\n"}
        self.assertEqual(needs_of(model(doc=doc))["SR-1"]["content"], "Light.")


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


def meta(id_, qualified, annotated, *values):
    """A metadata usage typed by `qualified`, its definition, and its string literals."""
    lits = [
        {"@id": f"{id_}-v{i}", "@type": "LiteralString", "value": v}
        for i, v in enumerate(values)
    ]
    return {
        id_: el(
            id_,
            "MetadataUsage",
            owner=annotated,
            type=ids(f"{id_}-def"),
            annotatedElement=ids(annotated),
            ownedElement=ids(*(x["@id"] for x in lits)),
        ),
        f"{id_}-def": {
            **el(f"{id_}-def", "MetadataDefinition", name=qualified),
            "qualifiedName": qualified,
        },
        **{x["@id"]: x for x in lits},
    }


class ConnectsMappingTest(unittest.TestCase):
    def connector(self, kind="InterfaceUsage"):
        # lc3 sits beside lc2 under lc1; the interface joins lc2's port LI-1 and a nameless port of lc3
        return model(
            lc3=el("lc3", "PartUsage", "LC-3", "brakes", owner="lc1"),
            p3=el("p3", "PortUsage", None, "pIn", owner="lc3"),
            ci=el(
                "ci", kind, "LI-2", "drive", owner="lc1", relatedFeature=ids("li", "p3")
            ),
        )

    def test_interface_connects_owners_of_its_ends(self):
        for kind in ("InterfaceUsage", "ConnectionUsage"):
            n = needs_of(self.connector(kind))
            self.assertEqual(n["LI-2"]["type"], "interface")
            self.assertEqual(n["LI-2"]["connects"], ["LI-1", "LC-3"], kind)

    def test_perform_in_a_feature_realizes_it(self):
        n = needs_of(
            model(
                feat=el("feat", "ActionUsage", "FEAT-9", "drive", owner="pkg"),
                kw=el(
                    "kw",
                    "MetadataUsage",
                    owner="feat",
                    type=ids("featdef"),
                    annotatedElement=ids("feat"),
                ),
                featdef={
                    **el("featdef", "MetadataDefinition", name="Feature"),
                    "qualifiedName": "Trace::Feature",
                },
                pf=el(
                    "pf",
                    "PerformActionUsage",
                    owner="feat",
                    ownedReferenceSubsetting=ids("rs2"),
                ),
                rs2={
                    "@id": "rs2",
                    "@type": "ReferenceSubsetting",
                    "referencedFeature": {"@id": "f1"},
                },
            )
        )
        self.assertEqual(n["FEAT-9"]["type"], "feature")
        self.assertEqual(n["F-1"]["realizes"], ["FEAT-9"])

    def test_feature_chain_ends_at_its_last_feature(self):
        # `perform operate.propel;`: the export references a nameless chain feature
        chain = el("chain", "Feature", owner="perform", chainingFeature=ids("f1", "f2"))
        rs = {
            "@id": "rs",
            "@type": "ReferenceSubsetting",
            "referencedFeature": {"@id": "chain"},
        }
        self.assertEqual(
            needs_of(model(chain=chain, rs=rs))["F-2"]["realizes"], ["UC-1"]
        )

    def test_connector_end_through_a_chain(self):
        chain = el("chain", "Feature", owner="ci", chainingFeature=ids("lc2", "li"))
        n = needs_of(
            model(
                chain=chain,
                ci=el(
                    "ci",
                    "InterfaceUsage",
                    "LI-2",
                    "drive",
                    owner="lc1",
                    relatedFeature=ids("chain", "lc2"),
                ),
            )
        )
        self.assertEqual(n["LI-2"]["connects"], ["LI-1", "LC-2"])

    def test_chain_whose_last_link_is_a_chain(self):
        # the OMG Pilot exports chains as written, so a chain may end in another chain
        inner = el("inner", "Feature", owner="perform", chainingFeature=ids("f1", "f2"))
        outer = el(
            "outer", "Feature", owner="perform", chainingFeature=ids("f1", "inner")
        )
        rs = {
            "@id": "rs",
            "@type": "ReferenceSubsetting",
            "referencedFeature": {"@id": "outer"},
        }
        n = needs_of(model(inner=inner, outer=outer, rs=rs))
        self.assertEqual(n["F-2"]["realizes"], ["UC-1"])

    def test_mapping(self):
        mapping = {
            "keywords": {"Arch::External": "external"},
            "ids": {"component": r"LC_\d+", "external": r"EXT_\w+"},
            "metadata_links": {"Arch::Carries": "carries"},
            "metadata_fields": {"Arch::Medium": "medium"},
        }
        elements = model(
            lc1=el("lc1", "PartUsage", "LC_1", "vehicle", owner="pkg"),
            lc2=el("lc2", "PartUsage", "LC_2", "powertrain", owner="lc1"),
            ext=el("ext", "PartUsage", "EXT_ROAD", "road", owner="pkg"),
            **meta("m1", "Arch::External", "ext"),
            **meta("m2", "Arch::Carries", "li", "FUNC_1", "FUNC_2"),
            **meta("m3", "Arch::Medium", "li", "data"),
        )
        n = convert(elements, {}, mapping=mapping)["versions"][""]["needs"]
        self.assertEqual(n["EXT_ROAD"]["type"], "external")
        self.assertEqual(n["LI-1"]["carries"], ["FUNC_1", "FUNC_2"])
        self.assertEqual(n["LI-1"]["medium"], "data")
        self.assertEqual(n["LC_2"]["owned_by"], ["LC_1"])
        with self.assertRaises(BridgeError) as caught:
            convert(
                model(**meta("m4", "Arch::Medium", "li", "x")),
                {},
                mapping={"metadata_fields": {"Arch::Medium": "title"}},
            )
        self.assertIn("LI-1: field title is the bridge's own", str(caught.exception))
        with self.assertRaises(BridgeError) as caught:
            convert(model(), {}, mapping=mapping)
        self.assertIn(r"LC-1: a component id matches LC_\d+", str(caught.exception))


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

    def test_assembly_keyword_makes_a_physical_component_without_domain(self):
        n = needs_of(
            model(
                pc=el("pc", "PartUsage", "PC-1", "switch", owner="pkg"),
                **keyword("k1", "Assembly", "pc"),
            )
        )
        self.assertEqual((n["PC-1"]["type"], n["PC-1"]["domain"]), ("physical", ""))

    def test_assembly_keyword_does_not_make_a_port_physical(self):
        n = needs_of(
            model(
                pi=el("pi", "PortUsage", "LI-9", "bus", owner="pkg"),
                **keyword("k1", "Assembly", "pi"),
            )
        )
        self.assertEqual(n["LI-9"]["type"], "interface")

    def test_assembly_with_a_domain_is_an_error(self):
        with self.assertRaisesRegex(
            BridgeError, "PC-1: an assembly takes no domain keyword"
        ):
            needs_of(
                model(
                    pc=el("pc", "PartUsage", "PC-1", "switch", owner="pkg"),
                    **keyword("k1", "Assembly", "pc"),
                    **keyword("k2", "Mechanical", "pc"),
                )
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


def matches(id_, target, need="CRS-1", partial=None, meta="Matches"):
    """`@<meta> { need = ...; partial = ...; }` on `target`."""
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
            type=ids(f"def{meta}"),
            annotatedElement=ids(target),
            ownedElement=ids(*children),
        ),
        f"def{meta}": {
            **el(f"def{meta}", "MetadataDefinition", name=meta),
            "qualifiedName": f"Trace::{meta}",
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


class ConstraintTest(unittest.TestCase):
    def test_constraint_is_a_need_and_partial_satisfies_keeps_satisfies(self):
        con = el("con", "ConstraintUsage", "CON-001", "limit", owner="pkg")
        n = needs_of(
            model(
                con=con,
                **matches("s", "con", need="CRS-001", partial=True, meta="Satisfies"),
            )
        )["CON-001"]
        self.assertEqual(n["type"], "constraint")
        self.assertEqual((n["satisfies"], n["partial_satisfies"]), (["CRS-001"],) * 2)

    def test_satisfies_without_partial(self):
        con = el("con", "ConstraintUsage", "CON-001", "limit", owner="pkg")
        n = needs_of(model(con=con, **matches("s", "con", meta="Satisfies")))["CON-001"]
        self.assertEqual((n["satisfies"], n["partial_satisfies"]), (["CRS-1"], []))

    def test_implements_on_a_verification(self):
        n = needs_of(
            model(
                stc=el("stc", "VerificationCaseUsage", "STC-1", "t", owner="pkg"),
                **matches("i", "stc", need="CTR-001", meta="Implements"),
            )
        )["STC-1"]
        self.assertEqual(n["implements"], ["CTR-001"])

    def test_constraint_prefix_must_match(self):
        with self.assertRaisesRegex(
            BridgeError, "SR-9: a constraint's id starts with CON-"
        ):
            needs_of(
                model(con=el("con", "ConstraintUsage", "SR-9", "limit", owner="pkg"))
            )


PLATFORM_FILES = {"platform/p.sysml"}


def rfq(*keywords, **overrides):
    """model() plus a platform part WSW-PC-1 and a platform feature WSW-FEAT-1, as an RFQ build sees them;
    `keywords` are keyword() dicts, merged so two of one kind share their definition."""
    extra = {
        "ppc": el("ppc", "PartUsage", "WSW-PC-1", "caps", owner="pkg"),
        "pfeat": el("pfeat", "ActionUsage", "WSW-FEAT-1", "control", owner="pkg"),
        **keyword("kpp", "Mechanical", "ppc"),
        **keyword("kpf", "Feature", "pfeat"),
    }
    for k in keywords:
        extra.update(k)
    elements = model(**extra, **overrides)
    locations = {"WSW-PC-1": "platform/p.sysml:1", "WSW-FEAT-1": "platform/p.sysml:2"}
    return elements, locations


def convert_rfq(elements, locations, platform=True):
    return convert(elements, locations, PLATFORM_FILES if platform else ())


class RealizationTest(unittest.TestCase):
    def assertError(self, elements, locations, text, platform=True):
        with self.assertRaises(BridgeError) as ctx:
            convert_rfq(elements, locations, platform)
        self.assertIn(text, str(ctx.exception))

    def test_modified_keyword_marks_a_physical_part(self):
        elements, locations = rfq(
            keyword("k1", "Mechanical", "pc"),
            keyword("k2", "Modified", "pc"),
            keyword("k3", "Mechanical", "other"),
            pc=el("pc", "PartUsage", "PC-1", "oemCaps", owner="pkg"),
            other=el("other", "PartUsage", "PC-2", "label", owner="pkg"),
            r=rel("r", "Subsetting", "pc", "ppc"),
        )
        n = convert_rfq(elements, locations)["versions"][""]["needs"]
        self.assertIs(n["PC-1"]["modified"], True)
        self.assertIs(n["PC-2"]["modified"], False)

    def test_modified_needs_a_platform_part(self):
        elements, locations = rfq(
            keyword("k1", "Mechanical", "pc"),
            keyword("k2", "Modified", "pc"),
            pc=el("pc", "PartUsage", "PC-1", "label", owner="pkg"),
        )
        self.assertError(
            elements,
            locations,
            "PC-1: #Modified needs a platform part to modify; a part of its own is new",
        )

    def test_modified_through_a_project_part_reaches_the_platform(self):
        elements, locations = rfq(
            keyword("k1", "Mechanical", "pc"),
            keyword("k2", "Mechanical", "pc2"),
            keyword("k3", "Modified", "pc2"),
            pc=el("pc", "PartUsage", "PC-1", "caps", owner="pkg"),
            pc2=el("pc2", "PartUsage", "PC-2", "oemCaps", owner="pkg"),
            r1=rel("r1", "Subsetting", "pc", "ppc"),
            r2=rel("r2", "Subsetting", "pc2", "pc"),
        )
        n = convert_rfq(elements, locations)["versions"][""]["needs"]
        self.assertIs(n["PC-2"]["modified"], True)

    def test_modified_on_a_non_physical_need_is_an_error(self):
        elements, locations = rfq(keyword("k", "Modified", "lc2"))
        self.assertError(elements, locations, "LC-2: #Modified needs a platform part")

    def test_project_feature_specializing_the_platform_is_an_error(self):
        elements, locations = rfq(
            keyword("kf", "Feature", "feat"),
            feat=el("feat", "ActionUsage", "FEAT-1", "drive", owner="pkg"),
            r=rel("r", "Subsetting", "feat", "pfeat"),
        )
        self.assertError(
            elements,
            locations,
            "FEAT-1: specializes the platform's WSW-FEAT-1; an RFQ derives its own "
            "features and the platform realizes them at P",
        )

    def test_project_component_specializing_the_platform_is_an_error(self):
        elements, locations = rfq(
            plc=el("plc", "PartUsage", "WSW-LC-1", "switch", owner="pkg"),
            r=rel("r", "Subsetting", "lc1", "plc"),
        )
        locations["WSW-LC-1"] = "platform/p.sysml:3"
        self.assertError(
            elements,
            locations,
            "LC-1: specializes the platform's WSW-LC-1; an RFQ derives its own "
            "logical components and the platform realizes them at P",
        )

    def test_platform_build_has_no_specialization_error(self):
        elements, locations = rfq(
            keyword("kf", "Feature", "feat"),
            feat=el("feat", "ActionUsage", "FEAT-1", "drive", owner="pkg"),
            r=rel("r", "Subsetting", "feat", "pfeat"),
        )
        n = convert_rfq(elements, locations, platform=False)["versions"][""]["needs"]
        self.assertEqual(n["FEAT-1"]["specializes"], ["WSW-FEAT-1"])

    def test_redefining_an_inherited_ref_part_reaches_the_platform(self):
        """`oemCaps :>> keyCaps`, where the platform assembly's `ref part keyCaps :> caps` has no short name."""
        elements, locations = rfq(
            keyword("k1", "Mechanical", "pc"),
            keyword("k2", "Modified", "pc"),
            ref=el("ref", "PartUsage", None, "keyCaps", owner="pkg"),
            r1=rel("r1", "Subsetting", "ref", "ppc"),
            pc=el("pc", "PartUsage", "PC-1", "oemCaps", owner="pkg"),
            r2=rel("r2", "Redefinition", "pc", "ref"),
        )
        n = convert_rfq(elements, locations)["versions"][""]["needs"]
        self.assertEqual(n["PC-1"]["specializes"], ["WSW-PC-1"])

    def test_physical_part_may_specialize_the_platform(self):
        elements, locations = rfq(
            keyword("k1", "Mechanical", "pc"),
            pc=el("pc", "PartUsage", "PC-1", "caps", owner="pkg"),
            r=rel("r", "Subsetting", "pc", "ppc"),
        )
        n = convert_rfq(elements, locations)["versions"][""]["needs"]
        self.assertEqual(n["PC-1"]["specializes"], ["WSW-PC-1"])


if __name__ == "__main__":
    unittest.main()
