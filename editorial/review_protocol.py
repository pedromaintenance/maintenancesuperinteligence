"""Ciclo 18 — governança editorial SIMULADA, sem parecer humano real.

Quatro rascunhos sintéticos fixos; identidades/competências declaradas são
fictícias, sem autenticação, assinatura, alçada, aceite SAP ou campo.
Hashes encadeados detectam alterações apenas perante entrada canônica mantida.
"""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import ImportRejected, require, load_lock, validate_snapshot
from evidence.ledger import sha
from methods.library import ROOT
from casefiles.integrated import FIXTURE_PATH as CASES_PATH, load_dependencies, build_collection
from notifications.drafts import SPEC_PATH as NOTES_SPEC, build_notifications
from quality.notifications import (RUBRIC_PATH, ORACLE_PATH, build_report as build_quality)

FIXTURE_PATH=ROOT/"editorial/review-fixture.v1.json"
CASE_IDS=("SIM-TECH-FD-01","SIM-TECH-HYD-01",
          "SIM-TECH-ECM-LOG-01","SIM-TECH-ECM-ACT-01")
DISCIPLINES=("lubrication","hydraulics","electronics","electronics")
STATES={"requires_revision","unresolved_disagreement","pending_real_review"}
ACTIONS={"submit","review_requires_revision","review_suggest_complete",
         "adjudicate_unresolved","revise","reopen_context","revoke_profile"}
REASONS={
    "submit":{"initial_draft"},
    "review_requires_revision":{"scope_needs_clarification","load_context_conflicted",
                                "event_timing_missing"},
    "review_suggest_complete":{"editorial_format_only"},
    "adjudicate_unresolved":{"disagreement_not_resolved"},
    "revise":{"synthetic_scope_clarified"},
    "reopen_context":{"oem_effectivity_changed","symptom_changed",
                      "machine_configuration_changed"},
    "revoke_profile":{"reviewer_profile_revoked"},
}
ROOT_FIELDS={"schema","version","purpose","sourceRubric","sourceNotificationSpec",
             "realHumanIdentities","qualifiedSignatures",
             "mayPersistPrivateEvidence","mayOpenSapNotifications","actors","cases"}
ACTOR_FIELDS={"actorId","personaKey","role","declaredCompetence","identityNature",
              "identityVerified","qualificationVerified","independenceVerified",
              "conflictOfInterestDeclared","credentials"}
CASE_FIELDS={"draftId","caseFileId","declaredDiscipline","authorId","reviewerIds",
             "adjudicatorId","custodianId","events"}
EVENT_FIELDS={"eventId","actorId","action","targetRevision","reason","nonce",
              "signature","targetActorId"}
GATES={
    "humanReviewerIdentityAuthenticated":False,
    "engineeringQualificationVerified":False,
    "reviewerIndependenceVerified":False,
    "currentDocumentRealReviewComplete":False,
    "oemEffectivityVerified":False,
    "fieldEvidenceValidated":False,
    "externalImmutableAuditAnchorVerified":False,
    "safeWorkMethodApproved":False,
    "mayCreateSapNotification":False,
    "mayCreateWorkOrder":False,
    "mayOrderParts":False,
    "mayModifyEcm":False,
    "mayReleaseEquipment":False,
}
CHECKPOINTS=(
    "Conferir identidade, competência e impedimentos em sistema privado aprovado.",
    "Solicitar dois pareceres independentes para a mesma revisão vigente.",
    "Resolver divergências e documentar eventuais correções de forma rastreável.",
    "Reavaliar toda versão após mudança de sintoma, configuração ou referência OEM.",
    "Exigir documentação OEM efetiva, evidência física e avaliação de segurança antes de executar.",
)

def exact(obj, expected, label):
    require(isinstance(obj,dict) and set(obj)==expected,
            f"editorial: {label}: campos inesperados ou ausentes")
    return obj

def fictional(value,prefix):
    return (isinstance(value,str)
            and re.fullmatch(re.escape(prefix)+r"[A-Z0-9-]+",value) is not None)

