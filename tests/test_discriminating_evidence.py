"""Cycle 34 — qualitative counterfactuals cannot become confirmed repair decisions."""
import copy
import json
import unittest

from knowledge.discriminating_evidence import (
    ROOT, MATRIX, POLICY, SCENARIOS, MAP_PATH, MECHANICAL_POLICY,
    evaluate,validate_policy,validate_matrix,validate_scenarios,
    verify_report,render_html,judge_case,POSITIONS,
)
from pilot.change_review_packets import ReviewRejected


class DiscriminatingEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix=json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.parent=json.loads(MAP_PATH.read_text(encoding="utf-8"))
        cls.mpolicy=json.loads(MECHANICAL_POLICY.read_text(encoding="utf-8"))
        cls.policy=json.loads(POLICY.read_text(encoding="utf-8"))
        cls.fixtures=json.loads(SCENARIOS.read_text(encoding="utf-8"))

    def result(self,matrix=None,parent=None,mpolicy=None,policy=None,fixtures=None):
        return evaluate(matrix or self.matrix,parent or self.parent,
                        mpolicy or self.mpolicy,policy or self.policy,
                        fixtures or self.fixtures)

    def test_36_qualitative_conditions_and_48_simulated_paths(self):
        report=self.result()
        self.assertTrue(verify_report(report,self.matrix,self.parent,self.mpolicy,
                                      self.policy,self.fixtures))
        self.assertEqual(report["ruleCount"],36)
        self.assertEqual(report["parentHypothesisCount"],12)
        self.assertEqual(report["ruleOutcomes"],{
            "supports_relative_hypothesis":12,
            "weakens_relative_hypothesis":12,"indeterminate":12})
        self.assertEqual(report["fictionalScenarioCount"],48)
        self.assertEqual(report["scenarioStateCounts"],
                         {kind:12 for kind in POSITIONS})
        self.assertEqual(report["physicalObservationsVerified"],0)
        self.assertEqual(report["causesConfirmed"],0)
        self.assertEqual(report["testsExecuted"],0)
        self.assertFalse(report["independentExpertValidationCompleted"])
        self.assertFalse(report["realWorldDiagnosticAccuracyMeasured"])
        self.assertFalse(report["mayExecuteTests"])
        self.assertFalse(report["mayCreateWorkOrder"])
        self.assertFalse(report["mayReleaseEquipment"])
        self.assertEqual(report["decision"],"editorial_discrimination_demo_only_no_go")
        for case in report["scenarios"]:
            self.assertEqual(case["hypothesisStatus"],"open_unconfirmed")
            self.assertEqual(case["observedEvidenceCount"],0)
            self.assertFalse(case["rootCauseConfirmed"])
            self.assertFalse(case["oemSerialEffectivityVerified"])
            self.assertFalse(case["mayExecuteTests"])

    def test_conflicting_support_and_weakening_remain_unresolved(self):
        report=self.result()
        for i in range(12):
            cases=report["scenarios"][i*4:i*4+4]
            self.assertEqual([x["qualitativeState"] for x in cases],
                             [POSITIONS[k] for k in POSITIONS])
            self.assertFalse(cases[0]["requiresHumanReconciliation"])
            self.assertFalse(cases[1]["requiresHumanReconciliation"])
            self.assertTrue(cases[2]["requiresHumanReconciliation"])
            self.assertTrue(cases[3]["requiresHumanReconciliation"])
            self.assertEqual(len(cases[2]["assumedRuleIds"]),2)
            self.assertTrue(all(x["rootCauseConfirmed"] is False for x in cases))

    def test_counterfactual_flips_direction_without_causal_confirmation(self):
        rules=validate_matrix(self.matrix,self.parent,self.mpolicy,self.policy)
        p={x["recordId"]:x for x in self.parent["records"]}
        case=copy.deepcopy(self.fixtures["cases"][0])
        self.assertEqual(judge_case(case,rules,p)["qualitativeState"],
                         POSITIONS["support_only"])
        case["assumedRuleIds"]=["DISC-001-2"]
        x=judge_case(case,rules,p)
        self.assertEqual(x["qualitativeState"],POSITIONS["weaken_only"])
        self.assertFalse(x["rootCauseConfirmed"])
        case["assumedRuleIds"]=["DISC-001-1","DISC-001-2"]
        x=judge_case(case,rules,p)
        self.assertEqual(x["qualitativeState"],POSITIONS["conflict"])
        self.assertTrue(x["requiresHumanReconciliation"])

    def test_mechanism_and_interpretation_confounder_never_change_identity(self):
        report=self.result()
        self.assertEqual(report["scenarios"][0]["parentBranchType"],
                         "interpretation_confounder")
        self.assertEqual(report["scenarios"][4]["parentBranchType"],
                         "physical_mechanism_candidate")
        self.assertEqual(report["scenarios"][24]["parentBranchType"],
                         "interpretation_confounder")
        self.assertEqual(report["scenarios"][32]["parentBranchType"],
                         "interpretation_confounder")

    def test_reject_fabricated_field_measurements_and_work_orders(self):
        for key in ("fieldSourceAvailable","measurementConfirmed",
                    "oemSerialEffectivityConfirmed","rootCauseConfirmed",
                    "independentReviewerApproved","mayExecuteTest",
                    "mayCreateWorkOrder","mayReleaseEquipment"):
            matrix=copy.deepcopy(self.matrix)
            matrix["rules"][0][key]=True
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_matrix(matrix,self.parent,self.mpolicy,self.policy)
        for key in ("realObservationsPresent","expertReviewed","operationalAuthority"):
            matrix=copy.deepcopy(self.matrix)
            matrix[key]=True
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_matrix(matrix,self.parent,self.mpolicy,self.policy)

    def test_directional_rule_and_parent_reference_cannot_be_changed(self):
        for key,value in (
            ("parentRecordId","MECH-KB-002"),
            ("outcome","physical_damage_confirmed"),
            ("ruleId","DISC-009-1"),
            ("evidenceStatus","measured_field_observation"),
            ("hypotheticalObservation","Rolamento danificado confirmado"),
        ):
            m=copy.deepcopy(self.matrix)
            m["rules"][0][key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_matrix(m,self.parent,self.mpolicy,self.policy)
        m=copy.deepcopy(self.matrix)
        m["rules"]=m["rules"][:-1]
        with self.assertRaises(ReviewRejected):
            validate_matrix(m,self.parent,self.mpolicy,self.policy)

    def test_reject_out_of_domain_or_forged_fixtures(self):
        rulemap=validate_matrix(self.matrix,self.parent,self.mpolicy,self.policy)
        for key,value in (
            ("parentRecordId","MECH-KB-777"),
            ("scenarioId","SIM-DISC-777-1"),
            ("assumedRuleIds",["DISC-001-2"]),
            ("fieldObservationVerified",True),
            ("rootCauseConfirmed",True),
            ("mayAuthorizeAction",True),
            ("independentReviewPerformed",True),
            ("sourceNature","field_confirmed"),
        ):
            fixture=copy.deepcopy(self.fixtures)
            fixture["cases"][0][key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_scenarios(fixture,rulemap)

    def test_source_change_invalidates_report_and_policy_cannot_approve(self):
        report=self.result()
        altered=copy.deepcopy(self.parent)
        altered["records"][0]["supportNote"]+=" Atualização editorial."
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.matrix,altered,self.mpolicy,
                          self.policy,self.fixtures)
        for key in ("independentExpertValidated","causalInferenceAuthorized",
                    "mayExecuteTests","mayCreateWorkOrder","mayReleaseEquipment"):
            pol=copy.deepcopy(self.policy)
            pol[key]=True
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_policy(pol)
        altered=copy.deepcopy(report)
        altered["causesConfirmed"]=1
        with self.assertRaises(ReviewRejected):
            verify_report(altered,self.matrix,self.parent,self.mpolicy,
                          self.policy,self.fixtures)

    def test_offline_html_is_non_interactive_and_escapes_literal_input(self):
        report=self.result()
        html=render_html(report,self.matrix,self.parent,self.mpolicy,
                         self.policy,self.fixtures)
        self.assertEqual(html.count("<section>"),12)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("NO GO",html)
        self.assertIn("Nenhum dado de máquina",html)
        evil=copy.deepcopy(self.matrix)
        evil["rules"][0]["hypotheticalObservation"]+=" <script>alert(1)</script>"
        revised=self.result(matrix=evil)
        safe=render_html(revised,evil,self.parent,self.mpolicy,
                         self.policy,self.fixtures)
        self.assertNotIn("<script>",safe)
        self.assertIn("&lt;script&gt;",safe)

    def test_schema_contracts(self):
        for name in (
            "discriminating-evidence-matrix.schema.json",
            "discrimination-scenarios.schema.json",
            "discrimination-policy.schema.json",
            "discrimination-report.schema.json",
        ):
            obj=json.loads((ROOT/"contracts"/name).read_text(encoding="utf-8"))
            self.assertEqual(obj["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(obj["additionalProperties"])


if __name__=="__main__":
    unittest.main()
