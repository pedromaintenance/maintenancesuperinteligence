"""Adversarial cycle 22: contradictory public documentary claims never approve field work."""
import copy
import json
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as original_catalog
from casefiles.integrated import load_dependencies, build_collection
from notifications.drafts import SPEC_PATH as NOTES_SPEC, build_notifications
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as quality_report
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_FIXTURE, build_report as editorial_report
from pilot.readiness import FIXTURE_PATH as READINESS_FIXTURE, build_report as readiness_report
from pilot.go_nogo import PACKAGE_PATH, build_report as gng_report
from pilot.evidence_sequence import SPEC_PATH as SEQUENCE_SPEC, build_report as sequence_report
from pilot.evidence_contradictions import (
    FIXTURE_PATH, build_report, validate_fixture, verify_report,
    descendant_cascade, render_html,
)

class EvidenceContradictionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,reg,snapshot: original_catalog(cat,reg)):
            cls.deps=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).deps)
        self.fixture=json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def base(self):
        raw=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        fake={"caseId":raw["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":x["hypothesisId"]}
                            for x in self.deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],"conflicts":[],"knowledgeGaps":[]}
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=fake)):
            cases=build_collection(
                json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text()),
                self.deps,self.snapshot)
        notes=build_notifications(json.loads(NOTES_SPEC.read_text()),
                                  cases["cases"],cases["investigationTrees"])
        quality=quality_report(notes,cases,json.loads(RUBRIC_PATH.read_text()),
                               json.loads(ORACLE_PATH.read_text()))
        editorial=editorial_report(json.loads(EDITORIAL_FIXTURE.read_text()),quality,notes)
        readiness=readiness_report(json.loads(READINESS_FIXTURE.read_text()),editorial)
        gng=gng_report(json.loads(PACKAGE_PATH.read_text()),readiness)
        sequence=sequence_report(json.loads(SEQUENCE_SPEC.read_text()),gng)
        return sequence,gng

    def report(self):
        seq,gng=self.base()
        return build_report(self.fixture,seq,gng)

    def reject(self):
        seq,gng=self.base()
        with self.assertRaises(ImportRejected):
            build_report(self.fixture,seq,gng)

    def test_six_crossfunctional_scenarios_stay_hypothetical(self):
        r=self.report()
        self.assertEqual(r["scenarioCount"],6)
        self.assertEqual(r["crossReviewQuestionCount"],6)
        self.assertEqual(r["sourceControlCount"],13)
        self.assertEqual(r["sourceDependencyCount"],17)
        self.assertEqual(r["decision"],"no_go")
        self.assertEqual(r["verifiedPhysicalFaults"],0)
        self.assertEqual(r["externalProofsVerified"],0)
        self.assertEqual(r["independentRealReviewsCompleted"],0)
        self.assertFalse(r["canAuthorizePilot"])
        self.assertFalse(r["canWriteSap"])
        self.assertFalse(r["canModifyEcm"])
        self.assertFalse(r["canCreateWorkOrder"])
        self.assertFalse(r["canReleaseEquipment"])

    def test_all_six_reopen_descendants_and_preserve_no_go(self):
        r=self.report()
        for c in r["scenarios"]:
            cascade=c["dependencyReopenCascade"]
            self.assertEqual(len(c["sourceControls"]),2)
            self.assertTrue(set(c["sourceControls"])<=set(cascade["allAffectedControls"]))
            self.assertEqual(cascade["affectedCount"],len(cascade["allAffectedControls"]))
            self.assertTrue(cascade["allReopenedAsUnverified"])
            self.assertFalse(cascade["operationallyApproved"])
            self.assertTrue(cascade["externalReviewRequired"])
            self.assertEqual(c["noGoDisposition"]["decision"],"no_go")
            self.assertFalse(c["finding"]["realWorldConflictConfirmed"])
            self.assertFalse(c["finding"]["mechanicalFailureConfirmed"])
            self.assertTrue(all(x is False for k,x in c["noGoDisposition"].items()
                                if k.startswith("may")))

    def test_review_questions_are_not_actual_human_assessments(self):
        for case in self.report()["scenarios"]:
            r=case["crossFunctionalReviewQuestion"]
            self.assertEqual(r["answer"],"not_available")
            self.assertFalse(r["realReviewPerformed"])
            self.assertFalse(r["crossFunctionConsensusEstablished"])
            self.assertTrue(r["primaryOwner"])
            self.assertTrue(r["peerOwner"])

    def test_oem_change_reopens_operational_firewall(self):
        r=self.report()["scenarios"][2]
        self.assertEqual(r["conflictMechanism"],"oem_revision_superseded")
        self.assertIn("operational-firewall",
                      r["dependencyReopenCascade"]["allAffectedControls"])
        self.assertIn("oem-effectivity",r["dependencyReopenCascade"]["triggerControls"])

    def test_privacy_retention_cascades_to_oem_and_operation(self):
        cascade=self.report()["scenarios"][5]["dependencyReopenCascade"]
        self.assertIn("evidence-legitimacy",cascade["allAffectedControls"])
        self.assertIn("oem-effectivity",cascade["allAffectedControls"])
        self.assertIn("operational-firewall",cascade["allAffectedControls"])

    def test_invalidation_preserves_unconfirmed_status(self):
        for c in self.report()["scenarios"]:
            self.assertEqual(len(c["staleProofInvalidations"]),2)
            for proof in c["staleProofInvalidations"]:
                self.assertFalse(proof["sourceAuthenticated"])
                self.assertFalse(proof["currentRevisionVerified"])
                self.assertFalse(proof["priorAssertionStillBinding"])
                self.assertFalse(proof["evidenceDiscardedAsFailure"])
                self.assertTrue(proof["invalidatedForDecision"])

    def test_report_deterministic_and_verifier_recomputes(self):
        seq,gng=self.base()
        r=build_report(self.fixture,seq,gng)
        self.assertEqual(r,build_report(self.fixture,seq,gng))
        self.assertEqual(verify_report(r,self.fixture,seq,gng),r)
        r["scenarios"][0]["dependencyReopenCascade"]["allAffectedControls"].pop()
        with self.assertRaises(ImportRejected):
            verify_report(r,self.fixture,seq,gng)

    def test_refuse_measured_assertion(self):
        self.fixture["scenarios"][0]["assertions"][0]["observed"]=True
        self.reject()

    def test_refuse_fake_authentication(self):
        self.fixture["scenarios"][1]["assertions"][1]["authenticated"]=True
        self.reject()

    def test_refuse_real_person_or_document(self):
        self.fixture["scenarios"][0]["assertions"][0]["claimantId"]="PRIVATE-BADGE"
        self.reject()

    def test_refuse_external_oem_document_url(self):
        self.fixture["scenarios"][2]["assertions"][1]["sourceDocument"]="private-manual"
        self.reject()

    def test_refuse_missing_conflict(self):
        self.fixture["scenarios"][4]["conflictExpected"]=False
        self.reject()

    def test_refuse_stale_proof_declared_current(self):
        self.fixture["scenarios"][2]["priorProofInvalidated"]=False
        self.reject()

    def test_refuse_skipped_revision(self):
        self.fixture["scenarios"][2]["assertions"][1]["documentRevision"]=4
        self.reject()

    def test_refuse_replaced_claim(self):
        self.fixture["scenarios"][2]["assertions"][0]["claim"]="mechanical_fault_confirmed"
        self.reject()

    def test_refuse_wrong_control_dependency(self):
        self.fixture["scenarios"][3]["triggerControlIds"][0]="signed-decision"
        self.reject()

    def test_refuse_removed_scenario(self):
        self.fixture["scenarios"].pop()
        self.reject()

    def test_refuse_deleted_crossreview_question(self):
        self.fixture["questions"].pop()
        self.reject()

    def test_refuse_external_question_answer(self):
        self.fixture["questions"][0]["answeredByRealPerson"]=True
        self.reject()

    def test_refuse_forged_consensus(self):
        self.fixture["questions"][4]["approvalGranted"]=True
        self.reject()

    def test_refuse_policy_sap(self):
        self.fixture["policy"]["mayWriteSap"]=True
        self.reject()

    def test_refuse_policy_machine_release(self):
        self.fixture["policy"]["mayReleaseEquipment"]=True
        self.reject()

    def test_refuse_bypass_propagation(self):
        self.fixture["policy"]["propagateToAllDescendants"]=False
        self.reject()

    def test_refuse_hidden_confidential_field(self):
        self.fixture["scenarios"][0]["assertions"][0]["employeeName"]="secret"
        self.reject()

    def test_refuse_false_real_incident(self):
        self.fixture["scenarios"][0]["realIncidentObserved"]=True
        self.reject()

    def test_refuse_reversed_document_context_claim_revision(self):
        self.fixture["scenarios"][2]["assertions"][0]["contextRevision"]=2
        self.reject()

    def test_html_static_offline_and_escapes(self):
        r=self.report()
        html=render_html(r)
        self.assertEqual(html.count("<section>"),6)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        r["scenarios"][0]["crossFunctionalReviewQuestion"]["question"]="<script>bad</script>"
        self.assertIn("&lt;script&gt;",render_html(r))

    def test_html_refuses_sap_approval(self):
        r=self.report()
        r["canWriteSap"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_refuses_real_world_contradiction_claim(self):
        r=self.report()
        r["scenarios"][2]["finding"]["realWorldConflictConfirmed"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_refuses_fake_source_approval(self):
        r=self.report()
        r["scenarios"][3]["staleProofInvalidations"][0]["sourceAuthenticated"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_reopening_does_not_exclude_other_controls(self):
        seq,gng=self.base()
        graph=validate_fixture(self.fixture,seq,gng)
        result=descendant_cascade(["identity-proof"],graph)
        self.assertIn("two-independent-reviews",result)
        self.assertIn("operational-firewall",result)
        self.assertNotIn("oem-effectivity",result)

    def test_reject_upstream_missing_edge(self):
        seq,gng=self.base()
        gng["approvalDependencies"][3]["predecessors"].pop()
        with self.assertRaises(ImportRejected):
            build_report(self.fixture,seq,gng)

    def test_reject_upstream_false_approved_evidence(self):
        seq,gng=self.base()
        seq["verifiedEvidenceCount"]=1
        with self.assertRaises(ImportRejected):
            build_report(self.fixture,seq,gng)

if __name__=="__main__":
    unittest.main()
