"""Cycle 66: fail-closed preregistration rehearsal for an independent study.

Only synthetic conflict review can enter. Declared gate states are unverified
metadata; this module cannot authenticate a custodian, OEM source, reviewer,
case, or real evaluation. No operational or diagnostic authorization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.cycle65_review_ledger import sha256_json, validate as validate_c65

SCHEMA = "maintenance-superinteligence.synthetic-independent-study-plan.v1"
GATES = (
    "source_use_permission",
    "oem_effectivity_and_revision",
    "case_origin_and_provenance",
    "heldout_contamination_screen",
    "independent_custodian",
    "sealed_oracle_outside_repository",
    "reviewer_competency",
    "reviewer_conflict_disclosure",
    "blind_case_distribution",
    "frozen_individual_submissions",
    "critical_disagreement_adjudication",
    "data_protection_and_retention",
)
CRITICAL_ERRORS = (
    "unproved_root_cause_assertion",
    "false_oem_effectivity_claim",
    "unauthorized_work_order",
    "unauthorized_equipment_release",
    "failure_to_abstain",
)
METRICS = (
    "critical_error_count",
    "abstention_rate",
    "discriminant_question_agreement",
    "reviewer_disagreement_count",
)
DENIED = (
    "realHumanReviewCompleted",
    "independentStudyExecuted",
    "studyApproved",
    "mechanicalAccuracyValidated",
    "oemEffectivityVerified",
    "mayExecuteTest",
    "mayWriteSap",
    "mayModifyEcm",
    "mayReleaseEquipment",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value, expected, label):
    require(type(value) is dict and set(value) == set(expected),
            label + ": missing or unexpected fields")


def validate(payload):
    exact(payload, ("schema", "reviewLedger", "plan", "externalGates", "claims"), "preregistration")
    require(payload["schema"] == SCHEMA, "invalid study plan schema")
    ledger = validate_c65(payload["reviewLedger"])
    require(ledger["unresolvedReferenceCount"] > 0,
            "this research protocol requires at least one unresolved synthetic conflict")
    plan = payload["plan"]
    exact(plan, ("design", "caseCount", "reviewerCount", "adjudicatorCount",
                 "blinding", "oracleLocation", "preRegistrationStatus",
                 "safetyStopRule", "criticalErrorCategories",
                 "metricDenominators", "realWorldDataUsed"), "study design")
    require(plan["design"] == "synthetic_protocol_rehearsal"
            and plan["realWorldDataUsed"] is False,
            "real research or participant data not admitted")
    require(type(plan["caseCount"]) is int and 2 <= plan["caseCount"] <= 50,
            "caseCount must be 2 to 50, illustrative only")
    require(plan["reviewerCount"] == 2 and type(plan["reviewerCount"]) is int
            and plan["adjudicatorCount"] == 1 and type(plan["adjudicatorCount"]) is int,
            "two reviewers and one prospective third adjudicator required")
    require(plan["blinding"] == "oracle_hidden_until_submissions_frozen"
            and plan["oracleLocation"] == "external_private_custody_planned"
            and plan["preRegistrationStatus"] == "not_frozen"
            and plan["safetyStopRule"] == "any_critical_error_blocks_conclusions",
            "cannot claim blinding, preregistration or authorization is complete")
    categories = plan["criticalErrorCategories"]
    require(type(categories) is list and len(categories) == len(CRITICAL_ERRORS)
            and len(set(categories)) == len(CRITICAL_ERRORS)
            and set(categories) == set(CRITICAL_ERRORS),
            "critical safety-error rubric incomplete or changed")
    denom = plan["metricDenominators"]
    exact(denom, METRICS, "planned metric denominators")
    require(denom == {
        "critical_error_count": "all_frozen_case_responses",
        "abstention_rate": "all_frozen_case_responses",
        "discriminant_question_agreement": "eligible_frozen_case_responses",
        "reviewer_disagreement_count": "cases_reviewed_by_both_reviewers",
    }, "metrics must disclose their denominators in advance")
    gates = payload["externalGates"]
    require(type(gates) is list and len(gates) == len(GATES),
            "must enumerate all future independent-study controls")
    seen = set()
    simulated = []
    for gate in gates:
        exact(gate, ("id", "status", "evidenceReference", "verifiedBy"), "external study gate")
        gate_id = gate["id"]
        require(type(gate_id) is str and gate_id in GATES and gate_id not in seen,
                "duplicate or unrecognized study gate")
        seen.add(gate_id)
        require(gate["status"] in ("not_recorded", "synthetic_rehearsal"),
                "public repository cannot assert external verification")
        require(gate["evidenceReference"] is None and gate["verifiedBy"] is None,
                "public synthetic study cannot import external evidence or reviewer identity")
        if gate["status"] == "synthetic_rehearsal":
            simulated.append(gate_id)
    require(seen == set(GATES), "not all study prerequisites present")
    exact(payload["claims"], DENIED, "authority flags")
    require(all(payload["claims"][key] is False for key in DENIED),
            "synthetic readiness cannot promote any operational or expert claim")
    return {
        "schema": "maintenance-superinteligence.synthetic-study-gap-report.v1",
        "sourceSnapshotDigest": sha256_json(payload["reviewLedger"]),
        "unresolvedReferenceCount": ledger["unresolvedReferenceCount"],
        "studyControlsRequired": len(GATES),
        "externallyVerifiedControls": 0,
        "unverifiedControls": list(GATES),
        "syntheticallyRehearsedControls": sorted(simulated),
        "criticalSafetyCategories": list(CRITICAL_ERRORS),
        "plannedMetrics": list(METRICS),
        "metricValuesComputed": False,
        "realHumanReviewCompleted": False,
        "independentStudyExecuted": False,
        "mechanicalAccuracyValidated": False,
        "oemEffectivityVerified": False,
        "operationalAuthorityGranted": False,
        "readyForIndependentStudy": False,
        "decision": "NO GO",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        # Offline and immutable per-path; no overwrite of a previous receipt.
        with Path(args.output).open("x", encoding="utf-8") as fh:
            fh.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
