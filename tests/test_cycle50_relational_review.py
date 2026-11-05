"""Cycle 50 — cross-object guard checks; author-written synthetic fixtures only."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from governance import cycle50_relational_review as c50
from governance import cycle49_contract_integration as c49
from pilot.change_review_packets import ReviewRejected


class Cycle50RelationalReviewTests(unittest.TestCase):
    def test_eight_relational_guards_reject_schema_valid_mutations(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("Pinned jsonschema installed by dedicated workflow")
        rows = c50.relational_review()
        self.assertEqual(len(rows), 8)
        self.assertEqual([x["probeId"] for x in rows], list(c50.CHECK_IDS))
        self.assertEqual(len({x["probeId"] for x in rows}), 8)
        self.assertTrue(all(x["syntheticStructuralSchemaAccepted"]
                            and x["relationalRuntimeValidatorRejected"]
                            and x["requiresBothValidationLayers"]
                            and not x["usesRealCases"]
                            and not x["humanApprovalClaimed"]
                            for x in rows))

    def test_cycle49_report_tampering_is_detected_by_recomputation(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("Pinned jsonschema installed by dedicated workflow")
        baseline, mutations = c50.report_integrity_review()
        self.assertTrue(c49.verify_report(baseline))
        self.assertEqual([x["probeId"] for x in mutations],
                         list(c50.TAMPER_IDS))
        self.assertTrue(all(x["syntheticStructuralSchemaAccepted"]
                            and x["recomputedReportRejected"]
                            and not x["independentlyAuthenticated"]
                            for x in mutations))

    def test_separate_coverage_and_relational_gate_are_never_authority(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("Pinned jsonschema installed by dedicated workflow")
        report = c50.evaluate()
        self.assertEqual(report["relationalProbeCount"], 8)
        self.assertEqual(report["relationalRuntimeRejectedCount"], 8)
        self.assertEqual(report["relationalSchemaAcceptedCount"], 8)
        self.assertEqual(report["reportTamperProbeCount"], 3)
        self.assertEqual(report["reportTamperRejectedCount"], 3)
        self.assertEqual(report["remainingExternalStudyGates"], 13)
        for key in c50.FALSE_FLAGS:
            self.assertIs(report[key], False, key)
        self.assertEqual(
            report["decision"],
            "no_go_relational_integrity_is_not_external_validation",
        )
        self.assertTrue(c50.verify_report(report))
        schema = json.loads(
            (c49.ROOT / "contracts/cycle50-relational-review.schema.json")
            .read_text(encoding="utf-8")
        )
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(report)

    def test_reject_forged_external_approval_and_fake_probe_counts(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Pinned jsonschema installed by dedicated workflow")
        report = c50.evaluate()
        spec = json.loads(
            (c49.ROOT / "contracts/cycle50-relational-review.schema.json")
            .read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(spec)
        changes = [
            ("mayWriteSAP", True),
            ("mayReleaseEquipment", True),
            ("independentCodeReviewVerified", True),
            ("mechanicalDiagnosticAccuracyEstablished", True),
            ("mayStartHumanStudy", True),
            ("relationalProbeCount", 7),
            ("remainingExternalStudyGates", 0),
            ("decision", "approved_for_real_field_study"),
        ]
        for key, val in changes:
            modified = copy.deepcopy(report)
            modified[key] = val
            with self.subTest(key=key):
                self.assertGreater(len(list(validator.iter_errors(modified))), 0)
                with self.assertRaises(ReviewRejected):
                    c50.verify_report(modified)

    def test_cli_exports_only_aggregates_and_is_reproducible(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("Pinned jsonschema installed by dedicated workflow")
        with tempfile.TemporaryDirectory() as folder:
            json_path = Path(folder) / "c50.json"
            md_path = Path(folder) / "c50.md"
            report = c50.cli([
                "--output", str(json_path), "--markdown", str(md_path)
            ])
            self.assertEqual(
                json.loads(json_path.read_text(encoding="utf-8")), report
            )
            self.assertTrue(c50.verify_report(report))
            self.assertIn("NO GO", md_path.read_text(encoding="utf-8"))
            text = json_path.read_text(encoding="utf-8")
            for term in ("HLD-001", "questionA", "questionB",
                         "armMapping", "reviewerAlias", "custodianKey"):
                self.assertNotIn(term, text)


if __name__ == "__main__":
    unittest.main()
