"""Ciclo 12 — dossiê estático e auditável, SEM qualquer aceite real.

Leitura exclusiva de fixtures públicos SIM-*. Nenhum IdP, SAP, ECM, manual
licenciado, arquivo de evidência privada ou assinatura é acessado.
"""
from __future__ import annotations
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import ImportRejected, require
from governance.integration_contracts import ROOT, POLICY_PATH, digest
from governance.deployment_readiness import (
    FIXTURE_PATH as READINESS_PATH, REQUIRED_CHANGE_IMPACTS,
    evaluate_readiness, validate_readiness,
)

DOSSIER_PATH = ROOT / "governance/readiness-dossier-fixture.v1.json"
PROOF_TYPES = {
    "corporate_identity_provider_server_validation": "identity_federation",
    "unique_human_identity_and_active_role": "identity_role",
    "competence_verified_from_corporate_source": "competence_register",
    "author_reviewers_adjudicator_separated": "separation_of_duties",
    "no_conflict_record": "conflict_of_interest",
    "two_independent_reviewers": "double_review",
    "immutable_claim_revision_and_source_manifest": "document_version",
    "verified_audit_timestamp_and_protected_storage": "audit_integrity",
    "qualified_document_entitlement_and_oem_effectivity": "oem_effectivity",
    "separate_operational_authorization": "operational_separation",
}
EXCEPTION_TARGETS = {
    "corporate_identity_provider_server_validation",
    "qualified_document_entitlement_and_oem_effectivity",
}
IMPACT_MAP = {
    **REQUIRED_CHANGE_IMPACTS,
    "conflict_of_interest_discovered": {
        "no_conflict_record", "author_reviewers_adjudicator_separated",
        "two_independent_reviewers", "separate_operational_authorization",
    },
}
GATE_FALSE_KEYS = {
    "engineerIdentityVerified", "securityIdentityVerified",
    "privacyIdentityVerified", "custodianIdentityVerified",
    "twoIndependentRealReviewers", "evidenceProtectedExternally",
    "sourceOemEffectivityVerified", "approvalGranted", "mayDeploy",
    "mayReleaseEquipment",
}
REQUEST_FIELDS = {
    "requestId", "controlId", "requestedProofType", "acceptanceCriterion",
    "evidenceSource", "requestedByRole", "privateEvidenceLocation",
    "authenticatedEvidence", "licensingVerified", "retentionReviewed",
    "signatureVerified", "status",
}
ACTION_FIELDS = {
    "actionId", "controlId", "ownerRole", "requestId", "action", "dueDate",
    "completionStatus", "completedByRealPerson", "implementationApproval",
}
EXCEPTION_FIELDS = {
    "exceptionId", "controlId", "requesterId", "rationale", "sourceRef",
    "decision", "waiveControl", "mayDeploy", "approvedByRealPerson",
}
SCENARIO_FIELDS = {
    "scenarioId", "eventType", "invalidates", "sourceEvidenceRef", "state",
    "reopenReview", "previousQualificationRemainsValid",
    "automaticReapproval", "operationalPermission",
}
ROOT_FIELDS = {
    "schema", "version", "nature", "sourceReadinessSchema",
    "sourceReadinessVersion", "evidenceRequests", "ownerActions",
    "exceptionRequests", "changeScenarios", "independentReviewGate",
    "publication",
}
GATE_FIELDS = GATE_FALSE_KEYS | {"schema", "status"}


def exact(obj: object, fields: set[str], where: str) -> dict:
    require(isinstance(obj, dict) and set(obj) == fields,
            f"{where}: unrecognized or missing fields")
    return obj


