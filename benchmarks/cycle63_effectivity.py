"""Cycle 63: synthetic reference effectivity matching, not OEM verification.

All identifiers are fabricated. Matching fabricated metadata never grants an
OEM applicability claim or permission for diagnosis, maintenance or operation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from benchmarks.cycle62_reference_semantics import validate as validate_c62

SCHEMA = "maintenance-superinteligence.synthetic-effectivity.v1"
TOKEN = re.compile(r"^SIM-[A-Z0-9]{3,20}$")
SERIAL_PREFIX = re.compile(r"^SIM-[A-Z]{2,6}$")
DENIED = ("realSerialVerified", "oemEffectivityVerified",
          "referenceApproved", "humanExpertReviewCompleted",
          "diagnosticAccuracyValidated", "mayExecuteTest", "mayWriteSap",
          "mayModifyEcm", "mayReleaseEquipment")
ATTRS = ("manufacturer", "model", "arrangement", "component",
         "configuration", "softwareRevision")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(obj, keys, label):
    require(type(obj) is dict and set(obj) == set(keys),
            label + ": missing or extra fields")


def token(value):
    return type(value) is str and TOKEN.fullmatch(value) is not None


def config(value, name):
    exact(value, ATTRS, name)
    require(all(token(value[key]) for key in ATTRS), "synthetic configuration tokens required")


def serial(value, name):
    exact(value, ("prefix", "number"), name)
    require(type(value["prefix"]) is str and SERIAL_PREFIX.fullmatch(value["prefix"]),
            name + ": invalid synthetic serial prefix")
    require(type(value["number"]) is int and 0 <= value["number"] <= 999999,
            name + ": invalid synthetic serial number")


def validate(payload):
    exact(payload, ("schema", "referenceCase", "asset", "effectivities", "claims"), "study")
    require(payload["schema"] == SCHEMA, "incorrect schema")
    previous = validate_c62(payload["referenceCase"])
    asset = payload["asset"]
    exact(asset, ("configuration", "serial", "nature"), "asset")
    require(asset["nature"] == "invented_asset_only", "real asset metadata prohibited")
    config(asset["configuration"], "asset configuration")
    serial(asset["serial"], "asset serial")
    refs = {r["id"] for r in payload["referenceCase"]["references"]}
    effectivities = payload["effectivities"]
    require(type(effectivities) is list and len(effectivities) == len(refs),
            "exactly one declared effectivity per synthetic reference")
    seen = set()
    results = []
    for entry in effectivities:
        exact(entry, ("referenceId", "configuration", "serialRange",
                      "sourceRevision", "sourceStatus", "oemVerified"), "effectivity")
        rid = entry["referenceId"]
        require(type(rid) is str and rid in refs and rid not in seen,
                "unknown or duplicate reference effectivity")
        seen.add(rid)
        config(entry["configuration"], "effectivity configuration")
        sr = entry["serialRange"]
        exact(sr, ("prefix", "start", "end"), "serial range")
        require(type(sr["prefix"]) is str and SERIAL_PREFIX.fullmatch(sr["prefix"]),
                "invalid serial-range prefix")
        require(type(sr["start"]) is int and type(sr["end"]) is int
                and 0 <= sr["start"] <= sr["end"] <= 999999,
                "invalid serial range")
        require(entry["sourceRevision"] == "SYNTHETIC"
                and entry["sourceStatus"] == "unverified_synthetic"
                and entry["oemVerified"] is False,
                "cannot claim source authenticity or effective OEM revision")
        mismatches = []
        for key in ATTRS:
            if entry["configuration"][key] != asset["configuration"][key]:
                mismatches.append(key + "_mismatch")
        if sr["prefix"] != asset["serial"]["prefix"]:
            mismatches.append("serial_prefix_mismatch")
        elif not sr["start"] <= asset["serial"]["number"] <= sr["end"]:
            mismatches.append("serial_number_outside_declared_range")
        # An exact synthetic match means only the strings and numbers match.
        results.append({
            "referenceId": rid,
            "metadataMatch": not mismatches,
            "mismatchReasons": mismatches,
            "applicabilityInterpretation":
                "synthetic_metadata_match_not_oem_verified" if not mismatches
                else "synthetic_metadata_mismatch",
            "oemEffectivityVerified": False,
            "referenceApproved": False
        })
    require(seen == refs, "effectivity coverage incomplete")
    exact(payload["claims"], DENIED, "claims")
    require(all(payload["claims"][x] is False for x in DENIED),
            "authority or real-world effectivity claim denied")
    return {
        "schema": "maintenance-superinteligence.synthetic-effectivity-result.v1",
        "caseId": previous["caseId"],
        "referencesEvaluated": len(results),
        "results": results,
        "realSerialVerified": False,
        "oemEffectivityVerified": False,
        "referenceApproved": False,
        "diagnosticAccuracyValidated": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO"
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output")
    args = p.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as out:
            out.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
