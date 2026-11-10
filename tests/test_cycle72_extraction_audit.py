"""Cycle 72: ancestry and synthetic contract protection for isolated C63."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.cycle72_extraction_audit import audit

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return (
        json.loads((ROOT / "benchmarks/cycle72-effectivity-extraction.v1.json").read_text()),
        json.loads((ROOT / "benchmarks/cycle71-reference-extraction.v1.json").read_text()),
        json.loads((ROOT / "benchmarks/cycle67-consolidation-inventory.v1.json").read_text()),
    )


class Cycle72Tests(unittest.TestCase):
    def test_valid_c63_ancestry_is_not_real_authority(self):
        a, b, c = fixture()
        r = audit(ROOT, a, b, c)
        self.assertEqual(r["pilotPr"], 103)
        self.assertEqual(r["directDependencies"], [62])
        self.assertEqual(r["transitiveDependencies"], [60, 61])
        self.assertEqual(r["ownFiles"], 4)
        self.assertEqual(r["isolatedTests"], 4)
        self.assertEqual(r["decision"], "NO GO")
        self.assertTrue(r["historicalResearchWorkflowVerified"])
        self.assertFalse(r["isolatedPilotWorkflowVerifiedByThisAudit"])
        self.assertFalse(r["readyForMerge"])

    def test_snapshot_is_not_live_confirmation(self):
        a, b, c = fixture()
        r = audit(ROOT, a, b, c)
        self.assertTrue(r["snapshotNotLive"])
        self.assertFalse(r["liveCIAuthenticatedByThisAudit"])

    def test_wrong_parent_branch_denied(self):
        a, b, c = fixture()
        a["extraction"]["base"] = "main"
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_wrong_parent_pr_denied(self):
        a, b, c = fixture()
        a["extraction"]["basePr"] = 96
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_missing_c62_direct_dependency_denied(self):
        a, b, c = fixture()
        a["extraction"]["directDependencies"] = [61]
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_missing_transitive_dependency_denied(self):
        a, b, c = fixture()
        a["extraction"]["transitiveDependencies"] = [61]
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_upstream_c62_lineage_tampering_denied(self):
        a, b, c = fixture()
        b["extraction"]["pr"] = 99
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_fake_merge_denied(self):
        a, b, c = fixture()
        a["extraction"]["merged"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_forged_human_review_denied(self):
        a, b, c = fixture()
        a["humanReviewCompleted"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_forged_oem_effectivity_denied(self):
        a, b, c = fixture()
        a["extraction"]["realOemEffectivityVerified"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_forged_sap_access_denied(self):
        a, b, c = fixture()
        a["mayWriteSap"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_extra_file_denied(self):
        a, b, c = fixture()
        a["extraction"]["files"].append("proprietary_oem.pdf")
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_cross_branch_test_command_denied(self):
        a, b, c = fixture()
        a["extraction"]["isolatedTests"].append("tests.test_cycle58_causal_gate")
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_fake_live_status_denied(self):
        a, b, c = fixture()
        a["snapshotNature"] = "verified_live"
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_unsupported_real_data_denied(self):
        a, b, c = fixture()
        a["extraction"]["dataScope"] = "field_case"
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_unknown_head_sha_denied(self):
        a, b, c = fixture()
        a["extraction"]["headSha"] = "INVALID"
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_upstream_inventory_dependency_drift_denied(self):
        a, b, c = fixture()
        c["inventory"][5]["dependencies"] = [61]
        with self.assertRaises(ValueError):
            audit(ROOT, a, b, c)

    def test_no_snapshot_mutation(self):
        a, b, c = fixture()
        original = copy.deepcopy((a, b, c))
        audit(ROOT, a, b, c)
        self.assertEqual((a, b, c), original)


if __name__ == "__main__":
    unittest.main()
