"""Ciclo 16 — rascunhos de NOTIFICAÇÃO DIDÁTICA, nunca SAP PM.

Consome SOMENTE quatro casos públicos sintéticos validados e suas árvores.
Não produz instrução de execução, peças/HH, notas reais, OS ou liberação.
"""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
import sys

from connectors.fmea_public import ImportRejected, require, load_lock, validate_snapshot
from casefiles.integrated import (FIXTURE_PATH as CASE_FIXTURE_PATH,
                                  load_dependencies, build_collection)
from evidence.ledger import sha
from methods.library import ROOT

SPEC_PATH = ROOT / "notifications/training-spec.v1.json"
CASE_IDS = ("SIM-TECH-FD-01", "SIM-TECH-HYD-01",
            "SIM-TECH-ECM-LOG-01", "SIM-TECH-ECM-ACT-01")
ROOT_KEYS = {"schema","version","mode","sourceTree","sourceCases",
             "sapIntegrationEnabled","operationalDispatchEnabled","entries"}
ENTRY_KEYS = {"caseFileId","draftId","title","discipline","investigationScope",
              "technicalNote","fieldObserved","actionPerformed",
              "mayIssueRealNotification"}
DENIAL_KEYS = ("fieldObserved","actionPerformed","mayIssueRealNotification")
GATE_KEYS = ("externalHumanReviewComplete","oemApplicabilityVerified",
             "riskAnalysisCompleted","safeExecutionAuthorized",
             "mayWriteToSap","mayCreateWorkOrder","mayOrderParts",
             "mayAlterEcm","mayReleaseEquipment")

def _exact(data, keys, where):
    require(isinstance(data,dict) and set(data) == keys,
            f"notification: {where}: missing or untrusted fields")
    return data

def validate_spec(spec, casefiles):
    s=_exact(spec,ROOT_KEYS,"training spec")
    require(s["schema"]=="maintenance-superinteligence.notification-training-spec.v1"
            and s["version"]=="1.0.0"
            and s["mode"]=="public_synthetic_training_only"
            and s["sourceTree"]=="trees/spec.v1.json"
            and s["sourceCases"]=="casefiles/technical-cases.v1.json"
            and s["sapIntegrationEnabled"] is False
            and s["operationalDispatchEnabled"] is False,
            "notification: source or authorization spoofed")
    require(isinstance(s["entries"],list) and len(s["entries"])==4
            and isinstance(casefiles,list) and len(casefiles)==4
            and [c["caseFileId"] for c in casefiles]==list(CASE_IDS),
            "notification: exactly four fixed cases are required")
    result={}
    for idx,row in enumerate(s["entries"],1):
        _exact(row,ENTRY_KEYS,"entry")
        cid=row["caseFileId"]
        require(cid==CASE_IDS[idx-1] and cid not in result
                and row["draftId"]==f"SIM-NOTE-{idx:03}"
                and isinstance(row["title"],str)
                and 15<=len(row["title"])<=40
                and row["title"].startswith("SIMULAÇÃO - ")
                and row["discipline"] in ("Mecânica / Lubrificação",
                                          "Mecânica / Hidráulica",
                                          "Elétrica / Eletrônica")
                and isinstance(row["investigationScope"],str)
                and 80<=len(row["investigationScope"])<=380
                and isinstance(row["technicalNote"],str)
                and 60<=len(row["technicalNote"])<=300
                and all(row[key] is False for key in DENIAL_KEYS),
                "notification: invalid synthetic title, discipline, scope or performed action")
        if cid=="SIM-TECH-FD-01":
            require(row["discipline"]=="Mecânica / Lubrificação",
                    "notification: incorrect discipline")
        elif cid=="SIM-TECH-HYD-01":
            require(row["discipline"]=="Mecânica / Hidráulica",
                    "notification: incorrect discipline")
        else:
            require(row["discipline"]=="Elétrica / Eletrônica",
                    "notification: incorrect discipline")
        result[cid]=row
    return result

