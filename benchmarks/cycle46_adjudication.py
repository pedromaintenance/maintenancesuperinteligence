"""Cycle 46 — lexical masking QA and *unattested* adjudication handoff.

Read-only audit of frozen Cycle 45 paired-question inputs and outputs.
All cases, submissions, arm mappings, HMAC keys and reports remain PRIVATE,
outside the checkout. Never identifies a real reviewer or certifies diagnosis.

Lexical rules and length ratios are HEURISTICS, not proof of blind assessment.
An adjudication draft is a queue of unresolved questions, not an engineering
acceptance, independent professional opinion, signature or operational order.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

from benchmarks.cycle45_blinded_pairwise import (
    check_custody, score, validate_receipt, validate_submission,
)
from benchmarks.heldout_study import read_private, read_private_key, save_private
from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "governance/cycle46-neutrality-policy.v1.json"
PREFIX = "maintenance-superinteligence.cycle46"
CUES = (
    "baseline", "experimental", "algoritmo", "inteligencia artificial",
    "gerado por ia", "modelo automatizado", "modelo anterior",
    "modelo proposto", "metodo desenvolvido",
)
RISK_CODES = (
    "question_origin_cue",
    "question_length_imbalance",
)
REVIEW_CODES = (
    "possible_blinding_leak", "reviewer_risk_flag", "reviewer_disagreement",
    "reviewer_uncertainty",
)
DRAFT_ACTIONS = (
    "request_reblinding", "request_independent_safety_review",
    "request_independent_disagreement_review",
    "request_additional_documentary_evidence",
)
FALSE_FIELDS = (
    "independentAdjudicatorAuthenticated", "actualIndependentReviewCompleted",
    "mechanicalDiagnosticAccuracyEstablished", "mayExecuteTest",
    "mayCreateWorkOrder", "mayWriteSAP", "mayModifyECM",
    "mayReleaseEquipment",
)
ALIAS = re.compile(r"^REV-[A-Z0-9]{2,16}$")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) ==
            {"schema", "version", "nature", "lengthRatioThreshold",
             "originDisclosureCues", "screenedWarnings",
             "requiresReviewReasons", "independentNeutralityVerified",
             "independentAdjudicationCompleted", "operationallyApproved"},
            "Cycle46 policy shape changed")
    require(policy["schema"] == PREFIX + "-neutrality-policy.v1"
            and policy["version"] == "1.0.0"
            and policy["nature"] ==
                "heuristic_language_screen_not_blindness_validation"
            and type(policy["lengthRatioThreshold"]) is float
            and policy["lengthRatioThreshold"] == 2.5
            and policy["originDisclosureCues"] == list(CUES)
            and policy["screenedWarnings"] == list(RISK_CODES)
            and policy["requiresReviewReasons"] == list(REVIEW_CODES)
            and policy["independentNeutralityVerified"] is False
            and policy["independentAdjudicationCompleted"] is False
            and policy["operationallyApproved"] is False,
            "Cycle46 screening policy weakened or real approval claimed")
    return True


def canonical_text(text):
    require(isinstance(text, str), "question must be text")
    chars = unicodedata.normalize("NFKD", text).casefold()
    return "".join(ch for ch in chars if not unicodedata.combining(ch))


def screening_warnings(case, policy):
    """Only return codes; never echo possibly sensitive question text."""
    validate_policy(policy)
    a, b = canonical_text(case["questionA"]), canonical_text(case["questionB"])
    tokens_a = re.findall(r"\w+", a, flags=re.UNICODE)
    tokens_b = re.findall(r"\w+", b, flags=re.UNICODE)
    require(tokens_a and tokens_b, "empty question cannot be screened")
    origin = any(
        re.search(r"(?<!\w)" + re.escape(cue) + r"(?!\w)", text)
        for text in (a, b) for cue in CUES
    )
    counts = (len(tokens_a), len(tokens_b))
    ratio = max(counts) / min(counts)
    warnings = []
    if origin:
        warnings.append("question_origin_cue")
    if ratio >= policy["lengthRatioThreshold"]:
        warnings.append("question_length_imbalance")
    return warnings


def prepare_handoff(source, candidates, metadata, quality_policy, packet, lock,
                    quality_receipt, key, submissions, receipts,
                    neutrality_policy):
    """Fail closed and reconstruct Cycle45 custody before inspecting the data."""
    validate_policy(neutrality_policy)
    check_custody(source, candidates, metadata, quality_policy, packet,
                  lock, quality_receipt, key)
    parent = score(source, candidates, metadata, quality_policy, packet,
                   lock, quality_receipt, key, submissions, receipts)
    require(parent["decision"] ==
            "no_go_unattested_blinded_preferences_not_mechanical_validity"
            and parent["independentMechanicalReviewVerified"] is False
            and parent["fieldDiagnosticImprovementEstablished"] is False,
            "unsafe Cycle45 review result supplied")
    for sub, receipt in zip(submissions, receipts):
        validate_submission(packet, sub)
        validate_receipt(packet, sub, receipt)
    require(len(submissions) == len(receipts) == 2
            and submissions[0]["reviewerAlias"] !=
                submissions[1]["reviewerAlias"],
            "two distinct synthetic reviewer aliases required")
    rows = []
    for card, parent_case in zip(packet["cases"], parent["cases"]):
        require(card["caseId"] == parent_case["caseId"],
                "case order mismatches frozen review")
        warnings = screening_warnings(card, neutrality_policy)
        reasons = []
        if warnings:
            reasons.append("possible_blinding_leak")
        if parent_case["riskFlags"]:
            reasons.append("reviewer_risk_flag")
        if parent_case["state"] == "disagreement_requires_adjudication":
            reasons.append("reviewer_disagreement")
        if parent_case["state"] in ("tied", "both_abstain"):
            reasons.append("reviewer_uncertainty")
        must_review = bool(reasons)
        rows.append({
            "caseId": card["caseId"], "domain": card["domain"],
            "heuristicMaskWarnings": warnings,
            "reviewReasons": reasons,
            "requiresIndependentAdjudication": must_review,
            "nextState": ("pending_external_adjudication" if must_review else
                          "pending_external_validation_no_adjudication"),
            "automaticallyResolved": False,
            "operationallyApproved": False,
        })
    return {
        "schema": PREFIX + "-handoff.v1",
        "version": "1.0.0",
        "mode": "private_unattested_review_triage_not_external_adjudication",
        "packetDigest": digest(packet),
        "lockDigest": digest(lock),
        "sourceReviewReportDigest": digest(parent),
        "qualityReceiptDigest": digest(quality_receipt),
        "neutralityPolicyDigest": digest(neutrality_policy),
        "submissionDigests": [digest(sub) for sub in submissions],
        "receiptDigests": [digest(rec) for rec in receipts],
        "caseCount": len(rows),
        "flaggedForAdjudicationCount":
            sum(x["requiresIndependentAdjudication"] for x in rows),
        "caseHandoffs": rows,
        "neutralityScreenPassedAsExpertProof": False,
        "automatedAdjudicationsCompleted": 0,
        "reviewerIdentitiesAuthenticated": False,
        "independentMechanicalReviewCompleted": False,
        "mechanicalDiagnosticAccuracyMeasured": False,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayWriteSAP": False,
        "mayModifyECM": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_adjudication_and_blinding_unverified",
    }


def validate_handoff(handoff, source, candidates, metadata, quality_policy,
                     packet, lock, quality_receipt, key, submissions, receipts,
                     neutrality_policy):
    require(handoff == prepare_handoff(
        source, candidates, metadata, quality_policy, packet, lock,
        quality_receipt, key, submissions, receipts, neutrality_policy
    ), "handoff changed or no longer matches frozen evidence")
    return True


def validate_draft(draft, handoff, submissions):
    """Accept only an UNATTESTED to-do list, never a technical conclusion."""
    require(isinstance(draft, dict) and set(draft) ==
            {"schema", "version", "handoffDigest", "adjudicatorAlias",
             "independentIdentityVerified", "externalEngineeringOpinionReceived",
             "entries", "technicalDecisionApproved", "mayReleaseEquipment"},
            "adjudication draft keys changed")
    ident = draft["adjudicatorAlias"]
    reviewer_aliases = [s["reviewerAlias"] for s in submissions]
    require(draft["schema"] == PREFIX + "-adjudication-draft.v1"
            and draft["version"] == "1.0.0"
            and draft["handoffDigest"] == digest(handoff)
            and isinstance(ident, str) and ALIAS.fullmatch(ident)
            and ident not in reviewer_aliases
            and draft["independentIdentityVerified"] is False
            and draft["externalEngineeringOpinionReceived"] is False
            and draft["technicalDecisionApproved"] is False
            and draft["mayReleaseEquipment"] is False,
            "adjudication cannot certify people, accept repairs or self-review")
    required = [r["caseId"] for r in handoff["caseHandoffs"]
                if r["requiresIndependentAdjudication"]]
    entries = draft["entries"]
    require(isinstance(entries, list)
            and [r.get("caseId") for r in entries
                 if isinstance(r, dict)] == required
            and len(entries) == len(required),
            "adjudication tasks missing, extra, duplicated or reordered")
    for item in entries:
        require(isinstance(item, dict)
                and set(item) == {"caseId", "proposedNextAction", "rationale",
                                  "signedByQualifiedEngineer",
                                  "contradictionResolved"},
                "adjudication item changed")
        require(item["proposedNextAction"] in DRAFT_ACTIONS
                and isinstance(item["rationale"], str)
                and 20 <= len(item["rationale"].strip()) <= 1200
                and item["signedByQualifiedEngineer"] is False
                and item["contradictionResolved"] is False,
                "adjudication cannot invent a resolved case or technical signoff")
    return True


def freeze_draft(draft, handoff, submissions):
    validate_draft(draft, handoff, submissions)
    return {
        "schema": PREFIX + "-draft-receipt.v1",
        "version": "1.0.0",
        "handoffDigest": digest(handoff),
        "draftDigest": digest(draft),
        "adjudicatorAlias": draft["adjudicatorAlias"],
        "frozen": True,
        "authenticatesHumanIdentity": False,
        "externalTechnicalAdjudicationCompleted": False,
        "decision": "pending_real_independent_review_no_go",
    }


def validate_draft_receipt(receipt, draft, handoff, submissions):
    require(receipt == freeze_draft(draft, handoff, submissions),
            "draft receipt was forged or source changed")
    return True


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="Cycle46 private masking/adjudication research, NO GO")
    cmds = parser.add_subparsers(dest="stage", required=True)
    a = cmds.add_parser("handoff")
    for k in ("source", "candidates", "quality-metadata", "quality-policy",
              "packet", "lock", "quality-receipt", "key",
              "submission-a", "submission-b", "receipt-a", "receipt-b",
              "output"):
        a.add_argument("--" + k, type=Path, required=True)
    a.add_argument("--neutrality-policy", type=Path, default=POLICY)
    f = cmds.add_parser("freeze-draft")
    for k in ("handoff", "draft", "submission-a", "submission-b", "receipt"):
        f.add_argument("--" + k, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.stage == "handoff":
        result = prepare_handoff(
            read_private(args.source), read_private(args.candidates),
            read_private(args.quality_metadata), read_private(args.quality_policy),
            read_private(args.packet), read_private(args.lock),
            read_private(args.quality_receipt), read_private_key(args.key),
            (read_private(args.submission_a), read_private(args.submission_b)),
            (read_private(args.receipt_a), read_private(args.receipt_b)),
            load(args.neutrality_policy),
        )
        save_private(args.output, result)
    else:
        handoff = read_private(args.handoff)
        draft = read_private(args.draft)
        submissions = (read_private(args.submission_a),
                       read_private(args.submission_b))
        save_private(args.receipt, freeze_draft(draft, handoff, submissions))


if __name__ == "__main__":
    cli()
