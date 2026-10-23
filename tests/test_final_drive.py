"""Differential pilot tests — all synthetic and non-operational."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected, load_lock
from investigations.final_drive import (
    ALLOWED_CHAIN_IDS, SIGNAL_LABELS, investigate, main,
    validate_case, validate_index,
)

ROOT = Path(__file__).resolve().parent.parent


def case_template():
    return {
        "schema": "maintenance-superinteligence.final-drive-case.v1",
        "caseId": "SIM-777E-TEST", "purpose": "training_simulation",
        "machine": {"manufacturer": "Caterpillar", "model": "777E",
                    "serialOrArrangement": None, "finalDrivePosition": None},
        "complaint": "Simulação didática de anomalia em óleo, sem prova de defeito.",
        "signals": [],
        "availableContext": {
            "oilHistoryAvailable": False, "sampleMetadataAvailable": False,
            "trendBaselineAvailable": False, "oemReferenceAvailable": False,
        },
    }


def present(code, number=1, result="present", nature="simulation"):
    return {"code": code, "result": result, "evidenceNature": nature,
            "sourceRef": f"SIM-EVIDENCE-{number}"}


def mocked_index():
    lock = load_lock()
    sources = [
        {"id": f"SRC-{n:02}", "title": f"Synthetic literature {n}",
         "organization": "Test fixture", "url": f"https://example.org/{n}",
         "role": "synthetic", "limitation": "Not applicable to real equipment"}
        for n in range(20)
    ]
    ids = list(ALLOWED_CHAIN_IDS) + [f"FC-OTHER-{n:02}" for n in range(20)]
    records = [{
        "fmeaId": rid, "title": f"Synthetic hypothesis {rid}",
        "family": "comando_final" if rid in ALLOWED_CHAIN_IDS else "outros",
        "operatingFunction": "Support power transfer", "functionalFailureId": "FF-SYN",
        "failureModeCandidate": "Mechanism can occur", "mechanismIds": ["ME-SYN"],
        "causalLevels": {"rootCauseNotEstablishedBecause": "No evidence was collected"},
        "potentialEffects": {"local": {"status": "possible_unobserved"},
                             "system": {"status": "possible_unobserved"}},
        "competingHypotheses": [
            {"id": "ALT1", "description": "Other cause", "discriminator": "Test"},
            {"id": "ALT2", "description": "Competing cause", "discriminator": "Another test"},
        ],
        "plannedInvestigations": [
            {"id": "I1", "methodId": "EV-01", "purpose": "Observe simulated signal",
             "status": "not_performed"},
            {"id": "I2", "methodId": "EV-02", "purpose": "Compare simulated histories",
             "status": "not_performed"},
        ],
        "sourceIds": ["SRC-00"],
        "applicability": {"modelId": None, "locationId": None,
                          "serialOrArrangement": None},
        "evidenceNature": "hypothesis_not_event",
        "reviewStatus": "inferido_com_literatura_geral",
        "confirmedRootCause": False, "empiricalOccurrences": 0,
        "approvedForOperationalUse": False,
    } for rid in ids]
    return {
        "schema": "maintenance-superinteligence.fmea-concept-index.v1",
        "contentVersion": lock["contentVersion"],
        "contractVersion": lock["contractVersion"],
        "inputSha256": lock["sha256"],
        "producerCommit": lock["producerCommit"],
        "reviewStatus": "inferred_not_operational",
        "approvedForOperationalUse": False, "records": records,
        "sources": sources,
    }


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.case = case_template()
        self.index = mocked_index()

    def run_case(self):
        return investigate(self.case, self.index)

    def assert_no_diagnosis(self, result):
        self.assertIsNone(result["confirmedRootCause"])
        self.assertIsNone(result["condemnedComponent"])
        self.assertFalse(result["mayReleaseEquipment"])
        self.assertFalse(result["mayCreateWorkOrder"])
        self.assertTrue(result["humanReviewRequired"])
        self.assertFalse(result["machineContext"]["oemApplicabilityVerified"])
        self.assertEqual(result["provenance"]["simulatedEvidenceOnly"], True)
        self.assertTrue(all(t["status"] == "not_performed"
                            for t in result["plannedInvestigations"]))
        self.assertTrue(all(h["disposition"] != "confirmed"
                            for h in result["hypotheses"]))

    def test_no_signals_still_open(self):
        result = self.run_case()
        self.assert_no_diagnosis(result)
        self.assertEqual(result["decision"], "needs_evidence")
        self.assertEqual(len(result["hypotheses"]), 7)
        self.assertEqual(len(result["plannedInvestigations"]), 8)

    def test_additives_alone_never_indicate_wear(self):
        self.case["signals"] = [present("additive_profile_changed")]
        result = self.run_case()
        self.assert_no_diagnosis(result)
        self.assertFalse(any(h["supportingSignals"] for h in result["hypotheses"]))
        self.assertTrue(any("aditivos" in x for x in result["knowledgeGaps"]))

    def test_change_documented_is_not_failure(self):
        self.case["signals"] = [
            present("additive_profile_changed"), present("lubricant_change_documented", 2)]
        result = self.run_case()
        self.assert_no_diagnosis(result)
        self.assertEqual(result["decision"], "needs_evidence")
        h = next(h for h in result["hypotheses"] if h["id"] == "PILOT-FORMULATION")
        self.assertEqual(h["supportingSignals"], ["lubricant_change_documented"])
        wear = next(h for h in result["hypotheses"] if h["id"] == "FC-FD-004")
        self.assertEqual(wear["supportingSignals"], [])

    def test_trending_particles_are_non_discriminating(self):
        self.case["signals"] = [present("particle_trend_increasing")]
        result = self.run_case()
        for rid in ("FC-FD-001", "FC-FD-003", "FC-FD-004"):
            self.assertIn("particle_trend_increasing",
                          next(h for h in result["hypotheses"]
                               if h["id"] == rid)["supportingSignals"])
        self.assert_no_diagnosis(result)

    def test_water_retests_diverge(self):
        self.case["signals"] = [
            present("water_retest_confirmed"),
            present("water_retest_not_reproduced", 2)]
        result = self.run_case()
        self.assert_no_diagnosis(result)
        self.assertEqual(result["decision"], "escalate_to_specialist")
        self.assertTrue(result["conflicts"])
        water = next(h for h in result["hypotheses"] if h["id"] == "FC-FD-002")
        self.assertEqual(water["disposition"], "mixed_evidence_open_not_confirmed")

    def test_external_noise_remains_competing_explanation(self):
        self.case["signals"] = [present("noise_localized_external")]
        result = self.run_case()
        bearing = next(h for h in result["hypotheses"] if h["id"] == "FC-FD-004")
        self.assertEqual(bearing["disposition"], "weakened_not_excluded")
        self.assert_no_diagnosis(result)

    def test_internal_external_noise_conflict(self):
        self.case["signals"] = [present("noise_localized_external"),
                                present("noise_localized_final_drive", 2)]
        result = self.run_case()
        self.assertEqual(result["decision"], "escalate_to_specialist")
        self.assert_no_diagnosis(result)

    def test_functional_loss_escalates_without_operational_clearance(self):
        self.case["signals"] = [present("reported_loss_of_function")]
        result = self.run_case()
        self.assertEqual(result["decision"], "escalate_to_specialist")
        self.assertTrue(result["riskAlerts"])
        self.assert_no_diagnosis(result)

    def test_magnetic_debris_escalates_but_does_not_condemn(self):
        self.case["signals"] = [present("magnetic_debris_increasing")]
        result = self.run_case()
        self.assertEqual(result["decision"], "escalate_to_specialist")
        self.assert_no_diagnosis(result)

    def test_incomplete_context_lists_gaps(self):
        result = self.run_case()
        self.assertGreaterEqual(len(result["knowledgeGaps"]), 5)
        self.assertTrue(any("série/arranjo" in s for s in result["knowledgeGaps"]))

    def test_all_context_flags_do_not_verify_oem_effectivity(self):
        self.case["machine"]["serialOrArrangement"] = "SIMULATED-SERIES"
        self.case["machine"]["finalDrivePosition"] = "SIMULATED-LEFT"
        self.case["availableContext"] = {k: True for k in self.case["availableContext"]}
        result = self.run_case()
        self.assert_no_diagnosis(result)
        self.assertFalse(result["machineContext"]["oemApplicabilityVerified"])

    def test_absent_and_inconclusive_do_not_count_as_positive(self):
        self.case["signals"] = [
            present("magnetic_debris_increasing", result="absent"),
            present("noise_localized_final_drive", 2, "inconclusive")]
        result = self.run_case()
        self.assertEqual(result["decision"], "needs_evidence")
        self.assert_no_diagnosis(result)

    def test_reject_field_data_in_pilot(self):
        self.case["signals"] = [present("water_retest_confirmed", nature="empirical_authorised")]
        with self.assertRaisesRegex(ImportRejected, "somente evidência simulada"):
            self.run_case()

    def test_reject_raw_oem_threshold_injection(self):
        self.case["machine"]["maxTorqueNm"] = 4400
        with self.assertRaises(ImportRejected):
            self.run_case()

    def test_reject_oem_model_substitution(self):
        self.case["machine"]["model"] = "6030"
        with self.assertRaisesRegex(ImportRejected, "apenas CAT 777E"):
            self.run_case()

    def test_reject_unrecognized_signal(self):
        self.case["signals"] = [present("bearing_broken_confirmed")]
        with self.assertRaisesRegex(ImportRejected, "signal desconhecido"):
            self.run_case()

    def test_reject_duplicate_signal(self):
        self.case["signals"] = [present("particle_trend_increasing"),
                                present("particle_trend_increasing", 2)]
        with self.assertRaisesRegex(ImportRejected, "duplicado"):
            self.run_case()

    def test_reject_source_ref_not_simulated(self):
        self.case["signals"] = [present("viscosity_outlier")]
        self.case["signals"][0]["sourceRef"] = "SAP-ORDER-1"
        with self.assertRaisesRegex(ImportRejected, "sourceRef"):
            self.run_case()

    def test_reject_confirmed_root_in_index(self):
        self.index["records"][0]["confirmedRootCause"] = True
        with self.assertRaisesRegex(ImportRejected, "promoção causal"):
            self.run_case()

    def test_reject_performed_source_test(self):
        self.index["records"][0]["plannedInvestigations"][0]["status"] = "performed"
        with self.assertRaisesRegex(ImportRejected, "investigação marcada"):
            self.run_case()

    def test_reject_serial_effectivity_in_generic_index(self):
        self.index["records"][0]["applicability"]["serialOrArrangement"] = "SYN"
        with self.assertRaisesRegex(ImportRejected, "efetividade"):
            self.run_case()

    def test_reject_mismatched_index_hash(self):
        self.index["inputSha256"] = "0" * 64
        with self.assertRaisesRegex(ImportRejected, "pinado"):
            self.run_case()

    def test_reject_index_missing_chain(self):
        self.index["records"] = [x for x in self.index["records"]
                                  if x["fmeaId"] != "FC-FD-004"]
        with self.assertRaises(ImportRejected):
            self.run_case()

    def test_reject_unapproved_malformed_case(self):
        self.case["purpose"] = "real_diagnosis"
        with self.assertRaisesRegex(ImportRejected, "simulação"):
            self.run_case()

    def test_examples_pass_and_remain_didactic(self):
        for name in ("777e_additives_only", "777e_change_documented",
                     "777e_water_disputed", "777e_debris_and_noise"):
            with self.subTest(name=name):
                obj = json.loads((ROOT / "examples" / f"{name}.json").read_text())
                self.assert_no_diagnosis(investigate(obj, self.index))

    def test_cli_rejects_tampered_source_before_reading_index(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            snapshot = tmp / "forged.json"
            snapshot.write_text('{"schema": "fake"}', encoding="utf-8")
            case = tmp / "case.json"
            case.write_text(json.dumps(self.case), encoding="utf-8")
            with patch("sys.stderr"):
                code = main(["--snapshot", str(snapshot), "--case", str(case)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
