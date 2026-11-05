"""Cycle 48 offline integration governance, no real-world validation."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from governance import cycle48_readiness as c48
from pilot.change_review_packets import ReviewRejected


class Cycle48ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = c48.load_manifest()
        cls.report = c48.build_report(cls.snapshot)

    def test_stack_matches_five_real_pinned_predecessors(self):
        r = self.report
        self.assertEqual(r["pendingStackCount"], 5)
        self.assertEqual([x["number"] for x in r["pendingIntegration"]],
                         [69, 70, 71, 72, 73])
        self.assertEqual([x["cycle"] for x in r["pendingIntegration"]],
                         [43, 44, 45, 46, 47])
        self.assertEqual(r["mainBaselineSha"],
                         "604c9fa2f98393ca31bef5cf31c40a60566851e7")
        for item in r["pendingIntegration"]:
            self.assertEqual(len(item["documentSha256"]), 64)
            self.assertEqual(len(item["headSha"]), 40)
        self.assertFalse(r["snapshotIsLive"])
        self.assertFalse(r["prChainApproved"])

    def test_thirteen_mandatory_external_gates_are_not_forged(self):
        self.assertEqual(len(c48.GATES), 13)
        self.assertEqual(self.report["unverifiedExternalGateCount"], 13)
        self.assertEqual(
            [g["gateId"] for g in self.report["pendingEvidenceRequests"]],
            list(c48.GATES),
        )
        for gate in self.snapshot["gates"]:
            self.assertFalse(gate["artifactReceived"])
            self.assertFalse(gate["externallyVerified"])
        self.assertEqual(self.report["proposedMetricCount"], 5)
        self.assertEqual(self.report["metricsEstimatedFromRealCases"], 0)
        self.assertFalse(self.report["studyMayRecruitParticipants"])
        self.assertFalse(self.report["studyMayStart"])

    def test_all_operational_and_research_authorities_are_denied(self):
        self.assertEqual(
            self.report["status"],
            "no_go_review_pr_stack_and_obtain_independent_study_evidence")
        for key in ("independentStudyCompleted", "externallyVerified",
                    "prChainApproved", "studyMayRecruitParticipants",
                    "studyMayStart", "diagnosticAccuracyEstablished",
                    "mayExecuteTests", "mayCreateWorkOrder",
                    "mayWriteSAP", "mayModifyECM", "mayReleaseEquipment"):
            self.assertIs(self.report[key], False, key)

    def test_closing_pr_or_forging_green_ci_is_not_evidence(self):
        mutations = (
            (("stack", 0, "state"), "merged"),
            (("stack", 1, "base"), "main"),
            (("stack", 2, "mergedIntoMain"), True),
            (("stack", 3, "mayAutomaticallyMerge"), True),
            (("stack", 4, "independentCodeReviewApproved"), True),
            (("stack", 4, "headSha"), "a"*40),
            (("stack", 3, "regressionOnHead"), "unknown"),
            (("mainBaselineSha",), "a"*40),
            (("source",), "live_authoritative_github_api"),
        )
        for route, value in mutations:
            altered = copy.deepcopy(self.snapshot)
            node = altered
            for step in route[:-1]:
                node = node[step]
            node[route[-1]] = value
            with self.subTest(route=route), self.assertRaises(ReviewRejected):
                c48.validate_manifest(altered)

    def test_gate_status_and_preregistered_claims_cannot_be_promoted(self):
        for field, value in (
            ("state", "approved"),
            ("artifactReceived", True),
            ("externallyVerified", True),
        ):
            changed = copy.deepcopy(self.snapshot)
            changed["gates"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ReviewRejected):
                c48.validate_manifest(changed)
        for field in c48.STUDY_FIELDS - {"design"}:
            changed = copy.deepcopy(self.snapshot)
            changed["studyDesign"][field] = True
            with self.subTest(field=field), self.assertRaises(ReviewRejected):
                c48.validate_manifest(changed)
        for field in c48.DENIED:
            changed = copy.deepcopy(self.snapshot)
            changed["safety"][field] = True
            with self.subTest(field=field), self.assertRaises(ReviewRejected):
                c48.validate_manifest(changed)

    def test_metric_denominators_are_not_misrepresented_as_measured(self):
        changed = copy.deepcopy(self.snapshot)
        changed["metrics"][0]["estimatedFromRealCases"] = True
        with self.assertRaises(ReviewRejected):
            c48.validate_manifest(changed)
        changed = copy.deepcopy(self.snapshot)
        changed["metrics"][1]["denominator"] = ""
        with self.assertRaises(ReviewRejected):
            c48.validate_manifest(changed)
        changed = copy.deepcopy(self.snapshot)
        changed["metrics"][2]["registeredForDesignDiscussionOnly"] = False
        with self.assertRaises(ReviewRejected):
            c48.validate_manifest(changed)

    def test_missing_or_crossing_source_file_rejected(self):
        changed = copy.deepcopy(self.snapshot)
        changed["stack"][0]["documentPath"] = "../../etc/passwd"
        with self.assertRaises(ReviewRejected):
            c48.validate_manifest(changed)
        changed = copy.deepcopy(self.snapshot)
        changed["stack"][0]["documentPath"] = (
            "docs/CICLO_0000_NONEXISTENT.md"
        )
        with self.assertRaises(ReviewRejected):
            c48.validate_manifest(changed)

    def test_document_mutation_changes_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for record in self.snapshot["stack"]:
                src = c48.ROOT / record["documentPath"]
                dst = root / record["documentPath"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
            self.assertTrue(c48.verify_report(self.report, self.snapshot, root))
            original = root / self.snapshot["stack"][0]["documentPath"]
            original.write_bytes(original.read_bytes() + b"\nDIFFERENT DOCUMENT\n")
            with self.assertRaises(ReviewRejected):
                c48.verify_report(self.report, self.snapshot, root)

    def test_cli_output_is_reproducible_public_metadata_only(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "readiness.json"
            summary = Path(folder) / "readiness.md"
            report = c48.cli(["--output", str(output),
                              "--markdown", str(summary)])
            self.assertEqual(report, self.report)
            self.assertEqual(c48.load_manifest(output), report)
            self.assertTrue(c48.verify_report(report, self.snapshot))
            md = summary.read_text(encoding="utf-8")
            self.assertIn("NO GO", md)
            self.assertIn("#69", md)
            self.assertIn("Evidências externas ausentes", md)
            self.assertNotIn("login", str(self.report))

    def test_report_tampering_does_not_change_eligibility(self):
        changed = copy.deepcopy(self.report)
        changed["studyMayStart"] = True
        with self.assertRaises(ReviewRejected):
            c48.verify_report(changed, self.snapshot)
        changed = copy.deepcopy(self.report)
        changed["unverifiedExternalGateCount"] = 0
        with self.assertRaises(ReviewRejected):
            c48.verify_report(changed, self.snapshot)


if __name__ == "__main__":
    unittest.main()
