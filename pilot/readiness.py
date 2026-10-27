"""Ciclo 19 — contrato de prontidão de PILOTO FUTURO. Tudo negado.

Este módulo NÃO autentica pessoas, NÃO verifica OEM/assinaturas, NÃO avalia
dados corporativos e NÃO estabelece prontidão de campo. Apenas valida,
reconstrói e exibe requisitos de segurança públicos em cenários sintéticos.
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
from casefiles.integrated import FIXTURE_PATH as CASES_PATH, load_dependencies, build_collection
from notifications.drafts import SPEC_PATH as NOTES_SPEC, build_notifications
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as build_quality
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_PATH, build_report as build_editorial

FIXTURE_PATH = ROOT / "pilot/readiness-fixture.v1.json"
SOURCE_LINKS = {
    "NIST-800-63-4": ("https://csrc.nist.gov/pubs/sp/800/63/4/final",
                      "identity_proofing_authentication_federation"),
    "ASVS-5.0.0": ("https://asvs.owasp.org/",
                   "application_security_requirements"),
    "LGPD-13709": ("https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
                    "data_minimization_security_governance"),
    "OEM-APPLICABILITY-PENDING": (None, "engineering_effectivity_requires_authorized_oem_documentation"),
}
STAKEHOLDERS = ("IT","InformationSecurity","Engineering","Legal",
                "MaintenanceManagement")
CONTROL_MAP = {
    "identity-proof": ("IT","authenticated-principal","NIST-800-63-4"),
    "competence": ("Engineering","reviewer-competence-evidence","NIST-800-63-4"),
    "conflict-screen": ("Legal","conflict-of-interest-screening","LGPD-13709"),
    "two-independent-reviews": ("Engineering","independent-review-decisions","ASVS-5.0.0"),
    "signed-decision": ("InformationSecurity","signature-verification","ASVS-5.0.0"),
    "trusted-audit": ("InformationSecurity","audit-anchor","ASVS-5.0.0"),
    "oem-effectivity": ("Engineering","oem-applicability-proof","OEM-APPLICABILITY-PENDING"),
    "equipment-configuration": ("MaintenanceManagement","configuration-attestation","OEM-APPLICABILITY-PENDING"),
    "evidence-legitimacy": ("Legal","authorized-evidence-package","LGPD-13709"),
    "version-lock": ("IT","version-lock","ASVS-5.0.0"),
    "revocation-reopen": ("IT","revocation-and-reopen-policy","NIST-800-63-4"),
    "privacy-retention": ("Legal","privacy-retention-policy","LGPD-13709"),
    "operational-firewall": ("MaintenanceManagement","operational-boundary","ASVS-5.0.0"),
}
THREATS = {
    "duplicate-principal": ("identity-proof","two-independent-reviews"),
    "expired-credential": ("identity-proof","revocation-reopen"),
    "forged-signature": ("signed-decision","trusted-audit"),
    "oem-revision-change": ("oem-effectivity","revocation-reopen"),
    "equipment-configuration-change": ("equipment-configuration","version-lock"),
    "unreported-conflict": ("conflict-screen","two-independent-reviews"),
    "unauthorized-sap-note": ("operational-firewall","version-lock"),
    "pii-telemetry-leak": ("privacy-retention","evidence-legitimacy"),
    "audit-log-tampering": ("trusted-audit","signed-decision"),
    "unlicensed-oem-copy": ("evidence-legitimacy","oem-effectivity"),
}
SCENARIOS = (
    ("baseline-no-real-proof","SIM-NOTE-001","none"),
    ("credential-revoked","SIM-NOTE-002","reviewer_credential_revoked"),
    ("oem-document-superseded","SIM-NOTE-003","oem_revision_changed"),
    ("equipment-configuration-altered","SIM-NOTE-004","equipment_configuration_changed"),
)
FIELDS = {"schema","version","purpose","sourceEditorial","sourceRubric",
          "identityProviderConnected","licensedOemDocumentAvailable",
          "physicalEvidenceAvailable","corporateDataImported",
          "mayRunPrivatePilot","mayIssueSapNotification","sources",
          "stakeholders","controls","threats","classificationPolicy",
          "scenarios","studyProtocol"}
STUDY_KEYS = {
    "consentAndLegalBasisApproved","reviewerCompetenceVerified",
    "independentRatersAssigned","preRegisteredEvaluationMethod",
    "anonymizationValidated","realAgreementMeasured",
    "benchmarkFieldQualityValidated",
}
BOUNDARIES = (
    "identity and authorization require corporate IdP and verified uniqueness",
    "competence and independence require authenticated private evidence",
    "two independent human reviews require the current immutable document revision",
    "OEM publication, revision, licensing, series effectivity and machine configuration require independent authorized checking",
    "secure evidence, retention, encryption and immutable audit logs must exist outside this public repository",
    "legal basis and purpose limitation require written review before private pilot",
    "technical review is not an equipment release, SAP/ECM action or a work permit",
)
CLASS_POLICY = {
    "public-synthetic":("public",("SIM-NOTE","synthetic_boolean_gates")),
    "corporate-private":("private_approved_only",("SAP-credentials-prohibited-here","telemetry-prohibited-here")),
    "oem-licensed":("licensed_restricted_only",("OEM-copyrighted-manual-prohibited-here",)),
}
PROOF_UNAVAILABLE = ("authenticated=false","signatureVerified=false",
                     "oemSeriesApproved=false","auditExternallyAnchored=false",
                     "fieldSafetyEvaluated=false")

def exact(o,keys,where):
    require(isinstance(o,dict) and set(o)==keys,
            f"pilot: {where}: unrecognized or missing field")
    return o

def validate_fixture(raw,editorial):
    x=exact(raw,FIELDS,"fixture")
    require(x["schema"]=="maintenance-superinteligence.private-pilot-readiness-fixture.v1"
            and x["version"]=="1.0.0"
            and x["purpose"]=="public_offline_requirements_only_not_private_pilot"
            and x["sourceEditorial"]=="editorial/review-fixture.v1.json"
            and x["sourceRubric"]=="quality/notification-rubric.v1.json"
            and all(x[k] is False for k in (
                "identityProviderConnected","licensedOemDocumentAvailable",
                "physicalEvidenceAvailable","corporateDataImported",
                "mayRunPrivatePilot","mayIssueSapNotification")),
            "pilot: source authentication or field authority fabricated")
    require(editorial["schema"]=="maintenance-superinteligence.editorial-review-report.v1"
            and editorial["caseCount"]==4
            and editorial["realReviewsCompleted"]==0
            and editorial["realApprovalsGranted"]==0
            and editorial["externalImmutableAuditLogVerified"] is False
            and editorial["mayWriteToSap"] is False,
            "pilot: only canonical fictional editorial input allowed")
    require(isinstance(x["sources"],list) and len(x["sources"])==4
            and [s.get("sourceId") for s in x["sources"]]==list(SOURCE_LINKS),
            "pilot: known public reference list required")
    for s in x["sources"]:
        exact(s,{"sourceId","uri","scope","evidenceOfCompliance"},"source")
        link,scope=SOURCE_LINKS[s["sourceId"]]
        require(s["uri"]==link and s["scope"]==scope
                and s["evidenceOfCompliance"] is False,
                "pilot: source metadata cannot constitute certification")
    require(isinstance(x["stakeholders"],list)
            and [s.get("owner") for s in x["stakeholders"]]==list(STAKEHOLDERS),
            "pilot: five stakeholder signoffs required")
    for s in x["stakeholders"]:
        exact(s,{"owner","signoff","qualifiedSignatoryVerified",
                 "externalApprovalProof","canApproveOperations"},"stakeholder")
        require(s["signoff"]=="not_requested"
                and s["qualifiedSignatoryVerified"] is False
                and s["externalApprovalProof"] is None
                and s["canApproveOperations"] is False,
                "pilot: real signoff not available in public mode")
    require(isinstance(x["controls"],list)
            and [c.get("controlId") for c in x["controls"]]==list(CONTROL_MAP),
            "pilot: all 13 controls required")
    for c in x["controls"]:
        exact(c,{"controlId","owner","proofKind","sourceId","acceptanceCondition",
                 "proofStatus","authorityVerified","externalEvidenceRef",
                 "mayWaive"},"control")
        owner,kind,src=CONTROL_MAP[c["controlId"]]
        require(c["owner"]==owner and c["proofKind"]==kind
                and c["sourceId"]==src
                and isinstance(c["acceptanceCondition"],str)
                and 35<=len(c["acceptanceCondition"])<=220
                and c["proofStatus"]=="not_provided"
                and c["authorityVerified"] is False
                and c["externalEvidenceRef"] is None
                and c["mayWaive"] is False,
                "pilot: fake verified control, altered ownership or bypass")
    require(isinstance(x["threats"],list)
            and [t.get("threatId") for t in x["threats"]]==list(THREATS),
            "pilot: exact threat register required")
    for t in x["threats"]:
        exact(t,{"threatId","controlIds","scenarioNature","expectedDecision",
                 "fieldExposureObserved"},"threat")
        require(t["controlIds"]==list(THREATS[t["threatId"]])
                and t["scenarioNature"]=="synthetic_threat_only"
                and t["expectedDecision"]=="deny_and_require_external_revalidation"
                and t["fieldExposureObserved"] is False,
                "pilot: threat bypass or physical observation fabricated")
    require(isinstance(x["classificationPolicy"],list)
            and [p.get("dataClass") for p in x["classificationPolicy"]]
                ==list(CLASS_POLICY),
            "pilot: public/private/licensed partition incomplete")
    for p in x["classificationPolicy"]:
        exact(p,{"dataClass","allowedRepository","realDataAllowed",
                 "retentionDays","retentionApprovalVerified","examples"},
              "data classification")
        repo,examples=CLASS_POLICY[p["dataClass"]]
        require(p["allowedRepository"]==repo and p["examples"]==list(examples)
                and p["realDataAllowed"] is False
                and p["retentionDays"] is None
                and p["retentionApprovalVerified"] is False,
                "pilot: copyrighted/private data or retention authorization fabricated")
    require(isinstance(x["scenarios"],list) and len(x["scenarios"])==4,
            "pilot: four synthetic scenarios expected")
    for i,c in enumerate(x["scenarios"]):
        exact(c,{"scenarioId","draftId","trigger","expectedState",
                 "documentRevisionCurrent","currentReviewValid",
                 "confidentialDataUsed","mayReleaseEquipment"},"scenario")
        name,draft,trigger=SCENARIOS[i]
        require(c["scenarioId"]==name and c["draftId"]==draft
                and c["trigger"]==trigger
                and c["expectedState"]=="blocked_pending_external_verification"
                and all(c[k] is False for k in (
                    "documentRevisionCurrent","currentReviewValid",
                    "confidentialDataUsed","mayReleaseEquipment")),
                "pilot: source revision or operational readiness claim")
    study=exact(x["studyProtocol"],STUDY_KEYS,"study")
    require(all(v is False for v in study.values()),
            "pilot: fictitious inter-rater agreement or consent")
    return x

def build_report(fixture,editorial):
    x=validate_fixture(fixture,editorial)
    assessment=[
        {"controlId":c["controlId"],"owner":c["owner"],
         "proofKind":c["proofKind"],"referenceId":c["sourceId"],
         "missingEvidence":c["acceptanceCondition"],
         "status":"not_verified",
         "proofCount":0,"canWaive":False,
         "mayEnablePrivatePilot":False}
        for c in x["controls"]]
    review_scenarios=[]
    previous=sha({"sourceEditorialSha256":sha(editorial),
                  "fixtureSha256":sha(x),
                  "purpose":"synthetic_reopen_policy_only"})
    for s in x["scenarios"]:
        trigger=s["trigger"]
        affected=("reviewer_identity" if trigger=="reviewer_credential_revoked"
                  else "oem_effectivity" if trigger=="oem_revision_changed"
                  else "equipment_configuration" if trigger=="equipment_configuration_changed"
                  else "all_controls_unverified")
        reopening=trigger!="none"
        trace={"scenarioId":s["scenarioId"],"draftId":s["draftId"],
               "trigger":trigger,"affectedValidation":affected,
               "reopenRequired":reopening,
               "previousReviewIsBinding":False,
               "sourceDocumentCurrent":False,
               "evidenceOfCurrentIndependentReview":False,
               "decision":"blocked_pending_external_verification",
               "mayOpenSapNotification":False,
               "mayRunPhysicalInspection":False,
               "mayReleaseEquipment":False}
        digest=sha({"prev":previous,"scenario":trace})
        trace["previousDigest"]=previous
        trace["eventDigest"]=digest
        review_scenarios.append(trace)
        previous=digest
    threats=[{"threatId":t["threatId"],"requiredControlIds":list(t["controlIds"]),
              "observedPhysicalExposure":False,
              "mitigationExternallyVerified":False,
              "status":"unverified_mitigation",
              "decision":"deny_and_require_external_revalidation"}
             for t in x["threats"]]
    return {
        "schema":"maintenance-superinteligence.private-pilot-readiness-report.v1",
        "version":"1.0.0",
        "purpose":"contract_testing_not_private_pilot_approval",
        "fixtureSha256":sha(x),
        "editorialReviewSha256":sha(editorial),
        "sourceFmeaSnapshotSha256":editorial["publicFmeaSnapshotSha256"],
        "sourceLinks":list(SOURCE_LINKS),
        "controlCount":len(assessment),
        "verifiedControlCount":0,
        "requiredExternalEvidence":assessment,
        "signoffCount":len(x["stakeholders"]),
        "verifiedSignoffCount":0,
        "signoffs":[{"owner":g["owner"],"status":"not_requested",
                     "qualifiedSignerVerified":False}
                    for g in x["stakeholders"]],
        "threatCount":len(threats),
        "threats":threats,
        "scenarioCount":len(review_scenarios),
        "scenarios":review_scenarios,
        "scenarioAuditHeadDigest":previous,
        "externalAuditAnchorVerified":False,
        "dataClasses":[{"dataClass":p["dataClass"],
                        "allowedRepository":p["allowedRepository"],
                        "realDataInPublicRepo":False,
                        "retentionPolicyApproved":False}
                       for p in x["classificationPolicy"]],
        "studyProtocol":dict(x["studyProtocol"]),
        "externalProofGaps":list(PROOF_UNAVAILABLE),
        "acceptanceCriteria":list(BOUNDARIES),
        "readinessDecision":"blocked_no_external_evidence",
        "realPilotAuthorized":False,
        "pilotExecuted":False,
        "realExpertAgreementMeasured":False,
        "mayWriteSap":False,
        "mayAlterEcm":False,
        "mayApproveMaintenance":False,
        "mayReleaseEquipment":False,
    }

def verify_report(report,fixture,editorial):
    require(report==build_report(fixture,editorial),
            "pilot: report, review, proof or hash altered")
    return report

def render_html(report):
    require(report.get("schema")
            =="maintenance-superinteligence.private-pilot-readiness-report.v1"
            and report.get("readinessDecision")=="blocked_no_external_evidence"
            and report.get("controlCount")==13
            and report.get("verifiedControlCount")==0
            and report.get("signoffCount")==5
            and report.get("verifiedSignoffCount")==0
            and report.get("threatCount")==10
            and report.get("scenarioCount")==4
            and report.get("realPilotAuthorized") is False
            and report.get("pilotExecuted") is False
            and report.get("externalAuditAnchorVerified") is False
            and report.get("realExpertAgreementMeasured") is False
            and report.get("mayWriteSap") is False
            and report.get("mayAlterEcm") is False
            and report.get("mayApproveMaintenance") is False
            and report.get("mayReleaseEquipment") is False,
            "pilot HTML: misleading field approval")
    require(all(c.get("status")=="not_verified"
                and c.get("proofCount")==0
                and c.get("canWaive") is False
                and c.get("mayEnablePrivatePilot") is False
                for c in report.get("requiredExternalEvidence",[]))
            and all(t.get("mitigationExternallyVerified") is False
                    and t.get("status")=="unverified_mitigation"
                    for t in report.get("threats",[]))
            and all(s.get("decision")=="blocked_pending_external_verification"
                    and s.get("mayOpenSapNotification") is False
                    and s.get("mayReleaseEquipment") is False
                    and s.get("sourceDocumentCurrent") is False
                    for s in report.get("scenarios",[]))
            and all(g.get("status")=="not_requested"
                    and g.get("qualifiedSignerVerified") is False
                    for g in report.get("signoffs",[]))
            and all(x is False for x in report.get("studyProtocol",{}).values()),
            "pilot HTML: evidence or reviewer status forged")
    esc=lambda x:escape(str(x),quote=True)
    controls="".join("<tr><td>"+esc(c["controlId"])+"</td><td>"
                     +esc(c["owner"])+"</td><td>"
                     +esc(c["missingEvidence"])+"</td><td>"
                     +esc(c["status"])+"</td></tr>"
                     for c in report["requiredExternalEvidence"])
    threats="".join("<li>"+esc(t["threatId"])+": "
                    +esc(", ".join(t["requiredControlIds"]))+"</li>"
                    for t in report["threats"])
    scenarios="".join("<li>"+esc(s["draftId"])+" / "+esc(s["trigger"])
                      +" — "+esc(s["decision"])+"</li>"
                      for s in report["scenarios"])
    signoffs="".join("<li>"+esc(x["owner"])+": "+esc(x["status"])+"</li>"
                    for x in report["signoffs"])
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
        + "form-action &apos;none&apos;" + '"><title>Prontidão privada — bloqueada</title>'
        '<style>body{font:15px system-ui,sans-serif;max-width:1150px;margin:1rem auto;'
        'padding:1rem;background:#fafafa;color:#242424}table{border-collapse:collapse;'
        'width:100%}th,td{padding:.5rem;border:1px solid #ddd;text-align:left}'
        '.warning{border-left:5px solid #a22;background:#fff0f0;padding:1rem}</style>'
        '</head><body><h1>Requisitos para piloto privado — NÃO AUTORIZADO</h1>'
        '<p class="warning">Somente simulação pública. Zero identidade, assinatura,'
        ' OEM ou competência comprovada; zero consentimento/aceite externo.'
        ' Proibida qualquer emissão SAP, ajuste ECM, atividade física ou liberação.</p>'
        '<h2>13 controles ainda sem evidência</h2><table><thead><tr>'
        '<th>Controle</th><th>Responsável proposto</th><th>Evidência necessária</th>'
        '<th>Estado</th></tr></thead><tbody>'+controls+'</tbody></table>'
        '<h2>Cinco instâncias de aceite pendentes</h2><ul>'+signoffs+'</ul>'
        '<h2>Dez ameaças sem mitigação externamente demonstrada</h2><ul>'
        +threats+'</ul><h2>Quatro cenários de invalidação</h2><ul>'
        +scenarios+'</ul><footer>HTML offline, sem JavaScript, formulários,'
         ' autenticação ou comunicação com sistemas corporativos.</footer></body></html>\n'
    )

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",type=Path,required=True)
    parser.add_argument("--editorial",type=Path,required=True)
    parser.add_argument("--fixture",type=Path,default=FIXTURE_PATH)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        deps=load_dependencies(snapshot)
        cf=json.loads(CASES_PATH.read_text(encoding="utf-8"))
        cases=build_collection(cf,deps,snapshot)
        ns=json.loads(NOTES_SPEC.read_text(encoding="utf-8"))
        notes=build_notifications(ns,cases["cases"],cases["investigationTrees"])
        rubric=json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        oracle=json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        quality=build_quality(notes,cases,rubric,oracle)
        ed_fixture=json.loads(EDITORIAL_PATH.read_text(encoding="utf-8"))
        expected_editorial=build_editorial(ed_fixture,quality,notes)
        given_editorial=json.loads(args.editorial.read_text(encoding="utf-8"))
        fixture=json.loads(args.fixture.read_text(encoding="utf-8"))
        require(given_editorial==expected_editorial
                and fixture==json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
                "pilot: altered synthetic corpus, editorial review or readiness")
        report=build_report(fixture,expected_editorial)
        output=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(output,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(report),encoding="utf-8")
        print(output)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed","reason":str(exc),
                          "mayWriteSap":False},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