def assemble_draft(case,tree,editorial):
    cid=case["caseFileId"]
    require(cid==tree["caseFileId"]
            and tree["decision"]=="abstain_pending_verified_evidence"
            and tree["testsExecuted"]==0
            and tree["mayCreateWorkOrder"] is False
            and tree["mayModifyECM"] is False
            and tree["mayReleaseEquipment"] is False
            and tree["unresolvedHypothesisSet"]["allOpen"] is True
            and tree["unresolvedHypothesisSet"]["hypothesesExcluded"]==0
            and case["approvedForOperationalUse"] is False
            and case["confirmedComponent"] is None
            and case["assetContext"]["realMachineIdentifier"] is None
            and case["assetContext"]["oemEffectivityVerified"] is False
            and case["causalLevels"]["rootCauseEstablished"] is False
            and case["operationalRisk"]["quantifiedRisk"] is None
            and all(h["status"]=="open_not_confirmed" and h["probability"] is None
                    for h in case["hypotheses"]),
            "notification: physical result, OEM authorization or causal confirmation")
    root=tree["rootNodeId"]
    matches=[n for n in tree["nodes"] if n["nodeId"]==root]
    require(len(matches)==1, "notification: unresolved decision-tree root")
    node=matches[0]
    gate=node["evidenceGate"]
    checkpoint=node["reviewCheckpoint"]
    require(gate["currentState"] in {"not_measured","contradicted","inconclusive"}
            and gate["mayDiscardHypothesis"] is False
            and gate["doesNotTakeConditionalBranch"] is True
            and checkpoint["allProofsVerified"] is False
            and checkpoint["humanReviewAuthenticated"] is False
            and checkpoint["oemEffectivityVerified"] is False
            and checkpoint["physicalMethodAuthorized"] is False
            and all(x["observed"] is False for x in node["conditionalBranches"]),
            "notification: evidence gap was promoted to a measured result")
    evidence_requests = [
        "Identificar corretamente produto, configuração e histórico aplicável no ambiente autorizado.",
        "Reconciliar metadados contraditórios ou ausentes antes de interpretar condição.",
        "Obter resultado físico comparável somente por método autorizado e seguro.",
        "Verificar publicação OEM, revisão e efetividade para arranjo e máquina reais fora do repositório público.",
    ]
    requires=[x for x in checkpoint["requiredProofs"]]
    return {
        "schema":"maintenance-superinteligence.notification-draft.v1",
        "version":"1.0.0",
        "draftId":editorial["draftId"],"caseFileId":cid,
        "draftKind":"training_only_not_sap_importable",
        "title":editorial["title"],
        "symptom":{
            "description":case["symptom"],
            "sourceNature":"fictional_report_not_field_measurement",
            "physicallyObserved":False,
            "assetSystem":case["assetContext"]["system"],
            "functionalRequirement":case["assetContext"]["requirement"],
        },
        "causalAssessment":{
            "potentialEffect":case["observedEffect"],
            "immediateMechanismsAreOnlyHypotheses":
                case["causalLevels"]["immediateMechanismsAreHypothetical"],
            "rootCauseStatus":"unknown_not_established",
            "confirmedDefect":None,
        },
        "hypothesisRegister":{
            "hypothesisIds":list(tree["unresolvedHypothesisSet"]["hypothesisIds"]),
            "allOpen":True,"excludedCount":0,
            "probabilitiesAssigned":False,
            "technicalNote":editorial["technicalNote"],
        },
        "inspectionScope":{
            "activity":"plan_human_investigation_only",
            "description":editorial["investigationScope"],
            "originTreeNodeId":root,
            "originQuestion":node["question"],
            "methodIds":list(node["methodIds"]),
            "genericPublicSourceIds":list(node["publicSources"]),
            "dataState":gate["currentState"],
            "physicalTestScheduled":False,
            "executed":False,
            "requiresOemMethodReview":True,
        },
        "requestedEvidence":{
            "items":evidence_requests,
            "unresolvedContextState":gate["currentState"],
            "presentMeasurementCount":0,
            "comparabilityVerified":False,
            "externalOriginalEvidenceReferences":[],
        },
        "planningConstraint":{
            "discipline":editorial["discipline"],
            "workHours":None,"materials":[],
            "oemPressureOrWearLimits":None,"cost":None,
            "numericPriority":None,"equipmentSerial":None,
            "sapEquipmentNumber":None,"sapNotificationNumber":None,
            "executionProcedures":[],
            "externalSafetyReviewRequired":True,
            "externalHumanApprovalRequired":True,
            "reviewCriteria":requires,
        },
        "postponementRisk":{
            "qualitativeDescription":
                case["operationalRisk"]["editorialRiskIfContinuedWithoutReview"],
            "quantifiedRisk":None,
            "fieldRiskAssessed":False,
            "continuedOperationApproved":False,
        },
        "decisionTrace":{
            "sourceCaseFileId":cid,
            "sourceTreeRootNodeId":root,
            "currentContextState":gate["currentState"],
            "decision":"abstain_pending_verified_evidence",
            "conditionalBranchTaken":False,
            "sourceCasefileStatus":case["decision"],
        },
        "provenance":{
            "casefileBenchmarkFixtureId":
                case["provenance"]["caseBenchmarkFixtureId"],
            "qualitativeEvidenceMatrixSha256":
                case["provenance"]["qualitativeEvidenceMatrixSha256"],
            "sourceReviewDossierSha256":
                case["provenance"]["reviewDossierSourceSha256"],
            "sourceTreeQuestionId":root,
            "claimedSeriesSpecificOemEvidence":False,
            "provenanceAuthenticatedFromPrivateSystem":False,
        },
        "reviewGates":dict.fromkeys(GATE_KEYS, False),
        "trainingBanner":"SIMULAÇÃO EDUCACIONAL — NÃO É NOTA OU ORDEM SAP",
        "mayExportToSap":False,
        "approvedForMaintenance":False,
    }

