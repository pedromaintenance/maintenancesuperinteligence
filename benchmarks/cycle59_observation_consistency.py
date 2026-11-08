"""Cycle 59: compare *declared* predictions to fictional observations.

This is a logical cross-check, not a physics engine or expert diagnosis.
Any source/measurement validity is unverified. Always NO GO.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from benchmarks.cycle58_causal_gate import validate as validate_c58

SCHEMA = "maintenance-superinteligence.observation-prediction-case.v1"
OBS_ID = re.compile(r"^obs_[a-z0-9_]{3,60}$")
ALLOWED = {"supports", "contradicts", "indeterminate"}
DENIED = ("mechanicalValidityValidated", "observationVerified",
          "humanExpertReviewCompleted", "causeConfirmed", "mayExecuteTest",
          "mayWriteSap", "mayModifyEcm", "mayReleaseEquipment")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def exact(value, fields, label):
    require(type(value) is dict and set(value) == set(fields),
            label + ": unexpected or missing fields")


def narrative(value):
    return type(value) is str and 8 <= len(value) <= 500 and value.strip() == value


def validate(payload):
    exact(payload, ("schema", "causalCase", "observations", "claims"), "study")
    require(payload["schema"] == SCHEMA, "unexpected schema")
    structural = validate_c58(payload["causalCase"])
    checks = {c["id"]: c for c in payload["causalCase"]["proposedChecks"]}
    hypotheses = {h["id"] for h in payload["causalCase"]["hypotheses"]}
    observations = payload["observations"]
    require(type(observations) is list and 1 <= len(observations) <= 20,
            "expected one to twenty synthetic observations")
    seen_ids = set()
    seen_checks = set()
    comparisons = []
    for obs in observations:
        exact(obs, ("id", "checkId", "nature", "recordedOutcome",
                    "recordedText", "sourceStatus", "predictedOutcomes"), "observation")
        require(type(obs["id"]) is str and OBS_ID.fullmatch(obs["id"])
                and obs["id"] not in seen_ids, "duplicate or invalid observation ID")
        seen_ids.add(obs["id"])
        require(type(obs["checkId"]) is str and obs["checkId"] in checks
                and obs["checkId"] not in seen_checks,
                "unknown check or duplicate observation for one check")
        seen_checks.add(obs["checkId"])
        require(obs["nature"] == "synthetic_fictional_record"
                and obs["sourceStatus"] == "unverified_synthetic",
                "observed data cannot claim real field measurement or validation")
        require(obs["recordedOutcome"] in ("pattern_a", "pattern_b", "undetermined"),
                "unrecognized fictional categorical outcome")
        require(narrative(obs["recordedText"]), "observation explanation required")
        preds = obs["predictedOutcomes"]
        require(type(preds) is list and len(preds) == len(hypotheses),
                "every hypothesis requires an observed-outcome interpretation")
        seen_h = set()
        for pred in preds:
            exact(pred, ("hypothesisId", "interpretation", "reason"), "interpretation")
            require(type(pred["hypothesisId"]) is str and pred["hypothesisId"] in hypotheses
                    and pred["hypothesisId"] not in seen_h, "invalid hypothesis mapping")
            seen_h.add(pred["hypothesisId"])
            require(pred["interpretation"] in ALLOWED, "invalid interpretation")
            require(narrative(pred["reason"]), "interpretation reason required")
            declared = next(p["expectation"] for p in checks[obs["checkId"]]["predictions"]
                            if p["hypothesisId"] == pred["hypothesisId"])
            # Here 'conflict' means the *record's own labels* disagree,
            # not that nature has falsified the hypothesis.
            comparisons.append({
                "observationId": obs["id"], "hypothesisId": pred["hypothesisId"],
                "declaredExpectation": declared,
                "recordedInterpretation": pred["interpretation"],
                "labelConflict": declared != pred["interpretation"]
                                 and "indeterminate" not in
                                 (declared, pred["interpretation"])
            })
        require(seen_h == hypotheses, "unmatched hypotheses")
    exact(payload["claims"], DENIED, "claims")
    require(all(payload["claims"][key] is False for key in DENIED),
            "unverified evidence promoted to real authorization or truth")
    conflicts = [p for p in comparisons if p["labelConflict"]]
    return {
        "schema": "maintenance-superinteligence.observation-prediction-result.v1",
        "caseId": structural["caseId"],
        "status": "synthetic_label_comparison_only",
        "syntheticObservations": len(observations),
        "labelComparisons": len(comparisons),
        "labelConflicts": len(conflicts),
        "conflictReferences": [{"observationId": p["observationId"],
                                "hypothesisId": p["hypothesisId"]}
                               for p in conflicts],
        "physicalConsistencyValidated": False,
        "mechanicalValidityValidated": False,
        "humanExpertReviewCompleted": False,
        "causeConfirmed": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        # Never overwrite prior evidence receipts.
        with Path(args.output).open("x", encoding="utf-8") as fp:
            fp.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
