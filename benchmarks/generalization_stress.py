"""Cycle 28: unseen-to-Cycle-27 synthetically authored challenge evaluation.

Explicitly NOT independent human validation or diagnostic accuracy.
The original Cycle-27 selector is evaluated unchanged as a baseline.
A separate quality gate handles documentary provenance and unsupported domains.
"""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path

from benchmarks.mechanical_reasoning import DOMAIN_PATHS, investigate as cycle27_selector
from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks/generalization-challenges.v1.json"
ORACLE = ROOT / "benchmarks/generalization-expectations.v1.json"
FAMILIES = frozenset(DOMAIN_PATHS)
UNSUPPORTED = frozenset(("braking", "transmission"))
SOURCES = frozenset(("credible_synthetic", "unverified", "contradictory", "stale", "revoked"))
CHALLENGES = ("first_gap", "third_gap", "conflicting_reports", "complete_context",
              "unverified_provenance", "conflicting_provenance",
              "outdated_evidence", "revoked_evidence")
DENIED = ("mayExecuteTests", "mayCreateWorkOrder", "mayReleaseEquipment")
KEYS = {"caseId", "familyId", "challengeKind", "fictionalSymptom",
        "contextAvailable", "unresolvedNarrativeConflict", "sourceStatus",
        "observationNature", "oemEffectivityVerified", "confirmedRootCause", *DENIED}
EXPECTATION_KEYS = {"caseId", "expectedNextQuestionId", "expectedAbstention",
                    "expectedOperationalAuthority"}

