"""Cycle 41 integration: actual subprocess-to-subprocess localhost API calls.

No real OIDC, corporate credentials, enterprise ACLs, OEM documents or equipment.
These tests exercise only ephemeral synthetic accounts and packet IDs.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request

from governance.loopback_http_services import (
    POLICY_PATH, OPENER, validate_policy, request_json, load,
)
from governance.loopback_service_harness import (
    ROOT, FIXTURE, validate_fixture, running_services, login, step_up, post,
    test_requests as exercise_scenarios, test_adversarial_guards,
    evaluate, verify_report, main, health,
)
from pilot.change_review_packets import ReviewRejected


class LoopbackServiceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=load(POLICY_PATH)
        cls.fixture=load(FIXTURE)
        cls.report=evaluate(cls.policy,cls.fixture)

    def test_12_real_http_synthetic_actions_and_12_adversarial_guards(self):
        r=self.report
        self.assertEqual(r["scenarioCount"],12)
        self.assertEqual(r["sandboxAuthorizedActions"],6)
        self.assertEqual(r["sandboxDeniedActions"],6)
        self.assertEqual(r["guardCount"],12)
        self.assertEqual(r["guardChecksPassed"],12)
        self.assertEqual(len(r["scenarios"]),12)
        self.assertEqual(len(r["securityGuards"]),12)
        self.assertTrue(all(s["expectationMet"] for s in r["scenarios"]))
        self.assertTrue(all(g["passed"] for g in r["securityGuards"]))
        self.assertEqual(r["decision"],
            "no_go_loopback_synthetic_http_only_no_external_idp_or_real_resources")

    def test_two_separate_loopback_processes_and_cross_process_security(self):
        r=self.report
        for key in ("separateServiceProcessIdsVerified",
                    "identityServiceBoundToLoopback",
                    "resourceServiceBoundToLoopback",
                    "crossProcessHttpIntrospectionExercised",
                    "introspectionServiceKeyChecked",
                    "sessionMacAndMfaCheckedInIdentityService",
                    "resourceRoleAndPacketAclChecked"):
            self.assertIs(r[key],True,key)

    def test_denials_cover_revocation_expiration_mfa_and_elevation(self):
        kinds={x["guard"] for x in self.report["securityGuards"]}
        self.assertEqual(kinds,{
            "incorrect_password_denied", "private_access_requires_mfa",
            "incorrect_totp_denied", "totp_replay_denied",
            "unkeyed_introspection_denied",
            "incorrect_service_key_denied",
            "tampered_hmac_session_denied",
            "unknown_route_denied", "role_claim_in_request_denied",
            "foreign_session_denied", "revoked_session_denied",
            "cross_process_expiry_denied",
        })
        denied={x["kind"] for x in self.report["scenarios"]
                if not x["sandboxResourceActionAllowed"]}
        self.assertEqual(denied,{
            "deny_author_private", "deny_reviewer_adjudication",
            "deny_adjudicator_review", "deny_unassigned_resource",
            "deny_operational_action", "deny_equipment_release",
        })

    def test_no_real_access_or_operational_authority_in_report(self):
        r=self.report
        for key in ("realIdentityProviderConnected", "tlsOrMtlsEnabled",
                    "signedIdentityCertificatesVerified",
                    "mayCreateWorkOrder", "mayExecuteTest",
                    "mayModifyEcm", "mayReleaseEquipment"):
            self.assertIs(r[key],False,key)
        for key in ("realUsersAuthenticated","realOIDCTokensValidated",
                    "realPrivateDocumentsAccessed","realPermissionsGranted",
                    "realOperationalActions"):
            self.assertEqual(r[key],0,key)
        for item in r["scenarios"]:
            self.assertFalse(item["realUserAuthenticated"])
            self.assertFalse(item["realDocumentAccessed"])
            self.assertFalse(item["operationalAuthority"])

    def test_working_separate_processes_are_127_loopback_only(self):
        with running_services(self.policy,self.fixture) as svc:
            i=health(svc["identity"])
            a=health(svc["resource"])
            self.assertEqual(i["role"],"identity")
            self.assertEqual(a["role"],"resource")
            self.assertEqual(i["boundHost"],"127.0.0.1")
            self.assertEqual(a["boundHost"],"127.0.0.1")
            self.assertNotEqual(i["pid"],a["pid"])
            self.assertEqual(i["pid"],svc["identityPid"])
            self.assertEqual(a["pid"],svc["resourcePid"])
            status,token=login(svc,"technical_reviewer_a")
            self.assertEqual(status,200)
            no_mfa,_=post(svc["resource"],"/authorize",{
                "token":token,"action":"read_assigned_private_case",
                "packetId":"IRP-001"})
            self.assertEqual(no_mfa,403)
            step_up(svc,"technical_reviewer_a",token)
            authorized,data=post(svc["resource"],"/authorize",{
                "token":token,"action":"read_assigned_private_case",
                "packetId":"IRP-001"})
            self.assertEqual(authorized,200)
            self.assertEqual(data["syntheticRecordId"],"SIMULATED-IRP-001")
            self.assertIs(data["realResourceAccess"],False)

    def test_service_only_accepts_json_and_rejects_large_payloads(self):
        with running_services(self.policy,self.fixture) as svc:
            i=svc["identity"]
            code,_=post(i,"/login",{"subject":"synthetic-author",
                                     "password":"x"*5000})
            self.assertEqual(code,400)
            bad=Request(i+"/login",data=b"not json",
                headers={"Content-Type":"text/plain"},method="POST")
            with self.assertRaises(HTTPError) as ctx:
                OPENER.open(bad,timeout=3)
            self.assertEqual(ctx.exception.code,400)

    def test_introspection_does_not_trust_public_client(self):
        with running_services(self.policy,self.fixture) as svc:
            code,token=login(svc,"technical_reviewer_a")
            self.assertEqual(code,200)
            step_up(svc,"technical_reviewer_a",token)
            status,_=post(svc["identity"],"/introspect",{"token":token})
            self.assertEqual(status,403)
            status,_=post(svc["identity"],"/introspect",{"token":token},
                          key="0"*64)
            self.assertEqual(status,403)
            status,data=post(svc["identity"],"/introspect",{"token":token},
                             key=svc["key"])
            self.assertEqual(status,200)
            self.assertTrue(data["active"])
            self.assertFalse(data["realOIDCAuthenticated"])
            self.assertFalse(data["realIdentityVerified"])
            self.assertEqual(data["assignments"],["IRP-001"])

    def test_policy_fail_closed_on_non_loopback_or_real_identity_claim(self):
        validate_policy(self.policy)
        changes=[
            ("bindHost","0.0.0.0"),
            ("scheme","https"),
            ("tokenFormat","jwt_id_token"),
            ("realIdpConnected",True),
            ("realOIDCImplemented",True),
            ("realJwtSignaturesVerified",True),
            ("tlsOrMutualTlsEnabled",True),
            ("realDocumentsAccessible",True),
            ("mayCreateWorkOrder",True),
            ("mayReleaseEquipment",True),
            ("identityProcessRequired",False),
            ("expectedGuardCount",0),
        ]
        for field,value in changes:
            p=copy.deepcopy(self.policy)
            p[field]=value
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_policy(p)

    def test_fixture_spoofed_real_users_rejected(self):
        for key in ("realUsersPresent","realPrivateDataPresent",
                    "realIdentityProofCollected"):
            f=copy.deepcopy(self.fixture)
            f[key]=True
            with self.subTest(field=key),self.assertRaises(ReviewRejected):
                validate_fixture(f)
        f=copy.deepcopy(self.fixture)
        f["profileAssignments"]["author"]=["IRP-001"]
        with self.assertRaises(ReviewRejected):
            validate_fixture(f)

    def test_loopback_client_rejects_any_external_host(self):
        for url in ("https://127.0.0.1:8000",
                    "http://0.0.0.0:8000",
                    "http://localhost:8000",
                    "http://10.0.0.1:8000",
                    "http://127.0.0.1:8000/path",
                    "http://127.0.0.1:8000@outside"):
            with self.subTest(url=url),self.assertRaises(ReviewRejected):
                request_json(url,"/authorize",{"foo":"bar"})

    def test_changing_generated_report_is_detected(self):
        report=copy.deepcopy(self.report)
        report["realUsersAuthenticated"]=1
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.policy,self.fixture)
        report=copy.deepcopy(self.report)
        report["securityGuards"][0]["passed"]=False
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.policy,self.fixture)

    def test_cli_generates_redacted_report_and_four_contracts(self):
        with tempfile.TemporaryDirectory(prefix="cycle41-") as folder:
            out=Path(folder)/"report.json"
            result=main(["--output",str(out)])
            self.assertEqual(result["guardChecksPassed"],12)
            data=out.read_text(encoding="utf-8")
            self.assertEqual(json.loads(data)["sandboxAuthorizedActions"],6)
            for word in ("LAB_SERVICE_KEY","LAB_BOOTSTRAP","SyntheticOnly-",
                         "seedHex","passwordHash","/home/runner","Bearer "):
                self.assertNotIn(word,data)
        for name in ("loopback-service-policy.schema.json",
                     "loopback-service-scenario.schema.json",
                     "loopback-service-guard.schema.json",
                     "loopback-service-report.schema.json"):
            obj=load(ROOT/"contracts"/name)
            self.assertEqual(obj["$schema"],
                "https://json-schema.org/draft/2020-12/schema")
            self.assertIs(obj["additionalProperties"],False)


if __name__=="__main__":
    unittest.main()
