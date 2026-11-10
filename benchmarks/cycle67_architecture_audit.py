"""Cycle 67: offline structural audit of stacked synthetic research increments.

Inventory and PR metadata are a historical snapshot, NOT a live GitHub query.
Passing means paths, declared imports, fixture smoke and tests are coherent;
it never establishes diagnostic validity, independent review or merge readiness.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
from pathlib import Path

DEFAULT_MANIFEST = Path(__file__).with_name("cycle67-consolidation-inventory.v1.json")
EXPECTED_CYCLES = tuple(range(58, 67))
DENIED_RESULTS = (
    "operationalAuthorityGranted", "oemEffectivityVerified",
    "realHumanReviewCompleted", "independentExpertReviewCompleted",
    "mechanicalAccuracyValidated", "diagnosticAccuracyValidated",
    "maintenanceDecisionAuthorized", "technicalConflictResolved",
    "referenceApproved", "readyForIndependentStudy",
)


def _check(ok, message):
    if not ok:
        raise ValueError(message)


def _safe_file(root, rel):
    _check(type(rel) is str and rel and not rel.startswith("/")
           and ".." not in Path(rel).parts and "\\" not in rel,
           "invalid relative repository path")
    return root / rel


def _ast_file(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _test_count(tree):
    return sum(1 for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef)
               for method in node.body
               if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
               and method.name.startswith("test_"))


def _dependencies(tree):
    deps = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            match = re.fullmatch(r"benchmarks\.cycle(\d+)_[a-z0-9_]+", node.module)
            if match:
                deps.add(int(match.group(1)))
    return sorted(deps)


def _smoke(entry):
    module = importlib.import_module("benchmarks." + Path(entry["code"]).stem)
    test_module = importlib.import_module("tests." + Path(entry["test"]).stem)
    sample = test_module.sample() if entry["cycle"] == 58 else test_module.fixture()
    result = module.validate(sample)
    _check(type(result) is dict and result.get("decision") == "NO GO",
           "fixture did not return explicit NO GO")
    for key in DENIED_RESULTS:
        _check(result.get(key) is not True, "unexpected authority flag: " + key)
    return {"decision": "NO GO", "realExpertValidityChecked": False}


def audit(root, manifest, run_smoke=True):
    root = Path(root).resolve()
    _check(type(manifest) is dict
           and manifest.get("schema") ==
           "maintenance-superinteligence.consolidation-inventory.v1",
           "unknown consolidation manifest schema")
    _check(manifest.get("snapshotNature") ==
           "github_metadata_snapshot_not_live_repository_state",
           "snapshot must not be treated as live data")
    cycles = manifest["inventory"]
    _check(type(cycles) is list
           and [entry["cycle"] for entry in cycles] == list(EXPECTED_CYCLES),
           "inventory needs ordered, unique cycles 58..66")
    stack = manifest["stack"]
    _check(type(stack) is list and
           [item["cycle"] for item in stack] == list(range(57, 67)),
           "stack requires PR coverage for cycle 57..66")
    errors = []
    findings = []
    cycle_rows = []
    for i, pr in enumerate(stack):
        if pr["pr"] != pr["cycle"] + 26 or pr["draft"] is not True            or pr["state"] != "open" or pr["merged"] is not False:
            errors.append("invalid PR snapshot metadata for cycle " + str(pr["cycle"]))
        if i and pr["base"] != stack[i - 1]["head"]:
            errors.append("PR chain discontinuity before cycle " + str(pr["cycle"]))
        if not re.fullmatch("[a-f0-9]{40}", pr["headSha"]):
            errors.append("missing head SHA for cycle " + str(pr["cycle"]))
    for entry in cycles:
        number = entry["cycle"]
        row = {"cycle": number, "domain": entry["domain"], "pr": entry["pr"],
               "testMethodDefinitions": 0, "importedUpstreamCycles": [],
               "fixtureSmoke": "not_run", "missingArtifacts": []}
        if (entry["pr"] != number + 26 or
                (entry["upstream"] is not None and entry["upstream"] not in EXPECTED_CYCLES)):
            errors.append("invalid inventory link for cycle " + str(number))
        paths = {key: _safe_file(root, entry[key])
                 for key in ("code", "test", "workflow", "doc")}
        row["missingArtifacts"] = [key for key, path in paths.items()
                                    if not path.is_file()]
        if row["missingArtifacts"]:
            errors.append("missing C" + str(number) + " artifacts: " +
                          ", ".join(row["missingArtifacts"]))
            cycle_rows.append(row)
            continue
        try:
            code_ast = _ast_file(paths["code"])
            tests_ast = _ast_file(paths["test"])
            methods = _test_count(tests_ast)
            deps = _dependencies(code_ast)
            row["testMethodDefinitions"] = methods
            row["importedUpstreamCycles"] = deps
            if methods == 0:
                errors.append("C" + str(number) + ": no test methods defined")
            for name in ("validate", "main"):
                if not any(isinstance(node, ast.FunctionDef) and node.name == name
                           for node in code_ast.body):
                    errors.append("C" + str(number) + ": missing " + name)
            expected = [] if entry["upstream"] is None else [entry["upstream"]]
            if deps != expected:
                errors.append("C" + str(number) +
                              ": code imports disagree with dependency manifest")
            workflow = paths["workflow"].read_text(encoding="utf-8")
            if "pull_request:" not in workflow or "push:" not in workflow:
                errors.append("C" + str(number) + ": workflow trigger missing")
            for own in ("code", "test"):
                if "- '" + entry[own] + "'" not in workflow:
                    errors.append("C" + str(number) +
                                  ": own file missing from workflow trigger: " + own)
            # Downstream CI should rerun when upstream code or upstream tests change.
            if entry["upstream"] is not None:
                parent = cycles[entry["upstream"] - EXPECTED_CYCLES[0]]
                trigger_missing = [key for key in ("code", "test")
                                   if "- '" + parent[key] + "'" not in workflow]
                if trigger_missing:
                    findings.append({
                        "cycle": number, "severity": "review_before_merge",
                        "code": "upstream_path_filter_gap",
                        "missingUpstreamTriggers": trigger_missing,
                        "upstreamCycle": entry["upstream"],
                    })
            for prior in range(58, number + 1):
                item = cycles[prior - 58]
                dotted_test = "tests." + Path(item["test"]).stem
                if dotted_test not in workflow:
                    errors.append("C" + str(number) +
                                  ": cumulative regression misses " + dotted_test)
            if "NO GO" not in paths["doc"].read_text(encoding="utf-8"):
                errors.append("C" + str(number) + ": missing NO GO documentation")
            if run_smoke:
                row["fixtureSmoke"] = _smoke(entry)["decision"]
        except (OSError, SyntaxError, ImportError, AttributeError, TypeError,
                KeyError, ValueError, AssertionError) as exc:
            errors.append("C" + str(number) + ": audit error: " + str(exc))
        cycle_rows.append(row)
    for relative in manifest.get("previousControls", []):
        if not _safe_file(root, relative).is_file():
            errors.append("missing earlier governance document: " + relative)
    comparison = manifest["baseComparison"]
    if comparison["status"] != "diverged" or comparison["behindBy"] <= 0:
        findings.append({"code": "refresh_main_comparison",
                         "severity": "review_before_merge"})
    else:
        findings.append({
            "code": "research_branch_diverged_from_main",
            "severity": "blocking_integration",
            "aheadAtSnapshot": comparison["aheadBy"],
            "behindAtSnapshot": comparison["behindBy"],
            "changedFilesAtSnapshot": comparison["changedFileCount"],
        })
    prereqs = manifest["nonTechnicalPrerequisites"]
    findings.append({"code": "human_and_external_gates_unverified",
                     "severity": "blocking_operational_authority",
                     "humanPortalQAOutstandingAtSnapshot":
                         prereqs["humanPortalQaItemsNotExecuted"],
                     "externalEvidenceGatesUnverifiedAtSnapshot":
                         prereqs["externalEvidenceGatesUnverified"]})
    return {
        "schema": "maintenance-superinteligence.consolidation-audit-result.v1",
        "manifestSnapshotDate": manifest["snapshotDate"],
        "snapshotNotLive": True,
        "inventoryStatus": "pass" if not errors else "fail",
        "inventoryErrors": errors,
        "cyclesAudited": len(cycle_rows),
        "testMethodDefinitions": sum(c["testMethodDefinitions"] for c in cycle_rows),
        "cycles": cycle_rows,
        "advisoryFindings": findings,
        "knownConceptualOverlaps": manifest["knownOverlaps"],
        "realMechanicalValidationCompleted": False,
        "humanIndependentReviewCompleted": False,
        "readyForMerge": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--output")
    args = p.parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = audit(args.root, data)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as f:
            f.write(rendered)
    else:
        print(rendered, end="")
    if result["inventoryStatus"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
