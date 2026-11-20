import unittest

from sysml2kit.reuse import reuse, reused_pcs


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

    def test_cycle_terminates(self):
        needs = {
            "A": need("feature", specializes=["B", "A"], owned_by=["B"]),
            "B": need("feature", specializes=["A"], owned_by=["A"]),
        }
        self.assertEqual(reuse(needs), {"A": "incomplete", "B": "incomplete"})


if __name__ == "__main__":
    unittest.main()
