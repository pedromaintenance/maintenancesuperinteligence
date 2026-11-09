"""Cycle 65: fictional reviewers and hash chains do not confer authority."""
import copy
import unittest

from benchmarks.cycle65_review_ledger import DENIED, digest_event, sha256_json, validate
from tests.test_cycle64_source_governance import fixture as source_fixture, source


def fixture(with_conflict=True):
    case = source_fixture()
    if with_conflict:
        case["sources"].append(source("SIM-SRC002", "SIM-LIN002", "SIM-VALUE2"))
    return {
        "schema": "maintenance-superinteligence.synthetic-conflict-review-ledger.v1",
        "sourceCase": case,
        "events": [],
        "claims": {key: False for key in DENIED},
    }


def append_event(p, id="SIM-EVT001", role="reviewer_a", alias="SIM-REVA01",
                 event_type="assessment", position="prefer_declared_claim",
                 claim="SIM-VALUE1", target=None, ref="SIM-REF001"):
    e = {
        "eventId": id, "referenceId": ref, "eventType": event_type,
        "actorRole": role, "actorAlias": alias, "position": position,
        "selectedClaimToken": claim if position == "prefer_declared_claim" else None,
        "targetEventId": target, "requiredEvidence": "independent_technical_review",
        "previousDigest": (p["events"][-1]["digest"] if p["events"]
                           else sha256_json(p["sourceCase"])),
    }
    e["digest"] = digest_event(e)
    p["events"].append(e)
    return e


def two_assessments(p):
    append_event(p)
    append_event(p, id="SIM-EVT002", role="reviewer_b", alias="SIM-REVB01",
                 claim="SIM-VALUE2")


