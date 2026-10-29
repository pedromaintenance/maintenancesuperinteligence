"""Cycle 40: in-memory, standalone synthetic identity and authorization lab.

NOT OIDC/JWT, NOT connected to an IdP, corporate records, SAP or private cases.
A real HMAC integrity check and in-memory per-resource authorization are used
only for synthetic test credentials and synthetic resource identifiers.
This sample authentication code is not production-ready security middleware.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import struct

from governance.federation_rbac import GRANTS, RESOURCE_RULES, current_public_packets
from pilot.change_review_packets import require, digest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "governance/isolated-identity-lab-policy.v1.json"
FIXTURE = ROOT / "governance/isolated-identity-lab-rehearsal.v1.json"
ROLES = tuple(GRANTS)
LAB_ACTIONS = tuple(RESOURCE_RULES)
POLICY_FALSE = (
    "realIdpConnected", "realOIDCImplemented", "realCompanyAccountsUsed",
    "realMFAProviderConnected", "persistentSessionStoreConnected",
    "persistentAuditStoreConnected", "realPrivateDocumentsAccessible",
    "operationalAuthorityGranted", "mayModifyUpstreamRules",
    "mayCreateWorkOrder", "mayExecuteTest", "mayModifyEcm",
    "mayReleaseEquipment",
)
POLICY_KEYS = {
    "schema", "version", "mode", "issuer", "audience",
    "sessionTTLSeconds", "pbkdf2Iterations", "totpStepSeconds",
    "totpDigits", "allowedRoles", "allowedActions", "privatePacketKinds",
    *POLICY_FALSE,
}
FIXTURE_KEYS = {
    "schema", "version", "nature", "allowedPacketIds",
    "profileAssignments", "scenarios", "realUsersPresent",
    "realPrivateDataPresent", "realIdentityProofCollected",
}
SCENARIO_KINDS = (
    "success_public", "success_custodian_index",
    "success_custodian_package", "success_assigned_reviewer",
    "success_reviewer_opinion", "success_adjudication_draft",
    "deny_author_private", "deny_reviewer_adjudication",
    "deny_adjudicator_review", "deny_unassigned_resource",
    "deny_operational_action", "deny_equipment_release",
)
RESULT_FLAGS = (
    "realIdpAuthentication", "realHumanIdentityVerified",
    "realOIDCSessionEstablished", "realPrivateDocumentAccessGranted",
    "realOperationalPermission",
)
SNAPSHOT_CONTEXT = "isolated_synthetic_only_not_real_identity"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) == POLICY_KEYS
            and policy["schema"] ==
                "maintenance-superinteligence.isolated-identity-lab-policy.v1"
            and policy["version"] == "1.0.0"
            and policy["mode"] ==
                "ephemeral_offline_synthetic_identity_and_acl_sandbox"
            and policy["issuer"] == "urn:maintenance:lab-only"
            and policy["audience"] == "maintenance-lab-private-synthetic"
            and type(policy["sessionTTLSeconds"]) is int
            and policy["sessionTTLSeconds"] == 900
            and type(policy["pbkdf2Iterations"]) is int
            and policy["pbkdf2Iterations"] == 120000
            and type(policy["totpStepSeconds"]) is int
            and policy["totpStepSeconds"] == 30
            and type(policy["totpDigits"]) is int
            and policy["totpDigits"] == 6
            and policy["allowedRoles"] == list(ROLES)
            and policy["allowedActions"] == list(LAB_ACTIONS)
            and policy["privatePacketKinds"] ==
                ["synthetic_private_review_case",
                 "synthetic_private_review_receipt"]
            and all(policy[k] is False for k in POLICY_FALSE),
            "sandbox policy claims production ID/auth or adds privileges")
    return True


def validate_fixture(fixture):
    require(isinstance(fixture, dict) and set(fixture) == FIXTURE_KEYS
            and fixture["schema"] ==
                "maintenance-superinteligence.isolated-identity-lab-rehearsal.v1"
            and fixture["version"] == "1.0.0"
            and fixture["nature"] ==
                "synthetic_identity_profiles_no_issued_real_credentials"
            and fixture["allowedPacketIds"] == ["IRP-001", "IRP-002"]
            and all(fixture[k] is False for k in
                    ("realUsersPresent", "realPrivateDataPresent",
                     "realIdentityProofCollected")),
            "sandbox fixture claims real people, private data or credentials")
    assignments=fixture["profileAssignments"]
    require(isinstance(assignments, dict)
            and set(assignments) == set(ROLES)
            and all(v == ([] if role == "author" else ["IRP-001"])
                    for role,v in assignments.items()),
            "fixture assigns unsafe or unauthorized resources")
    cases=fixture["scenarios"]
    require(isinstance(cases,list) and len(cases)==len(SCENARIO_KINDS),
            "12 ordered lab scenarios required")
    for i,(row,kind) in enumerate(zip(cases,SCENARIO_KINDS)):
        require(isinstance(row,dict)
                and set(row) == {"scenarioId","role","action","packetId","kind"}
                and row["scenarioId"]==f"LAB-{i+1:03d}"
                and row["kind"]==kind
                and row["role"] in ROLES
                and row["packetId"] in fixture["allowedPacketIds"]
                and isinstance(row["action"],str),
                "sandbox test case modified or out of registry")
    return True


def _url_encode(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _url_decode(raw):
    require(isinstance(raw,str) and len(raw)<4096
            and raw.isascii() and all(c in
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
                for c in raw), "malformed synthetic session encoding")
    return base64.urlsafe_b64decode(raw + "="*((-len(raw))%4))


def totp(seed, now, step=30, digits=6):
    """RFC 6238 style HOTP with SHA1, for test-only locally controlled seeds."""
    counter=int(now)//step
    require(counter>=0 and isinstance(seed,bytes) and len(seed)>=20,
            "test TOTP seed invalid")
    digest_bytes=hmac.new(seed,struct.pack(">Q",counter),hashlib.sha1).digest()
    pos=digest_bytes[-1]&0x0F
    number=struct.unpack(">I",digest_bytes[pos:pos+4])[0]&0x7FFFFFFF
    return str(number%(10**digits)).zfill(digits)


class IsolatedLab:
    """An isolated, memory-only authentication+resource enforcement rehearsal."""
    def __init__(self,policy,packet_ids,signing_key):
        validate_policy(policy)
        require(isinstance(signing_key,bytes) and len(signing_key)>=32,
                "lab signing key too short")
        require(set(packet_ids)=={"IRP-001","IRP-002"},
                "lab resource set must be two registered synthetic cases")
        self.policy=policy
        self.packet_ids=set(packet_ids)
        self._key=signing_key
        self._users={}
        self._sessions={}
        self._audit=[]

    def register(self,subject,role,password,seed,assignments):
        require(isinstance(subject,str) and subject.startswith("synthetic-")
                and subject not in self._users
                and role in ROLES
                and isinstance(password,str) and len(password)>=16
                and isinstance(seed,bytes) and len(seed)>=20
                and isinstance(assignments,list)
                and len(set(assignments))==len(assignments)
                and set(assignments).issubset(self.packet_ids)
                and (not assignments if role=="author" else True),
                "invalid or duplicate synthetic identity")
        salt=secrets.token_bytes(16)
        h=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,
                              self.policy["pbkdf2Iterations"])
        self._users[subject]={
            "role":role,"salt":salt,"passwordHash":h,
            "totpSeed":seed,"assignments":frozenset(assignments),
        }

    def _token(self,session):
        payload={k:session[k] for k in
                 ("sid","iss","aud","sub","role","iat","exp")}
        body=_url_encode(json.dumps(payload,sort_keys=True,
                         separators=(",",":")).encode("utf-8"))
        mac=_url_encode(hmac.new(self._key,body.encode("ascii"),
                                hashlib.sha256).digest())
        return body+"."+mac

    def login(self,subject,password,now):
        user=self._users.get(subject)
        require(user is not None and isinstance(password,str)
                and type(now) is int, "synthetic account missing")
        computed=hashlib.pbkdf2_hmac("sha256",password.encode(),
                    user["salt"],self.policy["pbkdf2Iterations"])
        require(hmac.compare_digest(computed,user["passwordHash"]),
                "synthetic password incorrect")
        sid=secrets.token_hex(24)
        s={"sid":sid,"iss":self.policy["issuer"],
           "aud":self.policy["audience"],"sub":subject,
           "role":user["role"],"iat":now,
           "exp":now+self.policy["sessionTTLSeconds"],
           "mfa":False,"lastTotpCounter":-1,"revoked":False}
        self._sessions[sid]=s
        return self._token(s)

    def _verified_session(self,token,now):
        require(isinstance(token,str) and type(now) is int and
                len(token)<4096 and token.count(".")==1,
                "malformed synthetic session")
        body,mac=token.split(".",1)
        expected=_url_encode(hmac.new(
            self._key,body.encode("ascii"),hashlib.sha256).digest())
        require(hmac.compare_digest(mac,expected),
                "sandbox token signature invalid")
        raw=_url_decode(body)
        try:
            claims=json.loads(raw.decode("utf-8"))
        except (ValueError,UnicodeError) as exc:
            raise ValueError("invalid synthetic token payload") from exc
        require(isinstance(claims,dict)
                and set(claims)=={"sid","iss","aud","sub","role","iat","exp"},
                "sandbox token structure invalid")
        s=self._sessions.get(claims["sid"])
        require(s is not None and not s["revoked"]
                and all(claims[k]==s[k] for k in claims)
                and claims["iss"]==self.policy["issuer"]
                and claims["aud"]==self.policy["audience"]
                and type(claims["iat"]) is int
                and type(claims["exp"]) is int
                and claims["iat"]<=now<claims["exp"],
                "revoked, expired or mismatched synthetic session")
        return s

    def step_up(self,token,otp,now):
        session=self._verified_session(token,now)
        user=self._users[session["sub"]]
        counter=now//self.policy["totpStepSeconds"]
        require(isinstance(otp,str) and otp.isascii()
                and len(otp)==self.policy["totpDigits"]
                and otp.isdigit()
                and counter>session["lastTotpCounter"]
                and hmac.compare_digest(
                    otp,totp(user["totpSeed"],now,
                             self.policy["totpStepSeconds"],
                             self.policy["totpDigits"])),
                "sandbox MFA invalid or OTP replayed")
        session["lastTotpCounter"]=counter
        session["mfa"]=True
        return True

    def revoke(self,token,now):
        session=self._verified_session(token,now)
        session["revoked"]=True
        return True

    def authorize(self,token,action,packet_id,now):
        """Enforce on in-memory synthetic resource. Never touches external data."""
        try:
            s=self._verified_session(token,now)
        except (ValueError,TypeError,KeyError) as exc:
            self._audit.append({"result":"deny","reason":"invalid_session"})
            return self._decision(False,"invalid_session")
        user=self._users.get(s["sub"])
        reason="granted_synthetic_resource_only"
        if (action not in LAB_ACTIONS or
            RESOURCE_RULES.get(action) is None):
            reason="unknown_or_operational_action"
        elif action not in GRANTS[user["role"]]:
            reason="role_denied"
        elif packet_id not in self.packet_ids:
            reason="unknown_synthetic_resource"
        elif action!="read_public_research" and packet_id not in user["assignments"]:
            reason="packet_not_assigned"
        elif action!="read_public_research" and not s["mfa"]:
            reason="mfa_required"
        elif action=="read_public_research":
            reason="granted_synthetic_resource_only"
        elif (user["role"]=="custodian"
              and action in ("read_assigned_private_case",
                             "submit_adjudication","submit_technical_opinion")):
            reason="role_denied"
        allowed=reason=="granted_synthetic_resource_only"
        self._audit.append({"result":"synthetic_allow" if allowed else "deny",
                            "reason":reason,"action":action})
        return self._decision(allowed,reason)

    @staticmethod
    def _decision(allowed,reason):
        return {
            "sandboxResourceActionAllowed":allowed,
            "reason":reason,
            "realOIDCAuthenticated":False,
            "realCompanyIdentityVerified":False,
            "realPrivateDocumentsRead":False,
            "realOperationalAuthorizationGranted":False,
            "mayCreateWorkOrder":False,
            "mayExecuteTest":False,
            "mayModifyEcm":False,
            "mayReleaseEquipment":False,
        }

    def synthetic_read(self,token,packet_id,now):
        verdict=self.authorize(token,"read_assigned_private_case",packet_id,now)
        return ("SYNTHETIC-CASE-"+packet_id if
                verdict["sandboxResourceActionAllowed"] else None)

    def audit_summary(self):
        return {"syntheticAllowed":sum(x["result"]=="synthetic_allow"
                                        for x in self._audit),
                "syntheticDenied":sum(x["result"]=="deny"
                                       for x in self._audit),
                "realRequestsExecuted":0}


def evaluate(policy,fixture):
    validate_policy(policy)
    validate_fixture(fixture)
    registry=current_public_packets()
    public_ids={p["packetId"] for p in registry["packets"]}
    require(set(fixture["allowedPacketIds"]).issubset(public_ids),
            "lab cases not found in frozen Cycle 37 registry")
    lab=IsolatedLab(policy,fixture["allowedPacketIds"],secrets.token_bytes(32))
    users={}
    for role in ROLES:
        subject="synthetic-"+role.replace("_","-")
        password="SyntheticOnly-"+secrets.token_hex(20)
        seed=secrets.token_bytes(20)
        lab.register(subject,role,password,seed,
                     fixture["profileAssignments"][role])
        users[role]=(subject,password,seed)
    result=[]
    now=1_793_286_000
    for row in fixture["scenarios"]:
        subject,pwd,seed=users[row["role"]]
        token=lab.login(subject,pwd,now)
        lab.step_up(token,totp(seed,now),now)
        verdict=lab.authorize(token,row["action"],row["packetId"],now)
        result.append({
            "scenarioId":row["scenarioId"],
            "kind":row["kind"],
            "role":row["role"],
            "sandboxResourceActionAllowed":verdict["sandboxResourceActionAllowed"],
            "reason":verdict["reason"],
            "realOIDCAuthenticated":False,
            "realCompanyIdentityVerified":False,
            "realPrivateDocumentsRead":False,
            "realOperationalAuthorizationGranted":False,
        })
        lab.revoke(token,now)
    allowed=sum(x["sandboxResourceActionAllowed"] for x in result)
    return {
        "schema":"maintenance-superinteligence.isolated-identity-lab-report.v1",
        "version":"1.0.0",
        "mode":"offline_in_memory_synthetic_authorization_with_hmac_sessions",
        "policyDigest":digest(policy),
        "fixtureDigest":digest(fixture),
        "sourcePacketRegistryDigest":digest(registry),
        "scenarioCount":len(result),
        "sandboxAuthorizedActions":allowed,
        "sandboxDeniedActions":len(result)-allowed,
        "syntheticCredentialsVerified":len(result),
        "syntheticTotpValidated":len(result),
        "syntheticSessionRevocations":len(result),
        "realUsersAuthenticated":0,
        "realOIDCOrIdPConnected":False,
        "realTokensAccepted":0,
        "realResourcePermissionsGranted":0,
        "realPrivateDocumentsAccessed":0,
        "realOperationalActions":0,
        "results":result,
        "sourceRulesChanged":False,
        "mayCreateWorkOrder":False,"mayExecuteTest":False,
        "mayModifyEcm":False,"mayReleaseEquipment":False,
        "decision":"no_go_synthetic_lab_only_external_idp_and_acl_not_integrated",
    }


def verify_report(report,policy,fixture):
    require(report == evaluate(policy,fixture),
            "Cycle40 report changed or inconsistent with generated synthetic lab")
    return True


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(argv)
    report=evaluate(load(POLICY),load(FIXTURE))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    return report


if __name__=="__main__":
    main()
