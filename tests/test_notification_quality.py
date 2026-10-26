"""Cycle 17 editorial-only notification quality regression tests."""
import copy
import json
import unittest
from unittest.mock import patch
from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as original_catalog
from casefiles.integrated import load_dependencies, build_collection
from notifications.drafts import SPEC_PATH, build_notifications
from quality.notifications import (RUBRIC_PATH, ORACLE_PATH, assess_draft,
                                   build_report, render_html, validate_rubric,
                                   validate_oracle, verify_report, _apply_mutation)

class QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,registry,snapshot: original_catalog(cat,registry)):
            cls.dependencies=load_dependencies(cls.snapshot)

    def setUp(self):
        self.dependencies=copy.deepcopy(type(self).dependencies)
        self.rubric=json.loads(RUBRIC_PATH.read_text())
        self.oracle=json.loads(ORACLE_PATH.read_text())

    def corpus(self):
        fixture=json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text())
        spec=json.loads(SPEC_PATH.read_text())
        raw=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        pilot={"caseId":raw["caseId"],"confirmedRootCause":None,
               "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
               "hypotheses":[{"id":x["hypothesisId"]}
                             for x in self.dependencies["families"]["final_drive"]["hypotheses"]],
               "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
               "decision":"needs_evidence","observations":[],"conflicts":[],"knowledgeGaps":[]}
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=pilot)):
            casefiles=build_collection(fixture,self.dependencies,self.snapshot)
        drafts=build_notifications(spec,casefiles["cases"],casefiles["investigationTrees"])
        return casefiles,drafts

    def test_twelve_criteria_and_four_drafts(self):
        self.assertEqual(len(validate_rubric(self.rubric)),12)
        src,drafts=self.corpus()
        report=build_report(drafts,src,self.rubric,self.oracle)
        self.assertEqual(report["assessedDraftCount"],4)
        self.assertEqual(report["documentsApprovedForField"],0)
        self.assertEqual(report["realNotificationsCreated"],0)
        self.assertFalse(report["interRaterReliabilityMeasured"])
        for a in report["assessments"]:
            self.assertEqual(a["status"],"adequate_for_synthetic_training")
            self.assertEqual(a["criteriaMet"],12)
            self.assertEqual(a["criteriaNeedsRevision"],0)
            self.assertEqual(len(a["externalEvidenceGaps"]),4)
            self.assertFalse(a["mayCreateSapNotification"])
            self.assertTrue(all(v is False for v in a["humanEditorialReview"].values()))

    def test_adversarial_oracle_fourteen_cases(self):
        src,drafts=self.corpus()
        report=build_report(drafts,src,self.rubric)
        self.assertTrue(validate_oracle(self.oracle,report,drafts,src,self.rubric))
        self.assertEqual(len(self.oracle["adversarial"]),14)
        for m in self.oracle["adversarial"]:
            with self.subTest(scenario=m["scenarioId"]):
                index=int(m["draftId"][-1])-1
                draft=copy.deepcopy(drafts["drafts"][index])
                _apply_mutation(draft,m["fieldPath"],m["replacement"])
                a=assess_draft(draft,src["cases"][index],
                               src["investigationTrees"]["trees"][index],self.rubric)
                self.assertEqual(a["status"],m["expectedStatus"])
                self.assertTrue(any(x["criterionId"]==m["expectedCriterion"]
                                    and x["status"]=="needs_revision"
                                    for x in a["findings"]))
                self.assertFalse(a["mayBeUsedForFieldMaintenance"])

    def test_missing_requirement_only_documentary(self):
        src,drafts=self.corpus()
        d=copy.deepcopy(drafts["drafts"][2])
        d["symptom"]["functionalRequirement"]=""
        a=assess_draft(d,src["cases"][2],src["investigationTrees"]["trees"][2],
                       self.rubric)
        self.assertEqual(a["status"],"needs_documentary_revision")
        self.assertEqual(a["criteriaNeedsRevision"],1)
        self.assertTrue(a["missingInformation"])

    def test_sensitive_values_not_copied_to_findings(self):
        src,drafts=self.corpus()
        d=copy.deepcopy(drafts["drafts"][0])
        d["planningConstraint"]["sapNotificationNumber"]="EXAMPLE-NONPUBLIC-ID"
        a=assess_draft(d,src["cases"][0],src["investigationTrees"]["trees"][0],
                       self.rubric)
        self.assertEqual(a["status"],"blocked_unsafe_claims")
        self.assertNotIn("EXAMPLE-NONPUBLIC-ID",json.dumps(a))

    def test_change_rubric_or_oracle_rejected(self):
        src,drafts=self.corpus()
        for key,value in (("expertValidated",True),("mayIssueSapNotification",True)):
            c=copy.deepcopy(self.rubric)
            c[key]=value
            with self.subTest(key=key),self.assertRaises(ImportRejected):
                validate_rubric(c)
        for mode in ("drop_baseline","approve","change_expectation"):
            o=copy.deepcopy(self.oracle)
            if mode=="drop_baseline":
                o["baseline"].pop()
            elif mode=="approve":
                o["baseline"][0]["realMaintenanceApproved"]=True
            else:
                o["adversarial"][0]["expectedCriterion"]="scope_is_investigation"
            with self.subTest(mode=mode),self.assertRaises(ImportRejected):
                build_report(drafts,src,self.rubric,o)

    def test_source_sap_claim_rejected(self):
        src,drafts=self.corpus()
        drafts["mayConnectToSap"]=True
        with self.assertRaises(ImportRejected):
            build_report(drafts,src,self.rubric,self.oracle)

    def test_fake_training_quality_rejected(self):
        src,drafts=self.corpus()
        drafts["drafts"][0]["causalAssessment"]["confirmedDefect"]="confirmed"
        with self.assertRaises(ImportRejected):
            build_report(drafts,src,self.rubric,self.oracle)

    def test_html_offline_escaped_and_no_fake_approval(self):
        src,drafts=self.corpus()
        report=build_report(drafts,src,self.rubric,self.oracle)
        html=render_html(report)
        self.assertEqual(html.count("<section>"),4)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("Content-Security-Policy",html)
        altered=copy.deepcopy(report)
        altered["assessments"][0]["findings"][0]["criterionTitle"]="<script>sample</script>"
        self.assertIn("&lt;script&gt;",render_html(altered))
        for key,value in (("mayCreateSapNotification",True),
                          ("documentsApprovedForField",1)):
            tampered=copy.deepcopy(report)
            tampered[key]=value
            with self.subTest(key=key),self.assertRaises(ImportRejected):
                render_html(tampered)

    def test_forged_expert_approval_or_removed_gap_rejected(self):
        src,drafts=self.corpus()
        report=build_report(drafts,src,self.rubric,self.oracle)
        for path in ("human","gap","score"):
            t=copy.deepcopy(report)
            if path=="human":
                t["assessments"][0]["humanEditorialReview"]["engineeringExpertAuthenticated"]=True
            elif path=="gap":
                t["assessments"][0]["externalEvidenceGaps"][0]["evidenceReceived"]=True
            else:
                t["assessments"][0]["criteriaMet"]=11
            with self.subTest(path=path),self.assertRaises(ImportRejected):
                if path=="score":
                    verify_report(t,drafts,src,self.rubric,self.oracle)
                else:
                    render_html(t)

if __name__=="__main__":
    unittest.main()
