"""Cycle 44 regression: author-constructed theory-of-tests, NEVER field accuracy."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from benchmarks import cycle44_discrimination as d
from pilot.change_review_packets import ReviewRejected


class Cycle44DiscriminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = d.load(d.FIXTURE)
        cls.report = d.evaluate(cls.data)

    def test_traces_all_four_domains_and_conflict_abstentions(self):
        r = self.report
        self.assertEqual(r["trialCount"], 8)
        self.assertEqual(r["rankedPaperOnlyCount"], 4)
        self.assertEqual(r["abstentionCount"], 4)
        self.assertEqual(r["syntheticPairCoverageComparison"]["scoredTrials"], 4)
        self.assertEqual(
            r["syntheticPairCoverageComparison"]["totalTheoreticalPairDifference"], 8
        )
        self.assertFalse(
            r["syntheticPairCoverageComparison"]["independentOracleUsed"])
        self.assertFalse(
            r["syntheticPairCoverageComparison"]["fieldInformationGainMeasured"])
        self.assertEqual({x["familyId"] for x in r["trials"]}, set(d.FAMILIES))
        for case in r["trials"]:
            self.assertEqual(case["physicalTestsPerformed"], 0)
            self.assertEqual(len(case["unconfirmedHypotheses"]), 3)
            for key in ("mayExecuteTest", "mayCreateWorkOrder",
                        "mayModifyEcm", "mayReleaseEquipment"):
                self.assertFalse(case[key])
            if case["state"] == "abstain":
                self.assertEqual(case["reason"], "unresolved_contradiction")
                self.assertIsNone(case["selectedQuestionId"])
                self.assertIsNone(case["theoreticalPairsSelected"])
            else:
                self.assertEqual(case["theoreticalPairsBaseline"], 0)
                self.assertEqual(case["theoreticalPairsSelected"], 2)
                self.assertEqual(case["theoreticalPairDifference"], 2)

    def test_its_symbolic_partition_count_is_not_information_gain(self):
        question = self.data["trials"][0]["questions"][1]
        h = self.data["trials"][0]["hypothesisIds"]
        self.assertEqual(d.theoretical_pair_coverage(question, h), 2)
        altered = copy.deepcopy(question)
        altered["symbolicOutcomesByHypothesis"][h[1]] = "group_a"
        altered["symbolicOutcomesByHypothesis"][h[2]] = "group_a"
        self.assertEqual(d.theoretical_pair_coverage(altered, h), 0)
        missing = copy.deepcopy(question)
        missing["symbolicOutcomesByHypothesis"][h[1]] = None
        self.assertIsNone(d.theoretical_pair_coverage(missing, h))
        renaming = copy.deepcopy(question)
        renaming["symbolicOutcomesByHypothesis"] = {
            name: {"group_a": "label_x", "group_b": "label_y"}[value]
            for name, value in question["symbolicOutcomesByHypothesis"].items()
        }
        self.assertEqual(d.theoretical_pair_coverage(renaming, h), 2)

    def test_unavailable_best_candidate_is_not_selected(self):
        trial = self.data["trials"][0]
        best_unavailable = trial["questions"][2]["questionId"]
        self.assertEqual(d.theoretical_pair_coverage(
            trial["questions"][2], trial["hypothesisIds"]), 3)
        r = d.assess_trial(trial)
        self.assertNotEqual(r["selectedQuestionId"], best_unavailable)
        self.assertEqual(r["theoreticalPairsSelected"], 2)
        self.assertFalse(r["mayExecuteTest"])

    def test_tie_and_incomplete_baseline_abstain(self):
        trial = copy.deepcopy(self.data["trials"][0])
        trial["questions"][2]["fictionalDocumentaryPrerequisitePresent"] = True
        trial["questions"][2]["symbolicOutcomesByHypothesis"] = copy.deepcopy(
            trial["questions"][1]["symbolicOutcomesByHypothesis"]
        )
        r = d.assess_trial(trial)
        self.assertEqual(r["state"], "abstain")
        self.assertEqual(r["reason"], "tie_requires_human_review")
        self.assertIsNone(r["selectedQuestionId"])
        trial = copy.deepcopy(self.data["trials"][0])
        trial["questions"][0]["symbolicOutcomesByHypothesis"][
            trial["hypothesisIds"][1]
        ] = None
        self.assertEqual(d.assess_trial(trial)["reason"],
                         "baseline_not_evaluable")

    def test_conflict_outranks_theoretical_perfect_partition(self):
        trial = copy.deepcopy(self.data["trials"][1])
        trial["questions"][2]["fictionalDocumentaryPrerequisitePresent"] = True
        self.assertEqual(d.theoretical_pair_coverage(
            trial["questions"][2], trial["hypothesisIds"]), 3)
        r = d.assess_trial(trial)
        self.assertEqual(r["state"], "abstain")
        self.assertIsNone(r["selectedQuestionId"])
        self.assertIsNone(r["theoreticalPairDifference"])

    def test_forged_field_validation_and_permissions_are_rejected(self):
        for field in d.DENIALS:
            altered = copy.deepcopy(self.data)
            altered["claims"][field] = True
            with self.subTest(field=field), self.assertRaises(ReviewRejected):
                d.validate_fixture(altered)
        for path, value in [
            (("trials", 0, "questions", 1, "requiresPhysicalTest"), True),
            (("trials", 0, "questions", 1, "operationalApprovalVerified"), True),
            (("trials", 0, "scenarioKind"), "field_confirmed"),
            (("trials", 0, "hypothesisIds"), ["one"]),
            (("trials", 1, "unresolvedContradiction"), False),
            (("trials", 0, "questions", 0, "questionId"), "unsafe result"),
            (("trials", 0, "baselineQuestionId"), "other"),
            (("trials", 0, "questions", 0, "symbolicOutcomesByHypothesis"),
             {"unvalidated": "confirmed"}),
        ]:
            altered = copy.deepcopy(self.data)
            obj = altered
            for key in path[:-1]:
                obj = obj[key]
            obj[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                d.validate_fixture(altered)

    def test_no_false_authority_in_output_and_report_integrity(self):
        self.assertTrue(d.verify_report(self.report, self.data))
        self.assertFalse(self.report["diagnosticAccuracyMeasured"])
        self.assertFalse(self.report["independentMechanicalReviewCompleted"])
        self.assertEqual(self.report["fieldMeasurements"], 0)
        self.assertEqual(self.report["confirmedRootCauses"], 0)
        self.assertEqual(
            self.report["decision"],
            "no_go_symbolic_discrimination_not_validated_in_field")
        for path, value in [
            (("diagnosticAccuracyMeasured",), True),
            (("independentMechanicalReviewCompleted",), True),
            (("fieldMeasurements",), 1),
            (("syntheticPairCoverageComparison", "independentOracleUsed"), True),
            (("trials", 0, "selectedQuestionId"), "unsafe_replace_motor"),
        ]:
            altered = copy.deepcopy(self.report)
            obj = altered
            for key in path[:-1]:
                obj = obj[key]
            obj[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                d.verify_report(altered, self.data)

    def test_schema_contracts_require_no_go(self):
        import json
        root = Path(__file__).resolve().parents[1] / "contracts"
        cases = json.loads((root / "cycle44-trials.schema.json").read_text(encoding="utf-8"))
        report = json.loads((root / "cycle44-report.schema.json").read_text(encoding="utf-8"))
        for schema in (cases, report):
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
        for key in d.DENIALS:
            self.assertIs(cases["properties"]["claims"]["properties"][key]["const"], False)
        for key in ("diagnosticAccuracyMeasured", "independentMechanicalReviewCompleted",
                    "mayExecuteTest", "mayCreateWorkOrder", "mayModifyEcm",
                    "mayReleaseEquipment"):
            self.assertIs(report["properties"][key]["const"], False)
        self.assertEqual(report["properties"]["decision"]["const"],
                         "no_go_symbolic_discrimination_not_validated_in_field")

    def test_cli_and_report_are_reproducible_offline(self):
        note = d.markdown(self.report)
        self.assertIn("NO GO", note)
        self.assertIn("Nenhum revisor independente", note)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "trial-results.json"
            summary = Path(tmp) / "trial-summary.md"
            report = d.main(["--output", str(output),
                             "--markdown", str(summary)])
            self.assertEqual(report, self.report)
            self.assertTrue(d.verify_report(d.load(output), self.data))
            self.assertIn("NO GO", summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
