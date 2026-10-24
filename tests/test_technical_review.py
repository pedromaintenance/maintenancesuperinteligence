"""Review governance regression tests: all persons and reviews are FICTIONAL."""
import copy
import json
from pathlib import Path
import unittest

from connectors.fmea_public import ImportRejected
from methods.discrimination import validate_matrix
from methods.library import ROOT, validate_catalog, validate_sources
from governance.review import evaluate_packet, validate_packet


class SyntheticGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.packet = json.loads((ROOT / "governance/review-packet.v1.json").read_text())
        registry = json.loads((ROOT / "data/diagnostic-method-sources.v1.json").read_text())
        self.sources = validate_sources(registry)
        self.methods = validate_catalog(
            json.loads((ROOT / "methods/catalog.v1.json").read_text()), self.sources)
        self.snapshot = {"records": [
            {"id": cid, "family": "comando_final", "confirmedRootCause": False}
            for cid in ("FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004")
        ]}
        matrix = json.loads((ROOT / "methods/discrimination-matrix.v1.json").read_text())
        self.families = validate_matrix(matrix, self.methods, self.snapshot)

    def validate(self):
        return validate_packet(self.packet, self.methods, self.sources, self.families)

    def result(self):
        return evaluate_packet(self.packet, self.methods,
                               self.sources, self.families, self.snapshot)

    def rejects(self, part=None):
        with self.assertRaises(ImportRejected) as caught:
            self.validate()
        if part:
            self.assertIn(part, str(caught.exception))

    def claim(self, claim_id):
        return next(c for c in self.packet["claims"] if c["claimId"] == claim_id)

    def review(self, claim_id, reviewer="SIM-REVIEWER-OIL-A"):
        return next(r for r in self.packet["assessments"]
                    if r["claimId"] == claim_id and r["reviewerId"] == reviewer)

    def test_eight_claims_nine_citations(self):
        d = self.validate()
        self.assertEqual(len(d["claims"]), 8)
        self.assertEqual(len(d["citations"]), 9)
        self.assertEqual(sum(len(x) for x in d["assessmentsByClaim"].values()), 13)

    def test_six_stage_vocabulary_has_no_oem_series_in_public_simulator(self):
        r = self.result()
        self.assertEqual(r["statusCounts"], {
            "draft": 1, "needs_evidence": 2, "under_review": 1, "disputed": 2,
            "general_reference_supported": 2, "oem_series_verified": 0
        })
        self.assertEqual(len(r["disagreements"]), 2)
        self.assertTrue(all(x["requiresRealTechnicalReview"] for x in r["decisions"]))
        self.assertFalse(r["hasAuthenticatedExpertReviews"])

    def test_public_approval_never_emerges_from_two_fictitious_personas(self):
        result = self.result()
        for d in result["decisions"]:
            self.assertFalse(d["reviewerIdentityVerified"])
            self.assertFalse(d["reviewerIndependenceVerified"])
            self.assertFalse(d["approvedForOperationalUse"])
            self.assertFalse(d["oemSeriesVerified"])
            self.assertFalse(d["rootCauseConfirmed"])
            self.assertEqual(d["technicalQualification"], "synthetic_workflow_only")
        self.assertFalse(result["discriminationScientificallyValidated"])
        self.assertFalse(result["mayAuthorizeWork"])
        self.assertFalse(result["mayCreateWorkOrder"])
        self.assertFalse(result["mayReleaseEquipment"])

    def test_unresolved_disagreement_keeps_positions_and_counterexample(self):
        r = self.result()
        water = next(d for d in r["disagreements"] if d["claimId"] == "CLM-OIL-WATER")
        self.assertEqual(water["positions"], ["support_general", "challenge"])
        self.assertEqual(water["resolution"], "not_adjudicated")
        self.assertTrue(water["counterexample"])

    def test_one_review_is_under_review_not_qualified(self):
        r = self.result()
        magnet = next(x for x in r["decisions"]
                      if x["claimId"] == "CLM-MECH-MAGNET")
        self.assertEqual(magnet["derivedStatus"], "under_review")

    def test_no_reviews_yet_is_draft(self):
        r = self.result()
        vib = next(x for x in r["decisions"]
                   if x["claimId"] == "CLM-VIB-CONTEXT")
        self.assertEqual(vib["derivedStatus"], "draft")

    def test_insufficient_evidence_requires_more_sources(self):
        r = self.result()
        hyd = next(x for x in r["decisions"]
                   if x["claimId"] == "CLM-HYD-LOAD")
        self.assertEqual(hyd["derivedStatus"], "needs_evidence")

    def test_second_round_with_two_fresh_personas_remains_only_synthetic(self):
        r1 = self.review("CLM-OIL-WATER", "SIM-REVIEWER-OIL-A")
        for i, persona in enumerate(("SIM-REVIEWER-OIL-C", "SIM-REVIEWER-OIL-D"), 1):
            r = copy.deepcopy(r1)
            r["reviewId"] = f"REV-OIL-WATER-R2-{i}"
            r["reviewerId"] = persona
            r["round"] = 2
            r["assessment"] = "support_general"
            self.packet["assessments"].append(r)
        output = self.result()
        decision = next(x for x in output["decisions"]
                        if x["claimId"] == "CLM-OIL-WATER")
        self.assertEqual(decision["derivedStatus"], "general_reference_supported")
        self.assertEqual(decision["reviewRound"], 2)
        self.assertFalse(decision["reviewerIdentityVerified"])
        self.assertFalse(decision["approvedForOperationalUse"])

    def test_one_new_second_round_persona_cannot_adjudicate(self):
        copy_review = copy.deepcopy(self.review("CLM-OIL-WATER"))
        copy_review.update(round=2, reviewId="REV-OIL-WATER-R2-1",
                           reviewerId="SIM-REVIEWER-OIL-C")
        self.packet["assessments"].append(copy_review)
        self.rejects("two fresh independent personas")

    def test_second_round_cannot_reuse_reviewer_from_first_round(self):
        r = copy.deepcopy(self.review("CLM-OIL-WATER"))
        self.packet["assessments"].extend([
            {**r, "reviewId": "REV-OIL-WATER-R2-1", "round": 2},
            {**r, "reviewId": "REV-OIL-WATER-R2-2", "round": 2,
             "reviewerId": "SIM-REVIEWER-OIL-C"},
        ])
        self.rejects("identical fictional reviewer")

    def test_unanimous_first_round_cannot_be_resubmitted_to_erase_trail(self):
        r = copy.deepcopy(self.review("CLM-OIL-FORMULATION"))
        self.packet["assessments"].extend([
            {**r, "reviewId": "REV-OIL-FORMULATION-R2-1", "round": 2,
             "reviewerId": "SIM-REVIEWER-OIL-C"},
            {**r, "reviewId": "REV-OIL-FORMULATION-R2-2", "round": 2,
             "reviewerId": "SIM-REVIEWER-OIL-D"},
        ])
        self.rejects("already unanimously supported")

    def test_forged_approval_from_source_is_blocked(self):
        self.packet["humanApprovalAuthority"] = True
        self.rejects("cannot claim operational authority")

    def test_forged_oem_document_is_blocked(self):
        self.claim("CLM-OIL-FORMULATION")["applicabilityEvidence"]["publicationId"] = "OEM-CUSTOM"
        self.rejects("no model, series, publication")

    def test_claim_false_confirmed_cause_blocked(self):
        self.claim("CLM-OIL-FORMULATION")["rootCauseConfirmed"] = True
        self.rejects("cannot confirm failure")

    def test_claim_numeric_threshold_without_reference_blocked(self):
        self.claim("CLM-HYD-LOAD")["statement"] += " Limite 4900 psi."
        self.rejects("unsupported numerical OEM statement")

    def test_review_signed_falsehood_blocked(self):
        self.review("CLM-OIL-FORMULATION")["signature"] = "Engineer X"
        self.rejects("fake signed review")

    def test_reviewer_verified_credentials_falsehood_blocked(self):
        self.packet["reviewers"][0]["credentialsVerified"] = True
        self.rejects("cannot self-certify")

    def test_reviewer_independence_falsehood_blocked(self):
        self.packet["reviewers"][0]["independenceVerified"] = True
        self.rejects("cannot self-certify")

    def test_reviewer_must_declare_no_conflict_in_synthetic_eligibility(self):
        self.review("CLM-OIL-FORMULATION")["conflictOfInterestDeclared"] = True
        self.rejects("declared conflict")

    def test_reviewer_competence_must_match_domain(self):
        self.review("CLM-OIL-FORMULATION")["competenceDeclaredDomain"] = "electronics"
        self.rejects("missing discipline")

    def test_same_person_twice_in_round_blocked(self):
        r = self.review("CLM-OIL-FORMULATION", "SIM-REVIEWER-OIL-B")
        r["reviewerId"] = "SIM-REVIEWER-OIL-A"
        self.rejects("identical fictional reviewer")

    def test_cross_claim_reference_blocked(self):
        self.review("CLM-OIL-FORMULATION")["citationIds"] = [
            self.claim("CLM-ECM-EVENT")["citationIds"][0]]
        self.rejects("foreign/recursive citation")

    def test_circular_citation_id_as_source_blocked(self):
        self.packet["citations"][0]["sourceId"] = self.packet["citations"][0]["citationId"]
        self.rejects("missing or circular source")

    def test_claim_cannot_use_method_from_other_discipline(self):
        self.claim("CLM-OIL-FORMULATION")["methodId"] = "MET-ECM-CODES"
        self.rejects("invalid cross-domain method")

    def test_source_citation_must_exist_in_catalog_method(self):
        self.packet["citations"][0]["sourceId"] = "BOSCH-REXROTH-CYTRO"
        self.rejects("source not supported")

    def test_source_cannot_claim_executed_oem_test(self):
        self.packet["citations"][0]["sourceApplicability"] = "oem_series_verified"
        self.rejects("cannot assert quoted OEM")

    def test_licensed_manual_copy_not_allowed(self):
        self.packet["citations"][0]["licenseCopyIncluded"] = True
        self.rejects("cannot assert quoted OEM")

    def test_counterexample_mandatory(self):
        self.claim("CLM-OIL-FORMULATION")["counterexample"] = ""
        self.rejects("missing limits")

    def test_orphaned_citation_rejected(self):
        self.packet["citations"].append({
            **self.packet["citations"][0],
            "citationId": "CIT-ORPHAN-1"
        })
        self.rejects("orphaned or multiply claimed")

    def test_duplicate_claimed_citation_rejected(self):
        target = self.claim("CLM-OIL-WATER")
        target["citationIds"] = self.claim("CLM-OIL-FORMULATION")["citationIds"]
        self.rejects("cross-claim citation")

    def test_duplicate_review_id_rejected(self):
        self.packet["assessments"][1]["reviewId"] = self.packet["assessments"][0]["reviewId"]
        self.rejects("duplicate/invalid review ID")

    def test_second_round_without_first_round_is_blocked(self):
        self.packet["assessments"][0]["round"] = 2
        self.rejects("second round requires two fresh independent personas")

    def test_forged_extra_evidence_field_rejected(self):
        self.packet["claims"][0]["oemTorqueN_m"] = 1200
        self.rejects("missing or unauthorized fields")

    def test_unrecognized_model_reference_rejected(self):
        self.claim("CLM-ECM-EVENT")["applicabilityEvidence"]["serialOrArrangement"] = "777E-X"
        self.rejects("no model, series, publication")

    def test_authored_editorial_claim_cannot_be_passed_as_measured(self):
        self.claim("CLM-ECM-EVENT")["evidenceNature"] = "verified_field_fact"
        self.rejects("cannot confirm failure")


if __name__ == "__main__":
    unittest.main()
