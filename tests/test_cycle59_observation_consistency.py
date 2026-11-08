"""Adversarial tests of fictional record consistency; no real mechanics scored."""
import copy
import unittest

from benchmarks.cycle58_causal_gate import CLAIMS_DENIED
from benchmarks.cycle59_observation_consistency import DENIED, SCHEMA, validate
from tests.test_cycle58_causal_gate import sample


def fixture():
    return {
        "schema": SCHEMA,
        "causalCase": sample(),
        "observations": [{
            "id": "obs_record_001",
            "checkId": "compare_paths",
            "nature": "synthetic_fictional_record",
            "sourceStatus": "unverified_synthetic",
            "recordedOutcome": "pattern_a",
            "recordedText": "Dados completamente inventados exibem um padrão A de treinamento.",
            "predictedOutcomes": [
                {"hypothesisId": "loss_a", "interpretation": "supports",
                 "reason": "O padrão fictício é coerente com a previsão textual A."},
                {"hypothesisId": "loss_b", "interpretation": "contradicts",
                 "reason": "O padrão fictício contraria a previsão textual B."}
            ]
        }],
        "claims": {key: False for key in DENIED}
    }


class ObservationConsistencyTest(unittest.TestCase):
    def test_all_labels_agree_but_not_mechanical_accuracy(self):
        result = validate(fixture())
        self.assertEqual(result["labelConflicts"], 0)
        self.assertEqual(result["labelComparisons"], 2)
        self.assertFalse(result["mechanicalValidityValidated"])
        self.assertEqual(result["decision"], "NO GO")

    def test_conflict_is_reported_not_causal_proof(self):
        data = fixture()
        data["observations"][0]["predictedOutcomes"][0]["interpretation"] = "contradicts"
        result = validate(data)
        self.assertEqual(result["labelConflicts"], 1)
        self.assertEqual(result["conflictReferences"][0]["hypothesisId"], "loss_a")
        self.assertFalse(result["causeConfirmed"])

    def test_indeterminate_not_counted_as_direct_opposition(self):
        data = fixture()
        data["observations"][0]["predictedOutcomes"][0]["interpretation"] = "indeterminate"
        self.assertEqual(validate(data)["labelConflicts"], 0)

    def test_reject_observed_claims_as_real(self):
        for nature, status in [("field_measurement", "unverified_synthetic"),
                               ("synthetic_fictional_record", "verified_oem")]:
            data = fixture()
            data["observations"][0]["nature"] = nature
            data["observations"][0]["sourceStatus"] = status
            with self.assertRaises(ValueError):
                validate(data)

    def test_reject_false_promotions(self):
        for key in DENIED:
            data = fixture()
            data["claims"][key] = True
            with self.subTest(field=key), self.assertRaises(ValueError):
                validate(data)

    def test_reject_unverified_causal_claims_from_previous_gate(self):
        data = fixture()
        data["causalCase"]["claims"][CLAIMS_DENIED[0]] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_missing_hypothesis_interpretation(self):
        data = fixture()
        data["observations"][0]["predictedOutcomes"].pop()
        with self.assertRaises(ValueError):
            validate(data)

    def test_unknown_check(self):
        data = fixture()
        data["observations"][0]["checkId"] = "unknown_check"
        with self.assertRaises(ValueError):
            validate(data)

    def test_duplicate_observation_id(self):
        data = fixture()
        data["observations"].append(copy.deepcopy(data["observations"][0]))
        with self.assertRaises(ValueError):
            validate(data)

    def test_duplicate_check_with_distinct_id(self):
        data = fixture()
        extra = copy.deepcopy(data["observations"][0])
        extra["id"] = "obs_record_002"
        data["observations"].append(extra)
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_unexpected_operational_instruction(self):
        data = fixture()
        data["observations"][0]["executeTest"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_do_not_mutate_input(self):
        data = fixture()
        frozen = copy.deepcopy(data)
        validate(data)
        self.assertEqual(data, frozen)


if __name__ == "__main__":
    unittest.main()
