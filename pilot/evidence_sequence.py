"""Ciclo 21: sequenciamento TOPOLÓGICO de requisitos sintéticos, nunca implantação.

Grafo e entregas são apenas contratos para futuras áreas responsáveis.
Nenhum acesso, credencial, OEM, SAP, ECM, ordem ou decisão GO.
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
from pilot.go_nogo import PACKAGE_PATH as GNG_PACKAGE, build_report as build_gng
from pilot.readiness import FIXTURE_PATH as READINESS_FIXTURE, build_report as build_readiness
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_FIXTURE, build_report as build_editorial
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as build_quality
from notifications.drafts import SPEC_PATH as NOTE_SPEC, build_notifications
from casefiles.integrated import FIXTURE_PATH as CASE_FIXTURE, load_dependencies, build_collection

SPEC_PATH=ROOT/"pilot/evidence-sequencing.v1.json"
OWNERS=("IT","InformationSecurity","Engineering","Legal","MaintenanceManagement")
PHASES=("P1-governance-foundations","P2-identity-security","P3-legal-evidence",
        "P4-oem-effectivity","P5-isolation","P6-external-acceptance",
        "P7-feasibility")
PHASE_CONTROLS=(
    ("privacy-retention","equipment-configuration"),
    ("identity-proof","competence","conflict-screen","version-lock",
     "two-independent-reviews","signed-decision","trusted-audit","revocation-reopen"),
    ("evidence-legitimacy",),
    ("oem-effectivity",),
    ("operational-firewall",),
    (),()
)
SPEC_KEYS={"schema","version","mode","sourcePackage","realPilotStarted",
           "realStakeholderApprovals","daysPlanned","costPlanned","workHoursPlanned",
           "phases","externalHandoffs","proofRequests",
           "adversarialReviewScenarios","policy"}
PHASE_KEYS={"phaseId","title","controlIds","exitCriteria",
            "phaseState","mayStartInRealEnvironment"}
HANDOFF_KEYS={"owner","packetId","requestedEvidenceIds","referenceOnly",
              "realReceiptVerified","signoffEvidence","approvalNotGranted"}
PROOF_KEYS={"controlId","expectedEvidenceId","owner","minimumAcceptanceCriteria",
            "dependentOn","submissionState","reviewerVerified",
            "documentRevisionCurrent","originAuthorized","licenseAndPrivacyCleared",
            "mayBypass"}
THREAT_KEYS={"scenarioId","threatId","requiredControlIds","rejection",
             "actualIncidentConfirmed","remediationClosed"}
POLICY_KEYS={"allowedDecision","canSubmitRealEvidence","canTransmitSap",
             "canAccessEcm","canReleaseEquipment","interRaterResultsAvailable"}
SAFETY_FIELDS=("realPilotStarted","realStakeholderApprovals")
PHASE_LABELS=(
    "Governança, configuração e minimização",
    "Identidade, competência e segurança",
    "Legitimidade de fontes e dados",
    "Efetividade documental e configuração OEM",
    "Segregação operacional e barreiras",
    "Aceite multidisciplinar independente",
    "Decisão de viabilidade de futuro piloto",
)
EXPECTED_EXIT=(
    "Políticas e configuração precisam ser verificadas em ambiente privado; sem aceite simulado.",
    "Identidade única, competência, segregação e trilha externa requerem provas reais.",
    "Licenças e permissões de evidência precisam de parecer jurídico independente.",
    "O fabricante, a publicação, a revisão e a efetividade por arranjo/série devem ser demonstrados.",
    "Sistema privado deve impedir por padrão SAP, ECM, pedidos e liberação de equipamento.",
    "TI, Segurança, Engenharia, Jurídico e Gestão devem emitir pareceres autenticados fora deste repositório.",
    "Somente processo corporativo privado pode avaliar viabilidade; aqui o resultado é sempre NO GO.",
)

def exact(obj, keys, where):
    require(isinstance(obj,dict) and set(obj)==keys,
            f"sequencing: unknown or missing {where} fields")
    return obj

def check_no_go(report):
    require(report.get("schema")=="maintenance-superinteligence.go-nogo-report.v1"
            and report.get("decision")=="no_go"
            and report.get("evidencePackageCount")==13
            and report.get("verifiedEvidenceCount")==0
            and report.get("stakeholderCount")==5
            and report.get("verifiedSignoffs")==0
            and report.get("findingCount")==10
            and report.get("verifiedRemediations")==0
            and report.get("realGoDecisionSigned") is False
            and report.get("realPilotExecuted") is False
            and all(v is False for v in report.get("acceptanceGates",{}).values())
            and all(v is False for v in report.get("noOperationalAuthority",{}).values()),
            "sequencing: only fully blocked canonical no-go input allowed")

def _graph(controls):
    require(isinstance(controls,list) and len(controls)==13,
            "sequencing: incomplete control dependency graph")
    ids=[c.get("controlId") for c in controls]
    require(len(set(ids))==13,"sequencing: duplicate controls")
    keys=set(ids)
    depends={}
    for c in controls:
        exact(c,{"controlId","predecessors","allPrerequisitesVerified",
                 "permissionToProceed"},"dependency")
        parent=c["predecessors"]
        require(isinstance(parent,list) and len(parent)==len(set(parent))
                and all(p in keys and p!=c["controlId"] for p in parent)
                and c["allPrerequisitesVerified"] is False
                and c["permissionToProceed"] is False,
                "sequencing: forged prerequisite or cyclic self-link")
        depends[c["controlId"]]=tuple(parent)
    return ids, depends

def topological_sequence(controls, phase_ids=None):
    """Kahn ordering; stage IDs break ties, never durations or likelihood."""
    ids, pred=_graph(controls)
    index={v:i for i,v in enumerate(ids)}
    if phase_ids is None:
        phase_ids={v:0 for v in ids}
    require(set(phase_ids)==set(ids),"sequencing: incomplete phase map")
    done=set()
    sequence=[]
    while len(done)<len(ids):
        candidates=[k for k in ids if k not in done
                    and all(parent in done for parent in pred[k])]
        require(candidates,"sequencing: cycle or unresolved prerequisite")
        choose=min(candidates,key=lambda k:(phase_ids[k],index[k]))
        sequence.append(choose)
        done.add(choose)
    depths={}
    for cid in sequence:
        depths[cid]=0 if not pred[cid] else max(depths[p] for p in pred[cid])+1
    descendants={}
    for cid in ids:
        seen=set()
        stack=[cid]
        while stack:
            curr=stack.pop()
            for child in ids:
                if child not in seen and curr in pred[child]:
                    seen.add(child)
                    stack.append(child)
        descendants[cid]=len(seen)
    return {
        "order":sequence,
        "predecessors":{k:list(pred[k]) for k in ids},
        "depth":depths,
        "descendantCount":descendants,
        "rootControls":[x for x in ids if not pred[x]],
        "edgeCount":sum(len(x) for x in pred.values()),
        "maxStructuralDependencyDepth":max(depths.values()),
    }

def validate_spec(spec, gng):
    s=exact(spec,SPEC_KEYS,"specification")
    check_no_go(gng)
    require(s["schema"]=="maintenance-superinteligence.evidence-sequencing-spec.v1"
            and s["version"]=="1.0.0"
            and s["mode"]=="public_synthetic_readiness_planning_only"
            and s["sourcePackage"]=="pilot/go-nogo-package.v1.json"
            and all(s[x] is False for x in SAFETY_FIELDS)
            and all(s[x] is None for x in ("daysPlanned","costPlanned","workHoursPlanned")),
            "sequencing: fabricated timeline, funding or pilot approval")
    controls=gng["approvalDependencies"]
    ids, dep=_graph(controls)
    require(isinstance(s["phases"],list)
            and len(s["phases"])==len(PHASES),
            "sequencing: seven phases required")
    phase_map={}
    for i,phase in enumerate(s["phases"]):
        exact(phase,PHASE_KEYS,"phase")
        require(phase["phaseId"]==PHASES[i]
                and phase["title"]==PHASE_LABELS[i]
                and phase["exitCriteria"]==EXPECTED_EXIT[i]
                and phase["controlIds"]==list(PHASE_CONTROLS[i])
                and phase["phaseState"]=="requirements_only_no_evidence"
                and phase["mayStartInRealEnvironment"] is False,
                "sequencing: phase order, objectives or field permission changed")
        for item in phase["controlIds"]:
            require(item not in phase_map and item in ids,
                    "sequencing: duplicate or unknown phase control")
            phase_map[item]=i
    require(set(phase_map)==set(ids),
            "sequencing: omitted dependency from phased rollout")
    for cid,prerequisites in dep.items():
        require(all(phase_map[before]<=phase_map[cid] for before in prerequisites),
                "sequencing: phase incorrectly precedes a prerequisite")
    graph=topological_sequence(controls,phase_map)
    require(graph["edgeCount"]==17 and graph["maxStructuralDependencyDepth"]>=3,
            "sequencing: unexpected source graph")
    require(isinstance(s["proofRequests"],list) and len(s["proofRequests"])==13,
            "sequencing: evidence manifest missing")
    original=gng["evidenceManifest"]
    owner_lookup={row["controlId"]:row["owner"]
                  for area in gng["stakeholderReviews"]
                  for row in []}  # owners below from reviewedControlIds
    owners={cid:area["owner"] for area in gng["stakeholderReviews"]
            for cid in area["reviewedControlIds"]}
    for p,e in zip(s["proofRequests"],original):
        exact(p,PROOF_KEYS,"proof")
        cid=p["controlId"]
        require(cid==e["controlId"]
                and p["expectedEvidenceId"]==e["manifestId"]
                and p["owner"]==owners[cid]
                and p["minimumAcceptanceCriteria"]==
                    next(c["acceptanceTest"] for c in
                         json.loads(GNG_PACKAGE.read_text(encoding="utf-8"))["controlPlan"]
                         if c["controlId"]==cid)
                and p["dependentOn"]==list(dep[cid])
                and p["submissionState"]=="not_submitted",
                "sequencing: evidence, ownership or dependency switched")
        require(all(p[k] is False for k in
                    ("reviewerVerified","documentRevisionCurrent",
                     "originAuthorized","licenseAndPrivacyCleared","mayBypass")),
                "sequencing: real proof claimed in public registry")
    require(isinstance(s["externalHandoffs"],list) and
            len(s["externalHandoffs"])==5,"sequencing: missing stakeholders")
    for handoff,area in zip(s["externalHandoffs"],gng["stakeholderReviews"]):
        exact(handoff,HANDOFF_KEYS,"handoff")
        name=area["owner"]
        require(name in OWNERS and handoff["owner"]==name
                and handoff["packetId"]=="SIM-HANDOFF-"+name.upper()
                and handoff["requestedEvidenceIds"]==[
                    p["expectedEvidenceId"] for p in s["proofRequests"] if p["owner"]==name]
                and handoff["referenceOnly"] is True
                and handoff["realReceiptVerified"] is False
                and handoff["signoffEvidence"] is None
                and handoff["approvalNotGranted"] is True,
                "sequencing: false receipt or approval")
    require(isinstance(s["adversarialReviewScenarios"],list)
            and len(s["adversarialReviewScenarios"])==10,
            "sequencing: missing threat tests")
    for a,threat in zip(s["adversarialReviewScenarios"],gng["findingRemediations"]):
        exact(a,THREAT_KEYS,"threat")
        require(a["scenarioId"]=="SIM-GNG-THREAT-"+threat["findingId"][-2:]
                and a["threatId"]==threat["threatId"]
                and a["requiredControlIds"]==threat["requiredControlIds"]
                and a["rejection"]=="deny_and_reopen_external_review"
                and a["actualIncidentConfirmed"] is False
                and a["remediationClosed"] is False,
                "sequencing: threat mitigation falsely completed")
    policy=exact(s["policy"],POLICY_KEYS,"policy")
    require(policy["allowedDecision"]=="no_go"
            and all(policy[key] is False for key in POLICY_KEYS-{"allowedDecision"}),
            "sequencing: no private data or field authority permitted")
    return graph

def build_report(spec,gng):
    graph=validate_spec(spec,gng)
    phases=[]
    for n,phase in enumerate(spec["phases"],1):
        phases.append({
            "phaseId":phase["phaseId"],
            "sequenceNumber":n,
            "title":phase["title"],
            "controlIds":list(phase["controlIds"]),
            "plannedDeliverable":phase["exitCriteria"],
            "documentaryState":"not_verified",
            "nextAction":"request_authorized_external_evidence_only",
            "externalExecutionAuthorized":False,
            "validatedExitCriteriaCount":0,
            "scheduleDate":None,"estimatedCost":None,"workHours":None,
        })
    control_order=[]
    for i,cid in enumerate(graph["order"],1):
        proof=next(x for x in spec["proofRequests"] if x["controlId"]==cid)
        control_order.append({
            "sequence":i,"controlId":cid,"owner":proof["owner"],
            "phaseId":next(p["phaseId"] for p in spec["phases"] if cid in p["controlIds"]),
            "predecessors":list(graph["predecessors"][cid]),
            "graphDepth":graph["depth"][cid],
            "dependentDownstreamControls":graph["descendantCount"][cid],
            "evidenceManifestId":proof["expectedEvidenceId"],
            "criterion":proof["minimumAcceptanceCriteria"],
            "evidenceVerified":False,
            "canProceed":False,
        })
    return {
        "schema":"maintenance-superinteligence.evidence-sequencing-report.v1",
        "version":"1.0.0",
        "mode":"public_synthetic_document_plan_only",
        "specSha256":sha(spec),
        "sourceNoGoSha256":sha(gng),
        "sourceFmeaSnapshotSha256":gng["sourcePublicFmeaSha256"],
        "controlCount":13,
        "dependencyLinkCount":graph["edgeCount"],
        "dependencyMaximumDepth":graph["maxStructuralDependencyDepth"],
        "topologicalOrder":list(graph["order"]),
        "rootPrerequisites":list(graph["rootControls"]),
        "phaseCount":7,
        "phases":phases,
        "sequencedControls":control_order,
        "externalHandoffs":[{
            "owner":x["owner"],"packetId":x["packetId"],
            "evidenceManifestIds":list(x["requestedEvidenceIds"]),
            "realReceiptVerified":False,
            "externalSignoffRecorded":False,
            "containsCorporateData":False,
        } for x in spec["externalHandoffs"]],
        "handoffCount":5,
        "adversarialCases":[{
            "scenarioId":a["scenarioId"],"threatId":a["threatId"],
            "requiredControls":list(a["requiredControlIds"]),
            "decision":"no_go","mitigationAuthenticated":False,
            "realIncidentObserved":False,
        } for a in spec["adversarialReviewScenarios"]],
        "adversarialCaseCount":10,
        "verifiedEvidenceCount":0,
        "verifiedExternalAcceptances":0,
        "realPilotActivitiesExecuted":0,
        "decision":"no_go",
        "executionAuthorized":False,
        "pilotReadinessValidated":False,
        "independentExpertReviewAuthenticated":False,
        "oemSeriesApplicabilityVerified":False,
        "realInterRaterAgreementMeasured":False,
        "realTimelineApproved":False,
        "realBudgetApproved":False,
        "operationalBoundary":dict(spec["policy"]),
    }

def verify_report(report,spec,gng):
    require(report==build_report(spec,gng),
            "sequencing: altered graph, order, status or approval")
    return report

def render_html(report):
    require(report.get("schema")
            =="maintenance-superinteligence.evidence-sequencing-report.v1"
            and report.get("controlCount")==13
            and report.get("dependencyLinkCount")==17
            and report.get("phaseCount")==7
            and report.get("handoffCount")==5
            and report.get("adversarialCaseCount")==10
            and report.get("verifiedEvidenceCount")==0
            and report.get("verifiedExternalAcceptances")==0
            and report.get("realPilotActivitiesExecuted")==0
            and report.get("decision")=="no_go"
            and all(report.get(k) is False for k in
                    ("executionAuthorized","pilotReadinessValidated",
                     "independentExpertReviewAuthenticated",
                     "oemSeriesApplicabilityVerified",
                     "realInterRaterAgreementMeasured","realTimelineApproved",
                     "realBudgetApproved"))
            and len(report.get("sequencedControls",[]))==13
            and all(c.get("evidenceVerified") is False and c.get("canProceed") is False
                    for c in report["sequencedControls"])
            and len(report.get("phases",[]))==7
            and all(p.get("externalExecutionAuthorized") is False
                    and p.get("validatedExitCriteriaCount")==0
                    and p.get("scheduleDate") is None
                    and p.get("estimatedCost") is None
                    and p.get("workHours") is None
                    for p in report["phases"])
            and len(report.get("externalHandoffs",[]))==5
            and all(h.get("realReceiptVerified") is False
                    and h.get("externalSignoffRecorded") is False
                    and h.get("containsCorporateData") is False
                    for h in report["externalHandoffs"])
            and len(report.get("adversarialCases",[]))==10
            and all(a.get("decision")=="no_go" and
                    a.get("mitigationAuthenticated") is False
                    for a in report["adversarialCases"])
            and all(v is False for k,v in report.get("operationalBoundary",{}).items()
                    if k!="allowedDecision")
            and report.get("operationalBoundary",{}).get("allowedDecision")=="no_go",
            "sequencing HTML: forged readiness or sensitive content")
    e=lambda x:escape(str(x),quote=True)
    rows="".join("<tr><td>"+e(c["sequence"])+"</td><td>"+e(c["controlId"])
                 +"</td><td>"+e(c["owner"])+"</td><td>"
                 +e(", ".join(c["predecessors"]) or "sem precedentes")
                 +"</td><td>"+e(c["phaseId"])+"</td></tr>"
                 for c in report["sequencedControls"])
    phases="".join("<li><strong>"+e(p["title"])+"</strong>: "
                   +e(p["plannedDeliverable"])+" — "+e(p["documentaryState"])+"</li>"
                   for p in report["phases"])
    handoffs="".join("<li>"+e(h["owner"])+": "
                     +e(", ".join(h["evidenceManifestIds"]))+"</li>"
                     for h in report["externalHandoffs"])
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            + "form-action &apos;none&apos;" + '"><title>Fases de evidência — NO GO</title>'
            '<style>body{font:15px system-ui,sans-serif;max-width:1150px;margin:1rem auto;'
            'padding:1rem;background:#fafafa;color:#242424}table{border-collapse:collapse;'
            'width:100%}td,th{border:1px solid #ddd;padding:.6rem;text-align:left}'
            '.blocked{border-left:5px solid #a22;background:#fff0f0;padding:1rem}'
            '</style></head><body><h1>Plano documental por dependências — NO GO</h1>'
            '<p class="blocked">Nenhuma evidência privada foi recebida; fases NÃO estão'
            ' liberadas. Nenhuma data, HH ou custo foi estimado. Não há assinatura'
            ' real, aprovação OEM, credencial, SAP/ECM ou liberação de equipamento.</p>'
            '<h2>Fases propostas (não executadas)</h2><ol>'+phases+'</ol>'
            '<h2>Ordem topológica de pré-requisitos</h2><table><thead><tr>'
            '<th>Sequência</th><th>Controle</th><th>Área proposta</th>'
            '<th>Predecessores</th><th>Fase</th></tr></thead><tbody>'+rows
            +'</tbody></table><h2>Pacotes de handoff conceituais</h2><ul>'
            +handoffs+'</ul><footer>Somente leitura offline; sem JavaScript,'
             ' autenticação, formulários ou acesso a dados corporativos.</footer>'
             '</body></html>\n')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",required=True,type=Path)
    p.add_argument("--gng",required=True,type=Path)
    p.add_argument("--spec",default=SPEC_PATH,type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--html",type=Path)
    args=p.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        deps=load_dependencies(snapshot)
        cases=build_collection(json.loads(CASE_FIXTURE.read_text(encoding="utf-8")),deps,snapshot)
        notes=build_notifications(json.loads(NOTE_SPEC.read_text(encoding="utf-8")),
                                  cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,
                              json.loads(RUBRIC_PATH.read_text(encoding="utf-8")),
                              json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
        editorial=build_editorial(json.loads(EDITORIAL_FIXTURE.read_text(encoding="utf-8")),
                                 quality,notes)
        readiness=build_readiness(json.loads(READINESS_FIXTURE.read_text(encoding="utf-8")),
                                  editorial)
        gng=build_gng(json.loads(GNG_PACKAGE.read_text(encoding="utf-8")),readiness)
        candidate=json.loads(args.gng.read_text(encoding="utf-8"))
        spec=json.loads(args.spec.read_text(encoding="utf-8"))
        require(candidate==gng
                and spec==json.loads(SPEC_PATH.read_text(encoding="utf-8")),
                "sequencing: noncanonical/private evidence or modified phase spec")
        report=build_report(spec,gng)
        content=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(content,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(report),encoding="utf-8")
        print(content)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayTransmitSap":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
