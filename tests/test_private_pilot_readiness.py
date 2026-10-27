"""Ciclo 19: readiness public contract tests, no authenticated external evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT,validate_catalog as original_catalog
from casefiles.integrated import load_dependencies,build_collection
from notifications.drafts import SPEC_PATH,build_notifications
from quality.notifications import RUBRIC_PATH,ORACLE_PATH,build_report as quality_report
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_FIXTURE,build_report as editorial_report
from pilot.readiness import (FIXTURE_PATH,build_report,validate_fixture,verify_report,
                             render_html,main)

class PrivatePilotReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,reg,snapshot:original_catalog(cat,reg)):
            cls.deps=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).deps)
        self.fixture=json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def editorial(self):
        src=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        fake={"caseId":src["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":x["hypothesisId"]}
                            for x in self.deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],
              "conflicts":[],"knowledgeGaps":[]}
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=fake)):
            cases=build_collection(json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text()),
                                   self.deps,self.snapshot)
        notes=build_notifications(json.loads(SPEC_PATH.read_text()),cases["cases"],
                                  cases["investigationTrees"])
        quality=quality_report(notes,cases,json.loads(RUBRIC_PATH.read_text()),
                               json.loads(ORACLE_PATH.read_text()))
        return editorial_report(json.loads(EDITORIAL_FIXTURE.read_text()),quality,notes)

    def output(self):
        return build_report(self.fixture,self.editorial())

    def reject(self):
        with self.assertRaises(ImportRejected):
            self.output()

    def test_thirteen_requirements_five_owners_ten_threats(self):
        result=self.output()
        self.assertEqual(result["controlCount"],13)
        self.assertEqual(result["verifiedControlCount"],0)
        self.assertEqual(result["signoffCount"],5)
        self.assertEqual(result["verifiedSignoffCount"],0)
        self.assertEqual(result["threatCount"],10)
        self.assertEqual(result["scenarioCount"],4)
        self.assertEqual(result["readinessDecision"],"blocked_no_external_evidence")
        self.assertEqual(result["realPilotAuthorized"],False)

    def test_no_real_assurance_or_effectivity_ever_claimed(self):
        r=self.output()
        self.assertEqual(len(r["externalProofGaps"]),5)
        self.assertEqual(r["realExpertAgreementMeasured"],False)
        self.assertEqual(r["pilotExecuted"],False)
        self.assertEqual(r["mayWriteSap"],False)
        self.assertEqual(r["mayAlterEcm"],False)
        self.assertEqual(r["mayApproveMaintenance"],False)
        self.assertEqual(r["mayReleaseEquipment"],False)
        self.assertTrue(all(x["status"]=="not_verified"
                            and x["proofCount"]==0 for x in r["requiredExternalEvidence"]))
        self.assertTrue(all(not x["mitigationExternallyVerified"]
                            for x in r["threats"]))
        self.assertTrue(all(x is False for x in r["studyProtocol"].values()))

    def test_sources_separate_oem_from_nist_owasp_lgpd(self):
        f=self.fixture
        self.assertEqual(len(f["sources"]),4)
        self.assertEqual(f["sources"][-1]["sourceId"],"OEM-APPLICABILITY-PENDING")
        self.assertIsNone(f["sources"][-1]["uri"])
        self.assertEqual(f["controls"][6]["sourceId"],"OEM-APPLICABILITY-PENDING")
        self.assertEqual(f["controls"][7]["sourceId"],"OEM-APPLICABILITY-PENDING")
        self.assertEqual(f["sources"][0]["sourceId"],"NIST-800-63-4")

    def test_reopening_preserves_external_block(self):
        r=self.output()
        self.assertEqual([x["trigger"] for x in r["scenarios"]],
                         ["none","reviewer_credential_revoked",
                          "oem_revision_changed","equipment_configuration_changed"])
        self.assertEqual([x["reopenRequired"] for x in r["scenarios"]],
                         [False,True,True,True])
        self.assertTrue(all(x["decision"]=="blocked_pending_external_verification"
                            for x in r["scenarios"]))
        self.assertTrue(all(not x["previousReviewIsBinding"]
                            and not x["sourceDocumentCurrent"]
                            and not x["evidenceOfCurrentIndependentReview"]
                            for x in r["scenarios"]))

    def test_audit_digest_chain_repeatable(self):
        a=self.output()
        self.assertEqual(a,self.output())
        for left,right in zip(a["scenarios"],a["scenarios"][1:]):
            self.assertEqual(left["eventDigest"],right["previousDigest"])
        self.assertEqual(a["scenarioAuditHeadDigest"],a["scenarios"][-1]["eventDigest"])
        self.assertFalse(a["externalAuditAnchorVerified"])

    def test_cannot_set_login_connected(self):
        self.fixture["identityProviderConnected"]=True
        self.reject()

    def test_cannot_inject_real_field_data(self):
        self.fixture["corporateDataImported"]=True
        self.reject()

    def test_cannot_claim_actual_pilot_approved(self):
        self.fixture["mayRunPrivatePilot"]=True
        self.reject()

    def test_cannot_claim_oem_license_available(self):
        self.fixture["licensedOemDocumentAvailable"]=True
        self.reject()

    def test_fake_verified_control_rejected(self):
        self.fixture["controls"][0]["proofStatus"]="verified"
        self.reject()

    def test_fake_signature_or_approval_in_control_rejected(self):
        self.fixture["controls"][4]["authorityVerified"]=True
        self.reject()

    def test_no_optional_bypass_acceptance(self):
        self.fixture["controls"][0]["mayWaive"]=True
        self.reject()

    def test_injecting_oem_serial_ref_rejected(self):
        self.fixture["controls"][6]["externalEvidenceRef"]="OEM-REAL-SERIAL-123"
        self.reject()

    def test_pilot_cannot_use_lgpd_as_oem_effectivity(self):
        self.fixture["controls"][6]["sourceId"]="LGPD-13709"
        self.reject()

    def test_duplicate_control_rejected(self):
        self.fixture["controls"][1]["controlId"]="identity-proof"
        self.reject()

    def test_fake_it_approval_rejected(self):
        self.fixture["stakeholders"][0]["signoff"]="approved"
        self.reject()

    def test_real_signatory_rejected(self):
        self.fixture["stakeholders"][3]["externalApprovalProof"]="SIGNED-PRIVATE"
        self.reject()

    def test_threat_suppression_rejected(self):
        self.fixture["threats"].pop()
        self.reject()

    def test_conflict_of_interest_threat_cannot_be_waived(self):
        self.fixture["threats"][5]["expectedDecision"]="accept_risk"
        self.reject()

    def test_fake_telemetry_exposure_rejected(self):
        self.fixture["threats"][7]["fieldExposureObserved"]=True
        self.reject()

    def test_oem_doc_not_publicly_admissible(self):
        self.fixture["classificationPolicy"][2]["allowedRepository"]="public"
        self.reject()

    def test_cannot_set_retention_without_legal_approval(self):
        self.fixture["classificationPolicy"][1]["retentionDays"]=365
        self.reject()

    def test_credential_revocation_cannot_validate_previous_review(self):
        self.fixture["scenarios"][1]["currentReviewValid"]=True
        self.reject()

    def test_change_oem_revision_must_reopen(self):
        self.fixture["scenarios"][2]["trigger"]="none"
        self.reject()

    def test_field_release_cannot_be_claimed(self):
        self.fixture["scenarios"][3]["mayReleaseEquipment"]=True
        self.reject()

    def test_inter_rater_reliability_cannot_be_fabricated(self):
        self.fixture["studyProtocol"]["realAgreementMeasured"]=True
        self.reject()

    def test_user_consent_cannot_be_fabricated(self):
        self.fixture["studyProtocol"]["consentAndLegalBasisApproved"]=True
        self.reject()

    def test_unknown_private_proof_field_rejected(self):
        self.fixture["controls"][0]["secretToken"]="DO-NOT-COPY"
        self.reject()

    def test_html_static_and_escaped(self):
        r=self.output()
        h=render_html(r)
        self.assertIn("Content-Security-Policy",h)
        self.assertNotIn("<script",h)
        self.assertNotIn("<form",h)
        self.assertIn("NÃO AUTORIZADO",h)
        self.assertEqual(h.count("<tr>"),14)
        r["requiredExternalEvidence"][0]["missingEvidence"]="<script>inert</script>"
        self.assertIn("&lt;script&gt;",render_html(r))

    def test_html_rejects_forged_real_approval(self):
        r=self.output()
        r["mayWriteSap"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_rejects_forged_proof(self):
        r=self.output()
        r["requiredExternalEvidence"][0]["proofCount"]=1
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_verifier_detects_tampered_chain_or_decision(self):
        e=self.editorial()
        report=build_report(self.fixture,e)
        self.assertEqual(verify_report(report,self.fixture,e),report)
        report["scenarios"][0]["eventDigest"]="0"*64
        with self.assertRaises(ImportRejected):
            verify_report(report,self.fixture,e)

    def test_forged_editorial_approval_rejected(self):
        editorial=self.editorial()
        editorial["realApprovalsGranted"]=1
        with self.assertRaises(ImportRejected):
            build_report(self.fixture,editorial)

    def test_canonical_baseline_has_no_real_reviewer_names(self):
        for owner in self.fixture["stakeholders"]:
            self.assertFalse(owner["qualifiedSignatoryVerified"])
            self.assertIsNone(owner["externalApprovalProof"])

if __name__=="__main__":
    unittest.main()
