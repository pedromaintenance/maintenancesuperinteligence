"""Qualificação de afirmações — workflow de PARECERES FICTÍCIOS em domínio público.

Simula dois revisores independentes POR ID, sem provar identidade, competência,
independência, autoria, assinatura ou revisão de engenheiro real.
Um 'general_reference_supported' aqui é estado DE EXERCÍCIO, não homologação.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import ImportRejected, load_lock, require, validate_snapshot
from evidence.ledger import sha
from methods.library import (CATALOG_PATH, SOURCES_PATH,
                             validate_catalog, validate_sources)
from methods.discrimination import MATRIX_PATH, validate_matrix


ROOT = Path(__file__).resolve().parent.parent
PACKET_PATH = ROOT / "governance/review-packet.v1.json"
PACKET_KEYS = {"schema", "version", "purpose", "sourceRegistryVersion",
               "methodCatalogVersion", "matrixVersion", "reviewers", "citations",
               "claims", "assessments", "approvalEvidence", "humanApprovalAuthority",
               "mayChangeEquipmentStatus", "operationalValidation"}
CLAIM_KEYS = {"claimId", "domain", "methodId", "pairId", "statement",
              "counterexample", "interpretationLimit", "citationIds",
              "evidenceNature", "applicabilityEvidence", "rootCauseConfirmed",
              "mayAuthorizeMaintenance"}
CITATION_KEYS = {"citationId", "sourceId", "methodId", "pairId",
                 "interpretationRole", "quotedPassage", "sourceApplicability",
                 "licenseCopyIncluded"}
REVIEWER_KEYS = {"reviewerId", "discipline", "identityNature", "credentialsVerified",
                 "independenceVerified", "organization"}
ASSESSMENT_KEYS = {"reviewId", "claimId", "reviewerId", "round", "assessment",
                   "rationale", "citationIds", "nature", "conflictOfInterestDeclared",
                   "competenceDeclaredDomain", "signature"}
STATES = ("draft", "needs_evidence", "under_review", "disputed",
          "general_reference_supported", "oem_series_verified")
EVALUATIONS = {"support_general", "insufficient", "challenge"}


def fields(value: object, keys: set[str], where: str) -> dict:
    require(isinstance(value, dict) and set(value) == keys,
            f"{where}: missing or unauthorized fields")
    return value


def description(value: object) -> bool:
    return isinstance(value, str) and 12 <= len(value.strip()) <= 1300


def references(value: object, label: str) -> list[str]:
    require(isinstance(value, list) and len(value) >= 1
            and all(isinstance(x, str) and bool(x) for x in value)
            and len(value) == len(set(value)), f"{label}: missing/duplicate link")
    return value


def _applicability(value: object) -> None:
    gate = fields(value, {"manufacturer", "model", "serialOrArrangement",
                          "publicationId", "revision", "verificationStatus",
                          "operationallyApproved"}, "applicability")
    require(all(gate[k] is None for k in ("manufacturer", "model",
                "serialOrArrangement", "publicationId", "revision"))
            and gate["verificationStatus"] == "not_verified"
            and gate["operationallyApproved"] is False,
            "applicability: no model, series, publication or OEM approval verified")


def validate_packet(packet: object, methods: dict,
                    sources: dict, families: dict) -> dict:
    p = fields(packet, PACKET_KEYS, "packet")
    require(p["schema"] == "maintenance-superinteligence.technical-review-packet.v1"
            and p["version"] == "1.0.0"
            and p["purpose"] == "simulation_only_independent_review_workflow"
            and p["sourceRegistryVersion"] == "1.0.0"
            and p["methodCatalogVersion"] == "1.0.0"
            and p["matrixVersion"] == "1.0.0"
            and p["approvalEvidence"] == []
            and p["humanApprovalAuthority"] is False
            and p["mayChangeEquipmentStatus"] is False
            and p["operationalValidation"] is False,
            "packet: public workflow cannot claim operational authority")
    require(isinstance(p["claims"], list) and len(p["claims"]) == 8,
            "packet: eight source-backed editorial claims required")
    require(isinstance(p["citations"], list) and len(p["citations"]) >= 8,
            "packet: reference metadata missing")
    require(isinstance(p["reviewers"], list) and len(p["reviewers"]) >= 2
            and isinstance(p["assessments"], list),
            "packet: review records missing")

    reviewers = {}
    for r in p["reviewers"]:
        fields(r, REVIEWER_KEYS, "reviewer")
        rid = r["reviewerId"]
        require(isinstance(rid, str)
                and re.fullmatch(r"SIM-REVIEWER-[A-Z-]+", rid)
                and rid not in reviewers,
                "reviewer: invalid, duplicated or non-synthetic identity")
        require(r["discipline"] in {"oil", "hydraulics", "mechanics",
                                    "vibration", "electronics"}
                and r["identityNature"] == "fictional_persona_no_real_signature"
                and r["credentialsVerified"] is False
                and r["independenceVerified"] is False
                and r["organization"] is None,
                "reviewer: cannot self-certify an independent expert")
        reviewers[rid] = r

    all_pairs = {pair["pairId"]: (fid, pair)
                 for fid, family in families.items() for pair in family["pairs"]}
    citations = {}
    for c in p["citations"]:
        fields(c, CITATION_KEYS, "citation")
        cid = c["citationId"]
        require(isinstance(cid, str) and re.fullmatch(r"CIT-[A-Z0-9-]+", cid)
                and cid not in citations, "citation: malformed/duplicate ID")
        require(c["sourceId"] in sources and c["methodId"] in methods
                and c["pairId"] in all_pairs,
                "citation: missing or circular source/method/pair")
        pair = all_pairs[c["pairId"]][1]
        method = methods[c["methodId"]]
        require(c["sourceId"] in method["sourceIds"]
                and c["methodId"] in pair["methodIds"],
                "citation: source not supported by referenced method/pair")
        require(c["interpretationRole"] == "public_general_context_only"
                and c["quotedPassage"] is None
                and c["sourceApplicability"] == "generic_not_oem_series"
                and c["licenseCopyIncluded"] is False,
                "citation: cannot assert quoted OEM applicability or licensed source")
        citations[cid] = c

    claims = {}
    citation_uses = Counter()
    for claim in p["claims"]:
        fields(claim, CLAIM_KEYS, "claim")
        cid = claim["claimId"]
        require(isinstance(cid, str) and re.fullmatch(r"CLM-[A-Z-]+", cid)
                and cid not in claims, "claim: malformed or duplicate ID")
        require(claim["domain"] in {"oil", "hydraulics", "mechanics",
                                    "vibration", "electronics"}
                and claim["methodId"] in methods
                and methods[claim["methodId"]]["domain"] == claim["domain"]
                and claim["pairId"] in all_pairs
                and claim["methodId"] in all_pairs[claim["pairId"]][1]["methodIds"],
                "claim: invalid cross-domain method or hypothesis pair")
        require(description(claim["statement"])
                and description(claim["counterexample"])
                and description(claim["interpretationLimit"])
                and not re.search(r"\d", claim["statement"]),
                "claim: unsupported numerical OEM statement or missing limits")
        links = references(claim["citationIds"], "claim citationIds")
        require(all(cid2 in citations
                    and citations[cid2]["methodId"] == claim["methodId"]
                    and citations[cid2]["pairId"] == claim["pairId"]
                    for cid2 in links),
                "claim: orphan/cross-claim citation link")
        for link in links:
            citation_uses[link] += 1
        require(claim["evidenceNature"] == "author_editorial_claim_not_field_fact"
                and claim["rootCauseConfirmed"] is False
                and claim["mayAuthorizeMaintenance"] is False,
                "claim: synthetic hypothesis cannot confirm failure or authorize work")
        _applicability(claim["applicabilityEvidence"])
        claims[cid] = claim
    require(set(citations) == set(citation_uses)
            and all(count == 1 for count in citation_uses.values()),
            "citation: orphaned or multiply claimed source link")

    assessments_by_claim = defaultdict(list)
    review_ids = set()
    for a in p["assessments"]:
        fields(a, ASSESSMENT_KEYS, "assessment")
        rev_id = a["reviewId"]
        require(isinstance(rev_id, str)
                and re.fullmatch(r"REV-[A-Z0-9-]+", rev_id)
                and rev_id not in review_ids, "assessment: duplicate/invalid review ID")
        review_ids.add(rev_id)
        cid = a["claimId"]
        require(cid in claims and a["reviewerId"] in reviewers,
                "assessment: orphan claim or reviewer")
        require(type(a["round"]) is int and a["round"] in (1, 2),
                "assessment: unrecognized review round")
        require(a["assessment"] in EVALUATIONS
                and description(a["rationale"])
                and a["nature"] == "synthetic_training_review_not_signed"
                and a["conflictOfInterestDeclared"] is False
                and a["competenceDeclaredDomain"] == claims[cid]["domain"]
                and reviewers[a["reviewerId"]]["discipline"] == claims[cid]["domain"]
                and a["signature"] is None,
                "assessment: fake signed review, declared conflict or missing discipline")
        evidence = references(a["citationIds"], "assessment citationIds")
        require(set(evidence).issubset(claims[cid]["citationIds"]),
                "assessment: reviewer referenced a foreign/recursive citation")
        assessments_by_claim[cid].append(a)

    decisions = []
    disagreements = []
    for cid, claim in claims.items():
        reviews = assessments_by_claim[cid]
        round_ids = Counter(r["round"] for r in reviews)
        require(len(reviews) <= 4
                and round_ids[1] <= 2 and round_ids[2] <= 2,
                "review: no more than two fictional persons per round")
        participants = [r["reviewerId"] for r in reviews]
        require(len(participants) == len(set(participants)),
                "review: identical fictional reviewer cannot count twice or re-adjudicate")
        if 2 in round_ids:
            require(round_ids[1] == 2 and round_ids[2] == 2,
                    "review: second round requires two fresh independent personas")
            r1 = [r["assessment"] for r in reviews if r["round"] == 1]
            require(r1 != ["support_general", "support_general"]
                    and set(r1) != {"support_general"},
                    "review: cannot re-adjudicate already unanimously supported claim")
        latest_round = max((r["round"] for r in reviews), default=0)
        latest = [r for r in reviews if r["round"] == latest_round]
        evaluations = [r["assessment"] for r in latest]
        if not evaluations:
            status = "draft"
        elif len(evaluations) < 2:
            status = "under_review"
        elif "challenge" in evaluations:
            status = "disputed"
        elif evaluations.count("support_general") == 2:
            status = "general_reference_supported"
        else:
            status = "needs_evidence"
        require(status in STATES and status != "oem_series_verified",
                "review: OEM series cannot be approved through public simulator")
        if status == "disputed":
            disagreements.append({
                "claimId": cid, "round": latest_round,
                "reviewIds": [r["reviewId"] for r in latest],
                "positions": [r["assessment"] for r in latest],
                "counterexample": claim["counterexample"],
                "resolution": "not_adjudicated",
                "requiresNewSourcesOrIndependentReview": True,
            })
        decisions.append({
            "claimId": cid, "derivedStatus": status,
            "reviewRound": latest_round,
            "reviewIds": [r["reviewId"] for r in latest],
            "reviewCount": len(reviews),
            "reviewersInLatestRound": len(latest),
            "reviewerIdentityVerified": False,
            "reviewerIndependenceVerified": False,
            "requiresRealTechnicalReview": True,
            "technicalQualification": "synthetic_workflow_only",
            "basis": "Two distinct fictional persona IDs (not independently authenticated)."
                     if len(latest) == 2 else "Insufficient fictional reviewer records.",
            "oemSeriesVerified": False,
            "approvedForOperationalUse": False,
            "rootCauseConfirmed": False,
        })
    return {"claims": claims, "citations": citations, "reviewers": reviewers,
            "assessmentsByClaim": assessments_by_claim,
            "decisions": decisions, "disagreements": disagreements}


def evaluate_packet(packet: dict, methods: dict, sources: dict,
                    families: dict, snapshot: dict) -> dict:
    require(validate_matrix_snapshot_consistency(families, snapshot),
            "review: frozen knowledge chain not verified")
    data = validate_packet(packet, methods, sources, families)
    decision_histogram = Counter(x["derivedStatus"] for x in data["decisions"])
    return {
        "schema": "maintenance-superinteligence.technical-review-report.v1",
        "reviewMode": "synthetic_only",
        "packetSha256": sha(packet),
        "claimsEvaluated": len(data["claims"]),
        "citationsLinked": len(data["citations"]),
        "fictionalReviewers": len(data["reviewers"]),
        "fictionalAssessments": sum(len(v) for v in data["assessmentsByClaim"].values()),
        "statusCounts": {s: decision_histogram[s] for s in STATES},
        "decisions": data["decisions"],
        "disagreements": data["disagreements"],
        "oemApprovalGranted": False,
        "hasAuthenticatedExpertReviews": False,
        "discriminationScientificallyValidated": False,
        "humanReviewRequired": True,
        "mayAuthorizeWork": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
        "notes": [
            "Toda revisão é fictícia; IDs diferentes não comprovam independência humana.",
            "O estado general_reference_supported é calculado somente dentro de simulação.",
            "Citações apontam para referências gerais e não validam o conteúdo por série.",
            "oem_series_verified é reservado a ambiente autorizado e rejeitado aqui.",
        ],
    }


def validate_matrix_snapshot_consistency(families: dict, snapshot: dict) -> bool:
    # validate_matrix already verifies IDs and confirmedRootCause from the snapshot.
    fd_ids = {r["id"] for r in snapshot["records"] if r["family"] == "comando_final"}
    return fd_ids == {"FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004"} \
        and all(r["confirmedRootCause"] is False
                for r in snapshot["records"] if r["id"] in fd_ids)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--packet", type=Path, default=PACKET_PATH)
    p.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    p.add_argument("--sources", type=Path, default=SOURCES_PATH)
    p.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        snapshot = validate_snapshot(args.snapshot.read_bytes(), load_lock())
        registry = validate_sources(json.loads(args.sources.read_text(encoding="utf-8")))
        methods = validate_catalog(json.loads(args.catalog.read_text(encoding="utf-8")),
                                   registry, snapshot)
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
        families = validate_matrix(matrix, methods, snapshot)
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        result = evaluate_packet(packet, methods, registry, families, snapshot)
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output)
        return 0
    except (ImportRejected, OSError, ValueError, TypeError, KeyError) as err:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(err),
                          "mayAuthorizeWork": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
