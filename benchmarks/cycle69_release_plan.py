"""Cycle 69: offline dependency-based decomposition of an unmerged research stack.

The manifest is a dated GitHub metadata snapshot. It cannot confirm current
branch protection, CI, technical quality, mergeability, or OEM applicability.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "benchmarks" / "cycle69-isolated-integration-plan.v1.json"
INVENTORY = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"
CYCLES = tuple(range(58, 67))
STAGES = ("not_opened", "draft_pilot_on_main")
NO_AUTHORITY = (
    "operationalAuthorityGranted", "readyForMerge", "mayExecuteTest",
    "mayWriteSap", "mayModifyEcm", "mayReleaseEquipment",
)


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def safe_path(root, relative):
    need(type(relative) is str and relative and not relative.startswith("/")
         and ".." not in Path(relative).parts and "\\" not in relative,
         "invalid path in integration plan")
    return root / relative


def dependencies(path):
    """Only static direct Python imports are covered, not dynamic imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found = re.fullmatch(r"benchmarks\.cycle(\d+)_[a-z0-9_]+", node.module)
            if found:
                result.add(int(found.group(1)))
    return sorted(result)


def audit(root, plan, inventory):
    root = Path(root).resolve()
    need(type(plan) is dict
         and set(plan) == {"schema", "snapshotDate", "snapshotNature",
                           "repository", "sourceRef", "mainSnapshot",
                           "integrationOrder", "groups", "units",
                           "deferredResearchTooling", "requiredReview", "authority"},
         "invalid release-plan structure")
    need(plan["schema"] == "maintenance-superinteligence.cycle69-integration-decomposition.v1"
         and plan["snapshotNature"] ==
         "connector_snapshot_not_live_branch_protection_or_authentication",
         "plan must declare non-live metadata")
    need(plan["sourceRef"] == "research/cycle68-integration-ci-remediation",
         "unexpected source for research extraction")
    snap = plan["mainSnapshot"]
    need(type(snap) is dict and set(snap) ==
         {"commit", "comparisonStatus", "researchAhead",
          "researchBehind", "changedFiles"}, "incomplete main comparison")
    need(type(snap["commit"]) is str and
         re.fullmatch("[a-f0-9]{40}", snap["commit"])
         and snap["comparisonStatus"] == "diverged"
         and all(type(snap[k]) is int and snap[k] >= 0
                 for k in ("researchAhead", "researchBehind", "changedFiles")),
         "main comparison is only a numeric/historical snapshot")
    claims = plan["authority"]
    need(type(claims) is dict and set(claims) == set(NO_AUTHORITY) | {"decision"}
         and claims["decision"] == "NO GO"
         and all(claims[k] is False for k in NO_AUTHORITY),
         "cannot assert merge or operational approval")
    review = plan["requiredReview"]
    need(type(review) is dict
         and set(review) == {"codeReviewCompleted", "licensingAndPrivacyReviewCompleted",
                             "humanPortalQACompleted", "independentEngineeringReviewCompleted",
                             "oemEffectivityVerified", "noMergeUntilBaseRechecked"}
         and review["noMergeUntilBaseRechecked"] is True
         and all(review[k] is False for k in review if k != "noMergeUntilBaseRechecked"),
         "missing independent approval gates")
    held = plan["deferredResearchTooling"]
    need(type(held) is dict and held["cycles"] == [67, 68]
         and held["state"] == "not_rebased_or_merged"
         and type(held["reason"]) is str and len(held["reason"]) > 40,
         "audit tools cannot be silently merged")
    order = plan["integrationOrder"]
    need(type(order) is list and len(order) == len(CYCLES)
         and set(order) == set(CYCLES) and len(set(order)) == len(CYCLES),
         "integration order must cover each cycle once")
    groups = plan["groups"]
    need(type(groups) is list and len(groups) == 3
         and {g["id"] for g in groups} ==
         {"causal_structure", "dimensional_metrology",
          "source_and_study_governance"}
         and all(type(g["meaning"]) is str and len(g["meaning"]) > 10
                 for g in groups),
         "three distinct integration domains are required")
    grouped = [c for group in groups for c in group["cycles"]]
    need(sorted(grouped) == list(CYCLES), "thematic groups must partition all cycles")
    historical = inventory["inventory"]
    need(type(historical) is list
         and [entry["cycle"] for entry in historical] == list(CYCLES),
         "C67 inventory mismatch")
    by_cycle = {entry["cycle"]: entry for entry in historical}
    units = plan["units"]
    need(type(units) is list and [u["cycle"] for u in units] == order,
         "unit sequence must match integration order")
    errors, rows = [], []
    counted_pilots = []
    seen = set()
    for unit in units:
        cycle = unit["cycle"]
        rec = by_cycle[cycle]
        row = {"cycle": cycle, "status": unit["integrationState"],
               "directDependencies": unit["dependencies"], "pilotPr": None,
               "missingArtifacts": []}
        if set(unit) != {"cycle", "sourcePr", "code", "test", "workflow",
                         "doc", "dependencies", "integrationState", "pilot"}:
            errors.append(f"C{cycle}: invalid release-unit fields")
            rows.append(row)
            continue
        if unit["sourcePr"] != rec["pr"] or any(
            unit[name] != rec[name] for name in ("code", "test", "workflow", "doc")
        ):
            errors.append(f"C{cycle}: release unit differs from tracked research source")
        for field in ("code", "test", "workflow", "doc"):
            if not safe_path(root, unit[field]).is_file():
                row["missingArtifacts"].append(field)
        if row["missingArtifacts"]:
            errors.append(f"C{cycle}: files missing: {row['missingArtifacts']}")
        if unit["dependencies"] != rec["dependencies"]:
            errors.append(f"C{cycle}: dependencies differ from tracked source")
        if not set(unit["dependencies"]).issubset(seen):
            errors.append(f"C{cycle}: integration order violates prerequisites")
        if cycle in seen:
            errors.append(f"C{cycle}: duplicated stage")
        seen.add(cycle)
        if not row["missingArtifacts"]:
            try:
                inferred = dependencies(safe_path(root, unit["code"]))
                if inferred != unit["dependencies"]:
                    errors.append(f"C{cycle}: source imports disagree with release plan")
            except (OSError, SyntaxError, ValueError) as exc:
                errors.append(f"C{cycle}: cannot read source AST: {exc}")
        status = unit["integrationState"]
        if status not in STAGES:
            errors.append(f"C{cycle}: invalid pilot status")
        if status == "draft_pilot_on_main":
            pilot = unit["pilot"]
            counted_pilots.append(cycle)
            if type(pilot) is not dict or set(pilot) != {
                "pr", "branch", "sha", "base", "draft",
                "merged", "expectedFiles"}:
                errors.append(f"C{cycle}: incomplete pilot metadata")
            else:
                row["pilotPr"] = pilot["pr"]
                expected_files = [unit[n] for n in ("code", "test", "workflow", "doc")]
                if (unit["dependencies"] or pilot["base"] != "main"
                    or pilot["draft"] is not True or pilot["merged"] is not False
                    or type(pilot["pr"]) is not int
                    or pilot["pr"] <= 0
                    or not re.fullmatch("[a-f0-9]{40}", pilot["sha"])
                    or pilot["expectedFiles"] != expected_files
                    or pilot["branch"] not in {
                        "integration/cycle69-pilot-c58-causal-gate",
                        "integration/cycle69-pilot-c60-metrology",
                    }):
                    errors.append(f"C{cycle}: pilot is not a root-only unmerged draft")
        elif unit["pilot"] is not None:
            errors.append(f"C{cycle}: unopened unit must have no pilot")
        rows.append(row)
    if counted_pilots != [58, 60]:
        errors.append("only two confirmed independent pilots were opened in this snapshot")
    if rows and (rows[0]["cycle"] != 58 or rows[1]["cycle"] != 60):
        errors.append("parallel root pilots must be first")
    return {
        "schema": "maintenance-superinteligence.cycle69-decomposition-audit-result.v1",
        "snapshotDate": plan["snapshotDate"],
        "snapshotNotLive": True,
        "historicalComparison": {
            "researchAhead": snap["researchAhead"],
            "researchBehind": snap["researchBehind"],
            "changedFiles": snap["changedFiles"],
        },
        "unitsAudited": len(rows),
        "standalonePilots": counted_pilots,
        "plannedDependentUnits": [r["cycle"] for r in rows
                                  if r["status"] == "not_opened"],
        "units": rows,
        "structuralErrors": errors,
        "planStatus": "pass" if not errors else "fail",
        "pilotCiAuthenticatedByThisTool": False,
        "approvalToMergeGranted": False,
        "independentExpertReviewCompleted": False,
        "oemEffectivityVerified": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--plan", default=str(PLAN))
    parser.add_argument("--inventory", default=str(INVENTORY))
    parser.add_argument("--output")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    result = audit(args.root, plan, inventory)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as target:
            target.write(rendered)
    else:
        print(rendered, end="")
    if result["planStatus"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
