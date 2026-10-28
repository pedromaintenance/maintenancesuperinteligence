"""Cycle 31 — synthetic dataset QA for documentary hypothesis-coverage benchmarks.

Detect leakage, duplicate narratives and gaps in TAG coverage, not actual
mechanical accuracy or validity. Real held-out metadata stays with a custodian.
"""
from __future__ import annotations
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import unicodedata

from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/"benchmarks/validation-quality-manifest.v1.json"
POLICY = ROOT/"benchmarks/validation-quality-policy.v1.json"
SPLITS = ("train","dev","test")
KNOWN = ("final_drive","hydraulics","electronics","cooling")
UNSUPPORTED = ("braking","transmission")
RELIABILITY = {"documented_synthetic","contradictory","revoked","unverified"}
REASONS = {"no_physical_confirmation","conflicting_documentary_evidence",
           "source_not_trustworthy","domain_unsupported"}
RECORD_KEYS = {
    "caseId","split","family","mechanismTag","mechanismStatus",
    "incidentLineage","sourceGroup","evidenceRef","syntheticNarrative",
    "sourceReliability","abstentionReason","abstentionRequired",
    "physicalEvidenceCollected","causalMechanismConfirmed",
    "oemApplicabilityVerified","mayCreateWorkOrder","mayReleaseEquipment",
}
MANIFEST_KEYS = {
    "schema","version","mode","realFieldDataPresent",
    "independentReviewerApproved","causesVerifiedByOEM","records",
}
POLICY_KEYS = {
    "schema","version","purpose","taxonomy","splitMinimums",
    "unsupportedTestMinimum","sourceReliabilityRequiredInTest",
    "nearDuplicateJaccardThreshold","independentReviewCompleted",
    "realWorldAccuracyMeasured","mayApproveOperationalUse",
}
SEVERITY = {
    "lineage_reused_cross_split":"critical",
    "source_group_reused_cross_split":"critical",
    "evidence_reused_cross_split":"critical",
    "exact_narrative_cross_split":"critical",
    "near_narrative_cross_split":"major",
    "duplicate_record_within_split":"major",
    "missing_split_minimum":"major",
    "missing_mechanism_tag_test":"major",
    "missing_unsupported_test":"major",
    "missing_source_reliability_test":"major",
}


def tokens(text):
    normalized = unicodedata.normalize("NFKD", text).casefold()
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return frozenset(re.findall(r"[a-z0-9]+", normalized))


def validate_policy(policy):
    require(isinstance(policy,dict) and set(policy)==POLICY_KEYS,
            "quality policy structure")
    require(policy["schema"]=="maintenance-superinteligence.validation-quality-policy.v1"
            and policy["version"]=="1.0.0"
            and policy["purpose"]=="synthetic_split_preflight_not_field_validation"
            and policy["independentReviewCompleted"] is False
            and policy["realWorldAccuracyMeasured"] is False
            and policy["mayApproveOperationalUse"] is False,
            "unsupported validation or approval claim")
    taxonomy=policy["taxonomy"]
    require(isinstance(taxonomy,dict) and set(taxonomy)==set(KNOWN)
            and all(isinstance(v,list) and len(v)==3
                    and all(isinstance(t,str) and re.fullmatch(r"[a-z_]{5,50}",t)
                            for t in v)
                    and len(set(v))==len(v) for v in taxonomy.values())
            and len(set(t for v in taxonomy.values() for t in v))==12,
            "taxonomy must contain 12 unique hypotheses in four systems")
    minimums=policy["splitMinimums"]
    require(isinstance(minimums,dict) and set(minimums)==set(SPLITS)
            and all(type(minimums[x]) is int and minimums[x]>=1 for x in SPLITS),
            "split gate not defined")
    require(type(policy["unsupportedTestMinimum"]) is int
            and policy["unsupportedTestMinimum"]>=1
            and policy["sourceReliabilityRequiredInTest"] ==
            ["contradictory","revoked","unverified"],
            "unknown-domain or provenance risk gate weakened")
    threshold=policy["nearDuplicateJaccardThreshold"]
    require(type(threshold) is float and 0.75<=threshold<=0.95,
            "invalid near-duplicate threshold")
    return taxonomy


