"""Cycle 60 unit conversions and denial boundaries (synthetic only)."""
import copy
import math
import unittest

from benchmarks.cycle60_metrology import DENIED, validate


def fixture(formula="hydraulic_power"):
    if formula == "hydraulic_power":
        data = [("input_a", "bar", 10, 0), ("input_b", "L/min", 60, 0),
                ("reported_result", "kW", 1, 0)]
    else:
        data = [("input_a", "N*m", 100, 0), ("input_b", "rpm", 60, 0),
                ("reported_result", "W", 200 * math.pi, 0)]
    return {
        "schema": "maintenance-superinteligence.synthetic-metrology.v1",
        "caseId": "SYN-601", "origin": "synthetic_training_only",
        "formula": formula,
        "quantities": [
            {"role": role, "unit": unit, "value": value,
             "absoluteUncertainty": uncertainty, "nature": "invented_example_only"}
            for role, unit, value, uncertainty in data
        ],
        "claims": {key: False for key in DENIED},
    }


class MetrologyTests(unittest.TestCase):
    def test_hydraulic_power_unit_conversion(self):
        r = validate(fixture())
        self.assertAlmostEqual(r["predictedSIInterval"][0], 1000)
        self.assertTrue(r["intervalsOverlap"])
        self.assertEqual(r["decision"], "NO GO")

    def test_shaft_power_angular_conversion(self):
        r = validate(fixture("shaft_power"))
        self.assertAlmostEqual(r["predictedSIInterval"][0], 200 * math.pi)
        self.assertTrue(r["intervalsOverlap"])

    def test_disjoint_intervals_are_only_documentary_conflict(self):
        p = fixture()
        p["quantities"][2]["value"] = 5
        r = validate(p)
        self.assertFalse(r["intervalsOverlap"])
        self.assertFalse(r["realMeasurementVerified"])

    def test_uncertainty_worst_case_bounds(self):
        p = fixture()
        p["quantities"][0]["absoluteUncertainty"] = 1
        p["quantities"][1]["absoluteUncertainty"] = 6
        r = validate(p)
        self.assertAlmostEqual(r["predictedSIInterval"][0], 810)
        self.assertAlmostEqual(r["predictedSIInterval"][1], 1210)

    def test_compatible_units_are_not_arbitrarily_interchangeable(self):
        p = fixture()
        p["quantities"][0]["unit"] = "kW"
        with self.assertRaisesRegex(ValueError, "dimension mismatch"):
            validate(p)

    def test_reject_real_world_measurement_claim(self):
        p = fixture()
        p["quantities"][0]["nature"] = "actual_telemetry"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_negative_or_invalid_uncertainty(self):
        for number in (-1, 11, float("nan"), float("inf"), "1", True):
            p = fixture()
            p["quantities"][0]["absoluteUncertainty"] = number
            with self.subTest(number=repr(number)), self.assertRaises(ValueError):
                validate(p)

    def test_reject_negative_values(self):
        p = fixture()
        p["quantities"][1]["value"] = -1
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_unknown_formula(self):
        p = fixture()
        p["formula"] = "efficiency"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_duplicate_roles(self):
        p = fixture()
        p["quantities"][2]["role"] = "input_a"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_operational_claims(self):
        for key in DENIED:
            p = fixture()
            p["claims"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(p)

    def test_reject_restricted_origin(self):
        p = fixture()
        p["origin"] = "authorized_restricted_case"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_unknown_field(self):
        p = fixture()
        p["quantities"][0]["sensorSerial"] = "private"
        with self.assertRaises(ValueError):
            validate(p)

    def test_no_mutation(self):
        p = fixture()
        before = copy.deepcopy(p)
        validate(p)
        self.assertEqual(p, before)


if __name__ == "__main__":
    unittest.main()