def validate_challenges(manifest):
    require(isinstance(manifest, dict) and set(manifest) ==
            {"schema","version","purpose","realFieldEvidence",
             "externalExpertValidation","operationallyApproved","cases"},
            "challenge manifest has unknown/missing fields")
    require(manifest["schema"] == "maintenance-superinteligence.generalization-challenges.v1"
            and manifest["version"] == "1.0.0"
            and manifest["purpose"] == "synthetic_out_of_template_challenge_inputs"
            and all(manifest[k] is False for k in
                    ("realFieldEvidence","externalExpertValidation","operationallyApproved")),
            "source promoted to field or expert proof")
    items = manifest["cases"]
    require(isinstance(items,list) and len(items)==34, "expected 34 novel challenges")
    require(len({x.get("caseId") for x in items})==34, "duplicate challenge")
    for i,c in enumerate(items,1):
        require(isinstance(c,dict) and set(c)==KEYS
                and c["caseId"] == f"SIM-GEN-{i:03d}"
                and isinstance(c["fictionalSymptom"],str)
                and len(c["fictionalSymptom"])>10
                and c["observationNature"]=="synthetic_narrative_not_field_measurement"
                and c["confirmedRootCause"] is None
                and c["oemEffectivityVerified"] is False
                and all(c[k] is False for k in DENIED),
                "challenge tampered with, false cause, or claimed authority")
        require(type(c["unresolvedNarrativeConflict"]) is bool
                and c["sourceStatus"] in SOURCES,
                "invalid source or contradiction")
        context=c["contextAvailable"]
        require(isinstance(context,dict) and all(type(v) is bool for v in context.values()),
                "invalid documentary context")
        if i<=32:
            family=list(DOMAIN_PATHS)[(i-1)//8]
            kind=CHALLENGES[(i-1)%8]
            require(c["familyId"]==family and c["challengeKind"]==kind,
                    "noncanonical challenge IDs/families")
            gates=[g[0] for g in DOMAIN_PATHS[family]["gates"]]
            require(set(context)==set(gates),"context keys not applicable to domain")
            missing=(gates[0] if kind=="first_gap" else gates[2] if kind=="third_gap" else None)
            require(all(v is (k!=missing) for k,v in context.items()),
                    "context availability mismatch")
            status=("unverified" if kind=="unverified_provenance" else
                    "contradictory" if kind=="conflicting_provenance" else
                    "stale" if kind=="outdated_evidence" else
                    "revoked" if kind=="revoked_evidence" else
                    "credible_synthetic")
            require(c["sourceStatus"]==status
                    and c["unresolvedNarrativeConflict"] is (kind=="conflicting_reports"),
                    "challenge semantics changed")
        else:
            require(c["familyId"] == ("braking" if i==33 else "transmission")
                    and c["challengeKind"]=="unmodeled_domain"
                    and context=={} and c["sourceStatus"]=="unverified"
                    and c["unresolvedNarrativeConflict"] is False,
                    "unsupported-domain fixture altered")
    return items

def validate_oracle(oracle,items):
    require(isinstance(oracle,dict) and set(oracle) ==
            {"schema","version","nature","diagnosticAccuracyMeasured",
             "independentExpertValidation","expectations"},
            "oracle keys missing/unexpected")
    require(oracle["schema"]=="maintenance-superinteligence.generalization-expectations.v1"
            and oracle["version"]=="1.0.0"
            and oracle["nature"]=="author_defined_unseen_by_cycle27_not_independently_reviewed"
            and oracle["diagnosticAccuracyMeasured"] is False
            and oracle["independentExpertValidation"] is False,
            "oracle falsely claims external validation")
    expectations=oracle["expectations"]
    require(isinstance(expectations,list) and len(expectations)==len(items),
            "oracle case count differs")
    allowed=set(("verify_source_provenance","reconcile_source_conflict",
                 "revalidate_documentary_evidence","reconcile_conflicting_reports",
                 "escalate_to_engineer_for_review","escalate_unsupported_domain"))
    allowed.update(g[1] for info in DOMAIN_PATHS.values() for g in info["gates"])
    for case,exp in zip(items,expectations):
        require(isinstance(exp,dict) and set(exp)==EXPECTATION_KEYS
                and exp["caseId"]==case["caseId"]
                and exp["expectedNextQuestionId"] in allowed
                and exp["expectedAbstention"] is True
                and exp["expectedOperationalAuthority"] is False,
                "oracle reordered, unauthorized, or invalid")
    return expectations

def assess_challenge(case):
    family=case["familyId"]
    if family not in FAMILIES:
        return {"baselineQuestionId":None,
                "gatedQuestionId":"escalate_unsupported_domain",
                "openHypotheses":[], "unsupportedDomain":True}
    prior=cycle27_selector({
        "caseId":case["caseId"],"familyId":family,
        "unresolvedContradiction":case["unresolvedNarrativeConflict"],
        "contextAvailable":case["contextAvailable"],
    })
    baseline=prior["selectedQuestionId"]
    source=case["sourceStatus"]
    gated=("revalidate_documentary_evidence" if source in ("stale","revoked") else
           "reconcile_source_conflict" if source=="contradictory" else
           "verify_source_provenance" if source=="unverified" else baseline)
    return {"baselineQuestionId":baseline,"gatedQuestionId":gated,
            "openHypotheses":prior["hypotheses"],"unsupportedDomain":False}

def evaluate(manifest,oracle):
    items=validate_challenges(manifest)
    expected=validate_oracle(oracle,items)
    results=[]
    for case,exp in zip(items,expected):
        outcome=assess_challenge(case)
        requires_gap=case["sourceStatus"]!="credible_synthetic" or outcome["unsupportedDomain"]
        results.append({
            "caseId":case["caseId"],"familyId":case["familyId"],
            "challengeKind":case["challengeKind"],
            "baselineQuestionId":outcome["baselineQuestionId"],
            "gatedQuestionId":outcome["gatedQuestionId"],
            "expectedQuestionId":exp["expectedNextQuestionId"],
            "baselineMatchesEditorial":outcome["baselineQuestionId"]==exp["expectedNextQuestionId"]
                                      if not outcome["unsupportedDomain"] else None,
            "gatedMatchesEditorial":outcome["gatedQuestionId"]==exp["expectedNextQuestionId"],
            "needsProvenanceGate":requires_gap,
            "unsupportedDomain":outcome["unsupportedDomain"],
            "hypothesisCount":len(outcome["openHypotheses"]),
            "allHypothesesOpen":all(x["status"]=="open_not_confirmed"
                                     and x["probability"] is None
                                     for x in outcome["openHypotheses"]),
            "rootCauseConfirmed":False,"measurementsPerformed":False,
            "oemApplicabilityVerified":False,"realEngineeringReview":False,
            "operationalAuthority":{k:False for k in DENIED},
        })
    supported=[r for r in results if not r["unsupportedDomain"]]
    return {
        "schema":"maintenance-superinteligence.generalization-report.v1",
        "version":"1.0.0","mode":"authored_synthetic_stress_not_field_validation",
        "manifestDigest":digest(manifest),"oracleDigest":digest(oracle),
        "caseCount":len(results),"supportedDomainCases":len(supported),
        "unknownDomainCases":len(results)-len(supported),
        "baselineEditorialAgreement":{"matched":sum(r["baselineMatchesEditorial"] for r in supported),
                                      "total":len(supported)},
        "qualityGatedEditorialAgreement":{"matched":sum(r["gatedMatchesEditorial"] for r in results),
                                           "total":len(results)},
        "cases":results,
        "independentExpertEvaluationCompleted":False,
        "realWorldDiagnosticAccuracyMeasured":False,
        "causesConfirmed":0,"testsExecuted":0,
        "mayClaimDiagnosticValidation":False,
        "mayCreateWorkOrder":False,"mayReleaseEquipment":False,
        "decision":"educational_only_no_go",
    }

def verify_report(report,manifest,oracle):
    require(report==evaluate(manifest,oracle),"edited or stale report/oracle not accepted")
    return True

def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.generalization-report.v1"
            and report.get("caseCount")==34
            and report.get("decision")=="educational_only_no_go"
            and report.get("mayClaimDiagnosticValidation") is False
            and report.get("realWorldDiagnosticAccuracyMeasured") is False
            and report.get("mayCreateWorkOrder") is False
            and report.get("mayReleaseEquipment") is False,
            "unsafe generalization HTML")
    section="".join(
        "<section><h2>"+escape(c["caseId"])+" — "+escape(c["familyId"])+"</h2>"
        "<p>"+escape(c["challengeKind"])+" | previous: "+escape(str(c["baselineQuestionId"]))+
        " | guarded: "+escape(c["gatedQuestionId"])+"</p>"
        "<p>Author expectation: "+escape(c["expectedQuestionId"])+
        " | agreement: "+escape(str(c["gatedMatchesEditorial"]))+"</p></section>"
        for c in report["cases"])
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            'form-action &apos;none&apos;"><title>Cycle 28 — synthetic stress</title>'
            '<style>body{font:15px system-ui;max-width:940px;margin:2em auto;'
            'padding:1em}section{border:1px solid #bbb;padding:1em;margin:1em 0}</style>'
            '</head><body><h1>Ciclo 28 — cenários novos (P&D)</h1>'
            '<p>Concordância com gabarito autoral, não precisão de falhas reais. '
            'Sem liberação, execução de testes ou evidência OEM.</p>'+section+'</body></html>')

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases",type=Path,default=CASES)
    ap.add_argument("--oracle",type=Path,default=ORACLE)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--html",type=Path)
    args=ap.parse_args(argv)
    manifest=json.loads(args.cases.read_text(encoding="utf-8"))
    oracle=json.loads(args.oracle.read_text(encoding="utf-8"))
    report=evaluate(manifest,oracle)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(report),encoding="utf-8")
    return report

if __name__=="__main__":
    main()
