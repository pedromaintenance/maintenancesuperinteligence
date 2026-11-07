"""Cycle 43: structural maturity checks, not diagnostic accuracy tests."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmarks.cycle43_readiness as audit


class Cycle43ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = audit.load(audit.MANIFEST)
        cls.report = audit.evaluate_readiness(cls.manifest)

    def test_all_claims_and_open_issues_are_accounted_for(self):
        self.assertEqual({c["id"] for c in self.report["claimStates"]},
                         set(audit.CLAIM_STATUS))
        self.assertEqual({i["number"] for i in self.report["trackedOpenIssues"]},
                         {1, 4, 5, 50})
        self.assertFalse(self.report["issueStatesAreLive"])
        self.assertGreaterEqual(len(self.report["evidenceFileFingerprints"]), 10)
        for entry in self.report["evidenceFileFingerprints"]:
            self.assertEqual(len(entry["sha256"]), 64)

    def test_authorial_24_and_counterfactual_128_are_not_accuracy(self):
        r = self.report
        self.assertEqual(r["authoredQuestionAgreement"], {"matched": 24, "total": 24})
        self.assertEqual(r["counterfactualStructuralChecks"]["total"], 128)
        self.assertEqual(set(r["counterfactualStructuralChecks"]["perFamily"]),
                         set(audit.FAMILIES))
        self.assertTrue(all(n == 32 for n in
                            r["counterfactualStructuralChecks"]["perFamily"].values()))
        self.assertFalse(r["counterfactualStructuralChecks"]["independentOracleUsed"])
        self.assertFalse(r["mayClaimMechanicalDiagnosticCompetence"])
        self.assertFalse(r["mayConcludeExternalTechnicalApproval"])
        self.assertEqual(r["decision"],
                         "no_go_independent_validation_not_performed")

    def test_no_promoted_real_world_proof_or_operational_permission(self):
        self.assertFalse(self.report["externalReviewArtifactsReceived"])
        self.assertEqual(set(self.report["safety"]), set(audit.SAFETY_FLAGS))
        self.assertTrue(all(v is False for v in self.report["safety"].values()))
        for field in audit.SAFETY_FLAGS:
            tampered = copy.deepcopy(self.manifest)
            tampered["safety"][field] = True
            with self.subTest(field=field), self.assertRaises(audit.ReadinessRejected):
                audit.validate_manifest(tampered)

    def test_declared_claims_cannot_be_upgraded_by_fiat(self):
        for path, value in [
            (("claims", 0, "state"), "expert_validated"),
            (("claims", 1, "externallyValidated"), True),
            (("claims", 0, "evidencePaths"), []),
            (("claims", 2, "limitation"), ""),
            (("externalReviewArtifactsReceived",), True),
            (("baseline", "mainCommit"), "untracked"),
            (("baseline", "snapshotDate"), "2026-11-04"),
        ]:
            altered = copy.deepcopy(self.manifest)
            cur = altered
            for key in path[:-1]:
                cur = cur[key]
            cur[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(audit.ReadinessRejected):
                audit.validate_manifest(altered)

    def test_no_auto_close_or_hidden_backlog_issue(self):
        for path, value in [
            (("openIssueSnapshot", 0, "mayAutoClose"), True),
            (("openIssueSnapshot", 1, "state"), "complete"),
            (("openIssueSnapshot", 2, "remainingWork"), ""),
            (("openIssueSnapshot", 3, "number"), 5),
        ]:
            altered = copy.deepcopy(self.manifest)
            cur = altered
            for key in path[:-1]:
                cur = cur[key]
            cur[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(audit.ReadinessRejected):
                audit.validate_manifest(altered)

    def test_missing_or_escape_evidence_is_not_accepted(self):
        for bad_path in ("../other.json", "/etc/passwd",
                         "docs/not-a-real-cycle43-evidence-file.json"):
            altered = copy.deepcopy(self.manifest)
            altered["claims"][0]["evidencePaths"][0] = bad_path
            with self.subTest(path=bad_path), self.assertRaises(audit.ReadinessRejected):
                audit.validate_manifest(altered)

    def test_counterfactual_catches_unsafe_selector_output(self):
        original = audit.investigate

        def compromised(case):
            result = original(case)
            result["confirmedRootCause"] = "invented_hydraulic_failure"
            return result

        cases = audit.load(audit.CASES_PATH)["cases"]
        with patch.object(audit, "investigate", side_effect=compromised):
            with self.assertRaises(audit.ReadinessRejected):
                audit.exercise_counterfactuals(cases)

    def test_report_reconstruction_detects_promotion(self):
        self.assertTrue(audit.verify_report(self.report, self.manifest))
        tampered = copy.deepcopy(self.report)
        tampered["mayClaimMechanicalDiagnosticCompetence"] = True
        with self.assertRaises(audit.ReadinessRejected):
            audit.verify_report(tampered, self.manifest)
        tampered = copy.deepcopy(self.report)
        tampered["counterfactualStructuralChecks"]["total"] = 129
        with self.assertRaises(audit.ReadinessRejected):
            audit.verify_report(tampered, self.manifest)

    def test_offline_cli_and_markdown_do_not_claim_external_review(self):
        md = audit.render_markdown(self.report)
        self.assertIn("NO GO", md)
        self.assertIn("não realizada", md)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "readiness.json"
            note = Path(tmp) / "readiness.md"
            report = audit.main(["--output", str(out), "--markdown", str(note)])
            self.assertEqual(report, self.report)
            self.assertTrue(out.is_file())
            self.assertTrue(note.is_file())
            self.assertTrue(audit.verify_report(audit.load(out), self.manifest))


if __name__ == "__main__":
    unittest.main()
