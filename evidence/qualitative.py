"""Qualitative, unobserved differential observations: no diagnosis is inferred.

"supports"/"weakens" belong to strictly hypothetical branches, NOT case outcomes.
Case evidence can only be classified as contradicted context, not_measured or
inconclusive; no conditional branch is ever selected as a physical result.
"""
from __future__ import annotations
import json
from pathlib import Path

from connectors.fmea_public import ImportRejected, require
from methods.library import ROOT

MATRIX_PATH = ROOT / "evidence/qualitative-discrimination.v1.json"
ROOT_KEYS = {"schema", "version", "purpose", "sourceMatrix", "sourceMethods",
             "approvedForOperationalUse", "observedPhysicalEvidence",
             "independentClinicalOrFieldValidation", "pairs"}
PAIR_KEYS = {"pairId", "familyId", "firstHypothesisId", "secondHypothesisId",
             "requiredContextKeys", "methodIds", "sourceIds",
             "conditionalObservations", "alternativeExplanations",
             "interpretationStatus", "testStatus", "observedOutcome",
             "mayExcludeEitherHypothesis", "canAuthorizeTest"}
OBS_KEYS = {"observationId", "conditionalReading", "effectOnFirst",
            "effectOnSecond", "nature"}
ALT_KEYS = {"explanationId", "statement", "cannotExcludeHypotheses",
            "causalMechanismVerified"}
CASE_EFFECT_STATES = {"contradicted", "not_measured", "inconclusive"}
COUNTERFACTUAL_EFFECTS = {"supports", "weakens", "inconclusive"}


def exact(value: object, fields: set, where: str) -> dict:
    require(isinstance(value, dict) and set(value) == fields,
            f"{where}: unexpected/missing fields")
    return value


def text(value: object, minimum: int = 1) -> bool:
    return isinstance(value, str) and minimum <= len(value.strip()) <= 1200


def validate_qualitative_matrix(data: object, families: dict, methods: dict,
                                sources: dict) -> dict:
    x = exact(data, ROOT_KEYS, "evidence matrix")
    require(x["schema"] == "maintenance-superinteligence.evidence-discrimination-matrix.v1"
            and x["version"] == "1.0.0"
            and x["purpose"] == "qualitative_counterfactual_reasoning_only"
            and x["sourceMatrix"] == "methods/discrimination-matrix.v1.json"
            and x["sourceMethods"] == "methods/catalog.v1.json"
            and x["approvedForOperationalUse"] is False
            and x["observedPhysicalEvidence"] is False
            and x["independentClinicalOrFieldValidation"] is False,
            "evidence matrix: asserted field validity or operational authority")
    expected = {p["pairId"]: (f["familyId"], p)
                for f in families.values() for p in f["pairs"]}
    require(isinstance(x["pairs"], list) and len(x["pairs"]) == len(expected) == 10,
            "evidence matrix: 10 reference pairs required")
    result = {}
    for row in x["pairs"]:
        p = exact(row, PAIR_KEYS, "evidence pair")
        pid = p["pairId"]
        require(pid in expected and pid not in result,
                "evidence pair: duplicated/foreign comparison")
        fid, original = expected[pid]
        actual_sources = sorted({sid for mid in original["methodIds"]
                                 for sid in methods[mid]["sourceIds"]})
        require(p["familyId"] == fid
                and p["firstHypothesisId"] == original["firstHypothesisId"]
                and p["secondHypothesisId"] == original["secondHypothesisId"]
                and p["requiredContextKeys"] == original["requiredContextKeys"]
                and p["methodIds"] == original["methodIds"]
                and p["sourceIds"] == actual_sources
                and all(sid in sources for sid in p["sourceIds"]),
                "evidence pair: IDs, context, method or public-source lineage changed")
        require(p["interpretationStatus"] == "unvalidated_editorial_conditionals"
                and p["testStatus"] == "not_performed"
                and p["observedOutcome"] is None
                and p["mayExcludeEitherHypothesis"] is False
                and p["canAuthorizeTest"] is False,
                "evidence pair: observation/diagnosis/test was fabricated")
        obs = p["conditionalObservations"]
        require(isinstance(obs, list) and len(obs) == 3,
                "evidence pair: first, second and indeterminate required")
        expected_ids = [f"{pid}-OBS-{letter}" for letter in "ABC"]
        expected_effects = [("supports", "weakens"), ("weakens", "supports"),
                            ("inconclusive", "inconclusive")]
        for i, observation in enumerate(obs):
            exact(observation, OBS_KEYS, "conditional observation")
            require(observation["observationId"] == expected_ids[i]
                    and observation["conditionalReading"]
                        == original["conditionalOutcomes"][i]["conditionalReading"]
                    and (observation["effectOnFirst"],
                         observation["effectOnSecond"]) == expected_effects[i]
                    and observation["effectOnFirst"] in COUNTERFACTUAL_EFFECTS
                    and observation["effectOnSecond"] in COUNTERFACTUAL_EFFECTS
                    and observation["nature"] == "counterfactual_not_observed",
                    "evidence pair: altered conditional pattern or promoted evidence")
        require(isinstance(p["alternativeExplanations"], list)
                and len(p["alternativeExplanations"]) == 2,
                "evidence pair: two different counterexamples required")
        distinct = set()
        for i, alternative in enumerate(p["alternativeExplanations"], 1):
            exact(alternative, ALT_KEYS, "counterexample")
            require(alternative["explanationId"] == f"{pid}-ALT-{i:02d}"
                    and text(alternative["statement"], 35)
                    and alternative["statement"] not in distinct
                    and alternative["cannotExcludeHypotheses"] is True
                    and alternative["causalMechanismVerified"] is False,
                    "evidence pair: weak/duplicate counterexample or false exclusion")
            distinct.add(alternative["statement"])
        result[pid] = p
    require(set(result) == set(expected), "evidence matrix: missing pair")
    return result


