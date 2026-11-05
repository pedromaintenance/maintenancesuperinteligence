"""Cycle 52: public, offline GitHub Pages publication provenance + catalog diff.

This checks pinned public GitHub metadata observed on 2026-11-05, not
current HTTP availability, author identity, GitHub API status or the accuracy
of any mechanical claim. Git blob identifiers are *not* signatures.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from scripts import sync_interfaces as ui

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "interfaces/publications.v1.json"
BASELINE = ROOT / "interfaces/snapshots/c51-pages-deploy.v1.json"
VERSIONS = ROOT / "portal/versoes.html"
PINNED_DEPLOY_SHA = "ad9a9b3e321dfe696a8a816e5cdc17637f9f0afc"
RUN = 42052320131
BLOBS = {
    "index.html": "c8b9efcf6bb1f697cfe6667e33c2aedcba532bcd",
    "auditoria.html": "145a7f9a34198631708f35512f3c1cea66ac52ee",
}
SITE = "https://pedromaintenance.github.io/maintenancesuperinteligence/"
RAW = re.compile(
    r'<script id="(?P<name>baseline|releases)" '
    r'type="application/json">\s*(?P<json>.*?)\s*</script>',
    re.DOTALL,
)
DENIALS = (
    "siteHttpIndependentlyVerified",
    "qualifiedHumanReviewCompleted",
    "operationalAuthorityGranted",
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(ok, message):
    if not ok:
        raise PublicationRejected(message)


class PublicationRejected(ValueError):
    """The public release receipt or a derived snapshot is stale or forged."""


def validate(ledger, past, current):
    require(isinstance(ledger, dict)
            and set(ledger) == {
                "schema", "version", "frozenAt", "evidenceNature",
                "canonicalSource", "baselineCatalog", "siteBase",
                "releases", "currentViewer", "restrictedEvidenceIncluded",
                "externalStudyGatesVerified", "operationallyApproved",
                "decision",
            }, "publication ledger structure changed")
    require(ledger["schema"] ==
            "maintenance-superinteligence.publication-history.v1"
            and ledger["version"] == "1.0.0"
            and ledger["frozenAt"] == "2026-11-05"
            and ledger["evidenceNature"] ==
            "github_actions_success_and_repository_blobs_not_live_http_or_human_approval"
            and ledger["canonicalSource"] == "interfaces/catalog.v1.json"
            and ledger["baselineCatalog"] ==
            "interfaces/snapshots/c51-pages-deploy.v1.json"
            and ledger["siteBase"] == SITE
            and ledger["restrictedEvidenceIncluded"] is False
            and ledger["externalStudyGatesVerified"] == 0
            and ledger["operationallyApproved"] is False
            and ledger["decision"] == "NO GO",
            "external study evidence or operational authority overstated")
    releases = ledger["releases"]
    require(isinstance(releases, list) and len(releases) == 1,
            "historic snapshot must contain only one confirmed release")
    release = releases[0]
    require(release["id"] == "PAGES-2026-11-05-001"
            and release["cycle"] == 51
            and release["publicationDateUtc"] == "2026-11-05T15:11:13Z"
            and release["sourceBranch"] == "main"
            and release["sourceCommit"] == PINNED_DEPLOY_SHA
            and release["workflowRunId"] == RUN
            and release["workflowRunUrl"] ==
            "https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/" + str(RUN)
            and release["deploymentWorkflow"] ==
            "Publish Maintenance Superintelligence portals to GitHub Pages"
            and release["pagesEnvironmentUrl"] == SITE
            and release["evidenceStatus"] == "github_actions_reported_success"
            and all(release[k] is False for k in DENIALS),
            "deployment record promoted or mismatched with GitHub snapshot")
    require(isinstance(release["files"], list)
            and len(release["files"]) == 2
            and {x["path"]: x["gitBlobSha"] for x in release["files"]} == BLOBS
            and all(x["nature"] == "standalone_public_html"
                    for x in release["files"]),
            "published file Git blob identifier changed")
    viewer = ledger["currentViewer"]
    require(viewer == {
        "label": "Visualização da branch em análise",
        "claim": "embedded_catalog_as_rendered_not_a_live_github_snapshot",
        "approvedForOperations": False,
        "independentEngineeringValidation": False,
    }, "viewer claims live authority")

    require(past["schema"] ==
            "maintenance-superinteligence.interfaces-catalog.v1"
            and past["snapshot"]["date"] == "2026-11-05"
            and past["snapshot"]["externalGatesVerified"] == 0
            and past["snapshot"]["operationalAuthorityGranted"] is False
            and len(past["sites"]) == 2
            and [x["id"] for x in past["sites"]] ==
                ["overview", "audit"],
            "baseline does not match published Cycle 51 snapshot")
    require(current["snapshot"] == past["snapshot"]
            and current["project"] == past["project"]
            and current["gates"] == past["gates"]
            and current["prs"] == past["prs"],
            "release metadata must not silently revise historical authority")
    require([x["id"] for x in current["sites"]] ==
            ["overview", "audit", "versions"],
            "versions portal missing from latest catalog")
    require("Ciclo 52" in (ROOT / "docs/ROADMAP.md").read_text(
        encoding="utf-8"), "roadmap did not record provenance milestone")
    return True


def _keyed(sequence):
    return all(isinstance(x, dict)
               and (isinstance(x.get("id"), str)
                    or isinstance(x.get("number"), int))
               for x in sequence)


def compare(original, revised, path=""):
    """Return public JSON *navigation* changes, not source/document diffs."""
    rows = []
    if isinstance(original, list) and isinstance(revised, list):
        if _keyed(original) and _keyed(revised):
            key = lambda x: str(x.get("id", x.get("number")))
            left = {key(x): x for x in original}
            right = {key(x): x for x in revised}
            for ident in sorted(set(left) | set(right)):
                rows.extend(compare(left.get(ident), right.get(ident),
                                    path + "[" + ident + "]"))
        else:
            for i in range(max(len(original), len(revised))):
                rows.extend(compare(
                    original[i] if i < len(original) else None,
                    revised[i] if i < len(revised) else None,
                    path + "[" + str(i) + "]",
                ))
        return rows
    if isinstance(original, dict) and isinstance(revised, dict):
        for key in sorted(set(original) | set(revised)):
            rows.extend(compare(original.get(key), revised.get(key),
                                (path + "." if path else "") + key))
        return rows
    if original != revised:
        category = ("added" if original is None else
                    "removed" if revised is None else "modified")
        rows.append({"path": path, "change": category})
    return rows


def read_embedded():
    html = VERSIONS.read_text(encoding="utf-8")
    data = {}
    for match in RAW.finditer(html):
        require(match.group("name") not in data,
                "duplicated versioned publication record in HTML")
        data[match.group("name")] = json.loads(match.group("json"))
    require(set(data) == {"baseline", "releases"},
            "publication HTML must embed exactly one baseline and ledger")
    return data


def check():
    # Explicitly validate the C51 three-page shared navigation first.
    ui.check()
    previous, current, ledger = load(BASELINE), ui.load(), load(LEDGER)
    validate(ledger, previous, current)
    embedded = read_embedded()
    require(embedded["baseline"] == previous and
            embedded["releases"] == ledger,
            "versions portal has stale embedded publication history")
    require("NO GO" in VERSIONS.read_text(encoding="utf-8")
            and "SAP/ECM" in VERSIONS.read_text(encoding="utf-8"),
            "publication page hides essential limits")
    diff = compare(previous, current)
    require(len(diff) >= 3
            and {"sites[versions]", "roadmap[marco-52]",
                 "documents[releases]"}.issubset({x["path"] for x in diff}),
            "expected new navigation/roadmap provenance entries absent")
    return {
        "schema": "maintenance-superinteligence.cycle52-publication-audit.v1",
        "version": "1.0.0",
        "evidenceNature": ledger["evidenceNature"],
        "baselineDeployRunId": RUN,
        "baselineSourceCommit": PINNED_DEPLOY_SHA,
        "confirmedGithubDeployRecords": 1,
        "historicalPublishedFiles": len(BLOBS),
        "standalonePortalsInSync": 3,
        "catalogChangeCount": len(diff),
        "catalogChangedPaths": diff,
        "externalStudyGatesVerified": 0,
        "liveHttpIndependentlyVerified": False,
        "independentHumanQACompleted": False,
        "mechanicalDiagnosticAccuracyValidated": False,
        "mayWriteSAP": False,
        "mayModifyECM": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_publication_receipt_is_not_mechanical_or_human_certification",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify offline Pages release provenance")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    require(args.check or args.output is not None,
            "provide --check or --output")
    result = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)
                               + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
