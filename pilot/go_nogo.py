"""Ciclo 20 — go/no-go de projeto privado: REGRA FINAL NO_GO.

Somente contratos e dados SIMULADOS públicos. Este módulo não recebe,
autentica, assina, inspeciona ou autoriza evidência corporativa/OEM real.
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
from pilot.readiness import (
    FIXTURE_PATH as READINESS_FIXTURE, CONTROL_MAP, THREATS, STAKEHOLDERS,
    CLASS_POLICY, build_report as build_readiness)
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_FIXTURE, build_report as build_editorial
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as build_quality
from notifications.drafts import SPEC_PATH as NOTE_SPEC, build_notifications
from casefiles.integrated import FIXTURE_PATH as CASES_FIXTURE, load_dependencies, build_collection

PACKAGE_PATH=ROOT/"pilot/go-nogo-package.v1.json"
DEPENDENCIES={
    "identity-proof":(),
    "competence":("identity-proof",),
    "conflict-screen":("identity-proof",),
    "two-independent-reviews":("competence","conflict-screen","version-lock"),
    "signed-decision":("identity-proof","version-lock"),
    "trusted-audit":("signed-decision",),
    "oem-effectivity":("equipment-configuration","evidence-legitimacy"),
    "equipment-configuration":(),
    "evidence-legitimacy":("privacy-retention",),
    "version-lock":("identity-proof",),
    "revocation-reopen":("identity-proof","version-lock"),
    "privacy-retention":(),
    "operational-firewall":("signed-decision","trusted-audit","oem-effectivity"),
}
PHASES=("requirements_defined","evidence_not_submitted",
        "externally_review_pending","no_go")
FORBIDDEN=("go","operationally_ready","approved")
PACKAGE_KEYS={"schema","version","mode","sourceReadiness","allApprovalsAbsent",
              "realEvidenceImported","requirementPhase","controlPlan","workstreams",
              "scenarios","retentionClassification","studyDesign","transitionPolicy",
              "operationalAuthority"}
CONTROL_KEYS={"controlId","owner","requiredEvidenceKind","acceptanceTest",
              "dependsOn","status","evidenceManifestId","evidenceUri",
              "evidenceSha256","externalReviewerIdentityVerified",
              "independentAcceptanceRecorded","canAdvance"}
WORK_KEYS={"owner","goNoGoState","signoffVerified","signoffEvidence",
           "blockers","mayAuthorizePilot"}
SCENARIO_KEYS={"scenarioId","threatId","failedControls","expectedOutcome",
               "findingId","remediationState","realIncidentObserved"}
STUDY_KEYS={"scope","rubricLockedExternally","legalBasisAndParticipantInformationApproved",
            "samplingMethodPreRegistered","reviewerQualificationVerified",
            "independentAssignmentVerified","blindingPlanApproved",
            "nominalKappaMeasured","ordinalWeightedKappaMeasured",
            "multiraterMethodSelected","adjudicationMethodApproved",
            "privacyApprovalVerified","fieldDiagnosticAccuracyEstablished"}
OPERATION_KEYS={"mayWriteSap","mayChangeEcm","mayRequestParts",
                "mayApproveMaintenance","mayReleaseEquipment","mayCollectPrivateData"}

def strict(obj,expected,label):
    require(isinstance(obj,dict) and set(obj)==expected,
            f"go-no-go: invalid {label} shape")
    return obj

def all_false(obj,keys,label):
    require(all(obj.get(key) is False for key in keys),
            f"go-no-go: fabricated approval in {label}")

def validate_package(package,readiness):
    p=strict(package,PACKAGE_KEYS,"package")
    require(p["schema"]=="maintenance-superinteligence.go-nogo-package.v1"
            and p["version"]=="1.0.0"
            and p["mode"]=="offline_public_synthetic_requirements"
            and p["sourceReadiness"]=="pilot/readiness-fixture.v1.json"
            and p["allApprovalsAbsent"] is True
            and p["realEvidenceImported"] is False
            and p["requirementPhase"]=="requirements_defined",
            "go-no-go: no private pilot authorized")
    require(readiness["schema"]=="maintenance-superinteligence.private-pilot-readiness-report.v1"
            and readiness["controlCount"]==13
            and readiness["verifiedControlCount"]==0
            and readiness["verifiedSignoffCount"]==0
            and readiness["readinessDecision"]=="blocked_no_external_evidence"
            and readiness["realPilotAuthorized"] is False
            and readiness["mayWriteSap"] is False,
            "go-no-go: only unverified readiness input accepted")
    require(isinstance(p["controlPlan"],list)
            and len(p["controlPlan"])==len(CONTROL_MAP)
            and [x.get("controlId") for x in p["controlPlan"]]==list(CONTROL_MAP),
            "go-no-go: required 13 controls omitted or reordered")
    for i,(c,source) in enumerate(zip(p["controlPlan"],readiness["requiredExternalEvidence"]),1):
        strict(c,CONTROL_KEYS,"control")
        owner,kind,_=CONTROL_MAP[c["controlId"]]
        require(c["owner"]==owner and c["requiredEvidenceKind"]==kind
                and c["controlId"]==source["controlId"]
                and c["acceptanceTest"]==
                  "Revisão externa autenticada para: "+source["missingEvidence"]
                and c["dependsOn"]==list(DEPENDENCIES[c["controlId"]])
                and all(d in CONTROL_MAP and d!=c["controlId"] for d in c["dependsOn"])
                and c["status"]=="evidence_not_submitted"
                and c["evidenceManifestId"]==f"SIM-PROOF-{i:02}"
                and c["evidenceUri"] is None
                and c["evidenceSha256"] is None,
                "go-no-go: unverifiable evidence, dependency or owner")
        all_false(c,("externalReviewerIdentityVerified",
                     "independentAcceptanceRecorded","canAdvance"),"control")
    # Acyclic prerequisites must be checkable in a real service later.
    visiting=set()
    visited=set()
    def visit(cid):
        require(cid not in visiting,"go-no-go: cyclic dependencies")
        if cid in visited:
            return
        visiting.add(cid)
        for dep in DEPENDENCIES[cid]:
            visit(dep)
        visiting.remove(cid)
        visited.add(cid)
    for cid in CONTROL_MAP:
        visit(cid)
    require(isinstance(p["workstreams"],list) and len(p["workstreams"])==5
            and [w.get("owner") for w in p["workstreams"]]==list(STAKEHOLDERS),
            "go-no-go: missing stakeholder")
    for w in p["workstreams"]:
        strict(w,WORK_KEYS,"stakeholder")
        require(w["goNoGoState"]=="externally_review_pending"
                and w["signoffEvidence"] is None
                and w["blockers"]==[c["controlId"] for c in p["controlPlan"]
                                   if c["owner"]==w["owner"]],
                "go-no-go: missing control dependencies")
        all_false(w,("signoffVerified","mayAuthorizePilot"),"stakeholder")
    require(isinstance(p["scenarios"],list)
            and len(p["scenarios"])==len(THREATS)
            and [s.get("threatId") for s in p["scenarios"]]==list(THREATS),
            "go-no-go: missing security adversary")
    for i,s in enumerate(p["scenarios"],1):
        strict(s,SCENARIO_KEYS,"scenario")
        require(s["scenarioId"]==f"SIM-GNG-THREAT-{i:02}"
                and s["failedControls"]==list(THREATS[s["threatId"]])
                and s["expectedOutcome"]=="no_go"
                and s["findingId"]==f"SIM-FIND-{i:02}"
                and s["remediationState"]=="not_started"
                and s["realIncidentObserved"] is False,
                "go-no-go: forged safety result")
    require(isinstance(p["retentionClassification"],list)
            and len(p["retentionClassification"])==len(CLASS_POLICY)
            and [r.get("dataClass") for r in p["retentionClassification"]]
                ==list(CLASS_POLICY),"go-no-go: missing data classification")
    for r in p["retentionClassification"]:
        strict(r,{"dataClass","allowedRepository","retentionDays",
                  "retentionApproved","realDataIncluded"},"retention")
        expected_repository,_=CLASS_POLICY[r["dataClass"]]
        require(r["allowedRepository"]==expected_repository
                and r["retentionDays"] is None,
                "go-no-go: invented data retention/license")
        all_false(r,("retentionApproved","realDataIncluded"),"retention")
    study=strict(p["studyDesign"],STUDY_KEYS,"human study")
    require(study["scope"]=="future_private_authorized_study_only",
            "go-no-go: pilot consent/field validity not established")
    all_false(study,STUDY_KEYS-{"scope"},"study")
    transition=strict(p["transitionPolicy"],
                      {"allowed","forbidden","default","current","realGoLivePermitted"},
                      "transition")
    require(transition["allowed"]==list(PHASES)
            and transition["forbidden"]==list(FORBIDDEN)
            and transition["default"]==transition["current"]=="no_go"
            and transition["realGoLivePermitted"] is False,
            "go-no-go: prohibited go or authorized state")
    operational=strict(p["operationalAuthority"],OPERATION_KEYS,"operational boundary")
    all_false(operational,OPERATION_KEYS,"operational boundary")
    return p

def build_report(package,readiness):
    p=validate_package(package,readiness)
    by_owner={owner:[c for c in p["controlPlan"] if c["owner"]==owner]
              for owner in STAKEHOLDERS}
    manifest=[{
        "manifestId":c["evidenceManifestId"],
        "controlId":c["controlId"],
        "evidenceKind":c["requiredEvidenceKind"],
        "sourceCategory":"external_private_future_requirement_only",
        "status":"evidence_not_submitted",
        "evidenceBytes":None,
        "evidenceReference":None,
        "authenticatedSubmitterVerified":False,
        "authorizedDataProvenanceVerified":False,
        "oemSeriesEffectivityVerified":False,
    } for c in p["controlPlan"]]
    dependencies=[{
        "controlId":cid,
        "predecessors":list(pred),
        "allPrerequisitesVerified":False,
        "permissionToProceed":False,
    } for cid,pred in DEPENDENCIES.items()]
    stakeholder_reviews=[{
        "owner":owner,
        "reviewedControlIds":[c["controlId"] for c in by_owner[owner]],
        "reviewState":"externally_review_pending",
        "verifiedReviewer":False,
        "signedAcceptance":False,
        "reviewProof":None,
        "outcome":"no_go",
    } for owner in STAKEHOLDERS]
    remediation=[{
        "findingId":s["findingId"],
        "threatId":s["threatId"],
        "requiredControlIds":list(s["failedControls"]),
        "requiredNextAction":"external_evidence_and_independent_review_required",
        "remediationStatus":"not_started",
        "dueDate":None,
        "assignedPerson":None,
        "verifiedClosure":False,
        "mayLiftBlock":False,
    } for s in p["scenarios"]]
    return {
        "schema":"maintenance-superinteligence.go-nogo-report.v1",
        "version":"1.0.0",
        "mode":"public_synthetic_contract_verification_only",
        "packageSha256":sha(p),
        "sourceReadinessSha256":sha(readiness),
        "sourcePublicFmeaSha256":readiness["sourceFmeaSnapshotSha256"],
        "requirementsPhase":"requirements_defined",
        "evidenceState":"evidence_not_submitted",
        "externalReviewState":"externally_review_pending",
        "decision":"no_go",
        "decisionReasons":(
            "13 required evidence packages missing",
            "5 external stakeholder signoffs not authenticated",
            "10 adversarial mitigations not demonstrated",
            "actual OEM applicability, privacy and authenticated human review unverified",
        ),
        "evidenceManifest":manifest,
        "evidencePackageCount":13,
        "verifiedEvidenceCount":0,
        "approvalDependencies":dependencies,
        "dependencyCount":13,
        "stakeholderReviews":stakeholder_reviews,
        "stakeholderCount":5,
        "verifiedSignoffs":0,
        "findingRemediations":remediation,
        "findingCount":10,
        "verifiedRemediations":0,
        "classification":list(p["retentionClassification"]),
        "studyProtocol":dict(p["studyDesign"]),
        "acceptanceGates":{
            "identityAuthenticated":False,
            "reviewerCompetenceVerified":False,
            "independentRealReviewComplete":False,
            "realSignatureVerified":False,
            "oemEffectivityVerified":False,
            "corporateSecurityApproved":False,
            "legalBasisApproved":False,
            "actualPilotSafetyApproved":False,
        },
        "noOperationalAuthority":dict(p["operationalAuthority"]),
        "realPilotExecuted":False,
        "realGoDecisionSigned":False,
        "expertAgreementMeasured":False,
        "externalImmutableAuditVerified":False,
    }

def verify_report(report,package,readiness):
    require(report==build_report(package,readiness),
            "go-no-go: forged decision, signature, permission or evidence")
    return report

def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.go-nogo-report.v1"
            and report.get("decision")=="no_go"
            and report.get("requirementsPhase")=="requirements_defined"
            and report.get("evidenceState")=="evidence_not_submitted"
            and report.get("externalReviewState")=="externally_review_pending"
            and report.get("evidencePackageCount")==13
            and report.get("verifiedEvidenceCount")==0
            and report.get("stakeholderCount")==5
            and report.get("verifiedSignoffs")==0
            and report.get("findingCount")==10
            and report.get("verifiedRemediations")==0
            and report.get("realPilotExecuted") is False
            and report.get("realGoDecisionSigned") is False
            and report.get("expertAgreementMeasured") is False
            and report.get("externalImmutableAuditVerified") is False
            and all(v is False for v in report.get("acceptanceGates",{}).values())
            and all(v is False for v in report.get("noOperationalAuthority",{}).values())
            and len(report.get("evidenceManifest",[]))==13
            and all(c.get("status")=="evidence_not_submitted"
                    and c.get("evidenceBytes") is None
                    and c.get("evidenceReference") is None
                    and c.get("authenticatedSubmitterVerified") is False
                    for c in report["evidenceManifest"])
            and len(report.get("stakeholderReviews",[]))==5
            and all(s.get("outcome")=="no_go"
                    and s.get("signedAcceptance") is False
                    and s.get("verifiedReviewer") is False
                    for s in report["stakeholderReviews"])
            and len(report.get("findingRemediations",[]))==10
            and all(x.get("verifiedClosure") is False
                    and x.get("mayLiftBlock") is False
                    for x in report["findingRemediations"]),
            "go-no-go HTML: fabricated source approval")
    esc=lambda x:escape(str(x),quote=True)
    rows="".join("<tr><td>"+esc(s["owner"])+"</td><td>"
                 +esc(", ".join(s["reviewedControlIds"]))+"</td><td>"
                 +esc(s["reviewState"])+"</td></tr>"
                 for s in report["stakeholderReviews"])
    proofs="".join("<li>"+esc(p["controlId"])+" — "+esc(p["evidenceKind"])
                   +" : "+esc(p["status"])+"</li>"
                   for p in report["evidenceManifest"])
    threats="".join("<li>"+esc(f["threatId"])+" — "
                     +esc(f["requiredNextAction"])+"</li>"
                     for f in report["findingRemediations"])
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
        + "form-action &apos;none&apos;" + '"><title>Go/No-Go: NO GO</title>'
        '<style>body{font:15px system-ui,sans-serif;max-width:1100px;margin:1rem auto;'
        'padding:1rem;background:#fafafa;color:#222}table{border-collapse:collapse;'
        'width:100%}th,td{border:1px solid #ddd;padding:.6rem;text-align:left}'
        '.blocked{border-left:5px solid #a22;background:#fff0f0;padding:1rem}'
        '</style></head><body><h1>Piloto privado: decisão NO GO</h1>'
        '<p class="blocked">Exercício público sem evidência privada, identidade,'
        ' revisão OEM, consentimento, verificação humana, SAP, ECM ou autorização'
        ' de operação. Nenhum campo preenchido equivale a assinatura real.</p>'
        '<h2>Cinco revisões externas pendentes</h2>'
        '<table><thead><tr><th>Área</th><th>Controles</th><th>Estado</th>'
        '</tr></thead><tbody>'+rows+'</tbody></table>'
        '<h2>13 evidências ainda não submetidas</h2><ul>'+proofs+'</ul>'
        '<h2>10 achados sintéticos não resolvidos</h2><ul>'+threats+'</ul>'
        '<footer>Arquivo estático offline; nenhum JS, envio SAP, login ou rede.'
        '</footer></body></html>\n'
    )

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",required=True,type=Path)
    parser.add_argument("--readiness",required=True,type=Path)
    parser.add_argument("--package",default=PACKAGE_PATH,type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        deps=load_dependencies(snapshot)
        cases=build_collection(json.loads(CASES_FIXTURE.read_text(encoding="utf-8")),deps,snapshot)
        notes=build_notifications(json.loads(NOTE_SPEC.read_text(encoding="utf-8")),
                                  cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,
                              json.loads(RUBRIC_PATH.read_text(encoding="utf-8")),
                              json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
        editorial=build_editorial(json.loads(EDITORIAL_FIXTURE.read_text(encoding="utf-8")),
                                 quality,notes)
        readiness=build_readiness(json.loads(READINESS_FIXTURE.read_text(encoding="utf-8")),
                                  editorial)
        given=json.loads(args.readiness.read_text(encoding="utf-8"))
        package=json.loads(args.package.read_text(encoding="utf-8"))
        require(given==readiness and package==json.loads(PACKAGE_PATH.read_text(encoding="utf-8")),
                "go-no-go: altered upstream readiness or requirement package")
        report=build_report(package,readiness)
        payload=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(payload,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(report),encoding="utf-8")
        print(payload)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayWriteSap":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
