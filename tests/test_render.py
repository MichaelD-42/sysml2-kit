import re
import unittest
import xml.etree.ElementTree as ET
from typing import ClassVar

from sysml2kit.render import CHAR_W, trace_svg, use_case_svg, use_cases

SVG = "{http://www.w3.org/2000/svg}"


def need(type_, **links):
    return {"type": type_, "title": type_, "docname": "model", **links}


def segments(d):
    """Axis-aligned segments of a path made of M/H/V commands; curves are skipped."""
    if "C" in d:
        return []
    x = y = 0.0
    out = []
    for cmd, args in re.findall(r"([MHV])([-\d.,]+)", d):
        if cmd == "M":
            x, y = map(float, args.split(","))
        elif cmd == "H":
            out.append(((x, y), (float(args), y)))
            x = float(args)
        else:
            out.append(((x, y), (x, float(args))))
            y = float(args)
    return out


class TraceSvgTest(unittest.TestCase):
    NEEDS: ClassVar = {
        "CRS-001": need("crs"),
        "SR-001": need("sysreq", satisfies=["CRS-001"]),
        "SR-002": need("sysreq", satisfies=["CRS-001"]),
        "F-001": need("function", allocated_to=["LC-001"]),
        "LC-001": need("component", satisfies=["SR-001", "SR-002"]),
        "STC-001": need("systest", verifies=["SR-002"]),
    }

    def setUp(self):
        self.root = ET.fromstring(trace_svg(self.NEEDS))

    def edges(self):
        return [
            p.get("d") for p in self.root.iter(f"{SVG}path") if "h24" not in p.get("d")
        ]  # not legend

    def test_every_link_is_drawn(self):
        self.assertEqual(len(self.edges()), 6)

    def test_each_box_links_to_its_need(self):
        links = {
            a.get("href"): [t.text for t in a.iter(f"{SVG}text")]
            for a in self.root.iter(f"{SVG}a")
        }
        self.assertEqual(len(links), len(self.NEEDS))
        self.assertEqual(links["model.html#SR-001"][0], "SR-001")

    def test_a_need_without_a_page_is_not_linked(self):
        needs = {
            "CRS-001": {**need("crs"), "docname": "customer/requirements"},
            "X-1": {**need("crs"), "docname": None},
        }
        root = ET.fromstring(trace_svg(needs))
        self.assertEqual(
            [a.get("href") for a in root.iter(f"{SVG}a")],
            ["customer/requirements.html#CRS-001"],
        )

    def test_routed_edges_never_run_through_a_box(self):
        boxes = [
            tuple(float(r.get(k)) for k in ("x", "y", "width", "height"))
            for r in self.root.iter(f"{SVG}rect")
            if r.get("class") == "s2k-box"
        ]
        routed = [d for d in self.edges() if "C" not in d]
        self.assertTrue(routed, "the fixture must contain an edge that skips a column")
        for d in routed:
            for (x1, y1), (x2, y2) in segments(d):
                for bx, by, bw, bh in boxes:
                    if y1 == y2:
                        crosses = (
                            by < y1 < by + bh
                            and max(x1, x2) > bx
                            and min(x1, x2) < bx + bw
                        )
                    else:
                        crosses = (
                            bx < x1 < bx + bw
                            and max(y1, y2) > by
                            and min(y1, y2) < by + bh
                        )
                    self.assertFalse(
                        crosses, f"{d} runs through the box at ({bx}, {by})"
                    )


class UseCaseSvgTest(unittest.TestCase):
    def test_extracts_subject_and_actors_and_draws_them(self):
        elements = [
            {
                "@id": "uc",
                "@type": "UseCaseUsage",
                "declaredShortName": "UC-001",
                "name": "commute",
                "ownedMembership": [{"@id": "sm"}, {"@id": "am"}],
            },
            {
                "@id": "sm",
                "@type": "SubjectMembership",
                "ownedMemberElement": {"@id": "s"},
            },
            {"@id": "s", "@type": "ReferenceUsage", "name": "vehicle"},
            {
                "@id": "am",
                "@type": "ActorMembership",
                "ownedMemberElement": {"@id": "a"},
            },
            {"@id": "a", "@type": "PartUsage", "name": "driver"},
        ]
        cases = use_cases(elements)
        self.assertEqual(cases, [("vehicle", [("UC-001", "commute", ["driver"])])])
        root = ET.fromstring(use_case_svg(*cases[0]))
        self.assertEqual(
            sorted(t.text for t in root.iter(f"{SVG}text")),
            ["UC-001", "commute", "driver", "vehicle"],
        )
        self.assertEqual(len(list(root.iter(f"{SVG}ellipse"))), 1)
        link = next(root.iter(f"{SVG}a"))
        self.assertEqual(link.get("href"), "#UC-001")
        self.assertEqual(len(list(link.iter(f"{SVG}ellipse"))), 1)

    def test_use_cases_without_an_id_are_still_drawn(self):
        elements = [
            {"@id": "a", "@type": "UseCaseUsage", "name": "draft"},
            {"@id": "b", "@type": "UseCaseUsage", "name": "other draft"},
        ]
        cases = use_cases(elements)
        self.assertEqual(
            cases, [("system", [("", "draft", []), ("", "other draft", [])])]
        )
        root = ET.fromstring(use_case_svg(*cases[0]))
        self.assertEqual(len(list(root.iter(f"{SVG}ellipse"))), 2)
        self.assertEqual(list(root.iter(f"{SVG}a")), [], "no id, nothing to link to")

    def test_subjects_with_one_name_but_different_types_get_separate_diagrams(self):
        def case(uc, subject, type_id=None):
            s = {"@id": subject, "@type": "ReferenceUsage", "name": "vehicle"}
            if type_id:
                s["type"] = [{"@id": type_id}]
            return [
                {
                    "@id": uc,
                    "@type": "UseCaseUsage",
                    "name": uc,
                    "ownedMembership": [{"@id": uc + "m"}],
                },
                {
                    "@id": uc + "m",
                    "@type": "SubjectMembership",
                    "ownedMemberElement": {"@id": subject},
                },
                s,
            ]

        types = [
            {
                "@id": "car",
                "@type": "PartDefinition",
                "name": "Car",
                "qualifiedName": "P::Car",
            },
            {
                "@id": "truck",
                "@type": "PartDefinition",
                "name": "Truck",
                "qualifiedName": "P::Truck",
            },
        ]
        split = use_cases(
            case("drive", "s1", "car") + case("haul", "s2", "truck") + types
        )
        self.assertEqual(
            split,
            [
                ("vehicle : P::Car", [("", "drive", [])]),
                ("vehicle : P::Truck", [("", "haul", [])]),
            ],
        )
        # untyped subjects of one name are the same subject, as in the example model
        merged = use_cases(case("drive", "s1") + case("haul", "s2"))
        self.assertEqual(merged, [("vehicle", [("", "drive", []), ("", "haul", [])])])

    def test_null_membership_list_is_no_members(self):
        elements = [
            {"@id": "a", "@type": "UseCaseUsage", "name": "x", "ownedMembership": None}
        ]
        self.assertEqual(use_cases(elements), [("system", [("", "x", [])])])

    def test_long_actor_names_stay_inside_the_image(self):
        actor = "maintenanceTechnicianOnDuty"
        root = ET.fromstring(use_case_svg("s", [("UC-001", "service", [actor])]))
        label = next(t for t in root.iter(f"{SVG}text") if t.text == actor)
        self.assertGreaterEqual(float(label.get("x")) - CHAR_W * len(actor) / 2, 0)


if __name__ == "__main__":
    unittest.main()
