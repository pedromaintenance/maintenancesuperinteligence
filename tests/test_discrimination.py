"""Regressões adversariais do seletor: toda observação é SIMULADA."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog, validate_sources
from methods.discrimination import validate_matrix, validate_case, select_questions, main


class DiscriminationTests(unittest.TestCase):
    def setUp(self):
        self.matrix = json.loads((ROOT / "methods/discrimination-matrix.v1.json").read_text())
        sources = json.loads((ROOT / "data/diagnostic-method-sources.v1.json").read_text())
        self.methods = validate_catalog(
            json.loads((ROOT / "methods/catalog.v1.json").read_text()),
            validate_sources(sources))
        self.fmea = {"records": [
            {"id": id, "family": "comando_final", "confirmedRootCause": False}
            for id in ("FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004")
        ]}
        self.cases = {
            key: json.loads((ROOT / f"examples/discrimination_{key}.json").read_text())
            for key in ("777e", "hydraulics", "electronics")
        }

    def selection(self, key):
        return select_questions(self.cases[key], self.matrix, self.methods, self.fmea)

    def reject(self, key="777e"):
        with self.assertRaises(ImportRejected):
            self.selection(key)

    def test_three_families_and_fmea_binding(self):
        f = validate_matrix(self.matrix, self.methods, self.fmea)
        self.assertEqual(set(f), {"final_drive", "hydraulics", "electronics"})
        self.assertEqual(sum(len(x["pairs"]) for x in f.values()), 10)

    def test_final_drive_keeps_all_seven_hypotheses(self):
        result = self.selection("777e")
        self.assertEqual(len(result["hypotheses"]), 7)
        self.assertEqual(len(result["comparisons"]), 4)
        self.assertTrue(all(x["bothRemainOpen"] and x["observedOutcome"] is None
                            for x in result["comparisons"]))
        self.assertEqual(result["selectionRationale"]["selectionStatus"],
                         "ask_missing_context")

    def test_hydraulic_conflict_is_prioritized_before_missing_context(self):
        result = self.selection("hydraulics")
        self.assertEqual(result["selectionRationale"]["selectedPairId"], "HYD-P01")
        self.assertEqual(result["selectionRationale"]["selectionStatus"],
                         "reconcile_contradiction")
        self.assertIn("load_context", result["selectionRationale"]["selectedNextQuestion"])
        self.assertEqual(len(result["hypotheses"]), 4)

    def test_electronics_logged_dtc_does_not_condemn_sensor(self):
        result = self.selection("electronics")
        self.assertEqual(result["selectionRationale"]["selectionStatus"],
                         "ask_missing_context")
        self.assertFalse(result["reportedSignalsAreMeasurements"])
        self.assertTrue(all(x["confirmedRootCause"] is False for x in result["hypotheses"]))
        self.assertIsNone(result["confirmedComponent"])

    def test_every_family_blocks_unsafe_execution(self):
        for key in self.cases:
            with self.subTest(key=key):
                r = self.selection(key)
                self.assertFalse(r["mayRunTests"])
                self.assertFalse(r["mayModifyECM"])
                self.assertFalse(r["mayCreateWorkOrder"])
                self.assertFalse(r["mayReleaseEquipment"])
                self.assertTrue(r["selectionRationale"]["noInformationGainOrCostScores"])
                self.assertTrue(all(c["executionStatus"] == "proposed_not_executed"
                                    and c["status"] == "question_only"
                                    and c["oemApplicability"] == "not_verified"
                                    and not c["mayExecute"]
                                    for c in r["candidateQuestions"]))

    def test_contradicted_is_distinct_from_unknown_and_not_applicable(self):
        r = self.selection("hydraulics")
        states = {x["key"]: x["state"] for p in r["comparisons"]
                  for x in p["discriminatingContext"]}
        self.assertEqual(states["load_context"], "contradicted")
        self.assertEqual(states["hydraulic_schematic"], "unknown")
        self.assertEqual(states["duty_cycle"], "not_applicable")

    def test_not_applicable_does_not_count_as_verified_context(self):
        case = self.cases["hydraulics"]
        case["contextStates"] = [{
            "key": k, "state": "not_applicable", "sourceRef": "SIM-NA"
        } for k in sorted({x for family in self.matrix["families"]
                            if family["familyId"] == "hydraulics"
                            for p in family["pairs"] for x in p["requiredContextKeys"]})]
        r = self.selection("hydraulics")
        self.assertTrue(all(p["status"] == "review_applicability" for p in r["comparisons"]))
        self.assertFalse(r["mayRunTests"])

    def test_complete_simulated_context_is_not_oem_test_approval(self):
        case = self.cases["electronics"]
        case["contextStates"] = [{
            "key": k, "state": "available_simulated", "sourceRef": "SIM-PAPER"
        } for k in sorted({x for family in self.matrix["families"]
                            if family["familyId"] == "electronics"
                            for p in family["pairs"] for x in p["requiredContextKeys"]})]
        r = self.selection("electronics")
        self.assertEqual(r["selectionRationale"]["selectionStatus"],
                         "prepare_human_method_review")
        self.assertFalse(r["mayRunTests"])
        self.assertTrue(all(c["oemApplicability"] == "not_verified"
                            for c in r["candidateQuestions"]))

    def test_reject_false_oem_approval(self):
        self.cases["777e"]["oemGate"]["approved"] = True
        self.reject()

    def test_reject_inserted_field_result(self):
        self.cases["777e"]["confirmedComponent"] = "bearing"
        self.reject()

    def test_reject_real_evidence_claim(self):
        self.cases["777e"]["evidenceNature"] = "real_measurement"
        self.reject()

    def test_reject_circular_hypothesis_pair(self):
        pair = self.matrix["families"][0]["pairs"][0]
        pair["secondHypothesisId"] = pair["firstHypothesisId"]
        self.reject()

    def test_reject_orphan_hypothesis(self):
        self.matrix["families"][0]["pairs"][0]["firstHypothesisId"] = "FAKE-HYPO"
        self.reject()

    def test_reject_missing_ambiguity_outcome(self):
        self.matrix["families"][0]["pairs"][0]["conditionalOutcomes"].pop()
        self.reject()

    def test_reject_outcome_falsely_observed(self):
        self.matrix["families"][0]["pairs"][0]["hasObservedOutcome"] = True
        self.reject()

    def test_reject_method_marked_performed(self):
        self.matrix["families"][1]["pairs"][0]["testStatus"] = "performed"
        self.reject("hydraulics")

    def test_reject_method_from_wrong_discipline(self):
        self.matrix["families"][1]["pairs"][0]["methodIds"][0] = "MET-ECM-CODES"
        self.reject("hydraulics")

    def test_reject_unknown_method(self):
        self.matrix["families"][2]["pairs"][0]["methodIds"][0] = "MET-UNKNOWN"
        self.reject("electronics")

    def test_reject_fmea_source_forgery(self):
        self.matrix["families"][1]["pairs"][0]["sourceRefs"] = ["fmea_public_1.0.0"]
        self.reject("hydraulics")

    def test_reject_fmea_confirmed_roots(self):
        self.fmea["records"][0]["confirmedRootCause"] = True
        self.reject()

    def test_reject_fmea_missing_chain(self):
        self.fmea["records"].pop()
        self.reject()

    def test_reject_duplicate_context_key(self):
        self.cases["777e"]["contextStates"].append(
            copy.deepcopy(self.cases["777e"]["contextStates"][0]))
        self.reject()

    def test_reject_unknown_context_with_fake_source(self):
        self.cases["electronics"]["contextStates"][0]["sourceRef"] = "SIM-MEASURED"
        self.reject("electronics")

    def test_reject_non_simulated_source_for_context(self):
        self.cases["hydraulics"]["contextStates"][1]["sourceRef"] = "SAP-PR-1234"
        self.reject("hydraulics")

    def test_reject_probability_weight(self):
        self.matrix["families"][0]["pairs"][0]["likelihoodRatio"] = 4.5
        self.reject()

    def test_reject_false_condition_certain_failure(self):
        self.matrix["families"][0]["hypotheses"][0]["nature"] = "confirmed_fault"
        self.reject()

    def test_reject_numeric_oem_limits(self):
        self.matrix["families"][1]["pairs"][0]["pressureLimit"] = 120
        self.reject("hydraulics")

    def test_reject_case_invalid_reported_signal_type(self):
        self.cases["electronics"]["reportedSignals"] = [123]
        self.reject("electronics")

    def test_reject_corrupt_snapshot_in_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            sample = p / "snapshot.json"
            sample.write_text('{"fake":true}')
            with patch("sys.stderr"):
                status = main(["--snapshot", str(sample),
                               "--case", str(ROOT / "examples/discrimination_777e.json")])
            self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
