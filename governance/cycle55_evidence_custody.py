"""C55: offline provenance custody for one real GitHub Pages HTTP receipt.

Exact archived original JSON bytes, GitHub artifact metadata, and the three
HTTP delivery digests are checked. This is a public draft Git snapshot only;
the original ZIP itself is NOT stored in Git. A passing report does not prove
continuous availability, independent human QA, equipment safety, or source
authenticity beyond the already observed GitHub Actions run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts import pages_release_gate as pages

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archives/pages/2026-11-07-run-42412015125"
INDEX = ROOT / "archives/pages/index.v1.json"
CANDIDATE = "pages-release-candidate.json"
RECEIPT = "pages-http-receipt.json"
MANIFEST = "custody-manifest.v1.json"
ORIGINAL_HASHES = {
    CANDIDATE: "9bd547dae00b6d59a9dad0c91493e9d1f399fbca0844a2757dd6f610aa02257b",
    RECEIPT: "729a14ee3f9f595223729516a76251294eded07b270d7594c5c5f8b7812cf483",
}
RUN = 42412015125
COMMIT = "b930a177cc9ba1c94c32785f8fa0b16c37723afb"
ARTIFACT_ID = 13589439429
ARTIFACT_HASH = "58b0b05a15589ddeec6f9f25cd6f57d3a7c10031300cee86734b2aa58646101b"
HTML_GIT_BLOBS = {
    "index.html": "11a8ade824affa0a96ac5be17fff673c2a122d07",
    "auditoria.html": "beff22c50d27ad116d72e9452792313828a1046d",
    "versoes.html": "90104fbb92edea753317a10d45766a0d8fa893bf",
}


class CustodyRejected(ValueError):
    """Evidence can no longer be tied to the pinned observed release."""


def require(condition: bool, message: str):
    if not condition:
        raise CustodyRejected(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_json(name: str) -> dict:
    return json.loads((ARCHIVE / name).read_text(encoding="utf-8"))


def verify():
    require(ARCHIVE.is_dir()
            and {p.name for p in ARCHIVE.iterdir()} ==
            {CANDIDATE, RECEIPT, MANIFEST}
            and not any(p.is_symlink() for p in ARCHIVE.iterdir()),
            "source archive changed, contains unknown files or symlinks")
    manifest = _read_json(MANIFEST)
    candidate = _read_json(CANDIDATE)
    receipt = _read_json(RECEIPT)

    require(set(manifest) == {
        "schema", "version", "custodyState", "source", "files",
        "publishedHtml", "evidenceScope", "liveHttpAtSourceVerified",
        "independentCurrentHttpVerified", "humanQASignOff",
        "browserScreenReaderAuditCompleted", "corporateDataApproval",
        "fieldDiagnosticAccuracyVerified", "externalStudyGatesVerified",
        "operationalAuthorityGranted", "decision",
    }, "unexpected custody manifest fields")
    require(manifest["schema"] ==
            "maintenance-superinteligence.pages-evidence-custody.v1"
            and manifest["version"] == "1.0.0"
            and manifest["custodyState"] ==
            "git_versioned_draft_not_merged_not_independently_attested"
            and manifest["evidenceScope"] ==
            "three_http_200_content_hash_matches_at_one_observed_time_not_continuous_monitoring"
            and manifest["liveHttpAtSourceVerified"] is True
            and all(manifest[k] is False for k in (
                "independentCurrentHttpVerified", "humanQASignOff",
                "browserScreenReaderAuditCompleted", "corporateDataApproval",
                "fieldDiagnosticAccuracyVerified", "operationalAuthorityGranted",
            ))
            and manifest["externalStudyGatesVerified"] == 0
            and manifest["decision"] == "NO GO",
            "archived receipt claims a false authority or changed evidence scope")

    source = manifest["source"]
    require(set(source) == {
        "repository", "workflowRunId", "workflowUrl", "commit",
        "artifactId", "artifactName", "artifactArchiveSha256",
        "artifactExpiresAtUtc", "archiveZipRetainedInGit",
        "observedFrom",
    }, "archive source fields changed")
    require(source["repository"] == "pedromaintenance/maintenancesuperinteligence"
            and source["workflowRunId"] == RUN
            and source["workflowUrl"] ==
            "https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42412015125"
            and source["commit"] == COMMIT
            and source["artifactId"] == ARTIFACT_ID
            and source["artifactName"] == "pages-release-evidence-42412015125"
            and source["artifactArchiveSha256"] == ARTIFACT_HASH
            and source["artifactExpiresAtUtc"] == "2026-12-07T20:38:33Z"
            and source["archiveZipRetainedInGit"] is False,
            "source metadata not tied to verified first HTTP receipt")

    checks = []
    require(isinstance(manifest["files"], list)
            and [x["path"] for x in manifest["files"]] ==
            [CANDIDATE, RECEIPT],
            "original file order/paths changed")
    for entry in manifest["files"]:
        require(set(entry) == {"path", "sha256", "sizeBytes"},
                "missing original file metadata")
        path = ARCHIVE / entry["path"]
        raw = path.read_bytes()
        require(entry["sha256"] == ORIGINAL_HASHES[entry["path"]]
                and sha256(raw) == ORIGINAL_HASHES[entry["path"]]
                and len(raw) == entry["sizeBytes"],
                "archived original JSON bytes were modified")
        checks.append({"file": entry["path"], "sha256": sha256(raw)})

    pages.validate_candidate(candidate)
    require(candidate["workflowRunId"] == RUN
            and candidate["sourceCommit"] == COMMIT
            and candidate["siteBase"] == pages.PUBLIC_BASE,
            "original candidate does not belong to pinned deployment")
    require(receipt["schema"] == pages.RECEIPT_SCHEMA
            and receipt["sourceCommit"] == COMMIT
            and receipt["workflowRunId"] == RUN
            and receipt["siteBase"] == pages.PUBLIC_BASE
            and receipt["verifiedAtUtc"] ==
            "2026-11-07T20:38:33.178533+00:00"
            and receipt["deliveryStatus"] ==
            "three_public_http_body_digests_match_staged_artifacts"
            and receipt["liveHttpBytesVerified"] is True
            and receipt["decision"] == "NO GO",
            "original HTTP receipt is inconsistent")
    require(all(receipt[k] is False for k in (
        "browserAccessibilityVerified", "humanQualifiedReviewVerified",
        "mechanicalAccuracyVerified", "operationalAuthorityGranted",
    )) and receipt["externalStudyGatesVerified"] == 0,
            "original receipt falsely promoted qualified/operational status")

    require(isinstance(manifest["publishedHtml"], list)
            and len(manifest["publishedHtml"]) == 3
            and len(receipt["files"]) == 3,
            "incomplete original HTTP evidence")
    for pinned, original, served in zip(
            manifest["publishedHtml"], candidate["files"], receipt["files"]):
        require(set(pinned) == {"path", "sha256", "sizeBytes", "gitBlobSha"}
                and pinned["path"] == original["path"] == served["path"]
                and pinned["sha256"] == original["sha256"] == served["sha256"]
                and pinned["sizeBytes"] == original["sizeBytes"] == served["sizeBytes"]
                and pinned["gitBlobSha"] == HTML_GIT_BLOBS[pinned["path"]]
                and served["httpStatus"] == 200
                and served["bytesMatched"] is True,
                "source commit HTML and HTTP digest disagree")

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    require(index == {
        "schema": "maintenance-superinteligence.pages-custody-index.v1",
        "version": "1.0.0",
        "evidenceType": "archived_original_json_not_original_zip",
        "entries": [{
            "runId": RUN,
            "commit": COMMIT,
            "manifest": "archives/pages/2026-11-07-run-42412015125/custody-manifest.v1.json",
            "candidate": "archives/pages/2026-11-07-run-42412015125/pages-release-candidate.json",
            "receipt": "archives/pages/2026-11-07-run-42412015125/pages-http-receipt.json",
            "custody": "draft_git_review_required_before_main",
        }],
        "externalStudyGatesVerified": 0,
        "humanReviewCompleted": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }, "custody index is inconsistent with immutable receipt")

    return {
        "schema": "maintenance-superinteligence.cycle55-custody-audit.v1",
        "runId": RUN,
        "sourceCommit": COMMIT,
        "sourceArtifactId": ARTIFACT_ID,
        "verifiedOriginalJsonFiles": 2,
        "matchedPublicHtmlFilesFromRecordedReceipt": 3,
        "originalJsonSha256Matched": True,
        "sourceZipArchiveRetained": False,
        "rechecksCurrentPagesHttp": False,
        "humanReviewCompleted": False,
        "fieldDiagnosticAccuracyValidated": False,
        "externalStudyGatesVerified": 0,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
        "files": checks,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify original public Pages evidence custody")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    require(args.check or args.output is not None, "provide --check or --output")
    result = verify()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
