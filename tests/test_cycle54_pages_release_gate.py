"""Cycle 54: reproduce release byte checks without contacting real public site."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse

from scripts import pages_release_gate as gate


class FakeHTTP:
    def __init__(self, raw, url, status=200):
        self.raw, self.url, self.status = raw, url, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return self.raw[:size]

    def getcode(self):
        return self.status

    def geturl(self):
        return self.url


class PagesReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.pages = {
            name: (cls.root / "portal" / name).read_bytes()
            for name in gate.SITE_NAMES
        }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.site = Path(self.tmp.name) / "_site"
        self.site.mkdir()
        for name, raw in self.pages.items():
            (self.site / name).write_bytes(raw)
        (self.site / ".nojekyll").touch()

    def prepare(self):
        return gate.build_candidate(self.site, "a" * 40, 12345)

    def test_candidate_contains_only_public_html_hashes_and_explicit_no_go(self):
        candidate = self.prepare()
        gate.validate_candidate(candidate)
        self.assertEqual([x["path"] for x in candidate["files"]],
                         list(gate.SITE_NAMES))
        self.assertTrue(all(len(x["sha256"]) == 64
                            for x in candidate["files"]))
        self.assertTrue(all(x["sizeBytes"] > 1024
                            for x in candidate["files"]))
        self.assertFalse(candidate["liveHttpBytesVerified"])
        self.assertFalse(candidate["browserAccessibilityVerified"])
        self.assertFalse(candidate["humanQualifiedReviewVerified"])
        self.assertFalse(candidate["operationalAuthorityGranted"])
        self.assertEqual(candidate["externalStudyGatesVerified"], 0)
        self.assertEqual(candidate["decision"], "NO GO")
        self.assertNotIn("contents", candidate)
        self.assertNotIn("token", str(candidate).lower())

    def test_http_200_byte_match_only_is_delivery_evidence_not_human_certification(self):
        candidate = self.prepare()
        visited = []

        def opener(request, timeout):
            name = Path(urlparse(request.full_url).path).name
            self.assertEqual(timeout, 15)
            visited.append(name)
            return FakeHTTP(self.pages[name], request.full_url)

        receipt = gate.verify_delivery(candidate, attempts=1, opener=opener)
        self.assertEqual(visited, list(gate.SITE_NAMES))
        self.assertEqual(receipt["sourceCommit"], "a" * 40)
        self.assertEqual(receipt["workflowRunId"], 12345)
        self.assertTrue(receipt["liveHttpBytesVerified"])
        self.assertEqual(receipt["deliveryStatus"],
                         "three_public_http_body_digests_match_staged_artifacts")
        self.assertEqual([x["httpStatus"] for x in receipt["files"]],
                         [200, 200, 200])
        for field in ("browserAccessibilityVerified",
                      "humanQualifiedReviewVerified",
                      "mechanicalAccuracyVerified",
                      "operationalAuthorityGranted"):
            self.assertIs(receipt[field], False)
        self.assertEqual(receipt["decision"], "NO GO")

    def test_wrong_http_bytes_404_and_redirect_outside_origin_fail_closed(self):
        candidate = self.prepare()

        def wrong_bytes(request, timeout):
            name = Path(urlparse(request.full_url).path).name
            return FakeHTTP(self.pages[name] + b"adulteration",
                            request.full_url)

        def error_status(request, timeout):
            name = Path(urlparse(request.full_url).path).name
            return FakeHTTP(self.pages[name], request.full_url, 404)

        def unsafe_redirect(request, timeout):
            name = Path(urlparse(request.full_url).path).name
            return FakeHTTP(self.pages[name],
                            "https://example.org/redirected")

        for opener in (wrong_bytes, error_status, unsafe_redirect):
            with self.subTest(opener=opener), self.assertRaises(gate.ReleaseRejected):
                gate.verify_delivery(candidate, attempts=1, opener=opener)

    def test_missing_or_unlisted_files_and_forged_candidate_fail_closed(self):
        (self.site / "credentials.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(gate.ReleaseRejected):
            self.prepare()
        (self.site / "credentials.json").unlink()
        candidate = self.prepare()
        for key, value in (
            ("liveHttpBytesVerified", True),
            ("operationalAuthorityGranted", True),
            ("externalStudyGatesVerified", 13),
            ("humanQualifiedReviewVerified", True),
            ("sourceCommit", "invalid"),
            ("siteBase", "https://example.org/"),
        ):
            forged = copy.deepcopy(candidate)
            forged[key] = value
            with self.subTest(field=key), self.assertRaises(gate.ReleaseRejected):
                gate.validate_candidate(forged)
        (self.site / "auditoria.html").unlink()
        with self.assertRaises(gate.ReleaseRejected):
            self.prepare()

    def test_tampered_embedded_gates_or_external_js_fail_before_deploy(self):
        source = self.pages["index.html"]
        for before, after in (
            (b"NO GO OPERACIONAL", b"GO   OPERACIONAL"),
            (b"prefers-reduced-motion", b"no-motion-support"),
            (b'"externalGatesVerified":0', b'"externalGatesVerified":1'),
        ):
            # The embedded catalog is compact JSON in source; mutations should
            # be effective. If exact text changes, update this test intentionally.
            self.assertIn(before, source)
            (self.site / "index.html").write_bytes(source.replace(before, after, 1))
            with self.subTest(mutation=before), self.assertRaises(gate.ReleaseRejected):
                self.prepare()
            (self.site / "index.html").write_bytes(source)
        (self.site / "index.html").write_bytes(
            source.replace(b"</head>", b'<script src="https://example.org/bad.js"></script></head>', 1)
        )
        with self.assertRaises(gate.ReleaseRejected):
            self.prepare()

    def test_manifest_schema_and_receipt_schema_reject_false_authority(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Dedicated CI pins jsonschema==4.23.0")
        candidate = self.prepare()
        receipt = gate.verify_delivery(
            candidate, attempts=1,
            opener=lambda req, timeout: FakeHTTP(
                self.pages[Path(urlparse(req.full_url).path).name],
                req.full_url,
            ),
        )
        for path, payload in (
            ("pages-release-candidate.schema.json", candidate),
            ("pages-http-receipt.schema.json", receipt),
        ):
            schema = json.loads(
                (self.root / "contracts" / path).read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            self.assertEqual(
                list(Draft202012Validator(schema).iter_errors(payload)), []
            )
        schema = json.loads(
            (self.root / "contracts/pages-http-receipt.schema.json")
            .read_text(encoding="utf-8")
        )
        receipt["humanQualifiedReviewVerified"] = True
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(receipt)))


if __name__ == "__main__":
    unittest.main()
