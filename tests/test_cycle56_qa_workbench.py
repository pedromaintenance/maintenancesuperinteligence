"""C56 QA template and offline evidence intake — no simulated human completion."""
from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path

from governance import cycle56_qa_workbench as qa

class Cycle56WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.template=qa.load(qa.TEMPLATE)
        self.schema=qa.load(qa.SCHEMA)

    def test_eight_original_checks_are_all_unexecuted_and_no_go(self):
        report=qa.check()
        self.assertEqual(report["qaChecksAvailable"],8)
        self.assertEqual(report["humanChecksActuallyExecuted"],0)
        self.assertTrue(report["offlineTemplateIdentical"])
        self.assertFalse(report["qualifiedHumanSignoff"])
        self.assertFalse(report["browserAccessibilityVerified"])
        self.assertFalse(report["operationalAuthorityGranted"])
        self.assertEqual(report["externalStudyGatesVerified"],0)
        self.assertEqual(report["decision"],"NO GO")

    def test_template_modified_to_claim_review_is_rejected(self):
        for key in ("humanReviewCompleted","operationalAuthorityGranted",
                    "mechanicalDiagnosticAccuracyValidated",
                    "humanReviewerIdentityCollectedHere"):
            bad=copy.deepcopy(self.template)
            bad[key]=True
            with self.subTest(key=key),self.assertRaises(qa.QAGateRejected):
                qa.validate_template(bad)

    def test_original_checklists_cannot_be_preapproved_or_reordered(self):
        for mutation in ("passed","removed","reordered","evidence"):
            bad=copy.deepcopy(self.template)
            if mutation=="passed":bad["checks"][0]["status"]="passed"
            if mutation=="removed":bad["checks"].pop()
            if mutation=="reordered":bad["checks"].reverse()
            if mutation=="evidence":bad["checks"][0]["evidenceReference"]="fake"
            with self.subTest(mutation=mutation),self.assertRaises(qa.QAGateRejected):
                qa.validate_template(bad)

    def test_workbench_html_is_standalone_and_has_data_controls(self):
        text=qa.WORKBENCH.read_text(encoding="utf-8")
        for key in ('id="qa-template"','id="import"','id="export"',
                    'id="reset"','id="file"','id="platform"','id="release"',
                    'id="tests"','id="metrics"','id="interpretation"',
                    "NO GO OPERACIONAL",'id="content"','aria-live="polite"',
                    "prefers-reduced-motion","validateImport(doc)",
                    "JSON.stringify(state,null,2)"):
            self.assertIn(key,text)
        for banned in ("fetch(","localStorage","XMLHttpRequest",
                       "<script src=","<link rel=\"stylesheet\" href="):
            self.assertNotIn(banned,text)
        self.assertTrue(qa.check()["staticJsAndMarkupContractsChecked"])

    def test_partial_reports_can_be_saved_but_never_signed_off_by_schema(self):
        from jsonschema import Draft202012Validator
        validator=Draft202012Validator(self.schema)
        self.assertTrue(validator.is_valid(self.template))
        partial=copy.deepcopy(self.template)
        partial["observedPlatform"]="Firefox Windows - laboratório"
        partial["reviewedRelease"]="b930a177cc9ba1c94c32785f8fa0b16c37723afb"
        partial["checks"][0].update(status="failed",observations="Barra sobreposta em 320px",evidenceReference="issue-1")
        self.assertTrue(validator.is_valid(partial))
        for field in ("humanReviewCompleted","operationalAuthorityGranted","mechanicalDiagnosticAccuracyValidated"):
            forged=copy.deepcopy(partial)
            forged[field]=True
            with self.subTest(field=field):
                self.assertFalse(validator.is_valid(forged))
        forged=copy.deepcopy(partial)
        forged["decision"]="GO"
        self.assertFalse(validator.is_valid(forged))
        forged=copy.deepcopy(partial)
        forged["checks"][0]["id"]="wrong"
        self.assertFalse(validator.is_valid(forged))

    def test_no_web_or_human_check_was_performed_by_ci(self):
        report=qa.check()
        self.assertEqual(report["humanChecksActuallyExecuted"],0)
        self.assertFalse(report["browserAccessibilityVerified"])
        self.assertFalse(report["qualifiedHumanSignoff"])

if __name__=="__main__":
    unittest.main()