def ident(value: object, pattern: str) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def check_dossier(fixture: object, readiness: dict, policy: dict) -> dict:
    source = validate_readiness(readiness, policy)
    f = exact(fixture, ROOT_FIELDS, "dossier")
    require(f["schema"] == "maintenance-superinteligence.readiness-dossier-fixture.v1"
            and f["version"] == "1.0.0"
            and f["nature"] == "public_synthetic_dossier_only"
            and f["sourceReadinessSchema"] == readiness["schema"]
            and f["sourceReadinessVersion"] == readiness["version"]
            and f["sourceReadinessSchema"]
                == "maintenance-superinteligence.deployment-readiness-fixture.v1"
            and f["sourceReadinessVersion"] == "1.0.0",
            "dossier: source Cycle 11 contract incompatible or falsely upgraded")
    controls = source["controls"]
    require(isinstance(f["evidenceRequests"], list)
            and len(f["evidenceRequests"]) == 10, "requests: all ten required")
    reqs = {}
    for r in f["evidenceRequests"]:
        exact(r, REQUEST_FIELDS, "request")
        cid = r["controlId"]
        require(cid in controls and cid not in reqs
                and ident(r["requestId"], r"SIM-REQ-\d{2}")
                and r["requestId"] == "SIM-REQ-" + controls[cid]["evidenceId"][-2:]
                and r["requestedProofType"] == PROOF_TYPES[cid]
                and r["acceptanceCriterion"] == controls[cid]["acceptanceCriterion"]
                and r["requestedByRole"] == controls[cid]["ownerRole"]
                and r["evidenceSource"] == "private_corporate_system_required"
                and r["privateEvidenceLocation"] is None
                and r["status"] == "not_received"
                and all(r[k] is False for k in ("authenticatedEvidence",
                           "licensingVerified", "retentionReviewed", "signatureVerified")),
                "request: duplicate, wrong owner, missing provenance or false approval")
        reqs[cid] = r
    require(set(reqs) == set(controls), "request: missing source control")
    require(isinstance(f["ownerActions"], list)
            and len(f["ownerActions"]) == 10, "actions: all ten required")
    actions = {}
    for a in f["ownerActions"]:
        exact(a, ACTION_FIELDS, "owner action")
        cid = a["controlId"]
        require(cid in controls and cid not in actions
                and a["actionId"] == "SIM-ACTION-" + controls[cid]["evidenceId"][-2:]
                and a["requestId"] == reqs[cid]["requestId"]
                and a["ownerRole"] == controls[cid]["ownerRole"]
                and a["action"] == "document_and_verify_private_control_in_approved_environment"
                and a["dueDate"] is None
                and a["completionStatus"] == "pending_not_executed"
                and a["completedByRealPerson"] is False
                and a["implementationApproval"] is False,
                "action: forged completion, duplicate, owner mismatch or orphan")
        actions[cid] = a
    require(set(actions) == set(controls), "action: missing source control")
    require(isinstance(f["exceptionRequests"], list)
            and len(f["exceptionRequests"]) == len(EXCEPTION_TARGETS),
            "exceptions: two negative example cases required")
    exceptions = {}
    for x in f["exceptionRequests"]:
        exact(x, EXCEPTION_FIELDS, "exception")
        cid = x["controlId"]
        require(cid in EXCEPTION_TARGETS and cid not in exceptions
                and ident(x["exceptionId"], r"SIM-EXCEPTION-\d{2}")
                and ident(x["requesterId"], r"SIM-REQUESTER-[A-Z0-9-]+")
                and isinstance(x["rationale"], str)
                and 20 <= len(x["rationale"].strip()) <= 300
                and x["sourceRef"] is None
                and x["decision"] == "blocked_no_verified_evidence"
                and x["waiveControl"] is False
                and x["mayDeploy"] is False
                and x["approvedByRealPerson"] is False,
                "exception: cannot waive a required security or OEM control")
        exceptions[cid] = x
    require(set(exceptions) == EXCEPTION_TARGETS
            and len({x["exceptionId"] for x in exceptions.values()}) == 2,
            "exception: missing or duplicated exercise")
    require(isinstance(f["changeScenarios"], list)
            and len(f["changeScenarios"]) == len(IMPACT_MAP),
            "scenario: all change triggers required")
    scenarios = {}
    for s in f["changeScenarios"]:
        exact(s, SCENARIO_FIELDS, "scenario")
        key = s["eventType"]
        require(key in IMPACT_MAP and key not in scenarios
                and ident(s["scenarioId"], r"SIM-SCENARIO-\d{2}")
                and isinstance(s["invalidates"], list)
                and len(s["invalidates"]) == len(set(s["invalidates"]))
                and set(s["invalidates"]) == IMPACT_MAP[key]
                and s["sourceEvidenceRef"] is None
                and s["state"] == "simulated_not_occurred"
                and s["reopenReview"] is True
                and s["previousQualificationRemainsValid"] is False
                and s["automaticReapproval"] is False
                and s["operationalPermission"] is False,
                "scenario: cannot suppress invalidation or automatically reapprove")
        scenarios[key] = s
    require(set(scenarios) == set(IMPACT_MAP)
            and len({x["scenarioId"] for x in scenarios.values()})
                == len(IMPACT_MAP),
            "scenario: duplicate/missing change case")
    gate = exact(f["independentReviewGate"], GATE_FIELDS, "review gate")
    require(gate["schema"] == "maintenance-superinteligence.independent-review-gate.v1"
            and gate["status"] == "blocked_pending_private_review"
            and all(gate[k] is False for k in GATE_FALSE_KEYS),
            "review gate: no real signatures, reviewers, OEM or approval present")
    publication = exact(f["publication"],
        {"allowedDataClass", "privateDataIncluded", "licensedManualIncluded",
         "realIdentifiersIncluded", "secretsIncluded", "mayShareWithPublic"},
        "publication")
    require(publication["allowedDataClass"] == "synthetic_only"
            and all(publication[k] is False for k in publication
                    if k != "allowedDataClass"),
            "publication: corporate/private/licensed information is disallowed")
    return {"readiness": source, "requests": reqs, "actions": actions,
            "exceptions": exceptions, "scenarios": scenarios}


