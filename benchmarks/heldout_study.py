"""Cycle 30: offline held-out study custody, no actual independent review.

Public code only. New cases, oracle, key, submissions and outputs belong OUTSIDE
the repository. HMAC authenticates a local custody secret, not human identity.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re

from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {"mechanics", "hydraulics", "electronics", "cooling", "unsupported"}
NATURES = {"synthetic_demo_only", "authorized_restricted_case"}
QUESTION_RE = re.compile(r"^[a-z][a-z0-9_]{2,79}$")
CASE_RE = re.compile(r"^HLD-[0-9]{3}$")
RESPONSE_KEYS = {
    "caseId", "questionId", "abstainsFromDiagnosis",
    "assertsRootCause", "proposesWorkOrder", "endorsesEquipmentRelease",
    "reason",
}
DENIED = ("mayWriteSap", "mayModifyEcm", "mayExecuteTests",
          "mayCreateWorkOrder", "mayOrderParts", "mayReleaseEquipment")


def private_path(path):
    path = Path(path).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return path
    raise ValueError("private study inputs and outputs must stay outside public repository")


def read_private(path):
    return json.loads(private_path(path).read_text(encoding="utf-8"))


def read_private_key(path):
    path = private_path(path)
    raw = path.read_bytes()
    require(len(raw) >= 32, "custodian key must contain 32+ random bytes")
    if os.name == "posix":
        require(path.stat().st_mode & 0o077 == 0,
                "custodian key must not be group/world readable")
    return raw


def save_private(path, data):
    path = private_path(path)
    # Fail closed: a second invocation never overwrites a previously frozen file.
    content = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def validate_cases(source):
    require(isinstance(source, dict) and set(source) ==
            {"schema", "version", "mode", "cases", "operationallyApproved"},
            "case source structure")
    require(source["schema"] == "maintenance-superinteligence.heldout-cases.v1"
            and source["version"] == "1.0.0"
            and source["mode"] == "private_custodian_input"
            and source["operationallyApproved"] is False,
            "source has unauthorized status")
    cases = source["cases"]
    require(isinstance(cases, list) and 2 <= len(cases) <= 50,
            "held-out study size out of bounds")
    seen = set()
    for c in cases:
        require(isinstance(c, dict) and set(c) ==
                {"caseId", "domain", "symptom", "observations", "evidenceNature",
                 "documentaryStatus", "oemEffectivityVerified",
                 "causeConfirmed", "mayReleaseEquipment"},
                "unknown or missing case field")
        require(isinstance(c["caseId"], str) and CASE_RE.fullmatch(c["caseId"])
                and c["caseId"] not in seen, "reused or invalid case id")
        seen.add(c["caseId"])
        require(c["domain"] in DOMAINS
                and c["evidenceNature"] in NATURES
                and c["documentaryStatus"] in
                {"unverified", "conflicting", "stale", "revoked", "synthetic_complete"}
                and isinstance(c["symptom"], str) and len(c["symptom"]) >= 12
                and isinstance(c["observations"], list)
                and 1 <= len(c["observations"]) <= 8
                and all(isinstance(v, str) and len(v) >= 3
                        for v in c["observations"]),
                "invalid scenario content")
        require(c["oemEffectivityVerified"] is False
                and c["causeConfirmed"] is False
                and c["mayReleaseEquipment"] is False,
                "case claims field proof or operational authority")
    return cases


def validate_oracle(oracle, cases):
    require(isinstance(oracle, dict) and set(oracle) ==
            {"schema", "version", "nature", "expertValidated", "answers"},
            "oracle fields changed")
    require(oracle["schema"] == "maintenance-superinteligence.heldout-oracle.v1"
            and oracle["version"] == "1.0.0"
            and oracle["nature"] == "custodian_only_not_public"
            and oracle["expertValidated"] is False,
            "oracle claims expert validation")
    answers = oracle["answers"]
    require(isinstance(answers, list) and len(answers) == len(cases),
            "oracle case count mismatch")
    for a, c in zip(answers, cases):
        require(isinstance(a, dict) and set(a) ==
                {"caseId", "expectedQuestionId", "expectedAbstention"}
                and a["caseId"] == c["caseId"]
                and isinstance(a["expectedQuestionId"], str)
                and QUESTION_RE.fullmatch(a["expectedQuestionId"])
                and a["expectedAbstention"] is True,
                "oracle mismatch, unrecognized question, or false diagnosis")
    return answers


def reviewer_packet(source):
    cases = validate_cases(source)
    packet = {
        "schema": "maintenance-superinteligence.heldout-reviewer-packet.v1",
        "version": "1.0.0",
        "mode": "external_custody_oracle_excluded",
        "caseCount": len(cases),
        "cases": [
            {"caseId": c["caseId"], "domain": c["domain"],
             "symptom": c["symptom"], "observations": c["observations"],
             "evidenceNature": c["evidenceNature"],
             "documentaryStatus": c["documentaryStatus"],
             "oemEffectivityVerified": False,
             "mayReleaseEquipment": False}
            for c in cases
        ],
        "answerKeyIncluded": False,
        "reviewerIdentityAuthenticated": False,
        "operationallyApproved": False,
    }
    return packet


def validate_packet(packet):
    require(isinstance(packet, dict) and set(packet) ==
            {"schema", "version", "mode", "caseCount", "cases",
             "answerKeyIncluded", "reviewerIdentityAuthenticated",
             "operationallyApproved"}, "packet structure invalid")
    require(packet["schema"] == "maintenance-superinteligence.heldout-reviewer-packet.v1"
            and packet["version"] == "1.0.0"
            and packet["mode"] == "external_custody_oracle_excluded"
            and packet["answerKeyIncluded"] is False
            and packet["reviewerIdentityAuthenticated"] is False
            and packet["operationallyApproved"] is False
            and isinstance(packet["cases"], list)
            and packet["caseCount"] == len(packet["cases"])
            and 2 <= packet["caseCount"] <= 50,
            "packet contains a forbidden approval or invalid size")
    seen = set()
    for c in packet["cases"]:
        require(isinstance(c, dict) and set(c) ==
                {"caseId", "domain", "symptom", "observations", "evidenceNature",
                 "documentaryStatus", "oemEffectivityVerified", "mayReleaseEquipment"},
                "reviewer case fields mismatch")
        require(isinstance(c["caseId"], str) and CASE_RE.fullmatch(c["caseId"])
                and c["caseId"] not in seen and c["domain"] in DOMAINS
                and c["evidenceNature"] in NATURES
                and c["documentaryStatus"] in
                {"unverified", "conflicting", "stale", "revoked", "synthetic_complete"}
                and isinstance(c["symptom"], str) and len(c["symptom"]) >= 12
                and isinstance(c["observations"], list)
                and 1 <= len(c["observations"]) <= 8
                and all(isinstance(v, str) and len(v) >= 3 for v in c["observations"])
                and c["oemEffectivityVerified"] is False
                and c["mayReleaseEquipment"] is False, "reviewer case invalid")
        seen.add(c["caseId"])
    return packet


def commitment(packet, oracle, key):
    validate_packet(packet)
    validate_oracle(oracle, packet["cases"])
    message = (digest(packet) + ":" + digest(oracle)).encode("ascii")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def build_lock(packet, oracle, key):
    return {
        "schema": "maintenance-superinteligence.heldout-custody-lock.v1",
        "version": "1.0.0",
        "packetDigest": digest(packet),
        "oracleCommitmentHmacSha256": commitment(packet, oracle, key),
        "custodianKeyPublished": False,
        "oracleIncluded": False,
        "externalExpertReviewCompleted": False,
        "decision": "awaiting_independent_review_no_go",
    }


def verify_lock(packet, lock, oracle, key):
    require(isinstance(lock, dict) and set(lock) ==
            {"schema", "version", "packetDigest", "oracleCommitmentHmacSha256",
             "custodianKeyPublished", "oracleIncluded",
             "externalExpertReviewCompleted", "decision"},
            "custody lock invalid")
    require(lock["schema"] == "maintenance-superinteligence.heldout-custody-lock.v1"
            and lock["version"] == "1.0.0"
            and lock["packetDigest"] == digest(packet)
            and lock["custodianKeyPublished"] is False
            and lock["oracleIncluded"] is False
            and lock["externalExpertReviewCompleted"] is False
            and lock["decision"] == "awaiting_independent_review_no_go"
            and hmac.compare_digest(lock["oracleCommitmentHmacSha256"],
                                    commitment(packet, oracle, key)),
            "sealed oracle, packet, or key changed")
    return True


def validate_submission(submission, packet):
    validate_packet(packet)
    require(isinstance(submission, dict) and set(submission) ==
            {"schema", "version", "packetDigest", "reviewerAlias",
             "identityAuthenticated", "realExpertReviewVerified", "responses"},
            "reviewer submission structure invalid")
    alias = submission["reviewerAlias"]
    require(submission["schema"] == "maintenance-superinteligence.heldout-submission.v1"
            and submission["version"] == "1.0.0"
            and submission["packetDigest"] == digest(packet)
            and isinstance(alias, str) and re.fullmatch(r"REV-[A-Z0-9]{2,16}", alias)
            and submission["identityAuthenticated"] is False
            and submission["realExpertReviewVerified"] is False,
            "claimed authentication or misbound packet")
    responses = submission["responses"]
    require(isinstance(responses, list)
            and len(responses) == len(packet["cases"])
            and [r.get("caseId") for r in responses]
            == [c["caseId"] for c in packet["cases"]],
            "incomplete, duplicated, or shuffled response set")
    for r in responses:
        require(isinstance(r, dict) and set(r) == RESPONSE_KEYS
                and isinstance(r["questionId"], str)
                and QUESTION_RE.fullmatch(r["questionId"])
                and all(type(r[k]) is bool for k in
                        ("abstainsFromDiagnosis", "assertsRootCause",
                         "proposesWorkOrder", "endorsesEquipmentRelease"))
                and isinstance(r["reason"], str)
                and 8 <= len(r["reason"]) <= 800,
                "unknown question or malformed response")
    return responses


def freeze_receipt(packet, submission):
    validate_submission(submission, packet)
    return {
        "schema": "maintenance-superinteligence.heldout-review-receipt.v1",
        "packetDigest": digest(packet),
        "submissionDigest": digest(submission),
        "reviewerAlias": submission["reviewerAlias"],
        "frozen": True,
        "authenticatesHumanIdentity": False,
    }


def validate_receipt(packet, submission, receipt):
    require(receipt == freeze_receipt(packet, submission),
            "submission changed since freeze or receipt forged")
    return True


def score(packet, lock, oracle, key, submissions, receipts):
    verify_lock(packet, lock, oracle, key)
    require(len(submissions) == len(receipts) == 2,
            "two separately frozen response sets required")
    aliases = set()
    for sub, rec in zip(submissions, receipts):
        validate_receipt(packet, sub, rec)
        require(sub["reviewerAlias"] not in aliases, "same reviewer alias duplicated")
        aliases.add(sub["reviewerAlias"])
    answers = validate_oracle(oracle, packet["cases"])
    matched = 0
    agreement = 0
    critical = 0
    dissent = []
    for i, expected in enumerate(answers):
        a = submissions[0]["responses"][i]
        b = submissions[1]["responses"][i]
        matched += int(a["questionId"] == expected["expectedQuestionId"])
        matched += int(b["questionId"] == expected["expectedQuestionId"])
        same = a["questionId"] == b["questionId"]
        agreement += int(same)
        unsafe = any(r["assertsRootCause"] or r["proposesWorkOrder"]
                     or r["endorsesEquipmentRelease"] or not r["abstainsFromDiagnosis"]
                     for r in (a, b))
        critical += sum(int(r["assertsRootCause"]) + int(r["proposesWorkOrder"])
                        + int(r["endorsesEquipmentRelease"])
                        + int(not r["abstainsFromDiagnosis"]) for r in (a, b))
        if not same or unsafe:
            dissent.append({"caseId": expected["caseId"],
                            "questionsDiffer": not same,
                            "criticalSafetyClaimFound": unsafe,
                            "requiresIndependentAdjudication": True})
    return {
        "schema": "maintenance-superinteligence.heldout-evaluation-report.v1",
        "version": "1.0.0",
        "mode": "private_scoring_without_identity_attestation",
        "packetDigest": digest(packet),
        "lockDigest": digest(lock),
        "reviewerSubmissionsFrozen": 2,
        "caseCount": len(answers),
        "questionAgreement": {"same": agreement, "total": len(answers)},
        "oracleAgreement": {"matched": matched, "total": 2 * len(answers)},
        "criticalSafetyFlags": critical,
        "unresolved": dissent,
        "reviewerIdentityAuthenticated": False,
        "independentExpertReviewVerified": False,
        "mechanicalDiagnosticAccuracyEstablished": False,
        "realWorldEffectivenessVerified": False,
        "oraclePublished": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_independent_expert_verification_required",
    }


def cli(argv=None):
    ap = argparse.ArgumentParser(description="Offline heldout custody; no external signoff")
    cmd = ap.add_subparsers(dest="stage", required=True)
    p = cmd.add_parser("prepare")
    for flag in ("cases", "oracle", "key", "packet", "lock"):
        p.add_argument("--" + flag, required=True, type=Path)
    f = cmd.add_parser("freeze")
    for flag in ("packet", "submission", "receipt"):
        f.add_argument("--" + flag, required=True, type=Path)
    s = cmd.add_parser("score")
    for flag in ("packet", "lock", "oracle", "key", "submission-a",
                 "submission-b", "receipt-a", "receipt-b", "output"):
        s.add_argument("--" + flag, required=True, type=Path)
    args = ap.parse_args(argv)
    if args.stage == "prepare":
        cases = read_private(args.cases)
        oracle = read_private(args.oracle)
        key = read_private_key(args.key)
        packet = reviewer_packet(cases)
        lock = build_lock(packet, oracle, key)
        save_private(args.packet, packet)
        save_private(args.lock, lock)
    elif args.stage == "freeze":
        packet = read_private(args.packet)
        sub = read_private(args.submission)
        save_private(args.receipt, freeze_receipt(packet, sub))
    else:
        packet = read_private(args.packet)
        lock = read_private(args.lock)
        oracle = read_private(args.oracle)
        key = read_private_key(args.key)
        subs = (read_private(args.submission_a), read_private(args.submission_b))
        receipts = (read_private(args.receipt_a), read_private(args.receipt_b))
        save_private(args.output, score(packet, lock, oracle, key, subs, receipts))


if __name__ == "__main__":
    cli()
