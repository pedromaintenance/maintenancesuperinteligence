"""Cycle 39 — deny-by-default federation/RBAC preflight, no real authentication."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from governance.federation_rbac import (
    ROOT, POLICY, REHEARSAL, KINDS, GRANTS, ACTOR_IDS,
    validate_policy, validate_fixture, preflight,
    evaluate, verify_report, render_html, main
)
from pilot.change_review_packets import ReviewRejected


class FederationRBACPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads(POLICY.read_text(encoding="utf-8"))
        cls.fixture=json.loads(REHEARSAL.read_text(encoding="utf-8"))

    def test_30_synthetic_scenarios_no_real_access_even_for_eligible_roles(self):
        report=evaluate(self.policy,self.fixture)
        self.assertTrue(verify_report(report,self.policy,self.fixture))
        self.assertEqual(report["scenarioCount"],30)
        self.assertEqual(report["actorProfiles"],5)
        self.assertEqual(report["availablePacketCount"],36)
        self.assertEqual(report["hypotheticalRoleEligibleCount"],8)
        self.assertEqual(report["structurallyOrRoleRejectedCount"],22)
        self.assertEqual(report["actualGrantedCount"],0)
        self.assertEqual(report["realAuthorizationsGranted"],0)
        self.assertEqual(report["realPrivateDocumentsAccessed"],0)
        self.assertFalse(report["realIdpConfigured"])
        self.assertFalse(report["sourceRulesChanged"])
        self.assertEqual(report["jwtSignaturesVerified"],0)
        self.assertEqual(report["realIdentitiesAuthenticated"],0)
        self.assertEqual(report["realRoleBindingsVerified"],0)
        self.assertEqual(report["decision"],
            "no_go_connect_verified_oidc_idp_and_real_access_enforcement")
        for row in report["results"]:
            self.assertFalse(row["authorizationGranted"])
            self.assertFalse(row["actualSubjectAuthenticated"])
            self.assertFalse(row["mayReadPrivateDocuments"])
            self.assertFalse(row["maySubmitTechnicalOpinion"])
            self.assertFalse(row["mayCreateWorkOrder"])
            self.assertFalse(row["mayModifyEcm"])
            self.assertFalse(row["mayReleaseEquipment"])

    def test_only_hypothetical_eligibility_and_never_approval(self):
        report=evaluate(self.policy,self.fixture)
        expected=["baseline_author_public","role_eligible_custody_index",
                  "role_eligible_prepare","role_eligible_reviewer_a_read",
                  "role_eligible_reviewer_a_opinion",
                  "role_eligible_reviewer_b_opinion",
                  "role_eligible_adjudication_only","duplicate_token_jti"]
        allowed=[r["kind"] for r in report["results"]
                 if r["hypotheticalRoleAndShapeEligible"]]
        self.assertEqual(allowed,expected)
        self.assertTrue(all(not r["authorizationGranted"]
                            for r in report["results"]))
        self.assertEqual(set(GRANTS),{p[1] for p in ACTOR_IDS})
        self.assertNotIn("release_equipment",GRANTS["adjudicator"])

    def test_replayed_jti_detected_for_second_mock_assertion(self):
        report=evaluate(self.policy,self.fixture)
        first,next_=report["results"][24:26]
        self.assertTrue(first["hypotheticalRoleAndShapeEligible"])
        self.assertFalse(next_["hypotheticalRoleAndShapeEligible"])
        self.assertIn("duplicate_jti_in_fixture",next_["structuralOrRoleFaults"])
        self.assertFalse(first["authorizationGranted"])

    def test_oidc_like_claims_are_not_tokens_or_verified_signatures(self):
        policy=self.policy
        self.assertEqual(policy["syntheticIssuer"],"https://idp.example.invalid/research")
        self.assertTrue(policy["defaultDeny"])
        self.assertTrue(policy["roleSeparationRequired"])
        for key in ("providerConfigured","oidcDiscoveryVerified",
                    "jwksSignatureVerifierConnected",
                    "oidcAudienceRegistered","externalRoleDirectoryConnected",
                    "sessionRevocationStoreConnected","mfaAssuranceValidated",
                    "realAccessEnforcementConnected","auditLogExternallyCustodied"):
            self.assertFalse(policy[key])
        self.assertFalse(self.fixture["realTokensPresent"])
        self.assertFalse(self.fixture["liveProviderConnected"])

    def test_reject_issuer_audience_expiry_nonce_mfa_and_algorithm_issues(self):
        results=evaluate(self.policy,self.fixture)["results"]
        by_kind={r["kind"]:r for r in results}
        checks={
            "unknown_packet":"unknown_packet",
            "wrong_issuer":"issuer_mismatch",
            "wrong_audience":"audience_mismatch",
            "expired_claim":"expired",
            "future_claim":"not_yet_valid",
            "nonce_mismatch":"nonce_mismatch",
            "missing_mfa":"mfa_claim_not_present",
            "actor_subject_mismatch":"subject_mismatch",
            "actor_role_spoof":"role_claim_mismatch",
            "reuse_jti":"duplicate_jti_in_fixture",
            "untrusted_algorithm":"unsupported_algorithm",
            "unexpected_scope":"mfa_claim_not_present",
            "long_lifetime":"excessive_or_invalid_lifetime",
            "tampered_auth_claims":"self_claimed_signature_not_trusted",
        }
        for key,fault in checks.items():
            self.assertIn(fault,by_kind[key]["structuralOrRoleFaults"],key)
            self.assertFalse(by_kind[key]["hypotheticalRoleAndShapeEligible"])
            self.assertFalse(by_kind[key]["authorizationGranted"])

    def test_operational_scope_never_appears_in_role_grants(self):
        report=evaluate(self.policy,self.fixture)
        for key in ("operation_always_forbidden","upstream_always_forbidden"):
            row=next(r for r in report["results"] if r["kind"]==key)
            self.assertIn("operational_resource_forbidden",row["structuralOrRoleFaults"])
            self.assertFalse(row["authorizationGranted"])
        all_grants={g for v in self.policy["roleGrants"].values() for g in v}
        self.assertEqual(all_grants,set(GRANTS["custodian"]) |
                         set(GRANTS["technical_reviewer_a"]) |
                         set(GRANTS["adjudicator"]))
        self.assertNotIn("modify_upstream",all_grants)
        self.assertNotIn("release_equipment",all_grants)

    def test_no_self_approval_or_reviewer_role_escalation(self):
        results=evaluate(self.policy,self.fixture)["results"]
        for kind in ("author_cannot_approve","reviewer_cannot_adjudicate",
                     "adjudicator_cannot_review","custodian_cannot_review",
                     "reviewer_cannot_read_index","author_private_case_denied"):
            row=next(r for r in results if r["kind"]==kind)
            self.assertIn("role_not_eligible",row["structuralOrRoleFaults"])
            self.assertFalse(row["authorizationGranted"])

    def test_policy_cannot_be_weakened_to_live_access_or_new_grants(self):
        forbidden=[
            "providerConfigured","oidcDiscoveryVerified",
            "jwksSignatureVerifierConnected","oidcAudienceRegistered",
            "externalRoleDirectoryConnected","sessionRevocationStoreConnected",
            "mfaAssuranceValidated","realAccessEnforcementConnected",
            "mayApproveTechnicalRelation","mayModifyUpstream",
            "mayCreateWorkOrder","mayExecuteTest","mayModifyEcm",
            "mayReleaseEquipment",
        ]
        for key in forbidden:
            policy=copy.deepcopy(self.policy)
            policy[key]=True
            with self.subTest(flag=key),self.assertRaises(ReviewRejected):
                validate_policy(policy)
        policy=copy.deepcopy(self.policy)
        policy["roleGrants"]["author"].append("submit_adjudication")
        with self.assertRaises(ReviewRejected):
            validate_policy(policy)
        policy=copy.deepcopy(self.policy)
        policy["defaultDeny"]=False
        with self.assertRaises(ReviewRejected):
            validate_policy(policy)
        policy=copy.deepcopy(self.policy)
        policy["syntheticIssuer"]="https://real-company.example.com"
        with self.assertRaises(ReviewRejected):
            validate_policy(policy)

    def test_fixture_spoof_and_credential_claims_rejected(self):
        for key in ("realIdentitiesPresent","realTokensPresent",
                    "liveProviderConnected"):
            fixture=copy.deepcopy(self.fixture)
            fixture[key]=True
            with self.subTest(flag=key),self.assertRaises(ReviewRejected):
                validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["profileActors"][2]["role"]="adjudicator"
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["scenarios"][0]["claims"]["issuerTrusted"]=True
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["scenarios"][0]["claims"]["signatureValidated"]=True
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["scenarios"][0]["claims"]["roleAssignmentVerified"]=True
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)

    def test_report_tampering_and_reordered_replay_detected(self):
        report=evaluate(self.policy,self.fixture)
        altered=copy.deepcopy(report)
        altered["results"][3]["authorizationGranted"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(altered,self.policy,self.fixture)
        altered=copy.deepcopy(report)
        altered["hypotheticalRoleEligibleCount"]=25
        with self.assertRaises(ReviewRejected):
            verify_report(altered,self.policy,self.fixture)
        altered=copy.deepcopy(report)
        altered["jwtSignaturesVerified"]=1
        with self.assertRaises(ReviewRejected):
            verify_report(altered,self.policy,self.fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["scenarios"].reverse()
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)

    def test_static_html_contains_no_interactions_or_private_information(self):
        report=evaluate(self.policy,self.fixture)
        html=render_html(report,self.policy,self.fixture)
        self.assertEqual(html.count("<section>"),30)
        self.assertIn("NO GO",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertNotIn("Bearer ",html)
        self.assertNotIn("REF-",html)
        with tempfile.TemporaryDirectory(prefix="cycle39-") as tmp:
            root=Path(tmp)
            main(["--output",str(root/"report.json"),
                  "--html",str(root/"report.html")])
            obj=json.loads((root/"report.json").read_text())
            self.assertEqual(obj["scenarioCount"],30)
            self.assertEqual(obj["actualGrantedCount"],0)

    def test_four_json_contracts_present(self):
        for path in (
            "federation-rbac-policy.schema.json",
            "federation-rbac-rehearsal.schema.json",
            "federation-rbac-report.schema.json",
            "federation-rbac-preflight-result.schema.json",
        ):
            schema=json.loads((ROOT/"contracts"/path).read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
