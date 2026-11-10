"""Cycle 62: typed, synthetic reference comparison without operational authority.

References are fictional training data, NOT OEM limits, alarms, safety criteria
or acceptance decisions. Interval relationships are mathematical only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from benchmarks.cycle60_metrology import UNITS
from benchmarks.cycle61_metrology_context import validate as validate_c61

SCHEMA = "maintenance-superinteligence.synthetic-reference-comparison.v1"
KINDS = {"nominal_target", "expected_operating_band", "alarm_threshold",
         "safety_threshold", "acceptance_band"}
BANDS = {"expected_operating_band", "acceptance_band"}
THRESHOLDS = {"alarm_threshold", "safety_threshold"}
DENIED = ("oemEffectivityVerified", "referenceApproved",
          "diagnosticAccuracyValidated", "maintenanceDecisionAuthorized",
          "expertReviewCompleted", "mayExecuteTest", "mayWriteSap",
          "mayModifyEcm", "mayReleaseEquipment")
ID = re.compile(r"^SIM-[A-Z0-9]{3,20}$")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def exact(obj, fields, name):
    require(type(obj) is dict and set(obj) == set(fields),
            name + ": missing or unexpected fields")


def numeric(v):
    return type(v) in (int, float) and math.isfinite(v)


def normalize(v, unit):
    require(numeric(v), "non-finite or non-numeric reference bound")
    scale = UNITS[unit][1]
    result = v * scale
    require(math.isfinite(result) and result >= 0, "invalid SI reference bound")
    return result


def interval_relation(observed, low, high):
    if observed[1] < low:
        return "entirely_below_reference"
    if observed[0] > high:
        return "entirely_above_reference"
    if observed[0] >= low and observed[1] <= high:
        return "entirely_within_reference"
    return "partially_overlapping_reference"


def threshold_relation(observed, bound, direction):
    # Threshold comparison is not a machine alarm or severity assessment.
    if direction == "above":
        if observed[0] > bound:
            return "entirely_beyond_threshold"
        if observed[1] <= bound:
            return "entirely_not_beyond_threshold"
    else:
        if observed[1] < bound:
            return "entirely_beyond_threshold"
        if observed[0] >= bound:
            return "entirely_not_beyond_threshold"
    return "threshold_crossing_uncertain"


def validate(data):
    exact(data, ("schema", "contextCase", "references", "claims"), "study")
    require(data["schema"] == SCHEMA, "unsupported schema")
    prior = validate_c61(data["contextCase"])
    require(prior["resultIsFictionalObservation"] is True,
            "reported result must be a fictional observation")
    require(prior["contextComparable"] is True,
            "context mismatch: mathematical comparison blocked")
    quantities = {q["role"]: q for q in data["contextCase"]["metrologyCase"]["quantities"]}
    reported = quantities["reported_result"]
    obs_unit = reported["unit"]
    obs_kind, scale = UNITS[obs_unit]
    observed = ((reported["value"] - reported["absoluteUncertainty"]) * scale,
                (reported["value"] + reported["absoluteUncertainty"]) * scale)
    require(all(math.isfinite(x) for x in observed), "observed interval overflow")
    ctx = data["contextCase"]["records"][2]["context"]
    references = data["references"]
    require(type(references) is list and 1 <= len(references) <= 10,
            "one to ten typed references required")
    seen = set()
    comparisons = []
    for ref in references:
        exact(ref, ("id", "kind", "unit", "source", "applicability",
                    "range", "direction"), "reference")
        rid = ref["id"]
        require(type(rid) is str and ID.fullmatch(rid) and rid not in seen,
                "invalid or duplicated reference ID")
        seen.add(rid)
        require(ref["kind"] in KINDS, "unknown reference semantic type")
        require(type(ref["unit"]) is str and ref["unit"] in UNITS and
                UNITS[ref["unit"]][0] == obs_kind, "reference dimensions mismatch")
        exact(ref["source"], ("origin", "documentId", "revision",
                              "effectivityVerified"), "reference source")
        require(ref["source"]["origin"] == "invented_training_source"
                and type(ref["source"]["documentId"]) is str
                and ID.fullmatch(ref["source"]["documentId"])
                and ref["source"]["revision"] == "SYNTHETIC"
                and ref["source"]["effectivityVerified"] is False,
                "source must not impersonate an OEM reference")
        require(ref["applicability"] == ctx,
                "reference operating context does not match fictional observation")
        kind = ref["kind"]
        shape = ref["range"]
        if kind == "nominal_target":
            exact(shape, ("value",), "nominal point")
            require(ref["direction"] is None, "nominal target is not an alarm")
            value = normalize(shape["value"], ref["unit"])
            relation = interval_relation(observed, value, value)
        elif kind in BANDS:
            exact(shape, ("lower", "upper"), "reference band")
            require(ref["direction"] is None, "band cannot be an alarm direction")
            low, high = (normalize(shape["lower"], ref["unit"]),
                         normalize(shape["upper"], ref["unit"]))
            require(low <= high, "inverted reference band")
            relation = interval_relation(observed, low, high)
        else:
            exact(shape, ("value",), "threshold point")
            require(ref["direction"] in ("above", "below"),
                    "alarm/safety thresholds require an explicit direction")
            bound = normalize(shape["value"], ref["unit"])
            relation = threshold_relation(observed, bound, ref["direction"])
        comparisons.append({"referenceId": rid, "referenceKind": kind,
                            "mathematicalRelation": relation,
                            "notOperationalDecision": True})
    exact(data["claims"], DENIED, "claims")
    require(all(data["claims"][x] is False for x in DENIED),
            "reference may not grant expert/operational claims")
    return {"schema": "maintenance-superinteligence.synthetic-reference-result.v1",
            "caseId": prior["caseId"], "observationDimension": obs_kind,
            "comparisons": comparisons,
            "referenceAuthority": "invented_only",
            "actualAlarmEvaluated": False,
            "actualSafetyLimitEvaluated": False,
            "acceptanceOrRejectionIssued": False,
            "oemEffectivityVerified": False,
            "maintenanceDecisionAuthorized": False,
            "operationalAuthorityGranted": False,
            "decision": "NO GO"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as out:
            out.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
