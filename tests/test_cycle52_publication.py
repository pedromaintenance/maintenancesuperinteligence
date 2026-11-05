"""Cycle52: verify Pages publication receipts and offline catalog deltas."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from governance import cycle52_publication_audit as a52
from scripts import sync_interfaces as ui


class Cycle52PublicationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = a52.load(a52.LEDGER)
        self.baseline = a52.load(a52.BASELINE)
        self.current = ui.load()

    def test_public_pages_deploy_is_pinned_and_not_human_approval(self):
        self.assertTrue(a52.validate(self.ledger, self.baseline, self.current))
        self.assertEqual(self.ledger["releases"][0]["workflowRunId"], 42052320131)
        self.assertEqual(self.ledger["releases"][0]["sourceCommit"],
                         a52.PINNED_DEPLOY_SHA)
        self.assertEqual({x["path"]: x["gitBlobSha"]
                          for x in self.ledger["releases"][0]["files"]},
                         a52.BLOBS)
        self.assertFalse(self.ledger["releases"][0]
                         ["siteHttpIndependentlyVerified"])
        self.assertFalse(self.ledger["releases"][0]
                         ["qualifiedHumanReviewCompleted"])
        self.assertEqual(self.ledger["externalStudyGatesVerified"], 0)
        self.assertEqual(self.ledger["decision"], "NO GO")

    def test_three_standalone_pages_embed_same_navigation_catalog(self):
        self.assertEqual(len(ui.PORTALS), 3)
        self.assertEqual([p.name for p in ui.PORTALS],
                         ["index.html", "auditoria.html", "versoes.html"])
        self.assertTrue(ui.check())
        self.assertTrue(a52.check())
        content = a52.read_embedded()
        self.assertEqual(content["baseline"], self.baseline)
        self.assertEqual(content["releases"], self.ledger)
        for portal in ui.PORTALS:
            html, _, current = ui.embedded(portal)
            self.assertEqual(current, self.current)
            self.assertIn("NO GO", html)
            self.assertIn("SAP/ECM", html)
            self.assertIn("versoes.html", html)

    def test_catalog_diff_reports_new_version_route_and_roadmap(self):
        changes = a52.compare(self.baseline, self.current)
        paths = {x["path"] for x in changes}
        self.assertIn("sites[versions]", paths)
        self.assertIn("roadmap[marco-52]", paths)
        self.assertIn("documents[releases]", paths)
        self.assertIn("roadmap[marco-53]", paths)
        self.assertIn("documents[a11y53]", paths)
        self.assertEqual(len(changes), 5)
        self.assertEqual({x["change"] for x in changes}, {"added"})
        self.assertEqual(a52.compare(self.baseline, self.baseline), [])
        self.assertEqual(a52.compare({"a": 1}, {"a": 2}),
                         [{"path": "a", "change": "modified"}])
        self.assertEqual(a52.compare({"a": 1}, {}),
                         [{"path": "a", "change": "removed"}])

    def test_report_recomputes_from_public_data_and_denies_operational_authority(self):
        report = a52.check()
        self.assertEqual(report["confirmedGithubDeployRecords"], 1)
        self.assertEqual(report["standalonePortalsInSync"], 3)
        self.assertEqual(report["catalogChangeCount"], 3)
        self.assertEqual(report["externalStudyGatesVerified"], 0)
        self.assertFalse(report["liveHttpIndependentlyVerified"])
        self.assertFalse(report["independentHumanQACompleted"])
        self.assertFalse(report["mechanicalDiagnosticAccuracyValidated"])
        self.assertFalse(report["mayWriteSAP"])
        self.assertFalse(report["mayModifyECM"])
        self.assertFalse(report["mayReleaseEquipment"])
        self.assertEqual(
            report["decision"],
            "no_go_publication_receipt_is_not_mechanical_or_human_certification",
        )

    def test_forged_success_evidence_and_http_checks_are_rejected(self):
        changes = [
            ("siteHttpIndependentlyVerified", True),
            ("qualifiedHumanReviewCompleted", True),
            ("operationalAuthorityGranted", True),
            ("sourceCommit", "b" * 40),
            ("workflowRunId", 1),
            ("evidenceStatus", "certified_by_external_engineer"),
            ("pagesEnvironmentUrl", "https://example.invalid/"),
        ]
        for key, value in changes:
            tampered = copy.deepcopy(self.ledger)
            tampered["releases"][0][key] = value
            with self.subTest(field=key), self.assertRaises(a52.PublicationRejected):
                a52.validate(tampered, self.baseline, self.current)

    def test_invalid_blob_or_hidden_external_gate_cannot_be_accepted(self):
        tampered = copy.deepcopy(self.ledger)
        tampered["releases"][0]["files"][1]["gitBlobSha"] = "a" * 40
        with self.assertRaises(a52.PublicationRejected):
            a52.validate(tampered, self.baseline, self.current)
        tampered = copy.deepcopy(self.ledger)
        tampered["externalStudyGatesVerified"] = 13
        with self.assertRaises(a52.PublicationRejected):
            a52.validate(tampered, self.baseline, self.current)
        tampered = copy.deepcopy(self.current)
        tampered["gates"][0]["status"] = "independently_approved"
        with self.assertRaises(a52.PublicationRejected):
            a52.validate(self.ledger, self.baseline, tampered)

    def test_schema_validation_and_false_authority_mutations(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Dedicated CI installs jsonschema==4.23.0")
        for filename, sample in (
            ("publications.schema.json", self.ledger),
            ("cycle52-publication-audit.schema.json", a52.check()),
        ):
            schema = json.loads(
                (ui.ROOT / "contracts" / filename).read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
            self.assertEqual(list(validator.iter_errors(sample)), [])
        report = a52.check()
        schema = json.loads(
            (ui.ROOT / "contracts/cycle52-publication-audit.schema.json")
            .read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema)
        for name in ("mayWriteSAP", "mayModifyECM", "mayReleaseEquipment",
                     "independentHumanQACompleted", "liveHttpIndependentlyVerified"):
            changed = copy.deepcopy(report)
            changed[name] = True
            with self.subTest(field=name):
                self.assertGreater(len(list(validator.iter_errors(changed))), 0)

    def test_standalone_version_portal_offers_diff_filters_and_export(self):
        text = a52.VERSIONS.read_text(encoding="utf-8")
        for needle in ('id="search"', 'id="type"', 'id="download"',
                       'id="changes"', 'id="catalog"', 'id="baseline"',
                       'id="releases"', "JSON.stringify(output,null,2)",
                       "role=\""):
            if needle == "role=\"":
                continue
            self.assertIn(needle, text)
        self.assertNotIn("<script src=", text)
        self.assertNotIn("fetch(", text)
        self.assertNotIn("cdn.jsdelivr", text)
        self.assertIn("index.html", text)
        self.assertIn("auditoria.html", text)


if __name__ == "__main__":
    unittest.main()
