"""Cycle 41: two loopback-only HTTP services in distinct TEST processes.

This is not OIDC, OAuth, TLS, corporate IAM, or a network deployment guide.
Both processes accept only synthetic accounts and fake case identifiers.
The resource service cannot read documents: it queries the identity service's
key-protected introspection endpoint for active MFA/session status.
Never expose these plain-HTTP demonstration services beyond 127.0.0.1.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from governance.isolated_identity_lab import IsolatedLab, validate_policy as validate_identity
from governance.federation_rbac import GRANTS, RESOURCE_RULES
from pilot.change_review_packets import require, ReviewRejected

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "governance/loopback-service-policy.v1.json"
IDENTITY_POLICY = ROOT / "governance/isolated-identity-lab-policy.v1.json"
FIELDS = {
    "schema", "version", "mode", "bindHost", "scheme", "tokenFormat",
    "identityServerImplementation", "resourceServerImplementation",
    "accessPolicy", "serviceIntrospectionKeyLengthBytes", "maxRequestBytes",
    "requestTimeoutSeconds", "maxClockAdvanceSeconds",
    "identityProcessRequired", "resourceProcessRequired",
    "syntheticResourceIds", "expectedScenarioCount", "expectedGuardCount",
    "realIdpConnected", "realOIDCImplemented",
    "realJwtSignaturesVerified", "realClientRegistrationVerified",
    "realHumanIdentitiesAuthenticated", "realMfaProviderConnected",
    "realDocumentsAccessible", "realBackendsConnected",
    "tlsOrMutualTlsEnabled", "enterpriseIAMConnected",
    "mayApproveTechnicalRelation", "mayWriteSAP", "mayCreateWorkOrder",
    "mayExecuteTest", "mayModifyEcm", "mayReleaseEquipment",
}
DENY_FIELDS = (
    "realIdpConnected", "realOIDCImplemented",
    "realJwtSignaturesVerified", "realClientRegistrationVerified",
    "realHumanIdentitiesAuthenticated", "realMfaProviderConnected",
    "realDocumentsAccessible", "realBackendsConnected",
    "tlsOrMutualTlsEnabled", "enterpriseIAMConnected",
    "mayApproveTechnicalRelation", "mayWriteSAP", "mayCreateWorkOrder",
    "mayExecuteTest", "mayModifyEcm", "mayReleaseEquipment",
)
SECRETS_ONLY_IN_LAB_ENV = (
    "LAB_SERVICE_KEY", "LAB_BOOTSTRAP", "LAB_IDENTITY_URL",
)
OPENER = build_opener(ProxyHandler({}))


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) == FIELDS
            and policy["schema"] ==
                "maintenance-superinteligence.loopback-service-policy.v1"
            and policy["version"] == "1.0.0"
            and policy["mode"] ==
                "separate_localhost_processes_synthetic_resources_only"
            and policy["bindHost"] == "127.0.0.1"
            and policy["scheme"] == "http"
            and policy["tokenFormat"] == "opaque_test_only_hmac_not_jwt_or_oidc"
            and policy["identityServerImplementation"] ==
                "stdlib_httpserver_ephemeral_test_process"
            and policy["resourceServerImplementation"] ==
                "stdlib_httpserver_ephemeral_test_process"
            and policy["accessPolicy"] ==
                "deny_by_default_role_action_resource_and_mfa"
            and type(policy["serviceIntrospectionKeyLengthBytes"]) is int
            and policy["serviceIntrospectionKeyLengthBytes"] == 32
            and type(policy["maxRequestBytes"]) is int
            and policy["maxRequestBytes"] == 4096
            and type(policy["requestTimeoutSeconds"]) is int
            and policy["requestTimeoutSeconds"] == 3
            and type(policy["maxClockAdvanceSeconds"]) is int
            and policy["maxClockAdvanceSeconds"] == 1800
            and policy["identityProcessRequired"] is True
            and policy["resourceProcessRequired"] is True
            and policy["syntheticResourceIds"] == ["IRP-001","IRP-002"]
            and policy["expectedScenarioCount"] == 12
            and policy["expectedGuardCount"] == 12
            and all(policy[k] is False for k in DENY_FIELDS),
            "Cycle41 policy claims live provider, external exposure or operational rights")
    validate_identity(load(IDENTITY_POLICY))
    return True


def request_json(url, path, payload, *, key=None, timeout=3):
    """No proxy use. In all callers, URL must be local 127.0.0.1 only."""
    require(isinstance(url,str)
            and re.fullmatch(r"http://127\.0\.0\.1:[0-9]{2,5}",url),
            "HTTP lab only permits IPv4 loopback host")
    body=json.dumps(payload,separators=(",",":")).encode("utf-8")
    headers={"Content-Type":"application/json"}
    if key is not None:
        headers["X-Lab-Service-Key"]=key
    req=Request(url+path,data=body,headers=headers,method="POST")
    try:
        with OPENER.open(req,timeout=timeout) as response:
            return response.status,json.loads(response.read(16384))
    except HTTPError as error:
        raw=error.read(16384)
        try:
            obj=json.loads(raw)
        except (ValueError,UnicodeError):
            obj={"ok":False,"reason":"http_error"}
        return error.code,obj
    except (URLError,TimeoutError,OSError):
        return 503,{"ok":False,"reason":"service_unavailable"}


class LabHttpHandler(BaseHTTPRequestHandler):
    server_version = "SyntheticLoopbackLab"
    sys_version = ""

    def log_message(self, *args):
        # Never emit test passwords, OTPs, bearer strings or request data.
        return

    def reply(self,status,payload):
        raw=json.dumps(payload,separators=(",",":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Synthetic-Only","true")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def parse_body(self):
        self.connection.settimeout(self.server.lab_policy["requestTimeoutSeconds"])
        h=self.headers.get_all("Content-Length") or []
        types=self.headers.get_all("Content-Type") or []
        require(len(h)==1 and len(types)==1 and
                types[0]=="application/json" and
                h[0].isascii() and h[0].isdigit(),
                "request missing or duplicate JSON headers")
        size=int(h[0])
        require(0<size<=self.server.lab_policy["maxRequestBytes"],
                "request exceeds lab body limit")
        raw=self.rfile.read(size)
        require(len(raw)==size,"truncated lab request")
        obj=json.loads(raw.decode("utf-8"))
        require(isinstance(obj,dict),"JSON root must be an object")
        return obj

    def service_key_valid(self):
        key=self.headers.get("X-Lab-Service-Key")
        return isinstance(key,str) and hmac.compare_digest(
            key,self.server.service_key)

    def do_GET(self):
        if self.path!="/health":
            self.reply(404,{"ok":False,"reason":"not_found"})
            return
        self.reply(200,{
            "ok":True,"context":"synthetic_loopback_only",
            "role":self.server.role,"pid":os.getpid(),
            "boundHost":self.server.server_address[0],
        })

    def do_POST(self):
        try:
            body=self.parse_body()
            if self.server.role=="identity":
                self.identity_route(body)
            else:
                self.resource_route(body)
        except (ReviewRejected,ValueError,KeyError,TypeError,
                UnicodeError,TimeoutError,OSError):
            self.reply(400,{"ok":False,"reason":"invalid_or_denied"})

    def identity_route(self,body):
        lab=self.server.identity_lab
        now=int(time.time())+self.server.clock_offset
        if self.path=="/login":
            require(set(body)=={"subject","password"},
                    "invalid login fields")
            try:
                token=lab.login(body["subject"],body["password"],now)
            except (ReviewRejected,ValueError,KeyError,TypeError):
                self.reply(403,{"ok":False,"reason":"login_denied"})
                return
            self.reply(200,{"ok":True,"token":token,"syntheticOnly":True})
        elif self.path=="/mfa":
            require(set(body)=={"token","otp"},"invalid MFA fields")
            try:
                lab.step_up(body["token"],body["otp"],now)
            except (ReviewRejected,ValueError,KeyError,TypeError):
                self.reply(403,{"ok":False,"reason":"mfa_denied"})
                return
            self.reply(200,{"ok":True,"syntheticOnly":True})
        elif self.path=="/revoke":
            require(set(body)=={"token"},"invalid revoke request")
            try:
                lab.revoke(body["token"],now)
            except (ReviewRejected,ValueError,KeyError,TypeError):
                self.reply(403,{"ok":False,"reason":"revoke_denied"})
                return
            self.reply(200,{"ok":True,"syntheticOnly":True})
        elif self.path=="/introspect":
            if not self.service_key_valid():
                self.reply(403,{"active":False})
                return
            require(set(body)=={"token"},"invalid introspection fields")
            try:
                s=lab._verified_session(body["token"],now)
                if not s["mfa"]:
                    self.reply(200,{"active":False})
                    return
                user=lab._users[s["sub"]]
                self.reply(200,{
                    "active":True,
                    "subject":s["sub"],"role":user["role"],
                    "assignments":sorted(user["assignments"]),
                    "realIdentityVerified":False,
                    "realOIDCAuthenticated":False,
                })
            except (ReviewRejected,ValueError,KeyError,TypeError):
                self.reply(200,{"active":False})
        elif self.path=="/advance-clock":
            if not self.service_key_valid():
                self.reply(403,{"ok":False,"reason":"denied"})
                return
            require(set(body)=={"seconds"}
                    and type(body["seconds"]) is int
                    and 1<=body["seconds"]<=
                       self.server.lab_policy["maxClockAdvanceSeconds"],
                    "invalid synthetic clock advance")
            self.server.clock_offset+=body["seconds"]
            self.reply(200,{"ok":True,"syntheticClockAdvanced":True})
        else:
            self.reply(404,{"ok":False,"reason":"not_found"})

    def resource_route(self,body):
        if self.path!="/authorize":
            self.reply(404,{"sandboxAllowed":False,"reason":"not_found"})
            return
        require(set(body)=={"token","action","packetId"},
                "invalid authorization fields")
        action,packet_id=body["action"],body["packetId"]
        if (not isinstance(action,str) or
            action not in RESOURCE_RULES or
            not isinstance(packet_id,str) or
            packet_id not in self.server.lab_policy["syntheticResourceIds"]):
            self.reply(403,{"sandboxAllowed":False,
                            "reason":"unknown_action_or_resource"})
            return
        status,identity=request_json(
            self.server.identity_url,"/introspect",
            {"token":body["token"]},key=self.server.service_key,
            timeout=self.server.lab_policy["requestTimeoutSeconds"])
        if status!=200 or identity.get("active") is not True:
            self.reply(403,{"sandboxAllowed":False,"reason":"inactive_session"})
            return
        role=identity.get("role")
        assignments=identity.get("assignments")
        if (role not in GRANTS or
            action not in GRANTS[role] or
            not isinstance(assignments,list) or
            any(p not in self.server.lab_policy["syntheticResourceIds"]
                for p in assignments)):
            self.reply(403,{"sandboxAllowed":False,"reason":"role_denied"})
            return
        if action!="read_public_research" and packet_id not in assignments:
            self.reply(403,{"sandboxAllowed":False,"reason":"packet_not_assigned"})
            return
        self.reply(200,{
            "sandboxAllowed":True,
            "reason":"synthetic_resource_only",
            "syntheticRecordId":"SIMULATED-"+packet_id,
            "realResourceAccess":False,
            "mayCreateWorkOrder":False,
            "mayReleaseEquipment":False,
        })


def server_main(role,port):
    policy=load(POLICY_PATH)
    validate_policy(policy)
    require(role in ("identity","resource")
            and type(port) is int and 1<=port<=65535,
            "invalid loopback server parameters")
    service_key=os.environ.get("LAB_SERVICE_KEY","")
    require(isinstance(service_key,str) and len(service_key)==64
            and all(c in "0123456789abcdef" for c in service_key),
            "invalid ephemeral inter-service secret")
    server=ThreadingHTTPServer(("127.0.0.1",port),LabHttpHandler)
    server.daemon_threads=True
    server.role=role
    server.lab_policy=policy
    server.service_key=service_key
    server.clock_offset=0
    if role=="identity":
        bootstrap=json.loads(os.environ.get("LAB_BOOTSTRAP","{}"))
        require(isinstance(bootstrap,dict)
                and set(bootstrap)=={"accounts"}
                and isinstance(bootstrap["accounts"],list)
                and len(bootstrap["accounts"])==5,
                "only five synthetic users permitted")
        lab=IsolatedLab(load(IDENTITY_POLICY),
                        policy["syntheticResourceIds"],
                        secrets.token_bytes(32))
        for item in bootstrap["accounts"]:
            require(isinstance(item,dict) and
                    set(item)=={"subject","role","password","seedHex","assignments"},
                    "invalid synthetic bootstrap")
            lab.register(item["subject"],item["role"],
                         item["password"],bytes.fromhex(item["seedHex"]),
                         item["assignments"])
        server.identity_lab=lab
    else:
        identity_url=os.environ.get("LAB_IDENTITY_URL","")
        require(re.fullmatch(r"http://127\.0\.0\.1:[0-9]{2,5}",identity_url),
                "resource process cannot connect off-host")
        server.identity_url=identity_url
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("role",choices=["identity","resource"])
    parser.add_argument("--port",required=True,type=int)
    args=parser.parse_args(argv)
    server_main(args.role,args.port)


if __name__=="__main__":
    main()
