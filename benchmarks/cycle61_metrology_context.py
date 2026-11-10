"""Cycle 61: synthetic measurement provenance and contextual comparability.

Structural cross-check only. No real instrument validity, calibration, OEM
reference, decision to operate, or causal diagnosis is inferred.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from benchmarks.cycle60_metrology import validate as validate_c60, ROLES, UNITS

SCHEMA = "maintenance-superinteligence.synthetic-metrology-context.v1"
ROLE_TYPES = {"input_a": "invented_observation",
              "input_b": "invented_observation"}
MEASUREMENT = "invented_observation"
REFERENCE = "invented_nominal_target"
IDENT = re.compile(r"^SIM-[A-Z0-9]{3,20}$")
DENIED = ("realMeasurementVerified", "calibrationVerified",
          "oemEffectivityVerified", "mechanicalValidityValidated",
          "expertReviewCompleted", "mayExecuteTest", "mayWriteSap",
          "mayModifyEcm", "mayReleaseEquipment")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(obj, keys, label):
    require(type(obj) is dict and set(obj) == set(keys),
            label + ": missing/extra field")


def valid_id(value):
    return type(value) is str and IDENT.fullmatch(value) is not None


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate(payload):
    exact(payload, ("schema", "metrologyCase", "records", "claims"), "context")
    require(payload["schema"] == SCHEMA, "invalid context schema")
    prior = validate_c60(payload["metrologyCase"])
    records = payload["records"]
    require(type(records) is list and len(records) == 3, "one record per quantity required")
    by_role = {}
    for rec in records:
        exact(rec, ("role", "nature", "context", "instrument",
                    "resolution", "uncertaintyModel"), "record")
        role = rec["role"]
        require(type(role) is str and role in ROLES and role not in by_role,
                "duplicate or unsupported role")
        by_role[role] = rec
        ctx = rec["context"]
        exact(ctx, ("scenarioId", "loadState", "thermalState", "samplingWindow"),
              "operational context")
        require(valid_id(ctx["scenarioId"]) and valid_id(ctx["samplingWindow"]),
                "only synthetic identifiers allowed")
        require(ctx["loadState"] in ("idle", "steady_load", "transient")
                and ctx["thermalState"] in ("cold", "stabilized", "warming"),
                "operating state missing")
        instrument = rec["instrument"]
        exact(instrument, ("syntheticId", "calibrationStatus",
                           "calibrationEvidence"), "instrument")
        require(instrument["calibrationStatus"] == "unverified_synthetic"
                and instrument["calibrationEvidence"] is None,
                "cannot claim calibration or certificate")
        if role in ROLE_TYPES or rec["nature"] == MEASUREMENT:
            require(rec["nature"] == MEASUREMENT, "inputs must be fictional readings")
            require(valid_id(instrument["syntheticId"]), "instrument ID required")
            require(rec["uncertaintyModel"] == "declared_absolute_bound",
                    "statistical confidence cannot be assumed")
        else:
            require(role == "reported_result" and rec["nature"] == REFERENCE,
                    "unknown record nature")
            require(instrument["syntheticId"] is None, "nominal target is not a sensor")
            require(rec["uncertaintyModel"] == "declared_target_band",
                    "nominal band must not impersonate measurement uncertainty")
        res = rec["resolution"]
        require(number(res) and res > 0, "positive instrument/band resolution required")
    require(set(by_role) == set(ROLES), "missing quantity role")
    quantities = {x["role"]: x for x in payload["metrologyCase"]["quantities"]}
    for role, rec in by_role.items():
        q = quantities[role]
        require(rec["resolution"] <= 2 * q["absoluteUncertainty"],
                "declared uncertainty must cover at least half the resolution")
        # This is a simple audit rule, not an ISO/GUM uncertainty model.
        require(q["unit"] in UNITS, "unknown unit")
    exact(payload["claims"], DENIED, "claims")
    require(all(payload["claims"][k] is False for k in DENIED),
            "operational or expert status promotion prohibited")
    contexts = {r: by_role[r]["context"] for r in ROLES}
    same_context = contexts["input_a"] == contexts["input_b"]
    result_is_observation = by_role["reported_result"]["nature"] == MEASUREMENT
    if result_is_observation:
        same_context = same_context and contexts["reported_result"] == contexts["input_a"]
    # A nominal target never counts as an observed result, even when contexts match.
    result_comparable = same_context and result_is_observation
    reasons = []
    if not same_context:
        reasons.append("operating_context_mismatch")
    if not result_is_observation:
        reasons.append("nominal_target_is_not_observed_result")
    if result_comparable:
        reasons.append("structural_comparison_only")
    return {
        "schema": "maintenance-superinteligence.synthetic-metrology-context-result.v1",
        "caseId": prior["caseId"],
        "contextComparable": same_context,
        "resultIsFictionalObservation": result_is_observation,
        "comparisonAllowed": result_comparable,
        "reportedIntervalOverlap": prior["intervalsOverlap"] if result_comparable else None,
        "reasonCodes": reasons,
        "metrologyContextReviewed": "synthetic_structure_only",
        "calibrationVerified": False,
        "realMeasurementVerified": False,
        "oemEffectivityVerified": False,
        "mechanicalValidityValidated": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = validate(data)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as dst:
            dst.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