def validate_manifest(manifest,policy):
    taxonomy=validate_policy(policy)
    require(isinstance(manifest,dict) and set(manifest)==MANIFEST_KEYS,
            "validation manifest fields")
    require(manifest["schema"]=="maintenance-superinteligence.validation-quality-manifest.v1"
            and manifest["version"]=="1.0.0"
            and manifest["mode"]=="public_synthetic_development_demonstration"
            and manifest["realFieldDataPresent"] is False
            and manifest["independentReviewerApproved"] is False
            and manifest["causesVerifiedByOEM"] is False,
            "manifest falsely promoted as external or field evidence")
    rows=manifest["records"]
    require(isinstance(rows,list) and 2<=len(rows)<=200,
            "invalid corpus size")
    ids=set()
    for row in rows:
        require(isinstance(row,dict) and set(row)==RECORD_KEYS,
                "unknown record field")
        ident=row["caseId"]
        require(isinstance(ident,str)
                and re.fullmatch(r"SIM-VSET-[0-9]{3}",ident)
                and ident not in ids, "invalid or duplicate case ID")
        ids.add(ident)
        require(row["split"] in SPLITS and
                row["family"] in set(KNOWN)|set(UNSUPPORTED) and
                row["mechanismStatus"]=="unconfirmed_training_hypothesis"
                and row["sourceReliability"] in RELIABILITY
                and row["abstentionReason"] in REASONS,
                "unexpected case nature or context")
        for key,prefix in (("incidentLineage","SIM-LINEAGE-"),
                           ("sourceGroup","SIM-GROUP-"),
                           ("evidenceRef","SIM-EVID-")):
            require(isinstance(row[key],str) and
                    re.fullmatch(prefix+r"[0-9]{3}",row[key]),
                    "source group identity missing")
        require(isinstance(row["syntheticNarrative"],str)
                and 24<=len(row["syntheticNarrative"])<=700
                and len(tokens(row["syntheticNarrative"]))>=5,
                "narrative inadequate to deduplicate")
        if row["family"] in KNOWN:
            require(row["mechanismTag"] in taxonomy[row["family"]],
                    "unknown or mislabeled hypothesis for domain")
        else:
            require(row["mechanismTag"]=="unmodeled"
                    and row["split"]=="test"
                    and row["abstentionReason"]=="domain_unsupported",
                    "out-of-scope domain must be test abstention")
        require(row["abstentionReason"] == (
                    "domain_unsupported" if row["family"] in UNSUPPORTED else
                    "conflicting_documentary_evidence" if row["sourceReliability"]=="contradictory" else
                    "source_not_trustworthy" if row["sourceReliability"] in ("revoked","unverified") else
                    "no_physical_confirmation"),
                "unsafe or inconsistent abstention flag")
        require(all(row[k] is False for k in
                    ("physicalEvidenceCollected","causalMechanismConfirmed",
                     "oemApplicabilityVerified","mayCreateWorkOrder",
                     "mayReleaseEquipment"))
                and row["abstentionRequired"] is True,
                "synthetic case claims measured cause or operational rights")
    return rows


