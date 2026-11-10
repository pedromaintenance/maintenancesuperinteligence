"""Cycle 63 regression: fabricated metadata match is not OEM effectivity."""
import copy
import unittest

from benchmarks.cycle63_effectivity import ATTRS, DENIED, validate
from tests.test_cycle62_reference_semantics import fixture as reference_fixture


def fixture():
    cfg = {
        "manufacturer": "SIM-OEMA",
        "model": "SIM-MODEL7",
        "arrangement": "SIM-ARR01",
        "component": "SIM-PUMP1",
        "configuration": "SIM-CONF1",
        "softwareRevision": "SIM-SOFT1",
    }
    return {
        "schema": "maintenance-superinteligence.synthetic-effectivity.v1",
        "referenceCase": reference_fixture(),
        "asset": {
            "configuration": dict(cfg),
            "serial": {"prefix": "SIM-ABC", "number": 500},
            "nature": "invented_asset_only"
        },
        "effectivities": [{
            "referenceId": "SIM-REF001",
            "configuration": dict(cfg),
            "serialRange": {"prefix": "SIM-ABC", "start": 400, "end": 600},
            "sourceRevision": "SYNTHETIC",
            "sourceStatus": "unverified_synthetic",
            "oemVerified": False,
        }],
        "claims": {key: False for key in DENIED}
    }


class EffectivityTests(unittest.TestCase):
    def test_all_fields_match_still_no_go(self):
        out = validate(fixture())
        self.assertTrue(out["results"][0]["metadataMatch"])
        self.assertFalse(out["oemEffectivityVerified"])
        self.assertFalse(out["referenceApproved"])
        self.assertEqual(out["decision"], "NO GO")

    def test_each_configuration_field_discriminates(self):
        for field in ATTRS:
            data = fixture()
            data["effectivities"][0]["configuration"][field] = "SIM-OTHER1"
            with self.subTest(field=field):
                out = validate(data)
                self.assertFalse(out["results"][0]["metadataMatch"])
                self.assertIn(field + "_mismatch", out["results"][0]["mismatchReasons"])

    def test_serial_boundaries_inclusive(self):
        for number in (400, 600):
            data = fixture()
            data["asset"]["serial"]["number"] = number
            with self.subTest(number=number):
                self.assertTrue(validate(data)["results"][0]["metadataMatch"])

    def test_serial_outside_range(self):
        data = fixture()
        data["asset"]["serial"]["number"] = 601
        out = validate(data)
        self.assertIn("serial_number_outside_declared_range",
                      out["results"][0]["mismatchReasons"])

    def test_prefix_mismatch_even_with_matching_number(self):
        data = fixture()
        data["asset"]["serial"]["prefix"] = "SIM-XYZ"
        out = validate(data)
        self.assertIn("serial_prefix_mismatch", out["results"][0]["mismatchReasons"])

    def test_inverted_serial_range_rejected(self):
        data = fixture()
        data["effectivities"][0]["serialRange"]["start"] = 601
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_boolean_serial_number(self):
        data = fixture()
        data["asset"]["serial"]["number"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_claim_of_oem_confirmation(self):
        data = fixture()
        data["effectivities"][0]["oemVerified"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_source_revision_promotion(self):
        data = fixture()
        data["effectivities"][0]["sourceRevision"] = "OEM-APPROVED"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_authentic_machine_identity(self):
        data = fixture()
        data["asset"]["nature"] = "real_cat_equipment"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_private_serial_prefix(self):
        data = fixture()
        data["asset"]["serial"]["prefix"] = "KYD"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_unknown_reference(self):
        data = fixture()
        data["effectivities"][0]["referenceId"] = "SIM-REF999"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_duplicate_effectivity(self):
        data = fixture()
        data["effectivities"].append(copy.deepcopy(data["effectivities"][0]))
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_missing_effectivity(self):
        data = fixture()
        data["effectivities"].clear()
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_claim_promotions(self):
        for field in DENIED:
            data = fixture()
            data["claims"][field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(data)

    def test_reject_unexpected_operational_field(self):
        data = fixture()
        data["asset"]["sapFunctionalLocation"] = "INTERNAL"
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_underlying_reference_authority(self):
        data = fixture()
        data["referenceCase"]["references"][0]["source"]["effectivityVerified"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_no_mutation(self):
        data = fixture()
        snapshot = copy.deepcopy(data)
        validate(data)
        self.assertEqual(data, snapshot)


if __name__ == "__main__":
    unittest.main()
