"""Cycle 40: isolated credentials, signed lab sessions, MFA, revocation and ACL."""
from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import tempfile
import unittest

from governance.isolated_identity_lab import (
    POLICY, FIXTURE, IsolatedLab, totp, load, validate_policy,
    validate_fixture, evaluate, verify_report, main,
)
from pilot.change_review_packets import ReviewRejected


class Cycle40IsolatedIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=load(POLICY)
        cls.fixture=load(FIXTURE)

    def setUp(self):
        self.now=1793286000
        self.lab=IsolatedLab(self.policy,["IRP-001","IRP-002"],
                             secrets.token_bytes(32))
        self.password="Synthetic-Lab-Only-"+secrets.token_hex(10)
        self.seed=secrets.token_bytes(20)
        self.lab.register("synthetic-reviewer-a","technical_reviewer_a",
                          self.password,self.seed,["IRP-001"])

    def login(self):
        return self.lab.login("synthetic-reviewer-a",self.password,self.now)

    def mfa(self,token):
        return self.lab.step_up(token,totp(self.seed,self.now),self.now)

    def allowed(self,token,action="read_assigned_private_case",
                packet="IRP-001",now=None):
        return self.lab.authorize(token,action,packet,
                                  self.now if now is None else now)

    def test_full_rehearsal_12_cases_real_synthetic_acl_not_external_auth(self):
        r=evaluate(self.policy,self.fixture)
        self.assertTrue(verify_report(r,self.policy,self.fixture))
        self.assertEqual(r["scenarioCount"],12)
        self.assertEqual(r["sandboxAuthorizedActions"],6)
        self.assertEqual(r["sandboxDeniedActions"],6)
        self.assertEqual(r["syntheticCredentialsVerified"],12)
        self.assertEqual(r["syntheticTotpValidated"],12)
        self.assertEqual(r["syntheticSessionRevocations"],12)
        self.assertEqual(r["realUsersAuthenticated"],0)
        self.assertEqual(r["realResourcePermissionsGranted"],0)
        self.assertEqual(r["realPrivateDocumentsAccessed"],0)
        self.assertEqual(r["realOperationalActions"],0)
        self.assertFalse(r["realOIDCOrIdPConnected"])
        self.assertFalse(r["sourceRulesChanged"])
        self.assertEqual(r["decision"],
            "no_go_synthetic_lab_only_external_idp_and_acl_not_integrated")
        for item in r["results"]:
            self.assertFalse(item["realOIDCAuthenticated"])
            self.assertFalse(item["realCompanyIdentityVerified"])
            self.assertFalse(item["realPrivateDocumentsRead"])
            self.assertFalse(item["realOperationalAuthorizationGranted"])

    def test_password_only_session_does_not_unlock_synthetic_private_data(self):
        token=self.login()
        decision=self.allowed(token)
        self.assertFalse(decision["sandboxResourceActionAllowed"])
        self.assertEqual(decision["reason"],"mfa_required")
        self.assertIsNone(self.lab.synthetic_read(token,"IRP-001",self.now))
        self.mfa(token)
        result=self.allowed(token)
        self.assertTrue(result["sandboxResourceActionAllowed"])
        self.assertFalse(result["realPrivateDocumentsRead"])
        self.assertEqual(self.lab.synthetic_read(token,"IRP-001",self.now),
                         "SYNTHETIC-CASE-IRP-001")
        self.assertEqual(self.lab.audit_summary()["realRequestsExecuted"],0)

    def test_bad_password_and_nonexistent_account_fail(self):
        with self.assertRaises(ReviewRejected):
            self.lab.login("synthetic-reviewer-a","wrong password",self.now)
        with self.assertRaises(ReviewRejected):
            self.lab.login("real-company-person",self.password,self.now)

    def test_totp_invalid_replayed_and_expired_session(self):
        token=self.login()
        with self.assertRaises(ReviewRejected):
            self.lab.step_up(token,"000",self.now)
        self.mfa(token)
        with self.assertRaises(ReviewRejected):
            self.mfa(token)
        expired=self.allowed(token,now=self.now+901)
        self.assertEqual(expired["reason"],"invalid_session")
        self.assertFalse(expired["sandboxResourceActionAllowed"])

    def test_revoke_invalidates_signed_token_even_inside_ttl(self):
        token=self.login()
        self.mfa(token)
        self.assertTrue(self.allowed(token)["sandboxResourceActionAllowed"])
        self.lab.revoke(token,self.now)
        decision=self.allowed(token)
        self.assertFalse(decision["sandboxResourceActionAllowed"])
        self.assertEqual(decision["reason"],"invalid_session")
        with self.assertRaises(ReviewRejected):
            self.lab.revoke(token,self.now)

    def test_signature_tampering_and_foreign_signer_never_authorize(self):
        token=self.login()
        self.mfa(token)
        body,mac=token.split(".")
        forged=body+"."+("A" if mac[0]!="A" else "B")+mac[1:]
        decision=self.allowed(forged)
        self.assertFalse(decision["sandboxResourceActionAllowed"])
        foreign=IsolatedLab(self.policy,["IRP-001","IRP-002"],
                            secrets.token_bytes(32))
        result=foreign.authorize(token,"read_assigned_private_case",
                                 "IRP-001",self.now)
        self.assertFalse(result["sandboxResourceActionAllowed"])

    def test_self_signed_role_escalation_rejected(self):
        token=self.login()
        self.mfa(token)
        body,mac=token.split(".")
        raw=base64.urlsafe_b64decode(body+"="*((-len(body))%4))
        obj=json.loads(raw.decode())
        obj["role"]="adjudicator"
        newbody=base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")
        forged=newbody+"."+mac
        r=self.allowed(forged,"submit_adjudication")
        self.assertFalse(r["sandboxResourceActionAllowed"])
        self.assertFalse(r["realOperationalAuthorizationGranted"])

    def test_cross_packet_authorization_fails_after_mfa(self):
        token=self.login()
        self.mfa(token)
        result=self.allowed(token,packet="IRP-002")
        self.assertFalse(result["sandboxResourceActionAllowed"])
        self.assertEqual(result["reason"],"packet_not_assigned")
        self.assertIsNone(self.lab.synthetic_read(token,"IRP-002",self.now))

    def test_unknown_packet_and_operations_fail_default_deny(self):
        token=self.login()
        self.mfa(token)
        for action in ("mayCreateWorkOrder","modify_upstream",
                       "modify_ecm","release_equipment","delete_audit_log"):
            res=self.allowed(token,action)
            with self.subTest(action=action):
                self.assertFalse(res["sandboxResourceActionAllowed"])
                self.assertEqual(res["reason"],"unknown_or_operational_action")
        res=self.allowed(token,packet="IRP-999")
        self.assertEqual(res["reason"],"unknown_synthetic_resource")

    def test_separation_between_reviewer_and_adjudicator(self):
        token=self.login()
        self.mfa(token)
        denied=self.allowed(token,"submit_adjudication")
        self.assertEqual(denied["reason"],"role_denied")
        allowed=self.allowed(token,"submit_technical_opinion")
        self.assertTrue(allowed["sandboxResourceActionAllowed"])
        self.assertFalse(allowed["realOperationalAuthorizationGranted"])

    def test_two_users_have_distinct_sessions_and_no_shadow_identities(self):
        otherpwd="Synthetic-Lab-Only-"+secrets.token_hex(10)
        otherseed=secrets.token_bytes(20)
        self.lab.register("synthetic-adjudicator","adjudicator",
                          otherpwd,otherseed,["IRP-001"])
        a=self.login()
        b=self.lab.login("synthetic-adjudicator",otherpwd,self.now)
        self.assertNotEqual(a,b)
        self.mfa(a)
        self.lab.step_up(b,totp(otherseed,self.now),self.now)
        self.assertFalse(self.allowed(a,"submit_adjudication")
                         ["sandboxResourceActionAllowed"])
        self.assertTrue(self.allowed(b,"submit_adjudication")
                        ["sandboxResourceActionAllowed"])

    def test_duplicate_user_and_unsafe_registration_rejected(self):
        with self.assertRaises(ReviewRejected):
            self.lab.register("synthetic-reviewer-a","adjudicator",self.password,
                              secrets.token_bytes(20),["IRP-001"])
        with self.assertRaises(ReviewRejected):
            self.lab.register("company-person","technical_reviewer_b",self.password,
                              secrets.token_bytes(20),["IRP-001"])
        with self.assertRaises(ReviewRejected):
            self.lab.register("synthetic-author","author",self.password,
                              secrets.token_bytes(20),["IRP-001"])
        with self.assertRaises(ReviewRejected):
            self.lab.register("synthetic-outsider","technical_reviewer_b",
                              self.password,secrets.token_bytes(20),["IRP-999"])

    def test_policy_never_claims_real_provider_or_real_authority(self):
        for flag in ("realIdpConnected","realOIDCImplemented",
                     "realCompanyAccountsUsed","realMFAProviderConnected",
                     "persistentSessionStoreConnected",
                     "persistentAuditStoreConnected",
                     "realPrivateDocumentsAccessible",
                     "operationalAuthorityGranted","mayModifyUpstreamRules",
                     "mayCreateWorkOrder","mayExecuteTest","mayModifyEcm",
                     "mayReleaseEquipment"):
            p=copy.deepcopy(self.policy)
            p[flag]=True
            with self.subTest(flag=flag),self.assertRaises(ReviewRejected):
                validate_policy(p)
        p=copy.deepcopy(self.policy)
        p["sessionTTLSeconds"]=86400
        with self.assertRaises(ReviewRejected):
            validate_policy(p)

    def test_fixture_no_real_data_or_extra_roles_or_unsafe_assignments(self):
        for f in ("realUsersPresent","realPrivateDataPresent",
                  "realIdentityProofCollected"):
            fixture=copy.deepcopy(self.fixture)
            fixture[f]=True
            with self.subTest(flag=f),self.assertRaises(ReviewRejected):
                validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["profileAssignments"]["author"]=["IRP-001"]
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["allowedPacketIds"].append("IRP-999")
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)

    def test_untrusted_report_cannot_forge_real_access(self):
        report=evaluate(self.policy,self.fixture)
        report["realUsersAuthenticated"]=1
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.policy,self.fixture)
        report=evaluate(self.policy,self.fixture)
        report["results"][0]["realOperationalAuthorizationGranted"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.policy,self.fixture)

    def test_cli_and_json_contracts(self):
        with tempfile.TemporaryDirectory(prefix="cycle40-lab-") as tmp:
            path=Path(tmp)/"report.json"
            r=main(["--output",str(path)])
            self.assertEqual(r["sandboxAuthorizedActions"],6)
            self.assertEqual(json.loads(path.read_text())["realUsersAuthenticated"],0)
            self.assertNotIn("Synthetic-Lab-Only",path.read_text())
        for n in ("isolated-identity-lab-policy.schema.json",
                  "isolated-identity-lab-rehearsal.schema.json",
                  "isolated-identity-lab-result.schema.json",
                  "isolated-identity-lab-report.schema.json"):
            schema=json.loads((Path(__file__).resolve().parents[1]/
                               "contracts"/n).read_text())
            self.assertEqual(schema["$schema"],
                             "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
