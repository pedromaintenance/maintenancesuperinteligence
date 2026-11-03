"""Cycle 42: failure injection and concurrency safeguards for loopback-only lab.

No real IAM, external identity, corporate documents or operational authority.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import secrets
import tempfile
import unittest

from governance.distributed_resilience import (
    POLICY,FIXTURE,GUARDS,FAULT_TYPES,CONTROL_PATHS,
    validate_policy,validate_fixture,evaluate,verify_report,main,
)
from governance.loopback_http_services import request_json,load as load_json
from governance.loopback_service_harness import (
    running_services,login,step_up,post,
    FIXTURE as PARENT_FIXTURE,
)
from governance.distributed_resilience import LOOPBACK_POLICY
from pilot.change_review_packets import ReviewRejected


class Cycle42DistributedResilienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=load_json(POLICY)
        cls.fixture=load_json(FIXTURE)
        cls.report=evaluate(cls.policy,cls.fixture)

    def test_15_guards_real_cross_process_faults_and_no_go(self):
        report=self.report
        self.assertEqual(report["guardCount"],15)
        self.assertEqual(report["guardChecksPassed"],15)
        self.assertEqual(len(report["allGuardResults"]),15)
        self.assertEqual([g["guard"] for g in report["allGuardResults"]],
                         list(GUARDS))
        self.assertTrue(all(g["passed"] is True for g in report["allGuardResults"]))
        self.assertEqual(report["decision"],
           "no_go_fault_tolerant_synthetic_loopback_not_enterprise_authorization")

    def test_failures_deny_without_cached_authorization(self):
        names={g["guard"] for g in self.report["allGuardResults"]}
        self.assertTrue({
            "incomplete_active_upstream_denied",
            "upstream_503_denied",
            "upstream_timeout_denied",
            "identity_process_outage_denied",
            "outage_has_no_cached_authorization",
            "expiry_during_introspection_denied",
        }.issubset(names))
        self.assertTrue(self.report["faultEndpointsDefaultDisabled"])

    def test_concurrent_wrong_scope_and_operational_requests_all_denied(self):
        self.assertEqual(self.report["crossPacketConcurrentRequests"],16)
        self.assertEqual(self.report["crossPacketConcurrentDenied"],16)
        self.assertEqual(self.report["operationalConcurrentRequests"],16)
        self.assertEqual(self.report["operationalConcurrentDenied"],16)

    def test_revocation_race_is_truthful_about_in_flight_boundary(self):
        r=self.report
        self.assertEqual(r["revocationRaceRequests"],16)
        self.assertTrue(r["revocationRaceOutcomesBounded"])
        self.assertEqual(r["afterRevocationAckRequests"],16)
        self.assertEqual(r["afterRevocationAckDenied"],16)
        self.assertFalse(r["strictGlobalLinearizabilityProven"])
        self.assertNotIn("revocationRaceAllDenied",r)
        self.assertNotIn("inFlightRequestsGuaranteedRevoked",r)

    def test_key_rotation_is_fail_closed_and_old_keys_rejected(self):
        r=self.report
        self.assertTrue(r["serviceKeyRotationFailedClosed"])
        self.assertTrue(r["serviceKeyRotationRestoredSyntheticOnly"])
        guards={g["guard"] for g in r["allGuardResults"]}
        self.assertTrue({
            "rotation_mismatch_denied",
            "rotation_restores_only_synthetic_access",
            "old_service_key_revoked",
        }.issubset(guards))

    def test_no_real_access_or_authority(self):
        report=self.report
        for key in ("realIdentityProviderConnected","tlsOrMtlsEnabled",
                    "mayCreateWorkOrder","mayExecuteTest","mayModifyEcm",
                    "mayReleaseEquipment","sourceRulesModified",
                    "strictGlobalLinearizabilityProven"):
            self.assertIs(report[key],False,key)
        for key in ("realUsersAuthenticated","realDocumentsAccessed",
                    "realPermissionsGranted","realOperationalActions"):
            self.assertEqual(report[key],0,key)
        for guard in report["allGuardResults"]:
            self.assertFalse(guard["realPrivateDataUsed"])
            self.assertFalse(guard["operationalPermissionGranted"])

    def test_policy_no_real_credentials_or_fallback_privileges(self):
        validate_policy(self.policy)
        for key in ("realIdpConnected","realHumanIdentitiesVerified",
                    "realPrivateDocumentsAccessible","realCustomerSystemConnected",
                    "enterpriseSecurityApproval","tlsOrMtlsEnabled",
                    "mayWriteSAP","mayModifyEcm","mayCreateWorkOrder",
                    "mayExecuteTest","mayReleaseEquipment"):
            policy=copy.deepcopy(self.policy)
            policy[key]=True
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_policy(policy)
        for key,value in (
            ("bindHost","0.0.0.0"),
            ("expectedGuardCount",14),
            ("concurrentRequestsPerGroup",0),
            ("allowGrantOnUpstreamFailure",True),
            ("allowCachedAuthorizationOnOutage",True),
            ("requireCompleteIntrospectionResponse",False),
            ("requirePostRevocationDenial",False),
            ("assumeGlobalLinearizabilityAcrossProcesses",True),
            ("faultControlsDisabledByDefault",False),
        ):
            policy=copy.deepcopy(self.policy)
            policy[key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_policy(policy)

    def test_fixture_cannot_drop_evidence_guard_or_import_real_data(self):
        validate_fixture(self.fixture)
        for key in ("noRealIdentityData","noRealDocumentation",
                    "noCorporateNetworkTraffic"):
            fixture=copy.deepcopy(self.fixture)
            fixture[key]=False
            with self.subTest(field=key),self.assertRaises(ReviewRejected):
                validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["guardNames"]=fixture["guardNames"][:-1]
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["targetSyntheticPacketId"]="IRP-999"
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)
        fixture=copy.deepcopy(self.fixture)
        fixture["sourceCycle"]=42
        with self.assertRaises(ReviewRejected):
            validate_fixture(fixture)

    def test_fault_endpoints_off_under_original_cycle41_mode(self):
        with running_services(load_json(LOOPBACK_POLICY),
                              load_json(PARENT_FIXTURE),faults=False) as svc:
            for target,path,body in (
                ("identity","/lab-fault-next-introspection",
                 {"mode":"incomplete_active_response"}),
                ("identity","/lab-rotate-service-key",
                 {"nextKey":secrets.token_hex(32)}),
                ("resource","/lab-rotate-service-key",
                 {"nextKey":secrets.token_hex(32)}),
            ):
                status,_=post(svc[target],path,body,key=svc["key"])
                self.assertEqual(status,404)

    def test_fault_controls_require_the_existing_key_and_known_fault_mode(self):
        with running_services(load_json(LOOPBACK_POLICY),
                              load_json(PARENT_FIXTURE),faults=True) as svc:
            code,_=post(svc["identity"],CONTROL_PATHS[0],
                        {"mode":"upstream_unavailable"})
            self.assertEqual(code,403)
            code,_=post(svc["identity"],CONTROL_PATHS[0],
                        {"mode":"upstream_unavailable"},key="f"*64)
            self.assertEqual(code,403)
            code,_=post(svc["identity"],CONTROL_PATHS[0],
                        {"mode":"unknown_fault"},key=svc["key"])
            self.assertEqual(code,400)
            code,_=post(svc["resource"],CONTROL_PATHS[1],
                        {"nextKey":"wrong"},key=svc["key"])
            self.assertEqual(code,400)

    def test_original_services_remain_usable_after_harness_additions(self):
        with running_services(load_json(LOOPBACK_POLICY),
                              load_json(PARENT_FIXTURE),faults=False) as svc:
            status,token=login(svc,"technical_reviewer_a")
            self.assertEqual(status,200)
            step_up(svc,"technical_reviewer_a",token)
            code,data=post(svc["resource"],"/authorize",{
                "token":token,"action":"read_assigned_private_case",
                "packetId":"IRP-001"})
            self.assertEqual(code,200)
            self.assertTrue(data["sandboxAllowed"])
            self.assertFalse(data["realResourceAccess"])

    def test_client_cannot_leave_loopback(self):
        for url in ("http://localhost:9000","http://10.0.0.1:9000",
                    "https://127.0.0.1:9000",
                    "http://0.0.0.0:9000",
                    "http://127.0.0.1:9000/path"):
            with self.subTest(url=url),self.assertRaises(ReviewRejected):
                request_json(url,"/introspect",{"token":"fake"})

    def test_report_tampering_detected_by_reexecution(self):
        report=copy.deepcopy(self.report)
        report["afterRevocationAckDenied"]=0
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.policy,self.fixture)
        report=copy.deepcopy(self.report)
        report["allGuardResults"][1]["passed"]=False
        with self.assertRaises(ReviewRejected):
            verify_report(report,self.policy,self.fixture)

    def test_json_cli_no_secrets_and_four_schema_files(self):
        with tempfile.TemporaryDirectory(prefix="cycle42-") as directory:
            target=Path(directory)/"report.json"
            r=main(["--output",str(target)])
            self.assertEqual(r["guardChecksPassed"],15)
            body=target.read_text(encoding="utf-8")
            for forbidden in ("LAB_SERVICE_KEY","LAB_BOOTSTRAP",
                              "SyntheticOnly-","seedHex","token",
                              "nextKey","/home/runner","Bearer "):
                self.assertNotIn(forbidden,body)
            self.assertEqual(json.loads(body)["realPermissionsGranted"],0)
        root=Path(__file__).resolve().parents[1]
        for path in (
            "distributed-resilience-policy.schema.json",
            "distributed-resilience-fixture.schema.json",
            "distributed-resilience-guard.schema.json",
            "distributed-resilience-report.schema.json",
        ):
            schema=json.loads((root/"contracts"/path).read_text())
            self.assertEqual(schema["$schema"],
                             "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
