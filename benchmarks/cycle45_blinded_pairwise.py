"""Cycle 45: private paired-question review REHEARSAL, never real expert attestation.

Reuses the held-out case validator and mandatory private quality preflight from
Cycles 30-32. Packet provenance is masked using balanced random arm assignment;
the mapping stays outside the public repository. This implementation cannot
verify human identities, independence, licensing or clinical/mechanical truth.

This lab's data must remain outside the repository, including synthetic data
used for its local CLI. CI creates artificial inputs in ephemeral directories.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets

from benchmarks.heldout_study import (
    read_private, read_private_key, reviewer_packet,
    save_private, validate_cases,
)
from benchmarks.private_quality_gate import (
    receipt as quality_receipt,
    verify_receipt as verify_quality_receipt,
)
from pilot.change_review_packets import digest, require

SCHEMA_PREFIX = "maintenance-superinteligence.cycle45"
REVIEWER = re.compile(r"^REV-[A-Z0-9]{2,16}$")
QUESTION = re.compile(r"^[a-z][a-z0-9_]{2,79}$")
ALLOWED_FLAGS = frozenset({
    "unsafe_question", "evidence_insufficient", "oem_effectivity_unknown",
    "cannot_assess_blindly", "question_implies_unapproved_test",
})
CHOICES = frozenset(("A", "B", "tie", "abstain"))
STUDY_DENIALS = (
    "realReviewerAuthenticated", "independentExpertReviewVerified",
    "mechanicalValidityEstablished", "mayExecuteTest",
    "mayWriteSAP", "mayModifyECM", "mayReleaseEquipment",
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_candidates(data, source):
    cases = validate_cases(source)
    require(isinstance(data, dict) and set(data) ==
            {"schema", "version", "mode", "cases", "realExpertReviewCompleted",
             "mayExecuteTest"}, "candidate source shape changed")
    require(data["schema"] == SCHEMA_PREFIX + "-candidate-source.v1"
            and data["version"] == "1.0.0"
            and data["mode"] == "private_custodian_pair_source"
            and data["realExpertReviewCompleted"] is False
            and data["mayExecuteTest"] is False,
            "candidates falsely claim external acceptance")
    rows = data["cases"]
    require(isinstance(rows, list) and len(rows) == len(cases)
            and [r.get("caseId") for r in rows] ==
            [c["caseId"] for c in cases], "candidate list mismatches source")
    for row in rows:
        require(isinstance(row, dict)
                and set(row) == {"caseId", "baseline", "experimental"},
                "unknown candidate attribute")
        pair = (row["baseline"], row["experimental"])
        for q in pair:
            require(isinstance(q, dict)
                    and set(q) == {"questionId", "questionText",
                                   "physicalTestAuthorized"}
                    and isinstance(q["questionId"], str)
                    and QUESTION.fullmatch(q["questionId"])
                    and isinstance(q["questionText"], str)
                    and 25 <= len(q["questionText"].strip()) <= 500
                    and q["physicalTestAuthorized"] is False,
                    "invalid question or implied test permission")
        require(pair[0]["questionId"] != pair[1]["questionId"]
                and pair[0]["questionText"].casefold().strip() !=
                pair[1]["questionText"].casefold().strip(),
                "identical baseline and experimental candidates")
    return rows


def balanced_assignment(n):
    """Cryptographic randomness, approximately balanced within one batch."""
    require(type(n) is int and 2 <= n <= 50, "invalid study size")
    baseline_first = ["A"] * (n // 2) + ["B"] * (n // 2)
    if n % 2:
        baseline_first.append(("A", "B")[secrets.randbelow(2)])
    secrets.SystemRandom().shuffle(baseline_first)
    return baseline_first


def build_packet(source, candidates, assignment):
    cases = validate_cases(source)
    pairs = validate_candidates(candidates, source)
    require(isinstance(assignment, list) and len(assignment) == len(cases)
            and all(x in ("A", "B") for x in assignment)
            and abs(assignment.count("A") - assignment.count("B")) <= 1,
            "invalid or unbalanced blind assignment")
    parent = reviewer_packet(source)
    blinded = []
    for case, pair, arm in zip(parent["cases"], pairs, assignment):
        a = pair["baseline"]["questionText"] if arm == "A" else pair["experimental"]["questionText"]
        b = pair["experimental"]["questionText"] if arm == "A" else pair["baseline"]["questionText"]
        blinded.append({**case, "questionA": a, "questionB": b})
    return {
        "schema": SCHEMA_PREFIX + "-reviewer-packet.v1",
        "version": "1.0.0",
        "mode": "private_masked_pair_review_not_attestation",
        "caseCount": len(blinded),
        "cases": blinded,
        "armProvenanceIncluded": False,
        "privateCustodyRequired": True,
        "realReviewerAuthenticated": False,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
    }


def validate_packet(packet):
    require(isinstance(packet, dict) and set(packet) ==
            {"schema", "version", "mode", "caseCount", "cases",
             "armProvenanceIncluded", "privateCustodyRequired",
             "realReviewerAuthenticated", "mayExecuteTest",
             "mayCreateWorkOrder", "mayReleaseEquipment"},
            "blind packet has unknown fields")
    require(packet["schema"] == SCHEMA_PREFIX + "-reviewer-packet.v1"
            and packet["version"] == "1.0.0"
            and packet["mode"] == "private_masked_pair_review_not_attestation"
            and packet["armProvenanceIncluded"] is False
            and packet["privateCustodyRequired"] is True
            and all(packet[k] is False for k in
                    ("realReviewerAuthenticated", "mayExecuteTest",
                     "mayCreateWorkOrder", "mayReleaseEquipment")),
            "blind packet exposes provenance or real authority")
    require(isinstance(packet["cases"], list)
            and len(packet["cases"]) == packet["caseCount"]
            and 2 <= packet["caseCount"] <= 50,
            "blind packet case count invalid")
    # Packet content is authenticated against the original source, candidate
    # source and private assignment using check_custody() before scoring.
    ids = set()
    for item in packet["cases"]:
        require(isinstance(item, dict) and set(item) ==
                {"caseId", "domain", "symptom", "observations", "evidenceNature",
                 "documentaryStatus", "oemEffectivityVerified",
                 "mayReleaseEquipment", "questionA", "questionB"},
                "reviewer case shape invalid")
        ident = item["caseId"]
        require(isinstance(ident, str) and re.fullmatch(r"HLD-[0-9]{3}", ident)
                and ident not in ids, "invalid case identifiers")
        ids.add(ident)
        require(isinstance(item["questionA"], str)
                and isinstance(item["questionB"], str)
                and item["questionA"] != item["questionB"]
                and 25 <= len(item["questionA"].strip()) <= 500
                and 25 <= len(item["questionB"].strip()) <= 500
                and item["oemEffectivityVerified"] is False
                and item["mayReleaseEquipment"] is False,
                "packet contains changed questions or claims OEM authorization")
    return packet


def _commitment(payload, key):
    require(isinstance(key, bytes) and len(key) >= 32,
            "custodian secret missing or too short")
    return hmac.new(key, digest(payload).encode("ascii"), hashlib.sha256).hexdigest()


def make_custody(source, candidates, packet, assignment, quality, key):
    validate_packet(packet)
    payload = {
        "packetDigest": digest(packet),
        "sourceDigest": digest(source),
        "candidateDigest": digest(candidates),
        "qualityReceiptDigest": digest(quality),
        "armMapping": [
            {"caseId": row["caseId"], "baselineArm": choice}
            for row, choice in zip(source["cases"], assignment)
        ],
    }
    return {
        "schema": SCHEMA_PREFIX + "-private-arm-lock.v1",
        "version": "1.0.0",
        "mode": "private_custodian_mapping_not_signature",
        **payload,
        "commitmentHmacSha256": _commitment(payload, key),
        "humanIdentityAuthenticated": False,
        "externalExpertReviewCompleted": False,
        "mayExecuteTest": False,
    }


def quality_preflight(source, metadata, policy):
    parent = reviewer_packet(source)
    return quality_receipt(source, metadata, policy, parent)


def prepare(source, candidates, metadata, policy, key, assignment=None):
    validate_candidates(candidates, source)
    quality = quality_preflight(source, metadata, policy)
    choices = balanced_assignment(len(source["cases"])) if assignment is None else assignment
    packet = build_packet(source, candidates, choices)
    lock = make_custody(source, candidates, packet, choices, quality, key)
    check_custody(source, candidates, metadata, policy, packet, lock, quality, key)
    return packet, lock, quality


def check_custody(source, candidates, metadata, policy, packet, lock, quality, key):
    verify_quality_receipt(
        quality, source, metadata, policy, reviewer_packet(source)
    )
    validate_candidates(candidates, source)
    validate_packet(packet)
    require(isinstance(lock, dict) and set(lock) ==
            {"schema", "version", "mode", "packetDigest", "sourceDigest",
             "candidateDigest", "qualityReceiptDigest", "armMapping",
             "commitmentHmacSha256", "humanIdentityAuthenticated",
             "externalExpertReviewCompleted", "mayExecuteTest"},
            "private mapping tampered")
    require(lock["schema"] == SCHEMA_PREFIX + "-private-arm-lock.v1"
            and lock["version"] == "1.0.0"
            and lock["mode"] == "private_custodian_mapping_not_signature"
            and all(lock[x] is False for x in
                    ("humanIdentityAuthenticated", "externalExpertReviewCompleted",
                     "mayExecuteTest")),
            "custody claims unauthorized trust")
    mapping = lock["armMapping"]
    require(isinstance(mapping, list)
            and len(mapping) == len(source["cases"])
            and all(isinstance(m, dict)
                    and set(m) == {"caseId", "baselineArm"}
                    and m["caseId"] == s["caseId"]
                    and m["baselineArm"] in ("A", "B")
                    for m, s in zip(mapping, source["cases"])),
            "private assignment does not match case IDs")
    assignment = [m["baselineArm"] for m in mapping]
    require(abs(assignment.count("A") - assignment.count("B")) <= 1,
            "allocation not balanced")
    require(packet == build_packet(source, candidates, assignment),
            "masked questions differ from frozen private candidate source")
    payload = {name: lock[name] for name in (
        "packetDigest", "sourceDigest", "candidateDigest",
        "qualityReceiptDigest", "armMapping"
    )}
    require(payload["packetDigest"] == digest(packet)
            and payload["sourceDigest"] == digest(source)
            and payload["candidateDigest"] == digest(candidates)
            and payload["qualityReceiptDigest"] == digest(quality),
            "content digest mismatches")
    mac = lock["commitmentHmacSha256"]
    require(isinstance(mac, str) and re.fullmatch(r"[a-f0-9]{64}", mac)
            and hmac.compare_digest(mac, _commitment(payload, key)),
            "private mapping HMAC rejected")
    return assignment


def validate_submission(packet, submission):
    validate_packet(packet)
    require(isinstance(submission, dict) and set(submission) ==
            {"schema", "version", "packetDigest", "reviewerAlias",
             "realHumanIdentityAuthenticated", "independentExpertReviewVerified",
             "assessments"}, "review submission fields changed")
    require(submission["schema"] == SCHEMA_PREFIX + "-review-submission.v1"
            and submission["version"] == "1.0.0"
            and submission["packetDigest"] == digest(packet)
            and isinstance(submission["reviewerAlias"], str)
            and REVIEWER.fullmatch(submission["reviewerAlias"])
            and submission["realHumanIdentityAuthenticated"] is False
            and submission["independentExpertReviewVerified"] is False,
            "reviewer identity or external expert status fabricated")
    answers = submission["assessments"]
    require(isinstance(answers, list)
            and len(answers) == packet["caseCount"]
            and [a.get("caseId") for a in answers] ==
            [case["caseId"] for case in packet["cases"]],
            "missing, duplicated or unordered blinded assessments")
    for answer in answers:
        require(isinstance(answer, dict) and set(answer) ==
                {"caseId", "preference", "reason", "riskFlags",
                 "physicalTestAuthorized", "technicalApprovalVerified"},
                "assessment shape changed")
        flags = answer["riskFlags"]
        require(answer["preference"] in CHOICES
                and isinstance(answer["reason"], str)
                and 12 <= len(answer["reason"].strip()) <= 1200
                and isinstance(flags, list)
                and len(flags) == len(set(flags))
                and all(isinstance(f, str) and f in ALLOWED_FLAGS for f in flags)
                and answer["physicalTestAuthorized"] is False
                and answer["technicalApprovalVerified"] is False,
                "invalid judgment or accidental authorization")
    return answers


def freeze_receipt(packet, submission):
    validate_submission(packet, submission)
    return {
        "schema": SCHEMA_PREFIX + "-review-receipt.v1",
        "version": "1.0.0",
        "packetDigest": digest(packet),
        "submissionDigest": digest(submission),
        "reviewerAlias": submission["reviewerAlias"],
        "frozen": True,
        "authenticatesHumanIdentity": False,
    }


def validate_receipt(packet, submission, receipt):
    require(receipt == freeze_receipt(packet, submission),
            "submission differs from frozen receipt or receipt forged")
    return True


def score(source, candidates, metadata, policy, packet, lock,
          quality, key, submissions, receipts):
    assignment = check_custody(
        source, candidates, metadata, policy, packet, lock, quality, key
    )
    require(len(submissions) == len(receipts) == 2,
            "two frozen separately attributed submissions required")
    for sub, rec in zip(submissions, receipts):
        validate_receipt(packet, sub, rec)
    require(submissions[0]["reviewerAlias"] != submissions[1]["reviewerAlias"],
            "duplicated reviewer alias, cannot represent two submissions")
    results = []
    for index, case in enumerate(packet["cases"]):
        a, b = (sub["assessments"][index] for sub in submissions)
        agreement = a["preference"] == b["preference"]
        flags = sorted(set(a["riskFlags"] + b["riskFlags"]))
        if flags:
            state = "risk_flagged_requires_adjudication"
        elif not agreement:
            state = "disagreement_requires_adjudication"
        elif a["preference"] == "abstain":
            state = "both_abstain"
        elif a["preference"] == "tie":
            state = "tied"
        else:
            state = ("baseline_preferred" if
                     a["preference"] == assignment[index]
                     else "experimental_preferred")
        results.append({
            "caseId": case["caseId"], "domain": case["domain"],
            "samePreference": agreement,
            "riskFlags": flags,
            "state": state,
            "requiresIndependentAdjudication":
                state in ("risk_flagged_requires_adjudication",
                          "disagreement_requires_adjudication"),
        })
    states = {
        state: sum(row["state"] == state for row in results)
        for state in ("baseline_preferred", "experimental_preferred", "tied",
                      "both_abstain", "risk_flagged_requires_adjudication",
                      "disagreement_requires_adjudication")
    }
    return {
        "schema": SCHEMA_PREFIX + "-private-review-report.v1",
        "version": "1.0.0",
        "mode": "offline_synthetic_or_unattested_private_preference_review",
        "packetDigest": digest(packet),
        "lockDigest": digest(lock),
        "qualityReceiptDigest": digest(quality),
        "frozenSubmissions": 2,
        "caseCount": len(results),
        "rawReviewerAgreement": {
            "same": sum(r["samePreference"] for r in results),
            "total": len(results),
        },
        "preferenceCounts": states,
        "cases": results,
        "reviewerIdentitiesAuthenticated": False,
        "independentMechanicalReviewVerified": False,
        "mechanicalDiagnosticAccuracyMeasured": False,
        "fieldDiagnosticImprovementEstablished": False,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayModifyECM": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_unattested_blinded_preferences_not_mechanical_validity",
    }


def verify_report(report, *args):
    require(report == score(*args),
            "review report changed or computed from different frozen inputs")
    return True


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="Private paired blind reviewer rehearsal; no external attestation"
    )
    sub = parser.add_subparsers(dest="stage", required=True)
    prepare_parser = sub.add_parser("prepare")
    for flag in ("source", "candidates", "quality-metadata", "quality-policy",
                 "key", "packet", "lock", "quality-receipt"):
        prepare_parser.add_argument("--" + flag, type=Path, required=True)
    freeze_parser = sub.add_parser("freeze")
    for flag in ("packet", "submission", "receipt"):
        freeze_parser.add_argument("--" + flag, type=Path, required=True)
    score_parser = sub.add_parser("score")
    for flag in ("source", "candidates", "quality-metadata", "quality-policy",
                 "key", "packet", "lock", "quality-receipt", "submission-a",
                 "submission-b", "receipt-a", "receipt-b", "output"):
        score_parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args(argv)

    if args.stage == "prepare":
        source = read_private(args.source)
        candidates = read_private(args.candidates)
        metadata = read_private(args.quality_metadata)
        policy = read_private(args.quality_policy)
        key = read_private_key(args.key)
        packet, lock, quality = prepare(
            source, candidates, metadata, policy, key
        )
        # All outputs must remain outside the checkout; the existing C30
        # atomic-create helper refuses overwrite of previous frozen files.
        save_private(args.packet, packet)
        save_private(args.lock, lock)
        save_private(args.quality_receipt, quality)
    elif args.stage == "freeze":
        packet = read_private(args.packet)
        submission = read_private(args.submission)
        save_private(args.receipt, freeze_receipt(packet, submission))
    else:
        report = score(
            read_private(args.source), read_private(args.candidates),
            read_private(args.quality_metadata),
            read_private(args.quality_policy),
            read_private(args.packet), read_private(args.lock),
            read_private(args.quality_receipt), read_private_key(args.key),
            (read_private(args.submission_a), read_private(args.submission_b)),
            (read_private(args.receipt_a), read_private(args.receipt_b)),
        )
        save_private(args.output, report)


if __name__ == "__main__":
    cli()
