"""Cycle 10 — untrusted adapter contract tests: deny all real approvals."""
import copy
import json
from pathlib import Path
import unittest

from connectors.fmea_public import ImportRejected
from governance.integration_contracts import (
    ROOT, validate_fixture, check_policy, evaluate_contract, BLOCKED,
)


class IntegrationContractsTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "governance/integration-policy.v1.json").read_text())
        self.fixture = json.loads((ROOT / "examples/integration-fixture.v1.json").read_text())

    def check(self):
        return validate_fixture(self.fixture, self.policy)

    def output(self):
        return evaluate_contract(self.fixture, self.policy)

    def rejects(self, piece=None):
        with self.assertRaises(ImportRejected) as got:
            self.check()
        if piece:
            self.assertIn(piece, str(got.exception))

    def test_all_eight_contracts_present(self):
        names = (
          "authenticated-principal", "credential-assertion",
          "technical-qualification", "claim-version",
          "independent-review-decision", "evidence-manifest",
          "audit-anchor", "oem-effectivity-attestation")
        for name in names:
            with self.subTest(name=name):
                obj = json.loads((ROOT / "contracts" / (name + ".schema.json")).read_text())
                self.assertEqual(obj["type"], "object")
                self.assertFalse(obj["additionalProperties"])
                self.assertTrue(obj["required"])

    def test_eight_personas_no_approvals(self):
        r = self.output()
        self.assertEqual(r["principalCount"], 8)
        self.assertEqual(r["credentialChecksAuthenticated"], 0)
        self.assertEqual(r["reviewSignaturesVerified"], 0)
        self.assertFalse(r["auditAnchorVerified"])
        self.assertFalse(r["oemSeriesApproved"])
        self.assertFalse(r["mayQualifyRealKnowledge"])
        self.assertFalse(r["mayOpenWorkOrder"])
        self.assertFalse(r["mayChangeEquipment"])
        self.assertEqual(r["approval"], "blocked_missing_private_verified_trust")

    def test_ten_missing_proofs_and_public_deny_all(self):
        r = self.output()
        self.assertEqual(len(r["requiredPrivateProofs"]), 10)
        self.assertTrue(all(x["status"] == "not_implemented"
                            for x in r["requiredPrivateProofs"]))
        self.assertEqual(r["allowedPublicOperations"], [])
        self.assertEqual(set(self.policy["publicActionsAlwaysDenied"]), set(BLOCKED))

    def test_reproducible_contract_report(self):
        self.assertEqual(self.output(), self.output())
        self.assertEqual(len(self.output()["fixtureSha256"]), 64)

    def test_supporting_fictional_votes_does_not_grant_real_conclusion(self):
        self.fixture["independentReviewDecisions"][1]["position"] = "support_general"
        r = self.output()
        self.assertEqual(r["reviewStatus"], "general_consensus_simulation")
        self.assertFalse(r["independentlyReviewedByHumans"])
        self.assertFalse(r["mayQualifyRealKnowledge"])
        self.assertFalse(r["oemSeriesApproved"])

    def test_challenge_is_not_erased(self):
        self.assertEqual(self.output()["reviewStatus"], "disputed_simulation")

    def test_false_authenticated_principal(self):
        self.fixture["principals"][0]["identityAuthenticated"] = True
        self.rejects("falsely authenticated")

    def test_false_verified_server(self):
        self.fixture["principals"][0]["serverVerified"] = True
        self.rejects("falsely authenticated")

    def test_fake_review_authority(self):
        self.fixture["principals"][1]["reviewAuthority"] = True
        self.rejects("falsely authenticated")

    def test_duplicate_principal_id(self):
        self.fixture["principals"][1]["principalId"] = "SIM-USER-AUTHOR"
        self.rejects("duplicated")

    def test_real_personal_identifier_not_allowed(self):
        self.fixture["principals"][0]["principalId"] = "employee123"
        self.rejects("invalid/duplicated")

    def test_role_escalation(self):
        self.fixture["principals"][1]["role"] = "administrator"
        self.rejects("wrong role/revision")

    def test_reviewer_cannot_be_author(self):
        self.fixture["independentReviewDecisions"][0]["principalId"] = "SIM-USER-AUTHOR"
        self.rejects("self-review")

    def test_adjudicator_cannot_be_reviewer(self):
        self.fixture["independentReviewDecisions"][0]["principalId"] = "SIM-USER-ADJUDICATOR"
        self.rejects("self-review")

    def test_same_person_double_review(self):
        decisions = self.fixture["independentReviewDecisions"]
        decisions[1]["principalId"] = decisions[0]["principalId"]
        self.rejects("two distinct")

    def test_replayed_decision_id(self):
        decisions = self.fixture["independentReviewDecisions"]
        decisions[1]["decisionId"] = decisions[0]["decisionId"]
        self.rejects("duplicate decision")

    def test_stale_revision_on_review(self):
        self.fixture["independentReviewDecisions"][1]["claimRevision"] = 2
        self.rejects("wrong role/revision")

    def test_claim_revision_cannot_self_assert_immutable(self):
        self.fixture["claimVersion"]["immutableVersionVerified"] = True
        self.rejects("immutable")

    def test_inject_real_machine_reference(self):
        self.fixture["claimVersion"]["realEquipmentRef"] = "777-001"
        self.rejects("real asset")

    def test_fake_idp_issuer_claimed_as_verified(self):
        self.fixture["credentialAssertions"][0]["issuerVerified"] = True
        self.rejects("cannot validate")

    def test_fake_credential_signature_claim(self):
        self.fixture["credentialAssertions"][0]["signatureVerified"] = True
        self.rejects("cannot validate")

    def test_token_metadata_not_accepted_in_public_fake(self):
        self.fixture["credentialAssertions"][0]["issuer"] = "https://idp.example.invalid"
        self.rejects("cannot validate")

    def test_expiry_not_trusted(self):
        self.fixture["credentialAssertions"][0]["expiryVerified"] = True
        self.rejects("cannot validate")

    def test_revocation_not_trusted(self):
        self.fixture["credentialAssertions"][0]["revocationChecked"] = True
        self.rejects("cannot validate")

    def test_competence_not_client_attested(self):
        self.fixture["technicalQualifications"][0]["competenceVerified"] = True
        self.rejects("cannot self-attest")

    def test_conflict_register_not_client_attested(self):
        self.fixture["technicalQualifications"][1]["conflictClearVerified"] = True
        self.rejects("cannot self-attest")

    def test_evidence_cannot_claim_real_data(self):
        self.fixture["evidenceManifest"]["realDataIncluded"] = True
        self.rejects("real records")

    def test_evidence_cannot_claim_licensed_content(self):
        self.fixture["evidenceManifest"]["licensedContentIncluded"] = True
        self.rejects("real records")

    def test_evidence_foreign_claim(self):
        self.fixture["evidenceManifest"]["claimId"] = "CLM-FOREIGN"
        self.rejects("verified licensed")

    def test_duplicate_evidence_reference(self):
        self.fixture["evidenceManifest"]["sourceReferenceIds"] = ["CIT-A", "CIT-A"]
        self.rejects("verified licensed")

    def test_fabricated_external_anchor(self):
        self.fixture["auditAnchor"]["externalStoreVerified"] = True
        self.rejects("no external trusted anchor")

    def test_fabricated_trusted_timestamp(self):
        self.fixture["auditAnchor"]["externalTimestampVerified"] = True
        self.rejects("no external trusted anchor")

    def test_oem_publication_cannot_be_claimed(self):
        self.fixture["oemEffectivityAttestation"]["publication"] = "OEM-ABC"
        self.rejects("not verified")

    def test_oem_series_cannot_be_assumed(self):
        self.fixture["oemEffectivityAttestation"]["serialOrArrangement"] = "ABC-001"
        self.rejects("not verified")

    def test_oem_approval_client_claim(self):
        self.fixture["oemEffectivityAttestation"]["operationalApproval"] = True
        self.rejects("not verified")

    def test_no_operational_authorizations_in_fixture(self):
        self.fixture["operationalAuthorizations"] = [{"command":"release_equipment"}]
        self.rejects("cannot import real tenant or operational authorizations")

    def test_public_role_cannot_enable_operational_action(self):
        self.policy["roles"][0]["canPropose"].append("release_equipment")
        with self.assertRaises(ImportRejected):
            check_policy(self.policy)

    def test_missing_required_proof_rejected(self):
        self.policy["requiredTrustProofs"].pop()
        with self.assertRaises(ImportRejected):
            check_policy(self.policy)

    def test_public_policy_enabling_verification_rejected(self):
        self.policy["verificationAvailable"] = True
        with self.assertRaises(ImportRejected):
            check_policy(self.policy)

    def test_duplicate_principal_assertion(self):
        self.fixture["credentialAssertions"].append(
            copy.deepcopy(self.fixture["credentialAssertions"][0]))
        self.rejects("cannot validate")

    def test_unknown_extra_operational_field_rejected(self):
        self.fixture["independentReviewDecisions"][0]["canApprove"] = True
        self.rejects("exact fields")


if __name__ == "__main__":
    unittest.main()
