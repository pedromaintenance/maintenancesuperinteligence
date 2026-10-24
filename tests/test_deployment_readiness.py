"""Contractual readiness is NOT evidence of production security or approval."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from governance.deployment_readiness import (
    ROOT, CYCLES, CHANGES, STATES, check_compatibility,
    evaluate_readiness, main, plan_controls, validate_readiness,
)


class DeploymentReadinessTests(unittest.TestCase):
    def setUp(self):
        self.packet = json.loads(
            (ROOT / "governance/deployment-readiness.v1.json").read_text())
        self.policy = json.loads(
            (ROOT / "governance/integration-policy.v1.json").read_text())

    def result(self):
        return evaluate_readiness(self.packet, self.policy)

    def reject(self, message=None):
        with self.assertRaises(ImportRejected) as ctx:
            self.result()
        if message:
            self.assertIn(message, str(ctx.exception))

    def control(self, control_id):
        return next(c for c in self.packet["controls"] if c["controlId"] == control_id)

    def test_ten_controls_and_real_status_counts(self):
        r = self.result()
        self.assertEqual(r["controlsTotal"], 10)
        self.assertEqual(r["controlStatusCounts"], {
            "not_implemented": 4, "planned": 3, "available_unverified": 3,
            "independently_verified": 0, "revoked": 0})
        self.assertEqual(r["independentlyVerifiedControls"], 0)
        self.assertEqual(r["publicSyntheticPlaceholders"], 10)
        self.assertFalse(r["allControlsSatisfied"])

    def test_topological_plan_respects_each_prerequisite(self):
        result = self.result()
        order = [x["controlId"] for x in result["implementationOrder"]]
        self.assertEqual(len(order), 10)
        index = {name: i for i, name in enumerate(order)}
        for item in result["implementationOrder"]:
            with self.subTest(item=item["controlId"]):
                self.assertTrue(all(index[dependency] < index[item["controlId"]]
                                    for dependency in item["blockedBy"]))
                self.assertFalse(item["acceptanceVerified"])
                self.assertFalse(item["publicEvidenceValidForApproval"])

    def test_repeated_run_is_identical_and_source_lineage_remains_public(self):
        a, b = self.result(), self.result()
        self.assertEqual(a, b)
        self.assertEqual(len(a["compatibility"]), 4)
        self.assertEqual({x["path"] for x in a["compatibility"]},
                         {x[0] for x in CYCLES.values()})
        self.assertTrue(all(len(x["contentSha256"]) == 64
                            and x["sourceVerifiedAsPublicFile"]
                            and not x["privateMigrationAuthorised"]
                            for x in a["compatibility"]))
        self.assertFalse(a["privateCompatibilityApproved"])

    def test_all_operational_actions_forbidden(self):
        r = self.result()
        self.assertEqual(r["acceptance"], "blocked_private_deployment")
        self.assertFalse(r["mayConnectCorporateSystems"])
        self.assertFalse(r["mayImportRealEvidence"])
        self.assertFalse(r["mayApproveOemEffectivity"])
        self.assertFalse(r["mayCreateWorkOrder"])
        self.assertFalse(r["mayReleaseEquipment"])
        self.assertFalse(r["engineeringApproved"])
        self.assertFalse(r["informationSecurityApproved"])
        self.assertFalse(r["privacyLegalApproved"])

    def test_every_impact_reopens_reviews_with_no_automatic_approval(self):
        r = self.result()
        self.assertEqual({x["trigger"] for x in r["changeRequalification"]}, CHANGES)
        for change in r["changeRequalification"]:
            self.assertEqual(change["decision"], "reopen_for_independent_review")
            self.assertFalse(change["automaticReapproval"])
            self.assertTrue(change["invalidates"])

    def test_independently_verified_is_forbidden_in_public_fixture(self):
        self.packet["controls"][0]["status"] = "independently_verified"
        self.reject("unverified status")

    def test_revoked_is_not_public_evidence_status(self):
        self.packet["controls"][0]["status"] = "revoked"
        self.reject("unverified status")

    def test_synthetic_available_status_not_approved(self):
        r = self.result()
        available = [x for x in r["implementationOrder"]
                     if x["status"] == "available_unverified"]
        self.assertEqual(len(available), 3)
        self.assertTrue(all(x["statusForPrivateRelease"]
                            == "blocked_missing_independent_verification"
                            for x in available))

    def test_mutation_to_claim_private_verified_source_rejected(self):
        self.packet["controls"][0]["publicEvidenceAuthoritative"] = True
        self.reject("unverified status")

    def test_mutation_to_real_reviewer_approval_rejected(self):
        self.packet["controls"][0]["reviewerApprovalReal"] = True
        self.reject("unverified status")

    def test_mutation_to_false_private_source_required_rejected(self):
        self.packet["controls"][0]["privateSourceRequired"] = False
        self.reject("unverified status")

    def test_mutation_to_fake_source_digest_rejected(self):
        self.packet["evidences"][0]["sourceDigest"] = "a" * 64
        self.reject("cannot contain or verify private evidence")

    def test_mutation_to_fake_authenticated_provenance_rejected(self):
        self.packet["evidences"][0]["provenanceAuthenticated"] = True
        self.reject("cannot contain or verify private evidence")

    def test_mutation_to_real_data_in_public_fixture_rejected(self):
        self.packet["evidences"][0]["containsPrivateData"] = True
        self.reject("cannot contain or verify private evidence")

    def test_mutation_to_licensed_content_rejected(self):
        self.packet["evidences"][0]["containsLicensedMaterial"] = True
        self.reject("cannot contain or verify private evidence")

    def test_duplicate_control_id_rejected(self):
        self.packet["controls"][1]["controlId"] = self.packet["controls"][0]["controlId"]
        self.reject("unknown or duplicate proof")

    def test_control_removed_is_rejected(self):
        self.packet["controls"].pop()
        self.reject("exactly ten")

    def test_missing_evidence_rejected(self):
        self.packet["evidences"].pop()
        self.reject("one placeholder")

    def test_duplicate_evidence_rejected(self):
        self.packet["evidences"][1]["controlId"] = self.packet["evidences"][0]["controlId"]
        self.reject("orphan, duplicate")

    def test_foreign_evidence_id_rejected(self):
        self.packet["evidences"][1]["evidenceId"] = "SIM-EVIDENCE-99"
        self.reject("orphan, duplicate")

    def test_untrusted_non_simulation_reference_rejected(self):
        self.packet["evidences"][0]["reference"] = "CORPORATE-SAP-LINK"
        self.reject("cannot contain or verify private evidence")

    def test_extra_approval_field_rejected(self):
        self.packet["acceptanceDecision"]["signedByEngineer"] = "someone"
        self.reject("missing or unauthorized fields")

    def test_fake_acceptance_granted_rejected(self):
        self.packet["acceptanceDecision"]["mayDeploy"] = True
        self.reject("public record cannot grant")

    def test_fake_security_signoff_rejected(self):
        self.packet["acceptanceDecision"]["securityApproved"] = True
        self.reject("public record cannot grant")

    def test_fake_oem_signoff_rejected(self):
        self.packet["acceptanceDecision"]["oemApprovalVerified"] = True
        self.reject("public record cannot grant")

    def test_external_tenant_rejected(self):
        self.packet["tenant"] = "actual-company"
        self.reject("no corporate tenant")

    def test_missing_change_impact_rejected(self):
        self.packet["changeImpacts"].pop()
        self.reject("revalidation triggers missing")

    def test_duplicate_change_impact_rejected(self):
        self.packet["changeImpacts"][1]["eventType"] = self.packet["changeImpacts"][0]["eventType"]
        self.reject("duplicate/unknown invalidation")

    def test_remove_requalification_dependency_rejected(self):
        self.packet["changeImpacts"][0]["invalidates"].pop()
        self.reject("stale approvals")

    def test_invented_automatic_reapproval_rejected(self):
        self.packet["changeImpacts"][0]["allowAutomaticReapproval"] = True
        self.reject("stale approvals")

    def test_invalidated_prior_approval_cannot_survive(self):
        self.packet["changeImpacts"][0]["previousApprovalValid"] = True
        self.reject("stale approvals")

    def test_missing_one_cycle_source_rejected(self):
        self.packet["compatibilityMatrix"]["entries"].pop()
        self.reject("unsupported source set")

    def test_fake_source_version_upgrade_is_rejected(self):
        self.packet["compatibilityMatrix"]["entries"][0]["requiredVersion"] = "9.9.9"
        self.reject("forged version")

    def test_public_compatibility_cannot_approve_private_migration(self):
        self.packet["compatibilityMatrix"]["authorisedPrivateMigration"] = True
        self.reject("claimed private migration")

    def test_unknown_compatibility_file_rejected(self):
        self.packet["compatibilityMatrix"]["entries"][0]["path"] = "../private/auth.json"
        self.reject("unsupported path")

    def test_compatibility_schema_drift_rejected(self):
        self.packet["compatibilityMatrix"]["entries"][0]["requiredSchema"] = "new-schema"
        self.reject("schema drift")

    def test_duplicate_source_rejected(self):
        self.packet["compatibilityMatrix"]["entries"][1] = copy.deepcopy(
            self.packet["compatibilityMatrix"]["entries"][0])
        self.reject("duplicate source")

    def test_dependency_cycle_rejected(self):
        a, b = self.packet["controls"][0], self.packet["controls"][1]
        a["dependsOn"] = [b["controlId"]]
        graph = {c["controlId"]: c for c in self.packet["controls"]}
        with self.assertRaisesRegex(ImportRejected, "dependency cycle"):
            plan_controls(graph)
        self.reject("baseline dependency drift")

    def test_orphan_dependency_rejected(self):
        self.packet["controls"][0]["dependsOn"] = ["not-a-control"]
        graph = {c["controlId"]: c for c in self.packet["controls"]}
        with self.assertRaisesRegex(ImportRejected, "foreign prerequisite"):
            plan_controls(graph)
        self.reject("baseline dependency drift")

    def test_self_dependency_rejected(self):
        c = self.packet["controls"][0]
        c["dependsOn"] = [c["controlId"]]
        graph = {c["controlId"]: c for c in self.packet["controls"]}
        with self.assertRaisesRegex(ImportRejected, "self-edge"):
            plan_controls(graph)
        self.reject("baseline dependency drift")

    def test_source_cycle_misattribution_rejected(self):
        self.packet["compatibilityMatrix"]["entries"][0]["cycle"] = "cycle10"
        self.reject("source cycle misattributed")

    def test_remove_necessary_dependency_requires_design_review(self):
        control = self.control("two_independent_reviewers")
        control["dependsOn"].remove("no_conflict_record")
        self.reject("baseline dependency drift")

    def test_invalid_status_type_rejected(self):
        self.packet["controls"][0]["status"] = True
        self.reject("unverified status")

    def test_ci_local_cli_rejects_untrusted_fixture(self):
        self.packet["controls"][0]["status"] = "independently_verified"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.json"
            path.write_text(json.dumps(self.packet), encoding="utf-8")
            with patch("sys.stderr"):
                code = main(["--fixture", str(path)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
