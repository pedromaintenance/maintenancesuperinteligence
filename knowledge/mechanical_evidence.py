"""Cycle 33 — traceable technical CLAIMS, not diagnosis or OEM effectivity.

The catalog has manufacturer/standard public references with deliberate,
author-developed interpretation hypotheses. No measured damage, repair approval,
machine serial effectivity or independent validation is claimed here.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
from urllib.parse import urlparse

from benchmarks.mechanical_reasoning import DOMAIN_PATHS
from pilot.change_review_packets import require, digest

ROOT=Path(__file__).resolve().parents[1]
MAP_PATH=ROOT/"knowledge/mechanical-evidence-map.v1.json"
POLICY_PATH=ROOT/"knowledge/mechanical-evidence-policy.v1.json"
FAMILIES=("final_drive","hydraulics","electronics","cooling")
FAMILY_TO_COMPONENT={
    "final_drive":"gear_and_bearing_compartment",
    "hydraulics":"actuation_and_fluid_circuit",
    "electronics":"ecm_and_monitored_circuit",
    "cooling":"radiator_coolant_and_airflow",
}
FAMILY_TO_GATE={
    "final_drive":"fluid_identity",
    "hydraulics":"load_context",
    "electronics":"ecm_identity",
    "cooling":"duty_cycle",
}
CLAIM_TYPES={"manufacturer_general_indicator","manufacturer_tool_capability",
             "analogy_across_equipment"}
BRANCH_TYPES={"physical_mechanism_candidate","interpretation_confounder"}
CONFOUNDER_IDS={"MECH-KB-001","MECH-KB-007","MECH-KB-009"}
SOURCE_TYPES={"manufacturer_technical_article","public_standard_abstract",
              "manufacturer_maintenance_guide","manufacturer_tool_description",
              "manufacturer_product_overview"}
TRUSTED_HOSTS={"evolution.skf.com","www.iso.org","www.cat.com",
               "fluidcare-knowledge.hydac.com","www.perkins.com","h-cpc.cat.com"}
SOURCE_FIELDS={"id","owner","title","url","sourceType","supportedScope","notSupported"}
RECORD_FIELDS={"recordId","system","componentContext","function","functionalFailure",
               "reportedSymptom","branchType","candidateOrConfounder",
               "alternativeExplanation","nextDiscriminatingQuestion",
               "contextGate","sourceIds","supportType","supportNote",
               "informationState","rootCauseConfirmed","measurementsPerformed",
               "oemEffectivityVerified","expertReviewCompleted","permissionToTest",
               "permissionToCreateWorkOrder","permissionToReleaseMachine"}
DENIALS=("rootCauseConfirmed","measurementsPerformed","oemEffectivityVerified",
         "expertReviewCompleted","permissionToTest",
         "permissionToCreateWorkOrder","permissionToReleaseMachine")
POLICY_FIELDS={"schema","version","expectedDomains","minimumRecordsByDomain",
               "allowedSupportTypes","externalTechnicalReviewCompleted",
               "validationAgainstFieldCases","mayApproveRepair","mayApproveTest",
               "mayReleaseEquipment"}
MAP_FIELDS={"schema","version","purpose","realDataIncluded",
            "oemSeriesEffectivityEstablished","externalReviewCompleted",
            "operationallyApproved","sourceCatalog","records"}


def check_policy(policy):
    require(isinstance(policy,dict) and set(policy)==POLICY_FIELDS,
            "evidence policy invalid")
    require(policy["schema"]=="maintenance-superinteligence.mechanical-evidence-policy.v1"
            and policy["version"]=="1.0.0"
            and policy["expectedDomains"]==list(FAMILIES)
            and type(policy["minimumRecordsByDomain"]) is int
            and policy["minimumRecordsByDomain"]>=3
            and policy["allowedSupportTypes"]==sorted(CLAIM_TYPES)
            and all(policy[k] is False for k in
                    ("externalTechnicalReviewCompleted","validationAgainstFieldCases",
                     "mayApproveRepair","mayApproveTest","mayReleaseEquipment")),
            "policy broadened or falsely verified")
    return True


def require_text(record,fields):
    require(all(isinstance(record[k],str) and
                len(record[k].strip())>=20 for k in fields),
            "missing explanatory text in technical map")


def validate_map(manifest,policy):
    check_policy(policy)
    require(isinstance(manifest,dict) and set(manifest)==MAP_FIELDS,
            "evidence catalog format unexpected")
    require(manifest["schema"]=="maintenance-superinteligence.mechanical-evidence-map.v1"
            and manifest["version"]=="1.0.0"
            and manifest["purpose"]=="traceable_nonoperational_mechanism_hypothesis_taxonomy"
            and all(manifest[k] is False for k in
                    ("realDataIncluded","oemSeriesEffectivityEstablished",
                     "externalReviewCompleted","operationallyApproved")),
            "technical catalog falsely promoted as diagnostic proof")
    sources=manifest["sourceCatalog"]
    require(isinstance(sources,list) and 5<=len(sources)<=16,
            "inadequate public reference catalog")
    by_id={}
    for source in sources:
        require(isinstance(source,dict) and set(source)==SOURCE_FIELDS,
                "source metadata incomplete")
        ident=source["id"]
        require(isinstance(ident,str) and ident not in by_id and
                5<=len(ident)<=64, "duplicate/invalid reference")
        by_id[ident]=source
        require(source["sourceType"] in SOURCE_TYPES,
                "source type unknown")
        require_text(source,("title","supportedScope","notSupported"))
        url=source["url"]
        require(isinstance(url,str) and len(url)<350 and
                urlparse(url).scheme=="https" and
                urlparse(url).hostname in TRUSTED_HOSTS and
                not urlparse(url).username and not urlparse(url).password,
                "unapproved URL or external evidence source")
    records=manifest["records"]
    require(isinstance(records,list) and
            len(records)==len(FAMILIES)*policy["minimumRecordsByDomain"],
            "incomplete or expanded taxonomy without review")
    counts=Counter()
    labels=set()
    for i,r in enumerate(records,1):
        require(isinstance(r,dict) and set(r)==RECORD_FIELDS,
                "technical record malformed")
        require(r["recordId"]==f"MECH-KB-{i:03d}"
                and r["system"] in FAMILIES
                and r["system"]==FAMILIES[(i-1)//3]
                and r["componentContext"]==FAMILY_TO_COMPONENT[r["system"]]
                and r["contextGate"]==FAMILY_TO_GATE[r["system"]],
                "record id, equipment domain or context gate inconsistent")
        valid_gates={x[0] for x in DOMAIN_PATHS[r["system"]]["gates"]}
        require(r["contextGate"] in valid_gates,
                "context gate not in frozen differential selector")
        counts[r["system"]]+=1
        require(r["branchType"] in BRANCH_TYPES
                and (r["branchType"]=="interpretation_confounder")==
                    (r["recordId"] in CONFOUNDER_IDS),
                "a diagnostic confounder was promoted to physical mechanism")
        require_text(r,("function","functionalFailure","reportedSymptom",
                        "alternativeExplanation","nextDiscriminatingQuestion",
                        "supportNote"))
        label=r["candidateOrConfounder"]
        require(isinstance(label,str) and len(label)>=8 and
                label not in labels, "missing or duplicate hypothesis label")
        labels.add(label)
        require(isinstance(r["sourceIds"],list)
                and 1<=len(r["sourceIds"])<=3
                and len(set(r["sourceIds"]))==len(r["sourceIds"])
                and all(x in by_id for x in r["sourceIds"]),
                "missing or duplicated source provenance")
        require(r["supportType"] in CLAIM_TYPES
                and r["informationState"]=="unverified_in_this_project"
                and all(r[k] is False for k in DENIALS),
                "assumption presented as proven mechanism or authorized action")
    require(all(counts[f]==3 for f in FAMILIES),"incomplete system families")
    return records


def evaluate(manifest,policy):
    entries=validate_map(manifest,policy)
    branches=Counter(x["branchType"] for x in entries)
    support=Counter(x["supportType"] for x in entries)
    family=Counter(x["system"] for x in entries)
    known={x["id"] for x in manifest["sourceCatalog"]}
    linked={source for x in entries for source in x["sourceIds"]}
    return {
        "schema":"maintenance-superinteligence.mechanical-evidence-report.v1",
        "version":"1.0.0","mode":"traceable_technical_background_only",
        "manifestDigest":digest(manifest),"policyDigest":digest(policy),
        "sourceCount":len(known),"linkedSourceCount":len(linked),
        "recordCount":len(entries),
        "domains":{k:family[k] for k in FAMILIES},
        "physicalMechanismCandidates":branches["physical_mechanism_candidate"],
        "diagnosticInterpretationConfounders":branches["interpretation_confounder"],
        "supportTypes":{k:support[k] for k in sorted(CLAIM_TYPES)},
        "traceabilityPresent":True,
        "realPhysicalFailureCasesReviewed":0,
        "independentlyExpertValidated":False,
        "oemSerialEffectivityValidated":False,
        "realDiagnosticAccuracyEstablished":False,
        "mayApproveTest":False,
        "mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
        "decision":"technical_reference_only_no_go",
    }


def verify_report(report,manifest,policy):
    require(report==evaluate(manifest,policy),
            "evidence report drift, authoring change or fake validation")
    return True


def render_html(manifest,report):
    require(report==evaluate(manifest,
            json.loads(POLICY_PATH.read_text(encoding="utf-8")))
            and report["decision"]=="technical_reference_only_no_go"
            and report["mayCreateWorkOrder"] is False
            and report["mayReleaseEquipment"] is False,
            "HTML attempted to present an unverified maintenance decision")
    refs={x["id"]:x for x in manifest["sourceCatalog"]}
    blocks=[]
    for r in manifest["records"]:
        links="; ".join(escape(refs[x]["owner"])+": "+
                        '<a href="'+escape(refs[x]["url"],quote=True)+'">'+
                        escape(refs[x]["title"])+"</a>" for x in r["sourceIds"])
        blocks.append(
            "<article><h2>"+escape(r["recordId"])+" · "+escape(r["system"])+"</h2>"+
            "<p><b>Função:</b> "+escape(r["function"])+"</p>"+
            "<p><b>Falha funcional:</b> "+escape(r["functionalFailure"])+"</p>"+
            "<p><b>Sintoma:</b> "+escape(r["reportedSymptom"])+"</p>"+
            "<p><b>Hipótese/Confundidor:</b> "+
            escape(r["candidateOrConfounder"])+" ("+
            escape(r["branchType"])+")</p>"+
            "<p><b>Pergunta discriminante (documental):</b> "+
            escape(r["nextDiscriminatingQuestion"])+"</p>"+
            "<p><b>Fonte geral:</b> "+links+"</p>"+
            "<p><b>Limite:</b> "+escape(r["supportNote"])+"</p></article>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; "
            'base-uri &apos;none&apos;; form-action &apos;none&apos;">'
            '<title>Taxonomia técnica — P&D</title>'
            '<style>body{font:15px system-ui;max-width:980px;margin:2em auto;'
            'padding:1em}article{border:1px solid #bbb;margin:1em 0;padding:1em}'
            'a{color:inherit}</style></head><body>'
            '<h1>Ciclo 33 — Referências e hipóteses, não diagnósticos</h1>'
            '<p>Não há medição, confirmação causal, aplicabilidade OEM por série, '
            'nem autorização de teste ou liberação.</p>'+
            "".join(blocks)+"</body></html>")


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=MAP_PATH)
    parser.add_argument("--policy",type=Path,default=POLICY_PATH)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    policy=json.loads(args.policy.read_text(encoding="utf-8"))
    report=evaluate(manifest,policy)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        # Do not use unrelated policies in the HTML source.
        require(policy==json.loads(POLICY_PATH.read_text(encoding="utf-8")),
                "HTML requires committed policy")
        args.html.write_text(render_html(manifest,report),encoding="utf-8")
    return report

if __name__=="__main__":
    main()
