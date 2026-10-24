"""Ciclo 11: gate de prontidão contratual, APENAS com evidência sintética.

Não implementa identidade, sistema de auditoria, qualificação humana, literatura
OEM por série ou alçadas de operação. Toda saída deve permanecer BLOQUEADA.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import ImportRejected, require
from governance.integration_contracts import (ROOT, POLICY_PATH, REQUIRED_PROOFS,
                                               check_policy, digest)

FIXTURE_PATH = ROOT / "governance/deployment-readiness.v1.json"
STATES = ("not_implemented", "planned", "available_unverified",
          "independently_verified", "revoked")
PUBLIC_STATES = set(STATES[:3])
CYCLES = {
    "cycle08": ("governance/review-packet.v1.json",
                "maintenance-superinteligence.technical-review-packet.v1"),
    "cycle09": ("examples/restricted-review-threat-fixture.v1.json",
                "maintenance-superinteligence.restricted-review-threat-fixture.v1"),
    "cycle10-fixture": ("examples/integration-fixture.v1.json",
                         "maintenance-superinteligence.integration-fixture.v1"),
    "cycle10-policy": ("governance/integration-policy.v1.json",
                        "maintenance-superinteligence.integration-policy.v1"),
}
CHANGES = {
    "claim_revision_changed", "oem_publication_revision_changed",
    "equipment_configuration_changed", "identity_revoked",
    "qualification_changed",
}
REQUIRED_CHANGE_IMPACTS = {
    "claim_revision_changed": {"immutable_claim_revision_and_source_manifest",
         "two_independent_reviewers", "verified_audit_timestamp_and_protected_storage",
         "separate_operational_authorization"},
    "oem_publication_revision_changed": {
         "qualified_document_entitlement_and_oem_effectivity",
         "two_independent_reviewers", "separate_operational_authorization"},
    "equipment_configuration_changed": {
         "qualified_document_entitlement_and_oem_effectivity",
         "two_independent_reviewers", "separate_operational_authorization"},
    "identity_revoked": {"unique_human_identity_and_active_role",
         "author_reviewers_adjudicator_separated", "two_independent_reviewers",
         "separate_operational_authorization"},
    "qualification_changed": {"competence_verified_from_corporate_source",
         "two_independent_reviewers", "separate_operational_authorization"},
}
ROOT_FIELDS = {"schema", "version", "mode", "tenant", "controls", "evidences",
               "compatibilityMatrix", "changeImpacts", "acceptanceDecision"}
CONTROL_FIELDS = {"controlId", "ownerRole", "dependsOn", "riskOnMissing",
                  "acceptanceCriterion", "status", "privateSourceRequired",
                  "publicEvidenceAuthoritative", "reviewerApprovalReal", "evidenceId"}
EVIDENCE_FIELDS = {"evidenceId", "controlId", "nature", "reference",
                   "provenanceAuthenticated", "identityVerified", "accessRightVerified",
                   "sourceDigest", "verifiedByIndependentPerson", "containsPrivateData",
                   "containsLicensedMaterial"}
ACCEPTANCE_FIELDS = {"schema", "status", "approverIdentityVerified",
                     "engineeringApproved", "securityApproved", "privacyApproved",
                     "recordsManagementApproved", "oemApprovalVerified", "mayDeploy",
                     "mayImportCorporateData", "mayReleaseEquipment"}


def exact(x: object, names: set[str], where: str) -> dict:
    require(isinstance(x, dict) and set(x) == names,
            f"{where}: missing or unauthorized fields")
    return x


def text(x: object, least: int = 4) -> bool:
    return isinstance(x, str) and least <= len(x.strip()) <= 320


def identifiers(values: object, where: str, *, min_items: int = 0) -> list:
    require(isinstance(values, list) and len(values) >= min_items
            and all(isinstance(v, str) and v.strip() for v in values)
            and len(set(values)) == len(values),
            f"{where}: duplicates, invalid or insufficient references")
    return values


def plan_controls(controls: dict) -> list[str]:
    """Independent, stable topological ordering of the declared dependencies."""
    graph = {key: set(v["dependsOn"]) for key, v in controls.items()}
    require(all(deps <= set(controls) and name not in deps
                for name, deps in graph.items()),
            "control: orphan, cyclic self-edge or foreign prerequisite")
    order = []
    while graph:
        ready = sorted(k for k, deps in graph.items() if not deps)
        require(ready, "control: dependency cycle")
        for name in ready:
            order.append(name)
            del graph[name]
        for deps in graph.values():
            deps.difference_update(ready)
    return order


def check_compatibility(value: object) -> list[dict]:
    matrix = exact(value, {"schema", "entries",
                           "authorisedPrivateMigration"}, "compatibility matrix")
    require(matrix["schema"] == "maintenance-superinteligence.contract-compatibility.v1"
            and matrix["authorisedPrivateMigration"] is False
            and isinstance(matrix["entries"], list)
            and len(matrix["entries"]) == 4,
            "compatibility: unsupported source set or claimed private migration")
    actual = {}
    for row in matrix["entries"]:
        exact(row, {"cycle", "path", "requiredSchema",
                    "requiredVersion", "migrationRequiredIfChanged"}, "compatibility row")
        key = (row["cycle"], row["path"])
        require(key not in actual and row["migrationRequiredIfChanged"] is True
                and row["requiredVersion"] == "1.0.0",
                "compatibility: forged version or duplicate source")
        require(row["path"] in [path for path, _ in CYCLES.values()],
                "compatibility: unsupported path")
        allowed = next((schema for path, schema in CYCLES.values()
                        if path == row["path"]), None)
        require(row["requiredSchema"] == allowed,
                "compatibility: schema drift requires migration")
        file_path = ROOT / row["path"]
        require(file_path.is_file() and file_path.resolve().is_relative_to(ROOT.resolve()),
                "compatibility: referenced public source not found or outside root")
        obj = json.loads(file_path.read_text(encoding="utf-8"))
        require(obj.get("schema") == row["requiredSchema"]
                and obj.get("version") == row["requiredVersion"],
                "compatibility: source schema/version mismatch; manual migration required")
        actual[row["path"]] = {
            "path": row["path"], "cycle": row["cycle"],
            "schema": row["requiredSchema"], "version": row["requiredVersion"],
            "contentSha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            "sourceVerifiedAsPublicFile": True,
            "privateMigrationAuthorised": False,
        }
    require(set(actual) == {path for path, _ in CYCLES.values()},
            "compatibility: missing locked Cycle 08-10 reference")
    return [actual[path] for path, _ in CYCLES.values()]


def validate_readiness(packet: object, policy: dict) -> dict:
    check_policy(policy)
    f = exact(packet, ROOT_FIELDS, "readiness fixture")
    require(f["schema"] == "maintenance-superinteligence.deployment-readiness-fixture.v1"
            and f["version"] == "1.0.0"
            and f["mode"] == "public_synthetic_no_external_attestation"
            and f["tenant"] == "SIM-TENANT-TRAINING",
            "readiness: no corporate tenant or authenticated source accepted")
    require(isinstance(f["controls"], list) and len(f["controls"]) == 10,
            "readiness: exactly ten external proofs required")
    controls = {}
    for c in f["controls"]:
        exact(c, CONTROL_FIELDS, "control")
        cid = c["controlId"]
        require(cid in REQUIRED_PROOFS and cid not in controls,
                "control: unknown or duplicate proof")
        identifiers(c["dependsOn"], "control dependsOn")
        require(text(c["ownerRole"]) and text(c["acceptanceCriterion"], 20)
                and c["riskOnMissing"] in {"critical", "high"}
                and c["status"] in PUBLIC_STATES
                and c["privateSourceRequired"] is True
                and c["publicEvidenceAuthoritative"] is False
                and c["reviewerApprovalReal"] is False
                and re.fullmatch(r"SIM-EVIDENCE-\d{2}", c["evidenceId"]),
                "control: unverified status cannot become approval or real evidence")
        controls[cid] = c
    require(set(controls) == REQUIRED_PROOFS,
            "readiness: lost an externally required proof")
    order = plan_controls(controls)
    require(isinstance(f["evidences"], list)
            and len(f["evidences"]) == len(controls),
            "evidence: one placeholder per control required")
    seen = set()
    for e in f["evidences"]:
        exact(e, EVIDENCE_FIELDS, "evidence")
        cid = e["controlId"]
        require(cid in controls and cid not in seen
                and e["evidenceId"] == controls[cid]["evidenceId"],
                "evidence: orphan, duplicate or cross-control link")
        seen.add(cid)
        require(e["nature"] == "synthetic_placeholder_only"
                and (e["reference"] is None or (
                     isinstance(e["reference"], str)
                     and re.fullmatch(r"SIM-PLAN-\d{2}", e["reference"])))
                and e["sourceDigest"] is None
                and all(e[key] is False for key in
                        ("provenanceAuthenticated", "identityVerified",
                         "accessRightVerified", "verifiedByIndependentPerson",
                         "containsPrivateData", "containsLicensedMaterial")),
                "evidence: public fixture cannot contain or verify private evidence")
    sources = check_compatibility(f["compatibilityMatrix"])
    require(isinstance(f["changeImpacts"], list)
            and len(f["changeImpacts"]) == len(CHANGES),
            "change: mandatory revalidation triggers missing")
    changes = {}
    for impact in f["changeImpacts"]:
        exact(impact, {"eventType", "invalidates", "reopenDecision",
                       "previousApprovalValid", "allowAutomaticReapproval",
                       "changeReference"}, "change impact")
        key = impact["eventType"]
        require(key in CHANGES and key not in changes,
                "change: duplicate/unknown invalidation trigger")
        deps = set(identifiers(impact["invalidates"], "change invalidates", min_items=2))
        require(deps == REQUIRED_CHANGE_IMPACTS[key]
                and impact["reopenDecision"] is True
                and impact["previousApprovalValid"] is False
                and impact["allowAutomaticReapproval"] is False
                and impact["changeReference"]
                    == "SIM-CHANGE-" + key.upper().replace("_", "-"),
                "change: stale approvals cannot survive a revision")
        changes[key] = sorted(deps)
    require(set(changes) == CHANGES, "change: missing invalidation trigger")
    decision = exact(f["acceptanceDecision"], ACCEPTANCE_FIELDS, "acceptance")
    require(decision["schema"] == "maintenance-superinteligence.deployment-acceptance.v1"
            and decision["status"] == "blocked"
            and all(decision[k] is False for k in ACCEPTANCE_FIELDS
                    - {"schema", "status"}),
            "acceptance: public record cannot grant readiness or operational approval")
    return {"controls": controls, "order": order, "sources": sources,
            "changes": changes, "decision": decision}


def evaluate_readiness(packet: dict, policy: dict) -> dict:
    checked = validate_readiness(packet, policy)
    cs = checked["controls"]
    counts = Counter(c["status"] for c in cs.values())
    items = []
    for step, key in enumerate(checked["order"], 1):
        c = cs[key]
        items.append({
            "step": step, "controlId": key, "ownerRole": c["ownerRole"],
            "riskOnMissing": c["riskOnMissing"], "status": c["status"],
            "acceptanceCriterion": c["acceptanceCriterion"],
            "blockedBy": c["dependsOn"],
            "privateEvidenceRequired": True, "publicEvidenceValidForApproval": False,
            "acceptanceVerified": False,
            "statusForPrivateRelease": "blocked_missing_independent_verification",
        })
    return {
        "schema": "maintenance-superinteligence.deployment-readiness-report.v1",
        "mode": "public_synthetic_no_external_attestation",
        "fixtureSha256": digest(packet), "policySha256": digest(policy),
        "controlsTotal": len(cs),
        "controlStatusCounts": {s: counts[s] for s in STATES},
        "independentlyVerifiedControls": 0,
        "publicSyntheticPlaceholders": len(packet["evidences"]),
        "allControlsSatisfied": False,
        "compatibility": checked["sources"],
        "compatibilityConsistentWithPublicFiles": True,
        "privateCompatibilityApproved": False,
        "implementationOrder": items,
        "changeRequalification": [{"trigger": key, "invalidates": checked["changes"][key],
                                   "decision": "reopen_for_independent_review",
                                   "automaticReapproval": False}
                                  for key in sorted(CHANGES)],
        "outstandingPrivateDependencies": sorted(REQUIRED_PROOFS),
        "engineeringApproved": False, "informationSecurityApproved": False,
        "privacyLegalApproved": False, "documentCustodyApproved": False,
        "mayConnectCorporateSystems": False, "mayImportRealEvidence": False,
        "mayApproveOemEffectivity": False, "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False, "acceptance": "blocked_private_deployment",
        "limitations": [
            "Public CI verifies schema lineage and synthetic states only.",
            "No IdP, signatures, reviewers, OEM source, secure audit vault or real data.",
            "Content hashes of public files do not certify private migration.",
            "No synthetic status can authorize deployment, maintenance or operations.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    p.add_argument("--policy", type=Path, default=POLICY_PATH)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        packet = json.loads(args.fixture.read_text(encoding="utf-8"))
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        result = evaluate_readiness(packet, policy)
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output)
        return 0
    except (ImportRejected, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(exc),
                          "mayConnectCorporateSystems": False}, ensure_ascii=False),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
