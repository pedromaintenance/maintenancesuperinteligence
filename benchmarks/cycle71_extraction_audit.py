"""C71: audit a dated C62 extraction record, not a live GitHub review.

Only checks static Python imports, source paths and an author-declared PR
snapshot. Does not authenticate GitHub CI, human reviews, sources, or machines.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "cycle71-reference-extraction.v1.json"
INVENTORY = ROOT / "benchmarks" / "cycle67-consolidation-inventory.v1.json"
PRIOR = ROOT / "benchmarks" / "cycle70-dependent-pilot-extractions.v1.json"

DENIED = (
    "mergeAuthorized", "humanCodeReviewVerified",
    "independentMechanicalValidationVerified", "oemEffectivityVerified",
    "mayExecuteTest", "mayWriteSap", "mayModifyEcm",
    "mayReleaseEquipment", "operationalAuthorityGranted",
)
FILES = [
    ".github/workflows/cycle62-reference-semantics.yml",
    "benchmarks/cycle62_reference_semantics.py",
    "docs/CICLO_2026-11-08_SEMANTICA_REFERENCIAS_62.md",
    "tests/test_cycle62_reference_semantics.py",
]
TESTS = [
    "tests.test_cycle60_metrology",
    "tests.test_cycle61_metrology_context",
    "tests.test_cycle62_reference_semantics",
]


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def dependencies(file_path):
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            match = re.fullmatch(r"benchmarks\.cycle(\d+)_[a-z0-9_]+", node.module)
            if match:
                imports.add(int(match.group(1)))
    return sorted(imports)


def audit(root, manifest, inventory, prior):
    root = Path(root).resolve()
    require(type(manifest) is dict and set(manifest) ==
            {"schema", "snapshotDate", "snapshotNature", "repository",
             "researchBase", "extraction", "remainingResearchCycles",
             "decision", *DENIED}, "invalid snapshot fields")
    require(manifest["schema"] == "maintenance-superinteligence.cycle71-reference-extraction.v1"
            and manifest["snapshotNature"] ==
            "github_connector_snapshot_not_live_verification"
            and manifest["researchBase"] ==
            "research/cycle70-isolated-dependent-extractions",
            "snapshot identity or provenance invalid")
    require(manifest["decision"] == "NO GO"
            and all(manifest[k] is False for k in DENIED),
            "review or operational authority may not be promoted")
    require(manifest["remainingResearchCycles"] == [63, 64, 65, 66],
            "unopened dependencies cannot disappear from the plan")
    e = manifest["extraction"]
    fields = {
        "cycle", "pr", "base", "basePr", "baseCycle",
        "head", "headSha", "draft", "merged", "dependencies",
        "ancestorPrs", "files", "specificCiAtSnapshot",
        "generalSecurityCiAtSnapshot", "isolatedTests",
        "sourceData", "realOemSourceIncluded",
    }
    require(type(e) is dict and set(e) == fields,
            "incomplete extraction metadata")
    require(e["cycle"] == 62 and e["pr"] == 101
            and e["baseCycle"] == 61 and e["basePr"] == 99
            and e["base"] == "integration/cycle70-c61-metrology-context"
            and e["head"] == "integration/cycle71-c62-reference-semantics"
            and type(e["headSha"]) is str
            and re.fullmatch(r"[a-f0-9]{40}", e["headSha"])
            and e["draft"] is True and e["merged"] is False,
            "C62 must remain a distinct Draft PR based on C61")
    require(e["dependencies"] == [60, 61]
            and e["ancestorPrs"] == [96, 99],
            "C62 must declare both upstream code dependencies")
    previous = {p["cycle"]: p for p in prior["pilots"]}
    require(previous[61]["pr"] == 99
            and previous[61]["basePr"] == 96
            and previous[61]["head"] == e["base"]
            and previous[61]["dependencies"] == [60]
            and previous[61]["draft"] is True
            and previous[61]["merged"] is False,
            "C61 branch provenance incompatible with C62 pilot")
    lookup = {c["cycle"]: c for c in inventory["inventory"]}
    expected = lookup[62]
    require(expected["dependencies"] == [60, 61]
            and e["files"] == FILES
            and FILES == sorted(expected[x] for x in
                                ("code", "test", "workflow", "doc")),
            "four-file scope does not match historical source inventory")
    require(e["isolatedTests"] == TESTS
            and e["specificCiAtSnapshot"] == "success"
            and e["generalSecurityCiAtSnapshot"] in
            ("queued", "in_progress", "success", "failure"),
            "test suite or dated CI metadata invalid")
    require(e["sourceData"] == "synthetic_training_only"
            and e["realOemSourceIncluded"] is False,
            "only fictional public training data permitted")
    for rel in FILES:
        require(type(rel) is str and ".." not in Path(rel).parts
                and not rel.startswith("/") and "\\" not in rel,
                "unsafe source path")
        require((root / rel).is_file(), "missing research artifact " + rel)
    imports = dependencies(root / expected["code"])
    require(imports == e["dependencies"],
            "code imports and declared upstream modules disagree")
    return {
        "schema": "maintenance-superinteligence.cycle71-extraction-audit-result.v1",
        "pilotPr": e["pr"],
        "directDependencies": imports,
        "changedFiles": len(FILES),
        "snapshotNotLive": True,
        "liveCIAuthenticatedByThisAudit": False,
        "humanReviewCompleted": False,
        "readyForMerge": False,
        "oemEffectivityVerified": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--manifest", default=str(MANIFEST))
    parser.add_argument("--inventory", default=str(INVENTORY))
    parser.add_argument("--prior", default=str(PRIOR))
    parser.add_argument("--output")
    a = parser.parse_args()
    output = audit(
        a.root,
        json.loads(Path(a.manifest).read_text(encoding="utf-8")),
        json.loads(Path(a.inventory).read_text(encoding="utf-8")),
        json.loads(Path(a.prior).read_text(encoding="utf-8")),
    )
    rendered = json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if a.output:
        with Path(a.output).open("x", encoding="utf-8") as destination:
            destination.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
