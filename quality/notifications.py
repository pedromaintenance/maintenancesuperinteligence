"""Ciclo 17: rubrica editorial para notificações inteiramente fictícias.

Nunca avalia validade diagnóstica, executa SAP ou certifica revisão humana.
As verificações retornam achados estruturados sem divulgar valores de entradas
adulteradas; publicação só é permitida após reconstrução do corpus canônico.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys

from connectors.fmea_public import ImportRejected, require, load_lock, validate_snapshot
from evidence.ledger import sha
from methods.library import ROOT
from casefiles.integrated import (FIXTURE_PATH as CASE_FIXTURE_PATH,
                                  load_dependencies, build_collection)
from notifications.drafts import (
    SPEC_PATH as NOTIFICATION_SPEC_PATH, build_notifications,
)

RUBRIC_PATH = ROOT / "quality/notification-rubric.v1.json"
ORACLE_PATH = ROOT / "benchmarks/notification-quality-oracle.v1.json"
CRITERION_ORDER = (
    "training_identification", "symptom_objective",
    "function_and_effect", "causality_not_confirmed",
    "alternatives_open", "missing_evidence_explicit",
    "discipline_consistent", "scope_is_investigation",
    "planning_without_invention", "risk_is_qualitative",
    "provenance_public_trace", "oem_human_safety_pending",
)
CRITICAL = {
    "training_identification", "causality_not_confirmed",
    "alternatives_open", "missing_evidence_explicit",
    "scope_is_investigation", "planning_without_invention",
    "provenance_public_trace", "oem_human_safety_pending",
}
RUBRIC_FIELDS = {"schema", "version", "mode", "sourceDraftCollection",
                 "expertValidated", "fieldAccuracyMeasured",
                 "mayIssueSapNotification", "criteria"}
CRITERION_FIELDS = {"criterionId", "title", "severity", "remediation", "checks"}
GATE_FIELDS = {
    "externalHumanReviewComplete", "oemApplicabilityVerified",
    "riskAnalysisCompleted", "safeExecutionAuthorized",
    "mayWriteToSap", "mayCreateWorkOrder", "mayOrderParts",
    "mayAlterEcm", "mayReleaseEquipment",
}
CASE_IDS = ("SIM-TECH-FD-01","SIM-TECH-HYD-01",
            "SIM-TECH-ECM-LOG-01","SIM-TECH-ECM-ACT-01")
DISCIPLINES = ("Mecânica / Lubrificação","Mecânica / Hidráulica",
               "Elétrica / Eletrônica","Elétrica / Eletrônica")
EXPECTED_CHECKS = {
    "training_identification": ["draftKind","draftId","trainingBanner"],
    "symptom_objective": ["symptom"],
    "function_and_effect": ["symptom","causalAssessment.potentialEffect"],
    "causality_not_confirmed": ["causalAssessment"],
    "alternatives_open": ["hypothesisRegister"],
    "missing_evidence_explicit": ["requestedEvidence","inspectionScope.dataState"],
    "discipline_consistent": ["planningConstraint.discipline"],
    "scope_is_investigation": ["inspectionScope"],
    "planning_without_invention": ["planningConstraint"],
    "risk_is_qualitative": ["postponementRisk"],
    "provenance_public_trace": ["provenance","decisionTrace"],
    "oem_human_safety_pending": ["reviewGates"],
}
BASELINE_GAPS = (
    ("unverified_oem_effectivity",
     "Publicação e efetividade OEM específica por série não fornecidas."),
    ("physical_evidence_not_obtained",
     "Medições e comparação física não foram realizadas."),
    ("human_review_not_authenticated",
     "Revisão por profissional qualificado ainda não realizada."),
    ("risk_of_task_not_assessed",
     "Análise de riscos para execução real ainda não realizada."),
)

def _map(obj):
    return obj if isinstance(obj,dict) else {}

def _txt(x):
    return isinstance(x,str) and bool(x.strip()) and len(x) <= 1200

def _get(obj,*path):
    for part in path:
        if not isinstance(obj,dict):
            return None
        obj=obj.get(part)
    return obj

def _safe_keys(obj,expected):
    return isinstance(obj,dict) and set(obj)==expected

def validate_rubric(obj):
    require(_safe_keys(obj,RUBRIC_FIELDS)
            and obj["schema"]=="maintenance-superinteligence.notification-quality-rubric.v1"
            and obj["version"]=="1.0.0"
            and obj["mode"]=="editorial_synthetic_document_check_only"
            and obj["sourceDraftCollection"]=="maintenance-superinteligence.notification-training-collection.v1"
            and obj["expertValidated"] is False
            and obj["fieldAccuracyMeasured"] is False
            and obj["mayIssueSapNotification"] is False
            and isinstance(obj["criteria"],list)
            and len(obj["criteria"])==len(CRITERION_ORDER),
            "quality: rubric cannot claim field certification or change criteria")
    results={}
    for i,c in enumerate(obj["criteria"]):
        cid=CRITERION_ORDER[i]
        require(_safe_keys(c,CRITERION_FIELDS)
                and c["criterionId"]==cid
                and c["severity"]==("critical" if cid in CRITICAL else "major")
                and c["checks"]==EXPECTED_CHECKS[cid]
                and _txt(c["title"]) and _txt(c["remediation"])
                and len(c["remediation"])>=40,
                "quality: missing, reordered or altered rubric criterion")
        results[cid]=c
    return results

def _checks(d,case,tree):
    symptom=_map(d.get("symptom"))
    ca=_map(d.get("causalAssessment"))
    hy=_map(d.get("hypothesisRegister"))
    ev=_map(d.get("requestedEvidence"))
    sc=_map(d.get("inspectionScope"))
    pc=_map(d.get("planningConstraint"))
    risk=_map(d.get("postponementRisk"))
    pr=_map(d.get("provenance"))
    dt=_map(d.get("decisionTrace"))
    gates=_map(d.get("reviewGates"))
    cpr=_map(case.get("provenance"))
    root=tree.get("rootNodeId")
    caseid=case.get("caseFileId")
    index=CASE_IDS.index(caseid) if caseid in CASE_IDS else -1
    required_pc_empty=("workHours","oemPressureOrWearLimits","cost",
                       "numericPriority","equipmentSerial",
                       "sapEquipmentNumber","sapNotificationNumber")
    source_methods=next((n for n in tree.get("nodes",[])
                         if n.get("nodeId")==root),{})
    findings = {
        "training_identification": (
            d.get("schema")=="maintenance-superinteligence.notification-draft.v1"
            and d.get("draftId")==f"SIM-NOTE-{index+1:03}"
            and d.get("caseFileId")==caseid
            and d.get("draftKind")=="training_only_not_sap_importable"
            and d.get("trainingBanner")=="SIMULAÇÃO EDUCACIONAL — NÃO É NOTA OU ORDEM SAP"
            and d.get("mayExportToSap") is False
            and d.get("approvedForMaintenance") is False
            and _txt(d.get("title"))
            and d.get("title","").startswith("SIMULAÇÃO - ")),
        "symptom_objective": (
            _txt(symptom.get("description"))
            and symptom.get("sourceNature")=="fictional_report_not_field_measurement"
            and symptom.get("physicallyObserved") is False
            and symptom.get("assetSystem")==_get(case,"assetContext","system")),
        "function_and_effect": (
            _txt(symptom.get("functionalRequirement"))
            and symptom.get("functionalRequirement")==_get(case,"assetContext","requirement")
            and _txt(ca.get("potentialEffect"))
            and ca.get("potentialEffect")==case.get("observedEffect")
            and symptom.get("description")==case.get("symptom")),
        "causality_not_confirmed": (
            ca.get("rootCauseStatus")=="unknown_not_established"
            and ca.get("confirmedDefect") is None
            and ca.get("immediateMechanismsAreOnlyHypotheses")
                ==_get(case,"causalLevels","immediateMechanismsAreHypothetical")
            and _get(case,"causalLevels","rootCauseEstablished") is False),
        "alternatives_open": (
            hy.get("allOpen") is True
            and hy.get("excludedCount")==0
            and hy.get("probabilitiesAssigned") is False
            and hy.get("hypothesisIds")
                ==_get(tree,"unresolvedHypothesisSet","hypothesisIds")
            and _txt(hy.get("technicalNote"))
            and len(_map(hy).get("hypothesisIds",[]))>=4),
        "missing_evidence_explicit": (
            isinstance(ev.get("items"),list)
            and len(ev.get("items",[]))>=4
            and all(_txt(x) for x in ev.get("items",[]))
            and ev.get("unresolvedContextState")==_get(source_methods,"evidenceGate","currentState")
            and ev.get("unresolvedContextState") in ("not_measured","contradicted","inconclusive")
            and sc.get("dataState")==ev.get("unresolvedContextState")
            and ev.get("presentMeasurementCount")==0
            and ev.get("comparabilityVerified") is False
            and ev.get("externalOriginalEvidenceReferences")==[]),
        "discipline_consistent": (
            index>=0 and pc.get("discipline")==DISCIPLINES[index]),
        "scope_is_investigation": (
            sc.get("activity")=="plan_human_investigation_only"
            and isinstance(sc.get("description"),str)
            and 80<=len(sc.get("description"))<=380
            and sc.get("originTreeNodeId")==root
            and sc.get("originQuestion")==source_methods.get("question")
            and sc.get("methodIds")==source_methods.get("methodIds")
            and sc.get("genericPublicSourceIds")==source_methods.get("publicSources")
            and sc.get("physicalTestScheduled") is False
            and sc.get("executed") is False
            and sc.get("requiresOemMethodReview") is True),
        "planning_without_invention": (
            all(key in pc and pc[key] is None for key in required_pc_empty)
            and pc.get("materials")==[]
            and pc.get("executionProcedures")==[]
            and pc.get("externalSafetyReviewRequired") is True
            and pc.get("externalHumanApprovalRequired") is True
            and isinstance(pc.get("reviewCriteria"),list)
            and pc.get("reviewCriteria")==_get(source_methods,"reviewCheckpoint","requiredProofs")),
        "risk_is_qualitative": (
            _txt(risk.get("qualitativeDescription"))
            and risk.get("qualitativeDescription")
                ==_get(case,"operationalRisk","editorialRiskIfContinuedWithoutReview")
            and risk.get("quantifiedRisk") is None
            and risk.get("fieldRiskAssessed") is False
            and risk.get("continuedOperationApproved") is False),
        "provenance_public_trace": (
            pr.get("casefileBenchmarkFixtureId")==cpr.get("caseBenchmarkFixtureId")
            and pr.get("qualitativeEvidenceMatrixSha256")
                ==cpr.get("qualitativeEvidenceMatrixSha256")
            and pr.get("sourceReviewDossierSha256")
                ==cpr.get("reviewDossierSourceSha256")
            and pr.get("sourceTreeQuestionId")==root
            and pr.get("claimedSeriesSpecificOemEvidence") is False
            and pr.get("provenanceAuthenticatedFromPrivateSystem") is False
            and dt.get("sourceCaseFileId")==caseid
            and dt.get("sourceTreeRootNodeId")==root
            and dt.get("currentContextState")
                ==_get(source_methods,"evidenceGate","currentState")
            and dt.get("decision")=="abstain_pending_verified_evidence"
            and dt.get("conditionalBranchTaken") is False
            and dt.get("sourceCasefileStatus")
                =="needs_human_review_and_discriminating_evidence"),
        "oem_human_safety_pending": (
            set(gates)==GATE_FIELDS
            and all(gates[k] is False for k in GATE_FIELDS)
            and _get(source_methods,"reviewCheckpoint","allProofsVerified") is False
            and tree.get("decision")=="abstain_pending_verified_evidence"
            and tree.get("mayReleaseEquipment") is False),
    }
    return findings

def assess_draft(d,case,tree,rubric):
    criteria=validate_rubric(rubric)
    require(case.get("caseFileId")==tree.get("caseFileId")
            and tree.get("caseFileId") in CASE_IDS
            and _get(tree,"unresolvedHypothesisSet","allOpen") is True
            and tree.get("testsExecuted")==0
            and tree.get("mayCreateWorkOrder") is False,
            "quality: source case/tree not permitted for documentary training")
    check=_checks(d,case,tree)
    findings=[]
    for cid in CRITERION_ORDER:
        c=criteria[cid]
        ok=check[cid] is True
        findings.append({
            "criterionId":cid,
            "criterionTitle":c["title"],
            "severity":c["severity"],
            "status":"met" if ok else "needs_revision",
            "affectedFields":list(c["checks"]),
            "explanation":(
                "Critério cumprido apenas no exemplar sintético; não constitui validação de campo."
                if ok else "Informações incompatíveis, incompletas ou não verificadas no exercício."),
            "correctiveDocumentationAction":c["remediation"],
            "humanFindingAuthenticated":False,
        })
    failed=[x for x in findings if x["status"]!="met"]
    blocked=any(x["severity"]=="critical" for x in failed)
    status=("blocked_unsafe_claims" if blocked else
            "needs_documentary_revision" if failed else
            "adequate_for_synthetic_training")
    return {
        "schema":"maintenance-superinteligence.notification-quality-assessment.v1",
        "draftId":d.get("draftId"),
        "caseFileId":case["caseFileId"],
        "status":status,
        "criterionCount":len(findings),
        "criteriaMet":len(findings)-len(failed),
        "criteriaNeedsRevision":len(failed),
        "findings":findings,
        "missingInformation":[
            {"criterionId":x["criterionId"],
             "sourceFieldNames":x["affectedFields"],
             "documentationGap":"review_synthetic_document_only",
             "requiredAction":x["correctiveDocumentationAction"]}
            for x in failed],
        "scopeSafetyFindings":[
            {"criterionId":x["criterionId"],
             "severity":"critical",
             "decision":"blocked_no_execution",
             "needsHumanVerification":True}
            for x in failed if x["severity"]=="critical"],
        "externalEvidenceGaps":[
            {"gapId":k,"description":v,"evidenceReceived":False,
             "remainsBlockingForOperationalUse":True}
            for k,v in BASELINE_GAPS],
        "humanEditorialReview":{
            "engineeringExpertAuthenticated":False,
            "independentReviewerAuthenticated":False,
            "interRaterReliabilityMeasured":False,
            "documentAcceptedByRealReviewer":False,
            "fieldDiagnosticValidityEstablished":False,
        },
        "sourceTreeRootNodeId":tree["rootNodeId"],
        "externalEvidenceAvailable":False,
        "mayBeUsedForFieldMaintenance":False,
        "mayCreateSapNotification":False,
        "mayReleaseEquipment":False,
    }

def build_report(collection,casefiles,rubric,oracle=None):
    validate_rubric(rubric)
    require(collection.get("schema")
            =="maintenance-superinteligence.notification-training-collection.v1"
            and collection.get("draftCount")==4
            and collection.get("realNotificationsCreated")==0
            and collection.get("mayConnectToSap") is False
            and [d.get("draftId") for d in collection.get("drafts",[])]
                ==[f"SIM-NOTE-{n:03}" for n in range(1,5)]
            and casefiles.get("schema")
                =="maintenance-superinteligence.technical-casefile-collection.v1"
            and casefiles.get("caseCount")==4,
            "quality: unknown document collection, source or SAP authorization")
    trees=casefiles["investigationTrees"]["trees"]
    cases=casefiles["cases"]
    docs=collection["drafts"]
    result=[assess_draft(d,c,t,rubric) for d,c,t in zip(docs,cases,trees)]
    require(all(x["status"]=="adequate_for_synthetic_training" for x in result),
            "quality: canonical synthetic documents no longer meet editorial rubric")
    output={
        "schema":"maintenance-superinteligence.notification-quality-report.v1",
        "version":"1.0.0",
        "mode":"synthetic_document_regression_only",
        "rubricSha256":sha(rubric),
        "sourceDraftCollectionSha256":sha(collection),
        "sourceCasefilesSha256":sha(casefiles),
        "publicFmeaSnapshotSha256":casefiles["pinnedFmeaSnapshotSha256"],
        "qualitativeMatrixSha256":cases[0]["provenance"]["qualitativeEvidenceMatrixSha256"],
        "sourceTreeSpecSha256":casefiles["investigationTrees"]["specSha256"],
        "sourceReviewDossierSha256":cases[0]["provenance"]["reviewDossierSourceSha256"],
        "assessments":result,
        "assessedDraftCount":len(result),
        "documentsAdequateForSyntheticTraining":len(result),
        "documentsApprovedForField":0,
        "realNotificationsCreated":0,
        "physicalTestsExecuted":0,
        "interRaterReliabilityMeasured":False,
        "independentRealExpertReviewComplete":False,
        "mayCreateSapNotification":False,
        "mayReleaseEquipment":False,
    }
    if oracle is not None:
        validate_oracle(oracle,output,collection,casefiles,rubric)
        output["oracleSha256"]=sha(oracle)
    return output

def _apply_mutation(d,path,value):
    parts=path.split(".")
    if parts == ["mayExportToSap"]:
        require("mayExportToSap" in d and value is True,
                "quality oracle: malformed simulated export permission")
        d["mayExportToSap"] = value
        return
    require(len(parts)==2 and isinstance(d.get(parts[0]),dict)
            and parts[1] in d[parts[0]],
            "quality oracle: unknown mutation key")
    d[parts[0]][parts[1]]=value

def validate_oracle(oracle,report,collection,casefiles,rubric):
    required={"schema","version","mode","rubricSource","sourceDrafts",
              "fieldValidityEstablished","interRaterReliabilityMeasured",
              "baseline","adversarial"}
    require(isinstance(oracle,dict) and set(oracle)==required
            and oracle["schema"]=="maintenance-superinteligence.notification-quality-oracle.v1"
            and oracle["version"]=="1.0.0"
            and oracle["mode"]=="independent_editorial_regression_not_expert_validation"
            and oracle["rubricSource"]=="quality/notification-rubric.v1.json"
            and oracle["sourceDrafts"]=="notifications/training-spec.v1.json"
            and oracle["fieldValidityEstablished"] is False
            and oracle["interRaterReliabilityMeasured"] is False
            and isinstance(oracle["baseline"],list) and len(oracle["baseline"])==4
            and isinstance(oracle["adversarial"],list) and len(oracle["adversarial"])==14,
            "quality oracle: unknown benchmark, missing scenario or false human validity")
    got=report["assessments"]
    for i,baseline in enumerate(oracle["baseline"]):
        require(set(baseline)=={"draftId","expectedStatus","expectedMet",
                               "expectedFailed","realMaintenanceApproved"}
                and baseline["draftId"]==f"SIM-NOTE-{i+1:03}"
                and baseline["expectedStatus"]=="adequate_for_synthetic_training"
                and baseline["expectedMet"]==12
                and baseline["expectedFailed"]==0
                and baseline["realMaintenanceApproved"] is False
                and got[i]["status"]==baseline["expectedStatus"]
                and got[i]["criteriaMet"]==baseline["expectedMet"],
                "quality oracle: baseline drift/false approval")
    names=set()
    for scenario in oracle["adversarial"]:
        require(set(scenario)=={"scenarioId","draftId","fieldPath","replacement",
                               "expectedCriterion","expectedStatus","rootCauseProven",
                               "sapAuthorizationGranted"}
                and scenario["scenarioId"] not in names
                and scenario["draftId"] in [d["draftId"] for d in collection["drafts"]]
                and scenario["expectedCriterion"] in CRITERION_ORDER
                and scenario["expectedStatus"] in {
                    "blocked_unsafe_claims","needs_documentary_revision"}
                and scenario["rootCauseProven"] is False
                and scenario["sapAuthorizationGranted"] is False,
                "quality oracle: invalid negative regression scenario")
        names.add(scenario["scenarioId"])
        index=int(scenario["draftId"][-1])-1
        changed=json.loads(json.dumps(collection["drafts"][index]))
        _apply_mutation(changed,scenario["fieldPath"],scenario["replacement"])
        assessment=assess_draft(changed,casefiles["cases"][index],
                                casefiles["investigationTrees"]["trees"][index],rubric)
        require(assessment["status"]==scenario["expectedStatus"]
                and any(f["criterionId"]==scenario["expectedCriterion"]
                        and f["status"]=="needs_revision"
                        for f in assessment["findings"]),
                "quality oracle: adverse scenario not caught or classification changed")
    return True

def verify_report(report,collection,casefiles,rubric,oracle):
    require(report==build_report(collection,casefiles,rubric,oracle),
            "quality report: forged assessment, rubric, source or approval")
    return report

def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.notification-quality-report.v1"
            and report.get("assessedDraftCount")==4
            and report.get("documentsAdequateForSyntheticTraining")==4
            and report.get("documentsApprovedForField")==0
            and report.get("realNotificationsCreated")==0
            and report.get("physicalTestsExecuted")==0
            and report.get("interRaterReliabilityMeasured") is False
            and report.get("independentRealExpertReviewComplete") is False
            and report.get("mayCreateSapNotification") is False
            and report.get("mayReleaseEquipment") is False
            and len(report.get("assessments",[]))==4
            and all(a.get("status")=="adequate_for_synthetic_training"
                    and a.get("criterionCount")==12
                    and a.get("criteriaMet")==12
                    and a.get("criteriaNeedsRevision")==0
                    and a.get("externalEvidenceAvailable") is False
                    and a.get("mayBeUsedForFieldMaintenance") is False
                    and a.get("mayCreateSapNotification") is False
                    and a.get("mayReleaseEquipment") is False
                    and all(v is False for v in a.get("humanEditorialReview",{}).values())
                    and all(f.get("status")=="met"
                            and f.get("humanFindingAuthenticated") is False
                            for f in a.get("findings",[]))
                    and all(g.get("evidenceReceived") is False
                            and g.get("remainsBlockingForOperationalUse") is True
                            for g in a.get("externalEvidenceGaps",[]))
                    for a in report["assessments"]),
            "quality HTML: report could misrepresent field approval or confidence")
    e=lambda x:escape(str(x),quote=True)
    cards=[]
    for a in report["assessments"]:
        rows="".join("<tr><td>"+e(f["criterionId"])+"</td><td>"
                     +e(f["criterionTitle"])+"</td><td>"+e(f["status"])
                     +"</td></tr>" for f in a["findings"])
        gaps="".join("<li>"+e(g["description"])+"</li>"
                     for g in a["externalEvidenceGaps"])
        cards.append("<section><h2>"+e(a["draftId"])+": "
                     +e(a["status"])+"</h2><p>Critérios documentais cumpridos: "
                     +e(a["criteriaMet"])+"/"+e(a["criterionCount"])
                     +" — apenas neste exercício.</p><table><thead><tr>"
                     "<th>Critério</th><th>Descrição</th><th>Resultado</th>"
                     "</tr></thead><tbody>"+rows+"</tbody></table>"
                     "<h3>Evidências externas que continuam faltando</h3><ul>"
                     +gaps+"</ul><p class='blocked'>ABSTER-SE de diagnóstico"
                     " ou intervenção real. Nenhum revisor autenticado.</p></section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            + "form-action &apos;none&apos;" + '"><title>Rubrica de notificações sintéticas</title>'
            '<style>body{font:15px system-ui,sans-serif;max-width:1180px;margin:2rem auto;'
            'padding:1rem;background:#fafafa;color:#282828}section{border:1px solid #ddd;'
            'background:white;margin:1.4rem 0;padding:1.1rem}table{border-collapse:collapse;'
            'width:100%}th,td{border:1px solid #ddd;text-align:left;padding:.6rem}'
            '.blocked{border-left:5px solid #a22;background:#fff1f1;padding:1rem}'
            '</style></head><body><h1>Qualidade documental — SIMULAÇÃO</h1>'
            '<p class="blocked">Critérios editoriais aprovados NÃO equivalem a'
            ' diagnóstico, nota SAP, revisão de engenharia nem liberação operacional.</p>'
            + "".join(cards)
            + '<footer>Dados fictícios e fontes públicas: sem JS, login, formulário'
              ' ou integração corporativa.</footer></body></html>\n')

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--drafts",type=Path,required=True)
    parser.add_argument("--snapshot",type=Path,required=True)
    parser.add_argument("--rubric",type=Path,default=RUBRIC_PATH)
    parser.add_argument("--oracle",type=Path,default=ORACLE_PATH)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    try:
        submitted_cases=json.loads(args.source.read_text(encoding="utf-8"))
        submitted_drafts=json.loads(args.drafts.read_text(encoding="utf-8"))
        rubric=json.loads(args.rubric.read_text(encoding="utf-8"))
        oracle=json.loads(args.oracle.read_text(encoding="utf-8"))
        require(rubric==json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
                and oracle==json.loads(ORACLE_PATH.read_text(encoding="utf-8")),
                "quality: external rubric/oracle modification not reviewed")
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        dependencies=load_dependencies(snapshot)
        fixture=json.loads(CASE_FIXTURE_PATH.read_text(encoding="utf-8"))
        canonical_cases=build_collection(fixture,dependencies,snapshot)
        notif_spec=json.loads(NOTIFICATION_SPEC_PATH.read_text(encoding="utf-8"))
        canonical_drafts=build_notifications(notif_spec,canonical_cases["cases"],
                                             canonical_cases["investigationTrees"])
        require(submitted_cases==canonical_cases and submitted_drafts==canonical_drafts,
                "quality: noncanonical or private draft/source corpus")
        report=build_report(canonical_drafts,canonical_cases,rubric,oracle)
        serialized=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(serialized,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(report),encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected, ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayCreateSapNotification":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
