"""C69: release decomposition must not imply merge or operational approval."""
import copy
import json
import unittest
from pathlib import Path

from benchmarks.cycle69_release_plan import audit

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "benchmarks" / "cycle69-isolated-integration-plan.v1.json"
INVENTORY = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"


def fixture():
    return (json.loads(PLAN.read_text(encoding="utf-8")),
            json.loads(INVENTORY.read_text(encoding="utf-8")))


class DecompositionTests(unittest.TestCase):
    def test_two_independent_pilots_and_seven_deferred_units(self):
        plan, inventory = fixture()
        result = audit(ROOT, plan, inventory)
        self.assertEqual(result["planStatus"], "pass", result["structuralErrors"])
        self.assertEqual(result["standalonePilots"], [58, 60])
        self.assertEqual(result["plannedDependentUnits"], [59, 61, 62, 63, 64, 65, 66])
        self.assertEqual(result["unitsAudited"], 9)
        self.assertEqual(result["decision"], "NO GO")
        self.assertFalse(result["approvalToMergeGranted"])

    def test_independent_pilots_are_based_on_main_and_only_four_files(self):
        plan, inventory = fixture()
        for u in plan["units"][:2]:
            with self.subTest(cycle=u["cycle"]):
                self.assertEqual(u["dependencies"], [])
                self.assertEqual(u["pilot"]["base"], "main")
                self.assertEqual(len(u["pilot"]["expectedFiles"]), 4)
                self.assertFalse(u["pilot"]["merged"])

    def test_topological_order_rejects_unmet_dependency(self):
        plan, inventory = fixture()
        plan["integrationOrder"] = [59, 58, 60, 61, 62, 63, 64, 65, 66]
        units_by_cycle = {u["cycle"]: u for u in plan["units"]}
        plan["units"] = [units_by_cycle[c] for c in plan["integrationOrder"]]
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")
        self.assertTrue(any("violates prerequisites" in s for s in out["structuralErrors"]))

    def test_bad_pilot_base_is_not_accepted(self):
        plan, inventory = fixture()
        plan["units"][0]["pilot"]["base"] = "research/cycle57-browser-replay-qa-and-static-fixes"
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")
        self.assertTrue(any("not a root-only" in s for s in out["structuralErrors"]))

    def test_merged_pilot_is_rejected(self):
        plan, inventory = fixture()
        plan["units"][0]["pilot"]["merged"] = True
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")

    def test_missing_pilot_file_rejected(self):
        plan, inventory = fixture()
        plan["units"][0]["pilot"]["expectedFiles"].pop()
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")

    def test_wrong_sha_rejected(self):
        plan, inventory = fixture()
        plan["units"][1]["pilot"]["sha"] = "improper"
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")

    def test_wrong_source_path_rejected(self):
        plan, inventory = fixture()
        plan["units"][0]["code"] = "benchmarks/missing_synthetic_gate.py"
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")

    def test_missing_dependency_rejected(self):
        plan, inventory = fixture()
        plan["units"][4]["dependencies"] = [61]
        out = audit(ROOT, plan, inventory)
        self.assertEqual(out["planStatus"], "fail")
        self.assertTrue(any("dependencies differ" in s for s in out["structuralErrors"]))

    def test_removed_group_member_rejected(self):
        plan, inventory = fixture()
        plan["groups"][2]["cycles"].pop()
        with self.assertRaises(ValueError):
            audit(ROOT, plan, inventory)

    def test_false_merge_authority_denied(self):
        plan, inventory = fixture()
        plan["authority"]["readyForMerge"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, plan, inventory)

    def test_false_technical_review_denied(self):
        plan, inventory = fixture()
        plan["requiredReview"]["independentEngineeringReviewCompleted"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, plan, inventory)

    def test_fake_live_snapshot_denied(self):
        plan, inventory = fixture()
        plan["snapshotNature"] = "certified_live_github_state"
        with self.assertRaises(ValueError):
            audit(ROOT, plan, inventory)

    def test_tooling_cannot_be_silently_integrated(self):
        plan, inventory = fixture()
        plan["deferredResearchTooling"]["state"] = "merged_into_main"
        with self.assertRaises(ValueError):
            audit(ROOT, plan, inventory)

    def test_untouched_inputs_and_no_go_flags(self):
        plan, inventory = fixture()
        old_p, old_i = copy.deepcopy(plan), copy.deepcopy(inventory)
        result = audit(ROOT, plan, inventory)
        self.assertEqual(plan, old_p)
        self.assertEqual(inventory, old_i)
        self.assertFalse(result["oemEffectivityVerified"])
        self.assertFalse(result["pilotCiAuthenticatedByThisTool"])
        self.assertFalse(result["operationalAuthorityGranted"])


if __name__ == "__main__":
    unittest.main()