def build_notifications(spec,casefiles,tree_bundle):
    entries=validate_spec(spec,casefiles)
    require(tree_bundle["schema"]=="maintenance-superinteligence.investigation-tree-collection.v1"
            and tree_bundle["treeCount"]==4
            and tree_bundle["nodeCount"]==13
            and tree_bundle["physicalTestsExecuted"]==0
            and tree_bundle["hypothesesExcluded"]==0
            and tree_bundle["operationalAuthorization"] is False,
            "notification: decision-tree collection is not a permitted source")
    trees=tree_bundle["trees"]
    require([t["caseFileId"] for t in trees]==list(CASE_IDS),
            "notification: tree-to-case sequence not aligned")
    drafts=[assemble_draft(c,t,entries[c["caseFileId"]])
            for c,t in zip(casefiles,trees)]
    return {
        "schema":"maintenance-superinteligence.notification-training-collection.v1",
        "version":"1.0.0","mode":"public_synthetic_training_only",
        "specSha256":sha(spec),"sourceTreesSha256":sha(tree_bundle),
        "drafts":drafts,"draftCount":4,
        "allHypothesesRemainOpen":True,
        "realNotificationsCreated":0,"workOrdersCreated":0,
        "physicalTestsExecuted":0,
        "mayConnectToSap":False,"mayReleaseEquipment":False,
    }

def verify_notifications(report,spec,cases,trees):
    require(report == build_notifications(spec,cases,trees),
            "notification: altered document, scope, authority or source trace")
    return report

