"""Ciclo 22 — contradições editoriais HIPOTÉTICAS, reabertura dependente e NO GO.

Nenhuma afirmação é medição, evidência privada, aprovação OEM ou parecer humano.
Detecção semântica se limita a seis pares editoriais versionados e ao grafo
documental público de 13 controles/17 dependências do Ciclo 21.
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
from casefiles.integrated import FIXTURE_PATH as CASE_FIXTURE, load_dependencies, build_collection
from notifications.drafts import SPEC_PATH as NOTE_SPEC, build_notifications
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as build_quality
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_FIXTURE, build_report as build_editorial
from pilot.readiness import FIXTURE_PATH as READINESS_FIXTURE, build_report as build_readiness
from pilot.go_nogo import PACKAGE_PATH as GNG_PACKAGE, build_report as build_gng, DEPENDENCIES
from pilot.evidence_sequence import SPEC_PATH as SEQUENCE_SPEC, build_report as build_sequence, topological_sequence

FIXTURE_PATH=ROOT/"pilot/evidence-contradictions.v1.json"
SCENARIO_DEFS=(
    ("duplicate-principal","identity-proof","two-independent-reviews",
     "same_principal","different_principals","persona_alias_collision","IT","Engineering"),
    ("expired-competence","competence","two-independent-reviews",
     "current_credential","expired_credential","qualification_expiry_disagreement","Engineering","IT"),
    ("oem-revision-superseded","oem-effectivity","version-lock",
     "current_oem_revision","superseded_oem_revision","oem_revision_superseded",
     "Engineering","MaintenanceManagement"),
    ("equipment-reconfigured","equipment-configuration","oem-effectivity",
     "configuration_unchanged","configuration_changed","machine_configuration_changed",
     "MaintenanceManagement","Engineering"),
    ("reviewer-evidence-conflict","two-independent-reviews","signed-decision",
     "review_supports","review_challenges","reviewer_disagreement",
     "Engineering","InformationSecurity"),
    ("privacy-retention-contradiction","privacy-retention","evidence-legitimacy",
     "retention_authorized","retention_not_authorized","legal_retention_conflict",
     "Legal","InformationSecurity"),
)
QUESTION_TEXT=(
    "A mesma identidade autenticada representa realmente duas pessoas distintas?",
    "A competência declarada continua válida após eventual expiração ou revogação?",
    "A revisão OEM aplicável cobre o arranjo/configuração do equipamento?",
    "Qual alteração de arranjo invalida a efetividade do documento anterior?",
    "A divergência entre pareceres foi preservada e vinculada à mesma revisão?",
    "A finalidade, base legal e retenção proposta permanecem consistentes e autorizadas?",
)
QUESTION_TARGETS=("two-independent-reviews","revocation-reopen",
                  "equipment-configuration","oem-effectivity",
                  "signed-decision","evidence-legitimacy")
ROOT_KEYS={"schema","version","mode","sourceSequence","sourceGoNoGo",
           "fieldEvidenceAvailable","privateDocumentsLoaded",
           "humanReviewsAuthenticated","sourceProofsVerified",
           "mayAuthorizePilot","scenarios","questions","policy"}
SCENARIO_KEYS={"scenarioId","label","assertions","invalidationReason",
               "triggerControlIds","crossReviewOwners","conflictExpected",
               "priorProofInvalidated","realIncidentObserved",
               "canResolveAutomatically"}
ASSERTION_KEYS={"assertionId","controlId","claim","contextRevision",
                "documentRevision","origin","observed","authenticated",
                "sourceDocument","claimantId"}
QUESTION_KEYS={"questionId","scenarioId","owner","peerOwner","sourceControlId",
               "targetControlId","question","answerState",
               "answeredByRealPerson","approvalGranted"}
POLICY_KEYS={"decision","allClaimsHypothetical","anyConflictBlocks",
             "propagateToAllDescendants","requireHumanExternalResolution",
             "neverAcceptStaleProof","mayWriteSap","mayAlterEcm",
             "mayCreateWorkOrder","mayReleaseEquipment"}

def exact(value,keys,name):
    require(isinstance(value,dict) and set(value)==keys,
            "contradiction: unrecognized or missing "+name)
    return value

def validate_fixture(fixture,sequence,gng):
    spec=exact(fixture,ROOT_KEYS,"fixture")
    require(spec["schema"]=="maintenance-superinteligence.evidence-contradiction-fixture.v1"
            and spec["version"]=="1.0.0"
            and spec["mode"]=="public_synthetic_cross_functional_conflict_only"
            and spec["sourceSequence"]=="pilot/evidence-sequencing.v1.json"
            and spec["sourceGoNoGo"]=="pilot/go-nogo-package.v1.json"
            and all(spec[k] is False for k in (
                "fieldEvidenceAvailable","privateDocumentsLoaded",
                "humanReviewsAuthenticated","sourceProofsVerified",
                "mayAuthorizePilot")),
            "contradiction: cannot turn synthetic claims into verified evidence")
    p=exact(spec["policy"],POLICY_KEYS,"policy")
    require(p["decision"]=="no_go"
            and all(p[k] is True for k in (
                "allClaimsHypothetical","anyConflictBlocks",
                "propagateToAllDescendants","requireHumanExternalResolution",
                "neverAcceptStaleProof"))
            and all(p[k] is False for k in (
                "mayWriteSap","mayAlterEcm","mayCreateWorkOrder",
                "mayReleaseEquipment")),
            "contradiction: evidence uncertainty must remain NO GO")
    require(sequence.get("schema")
            =="maintenance-superinteligence.evidence-sequencing-report.v1"
            and sequence.get("controlCount")==13
            and sequence.get("dependencyLinkCount")==17
            and sequence.get("decision")=="no_go"
            and sequence.get("verifiedEvidenceCount")==0
            and sequence.get("verifiedExternalAcceptances")==0
            and sequence.get("pilotReadinessValidated") is False
            and sequence.get("oemSeriesApplicabilityVerified") is False
            and sequence.get("executionAuthorized") is False
            and gng.get("schema")=="maintenance-superinteligence.go-nogo-report.v1"
            and gng.get("decision")=="no_go"
            and gng.get("verifiedEvidenceCount")==0
            and gng.get("verifiedSignoffs")==0,
            "contradiction: source reports are not authorized or canonical")
    edges=gng["approvalDependencies"]
    graph=topological_sequence(edges)
    require(graph["edgeCount"]==17
            and set(graph["predecessors"])==set(DEPENDENCIES)
            and all(graph["predecessors"][key]==list(DEPENDENCIES[key])
                    for key in DEPENDENCIES)
            and sequence["topologicalOrder"]==topological_sequence(
                edges, {cid:i for i,phase in enumerate(json.loads(
                    SEQUENCE_SPEC.read_text(encoding="utf-8"))["phases"])
                    for cid in phase["controlIds"]})["order"],
            "contradiction: removed/changed dependency or sequence")
    require(isinstance(spec["scenarios"],list)
            and len(spec["scenarios"])==len(SCENARIO_DEFS)
            and isinstance(spec["questions"],list)
            and len(spec["questions"])==len(SCENARIO_DEFS),
            "contradiction: all six scenarios/questions are mandatory")
    ids=set()
    for i,(case,rule,question) in enumerate(zip(
            spec["scenarios"],SCENARIO_DEFS,spec["questions"]),1):
        label,left,right,claim_a,claim_b,reason,owner,peer=rule
        exact(case,SCENARIO_KEYS,"scenario")
        scenario_id=f"SIM-CONFLICT-{i:02}"
        require(case["scenarioId"]==scenario_id
                and case["label"]==label
                and case["invalidationReason"]==reason
                and case["triggerControlIds"]==[left,right]
                and case["crossReviewOwners"]==[owner,peer]
                and case["conflictExpected"] is True
                and case["priorProofInvalidated"] is True
                and case["realIncidentObserved"] is False
                and case["canResolveAutomatically"] is False
                and isinstance(case["assertions"],list)
                and len(case["assertions"])==2,
                "contradiction: changed scenario, hidden conflict or real incident")
        for suffix,a,cid,claim,revision in zip(
                ("A","B"),case["assertions"],(left,right),
                (claim_a,claim_b),(1,2)):
            exact(a,ASSERTION_KEYS,"assertion")
            aid=f"SIM-ASSERT-{i:02}-{suffix}"
            require(a["assertionId"]==aid and aid not in ids
                    and a["controlId"]==cid
                    and a["claim"]==claim
                    and type(a["contextRevision"]) is int
                    and a["contextRevision"]==revision
                    and type(a["documentRevision"]) is int
                    and a["documentRevision"]==revision
                    and a["origin"]=="fictional_hypothesis_only"
                    and a["observed"] is False
                    and a["authenticated"] is False
                    and a["sourceDocument"] is None
                    and a["claimantId"] is None,
                    "contradiction: revision, scope or fake proof/authentication")
            ids.add(aid)
        exact(question,QUESTION_KEYS,"cross-functional question")
        require(question["questionId"]==f"SIM-XREVIEW-{i:02}"
                and question["scenarioId"]==scenario_id
                and question["owner"]==owner
                and question["peerOwner"]==peer
                and question["sourceControlId"]==left
                and question["targetControlId"]==QUESTION_TARGETS[i-1]
                and question["question"]==QUESTION_TEXT[i-1]
                and question["answerState"]=="external_review_not_performed"
                and question["answeredByRealPerson"] is False
                and question["approvalGranted"] is False,
                "contradiction: false cross-functional review or question")
    return graph

def descendant_cascade(roots,graph):
    """Transitive dependent closure from *canonical* directed prerequisites.

    Independent roots remain separate. Reopening a control does not prove failure.
    """
    predecessor=graph["predecessors"]
    descendants=set(roots)
    require(roots and len(roots)==len(set(roots))
            and set(roots)<=set(predecessor),
            "contradiction: unexpected graph root")
    queue=list(roots)
    while queue:
        source=queue.pop(0)
        for cid in graph["order"]:
            if source in predecessor[cid] and cid not in descendants:
                descendants.add(cid)
                queue.append(cid)
    return [cid for cid in graph["order"] if cid in descendants]

def build_report(fixture,sequence,gng):
    graph=validate_fixture(fixture,sequence,gng)
    outputs=[]
    for case,question in zip(fixture["scenarios"],fixture["questions"]):
        roots=list(case["triggerControlIds"])
        closure=descendant_cascade(roots,graph)
        stale=[{
            "assertionId":a["assertionId"],"controlId":a["controlId"],
            "claimRevision":a["documentRevision"],
            "currentRevisionVerified":False,
            "sourceAuthenticated":False,
            "priorAssertionStillBinding":False,
            "evidenceDiscardedAsFailure":False,
            "invalidatedForDecision":True,
        } for a in case["assertions"]]
        outputs.append({
            "scenarioId":case["scenarioId"],
            "label":case["label"],
            "assertionIds":[a["assertionId"] for a in case["assertions"]],
            "assertionStates":["hypothetical_unobserved","hypothetical_unobserved"],
            "conflictMechanism":case["invalidationReason"],
            "sourceControls":roots,
            "finding":{
                "findingId":"SIM-FIND-CONFLICT-"+case["scenarioId"][-2:],
                "status":"hypothetical_inconsistency_to_investigate",
                "conflictingAssertions":list(a["assertionId"] for a in case["assertions"]),
                "reviewNeeded":True,
                "realWorldConflictConfirmed":False,
                "mechanicalFailureConfirmed":False,
                "mayDiscardHypothesis":False,
            },
            "staleProofInvalidations":stale,
            "dependencyReopenCascade":{
                "triggerControls":roots,
                "allAffectedControls":closure,
                "downstreamControlIds":[x for x in closure if x not in roots],
                "affectedCount":len(closure),
                "allReopenedAsUnverified":True,
                "externalReviewRequired":True,
                "operationallyApproved":False,
            },
            "crossFunctionalReviewQuestion":{
                "questionId":question["questionId"],
                "primaryOwner":question["owner"],
                "peerOwner":question["peerOwner"],
                "question":question["question"],
                "answer":"not_available",
                "realReviewPerformed":False,
                "crossFunctionConsensusEstablished":False,
            },
            "noGoDisposition":{
                "decision":"no_go",
                "requiresVerifiedExternalEvidence":True,
                "requiresVersionRevalidation":True,
                "requiresAuthenticatedHumanReview":True,
                "mayTreatConflictAsMeasuredFault":False,
                "mayTransmitSap":False,
                "mayModifyEcm":False,
                "mayCreateWorkOrder":False,
                "mayReleaseEquipment":False,
            },
        })
    affected=list(dict.fromkeys(cid for row in outputs
                                for cid in row["dependencyReopenCascade"]["allAffectedControls"]))
    return {
        "schema":"maintenance-superinteligence.evidence-contradiction-report.v1",
        "version":"1.0.0",
        "mode":"synthetic_dependency_cross_review_only",
        "fixtureSha256":sha(fixture),
        "sourceSequenceSha256":sha(sequence),
        "sourceNoGoSha256":sha(gng),
        "sourceFmeaSnapshotSha256":sequence["sourceFmeaSnapshotSha256"],
        "sourceControlCount":13,
        "sourceDependencyCount":17,
        "scenarioCount":len(outputs),
        "crossReviewQuestionCount":len(outputs),
        "scenarios":outputs,
        "allAffectedControls":sorted(affected),
        "verifiedPhysicalFaults":0,
        "externalProofsVerified":0,
        "independentRealReviewsCompleted":0,
        "realOperationalActions":0,
        "decision":"no_go",
        "canAuthorizePilot":False,
        "canWriteSap":False,
        "canModifyEcm":False,
        "canCreateWorkOrder":False,
        "canReleaseEquipment":False,
    }

def verify_report(report,fixture,sequence,gng):
    require(report==build_report(fixture,sequence,gng),
            "contradiction: altered scenario, dependency closure or decision")
    return report

def render_html(report):
    require(report.get("schema")
            =="maintenance-superinteligence.evidence-contradiction-report.v1"
            and report.get("decision")=="no_go"
            and report.get("sourceControlCount")==13
            and report.get("sourceDependencyCount")==17
            and report.get("scenarioCount")==6
            and report.get("crossReviewQuestionCount")==6
            and all(report.get(k)==0 for k in (
                "verifiedPhysicalFaults","externalProofsVerified",
                "independentRealReviewsCompleted","realOperationalActions"))
            and all(report.get(k) is False for k in (
                "canAuthorizePilot","canWriteSap","canModifyEcm",
                "canCreateWorkOrder","canReleaseEquipment"))
            and isinstance(report.get("scenarios"),list)
            and len(report["scenarios"])==6
            and all(
                x.get("finding",{}).get("realWorldConflictConfirmed") is False
                and x.get("finding",{}).get("mechanicalFailureConfirmed") is False
                and x.get("dependencyReopenCascade",{}).get("operationallyApproved") is False
                and x.get("dependencyReopenCascade",{}).get("allReopenedAsUnverified") is True
                and x.get("crossFunctionalReviewQuestion",{}).get("realReviewPerformed") is False
                and x.get("noGoDisposition",{}).get("decision")=="no_go"
                and all(v is False for k,v in x.get("noGoDisposition",{}).items()
                        if k.startswith("may"))
                and all(z.get("sourceAuthenticated") is False
                        and z.get("priorAssertionStillBinding") is False
                        for z in x.get("staleProofInvalidations",[]))
                for x in report["scenarios"]),
            "contradiction HTML: false validation or authority")
    e=lambda v:escape(str(v),quote=True)
    panels=[]
    for item in report["scenarios"]:
        c=item["dependencyReopenCascade"]
        q=item["crossFunctionalReviewQuestion"]
        panels.append(
            "<section><h2>"+e(item["scenarioId"])+" — "+e(item["label"])+"</h2>"
            "<p><strong>Motivo hipotético:</strong> "+e(item["conflictMechanism"])+"</p>"
            "<p><strong>Controles a reabrir:</strong> "
            +e(", ".join(c["allAffectedControls"]))+"</p>"
            "<p><strong>Revisão cruzada ("+e(q["primaryOwner"])+"/"+e(q["peerOwner"])
            +"):</strong> "+e(q["question"])+"</p>"
            "<p class='denied'>NO GO: não observado, não autenticado;"
            " nenhuma causa mecânica estabelecida.</p></section>")
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
        + "form-action &apos;none&apos;" + '"><title>Contradições de evidência — NO GO</title>'
        '<style>body{font:15px system-ui,sans-serif;max-width:1100px;margin:1rem auto;'
        'padding:1rem;background:#fafafa;color:#262626}section{border:1px solid #ddd;'
        'margin:1rem 0;padding:1rem;background:#fff}.denied{padding:.8rem;'
        'border-left:5px solid #a22;background:#fff0f0}</style></head>'
        '<body><h1>Contradições documentais — SIMULAÇÃO NO GO</h1>'
        '<p class="denied">Seis hipóteses editoriais sem dados de campo ou revisão humana.'
        ' Reabertura não implica falha física, nem autoriza SAP, ECM ou liberação.</p>'
        + "".join(panels)
        + '<footer>Documento offline, sem scripts, formulários ou conexões externas.</footer>'
        '</body></html>\n'
    )

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--sequence",type=Path,required=True)
    p.add_argument("--gng",type=Path,required=True)
    p.add_argument("--fixture",type=Path,default=FIXTURE_PATH)
    p.add_argument("--output",type=Path)
    p.add_argument("--html",type=Path)
    args=p.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        dep=load_dependencies(snapshot)
        cases=build_collection(json.loads(CASE_FIXTURE.read_text(encoding="utf-8")),dep,snapshot)
        notes=build_notifications(json.loads(NOTE_SPEC.read_text(encoding="utf-8")),
                                  cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,
                              json.loads(RUBRIC_PATH.read_text(encoding="utf-8")),
                              json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
        editorial=build_editorial(json.loads(EDITORIAL_FIXTURE.read_text(encoding="utf-8")),
                                 quality,notes)
        ready=build_readiness(json.loads(READINESS_FIXTURE.read_text(encoding="utf-8")),
                              editorial)
        gng=build_gng(json.loads(GNG_PACKAGE.read_text(encoding="utf-8")),ready)
        sequence=build_sequence(json.loads(SEQUENCE_SPEC.read_text(encoding="utf-8")),gng)
        submitted_sequence=json.loads(args.sequence.read_text(encoding="utf-8"))
        submitted_gng=json.loads(args.gng.read_text(encoding="utf-8"))
        fixture=json.loads(args.fixture.read_text(encoding="utf-8"))
        require(submitted_sequence==sequence and submitted_gng==gng
                and fixture==json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
                "contradiction: untrusted or modified source case, review or fixture")
        report=build_report(fixture,sequence,gng)
        output=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(output,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(report),encoding="utf-8")
        print(output)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayTransmitSap":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
