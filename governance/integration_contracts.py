"""Design-only contracts for a FUTURE corporate review service.

No IdP integration, token parsing, signature verification, approvals or data ingest.
Only SIM-* synthetic inputs are accepted. Client-provided claims cannot authenticate
themselves and every attempt to produce real authorization must fail closed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from connectors.fmea_public import ImportRejected, require

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = ROOT / "examples/integration-fixture.v1.json"
POLICY_PATH = ROOT / "governance/integration-policy.v1.json"
ROLES = {"author", "reviewer", "adjudicator", "auditor", "custodian",
         "administrator", "oem_specialist"}
DECISIONS = {"support_general", "insufficient", "challenge"}
BLOCKED = ("create_work_order", "release_equipment", "modify_ecm",
           "approve_maintenance", "approve_oem_applicability", "attest_signature")
REQUIRED_PROOFS = {
    "corporate_identity_provider_server_validation", "unique_human_identity_and_active_role",
    "competence_verified_from_corporate_source", "author_reviewers_adjudicator_separated",
    "no_conflict_record", "two_independent_reviewers",
    "immutable_claim_revision_and_source_manifest",
    "verified_audit_timestamp_and_protected_storage",
    "qualified_document_entitlement_and_oem_effectivity",
    "separate_operational_authorization",
}


def fields(value: object, keys: set[str], label: str) -> dict:
    require(isinstance(value, dict) and set(value) == keys,
            f"{label}: expected exact fields")
    return value


def sim(value: object, prefix: str) -> bool:
    return isinstance(value, str) and re.fullmatch(re.escape(prefix) + r"[A-Z0-9-]+", value) is not None


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def check_policy(policy: object) -> dict:
    p = fields(policy, {"schema", "version", "mode", "roles", "principles",
                        "publicOperationalActionsAllowed", "verificationAvailable",
                        "requiredTrustProofs", "sensitiveDataMustRemainPrivate",
                        "publicActionsAlwaysDenied", "deploymentPrerequisites"}, "policy")
    require(p["schema"] == "maintenance-superinteligence.integration-policy.v1"
            and p["version"] == "1.0.0"
            and p["mode"] == "simulation_only"
            and p["verificationAvailable"] is False
            and p["publicOperationalActionsAllowed"] == [],
            "policy: cannot self-enable verification or operation")
    require(set(p["requiredTrustProofs"]) == REQUIRED_PROOFS
            and len(p["requiredTrustProofs"]) == len(REQUIRED_PROOFS),
            "policy: missing or duplicate trust proof")
    require(set(p["publicActionsAlwaysDenied"]) == set(BLOCKED),
            "policy: operations cannot be enabled")
    require(isinstance(p["roles"], list) and len(p["roles"]) == len(ROLES),
            "policy: missing roles")
    seen = set()
    for row in p["roles"]:
        fields(row, {"role", "canPropose", "cannotAuthorize"}, "policy role")
        require(row["role"] in ROLES and row["role"] not in seen,
                "policy: duplicate/unknown role")
        seen.add(row["role"])
        require(isinstance(row["canPropose"], list)
                and isinstance(row["cannotAuthorize"], list)
                and "approve_maintenance" in row["cannotAuthorize"]
                or (row["role"] in {"auditor","custodian","administrator","oem_specialist"}
                    and row["cannotAuthorize"]),
                "policy: role grants unsanctioned authority")
        require(not any(act in BLOCKED for act in row["canPropose"]),
                "policy: forbidden operation became proposed action")
    require(seen == ROLES and len(set(p["sensitiveDataMustRemainPrivate"])) >= 6
            and len(set(p["deploymentPrerequisites"])) >= 5,
            "policy: missing restricted-data boundaries")
    return p


def validate_fixture(fixture: object, policy: dict) -> dict:
    check_policy(policy)
    f = fields(fixture, {"schema", "version", "nature", "tenantId", "principals",
                         "credentialAssertions", "technicalQualifications", "claimVersion",
                         "independentReviewDecisions", "evidenceManifest", "auditAnchor",
                         "oemEffectivityAttestation", "operationalAuthorizations"}, "integration")
    require(f["schema"] == "maintenance-superinteligence.integration-fixture.v1"
            and f["version"] == "1.0.0"
            and f["nature"] == "untrusted_synthetic_contract_testing"
            and sim(f["tenantId"], "SIM-TENANT-")
            and f["operationalAuthorizations"] == [],
            "fixture: cannot import real tenant or operational authorizations")
    principal_keys = {"principalId","role","discipline","identityAuthenticated",
                      "serverVerified","reviewAuthority"}
    principals={}
    require(isinstance(f["principals"],list) and len(f["principals"]) >= 8,
            "principal: complete synthetic role roster required")
    for p in f["principals"]:
        fields(p,principal_keys,"principal")
        pid=p["principalId"]
        require(sim(pid,"SIM-USER-") and pid not in principals
                and p["role"] in ROLES and p["discipline"] in {"oil","hydraulics",
                     "electronics","mechanics","vibration"}
                and p["identityAuthenticated"] is False
                and p["serverVerified"] is False
                and p["reviewAuthority"] is False,
                "principal: invalid/duplicated or falsely authenticated identity")
        principals[pid]=p
    require({p["role"] for p in principals.values()} == ROLES,
            "principal: incomplete role coverage")
    credentials={}
    for item in f["credentialAssertions"]:
        fields(item,{"principalId","issuer","audience","issuedAt","expiresAt",
                     "nonce","issuerVerified","audienceVerified","signatureVerified",
                     "expiryVerified","revocationChecked"},"credential assertion")
        pid=item["principalId"]
        require(pid in principals and pid not in credentials
                and all(item[k] is None for k in
                        ("issuer","audience","issuedAt","expiresAt","nonce"))
                and all(item[k] is False for k in
                        ("issuerVerified","audienceVerified","signatureVerified",
                         "expiryVerified","revocationChecked")),
                "credential: fake provider cannot validate assertions")
        credentials[pid]=item
    qualification={}
    for item in f["technicalQualifications"]:
        fields(item,{"principalId","discipline","competenceVerified","independenceVerified",
                     "conflictClearVerified","qualificationSource"},"qualification")
        pid=item["principalId"]
        require(pid in principals and pid not in qualification
                and item["discipline"] == principals[pid]["discipline"]
                and item["qualificationSource"] is None
                and all(item[k] is False for k in ("competenceVerified",
                    "independenceVerified","conflictClearVerified")),
                "qualification: cannot self-attest competency or independence")
        qualification[pid]=item
    require(set(principals)==set(credentials)==set(qualification),
            "fixture: incomplete principal assertions")

    claim=fields(f["claimVersion"],{"claimId","revision","claimDigest",
                                   "immutableVersionVerified","realEquipmentRef"},"claim version")
    require(re.fullmatch(r"CLM-[A-Z-]+",claim["claimId"])
            and type(claim["revision"]) is int and claim["revision"]==1
            and isinstance(claim["claimDigest"],str)
            and re.fullmatch(r"[a-f0-9]{64}",claim["claimDigest"])
            and claim["immutableVersionVerified"] is False
            and claim["realEquipmentRef"] is None,
            "claim: revision cannot be treated as immutable or real asset")
    manifest=fields(f["evidenceManifest"],{"manifestId","claimId","classification",
                     "sourceReferenceIds","sourceAccessVerified","realDataIncluded",
                     "licensedContentIncluded","retentionVerified"},"evidence manifest")
    require(sim(manifest["manifestId"],"SIM-MANIFEST-")
            and manifest["claimId"]==claim["claimId"]
            and manifest["classification"]=="public_synthetic"
            and isinstance(manifest["sourceReferenceIds"],list)
            and manifest["sourceReferenceIds"]
            and len(set(manifest["sourceReferenceIds"]))==len(manifest["sourceReferenceIds"])
            and all(re.fullmatch(r"CIT-[A-Z0-9-]+",s) for s in manifest["sourceReferenceIds"])
            and all(manifest[k] is False for k in
                    ("sourceAccessVerified","realDataIncluded",
                     "licensedContentIncluded","retentionVerified")),
            "evidence: cannot claim verified licensed or real records")
    decisions=[]
    seen=set()
    for d in f["independentReviewDecisions"]:
        fields(d,{"decisionId","claimId","principalId","claimRevision","position",
                  "signatureVerified","independenceVerified","operationalApproval"},"review decision")
        require(sim(d["decisionId"],"SIM-DECISION-") and d["decisionId"] not in seen,
                "review: duplicate decision ID")
        seen.add(d["decisionId"])
        pid=d["principalId"]
        require(pid in principals and principals[pid]["role"]=="reviewer"
                and d["claimId"]==claim["claimId"]
                and type(d["claimRevision"]) is int
                and d["claimRevision"]==claim["revision"]
                and d["position"] in DECISIONS
                and all(d[k] is False for k in
                    ("signatureVerified","independenceVerified","operationalApproval")),
                "review: self-review, wrong role/revision or invented signature")
        decisions.append(d)
    require(len(decisions)==2 and len({d["principalId"] for d in decisions})==2,
            "review: two distinct fictional reviewer IDs required")
    require(all(d["principalId"] not in
            {p["principalId"] for p in principals.values()
             if p["role"] in ("author","adjudicator")}
            for d in decisions),"review: separation of roles failed")
    anchor=fields(f["auditAnchor"],{"anchorId","claimId","sourceDigest",
                  "externalTimestampVerified","externalStoreVerified","appendOnlyVerified",
                  "signerVerified"},"audit anchor")
    require(sim(anchor["anchorId"],"SIM-ANCHOR-")
            and anchor["claimId"]==claim["claimId"]
            and re.fullmatch(r"[a-f0-9]{64}",anchor["sourceDigest"])
            and all(anchor[k] is False for k in ("externalTimestampVerified",
                "externalStoreVerified","appendOnlyVerified","signerVerified")),
            "audit: no external trusted anchor exists")
    oem=fields(f["oemEffectivityAttestation"],{"attestationId","claimId","manufacturer",
               "model","serialOrArrangement","publication","revision","entitlementVerified",
               "documentVerified","effectivityVerified","qualifiedApproverVerified",
               "operationalApproval"},"oem attestation")
    require(sim(oem["attestationId"],"SIM-OEM-")
            and oem["claimId"]==claim["claimId"]
            and all(oem[k] is None for k in ("manufacturer","model",
                 "serialOrArrangement","publication","revision"))
            and all(oem[k] is False for k in ("entitlementVerified","documentVerified",
                 "effectivityVerified","qualifiedApproverVerified","operationalApproval")),
            "oem: publication and effectivity not verified")
    return {"principals":principals,"decisions":decisions,"claim":claim,
            "evidence":manifest,"anchor":anchor,"oem":oem}


def evaluate_contract(fixture: dict, policy: dict) -> dict:
    data=validate_fixture(fixture,policy)
    votes=[d["position"] for d in data["decisions"]]
    review_status=("disputed_simulation" if "challenge" in votes else
                   "needs_evidence_simulation" if "insufficient" in votes else
                   "general_consensus_simulation")
    return {
       "schema":"maintenance-superinteligence.private-integration-report.v1",
       "mode":"offline_contract_test_no_external_verifier",
       "fixtureSha256":digest(fixture),"policySha256":digest(policy),
       "principalCount":len(data["principals"]),
       "fictionalReviewerIds":[d["principalId"] for d in data["decisions"]],
       "reviewStatus":review_status,
       "credentialChecksAuthenticated":0,
       "competenceChecksVerified":0,
       "reviewSignaturesVerified":0,
       "auditAnchorVerified":False,"oemSeriesApproved":False,
       "claimRevisionExternallySealed":False,
       "requiredPrivateProofs":[{"proof":x,"status":"not_implemented"}
                                 for x in policy["requiredTrustProofs"]],
       "allowedPublicOperations":[],
       "realEvidenceProcessed":False,
       "independentlyReviewedByHumans":False,
       "mayQualifyRealKnowledge":False,
       "mayOpenWorkOrder":False,
       "mayChangeEquipment":False,
       "approval":"blocked_missing_private_verified_trust",
       "limitations":[
           "Synthetic IDs do not establish independent human identities.",
           "Client-side flags, dummy digests and JSON fixtures are not cryptographic proofs.",
           "No OIDC/SAML protocol, key management, IdP, licensed OEM or WORM audit integrated.",
           "This report is a design conformance exercise, not enterprise deployment."],
    }


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture",type=Path,default=FIXTURE_PATH)
    p.add_argument("--policy",type=Path,default=POLICY_PATH)
    p.add_argument("--output",type=Path)
    args=p.parse_args(argv)
    try:
        policy=json.loads(args.policy.read_text(encoding="utf-8"))
        fixture=json.loads(args.fixture.read_text(encoding="utf-8"))
        result=evaluate_contract(fixture,policy)
        output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(output,encoding="utf-8")
        print(output)
        return 0
    except (ImportRejected,KeyError,ValueError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed","reason":str(exc),
                          "approval":"blocked"},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
