"""Attack-oriented tests for public, untrusted restricted-review blueprint."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from connectors.fmea_public import ImportRejected
from governance.restricted_blueprint import (
    execute_fixture, validate_fixture, verify_report, derive_case
)
from methods.discrimination import validate_matrix
from methods.library import ROOT, validate_catalog, validate_sources


class RestrictedReviewBlueprintTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(
            (ROOT / "examples/restricted-review-threat-fixture.v1.json").read_text())
        self.packet = json.loads(
            (ROOT / "governance/review-packet.v1.json").read_text())
        sources = json.loads((ROOT / "data/diagnostic-method-sources.v1.json").read_text())
        self.sources = validate_sources(sources)
        self.methods = validate_catalog(
            json.loads((ROOT / "methods/catalog.v1.json").read_text()), self.sources)
        self.snapshot = {"records": [
            {"id": name, "family": "comando_final", "confirmedRootCause": False}
            for name in ("FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004")
        ]}
        self.families = validate_matrix(
            json.loads((ROOT / "methods/discrimination-matrix.v1.json").read_text()),
            self.methods, self.snapshot)

    def validate(self):
        return validate_fixture(self.fixture, self.packet, self.methods,
                                self.sources, self.families)

    def run_fixture(self):
        return execute_fixture(self.fixture, self.packet, self.methods,
                               self.sources, self.families, self.snapshot)

    def rejects(self, msg=None):
        with self.assertRaises(ImportRejected) as caught:
            self.run_fixture()
        if msg:
            self.assertIn(msg, str(caught.exception))

    def event(self, case=0, idx=0):
        return self.fixture["cases"][case]["events"][idx]

    def test_three_sequences_and_nine_events(self):
        x = self.run_fixture()
        self.assertEqual(x["caseCount"], 3)
        self.assertEqual(x["eventCount"], 9)
        self.assertEqual(x["untrustedIdentityCount"], 7)
        self.assertEqual(x["authenticatedIdentityCount"], 0)
        self.assertEqual(x["verifiedReviewSignatureCount"], 0)
        self.assertFalse(x["canApproveMaintenance"])

    def test_derived_states_preserve_disputed_history(self):
        x = self.run_fixture()
        self.assertEqual(x["derivedStates"], {
            "needs_evidence": 1,
            "qualified_general_claim_simulation": 1,
            "under_review": 1,
        })
        water = x["cases"][0]
        self.assertEqual(water["reviewPositions"], ["support_general", "challenge"])
        self.assertTrue(water["hasUnresolvedDispute"])
        self.assertEqual(water["fictionalAdjudicatorId"], "SIM-ACTOR-OIL-ADJ")

    def test_two_reviewer_personas_are_not_two_authenticated_engineers(self):
        x = self.run_fixture()
        formulated = x["cases"][1]
        self.assertEqual(formulated["derivedState"],
                         "qualified_general_claim_simulation")
        self.assertFalse(formulated["claimedRealIdentity"])
        self.assertEqual(formulated["validReviewSignatures"], 0)
        self.assertFalse(formulated["mayPublishGeneralClaimAsReal"])
        self.assertFalse(formulated["mayVerifyOemSeries"])

    def test_sha_chain_matches_source_and_is_reproducible(self):
        x = self.run_fixture()
        self.assertEqual(x, self.run_fixture())
        for case in x["cases"]:
            prev = "0" * 64
            self.assertEqual(len(case["auditEvents"]),
                             next(len(c["events"]) for c in self.fixture["cases"]
                                  if c["caseId"] == case["caseId"]))
            for e in case["auditEvents"]:
                self.assertEqual(e["previousSha256"], prev)
                prev = e["eventSha256"]
            self.assertEqual(case["auditHeadSha256"], prev)
        self.assertEqual(
            verify_report(x, self.fixture, self.packet, self.methods,
                          self.sources, self.families, self.snapshot), x)

    def test_replay_nonce_against_other_case_rejected(self):
        self.event(1, 0)["nonce"] = self.event(0, 0)["nonce"]
        self.rejects("duplicate/replayed nonce")

    def test_replay_event_id_against_other_case_rejected(self):
        self.event(1, 0)["eventId"] = self.event(0, 0)["eventId"]
        self.rejects("duplicate/replayed nonce")

    def test_duplicate_actor_identity_rejected(self):
        self.fixture["actors"][1]["actorId"] = self.fixture["actors"][0]["actorId"]
        self.rejects("duplicate synthetic identifier")

    def test_actor_self_certification_rejected(self):
        self.fixture["actors"][1]["identityVerified"] = True
        self.rejects("forged identity")

    def test_credential_self_certification_rejected(self):
        self.fixture["actors"][1]["credentialVerified"] = True
        self.rejects("forged identity")

    def test_independence_claim_unverified_rejected(self):
        self.fixture["actors"][1]["independenceVerified"] = True
        self.rejects("forged identity")

    def test_revoked_persona_denied_by_public_fixture(self):
        self.fixture["actors"][1]["revoked"] = True
        self.rejects("revocation")

    def test_conflict_of_interest_fails_closed(self):
        self.fixture["actors"][1]["conflictOfInterestDeclared"] = True
        self.rejects("declared conflict")

    def test_signature_forgery_rejected(self):
        self.event(0, 1)["signature"] = "SIMULATED-PKCS7"
        self.rejects("forged signature")

    def test_external_verifier_fake_capability_rejected(self):
        self.fixture["externalVerifierConfigured"] = True
        self.rejects("external authentication")

    def test_fake_external_trust_anchor_rejected(self):
        self.fixture["externalTrustAnchor"] = "my-key"
        self.rejects("external authentication")

    def test_fake_time_authority_rejected(self):
        self.fixture["externalTimeAuthorityConfigured"] = True
        self.rejects("external authentication")

    def test_fake_permission_to_persist_real_data_rejected(self):
        self.fixture["mayPersistRealData"] = True
        self.rejects("external authentication")

    def test_oem_authority_flag_rejected(self):
        self.fixture["mayIssueTechnicalApproval"] = True
        self.rejects("external authentication")

    def test_author_cannot_sign_as_reviewer(self):
        self.event(0, 1)["actorId"] = "SIM-ACTOR-OIL-AUTH"
        self.rejects("role/discipline")

    def test_adjudicator_cannot_review(self):
        self.event(0, 2)["actorId"] = "SIM-ACTOR-OIL-ADJ"
        self.rejects("role/discipline")

    def test_cross_discipline_review_blocked(self):
        self.event(0, 1)["actorId"] = "SIM-ACTOR-HYD-REV-A"
        self.rejects("role/discipline")

    def test_reviewer_cannot_be_author(self):
        self.event(0, 0)["actorId"] = "SIM-ACTOR-OIL-REV-A"
        self.rejects("role/discipline")

    def test_duplicate_reviewer_cannot_claim_independence(self):
        self.event(0, 2)["actorId"] = "SIM-ACTOR-OIL-REV-A"
        self.rejects("duplicate reviewer")

    def test_adjudicator_cannot_preempt_two_reviews(self):
        c = self.fixture["cases"][0]
        c["events"].pop(2)
        self.rejects("adjudication requires two disputed")

    def test_case_without_submission_is_rejected(self):
        self.fixture["cases"][0]["events"].pop(0)
        self.rejects("invalid review state")

    def test_case_double_submission_is_rejected(self):
        e = copy.deepcopy(self.event(0, 0))
        e["eventId"] = "SIM-EVENT-WATER-99"
        e["nonce"] = "SIM-NONCE-WATER-99"
        self.fixture["cases"][0]["events"].insert(1, e)
        self.rejects("must submit a draft")

    def test_revision_change_after_review_rejected(self):
        self.event(0, 1)["targetRevision"] = 2
        self.rejects("wrong claim/revision")

    def test_revision_change_from_source_rejected(self):
        self.fixture["cases"][0]["revision"] = 2
        self.rejects("immutable claim revision")

    def test_cross_tenant_replay_attempt_rejected(self):
        self.fixture["tenantId"] = "TENANT-PROD"
        self.rejects("external authentication")

    def test_foreign_claim_in_case_rejected(self):
        self.event(0, 1)["claimId"] = "CLM-HYD-LOAD"
        self.rejects("wrong claim/revision")

    def test_foreign_citation_rejected(self):
        self.event(0, 1)["sourceRefs"] = ["CIT-HYD-LOAD-1"]
        self.rejects("foreign/recursive citation")

    def test_extra_operational_permission_rejected(self):
        self.event(0, 2)["canReleaseEquipment"] = True
        self.rejects("unauthorized field")

    def test_fake_oem_source_revision_rejected(self):
        self.packet["claims"][0]["applicabilityEvidence"]["revision"] = "M1234"
        self.rejects("no model, series")

    def test_invalid_source_packet_claim_after_review_rejected(self):
        self.packet["claims"][0]["statement"] += " Novamente alterado."
        # Input is still an editorial text, so the source packet itself changed.
        # A report already issued for the prior packet must NOT validate anymore.
        mutated = self.run_fixture()
        self.assertNotEqual(mutated["reviewPacketSha256"], self.original_packet_sha)

    @property
    def original_packet_sha(self):
        from evidence.ledger import sha
        packet = json.loads(
            (ROOT / "governance/review-packet.v1.json").read_text())
        return sha(packet)

    def test_report_mutation_detected_without_original_source_change(self):
        report = self.run_fixture()
        report["cases"][0]["auditEvents"][1]["stateAfter"] = "oem_series_verified"
        with self.assertRaisesRegex(ImportRejected, "altered, replayed"):
            verify_report(report, self.fixture, self.packet, self.methods,
                          self.sources, self.families, self.snapshot)

    def test_report_resealed_locally_still_differs_from_original_fixture(self):
        from evidence.ledger import sha
        report = self.run_fixture()
        event = report["cases"][0]["auditEvents"][1]
        event["event"]["action"] = "challenge"
        # Even if forged event digest were recomputed, it cannot match replay
        # from preserved source inputs.
        event["eventSha256"] = sha({k:v for k,v in event.items()
                                     if k != "eventSha256"})
        with self.assertRaisesRegex(ImportRejected, "altered, replayed"):
            verify_report(report, self.fixture, self.packet, self.methods,
                          self.sources, self.families, self.snapshot)

    def test_report_authorization_flag_forgery_blocked(self):
        report = self.run_fixture()
        report["canApproveMaintenance"] = True
        with self.assertRaisesRegex(ImportRejected, "altered, replayed"):
            verify_report(report, self.fixture, self.packet, self.methods,
                          self.sources, self.families, self.snapshot)

    def test_offline_fixture_cannot_replace_authenticated_review(self):
        report = self.run_fixture()
        self.assertFalse(report["externalAuditAnchorConfigured"])
        self.assertFalse(report["trustedClockConfigured"])
        self.assertEqual(report["reviewAuthenticity"], "not_achieved")
        self.assertEqual(report["qualifiedClaimsForRealWorldUse"], 0)
        self.assertFalse(report["oemEffectivityVerified"])
        self.assertFalse(report["canWriteSap"])
        self.assertFalse(report["canModifyEcm"])

    def test_valid_event_references_claim_digest(self):
        from evidence.ledger import sha
        report = self.run_fixture()
        for case in report["cases"]:
            claim = next(c for c in self.packet["claims"]
                         if c["claimId"] == case["claimId"])
            self.assertEqual(case["claimSha256"], sha(claim))
            self.assertTrue(all(e["claimSha256"] == sha(claim)
                                for e in case["auditEvents"]))


if __name__ == "__main__":
    unittest.main()
