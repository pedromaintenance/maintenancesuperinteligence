"""Cycle 38 — PRIVATE local custody for reviewer text and evidence bytes.

HMAC binds file content to a custody key. It does NOT authenticate humans,
validate OEM applicability, encrypt information, or authorize maintenance.
All private case inputs, keys, receipts, and reports must live outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re

from benchmarks.heldout_study import private_path, read_private_key, save_private
from knowledge.independent_review import (
    PROTOCOL, WORKLIST, build_packets, load as load_public,
)
from knowledge.causal_adjudication import (
    PLAN, POLICY as ADJ_POLICY, SUBMISSIONS, MATRIX, MAP_PATH,
    MECHANICAL_POLICY, DISCRIMINATION_POLICY, REVIEW_POLICY,
)
from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "governance/private-review-custody-policy.v1.json"
ROLES = ("technical_reviewer_a", "technical_reviewer_b", "adjudicator")
REVIEW_POSITIONS = ("conditional_support", "conditional_reject",
                    "request_revision", "abstain")
BATCH_KEYS = {"schema", "version", "mode", "packetId", "ruleId",
              "packetDigest", "records", "evidenceFiles",
              "identityProofValidated", "externalAuthorizationValidated",
              "oemSeriesEffectivityValidated", "humanSignoffValidated",
              "mayExecuteTest", "mayCreateWorkOrder", "mayReleaseEquipment"}
REC_KEYS = {"recordId", "reviewerSlot", "rolePseudonym",
            "externalClaimReference", "reviewPosition", "reasoning",
            "counterexampleHandling", "sourceIds",
            "identityVerified", "competenceVerified", "independenceVerified",
            "consentVerified", "digitalSignatureVerified",
            "oemEffectivityVerified", "mayAuthorizeMaintenance"}
EVIDENCE_KEYS = {"path", "sha256"}
NEVER_APPROVED = ("identityProofValidated", "externalAuthorizationValidated",
                  "oemSeriesEffectivityValidated", "humanSignoffValidated",
                  "mayExecuteTest", "mayCreateWorkOrder", "mayReleaseEquipment")
RECORD_DENIALS = ("identityVerified", "competenceVerified",
                  "independenceVerified", "consentVerified",
                  "digitalSignatureVerified", "oemEffectivityVerified",
                  "mayAuthorizeMaintenance")
POLICY_DENIALS = (
    "identityVerificationProviderConnected",
    "externalAuthorizationProviderConnected", "perRoleAccessControlImplemented",
    "encryptedStorageImplemented", "externalSignatureVerified",
    "oemEffectivityVerified", "independentHumanReviewConfirmed",
    "operationalSignoffApproved", "mayCreateWorkOrder", "mayExecuteTest",
    "mayReleaseEquipment",
)
REF_REGEX = re.compile(r"^REF-[A-Z0-9]{4,32}$")
ALIAS_REGEX = re.compile(r"^PSEUDO-[A-Z0-9]{3,24}$")


def validated_policy(policy):
    fields = {"schema", "version", "mode", "maxEvidenceFiles", "maxFileBytes",
              "requiredRoles", "allowedReviewerPositions",
              "adjudicatorDisposition", *POLICY_DENIALS, "sources"}
    require(isinstance(policy, dict) and set(policy) == fields
            and policy["schema"] ==
                "maintenance-superinteligence.private-review-custody-policy.v1"
            and policy["version"] == "1.0.0"
            and policy["mode"] ==
                "local_private_hmac_integrity_not_identity_verification"
            and type(policy["maxEvidenceFiles"]) is int
            and policy["maxEvidenceFiles"] == 4
            and type(policy["maxFileBytes"]) is int
            and policy["maxFileBytes"] == 20971520
            and policy["requiredRoles"] == list(ROLES)
            and policy["allowedReviewerPositions"] == list(REVIEW_POSITIONS)
            and policy["adjudicatorDisposition"] == "defer_unverified"
            and all(policy[k] is False for k in POLICY_DENIALS),
            "custody policy falsely claims authentication, security or approval")
    sources = policy["sources"]
    require(isinstance(sources, list) and len(sources) == 3
            and all(isinstance(s,dict)
                    and set(s) == {"title", "url", "scope"}
                    and isinstance(s["title"],str) and len(s["title"]) > 20
                    and isinstance(s["scope"],str) and len(s["scope"]) > 50
                    and isinstance(s["url"],str)
                    and (s["url"].startswith("https://csrc.nist.gov/")
                         or s["url"].startswith("https://www.nist.gov/"))
                    for s in sources), "public standards references malformed")
    return policy


def public_packet(packet_id):
    require(isinstance(packet_id,str) and
            re.fullmatch(r"IRP-[0-9]{3}",packet_id),
            "packet ID invalid")
    protocol, worklist = load_public(PROTOCOL), load_public(WORKLIST)
    plan, ap, subs, matrix, parent, mp, dp, rp = [
        load_public(p) for p in
        (PLAN, ADJ_POLICY, SUBMISSIONS, MATRIX, MAP_PATH,
         MECHANICAL_POLICY, DISCRIMINATION_POLICY, REVIEW_POLICY)
    ]
    # build_packets validates full frozen upstream source, not just ID fields
    bundle = build_packets(protocol,worklist,plan,ap,subs,matrix,parent,mp,dp,rp)
    matches = [p for p in bundle["packets"] if p["packetId"] == packet_id]
    require(len(matches) == 1, "packet not in committed Cycle 37 registry")
    return matches[0]


def evidence_bytes_check(row, policy):
    require(isinstance(row,dict) and set(row) == EVIDENCE_KEYS,
            "missing/extra evidence file fields")
    name = row["path"]
    wanted = row["sha256"]
    require(isinstance(name,str) and Path(name).is_absolute()
            and isinstance(wanted,str)
            and re.fullmatch(r"[a-f0-9]{64}",wanted),
            "evidence file path must be absolute and digest valid")
    # No symlink evidence: avoid changing target after validation, though
    # filesystem race protection needs OS handles/storage external to this CLI.
    untrusted = Path(name)
    require(not untrusted.is_symlink(), "symlink evidence forbidden")
    path = private_path(untrusted)
    require(path.is_file() and path.stat().st_size <= policy["maxFileBytes"]
            and path.stat().st_size > 0,
            "evidence attachment absent, empty or over allowed file size")
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(262144), b""):
            h.update(chunk)
    require(hmac.compare_digest(h.hexdigest(),wanted),
            "attachment was altered, substituted or mislabeled")
    return wanted


def inspect(submission, policy):
    validated_policy(policy)
    require(isinstance(submission,dict) and set(submission) == BATCH_KEYS
            and submission["schema"] ==
                "maintenance-superinteligence.private-review-submission.v1"
            and submission["version"] == "1.0.0"
            and submission["mode"] ==
                "private_unverified_reviewer_claims_not_operational"
            and all(submission[k] is False for k in NEVER_APPROVED),
            "private submission falsely asserts security or operational proof")
    packet = public_packet(submission["packetId"])
    require(submission["ruleId"] == packet["ruleId"]
            and submission["packetDigest"] == digest(packet),
            "wrong source rule, stale packet or manipulated public technical snapshot")
    refs = {s["sourceId"] for s in packet["generalBackgroundSources"]}
    records = submission["records"]
    require(isinstance(records,list) and len(records) == 3,
            "one claim per segregated slot required")
    used_aliases=set()
    for idx,r in enumerate(records):
        require(isinstance(r,dict) and set(r) == REC_KEYS,
                "review record missing fields")
        expected_role = ROLES[idx]
        alias = r["rolePseudonym"]
        require(r["reviewerSlot"] == expected_role
                and r["recordId"] ==
                    f"{submission['packetId']}-{('A','B','D')[idx]}"
                and isinstance(alias,str)
                and ALIAS_REGEX.fullmatch(alias)
                and alias not in used_aliases
                and isinstance(r["externalClaimReference"],str)
                and REF_REGEX.fullmatch(r["externalClaimReference"]),
                "review role collision, missing role assignment or invalid pseudonym")
        used_aliases.add(alias)
        require((r["reviewPosition"] in REVIEW_POSITIONS
                 if idx < 2 else r["reviewPosition"] == "defer_unverified")
                and isinstance(r["reasoning"],str)
                and len(r["reasoning"].strip()) >= 80
                and isinstance(r["counterexampleHandling"],str)
                and len(r["counterexampleHandling"].strip()) >= 55,
                "missing reasoning, counterexample handling or abstention")
        source_ids = r["sourceIds"]
        require(isinstance(source_ids,list) and 1<=len(source_ids)<=len(refs)
                and len(set(source_ids))==len(source_ids)
                and set(source_ids).issubset(refs),
                "private opinion references source not included in packet")
        require(all(r[k] is False for k in RECORD_DENIALS),
                "reviewer self-asserted credentials or unverified signoff")
    files=submission["evidenceFiles"]
    require(isinstance(files,list) and 1<=len(files)<=policy["maxEvidenceFiles"],
            "at least one private evidence attachment is required")
    names=[]
    for f in files:
        evidence_bytes_check(f,policy)
        names.append(str(private_path(f["path"])))
    require(len(names)==len(set(names)), "duplicate evidence attachment")
    return packet


def frozen_receipt(submission, policy, key):
    packet = inspect(submission, policy)
    payload = {
        "submissionDigest":digest(submission),
        "packetDigest":digest(packet),
        "policyDigest":digest(policy),
        "attachmentDigests":[x["sha256"] for x in submission["evidenceFiles"]],
    }
    authentication_tag = hmac.new(key,
        json.dumps(payload,sort_keys=True,separators=(",",":")).encode("utf-8"),
        hashlib.sha256).hexdigest()
    return {
        "schema":"maintenance-superinteligence.private-review-receipt.v1",
        "version":"1.0.0",
        "mode":"local_hmac_custodian_key_not_human_signature",
        **payload,
        "custodyHmacSha256":authentication_tag,
        "identityAuthenticated":False,
        "rolePermissionVerified":False,
        "contentEncrypted":False,
        "independentReviewVerified":False,
        "humanSignoffValidated":False,
        "mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
    }


def verify_receipt(receipt, submission, policy, key):
    expected = frozen_receipt(submission,policy,key)
    require(isinstance(receipt,dict) and set(receipt)==set(expected),
            "receipt invalid")
    # Compare MAC separately using constant-time comparison
    want=receipt["custodyHmacSha256"]
    require(isinstance(want,str)
            and hmac.compare_digest(want,expected["custodyHmacSha256"]),
            "receipt MAC invalid or custody key changed")
    require(all(receipt[k]==expected[k] for k in expected
                if k!="custodyHmacSha256"),
            "receipt metadata changed")
    return True


def safe_report(receipt,submission,policy,key):
    verify_receipt(receipt,submission,policy,key)
    positions=[r["reviewPosition"] for r in submission["records"][:2]]
    return {
        "schema":"maintenance-superinteligence.private-review-custody-report.v1",
        "version":"1.0.0",
        "mode":"verified_local_byte_integrity_without_human_authentication",
        "packetId":submission["packetId"],
        "ruleId":submission["ruleId"],
        "packetDigest":receipt["packetDigest"],
        "submissionDigest":receipt["submissionDigest"],
        "receiptDigest":digest(receipt),
        "attachmentCount":len(submission["evidenceFiles"]),
        "attachmentByteDigestsChecked":True,
        "hmacVerifiedAgainstCustodianKey":True,
        "distinctRolePseudonymsPresent":True,
        "technicalDissentPresent":positions[0]!=positions[1],
        "claimedReviewerRecords":2,
        "claimedAdjudicatorRecords":1,
        "verifiedHumanReviewers":0,
        "externalIdentityProviderConnected":False,
        "humanCredentialsVerified":False,
        "organizationalAccessControlVerified":False,
        "encryptionVerified":False,
        "oemBySerialVerified":False,
        "independentTechnicalReviewCompleted":False,
        "upstreamRuleChanged":False,
        "mayExecuteTest":False,
        "mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
        "decision":"no_go_private_integrity_only_external_identity_and_authorization_required",
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    cmds=p.add_subparsers(dest="stage",required=True)
    for stage in ("seal","audit"):
        x=cmds.add_parser(stage)
        x.add_argument("--submission",type=Path,required=True)
        x.add_argument("--key",type=Path,required=True)
        x.add_argument("--receipt",type=Path,required=True)
        if stage=="audit":
            x.add_argument("--report",type=Path,required=True)
    args=p.parse_args(argv)
    paths=[args.submission,args.key,args.receipt]
    if args.stage=="audit":
        paths.append(args.report)
    paths=[private_path(f) for f in paths]
    require(len(set(paths))==len(paths),"private file paths must differ")
    policy=validated_policy(load_public(POLICY))
    submission=json.loads(args.submission.read_text(encoding="utf-8"))
    key=read_private_key(args.key)
    if args.stage=="seal":
        require(not args.receipt.exists(), "receipt path must be new")
        receipt=frozen_receipt(submission,policy,key)
        save_private(args.receipt,receipt)
        return receipt
    receipt=json.loads(args.receipt.read_text(encoding="utf-8"))
    report=safe_report(receipt,submission,policy,key)
    save_private(args.report,report)
    return report


if __name__=="__main__":
    main()
