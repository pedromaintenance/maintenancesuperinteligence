"""Negative and positive structural contract checks for Cycle 58 (synthetic only)."""
import copy
import unittest

from benchmarks.cycle58_causal_gate import validate, CLAIMS_DENIED, SCHEMA


def sample():
    return {
        "schema": SCHEMA, "caseId": "HLD-901",
        "origin": "synthetic_training_only",
        "context": {
            "requiredFunction": "Transmitir energia mecânica entre conjuntos simulados.",
            "observedSymptom": "Oscilação fictícia de desempenho sob uma carga simulada.",
            "operatingCondition": "Cenário inteiramente inventado, sem equipamento real."
        },
        "hypotheses": [
            {"id": "loss_a", "mechanism": "Perda de transmissão fictícia no caminho A.",
             "counterEvidence": "Integridade do caminho A contradiz esta hipótese.",
             "uncertainty": "unconfirmed"},
            {"id": "loss_b", "mechanism": "Perda de transmissão fictícia no caminho B.",
             "counterEvidence": "Integridade do caminho B contradiz esta hipótese.",
             "uncertainty": "unconfirmed"}
        ],
        "proposedChecks": [{
            "id": "compare_paths", "method": "Comparar registros simulados e procurar contradições.",
            "kind": "document_review", "safeToPerform": False,
            "requiresApplicableProcedure": True,
            "predictions": [
                {"hypothesisId": "loss_a", "expectation": "supports",
                 "reason": "Padrão A seria compatível com perda no caminho A."},
                {"hypothesisId": "loss_b", "expectation": "contradicts",
                 "reason": "Padrão A seria incompatível com perda no caminho B."}
            ]
        }],
        "claims": {key: False for key in CLAIMS_DENIED}
    }


class CausalGateTests(unittest.TestCase):
    def test_synthetic_sample_remains_no_go(self):
        out = validate(sample())
        self.assertEqual(out["result"], "structural_pass_no_diagnostic_validation")
        self.assertEqual(out["discriminatingChecks"], 1)
        self.assertEqual(out["decision"], "NO GO")
        self.assertFalse(out["independentExpertReviewCompleted"])

    def test_reject_claim_promotion(self):
        for claim in CLAIMS_DENIED:
            with self.subTest(claim=claim):
                data = sample()
                data["claims"][claim] = True
                with self.assertRaises(ValueError):
                    validate(data)

    def test_reject_unknown_or_restricted_origin(self):
        for value in ("authorized_restricted_case", "field_case", "synthetic_training_only "):
            with self.subTest(origin=value):
                data = sample()
                data["origin"] = value
                with self.assertRaises(ValueError):
                    validate(data)

    def test_reject_one_hypothesis(self):
        data = sample()
        data["hypotheses"].pop()
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_fake_discriminator(self):
        data = sample()
        data["proposedChecks"][0]["predictions"][1]["expectation"] = "supports"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_missing_prediction(self):
        data = sample()
        data["proposedChecks"][0]["predictions"].pop()
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_duplicate_hypothesis(self):
        data = sample()
        data["hypotheses"][1]["id"] = "loss_a"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_missing_counterevidence(self):
        data = sample()
        del data["hypotheses"][0]["counterEvidence"]
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_performance_of_unapproved_test(self):
        data = sample()
        data["proposedChecks"][0]["safeToPerform"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_asserted_cause(self):
        data = sample()
        data["hypotheses"][0]["uncertainty"] = "confirmed"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_unexpected_operational_field(self):
        data = sample()
        data["executeSapOrder"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_reviewer_role_forgery(self):
        data = sample()
        data["claims"]["humanReviewerSigned"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_input_not_modified(self):
        data = sample()
        before = copy.deepcopy(data)
        validate(data)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
