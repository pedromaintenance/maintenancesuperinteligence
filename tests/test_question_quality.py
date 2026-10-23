"""Testes adversariais do benchmark sintético: consistência != acurácia OEM."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from benchmarks.quality import (
    ROOT, CATEGORIES, eval_one, execute_benchmark, main, validate_manifest, validate_rubric
)
from methods.discrimination import select_questions, validate_matrix
from methods.library import validate_catalog, validate_sources


class QualityBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(
            (ROOT / "benchmarks/question-quality.v1.json").read_text())
        self.rubric = json.loads(
            (ROOT / "benchmarks/question-quality-rubric.v1.json").read_text())
        self.matrix = json.loads(
            (ROOT / "methods/discrimination-matrix.v1.json").read_text())
        sources = json.loads(
            (ROOT / "data/diagnostic-method-sources.v1.json").read_text())
        self.methods = validate_catalog(
            json.loads((ROOT / "methods/catalog.v1.json").read_text()),
            validate_sources(sources))
        self.snapshot = {"records": [
            {"id": name, "family": "comando_final", "confirmedRootCause": False}
            for name in ("FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004")
        ]}
        self.families = validate_matrix(self.matrix, self.methods, self.snapshot)
        self.fixtures = validate_manifest(self.manifest, self.families)

    def output(self, key="FD-ADDITIVES-UNKNOWN"):
        fix = next(f for f in self.fixtures if f["fixtureId"] == key)
        return fix, select_questions(fix["case"], self.matrix,
                                     self.methods, self.snapshot)

    def mutant(self, category, fn, fixture="FD-ADDITIVES-UNKNOWN"):
        case, report = self.output(fixture)
        fn(report)
        result = eval_one(case, report, self.families, self.methods)
        self.assertIn(category, result["failureClasses"])
        self.assertFalse(result["passes"])
        self.assertTrue(result["failures"])

    def test_benchmark_all_fifteen_pass(self):
        result = execute_benchmark(self.manifest, self.matrix,
                                   self.methods, self.snapshot)
        self.assertEqual(result["fixturesEvaluated"], 15)
        self.assertEqual(result["fixturesPassed"], 15)
        self.assertEqual(result["acceptance"], "regression_pass")
        self.assertEqual(result["syntheticAbstentionRate"], {
            "abstained": 15, "total": 15})
        self.assertEqual(result["canonicalReproducibility"], {
            "passed": 15, "total": 15})
        self.assertFalse(result["diagnosticAccuracyMeasured"])
        self.assertFalse(result["technicalExpertReviewComplete"])
        self.assertFalse(result["operationalValidation"])
        self.assertTrue(all(x["checksPassed"] == x["checksTotal"] for x in result["cases"]))

    def test_all_categories_have_coverage(self):
        r = execute_benchmark(self.manifest, self.matrix,
                              self.methods, self.snapshot)
        self.assertEqual(set(r["checkComplianceByCategory"]), set(CATEGORIES))
        for name, counts in r["checkComplianceByCategory"].items():
            with self.subTest(name=name):
                self.assertGreater(counts["total"], 0)
                self.assertEqual(counts["passed"], counts["total"])
                self.assertEqual(r["failureCountsByClass"][name], 0)

    def test_five_cases_per_family(self):
        from collections import Counter
        self.assertEqual(dict(Counter(x["familyId"] for x in self.fixtures)), {
            "final_drive": 5, "hydraulics": 5, "electronics": 5
        })

    def test_logged_and_active_dtc_are_different_scenarios_not_diagnoses(self):
        logged, logged_output = self.output("ECM-LOGGED-UNKNOWN")
        active, active_output = self.output("ECM-ACTIVE-CONTEXT-MISSING")
        self.assertNotEqual(logged["case"]["reportedSignals"],
                            active["case"]["reportedSignals"])
        self.assertEqual(logged_output["selectionRationale"]["selectedPairId"],
                         "EL-P01")
        self.assertEqual(active_output["selectionRationale"]["selectedPairId"],
                         "EL-P02")
        for report in (logged_output, active_output):
            self.assertIsNone(report["confirmedComponent"])
            self.assertFalse(report["mayModifyECM"])

    def test_oil_formulation_remains_unconfirmed(self):
        fixture, report = self.output("FD-FORMULATION-RECORDED")
        self.assertEqual(report["selectionRationale"]["selectedPairId"], "FD-P02")
        self.assertEqual(len(report["hypotheses"]), 7)
        self.assertTrue(all(x["status"] == "open_not_confirmed"
                            for x in report["hypotheses"]))
        self.assertEqual(fixture["expected"]["selectionStatus"], "ask_missing_context")

    def test_hydraulic_load_conflict_precedes_pressure_question(self):
        fixture, report = self.output("HYD-LOAD-DISPUTED")
        self.assertEqual(report["selectionRationale"]["selectionStatus"],
                         "reconcile_contradiction")
        self.assertIn("load_context",
                      report["selectionRationale"]["selectedNextQuestion"])
        self.assertFalse(report["mayRunTests"])

    def test_context_not_applicable_is_not_available(self):
        _, report = self.output("HYD-LOAD-NOT-APPLICABLE")
        self.assertEqual(report["selectionRationale"]["selectionStatus"],
                         "review_applicability")

    def test_all_simulated_context_does_not_approve_oem(self):
        for key in ("FD-ALL-SIMULATED", "HYD-ALL-SIMULATED", "ECM-ALL-SIMULATED"):
            with self.subTest(key=key):
                _, report = self.output(key)
                self.assertEqual(report["selectionRationale"]["selectionStatus"],
                                 "prepare_human_method_review")
                self.assertFalse(report["mayRunTests"])
                self.assertIsNone(report["confirmedComponent"])

    def test_rubric_version_and_all_nine_classes(self):
        validated = validate_rubric(self.rubric)
        self.assertEqual(len(validated["categories"]), 9)
        self.assertEqual({x["failureClass"] for x in validated["categories"]},
                         set(CATEGORIES))
        report = execute_benchmark(self.manifest, self.matrix,
                                   self.methods, self.snapshot, self.rubric)
        self.assertEqual(len(report["rubricSha256"]), 64)
        self.assertFalse(report["diagnosticAccuracyMeasured"])

    def test_rubric_rejects_false_accuracy_claim(self):
        self.rubric["allowedInterpretation"] = "validated_failure_detection"
        with self.assertRaises(ImportRejected):
            validate_rubric(self.rubric)

    def test_rubric_rejects_omitted_failure_class(self):
        self.rubric["categories"].pop()
        with self.assertRaises(ImportRejected):
            validate_rubric(self.rubric)

    def test_rubric_rejects_duplicate_failure_class(self):
        self.rubric["categories"][1]["failureClass"] = (
            self.rubric["categories"][0]["failureClass"])
        with self.assertRaises(ImportRejected):
            validate_rubric(self.rubric)

    def test_rubric_rejects_decorative_pass_from_unreviewed_result(self):
        self.rubric["categories"][0]["expectedCheckStatus"] = "already_validated"
        with self.assertRaises(ImportRejected):
            validate_rubric(self.rubric)

    def test_golden_label_mutation_produces_selection_failure(self):
        altered = copy.deepcopy(self.manifest)
        altered["fixtures"][0]["expected"]["nextQuestionContains"] = "NO-REAL-MEASUREMENTS-EXIST"
        report = execute_benchmark(altered, self.matrix,
                                   self.methods, self.snapshot)
        self.assertEqual(report["acceptance"], "regression_fail")
        self.assertEqual(report["fixturesPassed"], 14)
        self.assertEqual(report["failureCountsByClass"]["selection"], 1)

    def test_mutated_case_family_id_rejected(self):
        self.manifest["fixtures"][0]["case"]["familyId"] = "hydraulics"
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_duplicate_fixture_id_rejected(self):
        self.manifest["fixtures"][1]["fixtureId"] = self.manifest["fixtures"][0]["fixtureId"]
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_false_review_complete_rejected(self):
        self.manifest["reviewStatus"] = "expert_approved"
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_manifest_cannot_claim_field_accuracy(self):
        self.manifest["nature"] = "validated_prediction_accuracy"
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_manifest_cannot_add_root_cause(self):
        self.manifest["fixtures"][0]["expected"]["rootCause"] = "bearing"
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_manifest_rejects_real_case_source(self):
        self.manifest["fixtures"][0]["case"]["caseId"] = "SAP-OS-00001"
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_manifest_rejects_false_oem_effectivity(self):
        self.manifest["fixtures"][0]["case"]["oemGate"]["approved"] = True
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_manifest_rejects_unsupported_confidence(self):
        self.manifest["fixtures"][0]["expected"]["confidence"] = 0.98
        with self.assertRaises(ImportRejected):
            validate_manifest(self.manifest, self.families)

    def test_output_provenance_mutation(self):
        self.mutant("provenance", lambda r: r.update(evidenceNature="field_data"))

    def test_output_hypothesis_promoted(self):
        self.mutant("hypothesis_promotion",
                    lambda r: r["hypotheses"][0].update(confirmedRootCause=True))

    def test_output_ambiguity_removed(self):
        self.mutant("ambiguity",
                    lambda r: r["comparisons"][0].update(observedOutcome="pattern_first"))

    def test_output_contradiction_ignored(self):
        self.mutant("contradiction",
                    lambda r: r["comparisons"][1].update(status="prepare_human_method_review"),
                    "FD-SAMPLE-CONTRADICTION")

    def test_output_missing_prerequisite(self):
        self.mutant("prerequisite",
                    lambda r: r["comparisons"][0].update(discriminatingContext=[]))

    def test_output_source_spoofed(self):
        self.mutant("provenance",
                    lambda r: r["candidateQuestions"][0].update(methodSourceIds=["SAP-SECRET"]))

    def test_output_unsafe_machine_release(self):
        self.mutant("safety", lambda r: r.update(mayReleaseEquipment=True))

    def test_output_oem_effectivity_spoofed(self):
        self.mutant("effectivity",
                    lambda r: r["candidateQuestions"][0].update(oemApplicability="verified"))

    def test_output_unjustified_question(self):
        self.mutant("selection",
                    lambda r: r["selectionRationale"].update(selectedNextQuestion="Condenar bomba"))

    def test_output_nondeterministic_repeat(self):
        fixture, result = self.output()
        report = eval_one(fixture, result, self.families, self.methods, reproducible=False)
        self.assertIn("reproducibility", report["failureClasses"])

    def test_output_extra_authority_field_rejected(self):
        self.mutant("provenance",
                    lambda r: r.update(operationApproved=True))

    def test_benchmark_cli_rejects_corrupted_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "forged-snapshot.json"
            p.write_text('{"fmea": "fake"}')
            with patch("sys.stderr"):
                code = main(["--snapshot", str(p)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
