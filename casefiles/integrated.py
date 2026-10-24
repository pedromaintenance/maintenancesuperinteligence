"""Ciclo 13: dossiê diferencial de engenharia SEM diagnóstico ou operação.

Monta fontes públicas explicitamente travadas por SHA-256, hipóteses editoriais,
métodos conceituais, perguntas e gates de governança. Não acessa dados reais.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import (ImportRejected, load_lock, require,
                                    validate_snapshot, build_consumer_index)
from evidence.ledger import sha
from investigations.final_drive import investigate
from methods.discrimination import MATRIX_PATH, select_questions, validate_matrix
from methods.library import (ROOT, CATALOG_PATH, SOURCES_PATH,
                             validate_catalog, validate_sources)
from benchmarks.quality import (BENCHMARK_PATH, execute_benchmark,
                                validate_manifest)
from governance.readiness_dossier import (DOSSIER_PATH, READINESS_PATH,
                                         POLICY_PATH, build_dossier)
from evidence.qualitative import (MATRIX_PATH as EVIDENCE_MATRIX_PATH,
                                  validate_qualitative_matrix, assess_case)

FIXTURE_PATH = ROOT / "casefiles/technical-cases.v1.json"
ALLOWED = {
    "SIM-TECH-FD-01": ("FD-ADDITIVES-UNKNOWN", "final_drive",
                       "final_drive_additive_profile",
                       "examples/777e_additives_only.json"),
    "SIM-TECH-HYD-01": ("HYD-LOAD-DISPUTED", "hydraulics",
                        "hydraulic_load_dispute", None),
    "SIM-TECH-ECM-LOG-01": ("ECM-LOGGED-UNKNOWN", "electronics",
                            "ecm_logged_event", None),
    "SIM-TECH-ECM-ACT-01": ("ECM-ACTIVE-CONTEXT-MISSING", "electronics",
                            "ecm_active_event", None),
}
CONTEXT = {
    "final_drive_additive_profile": {
        "asset": "Caminhão CAT 777E — referência educacional sem série",
        "system": "Comando final / redutor de roda",
        "function": "Transmitir torque com redução de velocidade ao conjunto de roda.",
        "requirement": "Manter transmissão e lubrificação dentro das condições OEM aplicáveis, ainda não obtidas.",
        "symptom": "Perfil de aditivos diferente no laudo sintético isolado.",
        "effect": "Anomalia potencial não caracterizada: condição do lubrificante ou possível dano ao conjunto não diferenciados.",
        "immediate": "Mudança de formulação, erro de coleta, contaminação ou mecanismo de desgaste são alternativas, não eventos confirmados.",
        "root": "Causa raiz desconhecida; faltam identificação do óleo, histórico, amostra comparável e efetividade OEM.",
        "continued": "Sem esclarecer origem, pode-se postergar deterioração ou desmontar sem justificativa; risco não quantificado.",
        "action": "Conferir identificação e histórico do óleo, rastreabilidade da amostra e tendências com responsável técnico antes de especificar inspeção.",
    },
    "hydraulic_load_dispute": {
        "asset": "Equipamento hidráulico genérico e fictício",
        "system": "Alimentação, controle e atuação hidráulica",
        "function": "Converter energia hidráulica em atuação controlada da carga.",
        "requirement": "Atender desempenho previsto sob configuração e condição de carga corretamente identificadas.",
        "symptom": "Atuação lenta informada e contexto de carga contraditório.",
        "effect": "Desempenho não caracterizado; restrição, demanda, bomba ou variação térmica ainda concorrem.",
        "immediate": "Demanda/carga, regulação, alimentação ou condição térmica poderiam explicar o sintoma; nenhuma medida validada.",
        "root": "Causa raiz desconhecida sem esquema, porta de ensaio, ciclo e parâmetros OEM efetivos.",
        "continued": "Potencial perda de função ou interpretação incorreta; não há análise de risco de campo suficiente para liberar operação.",
        "action": "Conciliar condição de carga e documentação do circuito antes de planejar qualquer avaliação instrumental autorizada.",
    },
    "ecm_logged_event": {
        "asset": "Equipamento com ECM genérico fictício",
        "system": "Monitoramento eletrônico / diagnóstico",
        "function": "Registrar e disponibilizar estados, eventos e diagnósticos do sistema monitorado.",
        "requirement": "Interpretar condição ativa/histórica com identificação do módulo, relógio e literatura da configuração.",
        "symptom": "Código genérico registrado, sem prova de falha ativa.",
        "effect": "Registro pode corresponder a fenômeno físico, circuito, evento transitório ou histórico.",
        "immediate": "Registro armazenado pode refletir condição já cessada; circuito e condição física ainda não foram comparados.",
        "root": "Causa raiz desconhecida; não há identificação do ECM nem evidência temporal/física independente.",
        "continued": "Substituição de sensor/ECM sem discriminação pode não resolver o evento; nenhum risco percentual foi estimado.",
        "action": "Solicitar identificação do ECM, natureza do registro, contexto temporal e leitura física comparável com acesso autorizado.",
    },
    "ecm_active_event": {
        "asset": "Equipamento com ECM genérico fictício",
        "system": "Monitoramento eletrônico / diagnóstico",
        "function": "Registrar e disponibilizar estados, eventos e diagnósticos do sistema monitorado.",
        "requirement": "Diferenciar indicação ativa, transitória e histórica conforme contexto e literatura do ECM.",
        "symptom": "Código genérico ativo somente no cenário sintético; contexto incompleto.",
        "effect": "A indicação de atividade não comprova defeito de sensor, ECM ou componente mecânico monitorado.",
        "immediate": "Intermitência, anomalia física ou medição elétrica são mecanismos ainda concorrentes.",
        "root": "Causa raiz desconhecida; faltam configuração do ECM, sequência temporal e medida independente.",
        "continued": "O risco operacional real exige avaliação local por profissional habilitado; código ativo fictício não autoriza conclusão nem liberação.",
        "action": "Diferenciar sinal ativo/histórico, cronologia e contexto operacional antes de planejar testes sob literatura autorizada.",
    },
}
FIXTURE_FIELDS = {"schema", "version", "purpose", "sourceBenchmark",
                  "sourceMethodMatrix", "sourceMethodCatalog", "sourceReadiness",
                  "sourceReviewDossier", "cases"}
CASE_FIELDS = {"caseFileId", "benchmarkFixtureId", "familyId",
               "editorialContextKey", "pilotCasePath", "evidenceNature",
               "sourceObservedMeasurements", "rootCauseConfirmed",
               "testPerformed", "diagnosticAccuracyEstablished", "fieldRiskScore",
               "oemPressureOrWearLimit", "realMachineIdentifier",
               "oemEffectivityVerified", "independentHumanReviewComplete",
               "mayRunTests", "mayCreateWorkOrder", "mayModifyECM",
               "mayReleaseEquipment", "operationallyApproved"}
DENIALS = ("sourceObservedMeasurements", "rootCauseConfirmed",
           "testPerformed", "diagnosticAccuracyEstablished",
           "oemEffectivityVerified", "independentHumanReviewComplete",
           "mayRunTests", "mayCreateWorkOrder", "mayModifyECM",
           "mayReleaseEquipment", "operationallyApproved")


def exact(obj: object, fields: set, name: str) -> dict:
    require(isinstance(obj, dict) and set(obj) == fields,
            f"{name}: unknown or missing contract field")
    return obj


def validate_fixture(fixture: object) -> dict:
    f = exact(fixture, FIXTURE_FIELDS, "casefile fixture")
    require(f["schema"] == "maintenance-superinteligence.technical-casefile-fixture.v1"
            and f["version"] == "1.0.0"
            and f["purpose"] == "synthetic_didactic_investigation_only"
            and f["sourceBenchmark"] == "benchmarks/question-quality.v1.json"
            and f["sourceMethodMatrix"] == "methods/discrimination-matrix.v1.json"
            and f["sourceMethodCatalog"] == "methods/catalog.v1.json"
            and f["sourceReadiness"] == "governance/deployment-readiness.v1.json"
            and f["sourceReviewDossier"] == "governance/readiness-dossier-fixture.v1.json",
            "casefile: foreign corpus, contract or authorization")
    require(isinstance(f["cases"], list) and len(f["cases"]) == len(ALLOWED),
            "casefile: all four anchored synthetic cases are mandatory")
    seen = set()
    for row in f["cases"]:
        exact(row, CASE_FIELDS, "casefile case")
        cid = row["caseFileId"]
        require(cid in ALLOWED and cid not in seen
                and (row["benchmarkFixtureId"], row["familyId"],
                     row["editorialContextKey"], row["pilotCasePath"]) == ALLOWED[cid],
                "casefile: unknown/duplicate id or changed technical context")
        seen.add(cid)
        require(row["evidenceNature"] == "simulation"
                and all(row[k] is False for k in DENIALS)
                and all(row[k] is None for k in (
                    "fieldRiskScore", "oemPressureOrWearLimit",
                    "realMachineIdentifier")),
                "casefile: real data, field scores, OEM limits or authority forbidden")
    require(seen == set(ALLOWED), "casefile: missing training family")
    return {x["caseFileId"]: x for x in f["cases"]}


def load_dependencies(snapshot: dict) -> dict:
    registry = validate_sources(json.loads(SOURCES_PATH.read_text(encoding="utf-8")))
    methods = validate_catalog(json.loads(CATALOG_PATH.read_text(encoding="utf-8")),
                               registry, snapshot)
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    families = validate_matrix(matrix, methods, snapshot)
    evidence_matrix = json.loads(EVIDENCE_MATRIX_PATH.read_text(encoding="utf-8"))
    qualitative = validate_qualitative_matrix(evidence_matrix, families, methods, registry)
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    checks = execute_benchmark(benchmark, matrix, methods, snapshot)
    require(checks["acceptance"] == "regression_pass"
            and checks["fixturesPassed"] == 15
            and checks["diagnosticAccuracyMeasured"] is False
            and checks["technicalReviewGate"]["mayClaimFieldDiagnosticValidity"] is False,
            "casefile: synthetic question regression/qualification gate failed")
    validated = validate_manifest(benchmark, families)
    readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    review_fixture = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    gate = build_dossier(review_fixture, readiness, policy)
    require(gate["decision"] == "blocked_missing_private_verified_trust"
            and gate["findingCount"] == 10
            and gate["deploymentApproved"] is False
            and gate["humanReviewAuthenticated"] is False,
            "casefile: review/deployment incorrectly authorized")
    return {"sources": registry, "methods": methods, "matrix": matrix,
            "families": families, "qualitativeMatrix": qualitative,
            "qualitativeInputSha256": sha(evidence_matrix),
            "benchmark": benchmark,
            "fixtures": {x["fixtureId"]: x for x in validated},
            "checks": checks, "gate": gate, "readiness": readiness,
            "reviewFixture": review_fixture}


def assemble_case(row: dict, deps: dict, snapshot: dict) -> dict:
    require(row["caseFileId"] in ALLOWED, "casefile: unknown requested case")
    fixture = deps["fixtures"][row["benchmarkFixtureId"]]
    require(fixture["familyId"] == row["familyId"], "casefile: domain not linked")
    case = fixture["case"]
    selection = select_questions(case, deps["matrix"], deps["methods"], snapshot)
    expected = fixture["expected"]
    selected = selection["selectionRationale"]
    require(selected["selectedPairId"] == expected["selectedPairId"]
            and selected["selectedMethodId"] == expected["selectedMethodId"]
            and selected["selectionStatus"] == expected["selectionStatus"]
            and expected["mustAbstain"] is True,
            "casefile: editorial golden selection not reproduced")
    require(len(selection["hypotheses"]) == expected["openHypotheses"]
            and len(selection["comparisons"]) == expected["unresolvedPairs"]
            and all(x["status"] == "open_not_confirmed"
                    and x["confirmedRootCause"] is False
                    for x in selection["hypotheses"])
            and all(x["observedOutcome"] is None
                    and x["bothRemainOpen"] is True
                    for x in selection["comparisons"])
            and selection["confirmedComponent"] is None
            and all(selection[k] is False for k in (
                "mayRunTests", "mayModifyECM", "mayCreateWorkOrder",
                "mayReleaseEquipment")),
            "casefile: confirmed mechanisms or performed tests without evidence")
    chosen = next(q for q in selection["candidateQuestions"]
                  if q["pairId"] == selected["selectedPairId"]
                  and q["methodId"] == selected["selectedMethodId"])
    candidates = []
    source_ids = set()
    for q in selection["candidateQuestions"]:
        require(q["mayExecute"] is False
                and q["executionStatus"] == "proposed_not_executed"
                and q["oemApplicability"] == "not_verified"
                and q["status"] == "question_only",
                "casefile: cannot promote proposed question to performed physical test")
        source_ids.update(q["methodSourceIds"])
        candidates.append({
            "pairId": q["pairId"], "methodId": q["methodId"],
            "question": q["methodQuestion"],
            "sources": list(q["methodSourceIds"]),
            "interpretationLimits": list(q["interpretationLimits"]),
            "safetyPrerequisites": list(q["safetyPrerequisites"]),
            "contextStatus": q["contextStatus"],
            "executionStatus": "proposed_not_executed",
            "mayExecute": False,
        })
    sources = [{
        "sourceId": sid, "title": deps["sources"][sid]["title"],
        "organization": deps["sources"][sid]["organization"],
        "url": deps["sources"][sid]["url"],
        "scope": "general_reference_not_series_effectivity",
        "limitation": deps["sources"][sid]["limitation"],
    } for sid in sorted(source_ids)]
    context = CONTEXT[row["editorialContextKey"]]
    evidence_assessment = assess_case(case, selection, deps["qualitativeMatrix"],
                                      deps["methods"])
    require(evidence_assessment["observedSupportCount"] == 0
            and evidence_assessment["observedWeakeningCount"] == 0
            and evidence_assessment["hypothesesExcluded"] == 0
            and evidence_assessment["testsPerformed"] == 0,
            "casefile: synthetic evidence promoted into physical conclusion")
    pilot = None
    pilot_hash = None
    if row["pilotCasePath"] is not None:
        # Strict hardcoded allowlist; never resolve arbitrary user-supplied paths.
        require(row["pilotCasePath"] == "examples/777e_additives_only.json",
                "casefile: unexpected pilot path")
        pilot_src = json.loads((ROOT / row["pilotCasePath"]).read_text(encoding="utf-8"))
        require(pilot_src["caseId"] == "SIM-777E-ADDITIVES-ONLY"
                and case["reportedSignals"] == [
                    s["code"] for s in pilot_src["signals"] if s["result"] == "present"],
                "casefile: final-drive source simulation inconsistent with benchmark")
        lock = load_lock()
        pilot = investigate(pilot_src, build_consumer_index(snapshot, lock), lock)
        require(pilot["confirmedRootCause"] is None
                and pilot["mayReleaseEquipment"] is False
                and pilot["mayCreateWorkOrder"] is False
                and all(t["status"] == "not_performed"
                        for t in pilot["plannedInvestigations"])
                and {h["id"] for h in pilot["hypotheses"]}
                == {h["id"] for h in selection["hypotheses"]},
                "casefile: source pilot was promoted to an operational diagnosis")
        pilot_hash = sha(pilot_src)
    methods = deps["methods"]
    risk = context["continued"]
    return {
        "schema": "maintenance-superinteligence.technical-casefile.v1",
        "version": "1.0.0",
        "caseFileId": row["caseFileId"],
        "familyId": row["familyId"],
        "scenario": case["scenario"],
        "assetContext": {
            "asset": context["asset"], "system": context["system"],
            "realMachineIdentifier": None, "oemEffectivityVerified": False,
            "function": context["function"], "requirement": context["requirement"],
        },
        "symptom": context["symptom"],
        "observedEffect": context["effect"],
        "causalLevels": {
            "immediateMechanismsAreHypothetical": context["immediate"],
            "rootCauseInterpretation": context["root"],
            "rootCauseEstablished": False,
            "causalRelationshipsFieldValidated": False,
        },
        "operationalRisk": {
            "editorialRiskIfContinuedWithoutReview": risk,
            "quantifiedRisk": None, "machineConditionAssessed": False,
            "operationAllowed": False,
        },
        "reportedSignals": [{"value": x, "nature": "synthetic_unmeasured"}
                            for x in case["reportedSignals"]],
        "simulatedContext": list(case["contextStates"]),
        "hypotheses": [{
            "id": h["id"], "title": h["title"],
            "editorialOrder": i + 1, "status": "open_not_confirmed",
            "causalEvidenceStatus": "not_field_validated",
            "supportFromObservedPhysicalEvidence": False,
            "probability": None,
        } for i, h in enumerate(selection["hypotheses"])],
        "hypothesisComparisons": list(selection["comparisons"]),
        "qualitativeEvidence": evidence_assessment,
        "selectedQuestion": {
            "pairId": selected["selectedPairId"],
            "methodId": selected["selectedMethodId"],
            "blockingQuestion": selected["selectedNextQuestion"],
            "status": selected["selectionStatus"],
            "reason": selected["reason"],
            "recommendedAction": context["action"],
            "decisionNature": "planning_human_investigation_only",
            "executionAuthorized": False,
        },
        "methods": candidates,
        "technicalReferences": sources,
        "knowledgeGaps": list(selection["knowledgeGaps"])
                         + ([] if pilot is None else pilot["knowledgeGaps"]),
        "fieldCautions": [
            "Revisão por engenharia e controle de riscos antes de qualquer ação física.",
            "Literatura OEM por máquina, série, arranjo, revisão e procedimento não obtida.",
            "Matriz editorial não ranqueia probabilidades, custo, severidade ou sensibilidade de teste.",
            "Evidência contraditória ou ausente não autoriza descartar hipóteses.",
        ],
        "pilot": (None if pilot is None else {
            "sourceCaseId": pilot["caseId"],
            "alternativeHypothesisCount": len(pilot["hypotheses"]),
            "sourceDecision": pilot["decision"],
            "observations": pilot["observations"],
            "conflicts": pilot["conflicts"],
            "plannedInvestigations": pilot["plannedInvestigations"],
            "rootCauseConfirmed": False,
        }),
        "provenance": {
            "evidenceNature": "simulation",
            "originalFmeaSnapshotSha256": load_lock()["sha256"],
            "fmeaContentVerifiedAgainstLock": True,
            "matrixSha256": sha(deps["matrix"]),
            "qualitativeEvidenceMatrixSha256": deps["qualitativeInputSha256"],
            "methodsCatalogSha256": sha(json.loads(CATALOG_PATH.read_text(encoding="utf-8"))),
            "benchmarkManifestSha256": sha(deps["benchmark"]),
            "caseBenchmarkFixtureId": fixture["fixtureId"],
            "benchmarkInputSha256": sha(case),
            "originalPilotCaseSha256": pilot_hash,
            "reviewDossierSourceSha256": deps["gate"]["dossierFixtureSha256"],
            "discriminationRule": selected["rule"],
        },
        "reviewGates": {
            "benchmarkSyntheticRegressionsPass": True,
            "benchmarkMeasuredFieldAccuracy": False,
            "sourceGeneralNotSpecific": True,
            "technicalReviewAuthenticated": False,
            "privateDeploymentApproved": False,
            "oemSeriesVerified": False,
            "mayRunPhysicalTests": False,
            "mayCreateWorkOrder": False,
            "mayModifyECM": False,
            "mayReleaseEquipment": False,
            "mayConfirmRootCause": False,
        },
        "decision": "needs_human_review_and_discriminating_evidence",
        "approvedForOperationalUse": False,
        "confirmedComponent": None,
    }


def build_collection(fixture: dict, deps: dict, snapshot: dict) -> dict:
    cases = validate_fixture(fixture)
    result = [assemble_case(cases[k], deps, snapshot) for k in ALLOWED]
    return {
        "schema": "maintenance-superinteligence.technical-casefile-collection.v1",
        "version": "1.0.0",
        "purpose": "four_synthetic_independent_differentials",
        "sourceFixtureSha256": sha(fixture),
        "pinnedFmeaSnapshotSha256": load_lock()["sha256"],
        "cases": result, "caseCount": 4,
        "hypothesesOpen": sum(len(x["hypotheses"]) for x in result),
        "testsExecuted": 0,
        "observedSupportingEvidence": 0,
        "observedWeakeningEvidence": 0,
        "hypothesesExcluded": 0,
        "counterexamples": sum(len(p["alternativeExplanations"])
                               for c in result for p in c["qualitativeEvidence"]["comparisons"]),
        "confirmedRootCauses": 0,
        "fieldDiagnosticAccuracyMeasured": False,
        "privateDeploymentApproved": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
    }


def verify_report(report: dict, fixture: dict, deps: dict, snapshot: dict) -> dict:
    require(report == build_collection(fixture, deps, snapshot),
            "casefile: forged, reordered or modified technical report")
    return report


def render_html(collection: dict) -> str:
    require(collection.get("schema")
            == "maintenance-superinteligence.technical-casefile-collection.v1"
            and collection.get("caseCount") == 4
            and collection.get("confirmedRootCauses") == 0
            and collection.get("testsExecuted") == 0
            and collection.get("observedSupportingEvidence") == 0
            and collection.get("observedWeakeningEvidence") == 0
            and collection.get("hypothesesExcluded") == 0
            and collection.get("counterexamples") == 20
            and collection.get("privateDeploymentApproved") is False
            and collection.get("mayCreateWorkOrder") is False
            and collection.get("mayReleaseEquipment") is False
            and len(collection.get("cases", [])) == 4
            and all(c.get("approvedForOperationalUse") is False
                    and c.get("confirmedComponent") is None
                    and c.get("decision") == "needs_human_review_and_discriminating_evidence"
                    and c.get("qualitativeEvidence", {}).get("testsPerformed") == 0
                    and c.get("qualitativeEvidence", {}).get("hypothesesExcluded") == 0
                    and c.get("qualitativeEvidence", {}).get("observedSupportCount") == 0
                    and c.get("qualitativeEvidence", {}).get("observedWeakeningCount") == 0
                    and all(p.get("cannotDismissEitherHypothesis") is True
                            and p.get("observedPhysicalEvidence") is False
                            and p.get("currentEvidenceState") in {"not_measured", "contradicted", "inconclusive"}
                            and p.get("testsPerformed") == 0
                            and all(q.get("hasBeenObserved") is False
                                    and q.get("mayExcludeHypothesis") is False
                                    for q in p.get("conditionalObservations", []))
                            for p in c["qualitativeEvidence"].get("comparisons", []))
                    and c.get("reviewGates", {}).get("mayRunPhysicalTests") is False
                    and c.get("reviewGates", {}).get("mayConfirmRootCause") is False
                    and c.get("reviewGates", {}).get("mayReleaseEquipment") is False
                    and len(c.get("hypotheses", [])) >= 4
                    and all(h.get("status") == "open_not_confirmed"
                            and h.get("probability") is None
                            for h in c["hypotheses"])
                    and all(m.get("mayExecute") is False
                            and m.get("executionStatus") == "proposed_not_executed"
                            for m in c.get("methods", []))
                    for c in collection["cases"]),
            "html: technical casefile not cleared for educational-only rendering")
    e = lambda x: escape(str(x), quote=True)
    sections = []
    for c in collection["cases"]:
        hyps = "".join("<tr><td>"+e(h["id"])+"</td><td>"+e(h["title"])
                       +"</td><td>Em aberto, sem probabilidade</td></tr>"
                       for h in c["hypotheses"])
        methods = "".join("<tr><td>"+e(m["methodId"])+"</td><td>"
                          +e(m["question"])+"</td><td>"
                          +e(", ".join(m["safetyPrerequisites"]))+"</td><td>"
                          +e(", ".join(m["interpretationLimits"]))
                          +"</td></tr>" for m in c["methods"])
        comparisons = "".join(
            "<tr><td>" + e(p["pairId"]) + "</td><td>"
            + e(" / ".join(p["hypothesisIds"])) + "</td><td>"
            + e(p["currentEvidenceState"]) + "</td><td>"
            + e(" | ".join(o["conditionalReading"] + " [SE: "
                          + o["effectOnFirstIfObserved"] + " / "
                          + o["effectOnSecondIfObserved"] + "]"
                          for o in p["conditionalObservations"])) + "</td><td>"
            + e(" | ".join(a["statement"] for a in p["alternativeExplanations"]))
            + "</td><td>"
            + e(", ".join(k["key"] for k in p["contextRequirements"]
                          if k["state"] in ("unknown", "contradicted", "not_applicable"))
                or "Dados físicos ainda não medidos")
            + "</td></tr>"
            for p in c["qualitativeEvidence"]["comparisons"])
        refs = "".join("<li>"+e(x["organization"])+": "+e(x["title"])
                       +" — "+e(x["limitation"])+"</li>" for x in c["technicalReferences"])
        gaps = "".join("<li>"+e(x)+"</li>" for x in c["knowledgeGaps"])
        sections.append(
            "<section><h2>"+e(c["caseFileId"])+": "+e(c["assetContext"]["system"])+"</h2>"
            "<p><strong>Função:</strong> "+e(c["assetContext"]["function"])+"</p>"
            "<p><strong>Requisito:</strong> "+e(c["assetContext"]["requirement"])+"</p>"
            "<p><strong>Sintoma simulado:</strong> "+e(c["symptom"])+"</p>"
            "<p><strong>Efeito potencial:</strong> "+e(c["observedEffect"])+"</p>"
            "<p><strong>Causa imediata (hipotética):</strong> "
            +e(c["causalLevels"]["immediateMechanismsAreHypothetical"])+"</p>"
            "<p><strong>Causa raiz:</strong> "+e(c["causalLevels"]["rootCauseInterpretation"])+"</p>"
            "<p><strong>Risco de postergação (não quantificado):</strong> "
            +e(c["operationalRisk"]["editorialRiskIfContinuedWithoutReview"])+"</p>"
            "<h3>Hipóteses concorrentes — ordem editorial, não probabilidade</h3>"
            "<div class='scroll'><table><tr><th>ID</th><th>Alternativa</th><th>Estado</th></tr>"
            +hyps+"</table></div>"
            "<h3>Próxima pergunta de investigação</h3><p>"
            +e(c["selectedQuestion"]["blockingQuestion"])+
            " — <strong>Estado:</strong> "+e(c["selectedQuestion"]["status"])+"</p>"
            "<p><strong>Ação proposta de investigação:</strong> "
            +e(c["selectedQuestion"]["recommendedAction"])+"</p>"
            "<h3>Evidência discriminante condicional — NÃO observada</h3>"
            "<p>supports/weakens indicam somente o que um resultado hipotético poderia sugerir;"
            " indeterminado e não medido nunca descartam hipóteses.</p>"
            "<div class='scroll'><table><tr><th>Par</th><th>Hipóteses abertas</th>"
            "<th>Estado dos dados</th><th>Observações que poderiam discriminar</th>"
            "<th>Contraexemplos</th><th>Lacuna</th></tr>"
            +comparisons+"</table></div>"
            "<h3>Métodos conceituais (não executar sem revisão humana)</h3>"
            "<div class='scroll'><table><tr><th>Método</th><th>Questão</th><th>Segurança</th>"
            "<th>Limites</th></tr>"+methods+"</table></div>"
            "<h3>Lacunas de conhecimento</h3><ul>"+gaps+"</ul>"
            "<h3>Fontes técnicas gerais — não são procedimento por série</h3><ul>"+refs+"</ul>"
            "<p class='blocked'>Sem testes executados, peça condenada, OS, ajuste ECM"
            " ou liberação. Efetividade OEM e revisão real pendentes.</p></section>"
        )
    return ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none';"
            " style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            "<title>Dossiês de investigação — casos sintéticos</title>"
            "<style>body{font:15px system-ui,sans-serif;color:#252525;"
            "background:#fafafa;max-width:1180px;margin:2rem auto;padding:1rem}"
            "section{background:#fff;border:1px solid #ddd;padding:1.3rem;"
            "margin:2rem 0;border-radius:8px}table{width:100%;border-collapse:collapse}"
            "th,td{border:1px solid #ddd;padding:.6rem;text-align:left;vertical-align:top}"
            ".scroll{overflow-x:auto}.blocked{border-left:5px solid #9a2525;"
            "background:#fff3f3;padding:.7rem}li{margin:.25rem 0}</style>"
            "</head><body><h1>Dossiês integrados de investigação de manutenção</h1>"
            "<p class='blocked'><strong>SIMULAÇÃO — SEM VALIDADE DE CAMPO.</strong>"
            " Hipóteses abertas; sem diagnóstico confirmado, teste realizado ou"
            " autorização para operar. Leitura humana necessária.</p>"
            + "".join(sections) + "<footer>Conteúdo público sintético; CI"
            " verifica regressão de contratos, não acurácia mecânica.</footer>"
            "</body></html>\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args(argv)
    try:
        snapshot = validate_snapshot(args.snapshot.read_bytes(), load_lock())
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        deps = load_dependencies(snapshot)
        report = build_collection(fixture, deps, snapshot)
        serialized = json.dumps(report, ensure_ascii=False, indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True, exist_ok=True)
            args.html.write_text(render_html(report), encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected, ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"result": "rejected_fail_closed",
                          "reason": str(exc), "mayReleaseEquipment": False},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
