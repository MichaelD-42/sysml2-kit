import unittest

from sysml2kit.reuse import (
    component_reuse,
    constraint_reuse,
    part_reuse,
    reuse,
    reused_pcs,
    unselected_variations,
)


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
        self.assertEqual(reuse(needs)["F"], "full")
        self.assertEqual(reused_pcs(needs, "F"), {"PC"})

    def test_variant_chain(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", specializes=["PV"]),
            "PV": need("physical", platform=True, variant=True),
        }
        self.assertEqual(reuse(needs)["F"], "full")

    def test_mixed_chain_is_partial(self):
        needs = {
            **chain(["P1", "P2"]),
            "P1": need("physical", platform=True),
            "P2": need("physical"),
        }
        self.assertEqual(reuse(needs)["F"], "partial")

    def test_all_new_is_new(self):
        needs = {**chain(["PC"]), "PC": need("physical")}
        self.assertEqual(reuse(needs)["F"], "new")

    def test_no_physical_is_incomplete(self):
        self.assertEqual(reuse(chain([]))["F"], "incomplete")

    def test_inherited_functions_count(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", platform=True),
            "RF": need("feature", specializes=["F"]),
        }
        self.assertEqual((reuse(needs)["F"], reuse(needs)["RF"]), ("full", "full"))

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
        self.assertEqual(reuse(needs)["F"], "partial")

    def test_unbacked_function_makes_feature_incomplete(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", platform=True),
            "FN2": need("function", owned_by=["F"]),
        }
        self.assertEqual(reuse(needs)["F"], "incomplete")
        needs["FN2"]["allocated_to"] = ["LC2"]
        needs["LC2"] = need("component")
        self.assertEqual(reuse(needs)["F"], "incomplete")

    def test_assembly_allocation_reaches_parts(self):
        needs = {
            **chain(["PA"]),
            "PA": need("physical", platform=True, leaf=False),
            "PC": need("physical", owned_by=["PA"]),
        }
        self.assertEqual(reuse(needs)["F"], "partial")
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
        self.assertEqual(reuse(needs)["F"], "incomplete")
        self.assertEqual(reused_pcs(needs, "F"), set())
        self.assertEqual(unselected_variations(needs, "F"), {"PV"})

    def test_selected_variant_reaches_only_that_variant(self):
        needs = self.variation(["PC"])
        needs["PC"] = need("physical", specializes=["PV1"])
        self.assertEqual(reuse(needs)["F"], "full")
        self.assertEqual(reused_pcs(needs, "F"), {"PC"})
        self.assertEqual(unselected_variations(needs, "F"), set())

    def test_part_subsetting_the_variation_is_unselected(self):
        needs = self.variation(["PC"])
        needs["PC"] = need("physical", specializes=["PV"])
        self.assertEqual(reuse(needs)["F"], "incomplete")
        self.assertEqual(unselected_variations(needs, "F"), {"PV"})

    def test_part_subsetting_a_variant_of_the_variation_is_selected(self):
        needs = self.variation(["PC"])
        needs["PV1"]["specializes"] = ["PV"]
        needs["PC"] = need("physical", specializes=["PV1"])
        self.assertEqual(reuse(needs)["F"], "full")
        self.assertEqual(unselected_variations(needs, "F"), set())

    def test_allocation_to_a_variant_reaches_its_parts(self):
        needs = self.variation(["PV1"])
        needs["PV1P"] = need("physical", platform=True, owned_by=["PV1"])
        self.assertEqual(reused_pcs(needs, "F"), {"PV1", "PV1P"})
        self.assertEqual(reuse(needs)["F"], "full")

    def test_platform_allocation_to_variants_selects_none_of_them(self):
        """The platform's own allocations offer every variant; only the project selects one."""
        needs = self.variation(["PV1", "PV2"])
        needs["LC"]["platform"] = True
        self.assertEqual(reuse(needs)["F"], "incomplete")
        self.assertEqual(unselected_variations(needs, "F"), {"PV"})
        needs["PC"] = need("physical", specializes=["PV1"])
        self.assertEqual(reuse(needs)["F"], "full")
        self.assertEqual(reused_pcs(needs, "F"), {"PV1"})
        self.assertEqual(unselected_variations(needs, "F"), set())

    def test_own_variants_are_all_offered(self):
        """In the platform's own build its variants are project needs: allocation reaches each."""
        needs = self.variation(["PV1", "PV2"])
        for v in ("PV", "PV1", "PV2"):
            needs[v]["platform"] = False
        self.assertEqual(reused_pcs(needs, "F"), {"PV1", "PV2"})

    def test_cycle_terminates(self):
        needs = {
            "A": need("feature", specializes=["B", "A"], owned_by=["B"]),
            "B": need("feature", specializes=["A"], owned_by=["A"]),
        }
        self.assertEqual(reuse(needs), {"A": "incomplete", "B": "incomplete"})

    def test_constraint_reuse_follows_its_owner_part(self):
        needs = {
            "CON-1": need("constraint", owned_by=["PC"]),
            "PC": need("physical", specializes=["PV"]),
            "PV": need("physical", platform=True),
        }
        self.assertEqual(constraint_reuse(needs, "CON-1"), "full")
        needs["PV"]["variant"] = True
        self.assertEqual(constraint_reuse(needs, "CON-1"), "full")
        needs["PC"]["specializes"] = []
        self.assertEqual(constraint_reuse(needs, "CON-1"), "new")
        needs["CON-1"]["owned_by"] = []
        self.assertEqual(constraint_reuse(needs, "CON-1"), "incomplete")

    def test_an_assembly_is_as_reused_as_its_parts(self):
        needs = {
            "CON-1": need("constraint", owned_by=["SET"]),
            "SET": need("physical", domain=""),
            "POS": need("physical", domain="", owned_by=["SET"], specializes=["PA"]),
            "PA": need("physical", platform=True, domain=""),
            "PC": need("physical", domain="EE", owned_by=["POS"], specializes=["PV"]),
            "PV": need("physical", platform=True, variant=True, domain="EE"),
        }
        self.assertEqual(constraint_reuse(needs, "CON-1"), "full")
        needs["NEW"] = need("physical", domain="ME", owned_by=["POS"])
        self.assertEqual(constraint_reuse(needs, "CON-1"), "partial")
        del needs["POS"], needs["PC"], needs["NEW"]
        self.assertEqual(constraint_reuse(needs, "CON-1"), "new")

    def test_a_domain_part_is_judged_by_itself_not_its_parts(self):
        needs = {
            "CON-1": need("constraint", owned_by=["BOARD"]),
            "BOARD": need("physical", domain="EE"),
            "PC": need("physical", domain="EE", owned_by=["BOARD"], specializes=["PV"]),
            "PV": need("physical", platform=True, domain="EE"),
        }
        self.assertEqual(constraint_reuse(needs, "CON-1"), "new")


