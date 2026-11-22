import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from explorer import db, load, views
from explorer.graph import Edge, Graph, Node
from tests.support import RFQ, rfq

NEEDS = RFQ / "build" / "needs" / "needs.json"


def part(key, qualified, platform=None, kind="PartUsage"):
    labels = ["Node", "Element", kind]
    props = {"key": key, "name": qualified.split("::")[-1], "qualifiedName": qualified}
    return Node(key, labels, props | {"kind": kind, "platform": platform})


class DefaultFocusTest(unittest.TestCase):
    """The first top-level project part, by key."""

    def test_falls_back_to_a_top_level_project_part(self):
        graph = db.Graph()
        self.addCleanup(graph.close)
        nodes = [
            part("pkg", "Shop", kind="Package"),
            part("A-1", "Shop::platformBench", platform=True),
            part("A-2", "Shop::bench::vice"),
            part("B-1", "Shop::bench"),
            part("C-1", "Shop::lathe"),
        ]
        owns = [("pkg", "A-1"), ("pkg", "B-1"), ("pkg", "C-1"), ("B-1", "A-2")]
        load.write(
            Graph({n.key: n for n in nodes}, [Edge(a, "OWNS", b) for a, b in owns]),
            graph,
        )
        for kind in ("context", "boundary", "interfaces", "composition"):
            with self.subTest(kind=kind):
                self.assertEqual(views.view(graph, kind, None)["focus"], "B-1")