def validate_fixture(fixture, quality_report, notification_collection):
    f=exact(fixture,ROOT_FIELDS,"fixture")
    require(f["schema"]=="maintenance-superinteligence.editorial-review-fixture.v1"
            and f["version"]=="1.0.0"
            and f["purpose"]=="offline_fictional_review_threat_exercise"
            and f["sourceRubric"]=="quality/notification-rubric.v1.json"
            and f["sourceNotificationSpec"]=="notifications/training-spec.v1.json"
            and all(f[k] is False for k in (
                "realHumanIdentities","qualifiedSignatures",
                "mayPersistPrivateEvidence","mayOpenSapNotifications")),
            "editorial: fonte ou autoridade corporativa não verificada")
    require(quality_report["documentsAdequateForSyntheticTraining"]==4
            and quality_report["documentsApprovedForField"]==0
            and quality_report["independentRealExpertReviewComplete"] is False
            and quality_report["interRaterReliabilityMeasured"] is False
            and notification_collection["draftCount"]==4
            and notification_collection["realNotificationsCreated"]==0,
            "editorial: origem documental não é evidência de aprovação técnica")
    require(isinstance(f["actors"],list) and len(f["actors"])==14
            and isinstance(f["cases"],list) and len(f["cases"])==4,
            "editorial: personas ou documentos sintéticos ausentes")
    actors={}
    personas=set()
    for a in f["actors"]:
        exact(a,ACTOR_FIELDS,"actor")
        aid=a["actorId"]
        require(fictional(aid,"SIM-")
                and fictional(a["personaKey"],"SIM-PERSON-")
                and aid not in actors and a["personaKey"] not in personas
                and a["role"] in {"author","reviewer","adjudicator","custodian"}
                and a["declaredCompetence"] in {
                    "lubrication","hydraulics","electronics","general"}
                and a["identityNature"]=="fictional_persona_only"
                and all(a[k] is False for k in (
                    "identityVerified","qualificationVerified","independenceVerified",
                    "conflictOfInterestDeclared"))
                and a["credentials"] is None,
                "editorial: personagem, pessoa, identidade ou competência adulterada")
        actors[aid]=a
        personas.add(a["personaKey"])
    docs=notification_collection["drafts"]
    require([c["draftId"] for c in f["cases"]]
            ==[d["draftId"] for d in docs]
            ==[f"SIM-NOTE-{n:03}" for n in range(1,5)],
            "editorial: documento de origem desconhecido")
    identifiers=set()
    nonces=set()
    cases=[]
    for i,(c,d) in enumerate(zip(f["cases"],docs)):
        exact(c,CASE_FIELDS,"case")
        require(c["draftId"]==d["draftId"]
                and c["caseFileId"]==CASE_IDS[i]
                and c["declaredDiscipline"]==DISCIPLINES[i]
                and c["authorId"]==f"SIM-AUTHOR-{i+1}"
                and c["reviewerIds"]==[
                    f"SIM-REVIEWER-{i+1}-A",f"SIM-REVIEWER-{i+1}-B"]
                and c["adjudicatorId"]=="SIM-ADJUDICATOR-1"
                and c["custodianId"]=="SIM-CUSTODIAN-1"
                and isinstance(c["events"],list)
                and 3<=len(c["events"])<=6,
                "editorial: escopo, disciplina ou atribuição de revisão incompatível")
        author=actors[c["authorId"]]
        reviewers=[actors[k] for k in c["reviewerIds"]]
        adjudicator=actors[c["adjudicatorId"]]
        custodian=actors[c["custodianId"]]
        require(author["role"]=="author"
                and author["declaredCompetence"]==c["declaredDiscipline"]
                and all(r["role"]=="reviewer"
                        and r["declaredCompetence"]==c["declaredDiscipline"]
                        for r in reviewers)
                and adjudicator["role"]=="adjudicator"
                and custodian["role"]=="custodian"
                and adjudicator["declaredCompetence"]=="general"
                and custodian["declaredCompetence"]=="general"
                and len({author["personaKey"],reviewers[0]["personaKey"],
                         reviewers[1]["personaKey"],adjudicator["personaKey"],
                         custodian["personaKey"]})==5,
                "editorial: autoavaliação, dupla identidade ou competência incorreta")
        for j,event in enumerate(c["events"],1):
            exact(event,EVENT_FIELDS,"event")
            action=event["action"]
            require(event["eventId"]==f"SIM-REV-EVT-{i+1}-{j}"
                    and event["eventId"] not in identifiers
                    and event["nonce"]==f"SIM-NONCE-{i+1}-{j}"
                    and event["nonce"] not in nonces
                    and action in ACTIONS
                    and event["reason"] in REASONS[action]
                    and event["actorId"] in actors
                    and type(event["targetRevision"]) is int
                    and event["targetRevision"]>=1
                    and event["signature"] is None
                    and (event["targetActorId"] in c["reviewerIds"]
                         if action=="revoke_profile" else
                         event["targetActorId"] is None),
                    "editorial: evento externo, nonce repetido ou assinatura forjada")
            identifiers.add(event["eventId"])
            nonces.add(event["nonce"])
        cases.append((c,d))
    return actors,cases

