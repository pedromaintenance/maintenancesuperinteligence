"""Cycle 44 — symbolic pairwise discrimination rehearsal, NOT field diagnosis.

This offline lab tests whether an explicit *author-proposed* symbolic answer
signature could distinguish competing hypothetical explanations. Its predictions
are not physical measurements, OEM limits, validated likelihoods or proof that
a proposed observation would differentiate mechanisms in actual machinery.

The lab neither collects external reviews nor replaces the private held-out
custody tooling of Cycles 30–32.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import re

from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/cycle44-symbolic-trials.v1.json"
FAMILIES = ("final_drive", "hydraulics", "electronics", "cooling")
DENIALS = (
    "diagnosticAccuracyMeasured", "independentExpertReviewCompleted",
    "fieldEvidenceUsed", "oemEffectivityVerified",
    "mayExecuteTest", "mayCreateWorkOrder", "mayModifyEcm",
    "mayReleaseEquipment",
)
QUESTION_KEYS = {
    "questionId", "questionText", "fictionalDocumentaryPrerequisitePresent",
    "symbolicOutcomesByHypothesis", "requiresPhysicalTest",
    "operationalApprovalVerified",
}
TRIAL_KEYS = {
    "trialId", "familyId", "scenarioKind", "fictionalSymptom",
    "hypothesisIds", "unresolvedContradiction", "sourceStatus",
    "baselineQuestionId", "questions",
}
SYMBOL = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_fixture(data):
    require(isinstance(data, dict) and set(data) ==
            {"schema", "version", "nature", "claims", "trials"},
            "Cycle44 fixture fields changed")
    require(data["schema"] == "maintenance-superinteligence.cycle44-trials.v1"
            and data["version"] == "1.0.0"
            and data["nature"] ==
            "author_constructed_symbolic_question_rehearsal",
            "Cycle44 source purported to contain real data")
    claims = data["claims"]
    require(isinstance(claims, dict) and set(claims) == set(DENIALS)
            and all(claims[key] is False for key in DENIALS),
            "external review or operational authority promoted")
    cases = data["trials"]
    require(isinstance(cases, list) and len(cases) == 8,
            "Cycle44 fixed rehearsal must include eight trials")
    ids = set()
    family_kinds = Counter()
    for trial in cases:
        require(isinstance(trial, dict) and set(trial) == TRIAL_KEYS,
                "unknown fields in synthetic trial")
        tid = trial["trialId"]
        require(isinstance(tid, str) and re.fullmatch(r"SIM-DISC-0[1-8]", tid)
                and tid not in ids, "missing or reused trial ID")
        ids.add(tid)
        family = trial["familyId"]
        kind = trial["scenarioKind"]
        require(family in FAMILIES and kind in ("normal", "contradictory"),
                "unknown family or scenario category")
        family_kinds[(family, kind)] += 1
        require(isinstance(trial["fictionalSymptom"], str)
                and len(trial["fictionalSymptom"]) >= 25,
                "trial lacks a meaningful fictional symptom")
        hypos = trial["hypothesisIds"]
        require(isinstance(hypos, list) and len(hypos) == 3
                and len(set(hypos)) == 3
                and all(isinstance(h, str) and SYMBOL.fullmatch(h)
                        for h in hypos),
                "hypotheses must be three unique, unconfirmed aliases")
        conflict = trial["unresolvedContradiction"]
        status = trial["sourceStatus"]
        require(type(conflict) is bool
                and conflict is (kind == "contradictory")
                and status == ("contradictory" if conflict
                               else "synthetic_context_declared"),
                "fictional conflicting evidence was silently resolved")
        questions = trial["questions"]
        require(isinstance(questions, list) and len(questions) == 3,
                "three registered candidate questions expected")
        qids = set()
        for q in questions:
            require(isinstance(q, dict) and set(q) == QUESTION_KEYS,
                    "question has extra or missing fields")
            qid = q["questionId"]
            require(isinstance(qid, str) and SYMBOL.fullmatch(qid)
                    and qid not in qids, "duplicate/invalid question")
            qids.add(qid)
            require(isinstance(q["questionText"], str)
                    and len(q["questionText"]) >= 25,
                    "question requires explicit documentary rationale")
            require(type(q["fictionalDocumentaryPrerequisitePresent"]) is bool
                    and q["requiresPhysicalTest"] is False
                    and q["operationalApprovalVerified"] is False,
                    "fictional prerequisite treated as an executed/approved test")
            outcomes = q["symbolicOutcomesByHypothesis"]
            require(isinstance(outcomes, dict)
                    and set(outcomes) == set(hypos)
                    and all(x is None or
                            (isinstance(x, str) and SYMBOL.fullmatch(x))
                            for x in outcomes.values()),
                    "invalid symbolic predictions or missing hypothesis")
        require(trial["baselineQuestionId"] == questions[0]["questionId"]
                and questions[0]["fictionalDocumentaryPrerequisitePresent"] is True,
                "registered baseline missing or unavailable")
    require(family_kinds == Counter(
        {(f, k): 1 for f in FAMILIES
         for k in ("normal", "contradictory")}),
        "domain/contradiction coverage changed")
    return cases


def theoretical_pair_coverage(question, hypothesis_ids):
    """Count separable pairs only if all author-assumed answers are specified.

    No probability, physical effectivity or real test outcome is assumed.
    Missing symbolic predictions force an unscored result.
    """
    answers = [question["symbolicOutcomesByHypothesis"][h] for h in hypothesis_ids]
    if any(a is None for a in answers):
        return None
    return sum(a != b for a, b in combinations(answers, 2))


def assess_trial(trial):
    questions = trial["questions"]
    all_counts = {
        q["questionId"]: theoretical_pair_coverage(q, trial["hypothesisIds"])
        for q in questions
    }
    base = trial["baselineQuestionId"]
    status = ("unresolved_contradiction"
              if trial["unresolvedContradiction"]
              else "source_not_suitable"
              if trial["sourceStatus"] != "synthetic_context_declared"
              else None)
    if status is None:
        available = [q for q in questions
                     if q["fictionalDocumentaryPrerequisitePresent"]
                     and all_counts[q["questionId"]] is not None]
        if all_counts[base] is None:
            status = "baseline_not_evaluable"
        elif not available:
            status = "no_candidate_evaluable"
        else:
            high = max(all_counts[q["questionId"]] for q in available)
            winners = [q["questionId"] for q in available
                       if all_counts[q["questionId"]] == high]
            if len(winners) != 1:
                status = "tie_requires_human_review"
    if status is not None:
        result = {
            "trialId": trial["trialId"], "familyId": trial["familyId"],
            "state": "abstain", "reason": status,
            "baselineQuestionId": base, "selectedQuestionId": None,
            "theoreticalPairsBaseline": None,
            "theoreticalPairsSelected": None,
            "theoreticalPairDifference": None,
        }
    else:
        selected = winners[0]
        result = {
            "trialId": trial["trialId"], "familyId": trial["familyId"],
            "state": "paper_ranking_under_author_assumptions",
            "reason": "symbolic_predictions_only_not_field_effectiveness",
            "baselineQuestionId": base, "selectedQuestionId": selected,
            "theoreticalPairsBaseline": all_counts[base],
            "theoreticalPairsSelected": high,
            "theoreticalPairDifference": high - all_counts[base],
        }
    result.update({
        "symbolicQuestionCoverage": [
            {"questionId": q["questionId"], "separablePairs": all_counts[q["questionId"]],
             "fictionalPrerequisitePresent":
             q["fictionalDocumentaryPrerequisitePresent"]}
            for q in questions
        ],
        "totalHypothesisPairs": 3,
        "unconfirmedHypotheses": list(trial["hypothesisIds"]),
        "physicalTestsPerformed": 0,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayModifyEcm": False,
        "mayReleaseEquipment": False,
    })
    return result


def evaluate(data):
    cases = validate_fixture(data)
    results = [assess_trial(t) for t in cases]
    ranked = [r for r in results if r["state"] ==
              "paper_ranking_under_author_assumptions"]
    abstained = [r for r in results if r["state"] == "abstain"]
    require(len(ranked) == 4 and len(abstained) == 4,
            "Cycle44 rehearsal no longer covers ranking and abstention")
    return {
        "schema": "maintenance-superinteligence.cycle44-report.v1",
        "version": "1.0.0",
        "mode": "symbolic_editorial_study_not_independent_review",
        "fixtureDigest": digest(data),
        "trialCount": len(results),
        "rankedPaperOnlyCount": len(ranked),
        "abstentionCount": len(abstained),
        "syntheticPairCoverageComparison": {
            "scoredTrials": len(ranked),
            "totalTheoreticalPairDifference":
                sum(r["theoreticalPairDifference"] for r in ranked),
            "fieldInformationGainMeasured": False,
            "independentOracleUsed": False,
        },
        "trials": results,
        "limitations": [
            "symbolic_outcomes_are_authored_not_observed",
            "no_likelihoods_or_test_costs_measured",
            "no_oem_series_or_physical_prerequisite_verified",
            "no_independent_expert_assessment_performed",
            "none_of_these_questions_authorizes_testing",
        ],
        "diagnosticAccuracyMeasured": False,
        "independentMechanicalReviewCompleted": False,
        "fieldMeasurements": 0,
        "confirmedRootCauses": 0,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayModifyEcm": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_symbolic_discrimination_not_validated_in_field",
    }


def verify_report(report, data):
    require(report == evaluate(data), "Cycle44 report stale or altered")
    return True


def markdown(report):
    require(report["decision"] ==
            "no_go_symbolic_discrimination_not_validated_in_field"
            and report["diagnosticAccuracyMeasured"] is False,
            "cannot publish unsafe report")
    lines = [
        "# Ciclo 44 — Ensaio simbólico de poder discriminante (NO GO)", "",
        "**Todos os casos são fictícios.** O cálculo é uma comparação de "
        "partições de hipóteses com respostas inventadas, não um teste real de "
        "poder preditivo, procedimento OEM ou recomendação de intervenção.", "",
        f"Casos: {report['trialCount']}; ranqueados apenas em papel: "
        f"{report['rankedPaperOnlyCount']}; abstenções: "
        f"{report['abstentionCount']}.", "",
        "| Caso | Família | Estado | Pergunta elegível | Pares simbólicos |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in report["trials"]:
        pair = ("não pontuado" if r["theoreticalPairsSelected"] is None
                else f"{r['theoreticalPairsSelected']}/3")
        lines.append(f"| {r['trialId']} | {r['familyId']} | {r['state']} | "
                     f"{r['selectedQuestionId'] or 'nenhuma'} | {pair} |")
    lines.extend(["", "Nenhum revisor independente participou. Os ganhos "
                  "calculados decorrem das suposições simbólicas do próprio "
                  "autor; não são ganhos de informação medidos em máquinas.", "",
                  "**Decisão:** NO GO para autoridade operacional e "
                  "alegações de competência diagnóstica.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    data = load(args.fixture)
    report = evaluate(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)
                           + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