def render_html(collection):
    require(collection.get("schema")
            =="maintenance-superinteligence.notification-training-collection.v1"
            and collection.get("draftCount")==4
            and collection.get("realNotificationsCreated")==0
            and collection.get("workOrdersCreated")==0
            and collection.get("physicalTestsExecuted")==0
            and collection.get("allHypothesesRemainOpen") is True
            and collection.get("mayConnectToSap") is False
            and collection.get("mayReleaseEquipment") is False,
            "notification HTML: unauthorized status or operational transfer")
    drafts=collection.get("drafts",[])
    require(len(drafts)==4 and
            [d.get("draftId") for d in drafts]==[
                f"SIM-NOTE-{i:03}" for i in range(1,5)],
            "notification HTML: altered training documents")
    for d in drafts:
        require(d.get("trainingBanner")
                =="SIMULAÇÃO EDUCACIONAL — NÃO É NOTA OU ORDEM SAP"
                and d.get("approvedForMaintenance") is False
                and d.get("mayExportToSap") is False
                and d.get("causalAssessment",{}).get("confirmedDefect") is None
                and d.get("hypothesisRegister",{}).get("allOpen") is True
                and d.get("inspectionScope",{}).get("executed") is False
                and d.get("inspectionScope",{}).get("physicalTestScheduled") is False
                and d.get("requestedEvidence",{}).get("presentMeasurementCount")==0
                and all(x is False for x in d.get("reviewGates",{}).values())
                and d.get("planningConstraint",{}).get("workHours") is None
                and d.get("planningConstraint",{}).get("numericPriority") is None
                and d.get("planningConstraint",{}).get("materials")==[]
                and d.get("planningConstraint",{}).get("sapNotificationNumber") is None,
                "notification HTML: counterfeit authority, measurements or planning")
    e=lambda x:escape(str(x),quote=True)
    cards=[]
    for d in drafts:
        hypotheses="; ".join(d["hypothesisRegister"]["hypothesisIds"])
        evidence="".join("<li>"+e(x)+"</li>"
                         for x in d["requestedEvidence"]["items"])
        cards.append("<section><h2>"+e(d["title"])+"</h2>"
                     "<p><strong>Identificação fictícia:</strong> "+e(d["draftId"])+"</p>"
                     "<p><strong>Disciplina:</strong> "+e(d["planningConstraint"]["discipline"])+"</p>"
                     "<p><strong>Sintoma relatado (fictício):</strong> "
                     +e(d["symptom"]["description"])+"</p>"
                     "<p><strong>Função/requisito:</strong> "
                     +e(d["symptom"]["functionalRequirement"])+"</p>"
                     "<p><strong>Efeito possível:</strong> "
                     +e(d["causalAssessment"]["potentialEffect"])+"</p>"
                     "<p><strong>Hipóteses abertas:</strong> "+e(hypotheses)+"</p>"
                     "<p><strong>Escopo delimitado — apenas investigação:</strong> "
                     +e(d["inspectionScope"]["description"])+"</p>"
                     "<p><strong>Pergunta vinculada:</strong> "
                     +e(d["inspectionScope"]["originTreeNodeId"])+" — "
                     +e(d["inspectionScope"]["originQuestion"])+"</p>"
                     "<h3>Evidências necessárias</h3><ul>"+evidence+"</ul>"
                     "<p><strong>Risco qualitativo de postergação:</strong> "
                     +e(d["postponementRisk"]["qualitativeDescription"])+"</p>"
                     "<p class='blocked'>Abstenção. Causa raiz não estabelecida, "
                     "método OEM não homologado e revisão humana pendente.</p>"
                     "</section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            + "form-action &apos;none&apos;" + '"><title>Notas didáticas de manutenção</title>'
            '<style>body{font:15px system-ui,sans-serif;background:#fafafa;'
            'max-width:1080px;margin:2rem auto;padding:1rem;color:#252525}'
            'section{padding:1.2rem;background:white;border:1px solid #ddd;'
            'margin:1rem 0;border-radius:7px}.blocked{border-left:5px solid #a22;'
            'padding:.8rem;background:#fff1f1}</style></head><body>'
            '<h1>Rascunhos didáticos — não registrar no SAP</h1>'
            '<p class="blocked">SIMULAÇÃO EDUCACIONAL. Não contém medições reais,'
            ' plano de execução, peças, HH ou autorização operacional.</p>'
            + "".join(cards)
            + '<footer>Gerado offline para treinamento; sem interface SAP,'
              ' JavaScript, formulário ou dados corporativos.</footer></body></html>\n')

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True,
                        help="JSON sintético de casefiles do Ciclo 15")
    parser.add_argument("--snapshot",type=Path,required=True,
                        help="Snapshot FMEA público fixado por SHA-256")
    parser.add_argument("--spec",type=Path,default=SPEC_PATH)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    try:
        source=json.loads(args.source.read_text(encoding="utf-8"))
        spec=json.loads(args.spec.read_text(encoding="utf-8"))
        # Rebuild trusted public corpus; never accept arbitrary "source" prose.
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        deps=load_dependencies(snapshot)
        fixture=json.loads(CASE_FIXTURE_PATH.read_text(encoding="utf-8"))
        canonical=build_collection(fixture,deps,snapshot)
        require(source==canonical,
                "notification: untrusted or altered external casefile corpus")
        require(spec==json.loads(SPEC_PATH.read_text(encoding="utf-8")),
                "notification: training text differs from reviewed project specimen")
        require(source["schema"]
                =="maintenance-superinteligence.technical-casefile-collection.v1"
                and source["caseCount"]==4
                and source["testsExecuted"]==0
                and source["confirmedRootCauses"]==0
                and source["mayCreateWorkOrder"] is False
                and source["mayReleaseEquipment"] is False,
                "notification: source casefile approval claimed")
        result=build_notifications(spec,source["cases"],source["investigationTrees"])
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",
                                   encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(result),encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayConnectToSap":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
