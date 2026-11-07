"""Cycle 43: reproducible *research* readiness audit of the public repository.

The 128 exhaustive counterfactuals exercise the AUTHOR'S question-selection
rules, not independent engineering correctness. File hashes show local content
identity, not author identity, external custodian assurance or technical approval.
No GitHub API, private document, IdP, OEM system, SAP or ECM is accessed.
"""
from __future__ import annotations

import argparse
import copy
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from benchmarks.mechanical_reasoning import (
    CASES_PATH, ORACLE_PATH, DOMAIN_PATHS, FAMILIES, evaluate, investigate,
)
from pilot.change_review_packets import digest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/cycle43-readiness.v1.json"

CLAIM_STATUS = {
    "question_selector": "implemented_synthetic",
    "independent_mechanical_review": "not_demonstrated",
    "schema_coverage": "partially_verified",
    "distributed_authorization": "synthetic_only",
    "backlog_traceability": "reconciliation_required",
}
ISSUE_STATUS = {1: "reassess", 4: "open", 5: "open", 50: "partially_implemented"}
SAFETY_FLAGS = (
    "diagnosticAccuracyMeasured", "independentMechanicalReviewCompleted",
    "realFieldMeasurementsIncluded", "oemSeriesEffectivityVerified",
    "realIdentityProviderConnected", "realPrivateDocumentsAccessed",
    "mayWriteSAP", "mayModifyECM", "mayExecuteTests", "mayReleaseEquipment",
)


class ReadinessRejected(ValueError):
    """A source or report attempts to overstate its provenance or authority."""


