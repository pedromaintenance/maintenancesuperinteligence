"""Ciclo 12: adversarial readiness dossier, no simulated approval or corporate data."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from governance.integration_contracts import ROOT
from governance.readiness_dossier import (
    build_dossier, check_dossier, render_html, main, IMPACT_MAP,
)


class ReadinessDossierTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(
            (ROOT / "governance/readiness-dossier-fixture.v1.json").read_text())
        self.source = json.loads(
            (ROOT / "governance/deployment-readiness.v1.json").read_text())
        self.policy = json.loads(
            (ROOT / "governance/integration-policy.v1.json").read_text())

    def validate(self):
        return check_dossier(self.fixture, self.source, self.policy)

    def result(self):
        return build_dossier(self.fixture, self.source, self.policy)

    def reject(self, message=None):
        with self.assertRaises(ImportRejected) as ctx:
            self.validate()
        if message:
            self.assertIn(message, str(ctx.exception))

    def test_ten_findings_and_open_evidence_requests(self):
        r = self.result()
        self.assertEqual(r["findingCount"], 10)
        self.assertEqual(len(r["findings"]), 10)
        self.assertEqual(r["criticalFindings"], 8)
        self.assertEqual(r["highFindings"], 2)
        self.assertEqual(len(r["evidenceRequests"]), 10)
        self.assertEqual(len(r["ownerActions"]), 10)
        self.assertTrue(all(not x["evidenceReceived"]
                            and x["decision"] == "blocked_pending_private_evidence"
                            for x in r["findings"]))
        self.assertTrue(all(x["status"] == "not_received"
                            for x in r["evidenceRequests"]))

    def test_six_scenarios_including_conflict_of_interest(self):
        result = self.result()
        self.assertEqual(len(result["changeScenarios"]), 6)
        self.assertEqual({x["eventType"] for x in result["changeScenarios"]},
                         set(IMPACT_MAP))
        conflict = next(x for x in result["changeScenarios"]
                        if x["eventType"] == "conflict_of_interest_discovered")
        self.assertIn("no_conflict_record", conflict["invalidates"])
        self.assertIn("two_independent_reviewers", conflict["invalidates"])
        self.assertFalse(conflict["automaticReapproval"])

    def test_two_exceptions_never_waive_controls(self):
        result = self.result()
        self.assertEqual(len(result["exceptions"]), 2)
        self.assertTrue(all(not x["waiveControl"] and not x["mayDeploy"]
                            and not x["approvedByRealPerson"]
                            and x["decision"] == "blocked_no_verified_evidence"
                            for x in result["exceptions"]))

    def test_readiness_never_becomes_approval(self):
        r = self.result()
        self.assertEqual(r["decision"], "blocked_missing_private_verified_trust")
        for key in ("humanReviewAuthenticated", "privateEvidenceStoredHere",
                    "evidenceFullyVerified", "oemEffectivityVerified",
                    "deploymentApproved", "mayImportCorporateData",
                    "mayCreateWorkOrder", "mayReleaseEquipment"):
            with self.subTest(key=key):
                self.assertIs(r[key], False)

    def test_public_compatibility_includes_cycles_eight_to_eleven(self):
        r = self.result()
        self.assertEqual(len(r["compatibility"]), 5)
        self.assertEqual({x["cycle"] for x in r["compatibility"]},
                         {"cycle08", "cycle09", "cycle10", "cycle11"})
        self.assertTrue(all(x["privateMigrationAuthorised"] is False
                            for x in r["compatibility"]))

    def test_deterministic_dossier_and_static_html(self):
        first = self.result()
        self.assertEqual(first, self.result())
        html = render_html(first)
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("Content-Security-Policy", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<form", html)
        self.assertIn("SIMULADO", html)
        self.assertIn("IMPLANTAÇÃO BLOQUEADA", html)
        self.assertEqual(html.count("<tr>"), 11)
        self.assertEqual(html, render_html(self.result()))

    def test_html_escapes_attacker_supplied_reason(self):
        rationale = "<script>alert('compromised')</script> justificativa não autorizada"
        self.fixture["exceptionRequests"][0]["rationale"] = rationale
        html = render_html(self.result())
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("alert('compromised')</script>", html)

    def test_dossier_status_cannot_be_forged(self):
        self.fixture["independentReviewGate"]["status"] = "approved"
        self.reject("no real signatures")

    def test_forged_real_reviewer_rejected(self):
        self.fixture["independentReviewGate"]["twoIndependentRealReviewers"] = True
        self.reject("no real signatures")

    def test_forged_engineering_approval_rejected(self):
        self.fixture["independentReviewGate"]["approvalGranted"] = True
        self.reject("no real signatures")

    def test_forged_effectivity_rejected(self):
        self.fixture["independentReviewGate"]["sourceOemEffectivityVerified"] = True
        self.reject("no real signatures")

    def test_dossier_disallows_private_source_location(self):
        self.fixture["evidenceRequests"][0]["privateEvidenceLocation"] = "https://intranet.example"
        self.reject("missing provenance or false approval")

    def test_dossier_disallows_authentication(self):
        self.fixture["evidenceRequests"][0]["authenticatedEvidence"] = True
        self.reject("missing provenance or false approval")

    def test_evidence_request_unreceived(self):
        self.fixture["evidenceRequests"][0]["status"] = "received"
        self.reject("missing provenance or false approval")

    def test_duplicate_evidence_request_rejected(self):
        self.fixture["evidenceRequests"][1]["controlId"] = (
            self.fixture["evidenceRequests"][0]["controlId"])
        self.reject("wrong owner, missing provenance")

    def test_suppressed_control_rejected(self):
        self.fixture["evidenceRequests"].pop()
        self.reject("all ten required")

    def test_changed_owner_role_rejected(self):
        self.fixture["ownerActions"][0]["ownerRole"] = "administrator"
        self.reject("owner mismatch")

    def test_marked_complete_action_rejected(self):
        self.fixture["ownerActions"][0]["completionStatus"] = "completed"
        self.reject("forged completion")

    def test_real_actor_completion_rejected(self):
        self.fixture["ownerActions"][0]["completedByRealPerson"] = True
        self.reject("forged completion")

    def test_action_link_to_other_control_rejected(self):
        self.fixture["ownerActions"][0]["requestId"] = (
            self.fixture["ownerActions"][1]["requestId"])
        self.reject("owner mismatch")

    def test_false_due_date_rejected(self):
        self.fixture["ownerActions"][0]["dueDate"] = "2026-10-24"
        self.reject("forged completion")

    def test_exception_cannot_waive_control(self):
        self.fixture["exceptionRequests"][0]["waiveControl"] = True
        self.reject("cannot waive")

    def test_exception_cannot_trigger_deployment(self):
        self.fixture["exceptionRequests"][0]["mayDeploy"] = True
        self.reject("cannot waive")

    def test_exception_cannot_be_real_signoff(self):
        self.fixture["exceptionRequests"][0]["approvedByRealPerson"] = True
        self.reject("cannot waive")

    def test_exception_cannot_reference_real_evidence(self):
        self.fixture["exceptionRequests"][0]["sourceRef"] = "SAP-SECRET"
        self.reject("cannot waive")

    def test_exception_must_have_context_not_empty(self):
        self.fixture["exceptionRequests"][0]["rationale"] = ""
        self.reject("cannot waive")

    def test_missing_exception_rejected(self):
        self.fixture["exceptionRequests"].pop()
        self.reject("two negative")

    def test_duplicate_exception_id_rejected(self):
        self.fixture["exceptionRequests"][1]["exceptionId"] = (
            self.fixture["exceptionRequests"][0]["exceptionId"])
        self.reject("duplicated exercise")

    def test_remove_scenario_rejected(self):
        self.fixture["changeScenarios"].pop()
        self.reject("all change triggers")

    def test_change_scenario_cannot_disable_reopen(self):
        self.fixture["changeScenarios"][0]["reopenReview"] = False
        self.reject("cannot suppress invalidation")

    def test_change_scenario_cannot_reapprove_automatically(self):
        self.fixture["changeScenarios"][0]["automaticReapproval"] = True
        self.reject("cannot suppress invalidation")

    def test_change_scenario_cannot_keep_prior_qualification(self):
        self.fixture["changeScenarios"][0]["previousQualificationRemainsValid"] = True
        self.reject("cannot suppress invalidation")

    def test_change_scenario_cannot_enable_operations(self):
        self.fixture["changeScenarios"][0]["operationalPermission"] = True
        self.reject("cannot suppress invalidation")

    def test_change_scenario_cannot_suppress_one_dependency(self):
        self.fixture["changeScenarios"][0]["invalidates"].pop()
        self.reject("cannot suppress invalidation")

    def test_change_scenario_cannot_add_unreviewed_dependency(self):
        self.fixture["changeScenarios"][0]["invalidates"].append("invented")
        self.reject("cannot suppress invalidation")

    def test_change_scenario_never_claims_real_event(self):
        self.fixture["changeScenarios"][0]["state"] = "occurred_in_mine"
        self.reject("cannot suppress invalidation")

    def test_publication_private_data_forbidden(self):
        self.fixture["publication"]["privateDataIncluded"] = True
        self.reject("corporate/private/licensed")

    def test_publication_real_identifier_forbidden(self):
        self.fixture["publication"]["realIdentifiersIncluded"] = True
        self.reject("corporate/private/licensed")

    def test_publication_license_violation_forbidden(self):
        self.fixture["publication"]["licensedManualIncluded"] = True
        self.reject("corporate/private/licensed")

    def test_publication_false_share_authority_forbidden(self):
        self.fixture["publication"]["mayShareWithPublic"] = True
        self.reject("corporate/private/licensed")

    def test_dossier_source_contract_migration_blocked(self):
        self.fixture["sourceReadinessVersion"] = "2.0.0"
        self.reject("source Cycle 11 contract incompatible")

    def test_unknown_extra_sap_command_rejected(self):
        self.fixture["ownerActions"][0]["sapCommand"] = "create_order"
        self.reject("unrecognized or missing fields")

    def test_source_tampering_is_rejected_using_cycle_11_rules(self):
        self.source["controls"][0]["status"] = "independently_verified"
        self.reject("unverified status")

    def test_html_does_not_accept_forged_approval(self):
        report = self.result()
        report["deploymentApproved"] = True
        with self.assertRaises(ImportRejected):
            render_html(report)

    def test_cli_writes_json_html_only_for_valid_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            jsonpath = Path(tmp) / "dossier.json"
            htmlpath = Path(tmp) / "dossier.html"
            with patch("builtins.print"):
                result = main(["--output", str(jsonpath), "--html", str(htmlpath)])
            self.assertEqual(result, 0)
            self.assertTrue(jsonpath.exists())
            self.assertTrue(htmlpath.exists())
            parsed = json.loads(jsonpath.read_text())
            self.assertEqual(parsed["findingCount"], 10)
            self.assertIn("SIMULADO", htmlpath.read_text())

    def test_cli_rejects_and_does_not_write_file_on_bad_fixture(self):
        self.fixture["independentReviewGate"]["mayDeploy"] = True
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "injected.json"
            out = Path(tmp) / "should-not-exist.html"
            src.write_text(json.dumps(self.fixture))
            with patch("sys.stderr"):
                status = main(["--fixture", str(src), "--html", str(out)])
            self.assertEqual(status, 2)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
