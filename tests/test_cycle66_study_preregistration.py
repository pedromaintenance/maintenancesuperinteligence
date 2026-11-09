"""C66: prerequisites must never be laundered into real study approval."""
import copy
import unittest

from benchmarks.cycle66_study_preregistration import (
    CRITICAL_ERRORS, DENIED, GATES, METRICS, validate,
)
from tests.test_cycle65_review_ledger import fixture as ledger_fixture


def fixture():
    return {
        "schema": "maintenance-superinteligence.synthetic-independent-study-plan.v1",
        "reviewLedger": ledger_fixture(),
        "plan": {
            "design": "synthetic_protocol_rehearsal",
            "caseCount": 12, "reviewerCount": 2, "adjudicatorCount": 1,
            "blinding": "oracle_hidden_until_submissions_frozen",
            "oracleLocation": "external_private_custody_planned",
            "preRegistrationStatus": "not_frozen",
            "safetyStopRule": "any_critical_error_blocks_conclusions",
            "criticalErrorCategories": list(CRITICAL_ERRORS),
            "metricDenominators": {
                "critical_error_count": "all_frozen_case_responses",
                "abstention_rate": "all_frozen_case_responses",
                "discriminant_question_agreement": "eligible_frozen_case_responses",
                "reviewer_disagreement_count": "cases_reviewed_by_both_reviewers",
            },
            "realWorldDataUsed": False,
        },
        "externalGates": [
            {"id": gate, "status": "not_recorded",
             "evidenceReference": None, "verifiedBy": None}
            for gate in GATES
        ],
        "claims": {key: False for key in DENIED},
    }


class IndependentStudyPlanTests(unittest.TestCase):
    def test_baseline_has_all_gaps_and_no_go(self):
        out = validate(fixture())
        self.assertEqual(out["studyControlsRequired"], 12)
        self.assertEqual(out["externallyVerifiedControls"], 0)
        self.assertEqual(len(out["unverifiedControls"]), 12)
        self.assertFalse(out["readyForIndependentStudy"])
        self.assertFalse(out["metricValuesComputed"])
        self.assertEqual(out["decision"], "NO GO")

    def test_all_synthetic_rehearsals_still_not_verified(self):
        data = fixture()
        for gate in data["externalGates"]:
            gate["status"] = "synthetic_rehearsal"
        out = validate(data)
        self.assertEqual(out["externallyVerifiedControls"], 0)
        self.assertEqual(len(out["syntheticallyRehearsedControls"]), 12)
        self.assertFalse(out["independentStudyExecuted"])

    def test_one_synthetic_rehearsal_only_counts_as_rehearsal(self):
        data = fixture()
        data["externalGates"][0]["status"] = "synthetic_rehearsal"
        out = validate(data)
        self.assertEqual(out["syntheticallyRehearsedControls"], [GATES[0]])
        self.assertEqual(out["unverifiedControls"], list(GATES))

    def test_reject_fake_verified_gate(self):
        data = fixture()
        data["externalGates"][0]["status"] = "verified"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_private_evidence_reference(self):
        data = fixture()
        data["externalGates"][0]["evidenceReference"] = "private://document"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_unverified_reviewer_identity(self):
        data = fixture()
        data["externalGates"][0]["verifiedBy"] = "SIM-REVIEWER"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_missing_or_duplicated_gate(self):
        data = fixture()
        data["externalGates"].pop()
        with self.assertRaises(ValueError):
            validate(data)
        data = fixture()
        data["externalGates"][1]["id"] = data["externalGates"][0]["id"]
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_unexpected_gate_id(self):
        data = fixture()
        data["externalGates"][0]["id"] = "operational_release"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_fake_frozen_protocol(self):
        data = fixture()
        data["plan"]["preRegistrationStatus"] = "frozen_and_signed"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_fake_completed_blinding(self):
        data = fixture()
        data["plan"]["blinding"] = "human_review_completed"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_public_oracle(self):
        data = fixture()
        data["plan"]["oracleLocation"] = "github_repo_public"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_critical_error_rule_relaxation(self):
        data = fixture()
        data["plan"]["safetyStopRule"] = "allow_two_critical_errors"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_missing_critical_error(self):
        data = fixture()
        data["plan"]["criticalErrorCategories"].pop()
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_duplicate_critical_error(self):
        data = fixture()
        data["plan"]["criticalErrorCategories"][1] = CRITICAL_ERRORS[0]
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_wrong_denominator(self):
        data = fixture()
        data["plan"]["metricDenominators"]["abstention_rate"] = "only_answered_cases"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_missing_metric(self):
        data = fixture()
        del data["plan"]["metricDenominators"][METRICS[0]]
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_real_participants_or_cases(self):
        data = fixture()
        data["plan"]["realWorldDataUsed"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_invalid_case_counts(self):
        for count in (1, 51, True, 12.0):
            data = fixture()
            data["plan"]["caseCount"] = count
            with self.subTest(count=count), self.assertRaises(ValueError):
                validate(data)

    def test_reject_forged_reviewer_or_adjudicator_count(self):
        for field, value in [("reviewerCount", 1), ("adjudicatorCount", 2),
                             ("reviewerCount", True)]:
            data = fixture()
            data["plan"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(data)

    def test_reject_authority_promotion(self):
        for key in DENIED:
            data = fixture()
            data["claims"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(data)

    def test_reject_upstream_approval(self):
        data = fixture()
        data["reviewLedger"]["claims"]["humanReviewCompleted"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_non_conflicted_study(self):
        data = fixture()
        data["reviewLedger"] = ledger_fixture(with_conflict=False)
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_unknown_fields(self):
        data = fixture()
        data["plan"]["authorizedAt"] = "2026-11-08"
        with self.assertRaises(ValueError):
            validate(data)

    def test_input_not_mutated(self):
        data = fixture()
        original = copy.deepcopy(data)
        validate(data)
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()