def _review_case(c,d,actors):
    revision=0
    revision_digest=None
    history=[]
    reviews=[]
    revoked=set()
    seen_review=set()
    adjudicated=False
    event_chain=[]
    prev=sha({"schema":"maintenance-superinteligence.editorial-review-audit-seed.v1",
              "draftId":c["draftId"],"sourceDocumentDigest":sha(d)})
    seen_decisions=[]
    for event in c["events"]:
        action=event["action"]
        actor=event["actorId"]
        rev=event["targetRevision"]
        reason=event["reason"]
        if action=="submit":
            require(revision==0 and actor==c["authorId"] and rev==1
                    and event is c["events"][0],
                    "editorial: primeiro evento deve submeter revisão inicial")
            revision=1
            revision_digest=sha({"draftDigest":sha(d),"revision":revision,
                                "reason":reason,"previousRevisionDigest":None})
            history.append({"revision":revision,"trigger":action,
                            "reason":reason,"revisionDigest":revision_digest,
                            "realDocumentEdited":False})
        elif action in {"review_requires_revision","review_suggest_complete"}:
            require(actor in c["reviewerIds"] and actor not in revoked
                    and rev==revision and revision>=1
                    and (actor,revision) not in seen_review
                    and actors[actor]["declaredCompetence"]==c["declaredDiscipline"],
                    "editorial: revisor duplicado, revogado, não competente ou versão obsoleta")
            seen_review.add((actor,revision))
            reviews.append({
                "reviewEventId":event["eventId"],"actorId":actor,
                "personaKey":actors[actor]["personaKey"],
                "revision":revision,"revisionDigest":revision_digest,
                "position":("requires_revision" if action=="review_requires_revision"
                            else "suggests_documentary_completeness_only"),
                "reason":reason,
                "identityAuthenticated":False,
                "signatureVerified":False,
                "engineeringOpinionVerified":False,
            })
            seen_decisions.append(action)
        elif action=="adjudicate_unresolved":
            active=[r for r in reviews if r["revision"]==revision
                    and r["actorId"] not in revoked]
            require(actor==c["adjudicatorId"] and rev==revision
                    and len(active)==2 and not adjudicated
                    and {r["position"] for r in active}
                       =={"requires_revision",
                          "suggests_documentary_completeness_only"},
                    "editorial: divergência ou autoridade de adjudicação fabricada")
            adjudicated=True
        elif action in {"revise","reopen_context"}:
            require(actor==c["authorId"] and rev==revision+1
                    and revision>=1 and not revoked
                    and (action!="revise" or len([
                        r for r in reviews if r["revision"]==revision])==2),
                    "editorial: versão alterada por papel errado ou salto/rollback")
            old=revision_digest
            revision=rev
            revision_digest=sha({"draftDigest":sha(d),"revision":revision,
                                "reason":reason,"previousRevisionDigest":old})
            history.append({"revision":revision,"trigger":action,
                            "reason":reason,"revisionDigest":revision_digest,
                            "realDocumentEdited":False})
            adjudicated=False
            seen_decisions=[]
        elif action=="revoke_profile":
            require(actor==c["custodianId"] and rev==revision
                    and event["targetActorId"] in c["reviewerIds"]
                    and event["targetActorId"] not in revoked,
                    "editorial: revogação por pessoa sem papel de custodiante")
            revoked.add(event["targetActorId"])
        else:
            require(False,"editorial: ação de fluxo desconhecida")
        digest=sha({"previousEventDigest":prev,
                    "event":event,"currentRevisionDigest":revision_digest})
        event_chain.append({
            "eventId":event["eventId"],"action":action,
            "actorId":actor,"targetRevision":rev,"reason":reason,
            "targetActorId":event["targetActorId"],
            "previousEventDigest":prev,"eventDigest":digest,
            "currentRevisionDigest":revision_digest,
            "verifiedCryptographicSignature":False,
            "verifiedTrustedTimestamp":False,
            "externalImmutabilityVerified":False,
        })
        prev=digest
    require(revision>=1 and len(history)>=1
            and [x["revision"] for x in history]==list(range(1,revision+1)),
            "editorial: encadeamento ou versionamento incoerente")
    current=[r for r in reviews if r["revision"]==revision
             and r["actorId"] not in revoked]
    positions={r["position"] for r in current}
    if len(current)==2 and positions=={"requires_revision"}:
        status="requires_revision"
    elif len(current)==2 and len(positions)==2:
        status="unresolved_disagreement"
    else:
        status="pending_real_review"
    review_output=[dict(x,validForCurrentRevision=(
        x["revision"]==revision and x["actorId"] not in revoked))
                   for x in reviews]
    return {
        "schema":"maintenance-superinteligence.editorial-review-case.v1",
        "draftId":c["draftId"],"caseFileId":c["caseFileId"],
        "declaredDiscipline":c["declaredDiscipline"],
        "authorId":c["authorId"],"reviewerIds":list(c["reviewerIds"]),
        "adjudicatorId":c["adjudicatorId"],
        "currentRevision":revision,"currentRevisionDigest":revision_digest,
        "sourceDraftSha256":sha(d),
        "documentRevisions":history,
        "independentRealReviewerCount":0,
        "fictionalCurrentReviewerCount":len(current),
        "reviewRecords":review_output,
        "adjudicationPerformedInSimulation":adjudicated,
        "revokedPersonaIds":sorted(revoked),
        "decision":status,
        "humanEditorialAgreementEstablished":False,
        "reviewerIdentitiesVerified":False,
        "reviewerCompetenceVerified":False,
        "auditTrail":event_chain,
        "auditFinalDigest":prev,
        "auditDigestRecomputedFromFixture":True,
        "externalAuditAnchorVerified":False,
        "evidenceGapResolution":{
            "oemEffectivitySourceAuthenticated":False,
            "physicalEvidenceCollected":False,
            "contextChangesRequireReReview":True,
            "allCurrentReviewGatesSatisfied":False,
        },
        "acceptanceBoundary":dict(GATES),
        "nextHumanReviewRequirements":list(CHECKPOINTS),
        "mayBeImportedToSap":False,
        "mayConfirmFailure":False,
        "mayReleaseEquipment":False,
    }

