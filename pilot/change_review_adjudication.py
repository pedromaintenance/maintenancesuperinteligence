"""Cycle 26: synthetic objection/revocation adjudication. Never approves changes."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from pilot.change_review_packets import (
    AREAS, DENIED, PROOFS, ReviewRejected, digest, require, verify_packets,
)

FIXTURE = Path(__file__).with_name("review-contestations.v1.json")
EVENTS = {
    "stale_graph_revision": "reopen_required",
    "evidence_revoked": "reopen_required",
    "reviewer_conflict": "reopen_required",
    "self_approval": "blocked_untrusted_assertion",
    "forged_signature": "blocked_untrusted_assertion",
    "owner_changed": "reopen_required",
    "oem_revision_changed": "reopen_required",
    "hidden_dissent": "blocked_untrusted_assertion",
    "false_approval": "blocked_untrusted_assertion",
    "safety_evidence_missing": "reopen_required",
}
FIELDS = {
    "scenarioId", "proposalId", "eventType", "proposerAlias",
    "reviewerAlias", "claimedGraphRevision", "evidenceReference",
    "purportedSignature", "purportedApproval", "ownerChanged",
    "oemRevisionChanged", "objectionSuppressed", "perspectives",
}
POSITIONS = {"objection", "counterargument"}
FIXTURE_KEYS = {"schema", "version", "mode", "scenarioCount", "scenarios"}
ALLOWED_EVIDENCE = set(PROOFS) | {None}


def _two_perspectives(positions):
    require(isinstance(positions, list) and len(positions) == 2,
            "two explicit synthetic perspectives required")
    require(all(isinstance(p, dict) and set(p) == {"area", "position"}
                and p["area"] in AREAS and p["position"] in POSITIONS
                for p in positions), "invalid perspective metadata")
    require(len({p["area"] for p in positions}) == 2
            and {p["position"] for p in positions} == POSITIONS,
            "unrepresented disagreement between distinct areas")


def validate_fixture(spec, packets):
    require(isinstance(spec, dict) and set(spec) == FIXTURE_KEYS,
            "unexpected contestation spec fields")
    require(spec["schema"] ==
            "maintenance-superinteligence.review-contestations.v1"
            and spec["version"] == "1.0.0"
            and spec["mode"] == "synthetic_untrusted_events"
            and spec["scenarioCount"] == 10, "unexpected contestation contract")
    require(isinstance(packets, dict) and packets.get("schema") ==
            "maintenance-superinteligence.graph-change-review-packets.v1"
            and packets.get("decision") == "no_go"
            and packets.get("packetCount") == 10
            and packets.get("independentReviewActual") is False
            and packets.get("sourceAuthenticityProven") is False,
            "invalid or operationally promoted source packets")
    require(isinstance(packets.get("noOperationalAuthority"), dict)
            and set(packets["noOperationalAuthority"]) == set(DENIED)
            and all(v is False for v in packets["noOperationalAuthority"].values()),
            "source may act on equipment")
    source_packets = packets.get("packets")
    require(isinstance(source_packets, list) and len(source_packets) == 10,
            "source proposal count mismatch")
    source_ids = {p["proposalId"] for p in source_packets}
    require(source_ids == {f"SIM-GDIFF-{n:02}" for n in range(1, 11)},
            "source proposal IDs changed")
    base_hash = packets.get("graphRevisionSha256")
    require(isinstance(base_hash, str) and bool(base_hash),
            "missing canonical graph digest")
    for p in source_packets:
        require(p.get("adjudication") == "veto_no_merge"
                and p.get("graphRevisionSha256") == base_hash
                and p.get("humanReviewsPerformed") == 0
                and p.get("realSignatures") == 0,
                "source packet falsely reviewed")
        require(isinstance(p.get("noOperationalAuthority"), dict)
                and set(p["noOperationalAuthority"]) == set(DENIED)
                and all(v is False for v in p["noOperationalAuthority"].values()),
                "source packet grants authority")
        gaps = p.get("documentaryEvidenceGaps")
        require(isinstance(gaps, list)
                and {x.get("proof") for x in gaps} == set(PROOFS)
                and len(gaps) == len(PROOFS)
                and all(x.get("verified") is False and x.get("receipt") is None
                        for x in gaps), "unverified proof promoted")
        objections = p.get("objections")
        require(isinstance(objections, list) and len(objections) == 5
                and {o.get("area") for o in objections} == set(AREAS)
                and all(o.get("status") == "synthetic_unresolved_not_a_real_reviewer"
                        for o in objections), "source objection disappeared")
    scenarios = spec.get("scenarios")
    require(isinstance(scenarios, list) and len(scenarios) == 10,
            "expected exactly ten synthetic scenarios")
    require({s.get("scenarioId") for s in scenarios} ==
            {f"SIM-ADJ-{n:02}" for n in range(1, 11)}
            and {s.get("proposalId") for s in scenarios} == source_ids
            and {s.get("eventType") for s in scenarios} == set(EVENTS),
            "changed scenario IDs, proposals, or event coverage")
    for index, s in enumerate(scenarios, start=1):
        require(isinstance(s, dict) and set(s) == FIELDS
                and s["scenarioId"] == f"SIM-ADJ-{index:02}"
                and s["proposalId"] == f"SIM-GDIFF-{index:02}",
                "unknown or reordered scenario fields")
        require(isinstance(s["proposerAlias"], str) and s["proposerAlias"].startswith("SIM-")
                and isinstance(s["reviewerAlias"], str)
                and s["reviewerAlias"].startswith("SIM-"),
                "untrusted personal identity in public fixture")
        require(s["evidenceReference"] in ALLOWED_EVIDENCE
                and s["claimedGraphRevision"] in ("baseline", "SIM-OBSOLETE-REVISION")
                and all(type(s[k]) is bool for k in
                        ("purportedSignature", "purportedApproval",
                         "ownerChanged", "oemRevisionChanged", "objectionSuppressed")),
                "noncanonical event inputs")
        _two_perspectives(s["perspectives"])
        event = s["eventType"]
        require((s["claimedGraphRevision"] == "SIM-OBSOLETE-REVISION") ==
                (event == "stale_graph_revision"), "false revision signal")
        require(s["purportedSignature"] == (event == "forged_signature"),
                "unmodelled signature claim")
        require(s["purportedApproval"] == (event == "false_approval"),
                "unmodelled approval claim")
        require(s["ownerChanged"] == (event == "owner_changed")
                and s["oemRevisionChanged"] == (event == "oem_revision_changed")
                and s["objectionSuppressed"] == (event == "hidden_dissent"),
                "unmodelled control revocation")
        require((s["proposerAlias"] == s["reviewerAlias"]) ==
                (event == "self_approval"), "unmodelled self-approval")
        require((s["evidenceReference"] == "oem_effectivity") ==
                (event in ("evidence_revoked", "oem_revision_changed"))
                and (s["evidenceReference"] == "safety_review") ==
                (event == "safety_evidence_missing"),
                "unmodelled evidence reference")
    return True


def build_report(spec, packets):
    validate_fixture(spec, packets)
    packet_by_id = {p["proposalId"]: p for p in packets["packets"]}
    prior = "0" * 64
    results = []
    audit = []
    for i, s in enumerate(spec["scenarios"], start=1):
        source = packet_by_id[s["proposalId"]]
        event = s["eventType"]
        status = EVENTS[event]
        perspectives = [
            {"area": p["area"], "position": p["position"],
             "status": "fictional_unverified_not_a_signoff"}
            for p in s["perspectives"]
        ]
        reopened = [
            {"proof": proof, "state": "not_verified_recheck_required"}
            for proof in PROOFS
        ]
        result = {
            "scenarioId": s["scenarioId"],
            "proposalId": s["proposalId"],
            "eventType": event,
            "sourceProposalDigest": source["sourceProposalSha256"],
            "sourcePacketDigest": digest(source),
            "canonicalGraphDigest": packets["graphRevisionSha256"],
            "proposedRevisionClaim": s["claimedGraphRevision"],
            "resolution": status,
            "adjudication": "veto_no_merge",
            "objectionsPreserved": perspectives,
            "reopenedDocumentaryGates": reopened,
            "actualIndependentReviews": 0,
            "authenticatedActors": 0,
            "realSignaturesVerified": 0,
            "mayMerge": False,
            "noOperationalAuthority": {k: False for k in DENIED},
        }
        record = {
            "sequence": i,
            "scenarioId": s["scenarioId"],
            "sourceEventDigest": digest(s),
            "sourcePacketDigest": digest(source),
            "resultDigest": digest(result),
            "previousDigest": prior,
        }
        record["entryDigest"] = digest(record)
        prior = record["entryDigest"]
        results.append(result)
        audit.append(record)
    return {
        "schema": "maintenance-superinteligence.review-adjudication-report.v1",
        "version": "1.0.0",
        "mode": "synthetic_no_operational_authority",
        "sourcePacketsDigest": digest(packets),
        "fixtureDigest": digest(spec),
        "canonicalGraphDigest": packets["graphRevisionSha256"],
        "scenarioCount": 10,
        "results": results,
        "auditTrail": audit,
        "auditTailDigest": prior,
        "objectionsPersist": True,
        "realHumanSignoffs": 0,
        "decision": "no_go",
        "noOperationalAuthority": {k: False for k in DENIED},
    }


def verify_report(report, spec, packets):
    require(report == build_report(spec, packets),
            "untrusted report, altered objection, stale digest, or fake signoff")
    return True


def render_html(report):
    require(report.get("decision") == "no_go" and report.get("scenarioCount") == 10
            and report.get("realHumanSignoffs") == 0
            and report.get("objectionsPersist") is True
            and isinstance(report.get("results"), list)
            and len(report["results"]) == 10
            and all(r.get("adjudication") == "veto_no_merge"
                    and r.get("mayMerge") is False for r in report["results"]),
            "refusing unsafe HTML")
    sections = "".join(
        "<section><h2>" + escape(r["scenarioId"]) + "</h2><p>"
        + escape(r["eventType"]) + " — " + escape(r["resolution"])
        + "</p><p>Two distinct synthetic objections preserved; seven documentary "
          "gates not verified. No signatures or maintenance authorization.</p></section>"
        for r in report["results"]
    )
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            'form-action &apos;none&apos;"><title>Cycle 26 — NO GO</title>'
            '<style>body{font:16px system-ui;max-width:940px;margin:2em auto;'
            'padding:1em}section{border:1px solid #aaa;padding:1em;margin:1em 0}</style>'
            '</head><body><h1>Cycle 26 — contestação sintética: NO GO</h1>'
            '<p>Simulações documentais, não revisão humana, prova OEM ou decisão de campo.</p>'
            + sections + '</body></html>\n')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", type=Path, required=True)
    ap.add_argument("--spec", type=Path, default=FIXTURE)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--html", type=Path)
    args = ap.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    packets = json.loads(args.packets.read_text(encoding="utf-8"))
    result = build_report(spec, packets)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(result), encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
