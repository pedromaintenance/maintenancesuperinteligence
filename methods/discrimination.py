"""Seletor determinístico de PERGUNTAS diagnósticas didáticas, não de testes em campo.

Matriz editorial explícita: os resultados condicionais NÃO são observações reais.
Nega probabilidades de falha, decisões SAP/ECM, limites OEM e autorização operacional.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import (ImportRejected, load_lock, require,
                                    validate_snapshot)
from methods.library import (CATALOG_PATH, SOURCES_PATH, validate_catalog,
                             validate_sources)

ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "methods/discrimination-matrix.v1.json"
FAMILY_IDS = ("final_drive", "hydraulics", "electronics")
FAMILY_DOMAINS = {"final_drive": {"oil", "mechanics", "vibration"},
                  "hydraulics": {"hydraulics"},
                  "electronics": {"electronics"}}
CASE_FIELDS = {"schema", "caseId", "familyId", "scenario", "evidenceNature",
               "reportedSignals", "contextStates", "oemGate"}
MATRIX_FIELDS = {"schema", "version", "purpose", "reviewStatus",
                 "approvedForOperationalUse", "sourceVersion", "families"}
PAIR_FIELDS = {"pairId", "firstHypothesisId", "secondHypothesisId", "question",
               "methodIds", "requiredContextKeys", "conditionalOutcomes",
               "knowledgeNature", "testStatus", "hasObservedOutcome", "sourceRefs"}
STATE_VALUES = {"unknown", "available_simulated", "contradicted", "not_applicable"}


def exact(x: object, fields: set[str], where: str) -> dict:
    require(isinstance(x, dict) and set(x) == fields,
            f"{where}: extra or missing fields")
    return x


def text(x: object) -> bool:
    return isinstance(x, str) and bool(x.strip()) and len(x) <= 1200


def unique_list(value: object, where: str, minimum: int = 1) -> list:
    require(isinstance(value, list) and len(value) >= minimum,
            f"{where}: list required")
    require(all(isinstance(x, str) and text(x) for x in value),
            f"{where}: text required")
    require(len(value) == len(set(value)), f"{where}: duplicate reference")
    return value


def validate_matrix(matrix: object, methods: dict, fmea: dict | None = None) -> dict:
    x = exact(matrix, MATRIX_FIELDS, "matrix")
    require(x["schema"] == "maintenance-superinteligence.discrimination-matrix.v1"
            and x["version"] == "1.0.0"
            and x["purpose"] == "synthetic_question_selection_only"
            and x["reviewStatus"] == "author_didactic_rubric_not_oem"
            and x["approvedForOperationalUse"] is False
            and x["sourceVersion"] == "1.0.0",
            "matrix: authority or version changed")
    require(isinstance(x["families"], list) and len(x["families"]) == 3,
            "matrix: all three didactic families required")
    families = {}
    for family in x["families"]:
        exact(family, {"familyId", "label", "hypotheses", "pairs"}, "family")
        fid = family["familyId"]
        require(fid in FAMILY_IDS and fid not in families and text(family["label"]),
                "family: invalid or duplicate id")
        require(isinstance(family["hypotheses"], list)
                and len(family["hypotheses"]) >= 4
                and isinstance(family["pairs"], list)
                and len(family["pairs"]) >= 3,
                "family: insufficient independent hypotheses/pairs")
        hypotheses = set()
        for h in family["hypotheses"]:
            exact(h, {"hypothesisId", "title", "nature"}, "hypothesis")
            require(text(h["hypothesisId"]) and text(h["title"])
                    and h["nature"] == "unconfirmed_training_alternative",
                    "hypothesis: cannot promote to confirmed")
            require(h["hypothesisId"] not in hypotheses,
                    "hypothesis: duplicate id")
            hypotheses.add(h["hypothesisId"])
        seen_pairs = set()
        for p in family["pairs"]:
            exact(p, PAIR_FIELDS, "pair")
            require(text(p["pairId"]) and p["pairId"] not in seen_pairs,
                    "pair: duplicate/invalid identifier")
            seen_pairs.add(p["pairId"])
            require(p["firstHypothesisId"] in hypotheses
                    and p["secondHypothesisId"] in hypotheses
                    and p["firstHypothesisId"] != p["secondHypothesisId"],
                    "pair: self-reference or orphan hypothesis")
            require(text(p["question"]) and p["knowledgeNature"]
                    == "didactic_conditional_not_validated"
                    and p["testStatus"] == "not_performed"
                    and p["hasObservedOutcome"] is False,
                    "pair: scenario outcomes cannot be observed facts")
            method_ids = unique_list(p["methodIds"], "pair methods", 2)
            require(all(mid in methods
                        and methods[mid]["domain"] in FAMILY_DOMAINS[fid]
                        for mid in method_ids),
                    "pair: method missing or wrong discipline")
            unique_list(p["requiredContextKeys"], "pair context", 2)
            refs = unique_list(p["sourceRefs"], "pair sources")
            expected_sources = ({"fmea_public_1.0.0", "methods_catalog_1.0.0"}
                                if fid == "final_drive" else {"methods_catalog_1.0.0"})
            require(set(refs) == expected_sources,
                    "pair: source provenance falsely attributed")
            outcomes = p["conditionalOutcomes"]
            require(isinstance(outcomes, list) and len(outcomes) == 3,
                    "pair: outcomes must include ambiguity")
            got = set()
            for o in outcomes:
                exact(o, {"outcomeId", "conditionalReading"}, "conditional outcome")
                require(text(o["conditionalReading"])
                        and o["outcomeId"] in {
                            "pattern_first", "pattern_second", "indeterminate"},
                        "pair: invalid hypothetical pattern")
                require(o["outcomeId"] not in got, "pair: duplicate outcome")
                got.add(o["outcomeId"])
            require(got == {"pattern_first", "pattern_second", "indeterminate"},
                    "pair: missing unresolved outcome")
        families[fid] = family
    require(set(families) == set(FAMILY_IDS),
            "matrix: missing expected family")
    if fmea is not None:
        fd_ids = {r["id"] for r in fmea["records"] if r["family"] == "comando_final"}
        valid_ids = fd_ids | {"PILOT-FORMULATION", "PILOT-SAMPLE", "PILOT-OTHER-NOISE"}
        require({h["hypothesisId"] for h in families["final_drive"]["hypotheses"]}
                == valid_ids, "final-drive hypothesis set diverged from pinned FMEA")
        require(all(r["confirmedRootCause"] is False
                    for r in fmea["records"] if r["id"] in fd_ids),
                "FMEA knowledge was promoted into a confirmed failure")
    return families


def validate_case(case: object, families: dict) -> dict:
    c = exact(case, CASE_FIELDS, "case")
    require(c["schema"] == "maintenance-superinteligence.discrimination-case.v1"
            and isinstance(c["caseId"], str)
            and re.fullmatch(r"SIM-[A-Z0-9-]+", c["caseId"])
            and c["familyId"] in families
            and c["evidenceNature"] == "simulation"
            and text(c["scenario"]),
            "case: only supported synthetic research contexts accepted")
    unique_list(c["reportedSignals"], "reported signals")
    gate = exact(c["oemGate"], {"serialOrArrangement", "technicalPublication",
                               "revision", "approved"}, "oem gate")
    require(gate == {"serialOrArrangement": None, "technicalPublication": None,
                     "revision": None, "approved": False},
            "case: false verified OEM effectivity")
    require(isinstance(c["contextStates"], list), "case: contextStates list required")
    allowed = {key for p in families[c["familyId"]]["pairs"]
               for key in p["requiredContextKeys"]}
    states = {}
    for item in c["contextStates"]:
        exact(item, {"key", "state", "sourceRef"}, "context")
        key = item["key"]
        require(key in allowed and key not in states,
                "case: unrecognized or duplicate context key")
        require(item["state"] in STATE_VALUES, "case: context status invalid")
        if item["state"] == "unknown":
            require(item["sourceRef"] is None,
                    "case: unknown context cannot claim source")
        else:
            require(isinstance(item["sourceRef"], str)
                    and re.fullmatch(r"SIM-[A-Z0-9-]+", item["sourceRef"]),
                    "case: contextual source must be synthetic")
        states[key] = item
    return states


def select_questions(case: dict, matrix: dict, methods: dict,
                     fmea: dict | None = None) -> dict:
    families = validate_matrix(matrix, methods, fmea)
    states = validate_case(case, families)
    family = families[case["familyId"]]
    comparisons = []
    choices = []
    for p in family["pairs"]:
        conditions = [
            {"key": key,
             "state": states[key]["state"] if key in states else "unknown",
             "sourceRef": states[key]["sourceRef"] if key in states else None}
            for key in p["requiredContextKeys"]
        ]
        conflicts = [x["key"] for x in conditions if x["state"] == "contradicted"]
        missing = [x["key"] for x in conditions if x["state"] == "unknown"]
        na = [x["key"] for x in conditions if x["state"] == "not_applicable"]
        # Sequência editorial, NÃO score de probabilidade, utilidade ou custo.
        state = ("reconcile_contradiction" if conflicts else
                 "ask_missing_context" if missing else
                 "review_applicability" if na else "prepare_human_method_review")
        comparisons.append({
            "pairId": p["pairId"],
            "hypothesisIds": [p["firstHypothesisId"], p["secondHypothesisId"]],
            "bothRemainOpen": True,
            "question": p["question"],
            "discriminatingContext": conditions,
            "status": state,
            "conditionalPatterns": p["conditionalOutcomes"],
            "observedOutcome": None,
        })
        for i, method_id in enumerate(p["methodIds"]):
            method = methods[method_id]
            choices.append({
                "pairId": p["pairId"], "methodId": method_id,
                "methodOrderInPair": i, "contextStatus": state,
                "firstQuestion": (
                    f"Conciliar fontes simuladas de: {', '.join(conflicts)}"
                    if conflicts else
                    f"Obter contexto faltante: {', '.join(missing)}"
                    if missing else
                    f"Justificar aplicabilidade de: {', '.join(na)}"
                    if na else method["diagnosticQuestion"]
                ),
                "methodQuestion": method["diagnosticQuestion"],
                "methodSourceIds": method["sourceIds"],
                "reconciliationKeys": conflicts,
                "missingContextKeys": missing,
                "notApplicableKeys": na,
                "interpretationLimits": [x["description"]
                                         for x in method["interpretationLimits"]],
                "safetyPrerequisites": method["safetyGates"],
                "status": "question_only",
                "executionStatus": "proposed_not_executed",
                "oemApplicability": "not_verified",
                "mayExecute": False,
            })
    priority = {"reconcile_contradiction": 0, "ask_missing_context": 1,
                "review_applicability": 2, "prepare_human_method_review": 3}
    chosen = min(choices, key=lambda x: (
        priority[x["contextStatus"]],
        next(i for i, p in enumerate(family["pairs"]) if p["pairId"] == x["pairId"]),
        x["methodOrderInPair"]))
    return {
        "schema": "maintenance-superinteligence.discrimination-selection.v1",
        "caseId": case["caseId"], "familyId": case["familyId"],
        "matrixVersion": matrix["version"], "catalogVersion": "1.0.0",
        "fmeaVerifiedBySnapshot": fmea is not None,
        "evidenceNature": "simulation",
        "reportedSignalsAreMeasurements": False,
        "hypotheses": [{"id": h["hypothesisId"], "title": h["title"],
                         "status": "open_not_confirmed", "confirmedRootCause": False}
                        for h in family["hypotheses"]],
        "comparisons": comparisons,
        "selectionRationale": {
            "rule": "contradiction_then_unknown_then_not_applicable_then_review",
            "tieBreak": "editorial_pair_order_then_method_order",
            "noInformationGainOrCostScores": True,
            "selectedPairId": chosen["pairId"],
            "selectedMethodId": chosen["methodId"],
            "selectedNextQuestion": chosen["firstQuestion"],
            "selectionStatus": chosen["contextStatus"],
            "reason": "Selecionada pergunta a partir de bloqueios explícitos; não indica melhor teste físico nem probabilidade de falha.",
        },
        "candidateQuestions": choices,
        "knowledgeGaps": ["Publicação OEM efetiva por série, pontos e condição de ensaio",
                          "Instrumentos, método, segurança e validação independente"],
        "decision": "needs_human_review_and_discriminating_evidence",
        "mayRunTests": False, "mayModifyECM": False,
        "mayCreateWorkOrder": False, "mayReleaseEquipment": False,
        "confirmedComponent": None,
        "limitations": [
            "Matriz editorial não é validação científica de sensibilidade/especificidade.",
            "Padrões de resultado são condicionais e não foram observados.",
            "Dois ou mais mecanismos concorrentes permanecem abertos.",
            "Não há parâmetros OEM, custo, duração, risco residual ou score probabilístico inferido.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--sources", type=Path, default=SOURCES_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        snapshot = validate_snapshot(args.snapshot.read_bytes(), load_lock())
        registry = validate_sources(json.loads(args.sources.read_text(encoding="utf-8")))
        methods = validate_catalog(json.loads(args.catalog.read_text(encoding="utf-8")),
                                   registry, snapshot)
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
        case = json.loads(args.case.read_text(encoding="utf-8"))
        result = select_questions(case, matrix, methods, snapshot)
        out = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(out, encoding="utf-8")
        print(out)
        return 0
    except (ImportRejected, OSError, ValueError, TypeError, KeyError) as err:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(err),
                          "mayRunTests": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
