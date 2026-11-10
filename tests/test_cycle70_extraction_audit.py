"""C70: topology checks are not live PR, expert or operational approval."""
import copy
import json
import unittest
from pathlib import Path

from benchmarks.cycle70_extraction_audit import audit

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return (
        json.loads((ROOT / "benchmarks/cycle70-dependent-pilot-extractions.v1.json").read_text()),
        json.loads((ROOT / "benchmarks/cycle69-isolated-integration-plan.v1.json").read_text()),
        json.loads((ROOT / "benchmarks/cycle67-consolidation-inventory.v1.json").read_text()),
    )


class IsolatedDependentExtractionTests(unittest.TestCase):
    def test_two_valid_draft_dependent_prs(self):
        current, earlier, inventory = fixture()
        out = audit(ROOT, current, earlier, inventory)
        self.assertEqual(out["pilotCount"], 2)
        self.assertEqual([p["pr"] for p in out["pilots"]], [98, 99])
        self.assertEqual([p["basePr"] for p in out["pilots"]], [95, 96])
        self.assertEqual(out["decision"], "NO GO")
        self.assertFalse(out["readyForMerge"])

    def test_snapshot_is_not_live_authentication(self):
        current, earlier, inventory = fixture()
        out = audit(ROOT, current, earlier, inventory)
        self.assertTrue(out["snapshotNotLive"])
        self.assertFalse(out["realMechanicalValidationCompleted"])
        self.assertTrue(all(not p["isolatedWorkflowVerifiedLiveByThisAudit"]
                            for p in out["pilots"]))

    def test_wrong_base_branch_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][0]["base"] = "main"
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_wrong_parent_pr_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][1]["basePr"] = 95
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_wrong_dependency_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][0]["dependencies"] = [60]
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_wrong_expected_diff_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][1]["paths"].append("benchmarks/cycle58_causal_gate.py")
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_invalid_sha_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][1]["headSha"] = "NOT_A_SHA"
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_false_merged_state_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][0]["merged"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_false_authority_rejected(self):
        current, earlier, inventory = fixture()
        current["readyForMerge"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_fake_live_ci_status_rejected(self):
        current, earlier, inventory = fixture()
        current["pilots"][0]["specificCiAtSnapshot"] = "verified_forever"
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_remove_deferred_cycle_rejected(self):
        current, earlier, inventory = fixture()
        current["remainingCycles"].pop()
        with self.assertRaises(ValueError):
            audit(ROOT, current, earlier, inventory)

    def test_input_unmodified(self):
        current, earlier, inventory = fixture()
        before = copy.deepcopy((current, earlier, inventory))
        audit(ROOT, current, earlier, inventory)
        self.assertEqual((current, earlier, inventory), before)


if __name__ == "__main__":
    unittest.main()
