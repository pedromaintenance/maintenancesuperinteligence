"""Cycle 47: adversarial *preflight* for masked paired-review evidence.

This is a conservative offline syntactic audit, NOT proof of blindness,
identity, independence, OEM applicability or diagnostic ability.

All case content and outputs remain outside the public repository. Public CI
uses synthetic temporary fixtures only. No tests, SAP/ECM actions or machine
releases are authorized.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

from benchmarks.cycle46_adjudication import (
    POLICY as C46_POLICY, load as load_json, validate_handoff,
)
from benchmarks.heldout_study import read_private, read_private_key, save_private
from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "governance/cycle47-adversarial-policy.v1.json"
PREFIX = "maintenance-superinteligence.cycle47"
MASK_FLAGS = (
    "hidden_unicode_control",
    "mixed_script_confusable",
    "obfuscated_method_origin_cue",
    "instructional_contamination",
    "near_duplicate_question_pair",
    "candidate_identifier_leak",
)
PROVENANCE_FLAGS = (
    "synthetic_evidence_only",
    "documentary_source_not_verified",
    "oem_effectivity_not_verified",
)
ORIGIN_CUES = (
    "baseline", "experimental", "modelo anterior", "modelo proposto",
    "inteligencia artificial", "gerado por ia", "gpt", "chatgpt", "llm",
    "algoritmo", "openai",
)
INSTRUCTION_CUES = (
    "ignore instrucoes anteriores", "ignore as instrucoes",
    "ignore previous instructions", "responda apenas",
    "system prompt", "developer message",
)
C47_NO_GO = "no_go_masking_and_provenance_not_independently_validated"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) == {
        "schema", "version", "nature", "tokenJaccardThreshold",
        "methodOriginCues", "instructionalCues", "maskWarnings",
        "documentaryWarnings", "expertMaskingVerified",
        "externalSourceProvenanceVerified", "independentEngineeringApproval",
        "operationallyApproved",
    }, "Cycle47 policy has missing or extra fields")
    require(
        policy["schema"] == PREFIX + "-adversarial-policy.v1"
        and policy["version"] == "1.0.0"
        and policy["nature"] == "conservative_syntactic_research_not_expert_validation"
        and type(policy["tokenJaccardThreshold"]) is float
        and policy["tokenJaccardThreshold"] == 0.9
        and policy["methodOriginCues"] == list(ORIGIN_CUES)
        and policy["instructionalCues"] == list(INSTRUCTION_CUES)
        and policy["maskWarnings"] == list(MASK_FLAGS)
        and policy["documentaryWarnings"] == list(PROVENANCE_FLAGS)
        and all(policy[k] is False for k in (
            "expertMaskingVerified", "externalSourceProvenanceVerified",
            "independentEngineeringApproval", "operationallyApproved",
        )), "Cycle47 source or authority falsely promoted")
    return True


def normalize(text):
    require(isinstance(text, str), "question must be a string")
    source = unicodedata.normalize("NFKD", text).casefold()
    return "".join(ch for ch in source if not unicodedata.combining(ch))


def compressed(text):
    return re.sub(r"[^a-z0-9]", "", normalize(text))


def words(text):
    return frozenset(re.findall(r"[a-z0-9]+", normalize(text)))


def character_scripts(text):
    names = [unicodedata.name(ch, "") for ch in text if ch.isalpha()]
    return {
        family for family in ("LATIN", "CYRILLIC", "GREEK")
        if any(family in name for name in names)
    }


def pair_masking_warnings(case, candidate, policy):
    """Return *codes only*; no potentially private text in the output."""
    validate_policy(policy)
    require(isinstance(case, dict) and
            all(isinstance(case.get(x), str) for x in
                ("questionA", "questionB")), "missing masked pair")
    require(isinstance(candidate, dict) and set(candidate) ==
            {"caseId", "baseline", "experimental"}, "candidate source invalid")
    qa, qb = case["questionA"], case["questionB"]
    texts = (qa, qb)
    flags = []
    if any(unicodedata.category(ch) in ("Cf", "Cc") for t in texts for ch in t):
        flags.append("hidden_unicode_control")
    if any(len(character_scripts(t)) >= 2 and
           ("CYRILLIC" in character_scripts(t) or
            "GREEK" in character_scripts(t)) for t in texts):
        flags.append("mixed_script_confusable")
    if any(compressed(cue) in compressed(text)
           for cue in ORIGIN_CUES for text in texts):
        flags.append("obfuscated_method_origin_cue")
    if any(compressed(cue) in compressed(text)
           for cue in INSTRUCTION_CUES for text in texts):
        flags.append("instructional_contamination")
    tokens = words(qa) | words(qb)
    overlap = len(words(qa) & words(qb)) / len(tokens) if tokens else 0
    if overlap >= policy["tokenJaccardThreshold"]:
        flags.append("near_duplicate_question_pair")
    identifiers = (
        candidate["baseline"].get("questionId", ""),
        candidate["experimental"].get("questionId", ""),
    )
    if any(str(ident).casefold() in text.casefold()
           for ident in identifiers for text in texts if ident):
        flags.append("candidate_identifier_leak")
    return flags


def documentary_warnings(case, policy):
    validate_policy(policy)
    flags = []
    if case["evidenceNature"] == "synthetic_demo_only":
        flags.append("synthetic_evidence_only")
    if case["documentaryStatus"] in (
        "unverified", "stale", "revoked", "conflicting"
    ):
        flags.append("documentary_source_not_verified")
    if case["oemEffectivityVerified"] is False:
        flags.append("oem_effectivity_not_verified")
    return flags


def evaluate(source, candidates, metadata, quality_policy, packet, lock,
             quality_receipt, key, submissions, receipts, handoff,
             c46_policy, policy):
    validate_policy(policy)
    # Full reconstruction (C30/C32 -> C45 -> C46), not blind trust in a JSON.
    validate_handoff(
        handoff, source, candidates, metadata, quality_policy,
        packet, lock, quality_receipt, key, submissions, receipts,
        c46_policy,
    )
    require(len(packet["cases"]) == len(candidates["cases"])
            == len(handoff["caseHandoffs"]), "case alignment invalid")
    rows = []
    for item, candidate, previous in zip(
        packet["cases"], candidates["cases"], handoff["caseHandoffs"]
    ):
        require(item["caseId"] == candidate["caseId"] == previous["caseId"],
                "case IDs changed since blinded review")
        mask = pair_masking_warnings(item, candidate, policy)
        provenance = documentary_warnings(item, policy)
        already_needs_adjudication = previous["requiresIndependentAdjudication"]
        if already_needs_adjudication:
            state = "pending_external_adjudication"
        elif provenance:
            state = "blocked_documentary_provenance"
        elif mask:
            state = "pending_external_blinding_review"
        else:
            state = "pending_external_validation_no_go"
        rows.append({
            "caseId": item["caseId"], "domain": item["domain"],
            "newMaskingHeuristicFlags": mask,
            "documentaryProvenanceFlags": provenance,
            "cycle46AlreadyRequiresAdjudication": already_needs_adjudication,
            "nextState": state,
            "requiresExternalReview": True,
            "blindnessVerified": False,
            "independentExpertVerified": False,
            "operationallyApproved": False,
        })
    return {
        "schema": PREFIX + "-readiness-report.v1",
        "version": "1.0.0",
        "nature": "syntactic_adversarial_review_not_external_attestation",
        "packetDigest": digest(packet),
        "cycle46HandoffDigest": digest(handoff),
        "policyDigest": digest(policy),
        "caseCount": len(rows),
        "newMaskingFlagsCount": sum(len(r["newMaskingHeuristicFlags"])
                                    for r in rows),
        "documentaryFlagsCount": sum(len(r["documentaryProvenanceFlags"])
                                     for r in rows),
        "casesBlockedByProvenance": sum(
            bool(r["documentaryProvenanceFlags"]) for r in rows
        ),
        "casesAlreadyNeedingAdjudication": sum(
            r["cycle46AlreadyRequiresAdjudication"] for r in rows
        ),
        "cases": rows,
        "humanMaskingValidationPerformed": False,
        "independentExpertReviewPerformed": False,
        "diagnosticAccuracyEstablished": False,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayWriteSAP": False,
        "mayModifyECM": False,
        "mayReleaseEquipment": False,
        "decision": C47_NO_GO,
    }


def verify_report(report, *args):
    require(report == evaluate(*args),
            "Cycle47 report modified or inputs no longer match custody")
    return True


def cli(argv=None):
    ap = argparse.ArgumentParser(
        description="Private masked-pair adversarial research. Always NO GO."
    )
    for flag in (
        "source", "candidates", "quality-metadata", "quality-policy",
        "packet", "lock", "quality-receipt", "key", "submission-a",
        "submission-b", "receipt-a", "receipt-b", "handoff", "output",
    ):
        ap.add_argument("--" + flag, type=Path, required=True)
    ap.add_argument("--cycle46-policy", type=Path, default=C46_POLICY)
    ap.add_argument("--adversarial-policy", type=Path, default=POLICY)
    args = ap.parse_args(argv)
    result = evaluate(
        read_private(args.source), read_private(args.candidates),
        read_private(args.quality_metadata), read_private(args.quality_policy),
        read_private(args.packet), read_private(args.lock),
        read_private(args.quality_receipt), read_private_key(args.key),
        (read_private(args.submission_a), read_private(args.submission_b)),
        (read_private(args.receipt_a), read_private(args.receipt_b)),
        read_private(args.handoff), load(args.cycle46_policy),
        load(args.adversarial_policy),
    )
    save_private(args.output, result)


if __name__ == "__main__":
    cli()