def build_dossier(fixture: dict, readiness: dict, policy: dict) -> dict:
    checked = check_dossier(fixture, readiness, policy)
    base = evaluate_readiness(readiness, policy)
    findings = []
    for row in base["implementationOrder"]:
        cid = row["controlId"]
        c = checked["readiness"]["controls"][cid]
        req = checked["requests"][cid]
        action = checked["actions"][cid]
        findings.append({
            "findingId": "SIM-FINDING-" + c["evidenceId"][-2:],
            "controlId": cid,
            "criticality": row["riskOnMissing"],
            "ownerRole": c["ownerRole"],
            "status": c["status"],
            "dependencies": list(c["dependsOn"]),
            "acceptanceCriterion": c["acceptanceCriterion"],
            "evidenceRequestId": req["requestId"],
            "requestedProofType": req["requestedProofType"],
            "evidenceRequestedFrom": "private_corporate_system_required",
            "evidenceReceived": False,
            "ownerActionId": action["actionId"],
            "ownerActionStatus": "pending_not_executed",
            "postponementRisk": (
                "Bloqueio de segurança, rastreabilidade ou segregação essencial"
                if row["riskOnMissing"] == "critical"
                else "Ausência de verificação de qualificação/independência"
            ),
            "decision": "blocked_pending_private_evidence",
            "verifiedByRealPerson": False,
        })
    return {
        "schema": "maintenance-superinteligence.readiness-review-dossier.v1",
        "version": "1.0.0",
        "mode": "synthetic_architecture_review_only",
        "readinessSourceSha256": digest(readiness),
        "dossierFixtureSha256": digest(fixture),
        "findings": findings,
        "independentReviewGate": fixture["independentReviewGate"],
        "findingCount": len(findings),
        "criticalFindings": sum(f["criticality"] == "critical" for f in findings),
        "highFindings": sum(f["criticality"] == "high" for f in findings),
        "evidenceRequests": [checked["requests"][f["controlId"]]
                             for f in findings],
        "ownerActions": [checked["actions"][f["controlId"]]
                         for f in findings],
        "exceptions": [checked["exceptions"][k] for k in sorted(EXCEPTION_TARGETS)],
        "changeScenarios": [checked["scenarios"][k] for k in sorted(IMPACT_MAP)],
        "compatibility": base["compatibility"] + [{
            "cycle": "cycle11",
            "path": "governance/deployment-readiness.v1.json",
            "schema": readiness["schema"],
            "version": readiness["version"],
            "contentSha256": digest(readiness),
            "sourceVerifiedAsPublicFile": True,
            "privateMigrationAuthorised": False,
        }],
        "futureAcceptanceCriteria": [
            "Identidades humanas verificadas pelo IdP e competência por disciplina",
            "Revisão independente, segregação de funções e conflitos tratados",
            "Fonte técnica OEM com direito de acesso, revisão e efetividade por série",
            "Proteção, retenção e classificação de evidências privadas/licenciadas",
            "Audit log externo e carimbo de tempo com integridade verificável",
            "Alçadas de Engenharia, Segurança, Privacidade e Gestão Documental",
            "Autorização operacional segregada da qualificação do conhecimento",
        ],
        "humanReviewAuthenticated": False,
        "privateEvidenceStoredHere": False,
        "evidenceFullyVerified": False,
        "oemEffectivityVerified": False,
        "deploymentApproved": False,
        "mayImportCorporateData": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
        "decision": "blocked_missing_private_verified_trust",
        "limitations": [
            "Checklist e identidades de exemplo não são pareceres reais.",
            "SHA de dados públicos e CI verde não são autorização de migração.",
            "Nenhum campo concluído ou verificado é produzido pelo simulador.",
        ],
    }


