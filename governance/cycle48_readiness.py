"""Cycle 48: offline integration snapshot + independent-study readiness gate.

The PR information is a fixed PUBLIC SNAPSHOT, NOT a live GitHub query.
A successful synthetic test cannot authenticate humans, license OEM documents,
verify cases, authorize maintenance, or allow a real-world study to begin.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from pilot.change_review_packets import require, digest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/cycle48-study-readiness.v1.json"
PREFIX = "maintenance-superinteligence.cycle48"
SHA = re.compile(r"^[0-9a-f]{40}$")
FROZEN_PR_SHAS = (
    "8c7c384fbf2fc0edfca62ded458b19efd14af7e6",
    "a394fa525f72f82845fb9869ec959de396600167",
    "7775e5593e3688db39b823321d61c4af9199d49f",
    "13b1fa12eafeb8780ed1c6d663129cf2c95939ca",
    "81467d4c359ba8a29096341cc413ba935aadc11e",
)
GATES = (
    "pr_chain_review", "baseline_freeze", "legal_case_authorization",
    "independent_custodian", "data_privacy_access", "corpus_leakage_review",
    "reviewer_identity_independence", "mechanical_competence",
    "oem_case_effectivity", "safety_and_stop_rules",
    "blinding_qualified_audit", "design_statistics_approval",
    "adjudicator_independence",
)
METRICS = (
    "case_level_preference", "pairwise_raw_agreement",
    "safety_flag_incidence", "case_abstention_fraction",
    "blinding_rejection_fraction",
)
DENIED = (
    "mayExecuteTests", "mayCreateWorkOrder", "mayWriteSAP", "mayModifyECM",
    "mayReleaseEquipment", "mayDeclareRootCause",
    "mayClaimDiagnosticAccuracy", "mayClaimIndependentReview",
)
PR_KEYS = {
    "number", "cycle", "base", "head", "headSha", "documentPath",
    "state", "dedicatedCiOnHead", "regressionOnHead",
    "independentCodeReviewApproved", "mergedIntoMain", "mayAutomaticallyMerge",
}
GATE_KEYS = {
    "id", "ownerRole", "requirement", "requestedArtifact",
    "state", "artifactReceived", "externallyVerified",
}
METRIC_KEYS = {
    "id", "numerator", "denominator", "interpretationRule",
    "registeredForDesignDiscussionOnly", "estimatedFromRealCases",
}
STUDY_FIELDS = {
    "design", "realDataCollected", "protocolPreRegistered",
    "sampleSizeJustified", "comparisonFrozen",
    "reviewerRecruitmentAuthorized", "blindnessHumanValidated",
    "caseProvenanceVerified", "independentExpertsConfirmed",
    "operationallyApproved",
}
MANIFEST_FIELDS = {
    "schema", "version", "snapshotDate", "source", "mainBaselineSha",
    "stack", "researchAim", "studyDesign", "gates", "metrics", "safety",
    "independentCaseStudyPerformed", "status",
}


def load_manifest(path=MANIFEST):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_manifest(data, root=ROOT):
    require(isinstance(data, dict) and set(data) == MANIFEST_FIELDS,
            "manifest missing fields or unexpected contents")
    require(
        data["schema"] == PREFIX + "-research-gate.v1"
        and data["version"] == "1.0.0"
        and data["snapshotDate"] == "2026-11-05"
        and data["source"] ==
            "human_reviewed_github_api_snapshot_reproduced_as_public_metadata_not_live"
        and isinstance(data["mainBaselineSha"], str)
        and SHA.fullmatch(data["mainBaselineSha"])
        and data["mainBaselineSha"] == "604c9fa2f98393ca31bef5cf31c40a60566851e7"
        and isinstance(data["researchAim"], str)
        and len(data["researchAim"]) >= 60
        and data["independentCaseStudyPerformed"] is False
        and data["status"] ==
            "no_go_pending_integration_and_external_study_prerequisites",
        "snapshot promoted to live or verified study")
    stack = data["stack"]
    require(isinstance(stack, list) and len(stack) == 5,
            "expected five pending PRs")
    refs = []
    for i, pr in enumerate(stack):
        require(isinstance(pr, dict) and set(pr) == PR_KEYS,
                "PR metadata fields changed")
        require(
            pr["number"] == 69 + i and pr["cycle"] == 43 + i
            and isinstance(pr["head"], str)
            and pr["head"].startswith("research/cycle" + str(43+i) + "-")
            and isinstance(pr["base"], str)
            and pr["base"] == ("main" if i == 0 else stack[i-1]["head"])
            and isinstance(pr["headSha"], str)
            and SHA.fullmatch(pr["headSha"])
            and pr["headSha"] == FROZEN_PR_SHAS[i]
            and pr["state"] == "open_draft"
            and pr["dedicatedCiOnHead"] == "passed"
            and pr["regressionOnHead"] == "passed"
            and pr["independentCodeReviewApproved"] is False
            and pr["mergedIntoMain"] is False
            and pr["mayAutomaticallyMerge"] is False,
            "PR dependency or approval unsupported by frozen snapshot")
        doc = pr["documentPath"]
        require(isinstance(doc, str) and doc.startswith("docs/CICLO_")
                and doc.endswith(".md") and ".." not in doc,
                "source path not within expected documentation")
        target = (Path(root) / doc).resolve()
        require(target.is_relative_to(Path(root).resolve()) and target.is_file(),
                "source document missing from checkout")
        refs.append({
            "number": pr["number"], "cycle": pr["cycle"],
            "base": pr["base"], "head": pr["head"],
            "headSha": pr["headSha"], "documentPath": doc,
            "documentSha256": sha256(target.read_bytes()).hexdigest(),
        })
    study = data["studyDesign"]
    require(isinstance(study, dict) and set(study) == STUDY_FIELDS
            and study["design"] ==
                "paired_blind_technical_question_preference_proposed"
            and all(study[k] is False for k in STUDY_FIELDS if k != "design"),
            "unverified study prerequisite promoted")
    gates = data["gates"]
    require(isinstance(gates, list)
            and [g.get("id") for g in gates] == list(GATES),
            "missing, reordered or duplicated external prerequisites")
    for g in gates:
        require(isinstance(g, dict) and set(g) == GATE_KEYS
                and g["state"] == "unverified_requires_external_evidence"
                and g["artifactReceived"] is False
                and g["externallyVerified"] is False
                and all(isinstance(g[k], str) and len(g[k]) >= 25 for k in
                        ("requirement", "requestedArtifact"))
                and isinstance(g["ownerRole"], str)
                and len(g["ownerRole"]) >= 10,
                "external evidence claimed without verification")
    metrics = data["metrics"]
    require(isinstance(metrics, list)
            and [m.get("id") for m in metrics] == list(METRICS),
            "study metrics, numerators or denominators missing")
    for m in metrics:
        require(isinstance(m, dict) and set(m) == METRIC_KEYS
                and all(isinstance(m[k], str) and len(m[k]) >= 30
                        for k in ("numerator", "denominator",
                                  "interpretationRule"))
                and m["registeredForDesignDiscussionOnly"] is True
                and m["estimatedFromRealCases"] is False,
                "metric promoted to real measurement")
    require(isinstance(data["safety"], dict)
            and set(data["safety"]) == set(DENIED)
            and all(data["safety"][k] is False for k in DENIED),
            "study metadata grants operational authority")
    return refs


def build_report(data, root=ROOT):
    refs = validate_manifest(data, root)
    return {
        "schema": PREFIX + "-readiness-report.v1",
        "version": "1.0.0",
        "sourceSnapshotDigest": digest(data),
        "snapshotIsLive": False,
        "mainBaselineSha": data["mainBaselineSha"],
        "pendingStackCount": len(refs),
        "pendingIntegration": refs,
        "unverifiedExternalGateCount": len(data["gates"]),
        "pendingEvidenceRequests": [
            {"gateId": g["id"], "ownerRole": g["ownerRole"],
             "request": g["requestedArtifact"]}
            for g in data["gates"]
        ],
        "proposedMetricCount": len(data["metrics"]),
        "metricsEstimatedFromRealCases": 0,
        "independentStudyCompleted": False,
        "externallyVerified": False,
        "prChainApproved": False,
        "studyMayRecruitParticipants": False,
        "studyMayStart": False,
        "diagnosticAccuracyEstablished": False,
        "mayExecuteTests": False,
        "mayCreateWorkOrder": False,
        "mayWriteSAP": False,
        "mayModifyECM": False,
        "mayReleaseEquipment": False,
        "status": "no_go_review_pr_stack_and_obtain_independent_study_evidence",
    }


def verify_report(report, data, root=ROOT):
    require(report == build_report(data, root),
            "report changed or evidence no longer matches checkout")
    return True


def markdown(data, report):
    require(report == build_report(data), "cannot format stale report")
    lines = [
        "# Ciclo 48 — Prontidão de integração e pesquisa (NO GO)", "",
        "Snapshot de " + data["snapshotDate"]
        + ", NÃO é consulta GitHub ao vivo.", "",
        "## PRs em fila (todos drafts não mesclados)", "",
        "| PR | Ciclo | Base | CI no HEAD do snapshot |",
        "| --- | --- | --- | --- |",
    ]
    for pr in data["stack"]:
        lines.append(
            f"| #{pr['number']} | {pr['cycle']} | {pr['base']} | "
            "dedicado e regressão aprovados |"
        )
    lines.extend(["", "## Evidências externas ausentes", ""])
    for i, gate in enumerate(data["gates"], 1):
        lines.append(
            f"{i}. {gate['id']} — {gate['ownerRole']}: "
            f"{gate['requestedArtifact']}"
        )
    lines.extend([
        "", "## Métricas somente propostas", "",
    ])
    for metric in data["metrics"]:
        lines.append(
            f"- {metric['id']}: numerador — {metric['numerator']}; "
            f"denominador — {metric['denominator']}."
        )
    lines.extend([
        "", "**NO GO:** não recrutar pessoas, coletar dados privados, "
        "diagnosticar falhas, executar testes, abrir OS, escrever no SAP/ECM "
        "ou liberar equipamentos por causa deste relatório.", "",
    ])
    return "\n".join(lines)


def cli(argv=None):
    ap = argparse.ArgumentParser(description="C48 public offline study no-go")
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--markdown", type=Path)
    args = ap.parse_args(argv)
    data = load_manifest(args.manifest)
    report = build_report(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(data, report), encoding="utf-8")
    return report


if __name__ == "__main__":
    cli()
