"""Arquitetura simulada de revisão restrita — SEM autenticação ou assinatura real.

Ferramenta de modelagem de ameaças: todos os SIM-ACTOR são PERSONAS FICTÍCIAS.
Hashes permitem detectar mudanças contra a entrada original (se preservada);
não constituem cadeia de custódia assinada, relógio confiável nem prova jurídica.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import ImportRejected, load_lock, require, validate_snapshot
from evidence.ledger import sha
from governance.review import PACKET_PATH, validate_packet
from methods.library import CATALOG_PATH, SOURCES_PATH, validate_catalog, validate_sources
from methods.discrimination import MATRIX_PATH, validate_matrix


ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = ROOT / "examples/restricted-review-threat-fixture.v1.json"
ACTOR_ROLES = {"author", "reviewer", "adjudicator"}
ACTIONS = {"submit", "support_general", "insufficient", "challenge",
           "adjudicate_needs_evidence"}
STATES = {"draft", "under_review", "disputed", "needs_evidence",
          "qualified_general_claim_simulation"}
FIXTURE_KEYS = {"schema", "version", "nature", "tenantId",
                "externalVerifierConfigured", "externalTrustAnchor",
                "externalTimeAuthorityConfigured", "mayPersistRealData",
                "mayIssueTechnicalApproval", "actors", "cases"}
ACTOR_KEYS = {"actorId", "role", "discipline", "identityNature",
              "identityVerified", "credentialVerified", "independenceVerified",
              "conflictOfInterestDeclared", "revoked", "authority"}
CASE_KEYS = {"caseId", "claimId", "revision", "events"}
EVENT_KEYS = {"eventId", "claimId", "actorId", "action", "nonce",
              "targetRevision", "sourceRefs", "explanation", "signature"}


def exact(obj: object, keys: set[str], label: str) -> dict:
    require(isinstance(obj, dict) and set(obj) == keys,
            f"{label}: missing/unauthorized field")
    return obj


def sim_text(s: object, prefix: str) -> bool:
    return (isinstance(s, str)
            and re.fullmatch(re.escape(prefix) + r"[A-Z0-9-]+", s) is not None)


def validate_fixture(fixture: object, review_packet: dict,
                     methods: dict, sources: dict, families: dict) -> dict:
    f = exact(fixture, FIXTURE_KEYS, "restricted fixture")
    require(f["schema"] == "maintenance-superinteligence.restricted-review-threat-fixture.v1"
            and f["version"] == "1.0.0"
            and f["nature"] == "offline_untrusted_synthetic_no_authentication"
            and sim_text(f["tenantId"], "SIM-TENANT-")
            and f["externalVerifierConfigured"] is False
            and f["externalTrustAnchor"] is None
            and f["externalTimeAuthorityConfigured"] is False
            and f["mayPersistRealData"] is False
            and f["mayIssueTechnicalApproval"] is False,
            "fixture: external authentication, trust anchor or approval claimed")
    require(isinstance(f["actors"], list) and len(f["actors"]) >= 7
            and isinstance(f["cases"], list) and len(f["cases"]) == 3,
            "fixture: three training cases and role roster required")
    reviewed = validate_packet(review_packet, methods, sources, families)
    claims = reviewed["claims"]
    actors = {}
    for a in f["actors"]:
        exact(a, ACTOR_KEYS, "actor")
        actor_id = a["actorId"]
        require(sim_text(actor_id, "SIM-ACTOR-") and actor_id not in actors,
                "actor: missing/duplicate synthetic identifier")
        require(a["role"] in ACTOR_ROLES
                and a["discipline"] in {"oil", "hydraulics", "mechanics",
                                        "vibration", "electronics"}
                and a["identityNature"] == "fictional_unverified_identity"
                and a["identityVerified"] is False
                and a["credentialVerified"] is False
                and a["independenceVerified"] is False
                and a["conflictOfInterestDeclared"] is False
                and a["revoked"] is False
                and a["authority"] == "simulation_only",
                "actor: forged identity, declared conflict, revocation or authority")
        actors[actor_id] = a

    case_ids, nonces, event_ids, claim_ids = set(), set(), set(), set()
    for case in f["cases"]:
        exact(case, CASE_KEYS, "review case")
        cid = case["caseId"]
        claim_id = case["claimId"]
        require(sim_text(cid, "SIM-RESTRICTED-") and cid not in case_ids
                and claim_id in claims and claim_id not in claim_ids,
                "case: unknown claim or duplicate case/claim")
        case_ids.add(cid)
        claim_ids.add(claim_id)
        require(type(case["revision"]) is int and case["revision"] == 1,
                "case: expected immutable claim revision 1")
        require(isinstance(case["events"], list) and 1 <= len(case["events"]) <= 4,
                "case: invalid event count")
        claim = claims[claim_id]
        for e in case["events"]:
            exact(e, EVENT_KEYS, "event")
            eid, nonce = e["eventId"], e["nonce"]
            require(sim_text(eid, "SIM-EVENT-")
                    and sim_text(nonce, "SIM-NONCE-")
                    and eid not in event_ids and nonce not in nonces,
                    "event: duplicate/replayed nonce or event identifier")
            event_ids.add(eid)
            nonces.add(nonce)
            require(e["claimId"] == claim_id
                    and e["actorId"] in actors
                    and e["action"] in ACTIONS
                    and type(e["targetRevision"]) is int
                    and e["targetRevision"] == case["revision"]
                    and e["signature"] is None,
                    "event: wrong claim/revision, unauthorized action or forged signature")
            a = actors[e["actorId"]]
            required_role = ("author" if e["action"] == "submit" else
                             "adjudicator" if e["action"] == "adjudicate_needs_evidence"
                             else "reviewer")
            require(a["role"] == required_role and
                    a["discipline"] == claim["domain"],
                    "event: role/discipline not authorized for claim")
            require(isinstance(e["explanation"], str)
                    and 12 <= len(e["explanation"].strip()) <= 1200,
                    "event: explanation insufficient")
            require(isinstance(e["sourceRefs"], list)
                    and e["sourceRefs"] and len(e["sourceRefs"]) == len(set(e["sourceRefs"]))
                    and set(e["sourceRefs"]).issubset(claim["citationIds"]),
                    "event: missing/foreign/recursive citation")
    return {"actors": actors, "claims": claims,
            "caseCount": len(case_ids), "eventCount": len(event_ids)}


def derive_case(case: dict, actors: dict, claim: dict) -> dict:
    """Recompute sequence without trusting user-supplied signatures or statuses."""
    state = "draft"
    author_id = None
    reviewer_ids = []
    positions = []
    adjudicator_id = None
    chain = []
    previous = "0" * 64
    claim_digest = sha(claim)
    for index, event in enumerate(case["events"], 1):
        actor = actors[event["actorId"]]
        action = event["action"]
        if action == "submit":
            require(index == 1 and state == "draft" and actor["role"] == "author",
                    "transition: must submit a draft exactly once")
            author_id = event["actorId"]
            state = "under_review"
        elif action in {"support_general", "insufficient", "challenge"}:
            require(state in {"under_review", "disputed"}
                    and len(reviewer_ids) < 2
                    and event["actorId"] != author_id
                    and event["actorId"] not in reviewer_ids
                    and actor["role"] == "reviewer",
                    "transition: duplicate reviewer or invalid review state")
            reviewer_ids.append(event["actorId"])
            positions.append(action)
            state = ("disputed" if "challenge" in positions else
                     "qualified_general_claim_simulation"
                     if positions == ["support_general", "support_general"] else
                     "needs_evidence"
                     if len(positions) == 2 else "under_review")
        elif action == "adjudicate_needs_evidence":
            require(state == "disputed" and len(reviewer_ids) == 2
                    and actor["role"] == "adjudicator"
                    and event["actorId"] not in reviewer_ids
                    and event["actorId"] != author_id
                    and adjudicator_id is None,
                    "transition: adjudication requires two disputed reviews and a third role")
            adjudicator_id = event["actorId"]
            state = "needs_evidence"
        else:
            raise ImportRejected("transition: unknown action")
        payload = {
            "sequence": index,
            "event": event,
            "actorRole": actor["role"],
            "claimRevision": case["revision"],
            "claimSha256": claim_digest,
            "previousSha256": previous,
            "stateAfter": state,
            "timestampTrust": "none_synthetic",
            "signatureVerified": False,
        }
        event_digest = sha(payload)
        chain.append({**payload, "eventSha256": event_digest})
        previous = event_digest
    return {
        "caseId": case["caseId"], "claimId": case["claimId"],
        "revision": case["revision"], "claimSha256": claim_digest,
        "derivedState": state, "claimedRealIdentity": False,
        "fictionalAuthorId": author_id,
        "fictionalReviewerIds": reviewer_ids,
        "fictionalAdjudicatorId": adjudicator_id,
        "reviewPositions": positions,
        "hasUnresolvedDispute": "challenge" in positions,
        "auditEvents": chain, "auditHeadSha256": previous,
        "externalAnchorVerified": False,
        "validReviewSignatures": 0,
        "mayPublishGeneralClaimAsReal": False,
        "mayVerifyOemSeries": False,
        "mayAuthorizeMaintenance": False,
    }


def execute_fixture(fixture: dict, review_packet: dict, methods: dict,
                    sources: dict, families: dict, snapshot: dict) -> dict:
    # Authenticated snapshot here is public FMEA *content* only.
    require({r["id"] for r in snapshot["records"] if r["family"] == "comando_final"}
            == {"FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004"},
            "fmea: wrong pinned FMEA chain")
    checked = validate_fixture(fixture, review_packet, methods, sources, families)
    cases = [derive_case(case, checked["actors"], checked["claims"][case["claimId"]])
             for case in fixture["cases"]]
    return {
        "schema": "maintenance-superinteligence.restricted-review-simulation-report.v1",
        "mode": "OFFLINE_SIMULATION_NOT_AUTHENTICATION",
        "fixtureSha256": sha(fixture),
        "reviewPacketSha256": sha(review_packet),
        "fmeaSha256VerifiedAtInput": True,
        "caseCount": len(cases),
        "eventCount": sum(len(c["auditEvents"]) for c in cases),
        "derivedStates": dict(sorted(Counter(c["derivedState"] for c in cases).items())),
        "cases": cases,
        "untrustedIdentityCount": len(checked["actors"]),
        "authenticatedIdentityCount": 0,
        "verifiedReviewSignatureCount": 0,
        "trustedClockConfigured": False,
        "externalAuditAnchorConfigured": False,
        "reviewAuthenticity": "not_achieved",
        "qualifiedClaimsForRealWorldUse": 0,
        "oemEffectivityVerified": False,
        "canWriteSap": False,
        "canModifyEcm": False,
        "canApproveMaintenance": False,
        "canReleaseEquipment": False,
        "notes": [
            "No private vault, IdP, KMS, signing service, or immutable audit store exists here.",
            "Hashes detect local changes only while original fixture and source packet remain trusted.",
            "Role and independence checks use fictional IDs; they are NOT authentication.",
            "Two matching fictional opinions are not evidence of true technical validity.",
            "All operational and OEM approvals remain prohibited.",
        ],
    }


def verify_report(report: object, fixture: dict, review_packet: dict,
                  methods: dict, sources: dict, families: dict, snapshot: dict) -> dict:
    """Fail closed: compare complete report to reconstruction from original input.

    A locally recomputed hash chain does not help if the original fixture is
    independently preserved. If an attacker controls BOTH, external trust is
    still impossible; that limitation is explicit in documentation.
    """
    require(report == execute_fixture(fixture, review_packet, methods, sources,
                                      families, snapshot),
            "audit: altered, replayed or locally re-sealed report does not match source")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--packet", type=Path, default=PACKET_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        snapshot = validate_snapshot(args.snapshot.read_bytes(), load_lock())
        registry = validate_sources(json.loads(SOURCES_PATH.read_text(encoding="utf-8")))
        methods = validate_catalog(json.loads(CATALOG_PATH.read_text(encoding="utf-8")),
                                   registry, snapshot)
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        families = validate_matrix(matrix, methods, snapshot)
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        review_packet = json.loads(args.packet.read_text(encoding="utf-8"))
        result = execute_fixture(fixture, review_packet, methods, registry,
                                 families, snapshot)
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected, ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"result": "rejected_fail_closed",
                          "reason": str(exc), "canApproveMaintenance": False},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