def assess_case(case: dict, selection: dict, validated: dict, methods: dict) -> dict:
    require(selection["caseId"] == case["caseId"]
            and selection["familyId"] == case["familyId"]
            and selection["reportedSignalsAreMeasurements"] is False
            and selection["confirmedComponent"] is None
            and all(selection[k] is False for k in (
                "mayRunTests", "mayModifyECM", "mayCreateWorkOrder",
                "mayReleaseEquipment")),
            "evidence assessment: fabricated observation or operational decision")
    rows = []
    refs = []
    for comp in selection["comparisons"]:
        p = validated[comp["pairId"]]
        require(p["familyId"] == case["familyId"]
                and comp["hypothesisIds"] == [
                    p["firstHypothesisId"], p["secondHypothesisId"]]
                and comp["observedOutcome"] is None
                and comp["bothRemainOpen"] is True,
                "evidence assessment: hypothesis excluded or observed result forged")
        conditions = comp["discriminatingContext"]
        states = {condition["state"] for condition in conditions}
        state = ("contradicted" if "contradicted" in states else
                 "not_measured" if "unknown" in states else "inconclusive")
        require(state in CASE_EFFECT_STATES, "evidence assessment: unknown state")
        available = [c["sourceRef"] for c in conditions
                     if c["sourceRef"] is not None]
        source_meta = [{"sourceId": sid, "sourceNature": "general_public_reference",
                        "oemApplicabilityVerified": False}
                       for sid in p["sourceIds"]]
        refs.extend(p["sourceIds"])
        observations = [
            {"observationId": o["observationId"],
             "conditionalReading": o["conditionalReading"],
             "effectOnFirstIfObserved": o["effectOnFirst"],
             "effectOnSecondIfObserved": o["effectOnSecond"],
             "observationNature": o["nature"],
             "hasBeenObserved": False,
             "provesRootCause": False,
             "mayExcludeHypothesis": False}
            for o in p["conditionalObservations"]]
        alternatives = [
            {"explanationId": a["explanationId"], "statement": a["statement"],
             "cannotExcludeHypotheses": True,
             "verifiedAsRealMechanism": False}
            for a in p["alternativeExplanations"]]
        rows.append({
            "pairId": p["pairId"],
            "hypothesisIds": [p["firstHypothesisId"], p["secondHypothesisId"]],
            "evidenceClaim": {
                "claimNature": "editorial_conditional_no_test",
                "reportedSymptomIsMeasurement": False,
                "mechanismVerified": False,
                "rootCauseVerified": False,
                "observedSupportOrWeakening": None,
                "bothHypothesesRemainOpen": True,
            },
            "evidenceProvenance": {
                "contextRefs": available,
                "contextRefsNature": "simulated_context_metadata_only",
                "generalSourceIds": p["sourceIds"],
                "sourceClaimsOemEffectivity": False,
                "externalAuthenticityVerified": False,
                "sourceMetadata": source_meta,
            },
            "currentEvidenceState": state,
            "contextRequirements": conditions,
            "conditionalObservations": observations,
            "alternativeExplanations": alternatives,
            "methodPlanning": [
                {"methodId": mid,
                 "question": methods[mid]["diagnosticQuestion"],
                 "prerequisites": [x["description"]
                                   for x in methods[mid]["prerequisites"]],
                 "safetyGates": methods[mid]["safetyGates"],
                 "interpretationLimits": [x["description"]
                                          for x in methods[mid]["interpretationLimits"]],
                 "sourceIds": methods[mid]["sourceIds"],
                 "testStatus": "not_performed", "mayExecute": False}
                for mid in p["methodIds"]],
            "cannotDismissEitherHypothesis": True,
            "testsPerformed": 0,
            "observedPhysicalEvidence": False,
            "fieldResult": None,
        })
    return {
        "schema": "maintenance-superinteligence.case-evidence-assessment.v1",
        "caseId": case["caseId"],
        "evidenceNature": "simulation",
        "causalLevelAssessment": {
            "symptomReported": True, "effectObservedByMeasurement": False,
            "immediateMechanismEstablished": False,
            "rootCauseEstablished": False,
            "observationMaturity": "unmeasured_context_only",
        },
        "comparisons": rows,
        "comparisonCount": len(rows),
        "unmeasuredOrContradictedPairs": sum(
            x["currentEvidenceState"] in {"not_measured", "contradicted"}
            for x in rows),
        "observedSupportCount": 0, "observedWeakeningCount": 0,
        "testsPerformed": 0, "hypothesesExcluded": 0,
        "mayExecuteTests": False, "mayConfirmRootCause": False,
        "mayApproveWorkOrder": False, "mayReleaseEquipment": False,
    }


