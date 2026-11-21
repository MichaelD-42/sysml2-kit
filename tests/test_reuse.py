import unittest

from sysml2kit.reuse import reuse, reused_pcs, unselected_variations


def need(type_, platform=False, variant=False, **links):
    return {
        "type": type_,
        "leaf": True,
        "platform": platform,
        "variant": variant,
        "owned_by": [],
        "allocated_to": [],
        "specializes": [],
        **links,
    }


def chain(pc, lc_platform=False):
    """Feature F owns function FN, allocated to LC, allocated to the given PCs."""
    return {
        "F": need("feature"),
        "FN": need("function", owned_by=["F"], allocated_to=["LC"]),
        "LC": need("component", platform=lc_platform, allocated_to=list(pc)),
    }


class ReuseTest(unittest.TestCase):
    def test_platform_chain(self):
        needs = {**chain(["PC"]), "PC": need("physical", platform=True)}
        self.assertEqual(reuse(needs), {"F": "platform"})
        self.assertEqual(reused_pcs(needs, "F"), {"PC"})

    def test_variant_chain(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", specializes=["PV"]),
            "PV": need("physical", platform=True, variant=True),
        }
        self.assertEqual(reuse(needs), {"F": "variant"})

    def test_mixed_chain_is_modified(self):
        needs = {
            **chain(["P1", "P2"]),
            "P1": need("physical", platform=True),
            "P2": need("physical"),
        }
        self.assertEqual(reuse(needs), {"F": "modified"})

    def test_all_new_is_new(self):
        needs = {**chain(["PC"]), "PC": need("physical")}
        self.assertEqual(reuse(needs), {"F": "new"})

    def test_no_physical_is_incomplete(self):
        self.assertEqual(reuse(chain([])), {"F": "incomplete"})

    def test_inherited_functions_count(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", platform=True),
            "RF": need("feature", specializes=["F"]),
        }
        self.assertEqual(reuse(needs), {"F": "platform", "RF": "platform"})

    def test_descendants_are_followed(self):
        needs = {
            "F": need("feature"),
            "FN": need("function", owned_by=["F"], allocated_to=["LC"]),
            "LC": need("component", leaf=False),
            "LC1": need("component", owned_by=["LC"], allocated_to=["PC"]),
            "PA": need("physical", leaf=False),
            "PC": need("physical", owned_by=["PA"], platform=True),
        }
        self.assertEqual(reused_pcs(needs, "F"), {"PC"})

    def test_composite_component_keeps_own_allocation(self):
        needs = {
            "F": need("feature"),
            "FN": need("function", owned_by=["F"], allocated_to=["LC"]),
            "LC": need("component", leaf=False, allocated_to=["PP"]),
            "LC1": need("component", owned_by=["LC"], allocated_to=["PN"]),
            "PP": need("physical", platform=True),
            "PN": need("physical"),
        }
        self.assertEqual(reuse(needs), {"F": "modified"})

    def test_unbacked_function_makes_feature_incomplete(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", platform=True),
            "FN2": need("function", owned_by=["F"]),
        }
        self.assertEqual(reuse(needs), {"F": "incomplete"})
        needs["FN2"]["allocated_to"] = ["LC2"]
        needs["LC2"] = need("component")
        self.assertEqual(reuse(needs), {"F": "incomplete"})

    def test_assembly_allocation_reaches_parts(self):
        needs = {
            **chain(["PA"]),
            "PA": need("physical", platform=True, leaf=False),
            "PC": need("physical", owned_by=["PA"]),
        }
        self.assertEqual(reuse(needs), {"F": "modified"})
        self.assertEqual(reused_pcs(needs, "F"), {"PA", "PC"})

    def variation(self, lc_targets):
        """Platform variation PV with variant children PV1 and PV2, in different domains."""
        return {
            **chain(lc_targets),
            "PV": need("physical", platform=True, leaf=False, domain="mech"),
            "PV1": need(
                "physical", platform=True, variant=True, owned_by=["PV"], domain="elec"
            ),
            "PV2": need(
                "physical", platform=True, variant=True, owned_by=["PV"], domain="sw"
            ),
        }

    def test_variation_without_selection_is_incomplete(self):
        needs = self.variation(["PV"])
        self.assertEqual(reuse(needs), {"F": "incomplete"})
        self.assertEqual(reused_pcs(needs, "F"), set())
        self.assertEqual(unselected_variations(needs, "F"), {"PV"})

    def test_selected_variant_reaches_only_that_variant(self):
        needs = self.variation(["PC"])
        needs["PC"] = need("physical", specializes=["PV1"])
        self.assertEqual(reuse(needs), {"F": "variant"})
        self.assertEqual(reused_pcs(needs, "F"), {"PC"})
        self.assertEqual(unselected_variations(needs, "F"), set())

    def test_allocation_to_a_variant_reaches_its_parts(self):
        needs = self.variation(["PV1"])
        needs["PV1P"] = need("physical", platform=True, owned_by=["PV1"])
        self.assertEqual(reused_pcs(needs, "F"), {"PV1", "PV1P"})
        self.assertEqual(reuse(needs), {"F": "variant"})

    def test_cycle_terminates(self):
        needs = {
            "A": need("feature", specializes=["B", "A"], owned_by=["B"]),
            "B": need("feature", specializes=["A"], owned_by=["A"]),
        }
        self.assertEqual(reuse(needs), {"A": "incomplete", "B": "incomplete"})


if __name__ == "__main__":
    unittest.main()