def build_report(fixture,quality_report,notes):
    actors,cases=validate_fixture(fixture,quality_report,notes)
    outputs=[_review_case(c,d,actors) for c,d in cases]
    require([x["decision"] for x in outputs]==[
            "requires_revision","unresolved_disagreement",
            "pending_real_review","pending_real_review"],
            "editorial: cenário de divergência ou reabertura alterado")
    return {
        "schema":"maintenance-superinteligence.editorial-review-report.v1",
        "version":"1.0.0",
        "nature":"fictional_not_authenticated",
        "fixtureSha256":sha(fixture),
        "qualityReportSha256":sha(quality_report),
        "notificationCollectionSha256":sha(notes),
        "publicFmeaSnapshotSha256":quality_report["publicFmeaSnapshotSha256"],
        "cases":outputs,"caseCount":4,
        "simulatedEventCount":sum(len(c["auditTrail"]) for c in outputs),
        "realReviewsCompleted":0,"realApprovalsGranted":0,
        "interRaterReliabilityMeasured":False,
        "signaturesVerified":False,
        "externalImmutableAuditLogVerified":False,
        "mayWriteToSap":False,"mayApproveMaintenance":False,
        "mayReleaseEquipment":False,
    }

def verify_report(report,fixture,quality_report,notes):
    require(report==build_report(fixture,quality_report,notes),
            "editorial: resultado, cadeia de auditoria ou versão adulterada")
    return report

