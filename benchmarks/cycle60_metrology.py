"""Cycle 60: offline dimensional metrology of invented numbers only.

No real-world sensor, pressure tap, OEM tolerance, or operating permission.
Uncertainty propagation uses interval bounds (not statistical confidence).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCHEMA = "maintenance-superinteligence.synthetic-metrology.v1"
DENIED = ("realMeasurementVerified", "oemApplicabilityVerified",
          "diagnosticAccuracyValidated", "expertReviewCompleted",
          "mayExecuteTest", "mayWriteSap", "mayModifyEcm", "mayReleaseEquipment")
# kind, scale to SI. No affine temperature scales: delta_temperature is an interval.
UNITS = {
    "Pa": ("pressure", 1.0), "kPa": ("pressure", 1000.0),
    "bar": ("pressure", 100000.0), "MPa": ("pressure", 1000000.0),
    "m3/s": ("volume_flow", 1.0), "L/min": ("volume_flow", 0.001 / 60),
    "W": ("power", 1.0), "kW": ("power", 1000.0),
    "N*m": ("torque", 1.0), "rad/s": ("angular_velocity", 1.0),
    "rpm": ("angular_velocity", 2 * math.pi / 60),
    "s": ("time", 1.0), "min": ("time", 60.0),
}
FORMULAS = {
    "hydraulic_power": (("pressure", "volume_flow"), "power"),
    "shaft_power": (("torque", "angular_velocity"), "power"),
}
ROLES = ("input_a", "input_b", "reported_result")


def require(test, message):
    if not test:
        raise ValueError(message)


def fields(value, expected, name):
    require(type(value) is dict and set(value) == set(expected),
            name + ": unexpected or missing fields")


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def interval(entry):
    fields(entry, ("role", "unit", "value", "absoluteUncertainty", "nature"), "quantity")
    require(entry["role"] in ROLES and entry["unit"] in UNITS, "unknown role or unit")
    require(entry["nature"] == "invented_example_only", "cannot assert real measurement")
    v, u = entry["value"], entry["absoluteUncertainty"]
    require(finite(v) and finite(u) and v >= 0 and u >= 0 and u <= v,
            "positive finite values and bounded uncertainties required")
    kind, scale = UNITS[entry["unit"]]
    lo, hi = (v - u) * scale, (v + u) * scale
    require(math.isfinite(hi), "SI conversion overflow")
    return kind, lo, hi


def validate(payload):
    fields(payload, ("schema", "caseId", "origin", "formula",
                     "quantities", "claims"), "case")
    require(payload["schema"] == SCHEMA and payload["origin"] == "synthetic_training_only",
            "only synthetic case schema accepted")
    require(type(payload["caseId"]) is str and
            payload["caseId"].startswith("SYN-") and
            len(payload["caseId"]) <= 24 and
            payload["caseId"][4:].isdigit(), "invalid synthetic case ID")
    require(payload["formula"] in FORMULAS, "unrecognized equation")
    fields(payload["claims"], DENIED, "claims")
    require(all(payload["claims"][c] is False for c in DENIED),
            "claims must not promote field evidence, expertise or authorization")
    quantities = payload["quantities"]
    require(type(quantities) is list and len(quantities) == 3,
            "exactly three quantities required")
    observed = {}
    for item in quantities:
        kind, low, high = interval(item)
        role = item["role"]
        require(role not in observed, "duplicated quantity role")
        observed[role] = (kind, low, high)
    require(set(observed) == set(ROLES), "quantity roles missing")
    inputs, output = FORMULAS[payload["formula"]]
    for role, expected in zip(ROLES, (*inputs, output)):
        require(observed[role][0] == expected,
                "dimension mismatch for " + role + ": expected " + expected)
    a, b, reported = (observed[r] for r in ROLES)
    predicted = (a[1] * b[1], a[2] * b[2])
    require(all(math.isfinite(x) for x in predicted), "calculation overflow")
    # Comparison only; output could be inconsistent due to fictional data or assumptions.
    overlap = max(predicted[0], reported[1]) <= min(predicted[1], reported[2])
    return {
        "schema": "maintenance-superinteligence.synthetic-metrology-result.v1",
        "caseId": payload["caseId"],
        "formula": payload["formula"],
        "resultDimension": output,
        "predictedSIInterval": [predicted[0], predicted[1]],
        "reportedSIInterval": [reported[1], reported[2]],
        "intervalsOverlap": overlap,
        "interpretation": "synthetic_interval_overlap_not_physical_validation",
        "realMeasurementVerified": False,
        "oemApplicabilityVerified": False,
        "diagnosticAccuracyValidated": False,
        "expertReviewCompleted": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as target:
            target.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
