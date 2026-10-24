"""Adversarial casefile tests; no real FMEA snapshot/network in unittest."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT
from casefiles.integrated import (ALLOWED, CONTEXT, assemble_case, build_collection,
                                  load_dependencies, render_html, validate_fixture,
                                  verify_report)


class IntegratedCasefileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = {"records": [
            {"id": x, "family": "comando_final", "confirmedRootCause": False}
            for x in ("FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004")
        ]}
        cls.deps = load_dependencies(cls.snapshot)

    def setUp(self):
        self.packet = json.loads(
            (ROOT / "casefiles/technical-cases.v1.json").read_text())

    def build(self):
        return build_collection(self.packet, self.deps, self.snapshot)

    def mock_pilot(self):
        source = json.loads((ROOT / "examples/777e_additives_only.json").read_text())
        return {
            "caseId": source["caseId"],
            "confirmedRootCause": None,
            "mayReleaseEquipment": False,
            "mayCreateWorkOrder": False,
            "hypotheses": [{"id":x["hypothesisId"]}
                            for x in self.deps["families"]["final_drive"]["hypotheses"]],
            "plannedInvestigations": [{"status":"not_performed"} for _ in range(8)],
            "decision": "needs_evidence",
            "observations": [{"code":s["code"],"result":s["result"]}
                             for s in source["signals"]],
            "conflicts": [],
            "knowledgeGaps": ["Histórico de formulação e coleta não apresentado."]
        }

    def build_mock(self):
        with patch("casefiles.integrated.build_consumer_index",
                   return_value={"synthetic": True}):
            with patch("casefiles.integrated.investigate",
                       return_value=self.mock_pilot()):
                return self.build()

    def rejects(self, part=None):
        with self.assertRaises(ImportRejected) as error:
            validate_fixture(self.packet)
        if part:
            self.assertIn(part, str(error.exception))

    def test_exact_four_cases_three_families(self):
        fixtures = validate_fixture(self.packet)
        self.assertEqual(len(fixtures), 4)
        self.assertEqual({v["familyId"] for v in fixtures.values()},
                         {"final_drive", "hydraulics", "electronics"})

    def test_casefile_all_opens_and_governance_denies(self):
        r = self.build_mock()
        self.assertEqual(r["caseCount"], 4)
        self.assertEqual(r["hypothesesOpen"], 19)
        self.assertEqual(r["testsExecuted"], 0)
        self.assertEqual(r["confirmedRootCauses"], 0)
        self.assertFalse(r["privateDeploymentApproved"])
        self.assertFalse(r["mayCreateWorkOrder"])
        self.assertFalse(r["mayReleaseEquipment"])
        self.assertTrue(all(len(c["hypotheses"]) >= 4 for c in r["cases"]))
        self.assertTrue(all(c["decision"] ==
                            "needs_human_review_and_discriminating_evidence"
                            for c in r["cases"]))

    def test_three_domains_have_plausible_causal_ladders_not_root_causes(self):
        for c in self.build_mock()["cases"]:
            with self.subTest(case=c["caseFileId"]):
                self.assertTrue(c["assetContext"]["function"])
                self.assertTrue(c["assetContext"]["requirement"])
                self.assertTrue(c["causalLevels"]["immediateMechanismsAreHypothetical"])
                self.assertTrue(c["causalLevels"]["rootCauseInterpretation"])
                self.assertFalse(c["causalLevels"]["rootCauseEstablished"])
                self.assertIsNone(c["operationalRisk"]["quantifiedRisk"])
                self.assertFalse(c["operationalRisk"]["operationAllowed"])
                self.assertFalse(c["reviewGates"]["technicalReviewAuthenticated"])

    def test_oil_adverse_formulation_competes_with_wear(self):
        c = self.build_mock()["cases"][0]
        self.assertEqual(c["familyId"], "final_drive")
        self.assertEqual(c["selectedQuestion"]["pairId"], "FD-P01")
        ids = {h["id"] for h in c["hypotheses"]}
        self.assertTrue({"PILOT-FORMULATION", "FC-FD-003",
                         "PILOT-SAMPLE", "FC-FD-002"}.issubset(ids))
        self.assertEqual(c["pilot"]["sourceCaseId"], "SIM-777E-ADDITIVES-ONLY")
        self.assertFalse(c["pilot"]["rootCauseConfirmed"])
        self.assertTrue(all(x["status"] == "not_performed"
                            for x in c["pilot"]["plannedInvestigations"]))

    def test_hydraulic_load_conflict_is_not_pump_condemnation(self):
        c = self.build_mock()["cases"][1]
        self.assertEqual(c["familyId"], "hydraulics")
        self.assertEqual(c["selectedQuestion"]["status"], "reconcile_contradiction")
        self.assertIn("load_context", c["selectedQuestion"]["blockingQuestion"])
        self.assertIn("HYD-PUMP", {h["id"] for h in c["hypotheses"]})
        self.assertIsNone(c["confirmedComponent"])
        self.assertTrue(any(x["state"]=="contradicted" for x in c["simulatedContext"]))

    def test_stored_versus_active_dtc_are_explicitly_distinct(self):
        x = self.build_mock()["cases"]
        logged, active = x[2], x[3]
        self.assertEqual(logged["reportedSignals"][0]["value"], "generic_logged_dtc")
        self.assertEqual(active["reportedSignals"][0]["value"], "generic_active_dtc")
        self.assertEqual(logged["selectedQuestion"]["pairId"], "EL-P01")
        self.assertEqual(active["selectedQuestion"]["pairId"], "EL-P02")
        self.assertEqual({h["id"] for h in logged["hypotheses"]},
                         {h["id"] for h in active["hypotheses"]})
        for c in (logged, active):
            self.assertFalse(c["reviewGates"]["mayModifyECM"])
            self.assertFalse(c["reviewGates"]["oemSeriesVerified"])

    def test_sources_only_refer_general_manufacturer_material(self):
        for case in self.build_mock()["cases"]:
            for ref in case["technicalReferences"]:
                self.assertEqual(ref["scope"],"general_reference_not_series_effectivity")
                self.assertTrue(ref["url"].startswith("https://"))
                self.assertTrue(ref["limitation"])

    def test_no_test_methods_are_executable(self):
        for case in self.build_mock()["cases"]:
            self.assertTrue(all(m["mayExecute"] is False
                                and m["executionStatus"] == "proposed_not_executed"
                                and m["safetyPrerequisites"]
                                for m in case["methods"]))

    def test_benchmark_and_governance_are_attached_not_inferred(self):
        report = self.build_mock()
        self.assertEqual(self.deps["checks"]["fixturesPassed"], 15)
        self.assertTrue(all(c["reviewGates"]["benchmarkSyntheticRegressionsPass"]
                            and not c["reviewGates"]["benchmarkMeasuredFieldAccuracy"]
                            for c in report["cases"]))
        self.assertTrue(all(c["provenance"]["reviewDossierSourceSha256"]
                            == self.deps["gate"]["dossierFixtureSha256"]
                            for c in report["cases"]))

    def test_deterministic_assembly_and_html_without_script(self):
        with patch("casefiles.integrated.build_consumer_index",return_value={}):
            with patch("casefiles.integrated.investigate",
                       return_value=self.mock_pilot()):
                a = self.build()
                b = self.build()
                self.assertEqual(a,b)
                self.assertEqual(verify_report(a,self.packet,self.deps,self.snapshot),a)
        html = render_html(a)
        self.assertEqual(html.count("<section>"),4)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("Content-Security-Policy",html)
        self.assertIn("SIMULAÇÃO",html)

    def test_output_forged_root_cause_rejected_by_report_verifier(self):
        orig = self.build_mock()
        changed = copy.deepcopy(orig)
        changed["cases"][0]["causalLevels"]["rootCauseEstablished"] = True
        with patch("casefiles.integrated.build_consumer_index",return_value={}):
            with patch("casefiles.integrated.investigate",
                       return_value=self.mock_pilot()):
                with self.assertRaises(ImportRejected):
                    verify_report(changed,self.packet,self.deps,self.snapshot)

    def test_html_rejects_forged_equipment_release(self):
        modified=self.build_mock()
        modified["cases"][0]["reviewGates"]["mayReleaseEquipment"]=True
        with self.assertRaises(ImportRejected):
            render_html(modified)

    def test_html_rejects_probability_fabrication(self):
        modified=self.build_mock()
        modified["cases"][1]["hypotheses"][0]["probability"]=0.92
        with self.assertRaises(ImportRejected):
            render_html(modified)

    def test_html_rejects_forged_executed_test(self):
        modified=self.build_mock()
        modified["cases"][2]["methods"][0]["executionStatus"]="completed_in_field"
        with self.assertRaises(ImportRejected):
            render_html(modified)

    def test_html_rejects_new_case_without_review(self):
        modified=self.build_mock()
        modified["cases"].append(copy.deepcopy(modified["cases"][0]))
        with self.assertRaises(ImportRejected):
            render_html(modified)

    def test_extra_input_field_with_sap_command_rejected(self):
        self.packet["cases"][0]["sapCommand"] = "open_order"
        self.rejects("unknown or missing contract field")

    def test_false_confirmed_mechanical_root_cause_input_rejected(self):
        self.packet["cases"][0]["rootCauseConfirmed"]=True
        self.rejects("real data, field scores")

    def test_false_test_performed_input_rejected(self):
        self.packet["cases"][0]["testPerformed"]=True
        self.rejects("real data, field scores")

    def test_fake_oem_effectivity_rejected(self):
        self.packet["cases"][0]["oemEffectivityVerified"]=True
        self.rejects("real data, field scores")

    def test_oem_numeric_pressure_limit_rejected(self):
        self.packet["cases"][1]["oemPressureOrWearLimit"]=3500
        self.rejects("real data, field scores")

    def test_probabilistic_risk_score_rejected(self):
        self.packet["cases"][1]["fieldRiskScore"]=0.93
        self.rejects("real data, field scores")

    def test_real_machine_identifier_rejected(self):
        self.packet["cases"][0]["realMachineIdentifier"]="777-001"
        self.rejects("real data, field scores")

    def test_real_data_flag_rejected(self):
        self.packet["cases"][1]["evidenceNature"]="real_field"
        self.rejects("real data, field scores")

    def test_external_pilot_path_rejected(self):
        self.packet["cases"][0]["pilotCasePath"]="../../corporate.json"
        self.rejects("changed technical context")

    def test_cross_case_benchmark_swap_rejected(self):
        self.packet["cases"][2]["benchmarkFixtureId"]="ECM-ACTIVE-CONTEXT-MISSING"
        self.rejects("changed technical context")

    def test_case_family_swap_rejected(self):
        self.packet["cases"][3]["familyId"]="hydraulics"
        self.rejects("changed technical context")

    def test_duplicate_case_rejected(self):
        self.packet["cases"][3]["caseFileId"]="SIM-TECH-FD-01"
        self.rejects("changed technical context")

    def test_missing_case_rejected(self):
        self.packet["cases"].pop()
        self.rejects("all four anchored")

    def test_fictitious_review_cannot_be_promoted_to_human(self):
        self.packet["cases"][3]["independentHumanReviewComplete"]=True
        self.rejects("real data, field scores")

    def test_fake_order_approval_rejected(self):
        self.packet["cases"][0]["mayCreateWorkOrder"]=True
        self.rejects("real data, field scores")

    def test_false_ecm_permission_rejected(self):
        self.packet["cases"][3]["mayModifyECM"]=True
        self.rejects("real data, field scores")

    def test_false_release_rejected(self):
        self.packet["cases"][0]["mayReleaseEquipment"]=True
        self.rejects("real data, field scores")

    def test_unrecognized_contract_version_rejected(self):
        self.packet["version"]="1.8.0"
        self.rejects("foreign corpus, contract")

    def test_unrecognized_benchmark_source_rejected(self):
        self.packet["sourceBenchmark"]="data/private-oil.xlsx"
        self.rejects("foreign corpus, contract")

    def test_no_observed_patterns_in_differential_pairs(self):
        for case in self.build_mock()["cases"]:
            self.assertTrue(all(pair["observedOutcome"] is None
                                and pair["bothRemainOpen"] is True
                                for pair in case["hypothesisComparisons"]))
            self.assertIsNone(case["confirmedComponent"])


if __name__ == "__main__":
    unittest.main()