class ReviewLedgerTests(unittest.TestCase):
    def test_empty_partial_session_is_not_review(self):
        out = validate(fixture())
        self.assertEqual(out["syntheticEventCount"], 0)
        self.assertEqual(out["tracks"][0]["workflowState"], "not_reviewed")
        self.assertFalse(out["realHumanReviewCompleted"])
        self.assertEqual(out["decision"], "NO GO")

    def test_no_conflict_requires_no_review_events(self):
        out = validate(fixture(with_conflict=False))
        self.assertEqual(out["unresolvedReferenceCount"], 0)
        self.assertEqual(out["tracks"], [])

    def test_two_opposing_fictional_assessments_do_not_resolve(self):
        p = fixture()
        two_assessments(p)
        out = validate(p)
        self.assertEqual(out["tracks"][0]["syntheticAssessments"], 2)
        self.assertEqual(out["tracks"][0]["workflowState"],
                         "two_synthetic_assessments_conflict_unresolved")
        self.assertFalse(out["technicalConflictResolved"])

    def test_three_roles_can_only_record_proposal(self):
        p = fixture()
        two_assessments(p)
        append_event(p, id="SIM-EVT003", role="arbiter", alias="SIM-ARBT01",
                     event_type="adjudication_proposal", claim="SIM-VALUE1")
        out = validate(p)
        self.assertEqual(out["tracks"][0]["syntheticProposals"], 1)
        self.assertEqual(out["tracks"][0]["workflowState"],
                         "synthetic_proposal_recorded_conflict_unresolved")
        self.assertFalse(out["independentExpertReviewCompleted"])

    def test_challenge_requires_other_assessment(self):
        p = fixture()
        two_assessments(p)
        append_event(p, id="SIM-EVT003", role="reviewer_a", alias="SIM-REVA01",
                     event_type="challenge", position="insufficient_evidence",
                     target="SIM-EVT002")
        out = validate(p)
        self.assertEqual(out["tracks"][0]["syntheticChallenges"], 1)
        self.assertFalse(out["tracks"][0]["conflictResolved"])

    def test_no_conflict_cannot_have_review_event(self):
        p = fixture(False)
        append_event(p)
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_tampered_event_body(self):
        p = fixture()
        append_event(p)
        p["events"][0]["requiredEvidence"] = "source_authenticity"
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            validate(p)

    def test_reject_source_snapshot_change(self):
        p = fixture()
        append_event(p)
        p["sourceCase"]["sources"][1]["claimToken"] = "SIM-VALUE3"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_rebased_chain(self):
        p = fixture()
        append_event(p)
        append_event(p, id="SIM-EVT002", role="reviewer_b", alias="SIM-REVB01",
                     claim="SIM-VALUE2")
        p["events"][1]["previousDigest"] = "0" * 64
        p["events"][1]["digest"] = digest_event(p["events"][1])
        with self.assertRaisesRegex(ValueError, "discontinuous"):
            validate(p)

    def test_duplicate_event_rejected(self):
        p = fixture()
        two_assessments(p)
        append_event(p, id="SIM-EVT002", role="arbiter", alias="SIM-ARBT01",
                     event_type="adjudication_proposal", claim="SIM-VALUE1")
        with self.assertRaisesRegex(ValueError, "duplicated event"):
            validate(p)

    def test_challenge_cannot_target_self(self):
        p = fixture()
        two_assessments(p)
        append_event(p, id="SIM-EVT003", role="reviewer_a", alias="SIM-REVA01",
                     event_type="challenge", position="insufficient_evidence",
                     target="SIM-EVT001")
        with self.assertRaises(ValueError):
            validate(p)

    def test_challenge_cannot_target_unknown_event(self):
        p = fixture()
        two_assessments(p)
        append_event(p, id="SIM-EVT003", role="reviewer_a", alias="SIM-REVA01",
                     event_type="challenge", position="insufficient_evidence",
                     target="SIM-UNKNOWN")
        with self.assertRaises(ValueError):
            validate(p)

    def test_duplicate_assessment_role_rejected(self):
        p = fixture()
        append_event(p)
        append_event(p, id="SIM-EVT002", role="reviewer_a", alias="SIM-REVA01")
        with self.assertRaises(ValueError):
            validate(p)

    def test_role_impersonation_rejected(self):
        p = fixture()
        append_event(p)
        append_event(p, id="SIM-EVT002", role="reviewer_b", alias="SIM-REVA01",
                     claim="SIM-VALUE2")
        with self.assertRaises(ValueError):
            validate(p)

    def test_proposal_requires_both_assessments(self):
        p = fixture()
        append_event(p)
        append_event(p, id="SIM-EVT002", role="arbiter", alias="SIM-ARBT01",
                     event_type="adjudication_proposal", claim="SIM-VALUE1")
        with self.assertRaises(ValueError):
            validate(p)

    def test_proposal_requires_third_alias(self):
        p = fixture()
        two_assessments(p)
        append_event(p, id="SIM-EVT003", role="arbiter", alias="SIM-REVA01",
                     event_type="adjudication_proposal", claim="SIM-VALUE1")
        with self.assertRaises(ValueError):
            validate(p)

    def test_invalid_selected_claim_token(self):
        p = fixture()
        append_event(p, claim="SIM-NONSENSE")
        with self.assertRaises(ValueError):
            validate(p)

    def test_abstention_cannot_hide_claim(self):
        p = fixture()
        e = append_event(p, position="insufficient_evidence")
        e["selectedClaimToken"] = "SIM-VALUE1"
        e["digest"] = digest_event(e)
        with self.assertRaises(ValueError):
            validate(p)

    def test_unknown_role_rejected(self):
        p = fixture()
        append_event(p, role="senior_engineer")
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_authority_claims(self):
        for flag in DENIED:
            p = fixture()
            p["claims"][flag] = True
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                validate(p)

    def test_reject_c64_provenance_promotion(self):
        p = fixture()
        p["sourceCase"]["sources"][0]["provenanceVerified"] = True
        with self.assertRaises(ValueError):
            validate(p)

    def test_no_unexpected_event_fields(self):
        p = fixture()
        e = append_event(p)
        e["realReviewerName"] = "PRIVATE"
        e["digest"] = digest_event(e)
        with self.assertRaises(ValueError):
            validate(p)

    def test_input_not_mutated(self):
        p = fixture()
        two_assessments(p)
        snapshot = copy.deepcopy(p)
        validate(p)
        self.assertEqual(p, snapshot)


if __name__ == "__main__":
    unittest.main()