def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.editorial-review-report.v1"
            and report.get("caseCount")==4
            and report.get("simulatedEventCount")==16
            and report.get("realReviewsCompleted")==0
            and report.get("realApprovalsGranted")==0
            and report.get("interRaterReliabilityMeasured") is False
            and report.get("signaturesVerified") is False
            and report.get("externalImmutableAuditLogVerified") is False
            and report.get("mayWriteToSap") is False
            and report.get("mayApproveMaintenance") is False
            and report.get("mayReleaseEquipment") is False
            and isinstance(report.get("cases"),list)
            and len(report["cases"])==4
            and [x.get("decision") for x in report["cases"]]==[
                "requires_revision","unresolved_disagreement",
                "pending_real_review","pending_real_review"]
            and all(c.get("independentRealReviewerCount")==0
                    and c.get("auditDigestRecomputedFromFixture") is True
                    and c.get("externalAuditAnchorVerified") is False
                    and c.get("reviewerIdentitiesVerified") is False
                    and c.get("reviewerCompetenceVerified") is False
                    and c.get("mayBeImportedToSap") is False
                    and c.get("mayConfirmFailure") is False
                    and c.get("mayReleaseEquipment") is False
                    and all(v is False for v in c.get("acceptanceBoundary",{}).values())
                    and all(r.get("identityAuthenticated") is False
                            and r.get("signatureVerified") is False
                            and r.get("engineeringOpinionVerified") is False
                            for r in c.get("reviewRecords",[]))
                    and all(e.get("verifiedCryptographicSignature") is False
                            and e.get("externalImmutabilityVerified") is False
                            and e.get("verifiedTrustedTimestamp") is False
                            for e in c.get("auditTrail",[]))
                    for c in report["cases"]),
            "editorial HTML: parecer real ou liberação fabricados")
    e=lambda x:escape(str(x),quote=True)
    sections=[]
    for c in report["cases"]:
        rev="".join("<li>Revisão "+e(r["revision"])+" — "
                    +e(r["trigger"])+" / "+e(r["reason"])+
                    " — documento sintético, sem edição de campo</li>"
                    for r in c["documentRevisions"])
        audits="".join("<li>"+e(x["eventId"])+" — "+e(x["action"])
                       +" — "+e(x["reason"])+"</li>"
                       for x in c["auditTrail"])
        reviews="".join("<li>"+e(x["actorId"])+" (fictício): "
                        +e(x["position"])+" — "+
                        ("vigente no exercício" if x["validForCurrentRevision"]
                         else "OBSOLETO ou revogado")+"</li>"
                        for x in c["reviewRecords"])
        sections.append("<section><h2>"+e(c["draftId"])+" — "+e(c["decision"])
                        +"</h2><p>Revisão atual: "+e(c["currentRevision"])
                        +" | Disciplina: "+e(c["declaredDiscipline"])
                        +"</p><h3>Histórico de versões</h3><ol>"+rev
                        +"</ol><h3>Posições editoriais fictícias</h3><ul>"+reviews
                        +"</ul><h3>Eventos de auditoria simulados</h3><ol>"
                        +audits+"</ol><p class='stop'>ABSTENÇÃO. Identidade,"
                        " competência e independência não verificadas;"
                        " nenhum registro SAP, ensaio ou liberação autorizado.</p></section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            + "form-action &apos;none&apos;" + '"><title>Revisões editoriais fictícias</title>'
            '<style>body{font:15px system-ui,sans-serif;max-width:1100px;'
            'margin:2rem auto;padding:1rem;color:#282828;background:#fafafa}'
            'section{border:1px solid #ddd;background:#fff;margin:1rem 0;padding:1rem}'
            '.stop{border-left:5px solid #a22;background:#fff0f0;padding:.8rem}'
            '</style></head><body><h1>Revisão editorial — SIMULAÇÃO NÃO AUTENTICADA</h1>'
            '<p class="stop">Hashes não equivalem a assinaturas ou identidade humana.'
            ' Divergências e revisões obsoletas não são aprovações técnicas.</p>'
            + "".join(sections)
            + '<footer>Offline, sem JS, formulário, rede ou integração corporativa.</footer>'
              '</body></html>\n')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--quality",type=Path,required=True)
    p.add_argument("--drafts",type=Path,required=True)
    p.add_argument("--fixture",type=Path,default=FIXTURE_PATH)
    p.add_argument("--output",type=Path)
    p.add_argument("--html",type=Path)
    args=p.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        deps=load_dependencies(snapshot)
        casefixture=json.loads(CASES_PATH.read_text(encoding="utf-8"))
        cases=build_collection(casefixture,deps,snapshot)
        spec=json.loads(NOTES_SPEC.read_text(encoding="utf-8"))
        notes=build_notifications(spec,cases["cases"],cases["investigationTrees"])
        rubric=json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        oracle=json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        quality=build_quality(notes,cases,rubric,oracle)
        submitted_quality=json.loads(args.quality.read_text(encoding="utf-8"))
        submitted_notes=json.loads(args.drafts.read_text(encoding="utf-8"))
        fixture=json.loads(args.fixture.read_text(encoding="utf-8"))
        require(submitted_quality==quality and submitted_notes==notes
                and fixture==json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
                "editorial: origem, documentação ou personas fictícias alteradas")
        result=build_report(fixture,quality,notes)
        serialized=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(serialized,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(result),encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayWriteToSap":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
