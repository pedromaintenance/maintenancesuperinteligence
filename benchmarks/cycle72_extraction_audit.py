"""C72: offline audit of C63's isolated, synthetic effectivity PR.

The manifest is a dated connector snapshot. Checking it cannot authenticate
a GitHub PR, prove OEM effectivity, grant merge authority or release equipment.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "cycle72-effectivity-extraction.v1.json"
PREVIOUS = ROOT / "benchmarks" / "cycle71-reference-extraction.v1.json"
INVENTORY = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"
DENIED = ("humanReviewCompleted", "mergeAuthorized", "operationalAuthorityGranted",
          "mayWriteSap", "mayModifyEcm", "mayReleaseEquipment", "mayExecuteTest")
EXPECTED_FILES = [
    ".github/workflows/cycle63-effectivity.yml",
    "benchmarks/cycle63_effectivity.py",
    "docs/CICLO_2026-11-08_MATRIZ_APLICABILIDADE_63.md",
    "tests/test_cycle63_effectivity.py",
]
EXPECTED_TESTS = [
    "tests.test_cycle60_metrology", "tests.test_cycle61_metrology_context",
    "tests.test_cycle62_reference_semantics", "tests.test_cycle63_effectivity",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def static_dependencies(path):
    source = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = set()
    for node in ast.walk(source):
        if isinstance(node, ast.ImportFrom) and node.module:
            match = re.fullmatch(r"benchmarks\.cycle(\d+)_[a-z0-9_]+", node.module)
            if match:
                out.add(int(match.group(1)))
    return sorted(out)


def audit(root, manifest, previous, inventory):
    root = Path(root).resolve()
    require(type(manifest) is dict and set(manifest) == {
        "schema", "snapshotDate", "snapshotNature", "repository", "researchBase",
        "extraction", "remainingResearchCycles", "decision", *DENIED
    }, "invalid C72 audit manifest")
    require(manifest["schema"] ==
            "maintenance-superinteligence.cycle72-effectivity-extraction.v1"
            and manifest["snapshotNature"] == "github_connector_snapshot_not_live"
            and manifest["researchBase"] ==
            "research/cycle71-c62-isolated-extraction-audit",
            "cannot claim a verified live GitHub state")
    require(manifest["decision"] == "NO GO"
            and all(manifest[k] is False for k in DENIED),
            "approval/operation claims must remain denied")
    require(manifest["remainingResearchCycles"] == [64, 65, 66],
            "dependent future cycles cannot disappear")
    item = manifest["extraction"]
    require(type(item) is dict and set(item) == {
        "cycle", "pr", "head", "headSha", "base", "basePr", "baseCycle",
        "parentPrs", "directDependencies", "transitiveDependencies", "draft",
        "merged", "files", "isolatedTests", "specificCiAtSnapshot",
        "generalSecurityCiAtSnapshot", "dataScope", "realOemEffectivityVerified"
    }, "invalid pilot metadata")
    require(item["cycle"] == 63 and item["pr"] == 103
            and item["head"] == "integration/cycle72-c63-synthetic-effectivity"
            and type(item["headSha"]) is str
            and re.fullmatch(r"[a-f0-9]{40}", item["headSha"])
            and item["draft"] is True and item["merged"] is False,
            "C63 must remain a distinct unmerged Draft")
    prior = previous["extraction"]
    require(prior["cycle"] == 62 and prior["pr"] == 101
            and prior["draft"] is True and prior["merged"] is False
            and prior["dependencies"] == [60, 61]
            and item["base"] == prior["head"] and item["basePr"] == prior["pr"]
            and item["baseCycle"] == prior["cycle"],
            "C63 must be based directly on isolated C62")
    require(item["parentPrs"] == [96, 99, 101]
            and item["directDependencies"] == [62]
            and item["transitiveDependencies"] == [60, 61],
            "C63 effectivity requires declared C62, C61 and C60 ancestry")
    records = {r["cycle"]: r for r in inventory["inventory"]}
    rec = records[63]
    require(rec["dependencies"] == [62] and item["files"] == EXPECTED_FILES
            and EXPECTED_FILES == sorted(rec[k] for k in
                                        ("code", "test", "workflow", "doc")),
            "pilot must contain only the four C63 artifacts")
    require(item["isolatedTests"] == EXPECTED_TESTS
            and item["specificCiAtSnapshot"] == "success"
            and item["generalSecurityCiAtSnapshot"] in
            ("queued", "in_progress", "success", "failure"),
            "CI status is a declared snapshot, not a verification")
    require(item["dataScope"] == "synthetic_training_only"
            and item["realOemEffectivityVerified"] is False,
            "real equipment information and OEM claims prohibited")
    for relative in item["files"]:
        require(type(relative) is str and relative and
                not relative.startswith("/") and
                "\\" not in relative and ".." not in Path(relative).parts,
                "unsafe artifact path")
        require((root / relative).is_file(), "missing C63 source: " + relative)
    deps = static_dependencies(root / rec["code"])
    require(deps == item["directDependencies"],
            "imported code dependencies do not match isolated plan")
    workflow = (root / rec["workflow"]).read_text(encoding="utf-8")
    for event in ("push", "pull_request"):
        match = re.search(
            r"(?m)^  " + re.escape(event) +
            r":\n    paths:\n((?:      - '[^']+'\n)+)", workflow
        )
        require(match is not None, "workflow trigger missing: " + event)
        event_paths = set(re.findall(r"(?m)^      - '([^']+)'$", match.group(1)))
        for path in (rec["code"], rec["test"], records[62]["code"],
                     records[62]["test"]):
            require(path in event_paths,
                    "missing dependency trigger " + event + " " + path)
    cmd = [line.strip() for line in workflow.splitlines()
           if line.strip().startswith("run: python -m unittest ")]
    require(len(cmd) == 1 and
            cmd[0] == "run: python -m unittest " + " ".join(EXPECTED_TESTS) + " -v",
            "workflow must test only C60-C63, without prior unrelated branches")
    return {
        "schema": "maintenance-superinteligence.cycle72-extraction-audit-result.v1",
        "pilotPr": item["pr"],
        "directDependencies": deps,
        "transitiveDependencies": item["transitiveDependencies"],
        "ownFiles": len(item["files"]),
        "isolatedTests": len(EXPECTED_TESTS),
        "snapshotNotLive": True,
        "liveCIAuthenticatedByThisAudit": False,
        "realHumanReviewCompleted": False,
        "oemEffectivityVerified": False,
        "readyForMerge": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--manifest", default=str(MANIFEST))
    p.add_argument("--previous", default=str(PREVIOUS))
    p.add_argument("--inventory", default=str(INVENTORY))
    p.add_argument("--output")
    args = p.parse_args()
    receipt = audit(
        args.root,
        json.loads(Path(args.manifest).read_text(encoding="utf-8")),
        json.loads(Path(args.previous).read_text(encoding="utf-8")),
        json.loads(Path(args.inventory).read_text(encoding="utf-8")),
    )
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as target:
            target.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
