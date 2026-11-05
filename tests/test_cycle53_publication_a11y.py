"""C53: append-only Pages receipt audit + static keyboard semantics (no browser claim)."""
from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path

from governance import cycle53_publication_history as c53
from governance import cycle52_publication_audit as c52
from scripts import sync_interfaces as ui


class Cycle53PublicationA11yTests(unittest.TestCase):
    def setUp(self):
        self.history=c53.load(c53.HISTORY)

    def test_two_confirmed_deploys_preserve_original_v1_unchanged(self):
        evidence=c53.verify(self.history)
        old=c52.load(c52.LEDGER)
        first=copy.deepcopy(self.history["releases"][0])
        self.assertEqual(
            first.pop("catalogSnapshot"),
            "interfaces/snapshots/c51-pages-deploy.v1.json")
        self.assertEqual(first,old["releases"][0])
        self.assertEqual([r["workflowRunId"] for r in self.history["releases"]],
                         [42052320131,42057123105])
        self.assertEqual([len(r["files"]) for r in self.history["releases"]],[2,3])
        self.assertEqual({x["path"] for x in c52.compare(evidence["v2"], ui.load())},
                         {"roadmap[marco-53]","documents[a11y53]"})
        self.assertEqual(self.history["externalStudyGatesVerified"],0)

    def test_immutable_first_receipt_and_recorded_git_blobs(self):
        for mutation in (
            lambda h: h["releases"][0].update({"sourceCommit":"f"*40}),
            lambda h: h["releases"][0].update({"workflowRunId":0}),
            lambda h: h["releases"][0]["files"][0].update({"gitBlobSha":"f"*40}),
            lambda h: h["releases"][1].update({"workflowRunId":0}),
            lambda h: h["releases"][1].update({"sourceCommit":"b"*40}),
            lambda h: h["releases"][1]["files"][2].update({"gitBlobSha":"a"*40}),
            lambda h: h["releases"].reverse(),
            lambda h: h["releases"].append(copy.deepcopy(h["releases"][1])),
        ):
            forged=copy.deepcopy(self.history)
            mutation(forged)
            with self.subTest(mutation=mutation),self.assertRaises(c53.ReleaseRejected):
                c53.verify(forged)

    def test_human_and_field_authority_cannot_be_promoted(self):
        for key in ("siteHttpIndependentlyVerified",
                    "qualifiedHumanReviewCompleted","operationalAuthorityGranted"):
            forged=copy.deepcopy(self.history)
            forged["releases"][1][key]=True
            with self.subTest(key=key),self.assertRaises(c53.ReleaseRejected):
                c53.verify(forged)
        forged=copy.deepcopy(self.history)
        forged["externalStudyGatesVerified"]=13
        with self.assertRaises(c53.ReleaseRejected):
            c53.verify(forged)
        forged=copy.deepcopy(self.history)
        forged["operationallyApproved"]=True
        with self.assertRaises(c53.ReleaseRejected):
            c53.verify(forged)

    def test_latest_portal_embeds_identical_v2_ledger_and_published_snapshot(self):
        report=c53.check()
        self.assertEqual(report["knownGithubSuccessfulDeploys"],2)
        self.assertEqual(report["recordedPublicHtmlBlobs"],5)
        self.assertTrue(report["versionsHtmlEmbeddedHistoryConsistent"])
        self.assertEqual(report["externalGatesVerified"],0)
        self.assertFalse(report["liveHttpIndependentlyVerified"])
        self.assertFalse(report["browserScreenReaderAuditCompleted"])
        self.assertFalse(report["qualifiedHumanReviewCompleted"])
        self.assertFalse(report["mayWriteSAP"])
        self.assertFalse(report["mayReleaseEquipment"])

    def test_all_three_portals_have_skip_links_visible_focus_and_reduced_motion(self):
        for html_path in ui.PORTALS:
            source=html_path.read_text(encoding="utf-8")
            with self.subTest(path=str(html_path)):
                for key in c53.REQUIRED_A11Y:
                    self.assertIn(key,source)
                self.assertIn('tabindex="-1"',source)
                self.assertIn('lang="pt-BR"',source)
                self.assertIn('name="viewport"',source)
                self.assertIn("NO GO",source)
                self.assertNotIn("fetch(",source)
                self.assertNotIn("<script src=",source)

    def test_audit_tabs_have_keyboard_control_and_accessible_relationships(self):
        s=ui.PORTALS[1].read_text(encoding="utf-8")
        for id in ("gates","prs","limites"):
            self.assertIn(f'id="tab-{id}"',s)
            self.assertIn(f'aria-controls="{id}"',s)
            self.assertIn(f'aria-labelledby="tab-{id}"',s)
        for key in ('event.key==="ArrowRight"','event.key==="ArrowLeft"',
                    'event.key==="Home"','event.key==="End"',
                    'button.focus()','t.tabIndex=active?0:-1',
                    'panel.hidden=!active'):
            self.assertIn(key,s)

    def test_versions_ui_has_public_comparison_choices_and_status_announcements(self):
        s=c53.PORTAL.read_text(encoding="utf-8")
        for key in ('id="publicationHistoryV2"','id="publishedCatalog"',
                    'id="from"','id="to"','id="download"',
                    'aria-live="polite"','id="counts"','id="changes"',
                    'historical_release_entries_are_immutable_new_confirmed_deploys_are_appended_only'):
            self.assertIn(key,s)
        self.assertIn("history.releases.map(release=>",s)
        self.assertIn("snapshots[from],snapshots[to]",s)
        self.assertIn("JSON.stringify(report,null,2)",s)

    def test_two_json_schemas_accept_real_pinned_receipts_and_deny_false_claims(self):
        try: from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("Dedicated CI installs jsonschema==4.23.0")
        for schema_file,payload in (
            ("publications-v2.schema.json",self.history),
            ("cycle53-publication-a11y.schema.json",c53.check()),
        ):
            doc=json.loads((ui.ROOT/"contracts"/schema_file).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(doc)
            validator=Draft202012Validator(doc)
            self.assertEqual(list(validator.iter_errors(payload)),[])
        schema=json.loads((ui.ROOT/"contracts/publications-v2.schema.json")
                          .read_text(encoding="utf-8"))
        validator=Draft202012Validator(schema)
        for field,value in (("operationallyApproved",True),
                            ("externalStudyGatesVerified",1)):
            forged=copy.deepcopy(self.history);forged[field]=value
            self.assertTrue(list(validator.iter_errors(forged)))
        forged=copy.deepcopy(self.history)
        forged["releases"][1]["qualifiedHumanReviewCompleted"]=True
        self.assertTrue(list(validator.iter_errors(forged)))


if __name__=="__main__":
    unittest.main()
