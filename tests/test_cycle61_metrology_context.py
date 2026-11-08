"""Cycle 61: regression of synthetic context and provenance; never field evidence."""
import copy
import unittest

from benchmarks.cycle61_metrology_context import DENIED, validate
from tests.test_cycle60_metrology import fixture as c60_fixture


def fixture(nominal=False):
    base = c60_fixture()
    for q in base["quantities"]:
        q["absoluteUncertainty"] = 0.1
    context = {"scenarioId": "SIM-CASE601", "loadState": "steady_load",
               "thermalState": "stabilized", "samplingWindow": "SIM-WINDOW601"}
    records = []
    for role in ("input_a", "input_b", "reported_result"):
        is_target = nominal and role == "reported_result"
        records.append({
            "role": role,
            "nature": "invented_nominal_target" if is_target else "invented_observation",
            "context": dict(context),
            "instrument": {
                "syntheticId": None if is_target else
                {"input_a": "SIM-GAUGE1", "input_b": "SIM-FLOWM1",
                 "reported_result": "SIM-POWER1"}[role],
                "calibrationStatus": "unverified_synthetic",
                "calibrationEvidence": None
            },
            "resolution": 0.1,
            "uncertaintyModel": "declared_target_band" if is_target else
            "declared_absolute_bound"
        })
    return {
        "schema": "maintenance-superinteligence.synthetic-metrology-context.v1",
        "metrologyCase": base, "records": records,
        "claims": {k: False for k in DENIED}
    }


class ContextTests(unittest.TestCase):
    def test_compatible_fictional_observations(self):
        out = validate(fixture())
        self.assertTrue(out["comparisonAllowed"])
        self.assertTrue(out["reportedIntervalOverlap"])
        self.assertEqual(out["decision"], "NO GO")
        self.assertFalse(out["calibrationVerified"])

    def test_context_mismatch_prevents_comparison(self):
        p = fixture()
        p["records"][1]["context"]["loadState"] = "idle"
        out = validate(p)
        self.assertFalse(out["comparisonAllowed"])
        self.assertIsNone(out["reportedIntervalOverlap"])
        self.assertIn("operating_context_mismatch", out["reasonCodes"])

    def test_sampling_window_mismatch(self):
        p = fixture()
        p["records"][2]["context"]["samplingWindow"] = "SIM-WINDOW999"
        self.assertFalse(validate(p)["comparisonAllowed"])

    def test_nominal_target_cannot_be_real_observation(self):
        out = validate(fixture(nominal=True))
        self.assertFalse(out["resultIsFictionalObservation"])
        self.assertFalse(out["comparisonAllowed"])
        self.assertIsNone(out["reportedIntervalOverlap"])
        self.assertIn("nominal_target_is_not_observed_result", out["reasonCodes"])

    def test_reject_calibration_certificate_claim(self):
        p = fixture()
        p["records"][0]["instrument"]["calibrationEvidence"] = "CERT-1234"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_real_calibration_status(self):
        p = fixture()
        p["records"][0]["instrument"]["calibrationStatus"] = "verified"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_insufficient_uncertainty_for_resolution(self):
        p = fixture()
        p["records"][0]["resolution"] = 0.5
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_zero_resolution(self):
        p = fixture()
        p["records"][0]["resolution"] = 0
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_nominal_reference_disguised_as_instrument(self):
        p = fixture(nominal=True)
        p["records"][2]["instrument"]["syntheticId"] = "SIM-SENSOR1"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_missing_instrument_identity(self):
        p = fixture()
        p["records"][1]["instrument"]["syntheticId"] = None
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_fake_authority(self):
        for key in DENIED:
            p = fixture()
            p["claims"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(p)

    def test_reject_unknown_context_status(self):
        p = fixture()
        p["records"][0]["context"]["loadState"] = "field_load"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_extra_operational_field(self):
        p = fixture()
        p["records"][0]["fieldMachineId"] = "CAT-777"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_duplicate_roles(self):
        p = fixture()
        p["records"][2]["role"] = "input_a"
        with self.assertRaises(ValueError):
            validate(p)

    def test_does_not_mutate_input(self):
        p = fixture()
        frozen = copy.deepcopy(p)
        validate(p)
        self.assertEqual(p, frozen)


if __name__ == "__main__":
    unittest.main()
