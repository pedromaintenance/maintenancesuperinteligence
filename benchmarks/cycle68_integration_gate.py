"""Cycle 68: audit repaired CI triggers and versioned synthetic output contracts.

This audits local text and author-provided synthetic fixtures. It does not
validate mechanics, authenticate manuals, prove coverage, or approve a merge.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
from pathlib import Path

from benchmarks.cycle67_architecture_audit import audit as audit_c67

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "cycle68-research-interfaces.v1.json"
INVENTORY = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"
CYCLES = list(range(58, 67))
TYPES = {"bool": bool, "int": int, "str": str, "list": list}
DENIED = ("mechanicalDiagnosisValidated", "oemEffectivityVerified",
          "independentExpertReviewCompleted", "mayWriteSap",
          "mayModifyEcm", "mayReleaseEquipment", "readyForMerge")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def _safe_path(root, name):
    require(type(name) is str and name and not name.startswith("/")
            and "\\" not in name and ".." not in Path(name).parts,
            "unsafe relative path")
    return root / name


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            match = re.fullmatch(r"benchmarks\.cycle(\d+)_[a-z0-9_]+", node.module)
            if match:
                result.add(int(match.group(1)))
    return sorted(result)


def _triggers(document, event):
    """Read the exact path-filter stanza; no generic YAML parser needed."""
    pattern = (r"(?m)^  " + re.escape(event) +
               r":\s*\n    paths:\s*\n((?:      - '[^']+'\s*\n)+)")
    match = re.search(pattern, document)
    if match is None:
        return None
    return re.findall(r"(?m)^      - '([^']+)'\s*$", match.group(1))


def _output_check(stage):
    impl = importlib.import_module(stage["module"])
    example_mod = importlib.import_module(stage["fixtureModule"])
    fixture = getattr(example_mod, stage["fixtureFunction"])()
    actual = impl.validate(fixture)
    require(type(actual) is dict, "result must be a dictionary")
    require(actual.get("schema") == stage["resultSchema"],
            "versioned result schema has drifted")
    require(actual.get("decision") == "NO GO",
            "a synthetic result attempted to grant operational authority")
    require(actual.get("operationalAuthorityGranted") is False,
            "explicit operational NO GO flag required")
    for key in stage["mustRemainFalse"]:
        require(actual.get(key) is False, "missing/positive false invariant: " + key)
    for field, name in stage["outputFields"].items():
        require(name in TYPES and type(actual.get(field)) is TYPES[name],
                "output field changed type: " + field)
    return actual


def audit(root, contract, inventory, overrides=None, run_fixtures=True):
    root = Path(root).resolve()
    require(type(contract) is dict and set(contract) ==
            {"schema", "contractScope", "snapshotNature", "researchStages",
             "workflowTriggerPolicy", "authority"}, "incomplete contract")
    require(contract["schema"] ==
            "maintenance-superinteligence.integration-interface-contract.v1"
            and contract["contractScope"] == "synthetic_research_offline_only"
            and contract["snapshotNature"] ==
            "author_asserted_structure_not_mechanical_validation"
            and contract["workflowTriggerPolicy"] ==
            "all_direct_imported_upstream_code_and_tests_for_push_and_pull_request",
            "contract must not claim external or operational evidence")
    claims = contract["authority"]
    require(type(claims) is dict and set(claims) ==
            set(DENIED) | {"decision"} and claims["decision"] == "NO GO"
            and all(claims[key] is False for key in DENIED),
            "contract attempted to promote authority")
    stages = contract["researchStages"]
    require(type(stages) is list and [s["cycle"] for s in stages] == CYCLES,
            "expected nine unique C58-C66 contracts")
    inventory_by_cycle = {s["cycle"]: s for s in inventory["inventory"]}
    require(sorted(inventory_by_cycle) == CYCLES, "historical inventory drift")
    errors, rows = [], []
    trigger_edges = 0
    path_checks = 0
    for stage in stages:
        cycle = stage["cycle"]
        record = inventory_by_cycle[cycle]
        required_fields = {"cycle", "domain", "module", "fixtureModule",
                           "fixtureFunction", "resultSchema", "outputFields",
                           "mustRemainFalse"}
        require(type(stage) is dict and set(stage) == required_fields,
                "missing/extra interface fields")
        require(stage["module"] == "benchmarks." + Path(record["code"]).stem
                and stage["fixtureModule"] == "tests." + Path(record["test"]).stem
                and stage["fixtureFunction"] == ("sample" if cycle == 58 else "fixture")
                and stage["domain"] == record["domain"],
                "contract points to wrong module or fixture")
        require(type(stage["outputFields"]) is dict
                and all(name in TYPES for name in stage["outputFields"].values())
                and type(stage["mustRemainFalse"]) is list
                and "operationalAuthorityGranted" in stage["mustRemainFalse"],
                "incomplete contract invariants")
        row = {"cycle": cycle, "directDependencies": [],
               "workflowEventsChecked": [], "syntheticFixture": "not_run"}
        codepath = _safe_path(root, record["code"])
        workflow_path = record["workflow"]
        try:
            deps = _imports(codepath)
            expected = record["dependencies"]
            row["directDependencies"] = deps
            if deps != expected:
                errors.append("C" + str(cycle) + ": imports differ from historical inventory")
            content = ((overrides or {}).get(workflow_path)
                       if workflow_path in (overrides or {})
                       else _safe_path(root, workflow_path).read_text(encoding="utf-8"))
            for event in ("push", "pull_request"):
                paths = _triggers(content, event)
                if paths is None:
                    errors.append("C" + str(cycle) + ": missing " + event + " paths filter")
                    continue
                row["workflowEventsChecked"].append(event)
                if len(paths) != len(set(paths)):
                    errors.append("C" + str(cycle) + ": duplicated workflow trigger path")
                for item in (record["code"], record["test"]):
                    path_checks += 1
                    if item not in paths:
                        errors.append("C" + str(cycle) + ": absent own path on " + event + ": " + item)
                for dep in deps:
                    parent = inventory_by_cycle[dep]
                    trigger_edges += 1
                    for item in (parent["code"], parent["test"]):
                        path_checks += 1
                        if item not in paths:
                            errors.append("C" + str(cycle) + ": missing upstream " +
                                          str(dep) + " " + event + " path: " + item)
            if run_fixtures:
                _output_check(stage)
                row["syntheticFixture"] = "NO GO"
        except (OSError, SyntaxError, ImportError, KeyError, TypeError,
                AttributeError, ValueError, AssertionError) as exc:
            errors.append("C" + str(cycle) + ": " + str(exc))
        rows.append(row)
    # C67 remains a historical snapshot, but its structural check uses the
    # current local workflow files. It must no longer report known trigger debt.
    if not overrides:
        previous = audit_c67(root, inventory, run_smoke=run_fixtures)
        if previous["inventoryStatus"] != "pass":
            errors.append("C67 structural audit is not passing")
        gap_findings = [f for f in previous["advisoryFindings"]
                        if f["code"] == "upstream_path_filter_gap"]
        if gap_findings:
            errors.append("C67 still reports direct dependency trigger gaps")
    return {
        "schema": "maintenance-superinteligence.integration-audit-result.v1",
        "contractScope": "synthetic_research_offline_only",
        "contractsAudited": len(rows),
        "directDependencyEdgesCheckedPerEvent": trigger_edges // 2,
        "triggerPathChecks": path_checks,
        "cycles": rows,
        "structuralErrors": errors,
        "integrationContractStatus": "pass" if not errors else "fail",
        "mechanicalAccuracyValidated": False,
        "oemEffectivityVerified": False,
        "independentExpertReviewCompleted": False,
        "readyForMerge": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--contract", default=str(CONTRACT))
    parser.add_argument("--inventory", default=str(INVENTORY))
    parser.add_argument("--output")
    args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    result = audit(args.root, contract, inventory)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as output:
            output.write(rendered)
    else:
        print(rendered, end="")
    if result["integrationContractStatus"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
