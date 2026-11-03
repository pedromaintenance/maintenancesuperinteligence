"""Cycle 41: launch two independent loopback HTTP processes for synthetic cases.

The harness runs ephemeral tests, terminates both subprocesses, and outputs only
aggregated outcomes: never passwords, MFA seeds, bearer strings or service keys.
No remote network or corporate identity integration is possible by design.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request

from governance.loopback_http_services import (
    POLICY_PATH, OPENER, load, validate_policy, request_json,
)
from governance.isolated_identity_lab import (
    FIXTURE, totp, validate_fixture,
)
from governance.federation_rbac import current_public_packets
from pilot.change_review_packets import require, digest

ROOT = Path(__file__).resolve().parents[1]


def allocate_port():
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1",0))
        return sock.getsockname()[1]


def health(url):
    try:
        with OPENER.open(Request(url+"/health",method="GET"),timeout=0.6) as response:
            if response.status != 200:
                return None
            return json.loads(response.read(1024))
    except (HTTPError,URLError,OSError,TimeoutError,ValueError):
        return None


def await_healthy(process,url,role):
    limit=time.monotonic()+8
    while time.monotonic()<limit:
        if process.poll() is not None:
            raise RuntimeError("synthetic loopback service process exited")
        result=health(url)
        if result is not None:
            require(result.get("ok") is True
                    and result.get("role")==role
                    and result.get("boundHost")=="127.0.0.1"
                    and type(result.get("pid")) is int
                    and result.get("pid")==process.pid,
                    "service identity/loopback binding mismatch")
            return result
        time.sleep(0.06)
    raise RuntimeError("synthetic loopback service failed to start")


def bootstrap_accounts(fixture):
    profiles=[]
    clients={}
    for role in fixture["profileAssignments"]:
        subject="synthetic-"+role.replace("_","-")
        password="SyntheticOnly-"+secrets.token_hex(24)
        seed=secrets.token_bytes(20)
        profiles.append({
            "subject":subject,"role":role,"password":password,
            "seedHex":seed.hex(),
            "assignments":fixture["profileAssignments"][role],
        })
        clients[role]={"subject":subject,"password":password,"seed":seed}
    return profiles,clients


def child_env(key,*,bootstrap=None,identity_url=None,faults=False):
    """Pass only minimal OS/Python settings plus synthetic lab secrets."""
    keep=("PATH","PYTHONPATH","SYSTEMROOT","WINDIR","TMP","TEMP",
          "TMPDIR","HOME","LANG","LC_ALL","PYTHONIOENCODING")
    env={k:os.environ[k] for k in keep if k in os.environ}
    env["PYTHONPATH"]=str(ROOT)
    env["PYTHONUNBUFFERED"]="1"
    env["LAB_SERVICE_KEY"]=key
    if faults:
        env["LAB_FAULTS_ENABLED"]="1"
    if bootstrap is not None:
        env["LAB_BOOTSTRAP"]=json.dumps({"accounts":bootstrap},
                                        separators=(",",":"))
    if identity_url is not None:
        env["LAB_IDENTITY_URL"]=identity_url
    return env


@contextmanager
def running_services(policy,fixture,*,faults=False):
    """Always stop children. Ephemeral ports, ephemeral identity+service keys."""
    validate_policy(policy)
    validate_fixture(fixture)
    id_port=allocate_port()
    api_port=allocate_port()
    while api_port==id_port:
        api_port=allocate_port()
    identity_url=f"http://127.0.0.1:{id_port}"
    api_url=f"http://127.0.0.1:{api_port}"
    key=secrets.token_hex(policy["serviceIntrospectionKeyLengthBytes"])
    profiles,clients=bootstrap_accounts(fixture)
    processes=[]
    try:
        for role,port,env in (
            ("identity",id_port,child_env(key,bootstrap=profiles,faults=faults)),
            ("resource",api_port,child_env(key,identity_url=identity_url,
                                           faults=faults)),
        ):
            cmd=[sys.executable,"-m","governance.loopback_http_services",
                 role,"--port",str(port)]
            child=subprocess.Popen(
                cmd,cwd=ROOT,env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                close_fds=True)
            processes.append(child)
            await_healthy(child,identity_url if role=="identity" else api_url,
                          role)
        require(len(processes)==2
                and processes[0].pid!=processes[1].pid
                and all(p.pid!=os.getpid() for p in processes),
                "identity and resource services not separate processes")
        yield {"identity":identity_url,"resource":api_url,
               "key":key,"clients":clients,
               "identityPid":processes[0].pid,
               "resourcePid":processes[1].pid,
               # Process handles are private to the harness, never serialized.
               "identityProcess":processes[0],
               "resourceProcess":processes[1]}
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)


def post(url,path,payload,key=None):
    return request_json(url,path,payload,key=key)


def login(svc,role,password_override=None):
    client=svc["clients"][role]
    status,result=post(svc["identity"],"/login",{
        "subject":client["subject"],
        "password":client["password"] if password_override is None
                   else password_override,
    })
    return status,result.get("token")


def step_up(svc,role,token):
    """Retry only on a TOTP time-window rollover, with synthetic seed."""
    seed=svc["clients"][role]["seed"]
    for attempt in range(4):
        code=totp(seed,int(time.time()))
        status,_=post(svc["identity"],"/mfa",{"token":token,"otp":code})
        if status==200:
            return code
        time.sleep(0.2)
    raise RuntimeError("synthetic TOTP step-up unexpectedly failed")


def test_requests(policy,fixture,svc):
    cases=[]
    for entry in fixture["scenarios"]:
        role=entry["role"]
        status,token=login(svc,role)
        require(status==200 and isinstance(token,str),
                "cannot log in synthetic test profile")
        step_up(svc,role,token)
        result_code,response=post(svc["resource"],"/authorize",{
            "token":token,"action":entry["action"],
            "packetId":entry["packetId"],
        })
        allowed=result_code==200 and response.get("sandboxAllowed") is True
        expected=entry["kind"].startswith("success_")
        require(allowed is expected,
                f"service authorization regression in {entry['scenarioId']}")
        require(response.get("realResourceAccess") is False
                if allowed else True,
                "resource service exposes non-synthetic access")
        cases.append({
            "scenarioId":entry["scenarioId"],"kind":entry["kind"],
            "role":role,"sandboxResourceActionAllowed":allowed,
            "expectationMet":True,
            "realUserAuthenticated":False,
            "realDocumentAccessed":False,
            "operationalAuthority":False,
        })
        revoke_code,_=post(svc["identity"],"/revoke",{"token":token})
        require(revoke_code==200,"synthetic session was not revoked")
    return cases


def test_adversarial_guards(svc):
    guards=[]
    def check(name,boolean):
        require(boolean is True, "loopback security guard failed: "+name)
        guards.append({"guard":name,"passed":True,
                       "realPrivateDataUsed":False})
    role="technical_reviewer_a"
    wrong,_=login(svc,role,password_override="incorrect-synthetic-password")
    check("incorrect_password_denied",wrong==403)

    status,token=login(svc,role)
    require(status==200,"test login failed")
    no_mfa,answer=post(svc["resource"],"/authorize",{
        "token":token,"action":"read_assigned_private_case",
        "packetId":"IRP-001"})
    check("private_access_requires_mfa",
          no_mfa==403 and answer.get("sandboxAllowed") is False)

    badotp,_=post(svc["identity"],"/mfa",{"token":token,"otp":"bad-otp"})
    check("incorrect_totp_denied",badotp==403)
    code=step_up(svc,role,token)
    replay,_=post(svc["identity"],"/mfa",{"token":token,"otp":code})
    check("totp_replay_denied",replay==403)

    unauth,_=post(svc["identity"],"/introspect",{"token":token})
    check("unkeyed_introspection_denied",unauth==403)
    wrongkey,_=post(svc["identity"],"/introspect",
                    {"token":token},key="0"*64)
    check("incorrect_service_key_denied",wrongkey==403)

    parts=token.split(".",1)
    require(len(parts)==2,"synthetic test session must be MAC protected")
    mac=parts[1]
    forged=parts[0]+"."+("A" if mac[0]!="A" else "B")+mac[1:]
    bad_token,answer=post(svc["resource"],"/authorize",{
        "token":forged,"action":"read_assigned_private_case",
        "packetId":"IRP-001"})
    check("tampered_hmac_session_denied",
          bad_token==403 and answer.get("sandboxAllowed") is False)

    unknown,answer=post(svc["resource"],"/forbidden",{
        "token":token,"action":"read_assigned_private_case",
        "packetId":"IRP-001"})
    check("unknown_route_denied",unknown==404)

    privilege,answer=post(svc["resource"],"/authorize",{
        "token":token,"action":"read_assigned_private_case",
        "packetId":"IRP-001","role":"adjudicator"})
    check("role_claim_in_request_denied",privilege==400)

    fake,answer=post(svc["resource"],"/authorize",{
        "token":"fake-token","action":"read_assigned_private_case",
        "packetId":"IRP-001"})
    check("foreign_session_denied",
          fake==403 and answer.get("sandboxAllowed") is False)

    revoked,_=post(svc["identity"],"/revoke",{"token":token})
    after,answer=post(svc["resource"],"/authorize",{
        "token":token,"action":"read_assigned_private_case",
        "packetId":"IRP-001"})
    check("revoked_session_denied",
          revoked==200 and after==403 and
          answer.get("sandboxAllowed") is False)

    status,live=login(svc,role)
    require(status==200,"expiry test login failed")
    step_up(svc,role,live)
    advanced,_=post(svc["identity"],"/advance-clock",
                    {"seconds":950},key=svc["key"])
    expired,answer=post(svc["resource"],"/authorize",{
        "token":live,"action":"read_assigned_private_case",
        "packetId":"IRP-001"})
    check("cross_process_expiry_denied",
          advanced==200 and expired==403 and
          answer.get("sandboxAllowed") is False)
    return guards


def evaluate(policy,fixture):
    validate_policy(policy)
    validate_fixture(fixture)
    registry=current_public_packets()
    ids={entry["packetId"] for entry in registry["packets"]}
    require(set(fixture["allowedPacketIds"]).issubset(ids),
            "synthetic laboratory packet IDs not found in frozen registry")
    with running_services(policy,fixture) as svc:
        scenarios=test_requests(policy,fixture,svc)
        guards=test_adversarial_guards(svc)
    allowed=sum(x["sandboxResourceActionAllowed"] for x in scenarios)
    require(len(scenarios)==policy["expectedScenarioCount"]
            and len(guards)==policy["expectedGuardCount"]
            and allowed==6,
            "unexpected service API result count")
    return {
        "schema":"maintenance-superinteligence.loopback-service-report.v1",
        "version":"1.0.0",
        "mode":"two_ephemeral_loopback_http_processes_synthetic_only",
        "policyDigest":digest(policy),
        "sourceFixtureDigest":digest(fixture),
        "sourceRegistryDigest":digest(registry),
        "separateServiceProcessIdsVerified":True,
        "identityServiceBoundToLoopback":True,
        "resourceServiceBoundToLoopback":True,
        "crossProcessHttpIntrospectionExercised":True,
        "introspectionServiceKeyChecked":True,
        "sessionMacAndMfaCheckedInIdentityService":True,
        "resourceRoleAndPacketAclChecked":True,
        "scenarioCount":len(scenarios),
        "sandboxAuthorizedActions":allowed,
        "sandboxDeniedActions":len(scenarios)-allowed,
        "guardCount":len(guards),
        "guardChecksPassed":sum(x["passed"] for x in guards),
        "scenarios":scenarios,
        "securityGuards":guards,
        "realIdentityProviderConnected":False,
        "realUsersAuthenticated":0,
        "realOIDCTokensValidated":0,
        "realPrivateDocumentsAccessed":0,
        "realPermissionsGranted":0,
        "realOperationalActions":0,
        "tlsOrMtlsEnabled":False,
        "signedIdentityCertificatesVerified":False,
        "mayCreateWorkOrder":False,
        "mayExecuteTest":False,
        "mayModifyEcm":False,
        "mayReleaseEquipment":False,
        "decision":"no_go_loopback_synthetic_http_only_no_external_idp_or_real_resources",
    }


def verify_report(report,policy,fixture):
    require(report==evaluate(policy,fixture),
            "loopback report forged or inconsistent with full service exercise")
    return True


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    report=evaluate(load(POLICY_PATH),load(FIXTURE))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    return report


if __name__=="__main__":
    main()