ORACLE_PATH = ROOT / "benchmarks/qualitative-oracle.v1.json"
ORACLE_KEYS = {"schema", "version", "purpose", "modelSource",
               "sourceBenchmark", "realFieldValidityEstablished",
               "canUseToExcludeHypotheses", "expected"}
EXPECTED_ORACLE_IDS = {
    "SIM-TECH-FD-01", "SIM-TECH-HYD-01",
    "SIM-TECH-ECM-LOG-01", "SIM-TECH-ECM-ACT-01",
}


def validate_oracle(oracle: object, reports: list[dict]) -> dict:
    """Versioned golden synthetic outcomes, NOT expert diagnostic accuracy."""
    o = exact(oracle, ORACLE_KEYS, "qualitative oracle")
    require(o["schema"] == "maintenance-superinteligence.qualitative-oracle.v1"
            and o["version"] == "1.0.0"
            and o["purpose"]
                == "independently_authored_synthetic_regression_expectations_not_mechanical_truth"
            and o["modelSource"] == "evidence/qualitative-discrimination.v1.json"
            and o["sourceBenchmark"] == "benchmarks/question-quality.v1.json"
            and o["realFieldValidityEstablished"] is False
            and o["canUseToExcludeHypotheses"] is False,
            "oracle: field validity or authorization was fabricated")
    require(isinstance(o["expected"], list) and len(o["expected"]) == 4,
            "oracle: four synthetic case records required")
    actual = {r["caseFileId"]: r for r in reports}
    require(set(actual) == EXPECTED_ORACLE_IDS,
            "oracle: expected casefiles missing")
    seen = set()
    for item in o["expected"]:
        exact(item, {"caseFileId", "benchmarkFixtureId", "selectedPairId",
                     "selectedMethodId", "comparisonStates",
                     "observedSupportCount", "observedWeakeningCount",
                     "hypothesesExcluded", "testsPerformed"}, "oracle case")
        cid = item["caseFileId"]
        require(cid in actual and cid not in seen,
                "oracle: unknown or repeated synthetic case")
        seen.add(cid)
        output = actual[cid]
        require(item["benchmarkFixtureId"]
                == output["provenance"]["caseBenchmarkFixtureId"]
                and item["selectedPairId"] == output["selectedQuestion"]["pairId"]
                and item["selectedMethodId"] == output["selectedQuestion"]["methodId"]
                and all(item[k] == 0 for k in (
                    "observedSupportCount", "observedWeakeningCount",
                    "hypothesesExcluded", "testsPerformed")),
                "oracle: question changed or nonzero physical observations")
        comparisons = output["qualitativeEvidence"]["comparisons"]
        require(isinstance(item["comparisonStates"], list)
                and len(item["comparisonStates"]) == len(comparisons),
                "oracle: case comparison count changed")
        for expected, observed in zip(item["comparisonStates"], comparisons):
            exact(expected, {"pairId", "currentEvidenceState",
                             "observedPhysicalEvidence", "bothHypothesesOpen",
                             "conditionalPatternsAreMeasurements"},
                  "oracle comparison")
            require(expected["pairId"] == observed["pairId"]
                    and expected["currentEvidenceState"]
                        == observed["currentEvidenceState"]
                    and expected["currentEvidenceState"] in CASE_EFFECT_STATES
                    and expected["observedPhysicalEvidence"] is False
                    and expected["bothHypothesesOpen"] is True
                    and expected["conditionalPatternsAreMeasurements"] is False,
                    "oracle: expected contradiction/missing/inconclusive state changed")
    return {x["caseFileId"]: x for x in o["expected"]}


def main(argv=None):
    raise SystemExit("Use casefiles.integrated; raw pairs cannot certify field evidence.")


if __name__ == "__main__":
    main()
