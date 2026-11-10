"""C70: verify a dated map of two isolated dependent PRs, not live CI.

A positive report confirms only local manifest/topology consistency.
No validation of GitHub identity, current merge state, or mechanical evidence.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "benchmarks" / "cycle70-dependent-pilot-extractions.v1.json"
PRIOR = ROOT / "benchmarks" / "cycle69-isolated-integration-plan.v1.json"
INV = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"
EXPECTED = {59: (98, 95, 58), 61: (99, 96, 60)}
DENIED = ("mergesPerformed", "humanCodeReviewVerified",
          "oemEffectivityVerified", "independentMechanicalValidationVerified",
          "operationalAuthorityGranted", "readyForMerge")


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            match = re.fullmatch(r"benchmarks\.cycle(\d+)_[a-z0-9_]+", node.module)
            if match:
                result.add(int(match.group(1)))
    return sorted(result)


def audit(root, current, earlier, inventory):
    root = Path(root).resolve()
    ensure(type(current) is dict and set(current) ==
           {"schema", "snapshotDate", "snapshotNature", "repository", "researchBase",
            "pilots", "remainingCycles", "decision", *DENIED},
           "invalid extraction plan structure")
    ensure(current["schema"] ==
           "maintenance-superinteligence.cycle70-dependent-pilot-extractions.v1"
           and current["snapshotNature"] == "github_connector_snapshot_not_live"
           and current["researchBase"] == "research/cycle69-research-stack-decomposition"
           and current["decision"] == "NO GO"
           and all(current[k] is False for k in DENIED),
           "plan claims live verification, merge or operational authority")
    ensure(type(current["pilots"]) is list and len(current["pilots"]) == 2
           and [p["cycle"] for p in current["pilots"]] == [59, 61]
           and current["remainingCycles"] == [62, 63, 64, 65, 66],
           "extracted and deferred cycles must be explicit and nonduplicated")
    prev = {u["cycle"]: u for u in earlier["units"]}
    original = {e["cycle"]: e for e in inventory["inventory"]}
    ensure(all(c in prev and c in original for c in [58, 59, 60, 61]),
           "prior research inventory does not cover pilot dependencies")
    findings = []
    for p in current["pilots"]:
        cycle = p["cycle"]
        pr, base_pr, parent = EXPECTED[cycle]
        ensure(type(p) is dict and set(p) ==
               {"cycle", "pr", "head", "headSha", "base", "basePr",
                "dependencies", "draft", "merged", "sourceCycle", "paths",
                "specificCiAtSnapshot", "generalSecurityCiAtSnapshot"},
               "pilot has missing or extra metadata")
        parent_pilot = prev[parent]["pilot"]
        expected_paths = sorted(original[cycle][k] for k in ("workflow", "code", "doc", "test"))
        ensure(p["pr"] == pr and p["basePr"] == base_pr
               and p["sourceCycle"] == cycle and p["dependencies"] == [parent]
               and p["base"] == parent_pilot["branch"]
               and parent_pilot["pr"] == base_pr
               and parent_pilot["base"] == "main"
               and p["draft"] is True and p["merged"] is False,
               "dependent PR must target the correct unmerged root pilot")
        ensure(type(p["headSha"]) is str and
               re.fullmatch(r"[a-f0-9]{40}", p["headSha"])
               and p["head"] == {
                   59: "integration/cycle70-c59-observation-consistency",
                   61: "integration/cycle70-c61-metrology-context",
               }[cycle], "unrecognized dependent pilot head")
        ensure(type(p["paths"]) is list and sorted(p["paths"]) == expected_paths
               and len(p["paths"]) == 4, "pilot must modify four own files")
        ensure(p["specificCiAtSnapshot"] == "success"
               and p["generalSecurityCiAtSnapshot"] in
               ("queued", "in_progress", "success", "failure"),
               "CI metadata is a dated observation, not authorization")
        code_path = original[cycle]["code"]
        ensure(".." not in Path(code_path).parts and not code_path.startswith("/"),
               "unsafe source path")
        actual = imports(root / code_path)
        ensure(actual == [parent], "code imports differ from declared direct dependency")
        findings.append({
            "cycle": cycle, "pr": pr, "basePr": base_pr,
            "directImports": actual, "snapshotCi": p["specificCiAtSnapshot"],
            "isolatedWorkflowVerifiedLiveByThisAudit": False,
            "approvalGranted": False,
        })
    return {
        "schema": "maintenance-superinteligence.cycle70-extraction-audit-result.v1",
        "pilotCount": len(findings),
        "pilots": findings,
        "dependentPrTopologyConsistent": True,
        "snapshotNotLive": True,
        "realMechanicalValidationCompleted": False,
        "realOemEffectivityVerified": False,
        "operationalAuthorityGranted": False,
        "readyForMerge": False,
        "decision": "NO GO",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--plan", default=str(PLAN))
    parser.add_argument("--earlier", default=str(PRIOR))
    parser.add_argument("--inventory", default=str(INV))
    parser.add_argument("--output")
    args = parser.parse_args()
    result = audit(
        args.root,
        json.loads(Path(args.plan).read_text(encoding="utf-8")),
        json.loads(Path(args.earlier).read_text(encoding="utf-8")),
        json.loads(Path(args.inventory).read_text(encoding="utf-8")),
    )
    rendered = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as f:
            f.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
