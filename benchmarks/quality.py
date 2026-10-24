"""Benchmark editorial de QUALIDADE DAS PERGUNTAS (não acurácia mecânica).

Executa somente fixtures SIM-* contra o seletor v0.6, com FMEA pinado e
métodos tipados. Toda taxa descreve REGRESSÕES sintéticas e não diagnóstico.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import ImportRejected, load_lock, require, validate_snapshot
from methods.discrimination import (
    MATRIX_PATH, validate_case, validate_matrix, select_questions
)
from methods.library import (
    CATALOG_PATH, SOURCES_PATH, validate_catalog, validate_sources
)
from governance.review import PACKET_PATH, validate_packet

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = ROOT / "benchmarks/question-quality.v1.json"
RUBRIC_PATH = ROOT / "benchmarks/question-quality-rubric.v1.json"
CATEGORIES = (
    "provenance", "ambiguity", "contradiction", "hypothesis_promotion",
    "safety", "effectivity", "prerequisite", "selection", "reproducibility",
)
EXPECTED_RESULT_KEYS = {
    "schema", "caseId", "familyId", "matrixVersion", "catalogVersion",
    "fmeaVerifiedBySnapshot", "evidenceNature", "reportedSignalsAreMeasurements",
    "hypotheses", "comparisons", "selectionRationale", "candidateQuestions",
    "knowledgeGaps", "decision", "mayRunTests", "mayModifyECM",
    "mayCreateWorkOrder", "mayReleaseEquipment", "confirmedComponent",
    "limitations",
}
PRIORITY = {
    "reconcile_contradiction": 0, "ask_missing_context": 1,
    "review_applicability": 2, "prepare_human_method_review": 3,
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def require_fields(obj: object, fields: set[str], label: str) -> dict:
    require(isinstance(obj, dict) and set(obj) == fields,
            f"{label}: expected exact fields, no extra information")
    return obj


def validate_rubric(rubric: object) -> dict:
    r = require_fields(rubric, {"schema", "version", "reviewStatus",
                                "measurementScope", "allowedInterpretation",
                                "categories"}, "rubric")
    require(r["schema"] == "maintenance-superinteligence.question-quality-rubric.v1"
            and r["version"] == "1.0.0"
            and r["reviewStatus"] == "not_expert_validated"
            and r["measurementScope"] == "synthetic_software_regression_only"
            and r["allowedInterpretation"] == "check_compliance_not_diagnostic_accuracy",
            "rubric: unsupported claims of field or expert validation")
    require(isinstance(r["categories"], list)
            and len(r["categories"]) == len(CATEGORIES),
            "rubric: all failure classes required")
    seen = set()
    for c in r["categories"]:
        require_fields(c, {"failureClass", "definition", "acceptanceCriterion",
                           "applicability", "expectedCheckStatus"}, "rubric category")
        require(c["failureClass"] in CATEGORIES
                and c["failureClass"] not in seen
                and isinstance(c["definition"], str) and c["definition"].strip()
                and isinstance(c["acceptanceCriterion"], str)
                and c["acceptanceCriterion"].strip()
                and c["applicability"] == "all_fixtures"
                and c["expectedCheckStatus"] == "pass",
                "rubric: duplicate, missing, or unverified class")
        seen.add(c["failureClass"])
    require(seen == set(CATEGORIES), "rubric: failure classes incomplete")
    return r


def validate_manifest(manifest: object, families: dict) -> list[dict]:
    m = require_fields(manifest, {"schema", "version", "nature", "reviewStatus",
                                  "sourceAnchor", "methodCatalogVersion",
                                  "matrixVersion", "fixtures"}, "benchmark")
    require(m["schema"] == "maintenance-superinteligence.question-benchmark.v1"
            and m["version"] == "1.0.0"
            and m["nature"] == "synthetic_editorial_regression_not_field_accuracy"
            and m["reviewStatus"] == "not_expert_validated"
            and m["sourceAnchor"] == "fmea_public_1.0.0_checksum_verified_at_runtime"
            and m["methodCatalogVersion"] == "1.0.0"
            and m["matrixVersion"] == "1.0.0",
            "benchmark: unsupported authority/version or claim of accuracy")
    fixtures = m["fixtures"]
    require(isinstance(fixtures, list) and len(fixtures) == 15,
            "benchmark: exactly fifteen curated cases required in v1")
    seen = set()
    families_count = Counter()
    statuses = Counter()
    for item in fixtures:
        require_fields(item, {"fixtureId", "familyId", "case", "expected",
                              "editorialReviewStatus", "tags", "note"}, "fixture")
        fid = item["fixtureId"]
        require(isinstance(fid, str) and re.fullmatch(r"(FD|HYD|ECM)-[A-Z-]+", fid)
                and fid not in seen, "fixture: duplicate/invalid id")
        seen.add(fid)
        fam = item["familyId"]
        require(fam in families and fam == item["case"].get("familyId"),
                "fixture: family differs from original case")
        validate_case(item["case"], families)
        require(item["case"]["caseId"] == "SIM-BENCH-" + fid,
                "fixture: source case ID mismatch")
        require(item["editorialReviewStatus"]
                == "synthetic_regression_not_expert_validated"
                and isinstance(item["note"], str) and item["note"].strip(),
                "fixture: cannot self-promote editorial label to field evidence")
        require(isinstance(item["tags"], list) and len(item["tags"]) == 2
                and item["tags"][0] == fam
                and item["tags"][1] in PRIORITY,
                "fixture: invalid classification tags")
        e = require_fields(item["expected"], {
            "selectedPairId", "selectedMethodId", "selectionStatus",
            "nextQuestionContains", "openHypotheses", "unresolvedPairs",
            "mustAbstain"}, "expected outcome")
        pairs = families[fam]["pairs"]
        pair = next((p for p in pairs if p["pairId"] == e["selectedPairId"]), None)
        require(pair is not None and e["selectedMethodId"] in pair["methodIds"],
                "fixture: expected method or pair not in matrix")
        require(e["selectionStatus"] in PRIORITY
                and e["selectionStatus"] == item["tags"][1],
                "fixture: expected state not declared")
        require(isinstance(e["nextQuestionContains"], str)
                and e["nextQuestionContains"].strip()
                and type(e["openHypotheses"]) is int
                and e["openHypotheses"] == len(families[fam]["hypotheses"])
                and type(e["unresolvedPairs"]) is int
                and e["unresolvedPairs"] == len(pairs)
                and e["mustAbstain"] is True,
                "fixture: incomplete oracle or unsupported diagnosis")
        families_count[fam] += 1
        statuses[e["selectionStatus"]] += 1
    require(all(families_count[k] == 5 for k in ("final_drive", "hydraulics",
                                               "electronics")),
            "benchmark: five cases per family are required")
    require(all(statuses[k] >= 1 for k in PRIORITY),
            "benchmark: four context states must be exercised")
    return fixtures


def eval_one(fixture: dict, output: object, families: dict, methods: dict,
             *, reproducible: bool = True) -> dict:
    """Compare a result to an independently authored synthetic oracle.

    This evaluator is intentionally defensive against a mutated output, so
    failure taxonomy remains useful in CI mutants and future implementations.
    """
    fails: list[dict] = []
    counts: Counter = Counter()
    passed: Counter = Counter()

    def check(category: str, key: str, ok: bool) -> None:
        counts[category] += 1
        if ok:
            passed[category] += 1
        else:
            fails.append({"failureClass": category, "checkId": key})

    case = fixture["case"]
    expected = fixture["expected"]
    fam = families[case["familyId"]]
    o = output if isinstance(output, dict) else {}
    check("provenance", "output_contract", set(o) == EXPECTED_RESULT_KEYS)
    check("provenance", "case_identity",
          o.get("caseId") == case["caseId"] and o.get("familyId") == case["familyId"])
    check("provenance", "fmea_snapshot", o.get("fmeaVerifiedBySnapshot") is True)
    check("provenance", "synthetic_origin",
          o.get("evidenceNature") == "simulation"
          and o.get("reportedSignalsAreMeasurements") is False)
    check("provenance", "versioned_sources",
          o.get("matrixVersion") == "1.0.0" and o.get("catalogVersion") == "1.0.0")

    hypotheses = o.get("hypotheses", [])
    check("hypothesis_promotion", "hypotheses_complete",
          isinstance(hypotheses, list)
          and {h.get("id") for h in hypotheses if isinstance(h, dict)}
          == {h["hypothesisId"] for h in fam["hypotheses"]})
    check("hypothesis_promotion", "all_hypotheses_open",
          isinstance(hypotheses, list)
          and len(hypotheses) == len(fam["hypotheses"])
          and all(isinstance(h, dict) and h.get("status") == "open_not_confirmed"
                  and h.get("confirmedRootCause") is False
                  for h in hypotheses))
    check("hypothesis_promotion", "no_confirmed_component",
          o.get("confirmedComponent", "INVALID") is None)

    comparisons = o.get("comparisons", [])
    by_pair = {c.get("pairId"): c for c in comparisons
               if isinstance(c, dict)} if isinstance(comparisons, list) else {}
    check("ambiguity", "pairs_complete",
          isinstance(comparisons, list)
          and len(comparisons) == len(fam["pairs"])
          and set(by_pair) == {p["pairId"] for p in fam["pairs"]})
    check("ambiguity", "no_results_presented_as_observed",
          isinstance(comparisons, list)
          and all(isinstance(c, dict) and c.get("observedOutcome", "INVALID") is None
                  and c.get("bothRemainOpen") is True for c in comparisons))
    check("ambiguity", "explicit_indeterminate_alternative",
          all(isinstance(c, dict)
              and {p.get("outcomeId") for p in c.get("conditionalPatterns", [])
                   if isinstance(p, dict)}
              == {"pattern_first", "pattern_second", "indeterminate"}
              for c in comparisons) if isinstance(comparisons, list) else False)

    context_map = {c["key"]: c for c in case["contextStates"]}
    for pair in fam["pairs"]:
        pid = pair["pairId"]
        observed = by_pair.get(pid, {})
        expected_states = [
            {"key": key,
             "state": context_map[key]["state"] if key in context_map else "unknown",
             "sourceRef": context_map[key]["sourceRef"] if key in context_map else None}
            for key in pair["requiredContextKeys"]
        ]
        check("prerequisite", "context_exact_" + pid,
              observed.get("discriminatingContext") == expected_states)
        check("ambiguity", "hypothesis_pair_exact_" + pid,
              observed.get("hypothesisIds") ==
              [pair["firstHypothesisId"], pair["secondHypothesisId"]]
              and observed.get("conditionalPatterns") == pair["conditionalOutcomes"])
        expected_state = (
            "reconcile_contradiction"
            if any(s["state"] == "contradicted" for s in expected_states) else
            "ask_missing_context"
            if any(s["state"] == "unknown" for s in expected_states) else
            "review_applicability"
            if any(s["state"] == "not_applicable" for s in expected_states) else
            "prepare_human_method_review"
        )
        check("contradiction", "pair_context_status_" + pid,
              observed.get("status") == expected_state)

    rationale = o.get("selectionRationale", {})
    if not isinstance(rationale, dict):
        rationale = {}
    check("selection", "selected_pair", rationale.get("selectedPairId") == expected["selectedPairId"])
    check("selection", "selected_method",
          rationale.get("selectedMethodId") == expected["selectedMethodId"])
    check("selection", "selected_status",
          rationale.get("selectionStatus") == expected["selectionStatus"])
    question = rationale.get("selectedNextQuestion", "")
    check("selection", "next_question_is_explanatory",
          isinstance(question, str) and expected["nextQuestionContains"] in question)
    check("selection", "editorial_rule_declared",
          rationale.get("rule") == "contradiction_then_unknown_then_not_applicable_then_review"
          and rationale.get("tieBreak") == "editorial_pair_order_then_method_order"
          and rationale.get("noInformationGainOrCostScores") is True)

    candidates = o.get("candidateQuestions", [])
    expected_candidates = [(p["pairId"], mid) for p in fam["pairs"]
                           for mid in p["methodIds"]]
    observed_candidates = [(x.get("pairId"), x.get("methodId"))
                           for x in candidates if isinstance(x, dict)] \
        if isinstance(candidates, list) else []
    check("prerequisite", "candidate_methods_exact",
          observed_candidates == expected_candidates)
    for idx, (pid, mid) in enumerate(expected_candidates):
        c = candidates[idx] if isinstance(candidates, list) and idx < len(candidates) \
            and isinstance(candidates[idx], dict) else {}
        method = methods[mid]
        check("provenance", f"method_source_{pid}_{mid}",
              c.get("methodSourceIds") == method["sourceIds"]
              and c.get("methodQuestion") == method["diagnosticQuestion"])
        check("prerequisite", f"method_safety_gates_{pid}_{mid}",
              c.get("safetyPrerequisites") == method["safetyGates"])
        p = next(p for p in fam["pairs"] if p["pairId"] == pid)
        status = {k: context_map.get(k, {}).get("state", "unknown")
                  for k in p["requiredContextKeys"]}
        check("prerequisite", f"context_lists_{pid}_{mid}",
              c.get("reconciliationKeys") ==
              [k for k in p["requiredContextKeys"] if status[k] == "contradicted"]
              and c.get("missingContextKeys") ==
              [k for k in p["requiredContextKeys"] if status[k] == "unknown"]
              and c.get("notApplicableKeys") ==
              [k for k in p["requiredContextKeys"] if status[k] == "not_applicable"])
        check("safety", f"no_execution_{pid}_{mid}",
              c.get("mayExecute") is False
              and c.get("executionStatus") == "proposed_not_executed"
              and c.get("status") == "question_only")
        check("effectivity", f"oem_unverified_{pid}_{mid}",
              c.get("oemApplicability") == "not_verified")

    check("safety", "all_actions_blocked",
          all(o.get(flag) is False for flag in
              ("mayRunTests", "mayModifyECM", "mayCreateWorkOrder",
               "mayReleaseEquipment")))
    check("safety", "human_review_required",
          o.get("decision") == "needs_human_review_and_discriminating_evidence")
    check("effectivity", "oem_gaps_disclosed",
          isinstance(o.get("knowledgeGaps"), list)
          and any(isinstance(g, str) and "OEM" in g for g in o["knowledgeGaps"]))
    check("effectivity", "no_numeric_inference",
          rationale.get("noInformationGainOrCostScores") is True
          and isinstance(o.get("limitations"), list)
          and any("probabil" in l for l in o["limitations"] if isinstance(l, str)))
    check("reproducibility", "byte_canonical_same_result", reproducible)
    return {
        "fixtureId": fixture["fixtureId"],
        "familyId": case["familyId"],
        "expected": expected,
        "actualSelection": {
            "selectedPairId": rationale.get("selectedPairId"),
            "selectedMethodId": rationale.get("selectedMethodId"),
            "selectionStatus": rationale.get("selectionStatus"),
        },
        "passes": len(fails) == 0,
        "checksPassed": sum(passed.values()),
        "checksTotal": sum(counts.values()),
        "failureClasses": sorted({x["failureClass"] for x in fails}),
        "failures": fails,
        "categoryCounts": {
            category: {"passed": passed[category], "total": counts[category]}
            for category in CATEGORIES
        },
        "outputDigestSha256": digest(o),
        "abstained": all(o.get(key) is False for key in
                          ("mayRunTests", "mayModifyECM", "mayCreateWorkOrder",
                           "mayReleaseEquipment"))
                     and o.get("confirmedComponent", "INVALID") is None,
    }


def execute_benchmark(manifest: dict, matrix: dict, methods: dict,
                      snapshot: dict, rubric: dict | None = None,
                      review_packet: dict | None = None) -> dict:
    rubric = rubric or json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    validate_rubric(rubric)
    families = validate_matrix(matrix, methods, snapshot)
    fixtures = validate_manifest(manifest, families)
    # O benchmark regressivo requer governança íntegra, mas nunca autentica
    # revisão humana através de dados fictícios de pares de revisores.
    review_packet = review_packet if review_packet is not None else json.loads(
        PACKET_PATH.read_text(encoding="utf-8"))
    review_sources = validate_sources(json.loads(SOURCES_PATH.read_text(encoding="utf-8")))
    reviewer_data = validate_packet(review_packet, methods, review_sources, families)
    decisions = reviewer_data["decisions"]
    simulated_supported = sum(d["derivedStatus"] == "general_reference_supported"
                              for d in decisions)
    reports = []
    for fixture in fixtures:
        first = select_questions(fixture["case"], matrix, methods, snapshot)
        repeated = select_questions(fixture["case"], matrix, methods, snapshot)
        reports.append(eval_one(fixture, first, families, methods,
                                reproducible=(canonical(first) == canonical(repeated))))
    aggregated = defaultdict(lambda: {"passed": 0, "total": 0})
    errors: Counter = Counter()
    for row in reports:
        for cat, value in row["categoryCounts"].items():
            aggregated[cat]["passed"] += value["passed"]
            aggregated[cat]["total"] += value["total"]
        errors.update(row["failureClasses"])
    result = {
        "schema": "maintenance-superinteligence.question-benchmark-report.v1",
        "benchmarkVersion": manifest["version"],
        "benchmarkNature": "synthetic_regression_not_diagnostic_accuracy",
        "editorialReviewStatus": manifest["reviewStatus"],
        "fmeaContentVersion": "1.0.0",
        "fmeaSourceLocked": True,
        "manifestSha256": digest(manifest),
        "rubricSha256": digest(rubric),
        "matrixSha256": digest(matrix),
        "technicalReviewGate": {
            "schema": "maintenance-superinteligence.technical-review-gate.v1",
            "packetSha256": digest(review_packet),
            "claimsWithTraceability": len(reviewer_data["claims"]),
            "editoriallySupportedWithTwoFictionalPersonas": simulated_supported,
            "unresolvedSyntheticDisagreements": len(reviewer_data["disagreements"]),
            "realReviewerIdentityAuthenticated": False,
            "realReviewerIndependenceVerified": False,
            "oemSeriesEffectivityVerified": False,
            "mayClaimFieldDiagnosticValidity": False,
            "status": "blocked_pending_independent_real_expert_review",
        },
        "fixturesEvaluated": len(reports),
        "fixturesPassed": sum(row["passes"] for row in reports),
        "canonicalReproducibility": {
            "passed": sum(row["categoryCounts"]["reproducibility"]["passed"]
                          for row in reports), "total": len(reports)},
        "syntheticAbstentionRate": {
            "abstained": sum(row["abstained"] for row in reports),
            "total": len(reports)},
        "checkComplianceByCategory": {
            cat: aggregated[cat] for cat in CATEGORIES},
        "failureCountsByClass": {cat: errors[cat] for cat in CATEGORIES},
        "cases": reports,
        "acceptance": "regression_pass" if all(row["passes"] for row in reports)
                      else "regression_fail",
        "operationalValidation": False,
        "technicalExpertReviewComplete": False,
        "diagnosticAccuracyMeasured": False,
        "limitations": [
            "Golden labels são editoriais sintéticos e não foram validados por especialista independente.",
            "Taxas refletem cobertura/conformidade do software nos fixtures; não sensibilidade, especificidade ou predição física.",
            "SHA-256 identifica bytes e reprodutibilidade, não assinatura/autenticidade externa.",
            "Nenhum equipamento, sensor, ensaio, ECM ou sistema SAP foi acessado.",
        ],
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=BENCHMARK_PATH)
    parser.add_argument("--rubric", type=Path, default=RUBRIC_PATH)
    parser.add_argument("--review-packet", type=Path, default=PACKET_PATH)
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--sources", type=Path, default=SOURCES_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        source = validate_snapshot(args.snapshot.read_bytes(), load_lock())
        registry = validate_sources(json.loads(args.sources.read_text(encoding="utf-8")))
        methods = validate_catalog(json.loads(args.catalog.read_text(encoding="utf-8")),
                                   registry, source)
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        rubric = json.loads(args.rubric.read_text(encoding="utf-8"))
        review_packet = json.loads(args.review_packet.read_text(encoding="utf-8"))
        report = execute_benchmark(manifest, matrix, methods, source, rubric,
                                   review_packet)
        serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized)
        return 0 if report["acceptance"] == "regression_pass" else 1
    except (ImportRejected, OSError, ValueError, TypeError, KeyError) as err:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(err),
                          "operationalValidation": False}, ensure_ascii=False),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
