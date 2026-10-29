"""Cycle 39 — fail-closed OIDC/RBAC integration *design*, not an IdP gateway.

No live JWT/OIDC signature verification or backend ACL is configured.  Claims in
public examples are forged, intentionally non-authoritative and have no power to
open a private file. Role eligibility is a pedagogical conditional only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

from governance.private_review_custody import validated_policy as verify_custody_policy
from governance.private_review_custody import POLICY as CUSTODY_POLICY
from knowledge.independent_review import (
    PROTOCOL, WORKLIST, build_packets, load as load_public
)
from knowledge.causal_adjudication import (
    PLAN, POLICY as ADJ_POLICY, SUBMISSIONS, MATRIX, MAP_PATH,
    MECHANICAL_POLICY, DISCRIMINATION_POLICY, REVIEW_POLICY
)
from pilot.change_review_packets import require, digest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "governance/federation-rbac-policy.v1.json"
REHEARSAL = ROOT / "governance/federation-rbac-rehearsal.v1.json"

GRANTS = {
    "author": ("read_public_research",),
    "custodian": (
        "read_public_research", "read_private_document_index",
        "prepare_private_review_package"
    ),
    "technical_reviewer_a": (
        "read_public_research", "read_assigned_private_case",
        "submit_technical_opinion"
    ),
    "technical_reviewer_b": (
        "read_public_research", "read_assigned_private_case",
        "submit_technical_opinion"
    ),
    "adjudicator": (
        "read_public_research", "read_assigned_private_case", "submit_adjudication"
    ),
}
ACTOR_IDS = (
    ("SIM-AUTHOR", "author", "sim-author"),
    ("SIM-CUSTODIAN", "custodian", "sim-custodian"),
    ("SIM-REVIEW-A", "technical_reviewer_a", "sim-review-a"),
    ("SIM-REVIEW-B", "technical_reviewer_b", "sim-review-b"),
    ("SIM-ADJUDICATOR", "adjudicator", "sim-adjudicator"),
)
RESOURCE_RULES = {
    "read_public_research": "public_research_metadata",
    "read_private_document_index": "private_review_receipt",
    "prepare_private_review_package": "private_review_case",
    "read_assigned_private_case": "private_review_case",
    "submit_technical_opinion": "private_review_case",
    "submit_adjudication": "private_review_case",
}
DENIED_FLAGS = (
    "providerConfigured", "oidcDiscoveryVerified",
    "jwksSignatureVerifierConnected", "oidcAudienceRegistered",
    "externalRoleDirectoryConnected", "sessionRevocationStoreConnected",
    "mfaAssuranceValidated", "realAccessEnforcementConnected",
    "auditLogExternallyCustodied", "mayApproveTechnicalRelation",
    "mayModifyUpstream", "mayCreateWorkOrder", "mayExecuteTest",
    "mayModifyEcm", "mayReleaseEquipment",
)
ALLOWED_TOP = {
    "schema", "version", "mode", "syntheticIssuer", "syntheticAudience",
    "simulationClockEpoch", "maxTokenLifetimeSeconds",
    "maximumClockSkewSeconds", "roleGrants", "privateResourceKinds",
    "publicResourceKinds", "operationalResourceKinds", "protectedActions",
    "defaultDeny", "roleSeparationRequired", "mfaConditionRequiredForPrivate",
    *DENIED_FLAGS, "sources"
}
CLAIM_KEYS = {
    "iss", "aud", "sub", "claimedRole", "iat", "nbf", "exp", "nonce",
    "jti", "alg", "acr", "amr", "signatureValidated",
    "issuerTrusted", "roleAssignmentVerified"
}
REQUEST_KEYS = {
    "scenarioId", "kind", "actorProfileId", "packetId", "action",
    "resourceType", "expectedNonce", "claims"
}
TOP_FIXTURE = {
    "schema", "version", "mode", "profileActors", "scenarios",
    "realIdentitiesPresent", "realTokensPresent", "liveProviderConnected"
}
KINDS = (
    "baseline_author_public", "role_eligible_custody_index",
    "role_eligible_prepare", "role_eligible_reviewer_a_read",
    "role_eligible_reviewer_a_opinion",
    "role_eligible_reviewer_b_opinion",
    "role_eligible_adjudication_only", "author_cannot_approve",
    "reviewer_cannot_adjudicate", "adjudicator_cannot_review",
    "custodian_cannot_review", "reviewer_cannot_read_index",
    "operation_always_forbidden", "upstream_always_forbidden",
    "author_private_case_denied", "unknown_packet",
    "wrong_issuer", "wrong_audience", "expired_claim", "future_claim",
    "nonce_mismatch", "missing_mfa", "actor_subject_mismatch",
    "actor_role_spoof", "duplicate_token_jti", "reuse_jti",
    "untrusted_algorithm", "unexpected_scope", "long_lifetime",
    "tampered_auth_claims",
)


def validate_policy(policy):
    require(isinstance(policy,dict) and set(policy)==ALLOWED_TOP
            and policy["schema"]=="maintenance-superinteligence.federation-rbac-policy.v1"
            and policy["version"]=="1.0.0"
            and policy["mode"]=="hypothetical_roles_no_live_identity_provider"
            and policy["syntheticIssuer"]=="https://idp.example.invalid/research"
            and policy["syntheticAudience"]=="maintenance-research-example"
            and type(policy["simulationClockEpoch"]) is int
            and policy["simulationClockEpoch"]==1793286000
            and type(policy["maxTokenLifetimeSeconds"]) is int
            and policy["maxTokenLifetimeSeconds"]==3600
            and type(policy["maximumClockSkewSeconds"]) is int
            and policy["maximumClockSkewSeconds"]==60
            and policy["roleGrants"]=={k:list(v) for k,v in GRANTS.items()}
            and policy["privateResourceKinds"]==[
                "private_review_case", "private_review_receipt"]
            and policy["publicResourceKinds"]==["public_research_metadata"]
            and policy["operationalResourceKinds"]==[
                "upstream_causal_rules","sap_pm","ecm","equipment_release"]
            and policy["protectedActions"]==[
                "read_private_document_index","prepare_private_review_package",
                "read_assigned_private_case","submit_technical_opinion",
                "submit_adjudication"]
            and policy["defaultDeny"] is True
            and policy["roleSeparationRequired"] is True
            and policy["mfaConditionRequiredForPrivate"] is True
            and all(policy[k] is False for k in DENIED_FLAGS),
            "RBAC policy attempts to create live identity or maintenance authority")
    sources=policy["sources"]
    require(isinstance(sources,list) and len(sources)==4
            and all(isinstance(s,dict)
                    and set(s)=={"title","url","relevance"}
                    and isinstance(s["title"],str) and len(s["title"])>=20
                    and isinstance(s["url"],str)
                    and s["url"].startswith("https://")
                    and isinstance(s["relevance"],str)
                    and len(s["relevance"])>=40
                    for s in sources),
            "federation and authorization technical references missing")
    return True


def current_public_packets():
    (protocol,worklist,plan,adj_policy,reviews,matrix,parent,mp,dp,rp)=[
        load_public(path) for path in (
            PROTOCOL,WORKLIST,PLAN,ADJ_POLICY,SUBMISSIONS,
            MATRIX,MAP_PATH,MECHANICAL_POLICY,DISCRIMINATION_POLICY,REVIEW_POLICY
        )
    ]
    custody=load_public(CUSTODY_POLICY)
    verify_custody_policy(custody)
    require(custody["identityVerificationProviderConnected"] is False
            and custody["perRoleAccessControlImplemented"] is False,
            "live security controls unexpectedly enabled")
    packets=build_packets(protocol,worklist,plan,adj_policy,reviews,
                          matrix,parent,mp,dp,rp)
    require(packets["packetCount"]==36
            and packets["realReviewOpinionsReceived"]==0
            and packets["verifiedIndependentReviewers"]==0,
            "no verified reviewers exist for the public rehearsal")
    return packets


def validate_fixture(fixture):
    require(isinstance(fixture,dict) and set(fixture)==TOP_FIXTURE
            and fixture["schema"]==
                "maintenance-superinteligence.federation-rbac-rehearsal.v1"
            and fixture["version"]=="1.0.0"
            and fixture["mode"]==
                "author_generated_fake_claims_never_real_oidc_tokens"
            and all(fixture[k] is False for k in
                    ("realIdentitiesPresent","realTokensPresent",
                     "liveProviderConnected")),
            "fake fixture claims real human identity or bearer tokens")
    profiles=fixture["profileActors"]
    require(isinstance(profiles,list) and len(profiles)==len(ACTOR_IDS),
            "five distinct artificial roles required")
    for p,(ident,role,sub) in zip(profiles,ACTOR_IDS):
        require(isinstance(p,dict)
                and set(p)=={"id","role","sub"}
                and (p["id"],p["role"],p["sub"])==(ident,role,sub),
                "synthetic actor identity conflict or profile reassignment")
    rows=fixture["scenarios"]
    require(isinstance(rows,list) and len(rows)==len(KINDS),
            "all 30 synthetic authorization challenges required")
    for i,r in enumerate(rows):
        require(isinstance(r,dict) and set(r)==REQUEST_KEYS
                and r["scenarioId"]==f"FID-{i+1:03d}"
                and r["kind"]==KINDS[i]
                and r["actorProfileId"] in {p["id"] for p in profiles}
                and isinstance(r["action"],str)
                and len(r["action"])>=4
                and isinstance(r["resourceType"],str)
                and isinstance(r["packetId"],str)
                and isinstance(r["expectedNonce"],str)
                and r["expectedNonce"]==f"nonce-{i+1:03d}"
                and isinstance(r["claims"],dict)
                and set(r["claims"])==CLAIM_KEYS,
                "rehearsal input changed or OIDC-like field missing")
        c=r["claims"]
        require(all(type(c[k]) is int for k in ("iat","nbf","exp"))
                and all(isinstance(c[k],str) for k in (
                    "iss","aud","sub","claimedRole","nonce",
                    "jti","alg","acr"))
                and isinstance(c["amr"],list)
                and all(isinstance(v,str) for v in c["amr"])
                and c["issuerTrusted"] is False
                and c["roleAssignmentVerified"] is False
                and c["signatureValidated"] is (r["kind"]=="tampered_auth_claims"),
                "synthetic claims cannot be promoted to validated credentials")
    return rows


def preflight(row,policy,profile,packet_ids,used_jtis):
    """For education only: check fake claim *shape*. No identity is accepted."""
    claim=row["claims"]
    faults=[]
    def flag(condition,why):
        if condition: faults.append(why)
    flag(row["packetId"] not in packet_ids,"unknown_packet")
    flag(claim["iss"]!=policy["syntheticIssuer"],"issuer_mismatch")
    flag(claim["aud"]!=policy["syntheticAudience"],"audience_mismatch")
    flag(claim["sub"]!=profile["sub"],"subject_mismatch")
    flag(claim["claimedRole"]!=profile["role"],"role_claim_mismatch")
    flag(claim["nonce"]!=row["expectedNonce"],"nonce_mismatch")
    flag(claim["alg"]!="RS256","unsupported_algorithm")
    flag(claim["acr"]!="urn:synthetic:mfa","assurance_claim_mismatch")
    flag(claim["amr"]!=["pwd","otp"],"mfa_claim_not_present")
    flag(claim["signatureValidated"] is not False,"self_claimed_signature_not_trusted")
    flag(claim["issuerTrusted"] is not False
         or claim["roleAssignmentVerified"] is not False,
         "self_claimed_external_trust_not_accepted")
    now=policy["simulationClockEpoch"]
    skew=policy["maximumClockSkewSeconds"]
    flag(claim["exp"]<=now-skew,"expired")
    flag(claim["nbf"]>now+skew,"not_yet_valid")
    flag(claim["iat"]>now+skew,"future_issued_at")
    flag(claim["exp"]<=claim["iat"]
         or claim["exp"]-claim["iat"]>
             policy["maxTokenLifetimeSeconds"],"excessive_or_invalid_lifetime")
    flag(not re.fullmatch(r"sim-jti-[0-9]{3}|sim-jti-replay",claim["jti"]),
         "invalid_jti_shape")
    flag(claim["jti"] in used_jtis,"duplicate_jti_in_fixture")
    used_jtis.add(claim["jti"])
    grant=row["action"] in GRANTS[profile["role"]]
    match=RESOURCE_RULES.get(row["action"])==row["resourceType"]
    flag(not grant,"role_not_eligible")
    flag(not match,"resource_action_pair_forbidden")
    flag(row["resourceType"] in
         policy["operationalResourceKinds"],"operational_resource_forbidden")
    return {
        "scenarioId":row["scenarioId"],
        "kind":row["kind"],
        "actorProfileId":row["actorProfileId"],
        "requestedAction":row["action"],
        "resourceType":row["resourceType"],
        "structuralOrRoleFaults":sorted(set(faults)),
        "hypotheticalRoleAndShapeEligible":not faults,
        "oidcSignatureCryptographicallyVerified":False,
        "realIdpIssuerTrusted":False,
        "realAudienceRegistrationVerified":False,
        "actualSubjectAuthenticated":False,
        "realMfaEnforced":False,
        "realSessionRevocationChecked":False,
        "realResourceAclChecked":False,
        "authorizationGranted":False,
        "mayReadPrivateDocuments":False,
        "maySubmitTechnicalOpinion":False,
        "mayApproveTechnicalRelation":False,
        "mayCreateWorkOrder":False,
        "mayModifyEcm":False,
        "mayReleaseEquipment":False,
        "decision":"deny_unverified_external_identity",
    }


def evaluate(policy,fixture):
    validate_policy(policy)
    rows=validate_fixture(fixture)
    packet_registry=current_public_packets()
    packet_ids={x["packetId"] for x in packet_registry["packets"]}
    profiles={p["id"]:p for p in fixture["profileActors"]}
    seen=set()
    results=[preflight(r,policy,profiles[r["actorProfileId"]],
                       packet_ids,seen) for r in rows]
    passed=sum(x["hypotheticalRoleAndShapeEligible"] for x in results)
    faults=Counter(f for x in results for f in x["structuralOrRoleFaults"])
    return {
        "schema":"maintenance-superinteligence.federation-rbac-report.v1",
        "version":"1.0.0",
        "mode":"simulated_claim_shape_and_role_preflight_not_live_access",
        "policyDigest":digest(policy),
        "fixtureDigest":digest(fixture),
        "packetRegistryDigest":digest(packet_registry),
        "scenarioCount":len(results),
        "hypotheticalRoleEligibleCount":passed,
        "structurallyOrRoleRejectedCount":len(results)-passed,
        "actualGrantedCount":0,
        "actorProfiles":len(profiles),
        "availablePacketCount":len(packet_ids),
        "denyReasonCounts":dict(sorted(faults.items())),
        "results":results,
        "realIdpConfigured":False,
        "jwtSignaturesVerified":0,
        "realIdentitiesAuthenticated":0,
        "realMfaSessionsEnforced":0,
        "realRoleBindingsVerified":0,
        "realAuthorizationsGranted":0,
        "realPrivateDocumentsAccessed":0,
        "sourceRulesChanged":False,
        "mayApproveTechnicalRelation":False,
        "mayCreateWorkOrder":False,
        "mayExecuteTest":False,
        "mayModifyEcm":False,
        "mayReleaseEquipment":False,
        "decision":"no_go_connect_verified_oidc_idp_and_real_access_enforcement",
    }


def verify_report(report,policy,fixture):
    require(report==evaluate(policy,fixture),
            "authorization report manipulated, role bypassed or source changed")
    return True


def render_html(report,policy,fixture):
    verify_report(report,policy,fixture)
    require(report["actualGrantedCount"]==0 and
            report["realPrivateDocumentsAccessed"]==0,
            "unsafe authorization grant cannot render")
    sections=[]
    for r in report["results"]:
        sections.append(
            "<section><h2>"+escape(r["scenarioId"])+" — "+
            escape(r["kind"])+"</h2><p><b>Hipótese de perfil:</b> "+
            escape(str(r["hypotheticalRoleAndShapeEligible"]))+
            "</p><p><b>Bloqueio:</b> "+
            escape(", ".join(r["structuralOrRoleFaults"]) or
                   "IdP externo indisponível; verificação real ausente")+
            "</p><p><b>Autorização real:</b> NEGADA.</p></section>")
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; "
        'base-uri &apos;none&apos;; form-action &apos;none&apos;">'
        '<title>Ciclo 39 — Autorização simulada, nenhum acesso real</title>'
        '<style>body{font:15px system-ui;max-width:950px;margin:2em auto;'
        'padding:1em}section{border:1px solid #aaa;margin:1em 0;padding:1em}'
        '</style></head><body><h1>Federação e RBAC — pré-validação, NO GO</h1>'
        '<p>30 cenários artificiais; 0 pessoas autenticadas, 0 tokens '
        'criptograficamente verificados, 0 permissões reais concedidas. '
        'Este painel não faz login nem acesso a documentos privados.</p>' +
        "".join(sections)+"</body></html>"
    )


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    require(args.output.resolve()!=
            (args.html.resolve() if args.html else None),
            "HTML and JSON paths must differ")
    policy=load_public(POLICY)
    fixture=load_public(REHEARSAL)
    report=evaluate(policy,fixture)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(report,policy,fixture),
                             encoding="utf-8")
    return report


if __name__=="__main__":
    main()
