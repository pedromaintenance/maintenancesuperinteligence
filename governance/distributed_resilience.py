"""Cycle 42: fail-closed resilience tests against two real localhost TEST processes.

Never deploy these fault hooks or the hand-rolled synthetic login protocol.
No corporate OIDC, IAM, documents, SAP, ECM or equipment connections.
Successful cases authorize ONLY invented IRP resources inside a temporary lab.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import secrets
from threading import Event
import time

from governance.loopback_http_services import load as load_json
from governance.loopback_service_harness import (
    FIXTURE as PARENT_FIXTURE, health, login, post, running_services, step_up,
)
from governance.federation_rbac import current_public_packets
from pilot.change_review_packets import require, digest

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"governance/distributed-resilience-policy.v1.json"
FIXTURE=ROOT/"governance/distributed-resilience-fixture.v1.json"
LOOPBACK_POLICY=ROOT/"governance/loopback-service-policy.v1.json"
IDENTITY_POLICY=ROOT/"governance/isolated-identity-lab-policy.v1.json"
GUARDS=(
    "fault_controls_unavailable_in_default_mode",
    "fault_control_requires_interservice_key",
    "incomplete_active_upstream_denied",
    "upstream_503_denied",
    "upstream_timeout_denied",
    "rotation_mismatch_denied",
    "rotation_restores_only_synthetic_access",
    "old_service_key_revoked",
    "concurrent_cross_packet_requests_denied",
    "concurrent_operational_requests_denied",
    "revocation_race_has_only_allow_or_deny_results",
    "after_revocation_ack_all_requests_denied",
    "identity_process_outage_denied",
    "outage_has_no_cached_authorization",
    "expiry_during_introspection_denied",
)
CONTROL_PATHS=("/lab-fault-next-introspection","/lab-rotate-service-key")
FAULT_TYPES=(
    "delay_timeout", "expire_before_verify", "incomplete_active_response",
    "upstream_unavailable",
)
DENIALS=(
    "realIdpConnected","realHumanIdentitiesVerified",
    "realPrivateDocumentsAccessible","realCustomerSystemConnected",
    "enterpriseSecurityApproval","tlsOrMtlsEnabled",
    "mayWriteSAP","mayModifyEcm","mayCreateWorkOrder",
    "mayExecuteTest","mayReleaseEquipment",
)


def validate_policy(policy):
    require(isinstance(policy,dict) and set(policy)=={
        "schema","version","mode","bindHost","parentIdentityPolicyVersion",
        "parentLoopbackPolicyVersion","expectedGuardCount",
        "concurrentRequestsPerGroup","revocationRaceRequests",
        "testOnlyControlPaths","allowedIntrospectionFaults",
        "keyRotationRequiresExistingKey","faultControlsDisabledByDefault",
        "allowGrantOnUpstreamFailure","allowCachedAuthorizationOnOutage",
        "requireCompleteIntrospectionResponse","requirePostRevocationDenial",
        "assumeGlobalLinearizabilityAcrossProcesses",
        "simulatedServiceKeyLengthHex",*DENIALS}
        and policy["schema"]==
            "maintenance-superinteligence.distributed-resilience-policy.v1"
        and policy["version"]=="1.0.0"
        and policy["mode"]==
            "loopback_fault_injection_sandbox_never_production"
        and policy["bindHost"]=="127.0.0.1"
        and policy["parentIdentityPolicyVersion"]=="1.0.0"
        and policy["parentLoopbackPolicyVersion"]=="1.0.0"
        and type(policy["expectedGuardCount"]) is int
        and policy["expectedGuardCount"]==len(GUARDS)
        and type(policy["concurrentRequestsPerGroup"]) is int
        and policy["concurrentRequestsPerGroup"]==16
        and type(policy["revocationRaceRequests"]) is int
        and policy["revocationRaceRequests"]==16
        and policy["testOnlyControlPaths"]==list(CONTROL_PATHS)
        and policy["allowedIntrospectionFaults"]==list(FAULT_TYPES)
        and policy["keyRotationRequiresExistingKey"] is True
        and policy["faultControlsDisabledByDefault"] is True
        and policy["allowGrantOnUpstreamFailure"] is False
        and policy["allowCachedAuthorizationOnOutage"] is False
        and policy["requireCompleteIntrospectionResponse"] is True
        and policy["requirePostRevocationDenial"] is True
        and policy["assumeGlobalLinearizabilityAcrossProcesses"] is False
        and type(policy["simulatedServiceKeyLengthHex"]) is int
        and policy["simulatedServiceKeyLengthHex"]==64
        and all(policy[k] is False for k in DENIALS),
        "Cycle42 resilience policy weakened or falsely claims real authority")
    from governance.loopback_http_services import validate_policy as validate_loopback
    from governance.isolated_identity_lab import validate_policy as validate_identity
    validate_loopback(load_json(LOOPBACK_POLICY))
    validate_identity(load_json(IDENTITY_POLICY))
    return True


def validate_fixture(fixture):
    require(isinstance(fixture,dict) and set(fixture)=={
        "schema","version","mode","sourceCycle","guardNames",
        "targetSyntheticPacketId","deniedCrossPacketId",
        "syntheticReviewerRole","forbiddenAction","allowedAction",
        "noRealIdentityData","noRealDocumentation","noCorporateNetworkTraffic"}
        and fixture["schema"]==
            "maintenance-superinteligence.distributed-resilience-fixture.v1"
        and fixture["version"]=="1.0.0"
        and fixture["mode"]==
            "author_generated_faults_on_synthetic_loopback_services"
        and type(fixture["sourceCycle"]) is int
        and fixture["sourceCycle"]==41
        and fixture["guardNames"]==list(GUARDS)
        and fixture["targetSyntheticPacketId"]=="IRP-001"
        and fixture["deniedCrossPacketId"]=="IRP-002"
        and fixture["syntheticReviewerRole"]=="technical_reviewer_a"
        and fixture["forbiddenAction"]=="mayCreateWorkOrder"
        and fixture["allowedAction"]=="read_assigned_private_case"
        and all(fixture[k] is True for k in (
            "noRealIdentityData","noRealDocumentation",
            "noCorporateNetworkTraffic")),
        "Cycle42 fixture attempts to include real documents or altered guards")
    return True


def _grant_request(svc,fixture,token,timeout=None):
    from governance.loopback_http_services import request_json
    data={
        "token":token,
        "action":fixture["allowedAction"],
        "packetId":fixture["targetSyntheticPacketId"],
    }
    if timeout is not None:
        return request_json(svc["resource"],"/authorize",data,timeout=timeout)
    return post(svc["resource"],"/authorize",data)


def _valid_synthetic_grant(status,data):
    return (status==200 and isinstance(data,dict)
            and data.get("sandboxAllowed") is True
            and data.get("syntheticRecordId")=="SIMULATED-IRP-001"
            and data.get("realResourceAccess") is False
            and data.get("mayCreateWorkOrder") is False
            and data.get("mayReleaseEquipment") is False)


def _denied(status,data):
    return (status==403 and isinstance(data,dict)
            and data.get("sandboxAllowed") is False)


def _active_session(svc,fixture):
    status,token=login(svc,fixture["syntheticReviewerRole"])
    require(status==200 and isinstance(token,str),
            "synthetic identity session unavailable")
    step_up(svc,fixture["syntheticReviewerRole"],token)
    return token


def _record(guard_list,name,ok):
    require(name==GUARDS[len(guard_list)] and ok is True,
            "Cycle42 guard failed: "+name)
    guard_list.append({
        "guard":name,"passed":True,
        "realPrivateDataUsed":False,
        "operationalPermissionGranted":False,
    })


def _wave(svc,fixture,token,action,packet_id,count):
    def call(_):
        status,data=post(svc["resource"],"/authorize",{
            "token":token,"action":action,"packetId":packet_id})
        return status,data
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(call,range(count)))


def _check_fault(svc,fixture,token,mode,timeout=None):
    status,_=post(svc["identity"],"/lab-fault-next-introspection",
                  {"mode":mode},key=svc["key"])
    require(status==200,"sandbox fault injection not scheduled")
    return _grant_request(svc,fixture,token,timeout=timeout)


def evaluate(policy,fixture):
    """Execute actual HTTP fault injection against ephemeral local processes."""
    validate_policy(policy)
    validate_fixture(fixture)
    registry=current_public_packets()
    require({fixture["targetSyntheticPacketId"],fixture["deniedCrossPacketId"]}
            .issubset({p["packetId"] for p in registry["packets"]}),
            "source packet IDs absent from frozen public registry")
    base_policy=load_json(LOOPBACK_POLICY)
    base_fixture=load_json(PARENT_FIXTURE)
    guards=[]

    # When launched normally (Cycle41 or separately), test controls are 404.
    with running_services(base_policy,base_fixture,faults=False) as svc:
        status,_=post(svc["identity"],CONTROL_PATHS[0],
                      {"mode":"upstream_unavailable"},key=svc["key"])
        status2,_=post(svc["resource"],CONTROL_PATHS[1],
                       {"nextKey":secrets.token_hex(32)},key=svc["key"])
        _record(guards,GUARDS[0],status==404 and status2==404)

    with running_services(base_policy,base_fixture,faults=True) as svc:
        token=_active_session(svc,fixture)
        status,data=_grant_request(svc,fixture,token)
        require(_valid_synthetic_grant(status,data),
                "baseline authorized synthetic request unavailable")

        status,_=post(svc["identity"],CONTROL_PATHS[0],
                      {"mode":"upstream_unavailable"})
        status2,_=post(svc["identity"],CONTROL_PATHS[0],
                       {"mode":"upstream_unavailable"},key="0"*64)
        _record(guards,GUARDS[1],status==403 and status2==403)

        status,data=_check_fault(svc,fixture,token,
                                 "incomplete_active_response")
        _record(guards,GUARDS[2],_denied(status,data))

        status,data=_check_fault(svc,fixture,token,
                                 "upstream_unavailable")
        _record(guards,GUARDS[3],_denied(status,data))

        status,data=_check_fault(svc,fixture,token,
                                 "delay_timeout",
                                 timeout=base_policy["requestTimeoutSeconds"]+2)
        _record(guards,GUARDS[4],_denied(status,data))

        oldkey=svc["key"]
        newkey=secrets.token_hex(32)
        status,_=post(svc["identity"],CONTROL_PATHS[1],
                      {"nextKey":newkey},key=oldkey)
        deny_status,deny_data=_grant_request(svc,fixture,token)
        _record(guards,GUARDS[5],
                status==200 and _denied(deny_status,deny_data))

        status2,_=post(svc["resource"],CONTROL_PATHS[1],
                       {"nextKey":newkey},key=oldkey)
        svc["key"]=newkey
        allow_status,allow_data=_grant_request(svc,fixture,token)
        _record(guards,GUARDS[6],
                status2==200 and _valid_synthetic_grant(allow_status,allow_data))

        stale_status,_=post(svc["identity"],"/introspect",
                            {"token":token},key=oldkey)
        _record(guards,GUARDS[7],stale_status==403)

        wrong=_wave(svc,fixture,token,fixture["allowedAction"],
                    fixture["deniedCrossPacketId"],
                    policy["concurrentRequestsPerGroup"])
        _record(guards,GUARDS[8],
                len(wrong)==16 and all(_denied(*pair) for pair in wrong))

        operations=_wave(svc,fixture,token,fixture["forbiddenAction"],
                         fixture["targetSyntheticPacketId"],
                         policy["concurrentRequestsPerGroup"])
        _record(guards,GUARDS[9],
                len(operations)==16
                and all(_denied(*pair) for pair in operations))

        # In-flight requests can have been checked before a revocation was
        # acknowledged. Do NOT claim cross-service strict linearizability.
        race_token=_active_session(svc,fixture)
        begin=Event()
        def racing(_):
            begin.wait()
            return _grant_request(svc,fixture,race_token)
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures=[pool.submit(racing,i)
                     for i in range(policy["revocationRaceRequests"])]
            begin.set()
            revoke_status,_=post(svc["identity"],"/revoke",
                                 {"token":race_token})
            race=[future.result(timeout=6) for future in futures]
        bounded=all(
            (_valid_synthetic_grant(status,data) or _denied(status,data))
            for status,data in race)
        _record(guards,GUARDS[10],
                revoke_status==200 and len(race)==16 and bounded)

        after=_wave(svc,fixture,race_token,fixture["allowedAction"],
                    fixture["targetSyntheticPacketId"],
                    policy["concurrentRequestsPerGroup"])
        _record(guards,GUARDS[11],
                len(after)==16 and all(_denied(*pair) for pair in after))

        alive=_active_session(svc,fixture)
        pre_status,pre_data=_grant_request(svc,fixture,alive)
        require(_valid_synthetic_grant(pre_status,pre_data),
                "identity did not authorize before outage")
        svc["identityProcess"].terminate()
        svc["identityProcess"].wait(timeout=3)
        require(svc["identityProcess"].poll() is not None
                and health(svc["resource"]) is not None,
                "resource must remain up when identity is down")
        down_status,down_data=_grant_request(svc,fixture,alive)
        _record(guards,GUARDS[12],_denied(down_status,down_data))
        again_status,again_data=_grant_request(svc,fixture,alive)
        _record(guards,GUARDS[13],_denied(again_status,again_data))

    # Next introspection expires the token *during* the request, before the
    # identity service reads its session; it cannot get a stale positive.
    with running_services(base_policy,base_fixture,faults=True) as svc:
        expiry_token=_active_session(svc,fixture)
        status,data=_grant_request(svc,fixture,expiry_token)
        require(_valid_synthetic_grant(status,data),
                "baseline session missing before injected expiry")
        status,data=_check_fault(svc,fixture,expiry_token,
                                 "expire_before_verify")
        _record(guards,GUARDS[14],_denied(status,data))

    require(len(guards)==policy["expectedGuardCount"]
            and all(g["passed"] is True for g in guards),
            "resilience guard record incomplete")
    return {
        "schema":"maintenance-superinteligence.distributed-resilience-report.v1",
        "version":"1.0.0",
        "mode":"multi_process_loopback_fault_injection_synthetic_only",
        "policyDigest":digest(policy),
        "fixtureDigest":digest(fixture),
        "parentPacketRegistryDigest":digest(registry),
        "guardCount":len(guards),
        "guardChecksPassed":len(guards),
        "crossPacketConcurrentRequests":len(wrong),
        "crossPacketConcurrentDenied":len(wrong),
        "operationalConcurrentRequests":len(operations),
        "operationalConcurrentDenied":len(operations),
        "revocationRaceRequests":len(race),
        "revocationRaceOutcomesBounded":bounded,
        "afterRevocationAckRequests":len(after),
        "afterRevocationAckDenied":len(after),
        "faultEndpointsDefaultDisabled":True,
        "serviceKeyRotationFailedClosed":True,
        "serviceKeyRotationRestoredSyntheticOnly":True,
        "sourceRulesModified":False,
        "allGuardResults":guards,
        "strictGlobalLinearizabilityProven":False,
        "realIdentityProviderConnected":False,
        "realUsersAuthenticated":0,
        "realDocumentsAccessed":0,
        "realPermissionsGranted":0,
        "realOperationalActions":0,
        "tlsOrMtlsEnabled":False,
        "mayCreateWorkOrder":False,
        "mayExecuteTest":False,
        "mayModifyEcm":False,
        "mayReleaseEquipment":False,
        "decision":"no_go_fault_tolerant_synthetic_loopback_not_enterprise_authorization",
    }


def verify_report(report,policy,fixture):
    require(report==evaluate(policy,fixture),
            "resilience report forged or diverges from executed fault scenarios")
    return True


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    report=evaluate(load_json(POLICY),load_json(FIXTURE))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    return report


if __name__=="__main__":
    main()
