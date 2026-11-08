"""Cycle 58: structural gate for causal claims; NOT a diagnostic evaluator.

Offline, standard-library only. This module never calls an OEM service,
writes SAP/ECM, assigns a root cause, or grants operational authority.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "maintenance-superinteligence.causal-evidence-case.v1"
ID = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
CASE = re.compile(r"^HLD-[0-9]{3}$")
ALLOWED_KINDS = {"document_review", "noninvasive_measurement", "visual_inspection"}
EXPECTED = {"supports", "contradicts", "indeterminate"}
CLAIMS_DENIED = ("causeConfirmed", "oemEffectivityVerified", "mayExecuteTest",
                 "mayWriteSap", "mayModifyEcm", "mayReleaseEquipment",
                 "independentExpertReviewCompleted", "diagnosticAccuracyValidated")


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def exact(obj, fields, label):
    ensure(type(obj) is dict and set(obj) == set(fields), label + ": invalid fields")


def sentence(value, name):
    ensure(type(value) is str and 8 <= len(value) <= 800 and value.strip() == value,
           name + ": provide an explicit, bounded description")


def validate(payload):
    exact(payload, ("schema", "caseId", "context", "hypotheses", "proposedChecks",
                    "claims", "origin"), "case")
    ensure(payload["schema"] == SCHEMA, "wrong schema")
    ensure(type(payload["caseId"]) is str and CASE.fullmatch(payload["caseId"]),
           "invalid case identifier")
    ensure(payload["origin"] == "synthetic_training_only",
           "public gate only accepts explicitly synthetic cases")
    exact(payload["context"], ("requiredFunction", "observedSymptom",
                                "operatingCondition"), "context")
    for key, value in payload["context"].items():
        sentence(value, key)
    hypotheses = payload["hypotheses"]
    ensure(type(hypotheses) is list and 2 <= len(hypotheses) <= 5,
           "two to five competing hypotheses required")
    ids = set()
    for h in hypotheses:
        exact(h, ("id", "mechanism", "counterEvidence", "uncertainty"), "hypothesis")
        ensure(type(h["id"]) is str and ID.fullmatch(h["id"]) and h["id"] not in ids,
               "hypothesis IDs must be unique")
        ids.add(h["id"])
        sentence(h["mechanism"], "mechanism")
        sentence(h["counterEvidence"], "counterEvidence")
        ensure(h["uncertainty"] == "unconfirmed", "cause cannot be promoted")
    checks = payload["proposedChecks"]
    ensure(type(checks) is list and 1 <= len(checks) <= 12,
           "at least one proposed discriminator required")
    checkids = set()
    genuinely_discriminating = 0
    for c in checks:
        exact(c, ("id", "method", "kind", "safeToPerform",
                  "requiresApplicableProcedure", "predictions"), "check")
        ensure(type(c["id"]) is str and ID.fullmatch(c["id"]) and c["id"] not in checkids,
               "check IDs must be unique")
        checkids.add(c["id"])
        sentence(c["method"], "check method")
        ensure(c["kind"] in ALLOWED_KINDS, "unsupported check category")
        ensure(c["safeToPerform"] is False and c["requiresApplicableProcedure"] is True,
               "proposal does not constitute authorization or a safe work procedure")
        predictions = c["predictions"]
        ensure(type(predictions) is list and len(predictions) == len(ids),
               "each check must state the expected outcome for every hypothesis")
        seen, directions = set(), set()
        for p in predictions:
            exact(p, ("hypothesisId", "expectation", "reason"), "prediction")
            ensure(type(p["hypothesisId"]) is str and p["hypothesisId"] in ids
                   and p["hypothesisId"] not in seen, "invalid prediction mapping")
            seen.add(p["hypothesisId"])
            ensure(p["expectation"] in EXPECTED, "unsupported prediction")
            directions.add(p["expectation"])
            sentence(p["reason"], "prediction reason")
        ensure(seen == ids, "predictions missing hypotheses")
        if "supports" in directions and "contradicts" in directions:
            genuinely_discriminating += 1
    ensure(genuinely_discriminating >= 1,
           "at least one check must distinguish competing hypotheses")
    exact(payload["claims"], CLAIMS_DENIED, "claims")
    ensure(all(payload["claims"][k] is False for k in CLAIMS_DENIED),
           "causal confidence or operational privilege promoted without proof")
    return {
        "schema": "maintenance-superinteligence.causal-gate-result.v1",
        "caseId": payload["caseId"],
        "result": "structural_pass_no_diagnostic_validation",
        "hypothesesCompared": len(ids),
        "proposedChecks": len(checks),
        "discriminatingChecks": genuinely_discriminating,
        "causeConfirmed": False,
        "diagnosticAccuracyValidated": False,
        "independentExpertReviewCompleted": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Synthetic case JSON; never private OEM/field data")
    parser.add_argument("--output", help="Optional result-only JSON path")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = validate(data)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        if path.exists():
            raise FileExistsError("will not overwrite previous evaluation receipt")
        with path.open("x", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
