"""Cycle 28: out-of-template generalization and provenance defenses."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
from benchmarks.generalization_stress import (
    CASES, ORACLE, DENIED, FAMILIES, validate_challenges, validate_oracle,
    assess_challenge, evaluate, verify_report, render_html
)
from pilot.change_review_packets import ReviewRejected

class Cycle28StressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(CASES.read_text(encoding="utf-8"))
        cls.oracle=json.loads(ORACLE.read_text(encoding="utf-8"))

    def test_34_novel_cases_baseline_regression_and_gated_comparison(self):
        result=evaluate(self.manifest,self.oracle)
        self.assertEqual(result["caseCount"],34)
        self.assertEqual(result["supportedDomainCases"],32)
        self.assertEqual(result["unknownDomainCases"],2)
        self.assertEqual(result["baselineEditorialAgreement"],{"matched":16,"total":32})
        self.assertEqual(result["qualityGatedEditorialAgreement"],{"matched":34,"total":34})
        self.assertTrue(verify_report(result,self.manifest,self.oracle))
        self.assertFalse(result["realWorldDiagnosticAccuracyMeasured"])
        self.assertFalse(result["independentExpertEvaluationCompleted"])
        self.assertEqual(result["causesConfirmed"],0)
        self.assertEqual(result["testsExecuted"],0)
        self.assertFalse(result["mayClaimDiagnosticValidation"])
        for c in result["cases"]:
            self.assertTrue(c["allHypothesesOpen"])
            self.assertFalse(c["rootCauseConfirmed"])
            self.assertFalse(c["measurementsPerformed"])
            self.assertFalse(c["oemApplicabilityVerified"])
            self.assertFalse(c["realEngineeringReview"])
            self.assertFalse(any(c["operationalAuthority"].values()))
        self.assertTrue(all(c["hypothesisCount"]==3
                            for c in result["cases"][:32]))
        self.assertTrue(all(c["hypothesisCount"]==0
                            for c in result["cases"][32:]))

    def test_metamorphic_quality_order_does_not_override_safe_abstention(self):
        case=next(c for c in self.manifest["cases"]
                  if c["challengeKind"]=="complete_context")
        previous=assess_challenge(case)
        self.assertEqual(previous["gatedQuestionId"],"escalate_to_engineer_for_review")
        for status,expected in [
            ("unverified","verify_source_provenance"),
            ("contradictory","reconcile_source_conflict"),
            ("stale","revalidate_documentary_evidence"),
            ("revoked","revalidate_documentary_evidence"),
        ]:
            modified=copy.deepcopy(case)
            modified["sourceStatus"]=status
            outcome=assess_challenge(modified)
            self.assertEqual(outcome["baselineQuestionId"],previous["baselineQuestionId"])
            self.assertEqual(outcome["gatedQuestionId"],expected)
            self.assertTrue(all(h["status"]=="open_not_confirmed"
                                for h in outcome["openHypotheses"]))

    def test_unknown_system_abstains_without_crash_or_component_guess(self):
        for c in self.manifest["cases"][32:]:
            out=assess_challenge(c)
            self.assertEqual(out["gatedQuestionId"],"escalate_unsupported_domain")
            self.assertIsNone(out["baselineQuestionId"])
            self.assertEqual(out["openHypotheses"],[])

    def test_reject_tampered_cases_and_authority_claims(self):
        changes=[
            (("realFieldEvidence",),True),
            (("externalExpertValidation",),True),
            (("operationallyApproved",),True),
            (("cases",0,"caseId"),"FIELD-001"),
            (("cases",0,"contextAvailable","fluid_identity"),True),
            (("cases",1,"sourceStatus"),"verified_oem"),
            (("cases",2,"unresolvedNarrativeConflict"),False),
            (("cases",3,"confirmedRootCause"),"damaged_pump"),
            (("cases",4,"mayExecuteTests"),True),
            (("cases",5,"mayCreateWorkOrder"),True),
            (("cases",6,"mayReleaseEquipment"),True),
            (("cases",7,"oemEffectivityVerified"),True),
            (("cases",33,"familyId"),"final_drive"),
        ]
        for path,value in changes:
            altered=copy.deepcopy(self.manifest)
            node=altered
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_challenges(altered)

    def test_mutated_oracle_is_not_silently_changed_back(self):
        cases=validate_challenges(self.manifest)
        for path,value in [
            (("independentExpertValidation",),True),
            (("diagnosticAccuracyMeasured",),True),
            (("expectations",0,"caseId"),"SIM-GEN-700"),
            (("expectations",0,"expectedAbstention"),False),
            (("expectations",1,"expectedOperationalAuthority"),True),
        ]:
            changed=copy.deepcopy(self.oracle)
            node=changed
            for k in path[:-1]:node=node[k]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_oracle(changed,cases)
        changed=copy.deepcopy(self.oracle)
        changed["expectations"][0]["expectedNextQuestionId"]="verify_source_provenance"
        result=evaluate(self.manifest,changed)
        self.assertEqual(result["qualityGatedEditorialAgreement"],{"matched":33,"total":34})

    def test_forged_results_are_rejected(self):
        report=evaluate(self.manifest,self.oracle)
        for path,value in [
            (("realWorldDiagnosticAccuracyMeasured",),True),
            (("mayReleaseEquipment",),True),
            (("cases",3,"rootCauseConfirmed"),True),
            (("cases",4,"operationalAuthority","mayCreateWorkOrder"),True),
            (("qualityGatedEditorialAgreement","matched"),999),
            (("cases",5,"gatedQuestionId"),"replace_sensor"),
        ]:
            changed=copy.deepcopy(report)
            node=changed
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                verify_report(changed,self.manifest,self.oracle)

    def test_html_static_and_schema_contracts(self):
        html=render_html(evaluate(self.manifest,self.oracle))
        self.assertEqual(html.count("<section>"),34)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        root=Path(__file__).resolve().parents[1]/"contracts"
        for name in ("generalization-challenges.schema.json",
                     "generalization-expectations.schema.json",
                     "generalization-report.schema.json"):
            schema=json.loads((root/name).read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])

if __name__=="__main__":
    unittest.main()