class DegreeTest(unittest.TestCase):
    def test_modified_part_is_partial(self):
        needs = {
            **chain(["PC"]),
            "PC": need("physical", modified=True, specializes=["PP"]),
            "PP": need("physical", platform=True),
        }
        self.assertEqual(part_reuse(needs, "PC"), "partial")
        self.assertEqual(reuse(needs)["F"], "partial")

    def test_component_degree_from_its_parts(self):
        needs = {
            **chain(["PP", "PN"]),
            "PP": need("physical", platform=True),
            "PN": need("physical"),
        }
        self.assertEqual(component_reuse(needs, "LC"), "partial")
        needs["LC"]["allocated_to"] = ["PN"]
        self.assertEqual(component_reuse(needs, "LC"), "new")
        needs["LC"]["allocated_to"] = []
        self.assertEqual(component_reuse(needs, "LC"), "incomplete")

    def test_composite_combines_its_leaves(self):
        needs = {
            "TOP": need("component", leaf=False),
            "A": need("component", owned_by=["TOP"], allocated_to=["PP"]),
            "B": need("component", owned_by=["TOP"]),
            "PP": need("physical", platform=True),
            "PN": need("physical"),
        }
        self.assertEqual(component_reuse(needs, "TOP"), "incomplete")
        needs["B"]["allocated_to"] = ["PN"]
        self.assertEqual(component_reuse(needs, "TOP"), "partial")

    def test_feature_combines_its_components(self):
        needs = {
            **chain(["PP"]),
            "FN2": need("function", owned_by=["F"], allocated_to=["LC2"]),
            "LC2": need("component", allocated_to=["PP", "PN"]),
            "PP": need("physical", platform=True),
            "PN": need("physical"),
        }
        self.assertEqual(reuse(needs)["LC"], "full")
        self.assertEqual(reuse(needs)["F"], "partial")

    def test_reuse_covers_components(self):
        needs = {**chain(["PC"]), "PC": need("physical", platform=True)}
        self.assertEqual(reuse(needs), {"F": "full", "LC": "full"})

    def test_part_via_inherited_ref_part_is_full(self):
        """`oemCaps :>> keyCaps :> Platform::keyCaps`: the redefined ref part is no need, the subset is."""
        needs = {
            **chain(["PC"]),
            "PC": need("physical", specializes=["PP"]),
            "PP": need("physical", platform=True),
        }
        self.assertEqual(part_reuse(needs, "PC"), "full")

    def test_platform_build_is_new(self):
        needs = {**chain(["PC"]), "PC": need("physical")}
        self.assertEqual(reuse(needs), {"F": "new", "LC": "new"})


if __name__ == "__main__":
    unittest.main()


class InheritedPartsTest(unittest.TestCase):
    def test_part_subsetting_a_partial_project_assembly_is_partial(self):
        """driverDoorSwitch :> oemWindowSwitch inherits the modified caps oemWindowSwitch owns."""
        needs = {
            "PA": need("physical", platform=True, domain=""),
            "OEM": need("physical", domain="", specializes=["PA"]),
            "CAPS": need("physical", domain="ME", owned_by=["OEM"], modified=True, specializes=["PP"]),
            "PP": need("physical", platform=True, domain="ME"),
            "DOOR": need("physical", domain="", specializes=["OEM"]),
        }
        self.assertEqual(part_reuse(needs, "OEM"), "partial")
        self.assertEqual(part_reuse(needs, "DOOR"), "partial")

    def test_specialization_cycle_terminates(self):
        needs = {
            "A": need("physical", domain="", specializes=["B"]),
            "B": need("physical", domain="", specializes=["A"]),
        }
        self.assertEqual(part_reuse(needs, "A"), "new")
