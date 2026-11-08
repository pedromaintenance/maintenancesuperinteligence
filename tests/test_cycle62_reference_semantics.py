"""Cycle 62: semantic reference comparisons are never equipment decisions."""
import copy
import unittest

from benchmarks.cycle62_reference_semantics import DENIED, validate
from tests.test_cycle61_metrology_context import fixture as context_fixture


def ref(kind="expected_operating_band"):
    base = {
        "id": "SIM-REF001", "kind": kind, "unit": "kW",
        "source": {"origin": "invented_training_source", "documentId": "SIM-DOC001",
                   "revision": "SYNTHETIC", "effectivityVerified": False},
        "applicability": {"scenarioId": "SIM-CASE601", "loadState": "steady_load",
                          "thermalState": "stabilized", "samplingWindow": "SIM-WINDOW601"},
        "range": {"lower": 0.8, "upper": 1.2}, "direction": None
    }
    if kind == "nominal_target":
        base["range"] = {"value": 1.0}
    if kind in ("alarm_threshold", "safety_threshold"):
        base["range"] = {"value": 1.1}
        base["direction"] = "above"
    return base


def fixture(kind="expected_operating_band"):
    return {"schema": "maintenance-superinteligence.synthetic-reference-comparison.v1",
            "contextCase": context_fixture(), "references": [ref(kind)],
            "claims": {k: False for k in DENIED}}


class ReferenceTests(unittest.TestCase):
    def test_expected_band_inside_not_acceptance(self):
        out = validate(fixture())
        self.assertEqual(out["comparisons"][0]["mathematicalRelation"],
                         "entirely_within_reference")
        self.assertFalse(out["acceptanceOrRejectionIssued"])
        self.assertEqual(out["decision"], "NO GO")

    def test_acceptance_band_not_maintenance_decision(self):
        out = validate(fixture("acceptance_band"))
        self.assertEqual(out["comparisons"][0]["referenceKind"], "acceptance_band")
        self.assertFalse(out["maintenanceDecisionAuthorized"])

    def test_nominal_is_point_not_range(self):
        out = validate(fixture("nominal_target"))
        self.assertEqual(out["comparisons"][0]["mathematicalRelation"],
                         "partially_overlapping_reference")

    def test_alarm_is_only_mathematical_threshold(self):
        out = validate(fixture("alarm_threshold"))
        self.assertEqual(out["comparisons"][0]["mathematicalRelation"],
                         "entirely_not_beyond_threshold")
        self.assertFalse(out["actualAlarmEvaluated"])

    def test_crossing_uncertainty_is_not_severity(self):
        data = fixture("safety_threshold")
        data["references"][0]["range"]["value"] = 1.0
        out = validate(data)
        self.assertEqual(out["comparisons"][0]["mathematicalRelation"],
                         "threshold_crossing_uncertain")
        self.assertFalse(out["actualSafetyLimitEvaluated"])

    def test_below_threshold_direction(self):
        data = fixture("alarm_threshold")
        data["references"][0]["direction"] = "below"
        data["references"][0]["range"]["value"] = 1.2
        self.assertEqual(validate(data)["comparisons"][0]["mathematicalRelation"],
                         "entirely_beyond_threshold")

    def test_dimension_mismatch_rejected(self):
        data = fixture()
        data["references"][0]["unit"] = "bar"
        with self.assertRaises(ValueError):
            validate(data)

    def test_inverted_band_rejected(self):
        data = fixture()
        data["references"][0]["range"] = {"lower": 2.0, "upper": 1.0}
        with self.assertRaises(ValueError):
            validate(data)

    def test_incompatible_context_rejected(self):
        data = fixture()
        data["references"][0]["applicability"]["loadState"] = "idle"
        with self.assertRaises(ValueError):
            validate(data)

    def test_unverified_oem_claim_rejected(self):
        data = fixture()
        data["references"][0]["source"]["effectivityVerified"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_fake_source_rejected(self):
        data = fixture()
        data["references"][0]["source"]["origin"] = "oem_private_manual"
        with self.assertRaises(ValueError):
            validate(data)

    def test_nominal_cannot_have_alarm_direction(self):
        data = fixture("nominal_target")
        data["references"][0]["direction"] = "above"
        with self.assertRaises(ValueError):
            validate(data)

    def test_alarm_requires_direction(self):
        data = fixture("alarm_threshold")
        data["references"][0]["direction"] = None
        with self.assertRaises(ValueError):
            validate(data)

    def test_reference_nature_not_measured_observation(self):
        data = fixture()
        data["contextCase"] = context_fixture(nominal=True)
        with self.assertRaises(ValueError):
            validate(data)

    def test_unique_reference_ids(self):
        data = fixture()
        data["references"].append(copy.deepcopy(data["references"][0]))
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_authority_promotion(self):
        for k in DENIED:
            data = fixture()
            data["claims"][k] = True
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate(data)

    def test_reject_unknown_field(self):
        data = fixture()
        data["references"][0]["sendSapOrder"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_inputs_not_mutated(self):
        data = fixture()
        old = copy.deepcopy(data)
        validate(data)
        self.assertEqual(data, old)


if __name__ == "__main__":
    unittest.main()
