"""Cycle 65: offline synthetic conflict-review ledger, never human adjudication.

Events are invented role-play entries. SHA-256 links them to the exact input
snapshot but does NOT authenticate actors, timestamps, or a remote custodian.
No conflict is ever resolved, no reference approved, and no operational GO.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from benchmarks.cycle64_source_governance import validate as validate_c64

SCHEMA = "maintenance-superinteligence.synthetic-conflict-review-ledger.v1"
ID = re.compile(r"^SIM-[A-Z0-9]{3,20}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
EVENT_TYPES = {"assessment", "challenge", "adjudication_proposal"}
ROLES = {"reviewer_a", "reviewer_b", "arbiter"}
POSITIONS = {"prefer_declared_claim", "insufficient_evidence"}
EVIDENCE_NEEDS = {"source_authenticity", "revision_scope",
                  "configuration_effectivity", "independent_technical_review"}
DENIED = ("humanIdentityVerified", "independenceVerified",
          "humanReviewCompleted", "technicalConflictResolved",
          "oemEffectivityVerified", "referenceApproved", "mayExecuteTest",
          "mayWriteSap", "mayModifyEcm", "mayReleaseEquipment")
EVENT_FIELDS = ("eventId", "referenceId", "eventType", "actorRole", "actorAlias",
                "position", "selectedClaimToken", "targetEventId",
                "requiredEvidence", "previousDigest", "digest")


def ensure(ok, message):
    if not ok:
        raise ValueError(message)


def exact(value, keys, label):
    ensure(type(value) is dict and set(value) == set(keys),
           label + ": missing or unexpected fields")


def token(value):
    return type(value) is str and ID.fullmatch(value) is not None


def sha256_json(value):
    """Deterministic content fingerprint, NOT a trusted signature."""
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def digest_event(event):
    """Hash a complete event EXCEPT its digest field, including previousDigest."""
    return sha256_json({key: value for key, value in event.items()
                        if key != "digest"})


def validate(payload):
    exact(payload, ("schema", "sourceCase", "events", "claims"), "study")
    ensure(payload["schema"] == SCHEMA, "unknown review ledger schema")
    upstream = validate_c64(payload["sourceCase"])
    conflicted = {r["referenceId"] for r in upstream["references"]
                  if r["unresolvedActiveClaimConflict"]}
    active_tokens = {}
    for s in payload["sourceCase"]["sources"]:
        if s["status"] == "active":
            active_tokens.setdefault(s["referenceId"], set()).add(s["claimToken"])
    events = payload["events"]
    ensure(type(events) is list and len(events) <= 60,
           "expected a partial synthetic ledger of at most 60 events")
    exact(payload["claims"], DENIED, "claims")
    ensure(all(payload["claims"][key] is False for key in DENIED),
           "synthetic review cannot grant identity, expert or operational status")
    current_digest = sha256_json(payload["sourceCase"])
    anchor_digest = current_digest
    seen_events = {}
    actor_roles = {}
    assessments = {}
    challenges = {}
    proposals = {}
    for entry in events:
        exact(entry, EVENT_FIELDS, "ledger event")
        event_id = entry["eventId"]
        ref = entry["referenceId"]
        role = entry["actorRole"]
        alias = entry["actorAlias"]
        event_type = entry["eventType"]
        ensure(token(event_id) and event_id not in seen_events,
               "invalid or duplicated event identifier")
        ensure(type(ref) is str and ref in conflicted,
               "events are allowed only for unresolved source conflicts")
        ensure(event_type in EVENT_TYPES and role in ROLES and token(alias),
               "invalid event type or synthetic role")
        ensure(alias not in actor_roles or actor_roles[alias] == role,
               "one synthetic alias cannot impersonate multiple review roles")
        actor_roles[alias] = role
        ensure(entry["position"] in POSITIONS
               and entry["requiredEvidence"] in EVIDENCE_NEEDS,
               "position and outstanding evidence requirement mandatory")
        if entry["position"] == "prefer_declared_claim":
            ensure(type(entry["selectedClaimToken"]) is str
                   and entry["selectedClaimToken"] in active_tokens.get(ref, set()),
                   "declared preference must name an existing active claim")
        else:
            ensure(entry["selectedClaimToken"] is None,
                   "abstention must not select a claim")
        ensure(type(entry["previousDigest"]) is str
               and HASH.fullmatch(entry["previousDigest"])
               and entry["previousDigest"] == current_digest,
               "event chain is discontinuous or rebased")
        ensure(type(entry["digest"]) is str and HASH.fullmatch(entry["digest"])
               and entry["digest"] == digest_event(entry),
               "event content fingerprint mismatch")
        if event_type == "assessment":
            ensure(role in ("reviewer_a", "reviewer_b") and
                   entry["targetEventId"] is None,
                   "assessment requires simulated reviewer role and no target")
            key = (ref, role)
            ensure(key not in assessments, "one assessment per simulated reviewer and reference")
            assessments[key] = entry
        elif event_type == "challenge":
            ensure(role in ("reviewer_a", "reviewer_b")
                   and entry["position"] == "insufficient_evidence",
                   "challenges only question an assessment")
            own = assessments.get((ref, role))
            ensure(own is not None and own["actorAlias"] == alias,
                   "challenger must already have authored an assessment")
            target_id = entry["targetEventId"]
            ensure(type(target_id) is str and target_id in seen_events
                   and seen_events[target_id]["referenceId"] == ref
                   and seen_events[target_id]["eventType"] == "assessment"
                   and seen_events[target_id]["actorRole"] != role,
                   "challenge must target another reviewer's earlier assessment")
            ensure((ref, role, target_id) not in challenges,
                   "duplicated challenge of the same assessment")
            challenges[(ref, role, target_id)] = entry
        else:
            ensure(role == "arbiter" and entry["targetEventId"] is None,
                   "proposal requires synthetic arbiter and no event target")
            a, b = assessments.get((ref, "reviewer_a")), assessments.get((ref, "reviewer_b"))
            ensure(a is not None and b is not None
                   and a["actorAlias"] != b["actorAlias"]
                   and alias not in (a["actorAlias"], b["actorAlias"]),
                   "proposal needs two distinct prior synthetic reviewer aliases and a third arbiter")
            ensure(ref not in proposals, "only one synthetic adjudication proposal per reference")
            proposals[ref] = entry
        seen_events[event_id] = entry
        current_digest = entry["digest"]
    tracks = []
    for ref in sorted(conflicted):
        count = sum((ref, role) in assessments for role in ("reviewer_a", "reviewer_b"))
        disputed = sum(key[0] == ref for key in challenges)
        if ref in proposals:
            state = "synthetic_proposal_recorded_conflict_unresolved"
        elif disputed:
            state = "synthetic_challenge_recorded_conflict_unresolved"
        elif count == 2:
            state = "two_synthetic_assessments_conflict_unresolved"
        elif count == 1:
            state = "one_synthetic_assessment_conflict_unresolved"
        else:
            state = "not_reviewed"
        tracks.append({
            "referenceId": ref, "syntheticAssessments": count,
            "syntheticChallenges": disputed,
            "syntheticProposals": int(ref in proposals),
            "workflowState": state, "conflictResolved": False,
            "realHumanReviewCompleted": False,
        })
    return {
        "schema": "maintenance-superinteligence.synthetic-conflict-review-result.v1",
        "caseId": upstream["caseId"],
        "unresolvedReferenceCount": len(conflicted),
        "syntheticEventCount": len(events),
        "sourceSnapshotDigest": anchor_digest,
        "chainHeadDigest": current_digest,
        "tracks": tracks,
        "realHumanReviewCompleted": False,
        "independentExpertReviewCompleted": False,
        "technicalConflictResolved": False,
        "oemEffectivityVerified": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as out:
            out.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
