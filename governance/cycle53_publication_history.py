"""Cycle 53: append-only public Pages receipt evidence and offline A11y checks.

No HTTP network calls are made; 'success' is grounded in GitHub runs
observed on 2026-11-05. A Git blob ID is not a signature. Future releases
must add independently checked pins through code review before promotion.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

from scripts import sync_interfaces as ui
from governance import cycle52_publication_audit as c52

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/"interfaces/publications.v2.json"
SECOND_SNAPSHOT=ROOT/"interfaces/snapshots/c52-pages-deploy.v1.json"
PORTAL=ROOT/"portal/versoes.html"
SITE="https://pedromaintenance.github.io/maintenancesuperinteligence/"
SECOND={
    "id":"PAGES-2026-11-05-002",
    "cycle":52,
    "publicationDateUtc":"2026-11-05T15:42:42Z",
    "sourceBranch":"main",
    "sourceCommit":"1ffa398b8d328a1f67dd49fbff7e37c3f0b82911",
    "workflowRunId":42057123105,
    "workflowRunUrl":"https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42057123105",
    "pagesEnvironmentUrl":SITE,
    "catalogSnapshot":"interfaces/snapshots/c52-pages-deploy.v1.json",
}
SECOND_BLOBS={
    "index.html":"ac92d08ed80901e1433bc7cb49dfee5f5ed3be91",
    "auditoria.html":"db9f0d21b6fe0f17f84bd56223610080619bf921",
    "versoes.html":"1bc2c0f3951ef25a9203d0a66faf8165ad7bee74",
}
JSON_SCRIPT=re.compile(
    r'<script id="(?P<id>publicationHistoryV2|publishedCatalog)" '
    r'type="application/json">\s*(?P<body>.*?)\s*</script>',
    re.DOTALL,
)
REQUIRED_A11Y=("class=\"skip-link\"","href=\"#main-content\"",
                "id=\"main-content\"","focus-visible",
                "prefers-reduced-motion")


class ReleaseRejected(ValueError):
    """The versioned evidence ledger or public presentation is inconsistent."""


def require(ok,reason):
    if not ok: raise ReleaseRejected(reason)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify(history=None):
    old=load(c52.LEDGER)
    previous=load(c52.BASELINE)
    second=load(SECOND_SNAPSHOT)
    current=ui.load()
    if history is None:history=load(HISTORY)
    c52.validate(old,previous,current)
    require(second==current,
            "published second snapshot must match the versioned Cycle52 catalog")
    require(second["snapshot"]==previous["snapshot"]
            and second["gates"]==previous["gates"]
            and second["project"]==previous["project"]
            and len(second["sites"])==3,
            "second public snapshot falsely promoted authority")
    require(isinstance(history,dict) and set(history)=={
        "schema","version","frozenAt","evidenceNature","supersedes",
        "canonicalSource","siteBase","appendPolicy","releases",
        "restrictedEvidenceIncluded","externalStudyGatesVerified",
        "operationallyApproved","decision"},
        "unexpected root fields in public release ledger")
    require(
        history["schema"]=="maintenance-superinteligence.publication-history.v2"
        and history["version"]=="2.0.0"
        and history["frozenAt"]=="2026-11-05"
        and history["evidenceNature"]==
            "observed_github_actions_deploy_receipts_and_git_blobs_not_independent_site_or_mechanical_attestation"
        and history["supersedes"]=="interfaces/publications.v1.json"
        and history["canonicalSource"]=="interfaces/catalog.v1.json"
        and history["siteBase"]==SITE
        and history["appendPolicy"]==
            "historical_release_entries_are_immutable_new_confirmed_deploys_are_appended_only"
        and history["restrictedEvidenceIncluded"] is False
        and history["externalStudyGatesVerified"]==0
        and history["operationallyApproved"] is False
        and history["decision"]=="NO GO",
        "ledger changed evidence status or claimed operational approval")
    rows=history["releases"]
    require(isinstance(rows,list) and len(rows)==2,
            "two observed releases are pinned; future releases require reviewed evidence")
    # Preserve all historical data byte-for-value except the v2 snapshot pointer.
    old_first=rows[0].copy()
    require(old_first.pop("catalogSnapshot",None)==
                "interfaces/snapshots/c51-pages-deploy.v1.json"
            and old_first==old["releases"][0],
            "append-only contract violated: first Pages receipt was rewritten")
    second_row=rows[1]
    require(isinstance(second_row,dict)
            and all(second_row.get(k)==v for k,v in SECOND.items()),
            "second deployment does not match verified GitHub run")
    require(second_row.get("deploymentWorkflow")==
            "Publish Maintenance Superintelligence portals to GitHub Pages"
            and second_row.get("evidenceStatus")=="github_actions_reported_success"
            and all(second_row.get(k) is False for k in
                ("siteHttpIndependentlyVerified",
                 "qualifiedHumanReviewCompleted","operationalAuthorityGranted")),
            "second deployment wrongly attested")
    files=second_row.get("files")
    require(isinstance(files,list)
            and len(files)==3
            and {x.get("path"):x.get("gitBlobSha") for x in files}==SECOND_BLOBS
            and all(x.get("nature")=="standalone_public_html" for x in files),
            "second published content differs from GitHub's known blobs")
    require(rows[0]["workflowRunId"]<rows[1]["workflowRunId"]
            and rows[0]["publicationDateUtc"]<rows[1]["publicationDateUtc"]
            and len({x["id"] for x in rows})==2,
            "release chronology is duplicated or reordered")
    return {"v1":previous,"v2":second,"history":history}


def _inline(html):
    blocks={}
    for m in JSON_SCRIPT.finditer(html):
        name=m.group("id")
        require(name not in blocks,"duplicated embedded JSON evidence")
        blocks[name]=json.loads(m.group("body"))
    require(set(blocks)=={"publicationHistoryV2","publishedCatalog"},
            "missing one of two static v2 history inputs")
    return blocks


def check():
    evidence=verify()
    ui.check()
    c52.check()
    html=PORTAL.read_text(encoding="utf-8")
    blocks=_inline(html)
    require(blocks["publicationHistoryV2"]==evidence["history"]
            and blocks["publishedCatalog"]==evidence["v2"],
            "versions HTML is not synchronized with public v2 receipts")
    for path in ui.PORTALS:
        page=path.read_text(encoding="utf-8")
        require(all(snippet in page for snippet in REQUIRED_A11Y),
                path.name+": keyboard navigation/focus/reduced-motion contract missing")
        require("NO GO" in page and "SAP/ECM" in page
                and "versoes.html" in page,
                path.name+": missing safety or version navigation")
    require('aria-controls="gates"' in (ROOT/"portal/auditoria.html").read_text(encoding="utf-8")
            and 'aria-selected=' in (ROOT/"portal/auditoria.html").read_text(encoding="utf-8"),
            "audit tabs lack accessible selection semantics")
    diff=c52.compare(evidence["v1"],evidence["v2"])
    require(len(diff)==3, "historical release difference changed")
    return {
        "schema":"maintenance-superinteligence.cycle53-publication-a11y-audit.v1",
        "version":"1.0.0",
        "knownGithubSuccessfulDeploys":2,
        "recordedPublicHtmlBlobs":5,
        "versionsHtmlEmbeddedHistoryConsistent":True,
        "staticKeyboardSemanticsChecked":True,
        "browserScreenReaderAuditCompleted":False,
        "liveHttpIndependentlyVerified":False,
        "qualifiedHumanReviewCompleted":False,
        "externalGatesVerified":0,
        "mayWriteSAP":False,"mayModifyECM":False,
        "mayCreateWorkOrder":False,"mayReleaseEquipment":False,
        "decision":"no_go_static_a11y_checks_are_not_human_or_mechanical_validation",
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description="Offline append-only Pages history audit")
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args(argv)
    require(args.check or args.output is not None,"provide --check or --output")
    report=check()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report


if __name__=="__main__":main()
