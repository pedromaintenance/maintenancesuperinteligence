"""Cycle 34 — conditional evidence matrix, not machine diagnostics.

Every signal is an AUTHOR'S hypothetical observation. The evidence relations are
qualitative editorial heuristics; never probabilities, proof of failure, OEM
effectivity, or authorization to inspect/test/act.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

from knowledge.mechanical_evidence import (
    MAP_PATH, POLICY_PATH as MECHANICAL_POLICY, validate_map,
)
from pilot.change_review_packets import require, digest

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/"knowledge/discriminating-evidence-matrix.v1.json"
SCENARIOS=ROOT/"knowledge/discrimination-scenarios.v1.json"
POLICY=ROOT/"knowledge/discrimination-policy.v1.json"

OUTCOMES=("supports_relative_hypothesis","weakens_relative_hypothesis","indeterminate")
KINDS=("support_only","weaken_only","conflict","inconclusive")
POSITIONS={
    "support_only":"tentative_support_not_confirmed",
    "weaken_only":"tentative_weakening_not_excluded",
    "conflict":"conflict_requires_documentary_reconciliation",
    "inconclusive":"insufficient_to_discriminate",
}
SIM_KEYS={"scenarioId","parentRecordId","scenarioKind","assumedRuleIds",
          "sourceNature","fieldObservationVerified","independentReviewPerformed",
          "rootCauseConfirmed","mayAuthorizeAction"}
MATRIX_KEYS={"schema","version","purpose","realObservationsPresent",
             "expertReviewed","operationalAuthority","rules"}
RULE_KEYS={"ruleId","parentRecordId","outcome","hypotheticalObservation",
           "causalInterpretation","nextSafeDocumentaryQuestion","evidenceStatus",
           "fieldSourceAvailable","measurementConfirmed",
           "oemSerialEffectivityConfirmed","rootCauseConfirmed",
           "independentReviewerApproved","mayExecuteTest",
           "mayCreateWorkOrder","mayReleaseEquipment"}
POLICY_KEYS={"schema","version","parentScope","requiredOutcomes","requiredScenarioKinds",
             "expectedParentRecords","minimumRulesPerParent",
             "independentExpertValidated","causalInferenceAuthorized",
             "mayExecuteTests","mayCreateWorkOrder","mayReleaseEquipment"}
FALSENESS=("fieldSourceAvailable","measurementConfirmed",
           "oemSerialEffectivityConfirmed","rootCauseConfirmed",
           "independentReviewerApproved","mayExecuteTest",
           "mayCreateWorkOrder","mayReleaseEquipment")


def text_fields(item,keys):
    require(all(isinstance(item[k],str) and len(item[k].strip())>=35 for k in keys),
            "inadequate discriminating rationale, conditional observation or question")


def validate_policy(policy):
    require(isinstance(policy,dict) and set(policy)==POLICY_KEYS,
            "policy fields drift")
    require(policy["schema"]=="maintenance-superinteligence.discrimination-policy.v1"
            and policy["version"]=="1.0.0"
            and policy["parentScope"]==
            "cycle33_source_attributed_unverified_mechanical_hypotheses"
            and policy["requiredOutcomes"]==list(OUTCOMES)
            and policy["requiredScenarioKinds"]==list(KINDS)
            and type(policy["expectedParentRecords"]) is int
            and policy["expectedParentRecords"]==12
            and type(policy["minimumRulesPerParent"]) is int
            and policy["minimumRulesPerParent"]==3
            and all(policy[k] is False for k in
                    ("independentExpertValidated","causalInferenceAuthorized",
                     "mayExecuteTests","mayCreateWorkOrder","mayReleaseEquipment")),
            "unsupported or operationally unsafe policy")
    return True


def validate_matrix(matrix,parent,mechanical_policy,policy):
    validate_policy(policy)
    parents=validate_map(parent,mechanical_policy)
    require(isinstance(matrix,dict) and set(matrix)==MATRIX_KEYS
            and matrix["schema"]==
                "maintenance-superinteligence.discriminating-evidence-matrix.v1"
            and matrix["version"]=="1.0.0"
            and matrix["purpose"]=="conditional_hypothesis_discrimination_not_diagnosis"
            and matrix["realObservationsPresent"] is False
            and matrix["expertReviewed"] is False
            and matrix["operationalAuthority"] is False,
            "matrix promotes unverified field evidence to fact")
    rules=matrix["rules"]
    require(isinstance(rules,list)
            and len(rules)==len(parents)*policy["minimumRulesPerParent"],
            "rule count incomplete")
    by_parent={}
    for i,rule in enumerate(rules):
        require(isinstance(rule,dict) and set(rule)==RULE_KEYS,
                "missing/unexpected rule field")
        parent_id=parents[i//3]["recordId"]
        outcome=OUTCOMES[i%3]
        require(rule["ruleId"]==f"DISC-{i//3+1:03d}-{i%3+1}"
                and rule["parentRecordId"]==parent_id
                and rule["outcome"]==outcome,
                "parent binding, order or directional inference altered")
        require(rule["evidenceStatus"]=="hypothetical_not_observed"
                and all(rule[k] is False for k in FALSENESS),
                "rule fabricates a measurement, OEM applicability or authorization")
        text_fields(rule,("hypotheticalObservation","causalInterpretation",
                          "nextSafeDocumentaryQuestion"))
        require(rule["hypotheticalObservation"].startswith("Se "),
                "a conditional observation must not claim a field finding")
        by_parent.setdefault(parent_id,[]).append(rule)
    require(set(by_parent)=={x["recordId"] for x in parents}
            and all(len(x)==3 for x in by_parent.values()),
            "an inference branch lacks its three outcomes")
    return by_parent


def validate_scenarios(fixtures,by_parent):
    require(isinstance(fixtures,dict)
            and set(fixtures)=={"schema","version","nature","cases"}
            and fixtures["schema"]=="maintenance-superinteligence.discrimination-scenarios.v1"
            and fixtures["version"]=="1.0.0"
            and fixtures["nature"]=="author_generated_synthetic_not_field_validation",
            "fixtures are not synthetic-only")
    records=fixtures["cases"]
    require(isinstance(records,list) and len(records)==len(by_parent)*len(KINDS),
            "four scenarios per parent required")
    for i,case in enumerate(records):
        require(isinstance(case,dict) and set(case)==SIM_KEYS,
                "scenario structure incomplete")
        number=i//4+1
        kind=KINDS[i%4]
        parent=f"MECH-KB-{number:03d}"
        valid_ids=[x["ruleId"] for x in by_parent[parent]]
        chosen=([valid_ids[0]] if kind=="support_only" else
                [valid_ids[1]] if kind=="weaken_only" else
                valid_ids[:2] if kind=="conflict" else [valid_ids[2]])
        require(case["scenarioId"]==f"SIM-DISC-{number:03d}-{i%4+1}"
                and case["parentRecordId"]==parent
                and case["scenarioKind"]==kind
                and case["assumedRuleIds"]==chosen
                and case["sourceNature"]==
                    "fictional_conditional_assumptions_not_field_records"
                and all(case[key] is False for key in
                        ("fieldObservationVerified","independentReviewPerformed",
                         "rootCauseConfirmed","mayAuthorizeAction")),
                "unsupported domain, changed synthetic signal or false case validity")
    return records


def judge_case(case,by_parent,parent_by_id):
    parent_id=case["parentRecordId"]
    rulebook={r["ruleId"]:r for r in by_parent[parent_id]}
    chosen=[rulebook[rule_id] for rule_id in case["assumedRuleIds"]]
    outcomes={r["outcome"] for r in chosen}
    if OUTCOMES[0] in outcomes and OUTCOMES[1] in outcomes:
        state=POSITIONS["conflict"]
    elif OUTCOMES[0] in outcomes:
        state=POSITIONS["support_only"]
    elif OUTCOMES[1] in outcomes:
        state=POSITIONS["weaken_only"]
    else:
        state=POSITIONS["inconclusive"]
    return {
        "scenarioId":case["scenarioId"],
        "parentRecordId":parent_id,
        "family":parent_by_id[parent_id]["system"],
        "parentBranchType":parent_by_id[parent_id]["branchType"],
        "assumedRuleIds":case["assumedRuleIds"],
        "observedEvidenceCount":0,
        "qualitativeState":state,
        "requiresHumanReconciliation":state in
            (POSITIONS["conflict"],POSITIONS["inconclusive"]),
        "nextDocumentaryQuestion":parent_by_id[parent_id]["nextDiscriminatingQuestion"],
        "hypothesisStatus":"open_unconfirmed",
        "rootCauseConfirmed":False,
        "oemSerialEffectivityVerified":False,
        "independentExpertReviewCompleted":False,
        "mayExecuteTests":False,
        "mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
    }


def evaluate(matrix,parent,mechanical_policy,policy,fixtures):
    by_parent=validate_matrix(matrix,parent,mechanical_policy,policy)
    cases=validate_scenarios(fixtures,by_parent)
    parent_by_id={x["recordId"]:x for x in parent["records"]}
    rows=[judge_case(c,by_parent,parent_by_id) for c in cases]
    counts=Counter(x["qualitativeState"] for x in rows)
    signals=Counter(r["outcome"] for r in matrix["rules"])
    return {
        "schema":"maintenance-superinteligence.discrimination-report.v1",
        "version":"1.0.0","mode":"synthetic_qualitative_conditionals_not_diagnostic_accuracy",
        "matrixDigest":digest(matrix),"parentDigest":digest(parent),
        "mechanicalPolicyDigest":digest(mechanical_policy),
        "policyDigest":digest(policy),"scenarioDigest":digest(fixtures),
        "parentHypothesisCount":len(parent["records"]),
        "ruleCount":len(matrix["rules"]),
        "ruleOutcomes":{k:signals[k] for k in OUTCOMES},
        "fictionalScenarioCount":len(rows),
        "scenarioStateCounts":{k:counts[POSITIONS[k]] for k in KINDS},
        "scenarios":rows,
        "physicalObservationsVerified":0,
        "causesConfirmed":0,"testsExecuted":0,
        "independentExpertValidationCompleted":False,
        "realWorldDiagnosticAccuracyMeasured":False,
        "operationalAuthorityGranted":False,
        "mayExecuteTests":False,"mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
        "decision":"editorial_discrimination_demo_only_no_go",
    }


def verify_report(report,matrix,parent,mechanical_policy,policy,fixtures):
    require(report==evaluate(matrix,parent,mechanical_policy,policy,fixtures),
            "report falsified or no longer derived from original evidence matrix")
    return True


def render_html(report,matrix,parent,mechanical_policy,policy,fixtures):
    verify_report(report,matrix,parent,mechanical_policy,policy,fixtures)
    require(report["decision"]=="editorial_discrimination_demo_only_no_go"
            and report["causesConfirmed"]==0 and report["testsExecuted"]==0
            and report["mayReleaseEquipment"] is False,
            "cannot publish a false field conclusion")
    glossary={
        "supports_relative_hypothesis":"Pode favorecer hipótese",
        "weakens_relative_hypothesis":"Pode enfraquecer hipótese",
        "indeterminate":"Não discrimina"
    }
    sections=[]
    rules=matrix["rules"]
    for i,parent_row in enumerate(parent["records"]):
        lines=[]
        for rule in rules[3*i:3*i+3]:
            lines.append("<li><b>"+escape(glossary[rule["outcome"]])+
                         "</b>: "+escape(rule["hypotheticalObservation"])+
                         ". <i>"+escape(rule["causalInterpretation"])+
                         "</i></li>")
        sections.append("<section><h2>"+escape(parent_row["recordId"])+" — "+
                        escape(parent_row["candidateOrConfounder"])+"</h2><p>"+
                        escape(parent_row["functionalFailure"])+"</p><ul>"+
                        "".join(lines)+"</ul><p><b>Próxima questão documental:</b> "+
                        escape(parent_row["nextDiscriminatingQuestion"])+
                        "</p></section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; "
            'base-uri &apos;none&apos;; form-action &apos;none&apos;">'
            '<title>Ciclo 34 — Evidência discriminante sintética</title>'
            '<style>body{font:15px system-ui;max-width:950px;margin:2em auto;'
            'padding:1em}section{border:1px solid #aaa;margin:1em 0;padding:1em}'
            '</style></head><body><h1>Matriz de evidências condicionais — NO GO</h1>'
            '<p>36 condições autorais, 48 cenários fictícios. Nenhum dado de máquina '
            'real, ensaio, comprovação causal, valor probabilístico ou OEM por série.'
            '</p>'+"".join(sections)+"</body></html>")


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--matrix",type=Path,default=MATRIX)
    p.add_argument("--parent",type=Path,default=MAP_PATH)
    p.add_argument("--mechanical-policy",type=Path,default=MECHANICAL_POLICY)
    p.add_argument("--policy",type=Path,default=POLICY)
    p.add_argument("--scenarios",type=Path,default=SCENARIOS)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--html",type=Path)
    args=p.parse_args(argv)
    load=lambda path:json.loads(path.read_text(encoding="utf-8"))
    matrix,parent,mpolicy,policy,fixtures=[load(x) for x in
        (args.matrix,args.parent,args.mechanical_policy,args.policy,args.scenarios)]
    result=evaluate(matrix,parent,mpolicy,policy,fixtures)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(result,matrix,parent,mpolicy,policy,fixtures),
                             encoding="utf-8")
    return result

if __name__=="__main__":
    main()
