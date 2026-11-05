"""Cycle 49: cross-cycle executable schemas; all inputs are synthetic in memory."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from governance import cycle49_contract_integration as c49
from pilot.change_review_packets import ReviewRejected


class Cycle49ContractIntegrationTests(unittest.TestCase):
    def test_all_expected_cross_cycle_samples_are_generated_without_real_data(self):
        instances = c49.build_instances()
        self.assertEqual(list(instances), list(c49.CONTRACTS))
        self.assertEqual(len(instances), 16)
        self.assertEqual(instances["cycle44-report"]["fieldMeasurements"], 0)
        self.assertFalse(instances["cycle45-private-review-report"]
                         ["independentMechanicalReviewVerified"])
        self.assertFalse(instances["cycle46-handoff"]
                         ["independentMechanicalReviewCompleted"])
        self.assertFalse(instances["cycle47-readiness-report"]
                         ["humanMaskingValidationPerformed"])
        self.assertFalse(instances["cycle48-readiness-report"]
                         ["studyMayStart"])
        self.assertEqual(instances["cycle48-readiness-report"]
                         ["unverifiedExternalGateCount"], 13)

    def test_no_unregistered_contract_files_can_be_selected(self):
        for name in ("../../README", "cycle50-nonexistent", "README.md",
                     "cycle49-contract-audit"):
            with self.subTest(name=name), self.assertRaises(ReviewRejected):
                c49._contract_path(name)
        for name in c49.CONTRACTS:
            self.assertTrue(c49._contract_path(name).is_file())

    def test_nested_explicit_false_authorities_are_detected(self):
        from tests.test_cycle45_blinded_pairwise import private_fixture
        from benchmarks.cycle45_blinded_pairwise import prepare
        source, candidates, metadata, policy = private_fixture()
        packet, lock, quality = prepare(
            source, candidates, metadata, policy,
            b"temporary-synthetic-key-only-not-for-real-people",
            assignment=["A", "B", "A", "B"],
        )
        schema = json.loads(c49._contract_path(
            "cycle45-reviewer-packet").read_text(encoding="utf-8")
        )
        paths = list(c49._iter_const_false(schema, packet))
        self.assertIn(("mayReleaseEquipment",), paths)
        self.assertIn(("cases", 0, "oemEffectivityVerified"), paths)
        self.assertIn(("cases", 3, "mayReleaseEquipment"), paths)
        changed = c49._mutate_at_path(
            packet, ("cases", 0, "mayReleaseEquipment"), True
        )
        self.assertTrue(changed["cases"][0]["mayReleaseEquipment"])
        self.assertFalse(packet["cases"][0]["mayReleaseEquipment"])

    def test_executable_schema_matrix_rejects_authority_mutations(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("Dedicated CI installs pinned jsonschema for execution")
        report = c49.execute_contract_review()
        self.assertEqual(report["contractCount"], 16)
        self.assertEqual(report["syntheticSamplesAccepted"], 16)
        self.assertGreater(report["mutationsRejected"], 50)
        self.assertEqual([r["contract"] for r in report["checks"]],
                         list(c49.CONTRACTS))
        self.assertEqual(report["decision"],
                         "no_go_contract_alignment_is_not_external_mechanical_validation")
        for name in ("mechanicalDiagnosticAccuracyMeasured",
                     "independentExpertReviewPerformed",
                     "studyMayRecruitParticipants", "studyMayStart",
                     "mayExecuteTests", "mayCreateWorkOrder", "mayWriteSAP",
                     "mayModifyECM", "mayReleaseEquipment"):
            self.assertIs(report[name], False, name)
        self.assertTrue(all(item["acceptedSyntheticSample"] is True and
                            item["realCasesUsed"] is False and
                            item["operationallyApproved"] is False
                            for item in report["checks"]))

    def test_cli_report_matches_schema_and_never_dumps_private_inputs(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Dedicated CI installs pinned jsonschema for execution")
        with tempfile.TemporaryDirectory() as temp:
            j = Path(temp) / "report.json"
            m = Path(temp) / "report.md"
            outcome = c49.cli(["--output", str(j), "--markdown", str(m)])
            self.assertEqual(json.loads(j.read_text(encoding="utf-8")),
                             outcome)
            self.assertIn("NO GO", m.read_text(encoding="utf-8"))
            schema = json.loads(
                (c49.ROOT / "contracts/cycle49-contract-audit.schema.json")
                .read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(outcome)
            output = j.read_text(encoding="utf-8")
            for private_marker in (
                "questionA", "questionB", "reviewerAlias",
                "armMapping", "custodianKey", "HLD-001",
            ):
                self.assertNotIn(private_marker, output)
            self.assertIn("no_go_contract_alignment", output)

    def test_failure_in_critical_report_field_is_rejected_by_schema(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Dedicated CI installs pinned jsonschema for execution")
        schema = json.loads(
            (c49.ROOT / "contracts/cycle49-contract-audit.schema.json")
            .read_text(encoding="utf-8")
        )
        report = c49.execute_contract_review()
        validator = Draft202012Validator(schema)
        for prop, val in (
            ("independentExpertReviewPerformed", True),
            ("mayModifyECM", True),
            ("studyMayStart", True),
            ("decision", "go_independent_validation_confirmed"),
            ("contractCount", 15),
        ):
            changed = copy.deepcopy(report)
            changed[prop] = val
            with self.subTest(prop=prop):
                self.assertGreater(sum(1 for _ in validator.iter_errors(changed)),
                                   0)


if __name__ == "__main__":
    unittest.main()
