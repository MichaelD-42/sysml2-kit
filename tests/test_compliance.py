import unittest

from sysml2kit.compliance import compliance, table_md


def need(type_, title="", **fields):
    return {
        "type": type_,
        "title": title,
        "leaf": True,
        "platform": False,
        "variant": False,
        "domain": "",
        "owned_by": [],
        "allocated_to": [],
        "specializes": [],
        "satisfies": [],
        "matches": [],
        "partial_matches": [],
        "answers": [],
        **fields,
    }


def model(platform=True, domain="mech", **feature):
    """Feature F -> function FN -> component LC -> physical PC."""
    return {
        "CRS-1": need("crs", "Carry load"),
        "F": need("feature", **feature),
        "FN": need("function", owned_by=["F"], allocated_to=["LC"]),
        "LC": need("component", allocated_to=["PC"]),
        "PC": need("physical", platform=platform, domain=domain),
    }


class ComplianceTest(unittest.TestCase):
    def test_platform_feature_row(self):
        rows, findings = compliance(model(matches=["CRS-1"]))
        self.assertEqual(
            rows, [("CRS-1", "Carry load", ["F"], "platform", False, [], ["mech"])]
        )
        self.assertEqual(findings, [])

    def test_worst_reuse_wins(self):
        needs = model(matches=["CRS-1"])
        needs["F2"] = need("feature", matches=["CRS-1"], reuse="new")
        needs["F"]["reuse"] = "variant"
        rows, _ = compliance(needs)
        self.assertEqual(rows[0][3], "new")
        self.assertEqual(rows[0][2], ["F", "F2"])

    def test_unanswered_crs_is_a_finding(self):
        rows, findings = compliance({"CRS-1": need("crs", "Carry load")})
        self.assertEqual(findings, ["CRS-1: not answered"])
        self.assertEqual(rows[0][3], "")

    def test_feature_and_statement_both_listed(self):
        needs = model(matches=["CRS-1"])
        needs["CST-1"] = need("cst", answers=["CRS-1"], compliance="comply")
        rows, findings = compliance(needs)
        self.assertEqual(rows[0][2], ["F"])
        self.assertEqual(rows[0][5], [("CST-1", "comply")])
        self.assertEqual(findings, [])

    def test_statement_alone_answers(self):
        needs = {
            "CRS-1": need("crs"),
            "CST-1": need("cst", answers=["CRS-1"]),
        }
        self.assertEqual(compliance(needs)[1], [])

    def test_partial_only_is_answered_but_flagged(self):
        needs = model(partial_matches=["CRS-1"])
        rows, findings = compliance(needs)
        self.assertTrue(rows[0][4])
        self.assertEqual(
            findings,
            ["CRS-1: partial match without a system requirement stating the gap"],
        )
        needs["SR-1"] = need("sysreq", satisfies=["CRS-1"])
        needs["LC2"] = need("component", satisfies=["SR-1"], owned_by=["LC"])
        self.assertEqual(compliance(needs)[1], [])

    def test_gap_sr_outside_the_chain_does_not_count(self):
        needs = model(partial_matches=["CRS-1"])
        needs["SR-1"] = need("sysreq", satisfies=["CRS-1"])
        needs["OTHER"] = need("component", satisfies=["SR-1"])
        self.assertEqual(len(compliance(needs)[1]), 1)

    def test_incomplete_match_is_a_finding(self):
        needs = model(matches=["CRS-1"])
        del needs["LC"]["allocated_to"][:]
        rows, findings = compliance(needs)
        self.assertEqual(rows[0][3], "incomplete")
        self.assertEqual(
            findings, ["CRS-1: matched, but its chain reaches no physical component"]
        )

    def test_table_links_each_need(self):
        needs = model(matches=["CRS-1"])
        needs["CST-1"] = need("cst", answers=["CRS-1"])
        out = table_md(compliance(needs)[0])
        self.assertIn("{need}`CRS-1`", out)
        self.assertIn("{need}`F`", out)
        self.assertIn("{need}`CST-1`", out)
        self.assertIn("mech", out)

    def test_table_shows_statement_value(self):
        needs = {
            "CRS-1": need("crs"),
            "CST-1": need("cst", answers=["CRS-1"], compliance="not-comply"),
        }
        self.assertIn("{need}`CST-1` (not-comply)", table_md(compliance(needs)[0]))

    def test_table_escapes_pipes(self):
        needs = {"CRS-1": need("crs", "a | b")}
        out = table_md(compliance(needs)[0])
        self.assertIn("a \\| b", out)