class SmallGraphTest(unittest.TestCase):
    def setUp(self):
        self.graph = db.Graph()
        self.addCleanup(self.graph.close)

    def test_vmodel_places_software_requirements_with_their_results(self):
        nodes = [
            Node("SWR-1", ["Node", "Need", "swreq"], {"key": "SWR-1"}),
            Node(
                "testresult__a",
                ["Node", "Need", "testresult"],
                {"key": "testresult__a", "result": "passed"},
            ),
        ]
        load.write(
            Graph({n.key: n for n in nodes}, [Edge("testresult__a", "TESTS", "SWR-1")]),
            self.graph,
        )
        v = views.view(self.graph, "vmodel", None)
        at = {n["key"]: (n["level"], n["side"]) for n in v["nodes"]}
        self.assertEqual(at, {"SWR-1": (4, "left"), "testresult__a": (4, "right")})

    def test_a_rule_with_local_and_network_checks_is_on_the_type_and_the_link(self):
        crs = {"local": {"properties": {"type": {"const": "crs"}}}}
        rule = {
            "id": "both",
            "select": {"properties": {"type": {"const": "sysreq"}}},
            "validate": {
                "local": {"required": ["title"]},
                "network": {"satisfies": {"contains": crs}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            shutil.copy(RFQ / "docs" / "ubproject.toml", docs)
            (docs / "schemas.json").write_text(json.dumps({"schemas": [rule]}))
            v = views.metamodel(self.graph, Path(tmp))
        sysreq = next(n for n in v["nodes"] if n["key"] == "type:sysreq")
        self.assertEqual(sysreq["rules"], ["both"])
        link = next(
            e
            for e in v["edges"]
            if (e["src"], e["type"], e["dst"])
            == ("type:sysreq", "SATISFIES", "type:crs")
        )
        self.assertEqual(link["rules"], ["both"])

    def test_a_project_added_need_type_goes_under_an_other_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            toml = (RFQ / "docs" / "ubproject.toml").read_text()
            toml += '\n[[needs.types]]\ndirective = "hazard"\ntitle = "Hazard"\nprefix = "HAZ-"\n'
            (docs / "ubproject.toml").write_text(toml)
            (docs / "schemas.json").write_text(json.dumps({"schemas": []}))
            v = views.metamodel(self.graph, Path(tmp))
        parents = {n["key"]: n["parent"] for n in v["nodes"]}
        self.assertEqual(parents["type:hazard"], "layer:?")
        self.assertIn("layer:?", parents)


class ViewsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = rfq()

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()

    def view(self, kind, focus=None):
        v = views.view(self.graph, kind, focus, NEEDS, RFQ)
        self.assertEqual(bool(v["reason"]), not v["nodes"])
        return v

    def names(self, v):
        return {n["name"] for n in v["nodes"]}

    def test_context_default(self):
        v = self.view("context")
        self.assertEqual(v["focus"], "LC-100")
        self.assertLessEqual(
            {
                "seat",
                "seatControlUnit",
                "occupant",
                "workshopTester",
                "endOfLineTester",
            },
            self.names(v),
        )

    def test_boundary_of_the_driver_switch(self):
        v = self.view("boundary", "LC-101")
        ports = {n["name"] for n in v["nodes"] if n["parent"] == "LC-101"}
        self.assertLessEqual({"lin", "supply"}, ports)

    def test_activity(self):
        v = self.view("activity", "SSW-FEAT-001")
        edges = {(e["src"], e["dst"], e["type"]) for e in v["edges"]}
        self.assertIn(("SSW-F-001", "SSW-F-002", "SUCCESSION"), edges)
        self.assertIn(
            ("FLOW", "KeyState"), {(e["type"], e["label"]) for e in v["edges"]}
        )

    def test_activity_without_actions(self):
        v = self.view("activity", "PC-101")
        self.assertEqual(v["nodes"], [])
        self.assertTrue(v["reason"])

    def test_variants_mark_the_rfq_selection(self):
        v = self.view("variants", "SeatSwitchPhysical::housing")
        selected = {n["key"]: n.get("selected") for n in v["nodes"]}
        self.assertTrue(selected["SSW-PC-002"])
        self.assertTrue(selected["SSW-PC-003"])
        self.assertTrue(selected["PC-101"])
        self.assertIn(
            ("PC-101", "SSW-PC-002", "SPECIALIZES"),
            {(e["src"], e["dst"], e["type"]) for e in v["edges"]},
        )
        v = self.view("variants", "SSW-PC-011")
        selected = {n["key"]: n.get("selected") for n in v["nodes"]}
        self.assertTrue(selected["SSW-PC-015"])
        self.assertFalse(selected["SSW-PC-012"])

    def test_trace(self):
        keys = {n["key"] for n in self.view("trace", "CRS-301")["nodes"]}
        self.assertLessEqual({"CON-101", "STC-101", "CTR-003"}, keys)

    def test_trace_stops_at_other_requirements(self):
        # CTR-003 also applies to CRS-302
        keys = {n["key"] for n in self.view("trace", "CRS-301")["nodes"]}
        self.assertNotIn("CRS-302", keys)

    def test_trace_shows_the_constraint(self):
        v = self.view("trace", "CRS-301")
        kinds = {n["key"]: n["kind"] for n in v["nodes"]}
        self.assertEqual(kinds["CON-101"], "ConstraintUsage")
        self.assertIn(
            ("CON-101", "CRS-301", "SATISFIES"),
            {(e["src"], e["dst"], e["type"]) for e in v["edges"]},
        )

    def test_trace_default_has_links(self):
        self.assertEqual(self.view("trace")["focus"], "CRS-201")

    def test_context_draws_each_thing_once(self):
        v = self.view("context")
        names = [n["name"] for n in v["nodes"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual([n["key"] for n in v["nodes"]].count(v["focus"]), 1)

    def test_usecase_actors_once(self):
        names = [n["name"] for n in self.view("usecases")["nodes"]]
        self.assertEqual(len(names), len(set(names)))

    def test_defaults_prefer_the_project_over_the_platform(self):
        # the project feature with the most actions, so the default is not a single box
        self.assertEqual(self.view("activity")["focus"], "FEAT-102")
        self.assertEqual(self.view("usecases")["focus"], "UC-101")
        self.assertEqual(self.view("variants")["focus"], "SSW-PC-001")

    def test_compliance(self):
        # two tables: customer requirements, then customer test requirements
        crs, ctr = (
            (RFQ / "docs" / "_generated" / "compliance.md").read_text().split("\n\n")
        )
        first = re.compile(r"^\| \{need\}`([^`]+)`", re.MULTILINE)
        v = self.view("compliance")
        self.assertEqual([r["crs"] for r in v["rows"]], first.findall(crs))
        self.assertEqual([r["ctr"] for r in v["ctrs"]], first.findall(ctr))
        row = next(r for r in v["rows"] if r["crs"] == "CRS-301")
        self.assertEqual(row["class"], "non-functional")
        self.assertEqual(row["constraints"], ["CON-101"])
        self.assertEqual(row["satisfied_by"], ["CON-101"])
        by = {r["crs"]: r["satisfied_by"] for r in v["rows"]}
        self.assertEqual(by["CRS-507"], ["SR-115"])  # textual SR answers a constraint
        self.assertIn("SR-119", by["CRS-304"])  # the partial's gap SR
        self.assertEqual(by["CRS-201"], [])  # functional: features, not satisfiers
        rating = {r["crs"]: r["rating"] for r in v["rows"]}
        self.assertEqual(rating["CRS-301"], "comply")
        self.assertEqual(rating["CRS-304"], "partial")
        self.assertEqual(rating["CRS-207"], "not offered")
        self.assertEqual(rating["CRS-901"], "commercial")
        self.assertEqual(rating["CRS-101"], "information")
        s = v["summary"]
        self.assertEqual(s["rated"], 40)  # 45 CRS less 5 information
        self.assertEqual(s["ratings"]["partial"]["count"], 1)
        self.assertEqual(sum(x["count"] for x in s["ratings"].values()), 40)
        self.assertEqual(s["verified"]["pct"], 100)
        self.assertEqual(s["ctrs_implemented"]["pct"], 100)
        self.assertEqual(sum(x["count"] for x in s["reuse"].values()), s["reused"])
        ctr003 = next(r for r in v["ctrs"] if r["ctr"] == "CTR-003")
        self.assertEqual(ctr003["implemented_by"], ["STC-101"])
        self.assertIn("CTR-003", {n["key"] for n in v["nodes"]})

    def test_every_default_renders(self):
        for kind in views.KINDS:
            with self.subTest(kind=kind):
                self.assertTrue(self.view(kind)["nodes"])

    def test_tree(self):
        roots = views.tree(self.graph)
        self.assertIn("SeatSwitchRfqPhysical", [r["name"] for r in roots])
        self.assertEqual({r["kind"] for r in roots}, {"Package"})

    def requirement(self, group, key):
        groups = {g["name"]: g for g in views.requirements_tree(self.graph)}
        return next(c for c in groups[group]["children"] if c["key"] == key)

    def test_requirements_tree_groups_and_classes(self):
        groups = views.requirements_tree(self.graph)
        self.assertEqual(
            [g["name"] for g in groups][:3],
            [
                "Customer requirements",
                "Customer test requirements",
                "System requirements",
            ],
        )
        self.assertIsNone(groups[0]["key"])
        crs = self.requirement("Customer requirements", "CRS-304")
        self.assertEqual(crs["class"], "non-functional")
        # the tree lists requirements only; what they link to is carried for the inspector
        self.assertEqual(crs["children"], [])
        links = {(c["rel"], c["key"]) for c in crs["links"]}
        self.assertIn(("satisfied by (partial)", "CON-104"), links)
        self.assertNotIn(("satisfied by", "CON-104"), links)
        self.assertIn(("satisfied by", "SR-119"), links)
        self.assertIn(("test requirement", "CTR-002"), links)

    def test_requirements_tree_lists_what_implements_a_ctr(self):
        ctr = self.requirement("Customer test requirements", "CTR-003")
        self.assertEqual(ctr["kind"], "ctr")
        links = {(c["rel"], c["key"]) for c in ctr["links"]}
        self.assertIn(("implemented by", "STC-101"), links)
        self.assertLessEqual(
            {("applies to", "CRS-301"), ("applies to", "CRS-302")}, links
        )
        atc = self.requirement("Acceptance tests", "ATC-106")
        self.assertIn(
            ("implements", "CTR-009"), {(c["rel"], c["key"]) for c in atc["links"]}
        )

    def paths(self, nodes, prefix=()):
        for n in nodes:
            here = prefix + (n["key"],)
            yield here
            yield from self.paths(n["children"], here)

    def test_rflp_tree_follows_the_chain(self):
        own = views.rflp_tree(self.graph)
        all_paths = set(self.paths(own))
        chain = ("LC-100", "UC-102", "FEAT-102", "F-101", "LC-101")
        self.assertIn(chain + ("PC-101",), all_paths)
        self.assertIn(chain + ("PC-102",), all_paths)
        # the product is the root, its use cases below it, shown by their titles
        self.assertEqual([n["key"] for n in own], ["LC-100"])
        self.assertEqual(own[0]["name"], "OEM_SeatSwitch")
        ucs = own[0]["children"]
        self.assertEqual(
            [n["key"] for n in ucs], ["UC-101", "UC-102", "UC-103", "UC-104", None]
        )
        self.assertEqual(
            ucs[0]["name"], "The occupant wants to adjust the seat position"
        )
        platform = views.rflp_tree(self.graph, platform=True)
        self.assertEqual([n["key"] for n in platform], ["SSW-LC-001"])
        self.assertEqual(platform[0]["name"], "ACME_SeatSwitch")
        self.assertIn(
            (
                "SSW-LC-001",
                "SSW-UC-001",
                "SSW-FEAT-001",
                "SSW-F-001",
                "SSW-LC-003",
                "SSW-PC-008",
            ),
            set(self.paths(platform)),
        )
        self.assertFalse(
            any(
                k.startswith(("LC-", "PC-", "FEAT-", "UC-"))
                for p in self.paths(platform)
                for k in p
                if k
            )
        )

    def test_rflp_tree_is_what_the_product_consists_of(self):
        own = views.rflp_tree(self.graph)
        all_paths = set(self.paths(own))
        nodes = {}
        for n in self.walk(own):
            nodes.setdefault(n["key"], n)
        # an RFQ feature lists the platform functions it inherits, marked platform
        below = {n["key"] for n in self.walk(nodes["FEAT-104"]["children"])}
        self.assertIn("SSW-F-011", below)
        self.assertTrue(nodes["SSW-F-011"]["platform"])
        comfort = {n["key"] for n in nodes["FEAT-102"]["children"]}
        self.assertIn("F-101", comfort)
        self.assertTrue(any(k.startswith("SSW-F-") for k in comfort))
        # an inherited function reaches its logical component, the component its physical parts,
        # a software component its units
        self.assertTrue(
            any(p[-3:] == ("FEAT-104", "SSW-F-011", "SSW-LC-005") for p in all_paths)
        )
        self.assertTrue(any(p[-2:] == ("SSW-LC-005", "SSW-PC-034") for p in all_paths))
        # the product's physical breakdown: assemblies down to software units, in both trees
        firmware = ("SSW-PC-016", "SSW-PC-034", "SSW-PC-035")
        self.assertIn(("LC-100", None) + firmware, all_paths)
        for top in ("SSW-PC-001", "SSW-PC-007", "SSW-PC-011"):
            self.assertIn(("LC-100", None, top), all_paths)
        platform = set(self.paths(views.rflp_tree(self.graph, platform=True)))
        self.assertIn(("SSW-LC-001", None) + firmware, platform)
        # a part is expanded in the breakdown; its rows under a logical component say where
        under_lc = [
            n
            for n in self.walk(nodes["SSW-LC-005"]["children"])
            if n["key"] == "SSW-PC-034"
        ]
        self.assertEqual(under_lc[0]["again"], "Physical breakdown")
        # a position's part shows the variant it selects
        self.assertTrue(
            any(p[-3:] == ("LC-101", "PC-101", "SSW-PC-002") for p in all_paths)
        )
        # a shared component is expanded once; later rows are marked and have no subtree
        rows = [n for n in self.walk(own) if n["key"] == "SSW-LC-004"]
        self.assertGreater(len(rows), 1)
        self.assertEqual(
            [bool(n["children"]) for n in rows], [True] + [False] * (len(rows) - 1)
        )
        self.assertEqual(
            rows[1]["again"], "The occupant wants to adjust the seat position"
        )

    def test_activity_of_a_feature_includes_inherited_actions(self):
        v = self.view("activity", "FEAT-104")
        keys = {n["key"] for n in v["nodes"]}
        self.assertLessEqual({"SSW-F-011", "SSW-F-012", "SSW-F-013"}, keys)
        self.assertIn(
            ("SSW-F-012", "SSW-F-013", "SUCCESSION"),
            {(e["src"], e["dst"], e["type"]) for e in v["edges"]},
        )
        keys = {n["key"] for n in self.view("activity", "FEAT-102")["nodes"]}
        self.assertIn("F-101", keys)
        self.assertTrue(any(k.startswith("SSW-F-") for k in keys))

    def walk(self, nodes):
        for n in nodes:
            yield n
            yield from self.walk(n["children"])

    def test_rflp_trees_carry_what_uses_the_platform(self):
        own = {
            n["key"]: n
            for n in self.walk(views.rflp_tree(self.graph))
            if not n["platform"]
        }
        platform = {
            n["key"]: n for n in self.walk(views.rflp_tree(self.graph, platform=True))
        }
        self.assertIn("SSW-PC-001", own["PC-101"]["uses"])
        self.assertIn("SSW-LC-001", own["LC-101"]["uses"])
        # the housing variation is no RFLP node; its variants are
        self.assertIn("PC-101", platform["SSW-PC-002"]["uses"])

    def test_requirement_links_name_use_cases_by_title(self):
        names = {
            x["key"]: x["name"]
            for g in views.requirements_tree(self.graph)
            for r in g["children"]
            for x in r["links"]
        }
        self.assertEqual(
            names["UC-101"], "The occupant wants to adjust the seat position"
        )

    def test_vmodel_levels_and_sides(self):
        v = views.view(self.graph, "vmodel", None)
        at = {n["key"]: (n["level"], n["side"]) for n in v["nodes"]}
        self.assertEqual(at["CRS-301"], (1, "left"))
        self.assertEqual(at["ATC-101"], (1, "right"))
        self.assertEqual(at["CTR-003"], (1, "right"))
        self.assertEqual(at["SR-101"], (2, "left"))
        self.assertEqual(at["CON-101"], (2, "left"))
        self.assertEqual(at["STC-101"], (2, "right"))
        self.assertEqual(at["FEAT-102"], (3, "left"))
        self.assertEqual(at["LC-101"], (4, "left"))
        self.assertEqual(at["PC-101"], (5, "bottom"))
        self.assertNotIn("SSW-FEAT-001", at)
        edges = {(e["src"], e["dst"], e["type"]) for e in v["edges"]}
        self.assertIn(("STC-101", "CTR-003", "IMPLEMENTS"), edges)
        self.assertIn(("ATC-106", "CTR-009", "IMPLEMENTS"), edges)
        self.assertIn(("CON-101", "CRS-301", "SATISFIES"), edges)
        self.assertIn(("STC-102", "CON-103", "VERIFIES"), edges)
        self.assertIn(("CTR-003", "CRS-301", "APPLIES_TO"), edges)
        self.assertEqual(v["empty"], [3, 4])

    def test_vmodel_of_another_focus_is_the_whole_v(self):
        v = views.view(self.graph, "vmodel", "LC-101")
        self.assertEqual(v["focus"], "LC-101")
        self.assertIn("CRS-201", {n["key"] for n in v["nodes"]})

    def test_vmodel_of_one_requirement(self):
        keys = {n["key"] for n in views.view(self.graph, "vmodel", "CRS-301")["nodes"]}
        self.assertLessEqual({"CTR-003", "STC-101"}, keys)
        self.assertNotIn("CRS-302", keys)
        self.assertNotIn("CTR-001", keys)

    def test_metamodel(self):
        v = self.view("metamodel")
        kinds = {n["key"]: n["kind"] for n in v["nodes"]}
        edges = {(kinds[e["src"]], e["type"], kinds[e["dst"]]): e for e in v["edges"]}
        types = {n["kind"]: n for n in v["nodes"] if n["parent"]}
        self.assertEqual(types["crs"]["parent"], "layer:R")
        self.assertEqual(types["ctr"]["parent"], "layer:V")
        self.assertEqual(types["swreq"]["parent"], "layer:P")
        self.assertEqual(types["crs"]["count"], len(types["crs"]["instances"]))
        self.assertGreater(types["crs"]["count"], 0)
        self.assertEqual(types["crs"]["rules"], ["crs-class"])
        self.assertEqual(types["prq"]["count"], 0)  # declared, none in this project
        satisfies = edges[("constraint", "SATISFIES", "crs")]
        self.assertGreater(satisfies["count"], 0)
        self.assertEqual(satisfies["count"], len(satisfies["instances"]))
        self.assertIn("crs-satisfied", satisfies["rules"])
        self.assertIn("constraint-satisfies", satisfies["rules"])
        self.assertFalse(satisfies["unused"])
        implements = edges[("systest", "IMPLEMENTS", "ctr")]
        self.assertGreater(implements["count"], 0)
        self.assertEqual(
            sorted(implements["rules"]), ["ctr-implemented", "systest-implements"]
        )
        # a rule's link the project has no instance of
        unused = edges[("sysreq", "SATISFIES", "prq")]
        self.assertEqual((unused["count"], unused["unused"]), (0, True))
        self.assertIn("partial_matches", v["unused_links"])
        self.assertNotIn("satisfies", v["unused_links"])
        # ownership is drawn once, as the declared owned_by link
        self.assertNotIn("OWNS", {e["type"] for e in v["edges"]})
        self.assertIn(("component", "OWNED_BY", "component"), edges)
        # most rules select platform: false, so counts say how many are platform
        self.assertEqual(types["sysreq"]["platform"], 14)
        self.assertEqual(types["crs"]["platform"], 0)
        allocated = edges[("component", "ALLOCATED_TO", "physical")]
        self.assertGreater(allocated["platform"], 0)
        self.assertEqual(
            allocated["label"],
            f"allocated to ({allocated['count']}, {allocated['platform']} platform)",
        )
        self.assertEqual(satisfies["label"], f"satisfies ({satisfies['count']})")

    def edges(self, v):
        names = {n["key"]: n["name"] for n in v["nodes"]}
        return {(names[e["src"]], e["type"], names[e["dst"]]) for e in v["edges"]}

    def test_context_shows_the_harness(self):
        v = self.view("context", "LC-100")
        self.assertIn("seatHarness", self.names(v))
        edges = self.edges(v)
        self.assertIn(("seatHarness", "CONNECTS", "OEM_SeatSwitch"), edges)
        self.assertIn(("seatControlUnit", "CONNECTS", "seatHarness"), edges)

    def test_context_of_an_inner_component(self):
        v = self.view("context", "SSW-LC-005")
        self.assertIn("switchController", self.names(v))

    def test_context_of_a_part_connected_to_nothing(self):
        v = views.view(self.graph, "context", "LC-101")
        self.assertEqual(v["reason"], "LC-101 is connected to nothing in its owner")

    def test_boundary_shows_the_pin_mapping(self):
        v = self.view("boundary", "SSW-PC-022")
        edges = {frozenset((a, b)) | {t} for a, t, b in self.edges(v)}
        for pin, port in (
            ("pin1Kl30", "supply"),
            ("pin2Kl31", "ground"),
            ("pin3Lin", "lin"),
        ):
            with self.subTest(pin=pin):
                self.assertIn(frozenset((pin, port, "BINDS")), edges)
        self.assertIn(frozenset(("pin1Kl30", "kl30", "CONNECTS")), edges)

    def test_boundary_of_a_selected_variant_has_the_variation_ports(self):
        v = self.view("boundary", "PC-102")
        ports = {n["name"] for n in v["nodes"] if n["parent"] == "PC-102"}
        self.assertLessEqual({"contacts", "levelLeds"}, ports)

    def test_structure_views_of_a_port_show_its_owner(self):
        for kind in ("boundary", "interfaces"):
            with self.subTest(kind=kind):
                v = self.view(kind, "SSW-PI-007")
                self.assertEqual(v["focus"], "SSW-PI-007")
                self.assertLessEqual(
                    {"SSW-PC-022", "SSW-PI-007"}, {n["key"] for n in v["nodes"]}
                )

    def test_firmware_composition_has_components_and_units(self):
        v = self.view("composition", "SSW-PC-016")
        edges = {(e["src"], e["dst"]) for e in v["edges"]}
        self.assertIn(("SSW-PC-016", "SSW-PC-034"), edges)
        self.assertIn(("SSW-PC-034", "SSW-PC-035"), edges)

    def test_composition_shows_shared_platform_parts_under_every_user(self):
        v = self.view("composition", "LC-100")
        edges = {(e["src"], e["dst"]) for e in v["edges"]}
        for switch in ("LC-101", "LC-102", "LC-103", "LC-104"):
            with self.subTest(switch=switch):
                self.assertIn((switch, "SSW-LC-003"), edges)
        self.assertNotIn(("LC-100", "SSW-LC-003"), edges)
        keys = [n["key"] for n in v["nodes"]]
        self.assertEqual(len(keys), len(set(keys)))
        # a tree stays a tree: one owner edge per part
        firmware = self.view("composition", "SSW-PC-016")
        self.assertEqual(len(firmware["edges"]), len(firmware["nodes"]) - 1)

    def test_composition_of_a_leaf(self):
        v = views.view(self.graph, "composition", "SSW-PC-035")
        self.assertEqual(v["reason"], "SSW-PC-035 has no parts")

    def test_activity_of_a_function_is_its_feature(self):
        v = self.view("activity", "SSW-F-001")
        self.assertEqual(v["focus"], "SSW-F-001")
        self.assertLessEqual({"SSW-F-001", "SSW-F-002"}, {n["key"] for n in v["nodes"]})

    def test_variants_of_a_selection_is_its_variation(self):
        v = self.view("variants", "PC-101")
        self.assertEqual(v["focus"], "PC-101")
        self.assertIn("SSW-PC-001", {n["key"] for n in v["nodes"]})

    def test_usecases_show_titles(self):
        v = self.view("usecases", "UC-101")
        names = {n["key"]: n["name"] for n in v["nodes"]}
        self.assertEqual(
            names["UC-104"],
            "The end-of-line tester wants to flash, code and test each switch for its seat position",
        )

    def test_product_overview(self):
        v = self.view("product")
        self.assertEqual(v["focus"], "LC-100")
        nodes = {n["key"]: n for n in v["nodes"]}
        tags = {
            k: [a["name"] for a in n["compartments"]["attributes"]]
            for k, n in nodes.items()
        }
        parent = {k: n["parent"] for k, n in nodes.items()}
        names = {n["name"]: k for k, n in nodes.items()}
        # the columns, in order
        groups = [n for n in v["nodes"] if n["kind"] == "group" and n["parent"] is None]
        self.assertEqual(
            [g["name"] for g in sorted(groups, key=lambda g: g["partition"])],
            ["Context", "Use cases", "Features", "Logical", "Physical"],
        )
        # context: actors and the vehicle side, not the product itself
        self.assertLessEqual(
            {"occupant", "seatControlUnit", "seatHarness", "endOfLineTester"},
            set(names),
        )
        self.assertEqual(parent[names["seatHarness"]], "group:context")
        # use cases with the features they perform, inherited functions counted
        self.assertLessEqual({"UC-101", "UC-102", "UC-103", "UC-104"}, set(nodes))
        self.assertEqual(
            nodes["UC-101"]["name"], "The occupant wants to adjust the seat position"
        )
        self.assertIn("8 functions", tags["FEAT-102"])
        self.assertIn("4 functions", tags["FEAT-104"])
        edges = {(e["src"], e["dst"], e["type"]) for e in v["edges"]}
        self.assertIn(("UC-101", "FEAT-104", "PERFORMS"), edges)
        self.assertIn((names["occupant"], "UC-101", "ACTOR"), edges)
        # logical: the positions under the product, with the variants they select; the blocks
        self.assertEqual(parent["LC-101"], "LC-100")
        self.assertLessEqual(
            {"housing: housingLH", "buttonSet: massageHeatingCooling"},
            set(tags["LC-101"]),
        )
        self.assertIn("SSW-LC-008", nodes)
        self.assertIn(("FEAT-104", "SSW-LC-005", "ALLOCATED_TO"), edges)
        # physical by domain, top level only; software components with their unit counts
        self.assertEqual(parent["SSW-PC-016"], "group:SW")
        self.assertEqual(parent["SSW-PC-034"], "SSW-PC-016")
        self.assertIn("6 units", tags["SSW-PC-034"])
        self.assertEqual(parent["SSW-PC-001"], "group:ME")
        self.assertIn("2 variants", tags["SSW-PC-001"])
        self.assertEqual(parent["SSW-PC-007"], "group:EE")
        self.assertNotIn("SSW-PC-035", nodes)
        self.assertNotIn("SSW-PC-008", nodes)
        # every edge ends on a drawn box
        self.assertLessEqual(
            {k for e in v["edges"] for k in (e["src"], e["dst"])}, set(nodes)
        )
        self.assertLess(len(v["nodes"]), 60)

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            views.view(self.graph, "nope", None)

    def test_unknown_focus(self):
        with self.assertRaises(KeyError):
            views.view(self.graph, "trace", "NOPE-1")


if __name__ == "__main__":
    unittest.main()