def require(condition, message):
    if not condition:
        raise ReadinessRejected(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _checked_path(root, relative):
    require(isinstance(relative, str) and relative
            and not relative.startswith("/") and "\\" not in relative,
            "invalid evidence path")
    parts = Path(relative).parts
    require(".." not in parts and "." not in parts, "evidence path traversal")
    base = root.resolve()
    candidate = (base / relative).resolve()
    require(candidate.is_relative_to(base) and candidate.is_file(),
            "missing or external evidence path: " + relative)
    return candidate


def validate_manifest(manifest, root=ROOT):
    require(isinstance(manifest, dict) and set(manifest) ==
            {"schema", "version", "baseline", "claims", "openIssueSnapshot",
             "safety", "externalReviewArtifactsReceived"},
            "cycle43 manifest shape changed")
    require(manifest["schema"] ==
            "maintenance-superinteligence.cycle43-readiness.v1"
            and manifest["version"] == "1.0.0", "unknown manifest version")
    baseline = manifest["baseline"]
    require(isinstance(baseline, dict) and set(baseline) ==
            {"mainCommit", "researchVersion", "lastCompletedCycle",
             "snapshotDate", "source"},
            "baseline structure changed")
    require(baseline["mainCommit"] ==
            "604c9fa2f98393ca31bef5cf31c40a60566851e7"
            and baseline["researchVersion"] == "4.2.0"
            and baseline["lastCompletedCycle"] == 42
            and baseline["snapshotDate"] == "2026-11-03"
            and baseline["source"] == "github_main_snapshot_not_live_api",
            "baseline must remain historical, not imply live status")
    require(manifest["externalReviewArtifactsReceived"] is False
            and isinstance(manifest["safety"], dict)
            and set(manifest["safety"]) == set(SAFETY_FLAGS)
            and all(manifest["safety"][k] is False for k in SAFETY_FLAGS),
            "real-world evidence or operational approval falsely asserted")
    claims = manifest["claims"]
    require(isinstance(claims, list) and len(claims) == len(CLAIM_STATUS),
            "claim audit coverage changed")
    require({x.get("id") for x in claims if isinstance(x, dict)} ==
            set(CLAIM_STATUS), "claim identities missing or duplicated")
    for entry in claims:
        require(set(entry) ==
                {"id", "state", "evidencePaths", "limitation",
                 "externallyValidated"}, "claim schema changed")
        require(entry["state"] == CLAIM_STATUS[entry["id"]]
                and entry["externallyValidated"] is False,
                "research state falsely promoted")
        require(isinstance(entry["limitation"], str)
                and len(entry["limitation"]) >= 30,
                "missing substantive limitation")
        paths = entry["evidencePaths"]
        require(isinstance(paths, list) and len(paths) >= 2
                and len(set(paths)) == len(paths),
                "missing/duplicate source paths")
        for path in paths:
            _checked_path(root, path)
    issues = manifest["openIssueSnapshot"]
    require(isinstance(issues, list) and len(issues) == len(ISSUE_STATUS),
            "issue coverage changed")
    require({x.get("number") for x in issues if isinstance(x, dict)} ==
            set(ISSUE_STATUS), "missing/duplicate tracked issues")
    for issue in issues:
        require(set(issue) == {"number", "state", "evidencePaths",
                              "remainingWork", "mayAutoClose"},
                "issue structure changed")
        require(issue["state"] == ISSUE_STATUS[issue["number"]]
                and issue["mayAutoClose"] is False
                and isinstance(issue["remainingWork"], str)
                and len(issue["remainingWork"]) >= 30,
                "automatic issue closure or unsupported completeness")
        require(isinstance(issue["evidencePaths"], list)
                and len(issue["evidencePaths"]) >= 1,
                "issue lacks evidence anchor")
        for path in issue["evidencePaths"]:
            _checked_path(root, path)
    _checked_path(root, "benchmarks/mechanical-reasoning-cases.v1.json")
    _checked_path(root, "benchmarks/mechanical-reasoning-oracle.v1.json")
    return True


def exercise_counterfactuals(cases):
    """Exhaustively test four Boolean context gates x conflict in four domains.

    Expected answers use the same authored gate order as the selector; hence
    these checks are a *structural regression*, never independent validation.
    """
    samples = {name: next(case for case in cases
                          if case["familyId"] == name) for name in FAMILIES}
    results = {}
    for family in FAMILIES:
        gates = DOMAIN_PATHS[family]["gates"]
        require(len(gates) == 4, "expected exactly four author-curated gates")
        checks = 0
        for conflict in (False, True):
            for flags in product((False, True), repeat=4):
                c = copy.deepcopy(samples[family])
                c["unresolvedContradiction"] = conflict
                c["contextAvailable"] = {
                    gate[0]: value for gate, value in zip(gates, flags)
                }
                answer = investigate(c)
                missing = next((g[1] for g, available in zip(gates, flags)
                                if not available), None)
                expected = ("reconcile_conflicting_reports" if conflict else
                            missing or "escalate_to_engineer_for_review")
                require(answer["selectedQuestionId"] == expected,
                        "question order or contradiction invariant failed")
                require(answer["confirmedRootCause"] is None
                        and answer["reviewRequired"] is True
                        and answer["testExecuted"] is False
                        and answer["oemEffectivityVerified"] is False
                        and answer["evidenceIsSimulated"] is True
                        and len(answer["hypotheses"]) == 3
                        and all(h["status"] == "open_not_confirmed"
                                and h["probability"] is None
                                for h in answer["hypotheses"])
                        and all(answer[k] is False for k in
                                ("mayRunTests", "mayCreateWorkOrder",
                                 "mayReleaseEquipment")),
                        "fictional exercise promoted cause or authority")
                checks += 1
        results[family] = checks
    require(sum(results.values()) == 128, "incomplete counterfactual coverage")
    return results


def evaluate_readiness(manifest, root=ROOT):
    validate_manifest(manifest, root)
    authored_cases = load(root / "benchmarks/mechanical-reasoning-cases.v1.json")
    authored_oracle = load(root / "benchmarks/mechanical-reasoning-oracle.v1.json")
    authored_result = evaluate(authored_cases, authored_oracle)
    require(authored_result["caseCount"] == 24
            and authored_result["agreementWithAuthoredOracle"] ==
            {"matched": 24, "total": 24}
            and authored_result["diagnosticAccuracyMeasured"] is False
            and authored_result["independentMechanicalReviewCompleted"] is False
            and authored_result["mayClaimDiagnosticValidity"] is False,
            "existing editorial regression has drifted")
    by_family = exercise_counterfactuals(authored_cases["cases"])
    all_paths = sorted({p for x in manifest["claims"] for p in x["evidencePaths"]}
                       | {p for x in manifest["openIssueSnapshot"]
                          for p in x["evidencePaths"]})
    fingerprints = [
        {"path": path, "sha256": sha256(_checked_path(root, path).read_bytes()).hexdigest()}
        for path in all_paths
    ]
    return {
        "schema": "maintenance-superinteligence.cycle43-readiness-report.v1",
        "version": "1.0.0",
        "baseline": manifest["baseline"],
        "manifestDigest": digest(manifest),
        "auditNature": "offline_self_consistency_and_document_presence",
        "claimStates": [{"id": x["id"], "state": x["state"],
                         "limitation": x["limitation"]}
                        for x in manifest["claims"]],
        "trackedOpenIssues": [{"number": x["number"], "state": x["state"],
                               "remainingWork": x["remainingWork"]}
                              for x in manifest["openIssueSnapshot"]],
        "evidenceFileFingerprints": fingerprints,
        "authoredQuestionAgreement": authored_result["agreementWithAuthoredOracle"],
        "counterfactualStructuralChecks": {
            "perFamily": by_family, "total": sum(by_family.values()),
            "independentOracleUsed": False,
        },
        "safety": dict(manifest["safety"]),
        "externalReviewArtifactsReceived": False,
        "mayClaimMechanicalDiagnosticCompetence": False,
        "mayConcludeExternalTechnicalApproval": False,
        "issueStatesAreLive": False,
        "decision": "no_go_independent_validation_not_performed",
    }


def verify_report(report, manifest, root=ROOT):
    require(report == evaluate_readiness(manifest, root),
            "stale, altered, or overclaimed readiness report")
    return True


def render_markdown(report):
    require(report["decision"] == "no_go_independent_validation_not_performed"
            and report["mayClaimMechanicalDiagnosticCompetence"] is False
            and report["mayConcludeExternalTechnicalApproval"] is False,
            "unsafe markdown summary")
    lines = [
        "# Ciclo 43 — Auditoria de maturidade de pesquisa (NO GO)",
        "",
        "Esta é uma auditoria estrutural **offline** de um snapshot público.",
        "Hashes de arquivos não autenticam autores, revisores nem fontes externas.",
        "Os casos são fictícios, não medições nem diagnósticos de campo.",
        "",
        "## Limites comprovados",
        "",
        f"- Concordância com gabarito **autoral**: "
        f"{report['authoredQuestionAgreement']['matched']}/"
        f"{report['authoredQuestionAgreement']['total']}.",
        f"- Checagens contrafactuais **estruturais**: "
        f"{report['counterfactualStructuralChecks']['total']}.",
        "- Validação mecânica independente: **não realizada**.",
        "- Efetividade OEM por série: **não verificada**.",
        "- Autorização de teste, OS, SAP, ECM ou liberação: **não concedida**.",
        "",
        "## Avaliação das evidências",
        "",
        "| Eixo | Estado declarado | Limite |",
        "| --- | --- | --- |",
    ]
    for c in report["claimStates"]:
        lines.append(f"| {c['id']} | {c['state']} | "
                     f"{c['limitation'].replace('|', '/')} |")
    lines.extend(["", "## Issues abertas no snapshot de 03/11/2026",
                  "", "| Issue | Estado de revisão | Trabalho remanescente |",
                  "| --- | --- | --- |"])
    for issue in report["trackedOpenIssues"]:
        lines.append(f"| #{issue['number']} | {issue['state']} | "
                     f"{issue['remainingWork'].replace('|', '/')} |")
    lines.extend(["", "**Decisão:** NO GO para validação técnica independente "
                  "e qualquer autoridade operacional.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    manifest = load(args.manifest)
    report = evaluate_readiness(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)
                           + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