def audit(manifest,policy):
    rows=validate_manifest(manifest,policy)
    bysplit=Counter(row["split"] for row in rows)
    findings=[]
    seen=set()
    def add(code,ids,group=None):
        key=(code,tuple(sorted(ids)),group)
        if key not in seen:
            seen.add(key)
            findings.append({"code":code,"severity":SEVERITY[code],
                             "caseIds":list(sorted(ids)),"coverageKey":group})
    for a in range(len(rows)):
        left=rows[a]
        ta=tokens(left["syntheticNarrative"])
        for b in range(a+1,len(rows)):
            right=rows[b]
            ids=[left["caseId"],right["caseId"]]
            cross=left["split"]!=right["split"]
            if cross:
                for attr,code in (
                    ("incidentLineage","lineage_reused_cross_split"),
                    ("sourceGroup","source_group_reused_cross_split"),
                    ("evidenceRef","evidence_reused_cross_split")):
                    if left[attr]==right[attr]:
                        add(code,ids)
            else:
                if (left["incidentLineage"]==right["incidentLineage"] or
                    left["sourceGroup"]==right["sourceGroup"] or
                    left["evidenceRef"]==right["evidenceRef"]):
                    add("duplicate_record_within_split",ids)
            tb=tokens(right["syntheticNarrative"])
            if ta==tb:
                add("exact_narrative_cross_split" if cross else
                    "duplicate_record_within_split",ids)
            elif cross:
                jaccard=len(ta & tb)/len(ta | tb)
                if jaccard>=policy["nearDuplicateJaccardThreshold"]:
                    add("near_narrative_cross_split",ids)
    for split in SPLITS:
        if bysplit[split]<policy["splitMinimums"][split]:
            add("missing_split_minimum",[],split)
    test=[x for x in rows if x["split"]=="test"]
    coverage={}
    for domain,tags in policy["taxonomy"].items():
        coverage[domain]={t:sum(x["family"]==domain and x["mechanismTag"]==t
                                for x in test) for t in tags}
        for tag,number in coverage[domain].items():
            if number==0:
                add("missing_mechanism_tag_test",[],domain+"/"+tag)
    unknown=sum(x["family"] in UNSUPPORTED for x in test)
    if unknown<policy["unsupportedTestMinimum"]:
        add("missing_unsupported_test",[],"unsupported")
    provenance={s:sum(x["sourceReliability"]==s for x in test)
                for s in policy["sourceReliabilityRequiredInTest"]}
    for s,count in provenance.items():
        if count==0:
            add("missing_source_reliability_test",[],s)
    findings.sort(key=lambda x:(x["code"],x["caseIds"],x["coverageKey"] or ""))
    passed=len(findings)==0
    return {
        "schema":"maintenance-superinteligence.validation-quality-report.v1",
        "version":"1.0.0","mode":"public_synthetic_metadata_preflight",
        "manifestDigest":digest(manifest),"policyDigest":digest(policy),
        "caseCount":len(rows),"splits":{s:bysplit[s] for s in SPLITS},
        "testHypothesisTagCoverage":coverage,
        "testUnsupportedCount":unknown,
        "testSourceQualityChallengeCount":provenance,
        "criticalFindingCount":sum(x["severity"]=="critical" for x in findings),
        "majorFindingCount":sum(x["severity"]=="major" for x in findings),
        "findings":findings,
        "qualityPreflightPassed":passed,
        "blindnessOrRealNoveltyEstablished":False,
        "realCaseDiagnosticsVerified":False,
        "independentExpertValidationCompleted":False,
        "mayApproveOperationalUse":False,
        "mayCreateWorkOrder":False,"mayReleaseEquipment":False,
        "decision":"synthetic_quality_pass_not_diagnostic_validation"
                   if passed else "quality_gate_rejected_no_go",
    }


def verify_report(report,manifest,policy):
    require(report==audit(manifest,policy),
            "quality report tampered, stale or different corpus")
    return True


def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.validation-quality-report.v1"
            and report.get("mayApproveOperationalUse") is False
            and report.get("blindnessOrRealNoveltyEstablished") is False
            and report.get("realCaseDiagnosticsVerified") is False,
            "unsafe quality audit visualization")
    items="".join("<li>"+escape(e["code"])+" — "+
                  escape(", ".join(e["caseIds"]) or (e["coverageKey"] or "coverage"))+
                  "</li>" for e in report["findings"])
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            'form-action &apos;none&apos;"><title>Cycle 31 dataset QA</title>'
            '<style>body{font:16px system-ui;max-width:960px;margin:2em auto;padding:1em}</style>'
            '</head><body><h1>Ciclo 31 — Qualidade de dataset (somente simulação)</h1>'
            '<p>'+escape(report["decision"])+'</p><ul>'+items+'</ul>'
            '<p>Cobertura de etiquetas de hipótese, não verdade sobre mecanismos físicos. '
            'Nenhuma validação cega ou aprovação de manutenção.</p></body></html>')


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,default=MANIFEST)
    ap.add_argument("--policy",type=Path,default=POLICY)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--html",type=Path)
    args=ap.parse_args(argv)
    manifest_path=args.manifest.resolve()
    output=args.output.resolve()
    is_public_demo=manifest_path==MANIFEST.resolve()
    if not is_public_demo:
        from benchmarks.heldout_study import private_path
        private_path(manifest_path)
        private_path(output)
        if args.html:
            private_path(args.html)
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    policy=json.loads(args.policy.read_text(encoding="utf-8"))
    result=audit(manifest,policy)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(result),encoding="utf-8")
    if not result["qualityPreflightPassed"]:
        raise SystemExit(2)
    return result

if __name__=="__main__":
    main()
