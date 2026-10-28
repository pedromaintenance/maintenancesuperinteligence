"""Cycle 27 regression and metamorphic checks. No field diagnostic evidence."""
import copy
import json
from pathlib import Path
import unittest

from benchmarks.mechanical_reasoning import (
    CASES_PATH, ORACLE_PATH, DOMAIN_PATHS, FAMILIES,
    ReviewRejected, evaluate, investigate, render_html,
    validate_cases, validate_oracle, verify_report,
)

class MechanicalReasoningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        cls.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))

    def test_all_four_domains_and_24_editorial_expectations(self):
        result = evaluate(self.manifest,self.oracle)
        self.assertEqual(result["caseCount"],24)
        self.assertEqual(result["agreementWithAuthoredOracle"],{"matched":24,"total":24})
        self.assertEqual(set(result["byDomain"]),set(FAMILIES))
        self.assertTrue(all(d=={"total":6,"matched":6} for d in result["byDomain"].values()))
        self.assertFalse(result["diagnosticAccuracyMeasured"])
        self.assertFalse(result["mayClaimDiagnosticValidity"])
        self.assertFalse(result["mayReleaseEquipment"])
        self.assertEqual(result["physicalCausesConfirmed"],0)
        self.assertTrue(verify_report(result,self.manifest,self.oracle))
        for c in result["cases"]:
            self.assertEqual(len(c["openHypotheses"]),3)
            self.assertTrue(c["abstainsFromDiagnosis"])
            self.assertTrue(c["prohibitedOperationalAuthority"])
            self.assertTrue(all(h["probability"] is None for h in c["openHypotheses"]))

    def test_metamorphic_question_changes_on_documentary_context(self):
        for domain in FAMILIES:
            case=next(c for c in self.manifest["cases"] if c["familyId"]==domain
                      and c["scenarioVariant"]=="first_missing")
            info=DOMAIN_PATHS[domain]
            self.assertEqual(investigate(case)["selectedQuestionId"],info["gates"][0][1])
            modified=copy.deepcopy(case)
            modified["contextAvailable"][info["gates"][0][0]]=True
            self.assertEqual(investigate(modified)["selectedQuestionId"],info["gates"][1][1])
            modified["unresolvedContradiction"]=True
            self.assertEqual(investigate(modified)["selectedQuestionId"],"reconcile_conflicting_reports")
            modified["unresolvedContradiction"]=False
            for gate,_,_ in info["gates"]:
                modified["contextAvailable"][gate]=True
            result=investigate(modified)
            self.assertEqual(result["selectedQuestionId"],"escalate_to_engineer_for_review")
            self.assertIsNone(result["confirmedRootCause"])
            self.assertFalse(result["mayRunTests"])

    def test_manifest_rejects_promoted_claims_and_fixture_edits(self):
        changes=[
            (("oemEffectivityVerified",),True),
            (("realFieldEvidence",),True),
            (("reviewedByIndependentMechanicalExpert",),True),
            (("operationallyApproved",),True),
            (("cases",0,"caseId"),"REAL-UNIT"),
            (("cases",0,"unresolvedContradiction"),False),
            (("cases",1,"confirmedRootCause"),"pump_bad"),
            (("cases",2,"mayRunTests"),True),
            (("cases",3,"mayCreateWorkOrder"),True),
            (("cases",4,"mayReleaseEquipment"),True),
            (("cases",5,"contextAvailable","fluid_identity"),False),
            (("cases",12,"fictionalSymptom"),"different symptom"),
        ]
        for path,value in changes:
            fixture=copy.deepcopy(self.manifest)
            node=fixture
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                validate_cases(fixture)

    def test_oracle_rejects_false_review_claims_and_missing_cases(self):
        for path,value in [
            (("independentExpertValidation",),True),
            (("realDiagnosticAccuracyMeasured",),True),
            (("expectations",0,"expectedAbstention"),False),
            (("expectations",1,"expectedOpenHypothesisCount"),0),
            (("expectations",2,"familyId"),"cooling"),
            (("expectations",3,"caseId"),"SIM-MECH-900"),
        ]:
            oracle=copy.deepcopy(self.oracle);node=oracle
            for k in path[:-1]:node=node[k]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_oracle(oracle,validate_cases(self.manifest))

    def test_expectation_mismatch_is_reported_not_hidden(self):
        oracle=copy.deepcopy(self.oracle)
        oracle["expectations"][0]["expectedQuestionId"]="invented_answer"
        result=evaluate(self.manifest,oracle)
        self.assertEqual(result["agreementWithAuthoredOracle"],{"matched":23,"total":24})
        self.assertFalse(result["cases"][0]["agreesWithAuthoredOracle"])
        self.assertFalse(result["mayClaimDiagnosticValidity"])

    def test_altered_report_is_rejected(self):
        r=evaluate(self.manifest,self.oracle)
        for path,value in [
            (("diagnosticAccuracyMeasured",),True),
            (("mayClaimDiagnosticValidity",),True),
            (("physicalCausesConfirmed",),1),
            (("agreementWithAuthoredOracle","matched"),999),
            (("cases",0,"selectedQuestionId"),"replace_component"),
            (("cases",1,"openHypotheses"),[]),
        ]:
            forged=copy.deepcopy(r);node=forged
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                verify_report(forged,self.manifest,self.oracle)

    def test_html_offline_is_non_operational(self):
        html=render_html(evaluate(self.manifest,self.oracle))
        self.assertEqual(html.count("<section>"),24)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("NO GO",html)

    def test_schemas_parse_and_keep_no_go(self):
        root=Path(__file__).resolve().parents[1]/"contracts"
        for name in ("mechanical-reasoning-cases.schema.json",
                     "mechanical-reasoning-oracle.schema.json",
                     "mechanical-reasoning-report.schema.json"):
            obj=json.loads((root/name).read_text(encoding="utf-8"))
            self.assertEqual(obj["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(obj["additionalProperties"],False)

if __name__=="__main__":
    unittest.main()
