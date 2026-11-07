"""Fail-closed release-candidate and HTTP-byte smoke check for public Pages.

Cycle 54. This is a software delivery check, NOT a browser, accessibility,
human, mechanical, OEM, or operational authority attestation. No GitHub token,
credentials, third-party content, or private case evidence enters the receipt.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

PUBLIC_BASE = "https://pedromaintenance.github.io/maintenancesuperinteligence/"
SITE_NAMES = ("index.html", "auditoria.html", "versoes.html")
SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
CATALOG_RE = re.compile(
    r'<script id="catalog" type="application/json">\s*(.*?)\s*</script>',
    re.DOTALL,
)
CANDIDATE_SCHEMA = "maintenance-superinteligence.pages-release-candidate.v1"
RECEIPT_SCHEMA = "maintenance-superinteligence.pages-http-delivery-receipt.v1"
SAFETY_FLAGS = (
    "operationalAuthorityGranted", "humanExpertStudyCompleted",
    "fieldDiagnosticAccuracyMeasured", "portalHasLiveBackend",
    "aiRolesAreRunningAgents",
)


class ReleaseRejected(ValueError):
    """Release candidate or HTTP-delivered content violates the public contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseRejected(message)


def json_output(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_html(raw: bytes, expected_name: str) -> dict:
    """Validate public navigation metadata without making external claims."""
    require(expected_name in SITE_NAMES, "unapproved Pages path")
    require(len(raw) > 1024, "incomplete HTML file")
    try:
        html = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ReleaseRejected("HTML is not valid UTF-8") from exc
    lower = html.lower()
    for snippet in (
        "<!doctype html>", 'lang="pt-BR"', "NO GO", "SAP/ECM",
        'href="#main-content"', 'id="main-content"',
        "focus-visible", "prefers-reduced-motion", "versoes.html",
    ):
        require(snippet in html, expected_name + ": missing " + snippet)
    require("<script src=" not in lower and "fetch(" not in html,
            "external JavaScript or dynamic fetch not permitted in public Pages")
    matches = CATALOG_RE.findall(html)
    require(len(matches) == 1, expected_name + ": expected one catalog")
    try:
        catalog = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise ReleaseRejected("invalid embedded public catalog") from exc
    require(catalog.get("schema") ==
            "maintenance-superinteligence.interfaces-catalog.v1",
            "unexpected catalog identity")
    snapshot = catalog.get("snapshot", {})
    require(isinstance(snapshot, dict)
            and snapshot.get("externalGatesVerified") == 0
            and snapshot.get("externalGatesTotal") == 13
            and all(snapshot.get(k) is False for k in SAFETY_FLAGS),
            "catalog promotes false independent evidence or authority")
    require(catalog.get("project", {}).get("decision") == "NO GO"
            and isinstance(catalog.get("gates"), list)
            and len(catalog["gates"]) == 13
            and all(x.get("status") == "unverified_requires_external_evidence"
                    for x in catalog["gates"]),
            "public page removes safety or external study gates")
    if expected_name == "versoes.html":
        require('id="publicationHistoryV2"' in html
                and 'id="publishedCatalog"' in html,
                "historical provenance markers missing from versions portal")
    return catalog


def build_candidate(site_dir: Path, source_sha: str,
                    run_id: int, *, base_url: str = PUBLIC_BASE) -> dict:
    require(isinstance(source_sha, str)
            and SOURCE_SHA_RE.fullmatch(source_sha) is not None,
            "source commit SHA must be a 40-character Git SHA")
    require(isinstance(run_id, int) and run_id >= 1, "invalid GitHub run ID")
    require(base_url == PUBLIC_BASE, "external publication origin is not allowlisted")
    require(site_dir.is_dir(), "staged Pages directory does not exist")
    allowed = set(SITE_NAMES) | {".nojekyll"}
    actual = {p.name for p in site_dir.iterdir()}
    require(actual <= allowed and set(SITE_NAMES) <= actual,
            "Pages stage contains missing or unauthorized files")
    require(all((site_dir / n).is_file()
                and not (site_dir / n).is_symlink() for n in SITE_NAMES),
            "Pages stage contains symbolic links or nonfiles")
    files = []
    canonical_catalog = None
    for name in SITE_NAMES:
        raw = (site_dir / name).read_bytes()
        catalog = inspect_html(raw, name)
        if canonical_catalog is None:
            canonical_catalog = catalog
        else:
            require(catalog == canonical_catalog,
                    "Pages HTML files contain differing catalog versions")
        files.append({"path": name, "sha256": _sha256(raw),
                      "sizeBytes": len(raw)})
    return {
        "schema": CANDIDATE_SCHEMA,
        "sourceCommit": source_sha,
        "workflowRunId": run_id,
        "siteBase": base_url,
        "files": files,
        "contentStage": "candidate_staged_not_http_verified",
        "liveHttpBytesVerified": False,
        "browserAccessibilityVerified": False,
        "humanQualifiedReviewVerified": False,
        "mechanicalAccuracyVerified": False,
        "externalStudyGatesVerified": 0,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def validate_candidate(data: dict) -> None:
    require(isinstance(data, dict) and set(data) == {
        "schema", "sourceCommit", "workflowRunId", "siteBase", "files",
        "contentStage", "liveHttpBytesVerified", "browserAccessibilityVerified",
        "humanQualifiedReviewVerified", "mechanicalAccuracyVerified",
        "externalStudyGatesVerified", "operationalAuthorityGranted", "decision",
    }, "unexpected candidate fields")
    require(data["schema"] == CANDIDATE_SCHEMA
            and data["siteBase"] == PUBLIC_BASE
            and SOURCE_SHA_RE.fullmatch(data["sourceCommit"]) is not None
            and isinstance(data["workflowRunId"], int)
            and data["workflowRunId"] >= 1
            and data["contentStage"] == "candidate_staged_not_http_verified"
            and data["liveHttpBytesVerified"] is False
            and data["browserAccessibilityVerified"] is False
            and data["humanQualifiedReviewVerified"] is False
            and data["mechanicalAccuracyVerified"] is False
            and data["externalStudyGatesVerified"] == 0
            and data["operationalAuthorityGranted"] is False
            and data["decision"] == "NO GO",
            "candidate claims evidence not obtained by staging")
    files = data["files"]
    require(isinstance(files, list) and len(files) == 3
            and [x.get("path") for x in files] == list(SITE_NAMES),
            "unexpected Pages artifact paths or order")
    for item in files:
        require(set(item) == {"path", "sha256", "sizeBytes"}
                and isinstance(item["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None
                and type(item["sizeBytes"]) is int
                and item["sizeBytes"] > 1024,
                "incomplete or invalid staged artifact evidence")


def _allowed_remote(url: str) -> bool:
    v = urlparse(url)
    return v.scheme == "https" and v.hostname == "pedromaintenance.github.io" \
        and v.port in (None, 443) and v.username is None \
        and v.password is None \
        and v.path.startswith("/maintenancesuperinteligence/")


def verify_delivery(candidate: dict, *, attempts: int = 10,
                    delay_seconds: float = 6,
                    sleeper=time.sleep, opener=urlopen) -> dict:
    """Compare actual HTTP response bytes to staged SHA256; fail closed.

    A successful check only establishes that three HTTP responses had the
    expected bytes at verification time; it does not test a real browser.
    """
    validate_candidate(candidate)
    require(type(attempts) is int and 1 <= attempts <= 20,
            "retry count outside bounds")
    observed = []
    for item in candidate["files"]:
        url = urljoin(candidate["siteBase"], item["path"])
        # Cache-buster avoids accepting a stale edge response as current content.
        url += "?release-check=" + candidate["sourceCommit"][:12]
        require(_allowed_remote(url), "unapproved remote URL")
        failure = "no HTTP response"
        matched = False
        for attempt in range(attempts):
            try:
                request = Request(url, headers={
                    "User-Agent": "MaintenanceSuperintelligence-PagesReleaseCheck/1",
                    "Cache-Control": "no-cache",
                    "Accept-Encoding": "identity",
                })
                with opener(request, timeout=15) as response:
                    status = response.getcode()
                    final_url = response.geturl()
                    require(_allowed_remote(final_url),
                            "redirect outside allowed GitHub Pages origin")
                    raw = response.read(2_500_001)
                if status != 200:
                    failure = f"HTTP status {status}"
                elif len(raw) > 2_500_000:
                    failure = "unexpected large content"
                elif _sha256(raw) != item["sha256"]:
                    failure = "HTTP content digest differs from staged artifact"
                elif len(raw) != item["sizeBytes"]:
                    failure = "HTTP content size differs from staged artifact"
                else:
                    inspect_html(raw, item["path"])
                    matched = True
                    observed.append({
                        "path": item["path"],
                        "httpStatus": 200,
                        "sha256": item["sha256"],
                        "bytesMatched": True,
                        "sizeBytes": len(raw),
                    })
                    break
            except (OSError, ValueError, ReleaseRejected) as exc:
                failure = type(exc).__name__ + ": " + str(exc)[:200]
            if attempt < attempts - 1:
                sleeper(delay_seconds)
        require(matched, item["path"] + ": remote verification failed: " + failure)
    return {
        "schema": RECEIPT_SCHEMA,
        "sourceCommit": candidate["sourceCommit"],
        "workflowRunId": candidate["workflowRunId"],
        "siteBase": PUBLIC_BASE,
        "verifiedAtUtc": datetime.now(timezone.utc).isoformat(),
        "deliveryStatus": "three_public_http_body_digests_match_staged_artifacts",
        "files": observed,
        "liveHttpBytesVerified": True,
        "browserAccessibilityVerified": False,
        "humanQualifiedReviewVerified": False,
        "mechanicalAccuracyVerified": False,
        "externalStudyGatesVerified": 0,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate/verify public Pages release artifacts")
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("prepare")
    pre.add_argument("--site-dir", type=Path, required=True)
    pre.add_argument("--source-sha", required=True)
    pre.add_argument("--run-id", type=int, required=True)
    pre.add_argument("--output", type=Path, required=True)
    post = sub.add_parser("verify")
    post.add_argument("--candidate", type=Path, required=True)
    post.add_argument("--base-url", required=True)
    post.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = build_candidate(args.site_dir, args.source_sha, args.run_id)
    else:
        require(args.base_url.rstrip("/") + "/" == PUBLIC_BASE,
                "Pages output must match allowlisted deployment origin")
        result = verify_delivery(json.loads(args.candidate.read_text(encoding="utf-8")))
    json_output(args.output, result)
    print(json.dumps({
        "schema": result["schema"],
        "sourceCommit": result["sourceCommit"],
        "workflowRunId": result["workflowRunId"],
        "filesChecked": len(result["files"]),
        "liveHttpBytesVerified": result["liveHttpBytesVerified"],
        "humanQualifiedReviewVerified": False,
        "operationalAuthorityGranted": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
