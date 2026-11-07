"""C55: real archived JSON bytes, custody pinning, and future ZIP importer."""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from governance import cycle55_evidence_custody as custody
from scripts import import_pages_evidence as importer
from scripts import pages_release_gate as pages


class Cycle55EvidenceCustodyTests(unittest.TestCase):
    def test_archived_original_jsons_match_observed_artifact_digests(self):
        report = custody.verify()
        self.assertEqual(report["sourceCommit"], custody.COMMIT)
        self.assertEqual(report["runId"], custody.RUN)
        self.assertEqual(report["sourceArtifactId"], custody.ARTIFACT_ID)
        self.assertEqual(report["verifiedOriginalJsonFiles"], 2)
        self.assertEqual(report["matchedPublicHtmlFilesFromRecordedReceipt"], 3)
        self.assertTrue(report["originalJsonSha256Matched"])
        self.assertTrue(report["sourceZipArchiveRetained"])
        self.assertTrue(report["sourceZipSha256Matched"])
        self.assertEqual(hashlib.sha256((custody.ARCHIVE / "source-artifact.zip").read_bytes()).hexdigest(), custody.ARTIFACT_HASH)
        self.assertFalse(report["rechecksCurrentPagesHttp"])
        self.assertFalse(report["humanReviewCompleted"])
        self.assertFalse(report["operationalAuthorityGranted"])
        self.assertEqual(report["externalStudyGatesVerified"], 0)
        self.assertEqual(report["decision"], "NO GO")
        for path, expected in custody.ORIGINAL_HASHES.items():
            self.assertEqual(
                hashlib.sha256((custody.ARCHIVE / path).read_bytes()).hexdigest(),
                expected,
            )

    def test_modifications_to_original_json_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for file in custody.ARCHIVE.iterdir():
                shutil.copy2(file, root / file.name)
            with patch.object(custody, "ARCHIVE", root):
                self.assertEqual(custody.verify()["verifiedOriginalJsonFiles"], 2)
                file = root / custody.RECEIPT
                original = file.read_bytes()
                file.write_bytes(original.replace(b'"NO GO"', b'"GO"'))
                with self.assertRaises(custody.CustodyRejected):
                    custody.verify()

    def test_false_source_artifact_id_and_authority_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for file in custody.ARCHIVE.iterdir():
                shutil.copy2(file, root / file.name)
            with patch.object(custody, "ARCHIVE", root):
                path = root / custody.MANIFEST
                manifest = json.loads(path.read_text(encoding="utf-8"))
                for key, value in (
                    ("artifactId", 1),
                    ("artifactArchiveSha256", "0" * 64),
                    ("commit", "0" * 40),
                ):
                    forged = copy.deepcopy(manifest)
                    forged["source"][key] = value
                    path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
                    with self.subTest(sourceField=key), self.assertRaises(
                            custody.CustodyRejected):
                        custody.verify()
                for key in ("operationalAuthorityGranted", "humanQASignOff",
                            "independentCurrentHttpVerified", "corporateDataApproval"):
                    forged = copy.deepcopy(manifest)
                    forged[key] = True
                    path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
                    with self.subTest(authorityField=key), self.assertRaises(
                            custody.CustodyRejected):
                        custody.verify()

    def test_future_zip_import_preserves_exact_json_bytes_and_never_pushes(self):
        candidate = (custody.ARCHIVE / custody.CANDIDATE).read_bytes()
        receipt = (custody.ARCHIVE / custody.RECEIPT).read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "artifact.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr(importer.FILES[0], candidate)
                z.writestr(importer.FILES[1], receipt)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            output = root / "new-archive"
            manifest = importer.prepare(
                archive=archive, archive_sha256=digest,
                commit=custody.COMMIT, run_id=custody.RUN,
                artifact_id=custody.ARTIFACT_ID,
                expires_at="2026-12-07T20:38:33Z",
                blobs=custody.HTML_GIT_BLOBS,
                output_dir=output,
            )
            self.assertEqual((output / importer.FILES[0]).read_bytes(), candidate)
            self.assertEqual((output / importer.FILES[1]).read_bytes(), receipt)
            self.assertFalse(manifest["humanQASignOff"])
            self.assertFalse(manifest["operationalAuthorityGranted"])
            self.assertFalse(manifest["source"]["archiveZipRetainedInGit"])
            self.assertEqual(manifest["decision"], "NO GO")
            with self.assertRaises(importer.ImportRejected):
                importer.prepare(
                    archive=archive, archive_sha256=digest,
                    commit=custody.COMMIT, run_id=custody.RUN,
                    artifact_id=custody.ARTIFACT_ID,
                    expires_at="2026-12-07T20:38:33Z",
                    blobs=custody.HTML_GIT_BLOBS, output_dir=output,
                )

    def test_future_import_rejects_false_archive_digest_and_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "fake.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr(importer.FILES[0],
                           (custody.ARCHIVE / custody.CANDIDATE).read_bytes())
                z.writestr("../attack.json", "oops")
            with self.assertRaises(importer.ImportRejected):
                importer.extract(path.read_bytes())
            with self.assertRaises(importer.ImportRejected):
                importer.prepare(
                    archive=path, archive_sha256="0" * 64,
                    commit=custody.COMMIT, run_id=custody.RUN,
                    artifact_id=custody.ARTIFACT_ID,
                    expires_at="2026-12-07T20:38:33Z",
                    blobs=custody.HTML_GIT_BLOBS,
                    output_dir=root / "output",
                )

    def test_archived_candidate_and_receipt_do_not_grant_independent_authority(self):
        c = json.loads((custody.ARCHIVE / custody.CANDIDATE).read_text())
        r = json.loads((custody.ARCHIVE / custody.RECEIPT).read_text())
        pages.validate_candidate(c)
        self.assertFalse(c["liveHttpBytesVerified"])
        self.assertTrue(r["liveHttpBytesVerified"])
        for field in ("humanQualifiedReviewVerified",
                      "browserAccessibilityVerified",
                      "mechanicalAccuracyVerified",
                      "operationalAuthorityGranted"):
            self.assertFalse(c[field])
            self.assertFalse(r[field])
        self.assertEqual(c["externalStudyGatesVerified"], 0)
        self.assertEqual(r["externalStudyGatesVerified"], 0)


if __name__ == "__main__":
    unittest.main()
