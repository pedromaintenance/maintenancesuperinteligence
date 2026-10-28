"""Cycle 29: safety-oriented reviewer protocol rehearsal, no real human participants."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pilot.change_review_packets import ReviewRejected
from benchmarks.blind_review_protocol import (
    SOURCE_CASES, SOURCE_ORACLE, REVIEW_FIXTURE, RUBRIC_PATH,
    SELECTED_IDS, SEVERITIES, REVIEWERS, SUBMISSION_KEYS,
    build_blind_packet, validate_blind, validate_rubric, validate_submissions,
    build_report, verify_report, render_html,
)

class Cycle29BlindReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SOURCE_CASES.read_text(encoding="utf-8"))
        cls.oracle = json.loads(SOURCE_ORACLE.read_text(encoding="utf-8"))
        cls.submissions = json.loads(REVIEW_FIXTURE.read_text(encoding="utf-8"))
        cls.rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))

    def test_export_contains_no_editorial_answer_or_oracle(self):
        packet = build_blind_packet(self.source)
        self.assertTrue(validate_blind(packet, self.source))
        self.assertEqual(packet["caseCount"], 12)
        self.assertEqual(tuple(c["caseId"] for c in packet["cases"]), SELECTED_IDS)
        self.assertFalse(packet["authorOracleIncluded"])
        self.assertEqual(packet["independentExpertsAssigned"], 0)
        encoded = json.dumps(packet)
        for marker in ("expectedNextQuestionId","authorExpectedQuestionId",
                       "gatedQuestionId","editorialOracle","matchesAuthorOracle"):
            self.assertNotIn(marker, encoded)
        self.assertTrue(all(c["equipmentSerialNumber"] is None
                            and c["oemApplicabilityVerified"] is False
                            and c["mayCreateWorkOrder"] is False
                            for c in packet["cases"]))
        forged = copy.deepcopy(packet)
        forged["cases"][0]["expectedNextQuestionId"] = "confirm_fluid_product_identity"
        with self.assertRaises(ReviewRejected):
            validate_blind(forged, self.source)

    def test_simulated_disagreements_are_preserved_not_resolved(self):
        report = build_report(self.source, self.oracle, self.submissions, self.rubric)
        self.assertTrue(verify_report(report,self.source,self.oracle,
                                      self.submissions,self.rubric))
        self.assertEqual(report["casesReviewedInSimulation"],12)
        self.assertEqual(report["fictionalReviewRecords"],24)
        self.assertEqual(report["simulatedQuestionAgreement"],{"same":8,"total":12})
        self.assertEqual(report["authorOracleAgreement"],{"matched":20,"total":24})
        self.assertEqual(report["criticalFindings"],5)
        self.assertEqual(len(report["findings"]),10)
        self.assertEqual({x["errorCode"] for x in report["findings"]},set(SEVERITIES))
        self.assertTrue(all(c["realExpertConsensus"] is False for c in report["cases"]))
        self.assertFalse(report["independentExpertReviewCompleted"])
        self.assertFalse(report["realReviewerIdentitiesVerified"])
        self.assertFalse(report["realAgreementMeasured"])
        self.assertFalse(report["mechanicalDiagnosticAccuracyMeasured"])
        self.assertFalse(report["mayCreateWorkOrder"])
        self.assertFalse(report["mayReleaseEquipment"])
        self.assertEqual(report["decision"],"no_go_external_review_still_required")
        self.assertTrue(all(x["realSafetyIncident"] is False
                            for x in report["findings"]))

    def test_false_evidence_and_authentication_rejected(self):
        changes = [
            (("realReviewerCount",), 1),
            (("reviewerIdentityValidated",), True),
            (("independentReviewPerformed",), True),
            (("realSignatures",), 1),
            (("submissions",0,"realEngineeringSignoff"),True),
            (("submissions",1,"realReviewerAuthenticated"),True),
            (("submissions",2,"reviewerAlias"),"real engineer name"),
            (("submissions",3,"caseId"),"SIM-GEN-999"),
            (("submissions",4,"questionId"),"replace_pump_now"),
            (("submissions",5,"abstainsFromDiagnosis"),"false"),
        ]
        packet=build_blind_packet(self.source)
        for path,value in changes:
            altered=copy.deepcopy(self.submissions)
            node=altered
            for k in path[:-1]:node=node[k]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_submissions(altered,packet)

    def test_unapproved_behavior_is_detected_not_executed(self):
        corrupted=copy.deepcopy(self.submissions)
        for x in corrupted["submissions"]:
            x["proposesWorkOrder"]=True
            x["endorsesEquipmentRelease"]=True
            x["assertsRootCause"]=True
            x["claimsOemApplicability"]=True
            x["abstainsFromDiagnosis"]=False
        r=build_report(self.source,self.oracle,corrupted,self.rubric)
        self.assertGreaterEqual(r["criticalFindings"],24*5)
        self.assertFalse(r["mayCreateWorkOrder"])
        self.assertFalse(r["mayReleaseEquipment"])
        self.assertEqual(r["decision"],"no_go_external_review_still_required")
        self.assertTrue(all(x["unsafeClaimsPresent"] for c in r["cases"]
                            for x in c["twoSyntheticReviews"]))

    def test_rubric_can_not_downgrade_critical_findings(self):
        for path,value in [
            (("realExpertEndorsed",),True),
            (("errors",0,"severity"),"minor"),
            (("errors",1,"weight"),1),
            (("errors",6,"errorCode"),"approved_action"),
        ]:
            altered=copy.deepcopy(self.rubric)
            node=altered
            for k in path[:-1]:node=node[k]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_rubric(altered)

    def test_source_and_oracle_drift_detected(self):
        report=build_report(self.source,self.oracle,self.submissions,self.rubric)
        altered_source=copy.deepcopy(self.source)
        altered_source["cases"][0]["realFieldEvidence"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(report,altered_source,self.oracle,
                          self.submissions,self.rubric)
        altered_oracle=copy.deepcopy(self.oracle)
        altered_oracle["expectations"][0]["expectedNextQuestionId"] = (
            "escalate_to_engineer_for_review")
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.source,altered_oracle,
                          self.submissions,self.rubric)
        edited=copy.deepcopy(report)
        edited["criticalFindings"]=0
        with self.assertRaises(ReviewRejected):
            verify_report(edited,self.source,self.oracle,self.submissions,self.rubric)

    def test_non_working_html_and_schema_presence(self):
        report=build_report(self.source,self.oracle,self.submissions,self.rubric)
        html=render_html(report)
        self.assertEqual(html.count("<section>"),12)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("NO GO",html)
        root=Path(__file__).resolve().parents[1]/"contracts"
        for name in ("blind-review-packet.schema.json","review-rehearsal-input.schema.json",
                     "review-error-rubric.schema.json","review-rehearsal-report.schema.json"):
            content=json.loads((root/name).read_text(encoding="utf-8"))
            self.assertEqual(content["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(content["additionalProperties"])

if __name__=="__main__":
    unittest.main()
