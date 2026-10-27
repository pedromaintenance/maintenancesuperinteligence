"""Ciclo 21: topological evidence-only sequencing and zero operational authority."""
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
from pilot.go_nogo import PACKAGE_PATH as GNG_PACKAGE, build_report as gng_report
from pilot.evidence_sequence import (SPEC_PATH,topological_sequence,validate_spec,
                                     build_report,render_html,verify_report)

class EvidenceSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda catalog,registry,snapshot:original_catalog(catalog,registry)):
            cls.deps=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).deps)
        self.spec=json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def gng(self):
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
        editorial=editorial_report(json.loads(EDITORIAL_FIXTURE.read_text()),
                                  quality,notes)
        ready=readiness_report(json.loads(READINESS_FIXTURE.read_text()),editorial)
        return gng_report(json.loads(GNG_PACKAGE.read_text()),ready)

    def reject(self):
        with self.assertRaises(ImportRejected):
            build_report(self.spec,self.gng())

    def report(self):
        return build_report(self.spec,self.gng())

    def test_expected_structure_and_no_go(self):
        r=self.report()
        self.assertEqual(r["controlCount"],13)
        self.assertEqual(r["dependencyLinkCount"],17)
        self.assertEqual(r["phaseCount"],7)
        self.assertEqual(r["handoffCount"],5)
        self.assertEqual(r["adversarialCaseCount"],10)
        self.assertEqual(r["decision"],"no_go")
        self.assertEqual(r["verifiedEvidenceCount"],0)
        self.assertEqual(r["verifiedExternalAcceptances"],0)
        self.assertEqual(r["realPilotActivitiesExecuted"],0)
        self.assertFalse(r["executionAuthorized"])
        self.assertFalse(r["realTimelineApproved"])
        self.assertFalse(r["realBudgetApproved"])

    def test_all_predecessors_precede_control(self):
        r=self.report()
        order={cid:i for i,cid in enumerate(r["topologicalOrder"])}
        self.assertEqual(len(order),13)
        for c in r["sequencedControls"]:
            self.assertEqual(c["sequence"],order[c["controlId"]]+1)
            for parent in c["predecessors"]:
                self.assertLess(order[parent],order[c["controlId"]])
            self.assertFalse(c["evidenceVerified"])
            self.assertFalse(c["canProceed"])

    def test_roots_and_depths_are_structural_not_duration(self):
        r=self.report()
        self.assertEqual(r["rootPrerequisites"],[
            "identity-proof","equipment-configuration","privacy-retention"])
        self.assertGreaterEqual(r["dependencyMaximumDepth"],3)
        self.assertEqual(r["sequencedControls"][0]["graphDepth"],0)
        self.assertEqual(sum(len(x["predecessors"]) for x in r["sequencedControls"]),17)
        self.assertTrue(all(x["dependentDownstreamControls"]>=0
                            for x in r["sequencedControls"]))

    def test_stages_are_prescriptive_not_executed(self):
        r=self.report()
        self.assertEqual([p["sequenceNumber"] for p in r["phases"]],list(range(1,8)))
        self.assertTrue(all(p["documentaryState"]=="not_verified"
                            and not p["externalExecutionAuthorized"]
                            and p["scheduleDate"] is None
                            and p["estimatedCost"] is None
                            and p["workHours"] is None
                            for p in r["phases"]))
        self.assertFalse(r["oemSeriesApplicabilityVerified"])
        self.assertFalse(r["independentExpertReviewAuthenticated"])

    def test_handoffs_contain_only_fictional_evidence_ids(self):
        r=self.report()
        for h in r["externalHandoffs"]:
            self.assertTrue(h["packetId"].startswith("SIM-HANDOFF-"))
            self.assertTrue(all(x.startswith("SIM-PROOF-")
                                for x in h["evidenceManifestIds"]))
            self.assertFalse(h["realReceiptVerified"])
            self.assertFalse(h["externalSignoffRecorded"])
            self.assertFalse(h["containsCorporateData"])

    def test_threat_cases_remain_unremediated(self):
        r=self.report()
        self.assertEqual(len(r["adversarialCases"]),10)
        self.assertTrue(all(x["decision"]=="no_go"
                            and not x["mitigationAuthenticated"]
                            and not x["realIncidentObserved"]
                            for x in r["adversarialCases"]))

    def test_reject_circular_dependency(self):
        r=self.gng()
        r["approvalDependencies"][0]["predecessors"]=["revocation-reopen"]
        with self.assertRaises(ImportRejected):
            topological_sequence(r["approvalDependencies"])

    def test_reject_duplicate_prerequisite(self):
        r=self.gng()
        r["approvalDependencies"][3]["predecessors"]=[
            "competence","competence","version-lock"]
        with self.assertRaises(ImportRejected):
            topological_sequence(r["approvalDependencies"])

    def test_reject_unknown_prerequisite(self):
        r=self.gng()
        r["approvalDependencies"][3]["predecessors"]=["SIM-UNKNOWN"]
        with self.assertRaises(ImportRejected):
            topological_sequence(r["approvalDependencies"])

    def test_reject_phase_missing_control(self):
        self.spec["phases"][1]["controlIds"].remove("identity-proof")
        self.reject()

    def test_reject_phase_reordered(self):
        self.spec["phases"][0]["phaseId"],self.spec["phases"][1]["phaseId"]=(
            self.spec["phases"][1]["phaseId"],self.spec["phases"][0]["phaseId"])
        self.reject()

    def test_reject_premature_proof_submission(self):
        self.spec["proofRequests"][0]["submissionState"]="submitted"
        self.reject()

    def test_reject_forged_oem_validation(self):
        self.spec["proofRequests"][6]["originAuthorized"]=True
        self.reject()

    def test_reject_obsolete_revision_marked_current(self):
        self.spec["proofRequests"][3]["documentRevisionCurrent"]=True
        self.reject()

    def test_reject_false_reviewer_independence(self):
        self.spec["proofRequests"][3]["reviewerVerified"]=True
        self.reject()

    def test_reject_fake_evidence_sha(self):
        self.spec["proofRequests"][6]["evidenceUri"]="SIM-FAKE"
        self.reject()

    def test_reject_wrong_owner(self):
        self.spec["proofRequests"][6]["owner"]="Legal"
        self.reject()

    def test_reject_unapproved_handoff(self):
        self.spec["externalHandoffs"][0]["realReceiptVerified"]=True
        self.reject()

    def test_reject_forged_handoff_signature(self):
        self.spec["externalHandoffs"][2]["signoffEvidence"]="FAKE-APPROVAL"
        self.reject()

    def test_reject_conflicting_permissions(self):
        self.spec["policy"]["canTransmitSap"]=True
        self.reject()

    def test_reject_ecm_or_equipment_release(self):
        self.spec["policy"]["canAccessEcm"]=True
        self.reject()
        self.spec=json.loads(SPEC_PATH.read_text())
        self.spec["policy"]["canReleaseEquipment"]=True
        self.reject()

    def test_reject_invented_schedule(self):
        self.spec["daysPlanned"]=10
        self.reject()

    def test_reject_invented_cost_or_hours(self):
        self.spec["costPlanned"]=1000
        self.reject()
        self.spec=json.loads(SPEC_PATH.read_text())
        self.spec["workHoursPlanned"]=40
        self.reject()

    def test_reject_false_completed_remediation(self):
        self.spec["adversarialReviewScenarios"][0]["remediationClosed"]=True
        self.reject()

    def test_reject_suppressed_threat(self):
        self.spec["adversarialReviewScenarios"].pop()
        self.reject()

    def test_reject_real_field_incident_claim(self):
        self.spec["adversarialReviewScenarios"][1]["actualIncidentConfirmed"]=True
        self.reject()

    def test_reject_forged_interrater_statistics(self):
        self.spec["policy"]["interRaterResultsAvailable"]=True
        self.reject()

    def test_report_verifies_source_and_rejects_tampering(self):
        upstream=self.gng()
        out=build_report(self.spec,upstream)
        self.assertEqual(verify_report(out,self.spec,upstream),out)
        out["sequencedControls"][0]["canProceed"]=True
        with self.assertRaises(ImportRejected):
            verify_report(out,self.spec,upstream)

    def test_html_is_static_and_escapes_text(self):
        r=self.report()
        html=render_html(r)
        self.assertIn("Content-Security-Policy",html)
        self.assertIn("NO GO",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        r["sequencedControls"][0]["controlId"]="<script>inert</script>"
        self.assertIn("&lt;script&gt;",render_html(r))

    def test_html_rejects_fake_field_approval(self):
        r=self.report()
        r["executionAuthorized"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_rejects_fake_evidence(self):
        r=self.report()
        r["sequencedControls"][0]["evidenceVerified"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

if __name__=="__main__":
    unittest.main()
