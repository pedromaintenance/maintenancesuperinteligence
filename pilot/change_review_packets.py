"""Cycle 25: offline synthetic review packets. Never an approval engine."""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
from hashlib import sha256

AREAS = ("IT", "InformationSecurity", "Engineering", "Legal", "MaintenanceManagement")
PROOFS = ("identity", "independent_competence", "oem_effectivity",
          "safety_review", "legal_basis", "signed_decision", "audit_chain")
OBJECTIONS = (
    ("Engineering", "oem_effectivity_unverified", "OEM applicability and revision not evidenced"),
    ("InformationSecurity", "identity_or_signature_unverified", "Identity, signatures and audit trust absent"),
    ("MaintenanceManagement", "segregation_or_owner_change", "Functional ownership must not be silently reassigned"),
    ("IT", "stale_graph_version", "Graph revisions and hashes must match current baseline"),
    ("Legal", "legal_basis_unverified", "Licensing, purpose and retention not approved"),
)
DENIED = ("mayWriteSap", "mayModifyEcm", "mayCreateWorkOrder",
          "mayOrderParts", "mayReleaseEquipment", "mayAuthorizePrivatePilot")

class ReviewRejected(ValueError):
    pass

def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def digest(x):
    return sha256(canonical(x).encode("utf-8")).hexdigest()

def require(ok, reason):
    if not ok:
        raise ReviewRejected(reason)

def build_packets(report):
    require(isinstance(report, dict) and report.get("schema") ==
            "maintenance-superinteligence.graph-change-review-report.v1",
            "unrecognized cycle 24 report")
    require(report.get("decision") == "no_go" and report.get("allProposalsVetoed") is True
            and report.get("realChangesCommitted") == 0
            and report.get("verifiedHumanReviewCount") == 0,
            "source claims approval")
    require(report.get("baselineControlCount") == 13
            and report.get("baselineEdgeCount") == 17
            and report.get("sourceOracleScenarioCount") == 100
            and report.get("proposalCount") == 10,
            "canonical graph / oracle mismatch")
    authority = report.get("operationalAuthority")
    require(isinstance(authority, dict) and all(authority.get(k) is False for k in DENIED),
            "source claims operational authority")
    proposals = report.get("proposals")
    require(isinstance(proposals, list) and len(proposals) == 10
            and len({p.get("proposalId") for p in proposals}) == 10,
            "proposal corpus invalid")
    packets = []
    for item in proposals:
        ident = item["proposalId"]
        require(isinstance(ident, str) and ident.startswith("SIM-GDIFF-"),
                "unexpected proposal identifier")
        adjud = item.get("changeAdjudication", {})
        req = item.get("reviewerAssignmentRequirement", {})
        coverage = item.get("coverageRegression", {})
        require(adjud.get("decision") == "veto_no_merge"
                and adjud.get("proposalAppliedToMain") is False
                and adjud.get("oldGraphModified") is False,
                "proposal accepted or graph edited")
        require(all(adjud.get(k) is False for k in DENIED[:5]),
                "proposal claims machine authority")
        require(req.get("areas") == list(AREAS)
                and req.get("signedChangeAcceptance") is False
                and req.get("individualReviewersAuthenticated") is False
                and req.get("independentTechnicalApprovalVerified") is False
                and req.get("oemEffectivityVerified") is False,
                "review approval or reviewer identity fabricated")
        require(coverage.get("referenceScenarioCount") == 100
                and coverage.get("realOutcomesMeasured") is False
                and item.get("syntheticProposal") is True,
                "false regression or empirical claim")
        require(item.get("graphNodeCount") == 13 and item.get("canonicalEdgeCount") == 17,
                "graph baseline altered")
        objections = [{"area": area, "code": code, "finding": finding,
                       "status": "synthetic_unresolved_not_a_real_reviewer"}
                      for area, code, finding in OBJECTIONS]
        packets.append({
            "proposalId": ident,
            "sourceProposalSha256": digest(item),
            "graphRevisionSha256": report["canonicalDagSha256"],
            "sourceReportSha256": digest(report),
            "changeType": item["changeType"],
            "impactClassification": item["impactClassification"],
            "pairChanges": item["reachabilityImpact"]["changedPairCount"],
            "affectedRegressionScenarios": len(coverage["affectedScenarios"]),
            "documentaryEvidenceGaps": [
                {"proof": proof, "verified": False, "receipt": None}
                for proof in PROOFS
            ],
            "objections": objections,
            "adjudication": "veto_no_merge",
            "reopenTriggers": ["graph_revision_changed", "evidence_revoked",
                               "reviewer_conflict", "owner_changed",
                               "oem_revision_changed"],
            "humanReviewsPerformed": 0,
            "realSignatures": 0,
            "noOperationalAuthority": {k: False for k in DENIED},
        })
    return {
        "schema": "maintenance-superinteligence.graph-change-review-packets.v1",
        "mode": "synthetic_offline_no_go",
        "sourceReportSha256": digest(report),
        "graphRevisionSha256": report["canonicalDagSha256"],
        "packetCount": 10,
        "packets": packets,
        "independentReviewActual": False,
        "sourceAuthenticityProven": False,
        "decision": "no_go",
        "noOperationalAuthority": {k: False for k in DENIED},
    }

def verify_packets(packets, source):
    require(packets == build_packets(source),
            "packets changed, stale, forged, or unauthorized")
    return True

def html_report(packets):
    require(packets.get("decision") == "no_go"
            and packets.get("packetCount") == 10
            and packets.get("independentReviewActual") is False
            and all(p.get("adjudication") == "veto_no_merge" for p in packets["packets"]),
            "unsafe HTML report")
    sections = []
    for p in packets["packets"]:
        sections.append("<section><h2>" + escape(p["proposalId"]) + "</h2><p>"
                        + escape(p["impactClassification"]) + " | altered pairs: "
                        + str(p["pairChanges"]) + " | affected scenarios: "
                        + str(p["affectedRegressionScenarios"]) +
                        "</p><p>7 required proofs absent. 5 synthetic objections. "
                        "No reviewer authenticated, no approval.</p></section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'" 
            '"><title>Cycle 25 - NO GO</title><style>body{font:16px system-ui;'
            'max-width:960px;margin:2em auto;padding:1em}section{border:1px solid #bbb;'
            'padding:1em;margin:1em 0}</style></head><body><h1>Cycle 25: NO GO</h1>'
            '<p>Entirely synthetic documentary packets. Not OEM evidence, real '
            'signatures, field validation or approval.</p>' + ''.join(sections)
            + '</body></html>')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle24", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    source = json.loads(args.cycle24.read_text(encoding="utf-8"))
    packets = build_packets(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(html_report(packets), encoding="utf-8")

if __name__ == "__main__":
    main()
