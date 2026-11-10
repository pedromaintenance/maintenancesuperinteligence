"""C71: prevent false branch topology and operational approval claims."""
import copy
import json
import unittest
from pathlib import Path

from benchmarks.cycle71_extraction_audit import audit

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return (
        json.loads((ROOT / "benchmarks/cycle71-reference-extraction.v1.json").read_text()),
        json.loads((ROOT / "benchmarks/cycle67-consolidation-inventory.v1.json").read_text()),
        json.loads((ROOT / "benchmarks/cycle70-dependent-pilot-extractions.v1.json").read_text()),
    )


class Extraction71Tests(unittest.TestCase):
    def test_valid_isolated_c62_reference_pr_never_go(self):
        current, inventory, earlier = fixture()
        result = audit(ROOT, current, inventory, earlier)
        self.assertEqual(result["pilotPr"], 101)
        self.assertEqual(result["directDependencies"], [60, 61])
        self.assertEqual(result["changedFiles"], 4)
        self.assertFalse(result["readyForMerge"])
        self.assertEqual(result["decision"], "NO GO")

    def test_no_live_github_assertion(self):
        c, i, p = fixture()
        result = audit(ROOT, c, i, p)
        self.assertFalse(result["liveCIAuthenticatedByThisAudit"])
        self.assertTrue(result["snapshotNotLive"])

    def test_wrong_parent_branch_rejected(self):
        c, i, p = fixture()
        c["extraction"]["base"] = "main"
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_missing_c60_dependency_rejected(self):
        c, i, p = fixture()
        c["extraction"]["dependencies"] = [61]
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_wrong_upstream_parent_pr_rejected(self):
        c, i, p = fixture()
        c["extraction"]["basePr"] = 96
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_false_merge_rejected(self):
        c, i, p = fixture()
        c["extraction"]["merged"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_false_human_approval_rejected(self):
        c, i, p = fixture()
        c["humanCodeReviewVerified"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_forged_operational_privilege_rejected(self):
        c, i, p = fixture()
        c["mayWriteSap"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_unexpected_artifact_in_diff_rejected(self):
        c, i, p = fixture()
        c["extraction"]["files"].append("docs/secret_oem.pdf")
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_workflow_test_scope_rejected_if_cross_chain(self):
        c, i, p = fixture()
        c["extraction"]["isolatedTests"].insert(0, "tests.test_cycle58_causal_gate")
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_malformed_sha_rejected(self):
        c, i, p = fixture()
        c["extraction"]["headSha"] = "not-a-sha"
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_prior_branch_lineage_tampering_rejected(self):
        c, i, p = fixture()
        p["pilots"][1]["basePr"] = 95
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_non_synthetic_source_rejected(self):
        c, i, p = fixture()
        c["extraction"]["sourceData"] = "real_caterpillar_machine"
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_future_cycle_cannot_disappear(self):
        c, i, p = fixture()
        c["remainingResearchCycles"].pop()
        with self.assertRaises(ValueError):
            audit(ROOT, c, i, p)

    def test_does_not_mutate_evidence_snapshots(self):
        c, i, p = fixture()
        old = copy.deepcopy((c, i, p))
        audit(ROOT, c, i, p)
        self.assertEqual((c, i, p), old)


if __name__ == "__main__":
    unittest.main()
