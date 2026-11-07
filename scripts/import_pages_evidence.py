"""C55: safely import a Pages evidence ZIP for human-reviewed Git custody.

The operator MUST obtain expected digest, run ID, commit, artifact ID, expiry,
and Git blob SHAs independently from GitHub. This tool checks the ZIP
contents against the supplied expectations; it cannot certify that the
operator-supplied values correspond to GitHub or confer human approval.
It never runs Git commands or pushes to any branch. The exact source ZIP
is also preserved so its digest remains independently checkable later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from scripts import pages_release_gate as page

FILES = ("pages-release-candidate.json", "pages-http-receipt.json")
PATHS = ("index.html", "auditoria.html", "versoes.html")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ImportRejected(ValueError):
    pass


def require(condition, explanation):
    if not condition:
        raise ImportRejected(explanation)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def extract(zip_bytes):
    require(len(zip_bytes) < 10_000_000, "archive exceeds safe 10MB bound")
    require(zipfile.is_zipfile(__import__("io").BytesIO(zip_bytes)),
            "not a valid ZIP")
    with zipfile.ZipFile(__import__("io").BytesIO(zip_bytes)) as z:
        infos = z.infolist()
        require(len(infos) == 2 and [i.filename for i in infos] == list(FILES),
                "unexpected paths or files in source ZIP")
        for item in infos:
            mode = (item.external_attr >> 16) & 0o170000
            require(not item.is_dir() and mode != 0o120000
                    and item.file_size < 80_000
                    and item.compress_size < 80_000,
                    "symbolic links and oversized archive members are denied")
        return {i.filename: z.read(i) for i in infos}


def validate_pair(data, commit, run):
    raw_candidate = data[FILES[0]]
    raw_receipt = data[FILES[1]]
    candidate = json.loads(raw_candidate.decode("utf-8"))
    receipt = json.loads(raw_receipt.decode("utf-8"))
    page.validate_candidate(candidate)
    require(candidate["sourceCommit"] == commit
            and candidate["workflowRunId"] == run
            and candidate["siteBase"] == page.PUBLIC_BASE,
            "candidate is not tied to provided run and commit")
    require(receipt["schema"] == page.RECEIPT_SCHEMA
            and receipt["sourceCommit"] == commit
            and receipt["workflowRunId"] == run
            and receipt["siteBase"] == page.PUBLIC_BASE
            and receipt["deliveryStatus"] ==
                "three_public_http_body_digests_match_staged_artifacts"
            and receipt["liveHttpBytesVerified"] is True
            and receipt["decision"] == "NO GO"
            and receipt["externalStudyGatesVerified"] == 0
            and all(receipt.get(field) is False for field in (
                "browserAccessibilityVerified", "humanQualifiedReviewVerified",
                "mechanicalAccuracyVerified", "operationalAuthorityGranted",
            )), "receipt claims forbidden human or physical authorization")
    require([x["path"] for x in receipt["files"]] == list(PATHS),
            "HTTP receipt has incomplete or unknown Pages resources")
    for local, remote in zip(candidate["files"], receipt["files"]):
        require(local["path"] == remote["path"]
                and local["sha256"] == remote["sha256"]
                and local["sizeBytes"] == remote["sizeBytes"]
                and remote["httpStatus"] == 200
                and remote["bytesMatched"] is True,
                "HTTP receipt does not match staged file")
    return candidate, receipt


def prepare(*, archive: Path, archive_sha256: str, commit: str, run_id: int,
            artifact_id: int, expires_at: str, blobs: dict,
            output_dir: Path) -> dict:
    require(HEX64.fullmatch(archive_sha256 or "") is not None,
            "provide full GitHub artifact ZIP SHA-256")
    require(HEX40.fullmatch(commit or "") is not None
            and type(run_id) is int and run_id > 0
            and type(artifact_id) is int and artifact_id > 0,
            "provide verified commit/run/artifact identification")
    require(isinstance(expires_at, str)
            and expires_at.endswith("Z") and len(expires_at) == 20,
            "supply GitHub artifact expiry timestamp in UTC")
    require(isinstance(blobs, dict) and set(blobs) == set(PATHS)
            and all(HEX40.fullmatch(x) for x in blobs.values()),
            "provide three Git blob SHAs obtained from the source commit")
    require(not output_dir.exists(), "refusing to overwrite an archive folder")
    source_zip = archive.read_bytes()
    require(sha256(source_zip) == archive_sha256,
            "ZIP SHA-256 differs from operator-provided GitHub artifact digest")
    data = extract(source_zip)
    candidate, receipt = validate_pair(data, commit, run_id)
    parts = [
        {**x, "gitBlobSha": blobs[x["path"]]}
        for x in candidate["files"]
    ]
    manifest = {
        "schema": "maintenance-superinteligence.pages-evidence-custody.v1",
        "version": "1.0.0",
        "custodyState": "git_versioned_draft_not_merged_not_independently_attested",
        "source": {
            "repository": "pedromaintenance/maintenancesuperinteligence",
            "workflowRunId": run_id,
            "workflowUrl":
                "https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/" + str(run_id),
            "commit": commit,
            "artifactId": artifact_id,
            "artifactName": "pages-release-evidence-" + str(run_id),
            "artifactArchiveSha256": archive_sha256,
            "artifactExpiresAtUtc": expires_at,
            "archiveZipRetainedInGit": True,
            "archiveZipFile": "source-artifact.zip",
            "archiveZipGitBlobSha": git_blob_sha(source_zip),
            "observedFrom": "Operator-supplied GitHub artifact URL/digest/blobs; check source independently before PR acceptance",
        },
        "files": [
            {"path": name, "sha256": sha256(data[name]),
             "sizeBytes": len(data[name])} for name in FILES
        ],
        "publishedHtml": parts,
        "evidenceScope":
            "three_http_200_content_hash_matches_at_one_observed_time_not_continuous_monitoring",
        "liveHttpAtSourceVerified": True,
        "independentCurrentHttpVerified": False,
        "humanQASignOff": False,
        "browserScreenReaderAuditCompleted": False,
        "corporateDataApproval": False,
        "fieldDiagnosticAccuracyVerified": False,
        "externalStudyGatesVerified": 0,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }
    output_dir.mkdir(parents=True)
    (output_dir / "source-artifact.zip").write_bytes(source_zip)
    for name in FILES:
        (output_dir / name).write_bytes(data[name])
    (output_dir / "custody-manifest.v1.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv=None):
    p = argparse.ArgumentParser(description="Import only public GitHub Pages release evidence")
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--archive-sha256", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--artifact-id", type=int, required=True)
    p.add_argument("--expires-at", required=True)
    p.add_argument("--git-blob", action="append", nargs=2,
                   metavar=("HTML_PATH", "GIT_BLOB_SHA"), required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args(argv)
    blob_pairs = args.git_blob
    require(len(blob_pairs) == 3, "exactly three Git blobs required")
    blob_map = dict(blob_pairs)
    require(len(blob_map) == 3, "duplicate Git blob path")
    result = prepare(
        archive=args.archive,
        archive_sha256=args.archive_sha256,
        commit=args.commit, run_id=args.run_id, artifact_id=args.artifact_id,
        expires_at=args.expires_at, blobs=blob_map,
        output_dir=args.output_dir,
    )
    print(json.dumps({
        "runId": args.run_id, "sourceCommit": args.commit,
        "originalJsonFilesArchived": len(result["files"]),
        "humanQASignOff": False, "decision": "NO GO",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
