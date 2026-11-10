"""C67: independent structural inventory and evidence claims must remain separate."""
import copy
import json
import unittest
from pathlib import Path

from benchmarks.cycle67_architecture_audit import audit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"


def fixture():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class ConsolidationAuditTests(unittest.TestCase):
    def test_full_nine_cycle_inventory_with_synthetic_smokes(self):
        out = audit(ROOT, fixture())
        self.assertEqual(out["inventoryStatus"], "pass", out["inventoryErrors"])
        self.assertEqual(out["cyclesAudited"], 9)
        self.assertTrue(all(r["fixtureSmoke"] == "NO GO" for r in out["cycles"]))
        self.assertGreaterEqual(out["testMethodDefinitions"], 150)
        self.assertFalse(out["readyForMerge"])

    def test_historical_metadata_is_not_live(self):
        out = audit(ROOT, fixture(), run_smoke=False)
        self.assertTrue(out["snapshotNotLive"])
        self.assertFalse(out["realMechanicalValidationCompleted"])
        self.assertFalse(out["humanIndependentReviewCompleted"])
        self.assertEqual(out["decision"], "NO GO")

    def test_identify_dependency_path_filter_debt(self):
        out = audit(ROOT, fixture(), run_smoke=False)
        gaps = [f["cycle"] for f in out["advisoryFindings"]
                if f["code"] == "upstream_path_filter_gap"]
        self.assertEqual(gaps, list(range(61, 67)))

    def test_identify_main_divergence_as_merge_blocker(self):
        out = audit(ROOT, fixture(), run_smoke=False)
        items = [f for f in out["advisoryFindings"]
                 if f["code"] == "research_branch_diverged_from_main"]
        self.assertEqual(len(items), 1)
        self.assertGreater(items[0]["behindAtSnapshot"], 0)
        self.assertEqual(items[0]["severity"], "blocking_integration")

    def test_missing_document_fails_structure(self):
        data = fixture()
        data["inventory"][-1]["doc"] = "docs/missing_cycle66_evidence.md"
        out = audit(ROOT, data, run_smoke=False)
        self.assertEqual(out["inventoryStatus"], "fail")
        self.assertIn("doc", out["cycles"][-1]["missingArtifacts"])

    def test_missing_python_module_fails_structure(self):
        data = fixture()
        data["inventory"][0]["code"] = "benchmarks/ghost_cycle58.py"
        out = audit(ROOT, data, run_smoke=False)
        self.assertEqual(out["inventoryStatus"], "fail")
        self.assertIn("code", out["cycles"][0]["missingArtifacts"])

    def test_changed_dependency_must_be_reviewed(self):
        data = fixture()
        data["inventory"][-1]["upstream"] = 64
        out = audit(ROOT, data, run_smoke=False)
        self.assertEqual(out["inventoryStatus"], "fail")
        self.assertTrue(any("imports disagree" in e for e in out["inventoryErrors"]))

    def test_changed_pr_base_breaks_continuity(self):
        data = fixture()
        data["stack"][-1]["base"] = "research/unknown-parent"
        out = audit(ROOT, data, run_smoke=False)
        self.assertEqual(out["inventoryStatus"], "fail")
        self.assertTrue(any("chain discontinuity" in e for e in out["inventoryErrors"]))

    def test_falsely_merged_snapshot_fails(self):
        data = fixture()
        data["stack"][0]["draft"] = False
        data["stack"][0]["merged"] = True
        out = audit(ROOT, data, run_smoke=False)
        self.assertEqual(out["inventoryStatus"], "fail")
        self.assertTrue(any("invalid PR snapshot" in e for e in out["inventoryErrors"]))

    def test_reject_laundered_live_metadata(self):
        data = fixture()
        data["snapshotNature"] = "verified_now"
        with self.assertRaises(ValueError):
            audit(ROOT, data, run_smoke=False)

    def test_reject_missing_cycles(self):
        data = fixture()
        data["inventory"].pop()
        with self.assertRaises(ValueError):
            audit(ROOT, data, run_smoke=False)

    def test_reject_path_traversal(self):
        data = fixture()
        data["inventory"][0]["doc"] = "../../secrets.txt"
        with self.assertRaises(ValueError):
            audit(ROOT, data, run_smoke=False)

    def test_manifest_not_mutated(self):
        data = fixture()
        before = copy.deepcopy(data)
        audit(ROOT, data, run_smoke=False)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
