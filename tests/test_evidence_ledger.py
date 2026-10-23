"""Ciclo 04: evidência sintética, proveniência, ensaios e auditoria."""
import copy
import json
from pathlib import Path
import unittest

from connectors.fmea_public import ImportRejected
from evidence.ledger import build_ledger, validate_ledger, _seal
from investigations.final_drive import investigate
from tests.test_final_drive import case_template, mocked_index, present

ROOT = Path(__file__).resolve().parent.parent


class EvidenceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.case = case_template()
        self.index = mocked_index()
        self.result = investigate(self.case, self.index)
        self.ledger = self.result["evidenceLedger"]

    def rebuild(self):
        self.result = investigate(self.case, self.index)
        self.ledger = self.result["evidenceLedger"]

    def validate(self):
        return validate_ledger(self.ledger, case=self.case, investigation=self.result)

    def rejects(self, message=""):
        with self.assertRaises(ImportRejected) as err:
            self.validate()
        if message:
            self.assertIn(message, str(err.exception))

    def reseal(self):
        self.ledger["auditTrail"] = _seal(self.ledger)

    def test_prior_cases_still_return_v2_with_ledger(self):
        self.assertEqual(self.result["schema"],
                         "maintenance-superinteligence.final-drive-investigation.v2")
        self.assertEqual(self.ledger["schema"], "maintenance-superinteligence.evidence-ledger.v1")
        self.assertEqual(self.ledger["testResults"], [])
        self.validate()

    def test_report_is_not_a_measurement(self):
        first = self.ledger["observations"][0]
        self.assertEqual(first["kind"], "operator_report")
        self.assertEqual(first["result"], "reported")
        self.assertIsNone(first["context"]["observedAt"])
        self.assertIsNone(first["signalCode"])
        self.assertEqual(self.result["confirmedRootCause"], None)

    def test_source_methods_remain_proposed(self):
        self.assertEqual(len(self.ledger["testMethods"]), 8)
        self.assertTrue(all(m["status"] == "proposed_not_executed"
                            for m in self.ledger["testMethods"]))
        self.assertEqual(self.ledger["humanReview"]["status"], "pending")

    def test_additive_change_is_non_discriminating(self):
        self.case["signals"] = [present("additive_profile_changed")]
        self.rebuild()
        evidence = self.ledger["evidence"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["relation"], "not_discriminating")
        self.assertIsNone(evidence[0]["hypothesisId"])
        self.assertTrue(all(a["confidence"] is None for a in
                            self.ledger["hypothesisAssessments"]))
        self.validate()

    def test_documented_oil_change_keeps_alternative_open(self):
        self.case["signals"] = [
            present("additive_profile_changed"),
            present("lubricant_change_documented", 2)]
        self.rebuild()
        formulation = next(a for a in self.ledger["hypothesisAssessments"]
                           if a["hypothesisId"] == "PILOT-FORMULATION")
        self.assertEqual(len(formulation["evidenceIds"]), 1)
        self.assertFalse(formulation["rootCauseConfirmed"])
        self.validate()

    def test_conflicting_water_retains_both_bases(self):
        self.case["signals"] = [
            present("water_retest_confirmed"),
            present("water_retest_not_reproduced", 2)]
        self.rebuild()
        h = next(a for a in self.ledger["hypothesisAssessments"]
                 if a["hypothesisId"] == "FC-FD-002")
        self.assertEqual(h["disposition"], "mixed_evidence_open_not_confirmed")
        self.assertEqual(len(h["evidenceIds"]), 2)
        self.assertFalse(h["rootCauseConfirmed"])
        self.validate()

    def test_every_existing_fixture_has_traceable_record(self):
        for name in ("777e_additives_only", "777e_change_documented",
                     "777e_water_disputed", "777e_debris_and_noise"):
            with self.subTest(fixture=name):
                case = json.loads((ROOT / "examples" / f"{name}.json").read_text())
                report = investigate(case, self.index)
                ledger = report["evidenceLedger"]
                self.assertEqual(len(ledger["observations"]),
                                 len(case["signals"]) + 1)
                self.assertEqual(len(ledger["testMethods"]), 8)
                self.assertEqual(len(ledger["auditTrail"]), 6)
                self.assertTrue(all(a["confidence"] is None for a in
                                    ledger["hypothesisAssessments"]))
                self.assertFalse(ledger["humanReview"]["operationalReleaseAuthorized"])
                validate_ledger(ledger, case=case, investigation=report)

    def test_synthetic_test_result_is_a_separate_object(self):
        case = json.loads((ROOT / "examples/777e_water_disputed.json").read_text())
        packet = json.loads((ROOT / "examples/777e_simulated_test_results.json").read_text())
        result = investigate(case, self.index, simulated_test_results=packet["results"])
        ledger = result["evidenceLedger"]
        self.assertEqual(len(ledger["testResults"]), 1)
        self.assertEqual(ledger["testResults"][0]["status"], "simulated_execution")
        self.assertEqual(ledger["testMethods"][2]["status"], "proposed_not_executed")
        self.assertFalse(ledger["humanReview"]["oemApplicabilityVerified"])
        self.assertEqual(result["decision"], "escalate_to_specialist")
        self.assertIsNone(result["confirmedRootCause"])
        validate_ledger(ledger, case=case, investigation=result)

    def test_test_result_cannot_claim_field_execution(self):
        self.case["signals"] = [present("water_retest_confirmed")]
        packet = json.loads((ROOT / "examples/777e_simulated_test_results.json").read_text())
        self.ledger = build_ledger(self.case, investigate(self.case, self.index),
                                   packet["results"])
        self.result = investigate(self.case, self.index)
        self.ledger["testResults"][0]["nature"] = "empirical_authorised"
        self.reseal()
        self.rejects("real execution or result not allowed")

    def test_simulated_result_needs_measurement_context(self):
        self.case["signals"] = [present("water_retest_confirmed")]
        packet = json.loads((ROOT / "examples/777e_simulated_test_results.json").read_text())
        self.ledger = build_ledger(self.case, investigate(self.case, self.index),
                                   packet["results"])
        self.result = investigate(self.case, self.index)
        self.ledger["testResults"][0]["context"]["instrumentId"] = None
        self.reseal()
        self.rejects("full measurement context")

    def test_test_result_cannot_reference_unknown_method(self):
        packet = json.loads((ROOT / "examples/777e_simulated_test_results.json").read_text())
        self.ledger = build_ledger(self.case, self.result, packet["results"])
        self.ledger["testResults"][0]["testMethodId"] = "TM-999"
        self.reseal()
        self.rejects("orphan method")

    def test_duplicate_test_result_rejected(self):
        packet = json.loads((ROOT / "examples/777e_simulated_test_results.json").read_text())
        self.ledger = build_ledger(self.case, self.result, packet["results"])
        self.ledger["testResults"].append(copy.deepcopy(self.ledger["testResults"][0]))
        self.reseal()
        self.rejects("duplicate IDs")

    def test_mutating_observation_detected_without_resealing(self):
        self.ledger["observations"][0]["description"] = "Forged interpretation"
        self.rejects("operator report provenance drift")

    def test_case_digest_detects_modified_original(self):
        self.case["complaint"] = "different source complaint"
        self.rejects("input case was mutated")

    def test_false_oem_approval_cannot_be_resealed(self):
        self.ledger["humanReview"]["oemApplicabilityVerified"] = True
        self.reseal()
        self.rejects("false human/OEM/operational approval")

    def test_cannot_add_numeric_confidence(self):
        self.ledger["hypothesisAssessments"][0]["confidence"] = 0.99
        self.reseal()
        self.rejects("falsely confirmed/scored")

    def test_cannot_confirm_root_cause(self):
        self.ledger["hypothesisAssessments"][0]["rootCauseConfirmed"] = True
        self.reseal()
        self.rejects("falsely confirmed/scored")

    def test_cannot_mark_source_method_executed(self):
        self.ledger["testMethods"][0]["status"] = "performed"
        self.reseal()
        self.rejects("falsely marked performed")

    def test_cannot_inject_real_source(self):
        self.ledger["observations"][0]["sourceRef"] = "SAP-PM-REAL"
        self.reseal()
        self.rejects("real or unsupported origin")

    def test_extra_unknown_observation_field_fails(self):
        self.ledger["observations"][0]["torqueOEM"] = 5000
        self.reseal()
        self.rejects("expected exact fields")

    def test_evidence_cannot_reference_missing_observation(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        self.ledger["evidence"][0]["observationId"] = "OBS-999"
        self.reseal()
        self.rejects("orphan observation")

    def test_evidence_cannot_have_dual_source(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        self.ledger["evidence"][0]["testResultId"] = "SIM-TR-999"
        self.reseal()
        self.rejects("exactly one origin")

    def test_evidence_cannot_reference_itself(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        self.ledger["evidence"][0]["observationId"] = "EVD-001"
        self.reseal()
        self.rejects("orphan observation")

    def test_cross_hypothesis_evidence_link_is_blocked(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        first = next(a for a in self.ledger["hypothesisAssessments"]
                     if a["hypothesisId"] == "FC-FD-001")
        target = next(a for a in self.ledger["hypothesisAssessments"]
                      if a["hypothesisId"] == "FC-FD-002")
        target["evidenceIds"] = first["evidenceIds"][:1]
        self.reseal()
        self.rejects("wrong hypothesis")

    def test_losing_backlink_is_rejected(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        target = next(a for a in self.ledger["hypothesisAssessments"]
                      if a["hypothesisId"] == "FC-FD-001")
        target["evidenceIds"] = []
        self.reseal()
        self.rejects("assessment missing backlink")

    def test_resealed_observation_source_forgery_is_blocked(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        self.ledger["observations"][1]["sourceRef"] = "SIM-FORGED"
        self.reseal()
        self.rejects("observation and case signal provenance drift")

    def test_resealed_evidence_causal_reversal_is_blocked(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        self.ledger["evidence"][0]["relation"] = "inconsistent_with"
        self.reseal()
        self.rejects("causal mapping differs from pilot rubric")

    def test_resealed_evidence_source_forgery_is_blocked(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        self.rebuild()
        self.ledger["evidence"][0]["sourceRef"] = "SIM-FORGED"
        self.reseal()
        self.rejects("evidence source reference drift")

    def test_resealed_neutral_evidence_omission_is_blocked(self):
        self.case["signals"] = [present("additive_profile_changed")]
        self.rebuild()
        self.ledger["evidence"] = []
        self.reseal()
        self.rejects("missing or invented neutral observations")

    def test_audit_reorder_rejected(self):
        self.ledger["auditTrail"][1], self.ledger["auditTrail"][2] = (
            self.ledger["auditTrail"][2], self.ledger["auditTrail"][1])
        self.rejects("hash chain")

    def test_fmea_binding_drift_detected(self):
        self.ledger["sourceBinding"]["fmeaInputSha256"] = "a" * 64
        self.reseal()
        self.rejects("provenance mismatch")


if __name__ == "__main__":
    unittest.main()
