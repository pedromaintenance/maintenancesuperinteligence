"""Ciclo 14: adversarial tests for qualitative conditional evidence (NOT field diagnosis)."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as genuine_validate_catalog
from evidence.qualitative import (MATRIX_PATH, validate_qualitative_matrix,
                                  assess_case)
from casefiles.integrated import (load_dependencies, build_collection,
                                 render_html, validate_fixture, verify_report)


class QualitativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = {"records": [
            {"id": f"FC-FD-{i:03d}", "family": "comando_final",
             "confirmedRootCause": False} for i in range(1, 5)
        ]}
        # The full FMEA source is used in CI after validating its locked bytes.
        # Compact isolated unittest fixture does not contain 24 FMEA investigations.
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda catalog, registry, snapshot:
                   genuine_validate_catalog(catalog, registry)):
            cls.deps = load_dependencies(cls.snapshot)

    def setUp(self):
        self.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        self.fixtures = json.loads(
            (ROOT / "casefiles/technical-cases.v1.json").read_text())

    def validate(self):
        return validate_qualitative_matrix(
            self.matrix, self.deps["families"],
            self.deps["methods"], self.deps["sources"])

    def reject(self, reason=None):
        with self.assertRaises(ImportRejected) as caught:
            self.validate()
        if reason:
            self.assertIn(reason, str(caught.exception))

    def pair(self, id):
        return next(x for x in self.matrix["pairs"] if x["pairId"] == id)

    def case(self, fixture_id):
        return self.deps["fixtures"][fixture_id]["case"]

    def selection(self, fixture_id):
        from methods.discrimination import select_questions
        return select_questions(
            self.case(fixture_id),
            self.deps["matrix"],
            self.deps["methods"],
            self.snapshot)

    def assess(self, fixture_id):
        return assess_case(self.case(fixture_id),
                           self.selection(fixture_id),
                           self.validate(), self.deps["methods"])

    def mocked_build(self):
        # Investigation/consumer FMEA linkage is tested by the real locked
        # snapshot CI; the unit corpus verifies only synthetic output integrity.
        source = json.loads((ROOT / "examples/777e_additives_only.json").read_text())
        mock = {
            "caseId": source["caseId"],
            "confirmedRootCause": None,
            "mayReleaseEquipment": False,
            "mayCreateWorkOrder": False,
            "hypotheses": [
                {"id": x["hypothesisId"]}
                for x in self.deps["families"]["final_drive"]["hypotheses"]],
            "plannedInvestigations": [{"status": "not_performed"} for _ in range(8)],
            "decision": "needs_evidence",
            "observations": [{"code": s["code"], "result": s["result"]}
                             for s in source["signals"]],
            "conflicts": [],
            "knowledgeGaps": ["Coleta e histórico não informados."],
        }
        with patch("casefiles.integrated.build_consumer_index", return_value={}):
            with patch("casefiles.integrated.investigate", return_value=mock):
                return build_collection(self.fixtures, self.deps, self.snapshot)

    def test_versioned_oracle_matches_all_four_case_outcomes(self):
        r = self.mocked_build()
        self.assertEqual(len(r["qualitativeOracleSha256"]), 64)
        self.assertEqual(len(self.deps["qualitativeOracle"]["expected"]), 4)
        for row in self.deps["qualitativeOracle"]["expected"]:
            self.assertTrue(all(x["currentEvidenceState"] in (
                "not_measured", "contradicted", "inconclusive")
                for x in row["comparisonStates"]))
            self.assertEqual(row["hypothesesExcluded"], 0)

    def test_oracle_cannot_invent_support_observed(self):
        self.deps["qualitativeOracle"]["expected"][0]["observedSupportCount"] = 1
        with self.assertRaises(ImportRejected):
            self.mocked_build()

    def test_oracle_cannot_promote_missing_to_negative(self):
        self.deps["qualitativeOracle"]["expected"][0]["comparisonStates"][0][
            "currentEvidenceState"] = "weakens"
        with self.assertRaises(ImportRejected):
            self.mocked_build()

    def test_oracle_cannot_hide_load_contradiction(self):
        self.deps["qualitativeOracle"]["expected"][1]["comparisonStates"][0][
            "currentEvidenceState"] = "inconclusive"
        with self.assertRaises(ImportRejected):
            self.mocked_build()

    def test_oracle_cannot_change_selected_pair_without_review(self):
        self.deps["qualitativeOracle"]["expected"][3]["selectedPairId"] = "EL-P01"
        with self.assertRaises(ImportRejected):
            self.mocked_build()

    def test_all_ten_original_pairs_and_twenty_distinct_counterexamples(self):
        m = self.validate()
        self.assertEqual(len(m), 10)
        self.assertEqual({k.split("-")[0] for k in m}, {"FD", "HYD", "EL"})
        self.assertEqual(sum(len(p["conditionalObservations"]) for p in m.values()), 30)
        self.assertEqual(sum(len(p["alternativeExplanations"]) for p in m.values()), 20)
        for p in m.values():
            self.assertEqual(p["testStatus"], "not_performed")
            self.assertIsNone(p["observedOutcome"])
            self.assertFalse(p["mayExcludeEitherHypothesis"])
            self.assertEqual(len(set(a["statement"]
                                     for a in p["alternativeExplanations"])), 2)

    def test_all_outcomes_conditional_and_open(self):
        for p in self.validate().values():
            self.assertEqual(
                [(x["effectOnFirst"], x["effectOnSecond"])
                 for x in p["conditionalObservations"]],
                [("supports", "weakens"), ("weakens", "supports"),
                 ("inconclusive", "inconclusive")])
            self.assertTrue(all(x["nature"] == "counterfactual_not_observed"
                                for x in p["conditionalObservations"]))

    def test_general_sources_are_exactly_the_method_catalog(self):
        for p in self.validate().values():
            expected = sorted(set(sid for mid in p["methodIds"]
                                  for sid in self.deps["methods"][mid]["sourceIds"]))
            self.assertEqual(p["sourceIds"], expected)

    def test_missing_context_does_not_become_weakening(self):
        a = self.assess("FD-ADDITIVES-UNKNOWN")
        self.assertTrue(all(r["currentEvidenceState"] == "not_measured"
                            for r in a["comparisons"]))
        self.assertEqual(a["observedWeakeningCount"], 0)
        self.assertEqual(a["hypothesesExcluded"], 0)

    def test_contradicted_load_is_context_not_confirmed_failure(self):
        a = self.assess("HYD-LOAD-DISPUTED")
        rows = [x for x in a["comparisons"]
                if x["currentEvidenceState"] == "contradicted"]
        self.assertTrue(rows)
        self.assertTrue(all(not x["observedPhysicalEvidence"]
                            and x["fieldResult"] is None and
                            x["cannotDismissEitherHypothesis"] for x in rows))

    def test_active_and_logged_ecm_remain_indeterminate(self):
        for id in ("ECM-LOGGED-UNKNOWN", "ECM-ACTIVE-CONTEXT-MISSING"):
            a = self.assess(id)
            self.assertEqual(a["observedSupportCount"], 0)
            self.assertEqual(a["observedWeakeningCount"], 0)
            self.assertTrue(all(x["currentEvidenceState"] in
                                ("not_measured", "contradicted", "inconclusive")
                                for x in a["comparisons"]))
            self.assertFalse(a["mayConfirmRootCause"])

    def test_report_renders_thirteen_pair_instances_and_twenty_six_counterexamples(self):
        r = self.mocked_build()
        self.assertEqual(r["counterexamples"], 26)
        self.assertEqual(r["hypothesesExcluded"], 0)
        self.assertEqual(r["observedSupportingEvidence"], 0)
        self.assertEqual(r["observedWeakeningEvidence"], 0)
        self.assertEqual(sum(c["qualitativeEvidence"]["comparisonCount"]
                             for c in r["cases"]), 13)
        html = render_html(r)
        self.assertEqual(html.count("<section>"), 4)
        self.assertIn("Evidência discriminante condicional", html)
        self.assertIn("Contraexemplos", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<form", html)

    def test_html_rejects_forged_observation_as_measured(self):
        r = self.mocked_build()
        r["cases"][0]["qualitativeEvidence"]["comparisons"][0][
            "conditionalObservations"][0]["hasBeenObserved"] = True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_rejects_hypothesis_exclusion_by_missing_evidence(self):
        r = self.mocked_build()
        r["cases"][0]["qualitativeEvidence"]["comparisons"][0][
            "cannotDismissEitherHypothesis"] = False
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_rejects_forged_support_in_case(self):
        r = self.mocked_build()
        r["cases"][0]["qualitativeEvidence"]["observedSupportCount"] = 1
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_rejects_assigned_probability(self):
        r = self.mocked_build()
        r["cases"][0]["hypotheses"][0]["probability"] = 0.9
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_matrix_fabricated_physical_observation_rejected(self):
        self.pair("FD-P01")["observedOutcome"] = "pattern_first"
        self.reject("observation/diagnosis/test")

    def test_matrix_fabricated_test_rejected(self):
        self.pair("HYD-P01")["testStatus"] = "performed"
        self.reject("observation/diagnosis/test")

    def test_matrix_can_exclude_hypothesis_rejected(self):
        self.pair("EL-P02")["mayExcludeEitherHypothesis"] = True
        self.reject("observation/diagnosis/test")

    def test_matrix_relabels_conditional_to_real_evidence_rejected(self):
        self.pair("FD-P02")["conditionalObservations"][0][
            "nature"] = "physical_measurement"
        self.reject("altered conditional pattern")

    def test_matrix_changes_conditional_language_without_review_rejected(self):
        self.pair("FD-P01")["conditionalObservations"][0][
            "conditionalReading"] = "A bomba está definitivamente danificada"
        self.reject("altered conditional pattern")

    def test_matrix_forged_effect_rejected(self):
        self.pair("HYD-P03")["conditionalObservations"][2][
            "effectOnSecond"] = "supports"
        self.reject("altered conditional pattern")

    def test_matrix_without_indeterminate_case_rejected(self):
        self.pair("EL-P02")["conditionalObservations"].pop()
        self.reject("first, second and indeterminate")

    def test_matrix_with_duplicate_comparison_rejected(self):
        self.matrix["pairs"][-1]["pairId"] = "FD-P01"
        self.reject("duplicated/foreign")

    def test_matrix_missing_comparison_rejected(self):
        self.matrix["pairs"].pop()
        self.reject("10 reference pairs")

    def test_fake_oem_source_injection_rejected(self):
        self.pair("FD-P01")["sourceIds"] = ["CAT-OEM-777E-SERIES-PROCEDURE"]
        self.reject("source lineage changed")

    def test_wrong_hypothesis_pair_rejected(self):
        self.pair("HYD-P02")["secondHypothesisId"] = "HYD-VALVE"
        self.reject("lineage changed")

    def test_wrong_method_in_pair_rejected(self):
        self.pair("EL-P01")["methodIds"][0] = "MET-OIL-PRODUCT"
        self.reject("lineage changed")

    def test_no_alternative_rejected(self):
        self.pair("FD-P04")["alternativeExplanations"].pop()
        self.reject("two different counterexamples")

    def test_short_counterexample_rejected(self):
        self.pair("FD-P04")["alternativeExplanations"][0]["statement"] = "ok"
        self.reject("weak/duplicate")

    def test_duplicate_counterexample_rejected(self):
        p = self.pair("FD-P04")
        p["alternativeExplanations"][1]["statement"] = (
            p["alternativeExplanations"][0]["statement"])
        self.reject("weak/duplicate")

    def test_confident_causal_mechanism_claim_rejected(self):
        self.pair("EL-P03")["alternativeExplanations"][0][
            "causalMechanismVerified"] = True
        self.reject("false exclusion")

    def test_matrix_operational_permission_rejected(self):
        self.matrix["approvedForOperationalUse"] = True
        self.reject("operational authority")

    def test_matrix_fabricated_external_validation_rejected(self):
        self.matrix["independentClinicalOrFieldValidation"] = True
        self.reject("operational authority")

    def test_unknown_private_evidence_field_rejected(self):
        self.pair("FD-P01")["privateOilReport"] = "not allowed"
        self.reject("unexpected/missing")

    def test_provenance_forged_as_real_is_rejected_in_case(self):
        r = self.mocked_build()
        r["cases"][0]["qualitativeEvidence"]["comparisons"][0][
            "evidenceProvenance"]["sourceClaimsOemEffectivity"] = True
        with self.assertRaises(ImportRejected):
            # Reassembly is required: a modified output is not trusted.
            from casefiles.integrated import verify_report
            with patch("casefiles.integrated.build_consumer_index", return_value={}):
                with patch("casefiles.integrated.investigate", return_value={
                    "caseId": "SIM-777E-ADDITIVES-ONLY", "confirmedRootCause": None,
                    "mayReleaseEquipment": False, "mayCreateWorkOrder": False,
                    "hypotheses": [{"id": x["hypothesisId"]}
                                   for x in self.deps["families"]["final_drive"]["hypotheses"]],
                    "plannedInvestigations": [{"status":"not_performed"} for _ in range(8)],
                    "decision": "needs_evidence", "observations": [], "conflicts": [],
                    "knowledgeGaps": [],
                }):
                    verify_report(r, self.fixtures, self.deps, self.snapshot)


if __name__ == "__main__":
    unittest.main()