def render_html(report: dict) -> str:
    """Offline, no JS/remote assets; all varying text encoded as text nodes."""
    require(report.get("schema")
            == "maintenance-superinteligence.readiness-review-dossier.v1"
            and report.get("deploymentApproved") is False
            and report.get("humanReviewAuthenticated") is False
            and report.get("mayCreateWorkOrder") is False
            and report.get("mayReleaseEquipment") is False
            and isinstance(report.get("findings"), list)
            and len(report["findings"]) == 10
            and all(x.get("evidenceReceived") is False
                    and x.get("verifiedByRealPerson") is False
                    and x.get("decision") == "blocked_pending_private_evidence"
                    for x in report["findings"])
            and isinstance(report.get("exceptions"), list)
            and len(report["exceptions"]) == 2
            and all(x.get("waiveControl") is False
                    and x.get("mayDeploy") is False
                    for x in report["exceptions"])
            and isinstance(report.get("changeScenarios"), list)
            and len(report["changeScenarios"]) == 6
            and all(x.get("automaticReapproval") is False
                    and x.get("reopenReview") is True
                    for x in report["changeScenarios"]),
            "html: invalid or falsely approved dossier")
    def e(v: object) -> str:
        return escape(str(v), quote=True)
    rows = []
    for f in report["findings"]:
        rows.append("<tr>" + "".join("<td>" + e(x) + "</td>" for x in (
            f["controlId"], f["criticality"], f["status"],
            f["ownerRole"], ", ".join(f["dependencies"]) or "Nenhuma",
            f["acceptanceCriterion"], f["requestedProofType"],
            f["postponementRisk"], f["ownerActionStatus"],
        )) + "</tr>")
    scenarios = "".join(
        "<li><strong>" + e(s["eventType"]) + "</strong>: reabrir "
        + e(", ".join(s["invalidates"]))
        + " — sem reaprovação automática</li>" for s in report["changeScenarios"])
    exceptions = "".join(
        "<li>" + e(x["controlId"]) + ": " + e(x["rationale"])
        + " — <strong>BLOQUEADO</strong></li>" for x in report["exceptions"])
    criteria = "".join("<li>" + e(x) + "</li>" for x in report["futureAcceptanceCriteria"])
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
        + "form-action &apos;none&apos;" + '"><title>Dossiê de Prontidão — Simulação</title>'
        '<style>body{font:15px system-ui,sans-serif;margin:3rem auto;max-width:1250px;'
        'padding:0 1.2rem;color:#242424;background:#fafafa}h1{font-size:1.8rem}'
        '.alert{border-left:6px solid #861515;background:#fff0f0;padding:1rem}'
        '.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;'
        'background:white}th,td{border:1px solid #ccc;padding:.7rem;text-align:left;'
        'vertical-align:top}th{background:#eee}td{overflow-wrap:anywhere}'
        'section{margin-top:2rem}footer{color:#666}</style></head><body>'
        '<h1>Dossiê de prontidão para revisão de arquitetura — Ciclo 12</h1>'
        '<p class="alert"><strong>SIMULADO — IMPLANTAÇÃO BLOQUEADA.</strong>'
        ' Não há autenticidade humana, comprovação corporativa, liberação OEM'
        ' nem autorização de manutenção. Dados apenas fictícios.</p>'
        '<p>Controles: ' + e(report["findingCount"]) +
        ' | Críticos: ' + e(report["criticalFindings"]) +
        ' | Altos: ' + e(report["highFindings"]) +
        ' | Evidências reais verificadas: 0</p>'
        '<section><h2>Critérios e pendências</h2><div class="scroll">'
        '<table><thead><tr>' + "".join("<th>" + x + "</th>" for x in (
            "Controle", "Risco", "Status", "Responsável funcional",
            "Dependências", "Critério de aceite", "Prova exigida",
            "Risco de postergação", "Ação",
        )) + '</tr></thead><tbody>' + "".join(rows) +
        '</tbody></table></div></section>'
        '<section><h2>Exceções didáticas rejeitadas</h2><ul>' +
        exceptions + '</ul></section>'
        '<section><h2>Alterações que reabrem qualificação</h2><ul>' +
        scenarios + '</ul></section>'
        '<section><h2>Critérios para futura revisão privada</h2><ul>' +
        criteria + '</ul></section>'
        '<footer><p>Fonte: contratos públicos v1; relatório gerado offline,'
        ' sem assinaturas, dados de campo ou integração empresarial.</p>'
        '</footer></body></html>\n'
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=READINESS_PATH)
    p.add_argument("--fixture", type=Path, default=DOSSIER_PATH)
    p.add_argument("--policy", type=Path, default=POLICY_PATH)
    p.add_argument("--output", type=Path)
    p.add_argument("--html", type=Path)
    args = p.parse_args(argv)
    try:
        source = json.loads(args.source.read_text(encoding="utf-8"))
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        result = build_dossier(fixture, source, policy)
        serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True, exist_ok=True)
            args.html.write_text(render_html(result), encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected, ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(exc),
                          "deploymentApproved": False}, ensure_ascii=False),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
