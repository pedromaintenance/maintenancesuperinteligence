"""C68: path filters and synthetic public interfaces remain fail-closed."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.cycle68_integration_gate import audit, _triggers

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "cycle68-research-interfaces.v1.json"
INVENTORY = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"


def fixture():
    return (json.loads(CONTRACT.read_text(encoding="utf-8")),
            json.loads(INVENTORY.read_text(encoding="utf-8")))


class IntegrationGateTests(unittest.TestCase):
    def test_nine_interfaces_and_all_direct_edges(self):
        contract, inventory = fixture()
        result = audit(ROOT, contract, inventory)
        self.assertEqual(result["integrationContractStatus"], "pass",
                         result["structuralErrors"])
        self.assertEqual(result["contractsAudited"], 9)
        self.assertEqual(result["directDependencyEdgesCheckedPerEvent"], 8)
        self.assertEqual(result["triggerPathChecks"], 68)
        self.assertTrue(all(s["syntheticFixture"] == "NO GO" for s in result["cycles"]))
        self.assertFalse(result["readyForMerge"])
        self.assertEqual(result["decision"], "NO GO")

    def test_repaired_path_filters_have_two_events(self):
        contract, inventory = fixture()
        result = audit(ROOT, contract, inventory, run_fixtures=False)
        self.assertEqual(result["structuralErrors"], [])
        self.assertTrue(all(len(row["workflowEventsChecked"]) == 2
                            for row in result["cycles"]))

    def test_remove_upstream_code_from_push_blocks_audit(self):
        contract, inventory = fixture()
        workflow = inventory["inventory"][4]["workflow"]
        text = (ROOT / workflow).read_text(encoding="utf-8")
        old = "      - 'benchmarks/cycle60_metrology.py'\n"
        self.assertEqual(text.count(old), 2)
        corrupted = text.replace(old, "", 1)
        report = audit(ROOT, contract, inventory, overrides={workflow: corrupted},
                       run_fixtures=False)
        self.assertEqual(report["integrationContractStatus"], "fail")
        self.assertTrue(any("missing upstream 60 push" in e
                            for e in report["structuralErrors"]))

    def test_remove_upstream_test_from_pull_request_blocks_audit(self):
        contract, inventory = fixture()
        workflow = inventory["inventory"][6]["workflow"]
        text = (ROOT / workflow).read_text(encoding="utf-8")
        marker = "      - 'tests/test_cycle63_effectivity.py'\n"
        self.assertEqual(text.count(marker), 2)
        prefix, suffix = text.split("  pull_request:\n", 1)
        corrupted = prefix + "  pull_request:\n" + suffix.replace(marker, "", 1)
        report = audit(ROOT, contract, inventory, overrides={workflow: corrupted},
                       run_fixtures=False)
        self.assertTrue(any("missing upstream 63 pull_request" in e
                            for e in report["structuralErrors"]))

    def test_unknown_schema_does_not_claim_pass(self):
        contract, inventory = fixture()
        contract["researchStages"][0]["resultSchema"] = "fake.promoted.v1"
        result = audit(ROOT, contract, inventory)
        self.assertEqual(result["integrationContractStatus"], "fail")
        self.assertFalse(result["operationalAuthorityGranted"])

    def test_fabricated_approval_denied_at_contract_boundary(self):
        contract, inventory = fixture()
        contract["authority"]["mayWriteSap"] = True
        with self.assertRaises(ValueError):
            audit(ROOT, contract, inventory, run_fixtures=False)

    def test_false_authority_in_module_response_is_rejected(self):
        contract, inventory = fixture()
        with patch("benchmarks.cycle68_integration_gate._output_check",
                   side_effect=ValueError("simulated GO is prohibited")):
            result = audit(ROOT, contract, inventory)
        self.assertEqual(result["integrationContractStatus"], "fail")
        self.assertTrue(any("simulated GO" in e for e in result["structuralErrors"]))

    def test_missing_stage_is_not_silently_ignored(self):
        contract, inventory = fixture()
        contract["researchStages"].pop()
        with self.assertRaises(ValueError):
            audit(ROOT, contract, inventory, run_fixtures=False)

    def test_wrong_domain_rejected(self):
        contract, inventory = fixture()
        contract["researchStages"][5]["domain"] = "oem_homologated"
        with self.assertRaises(ValueError):
            audit(ROOT, contract, inventory, run_fixtures=False)

    def test_wrong_own_module_rejected(self):
        contract, inventory = fixture()
        contract["researchStages"][6]["module"] = "benchmarks.real_sap_writer"
        with self.assertRaises(ValueError):
            audit(ROOT, contract, inventory, run_fixtures=False)

    def test_incorrect_result_type_fails(self):
        contract, inventory = fixture()
        contract["researchStages"][2]["outputFields"]["intervalsOverlap"] = "str"
        result = audit(ROOT, contract, inventory)
        self.assertEqual(result["integrationContractStatus"], "fail")
        self.assertTrue(any("changed type" in e for e in result["structuralErrors"]))

    def test_trigger_parser_refuses_unfiltered_workflow(self):
        self.assertIsNone(_triggers("on:\n  push:\n  pull_request:\n", "push"))

    def test_input_objects_unchanged(self):
        contract, inventory = fixture()
        old_contract, old_inventory = copy.deepcopy(contract), copy.deepcopy(inventory)
        audit(ROOT, contract, inventory, run_fixtures=False)
        self.assertEqual(contract, old_contract)
        self.assertEqual(inventory, old_inventory)

    def test_manifest_never_claims_operational_readiness(self):
        contract, inventory = fixture()
        result = audit(ROOT, contract, inventory, run_fixtures=False)
        self.assertFalse(result["mechanicalAccuracyValidated"])
        self.assertFalse(result["independentExpertReviewCompleted"])
        self.assertEqual(result["decision"], "NO GO")


if __name__ == "__main__":
    unittest.main()
