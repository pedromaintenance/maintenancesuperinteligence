"""C57: structural safeguards; real behavior is tested by Chromium in CI."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
NODE=ROOT/"tests/browser_cycle57.mjs"
SCHEMA=ROOT/"contracts/cycle57-browser-report.schema.json"
WORKFLOW=ROOT/".github/workflows/cycle57-browser-tests.yml"
PORTALS=[ROOT/"review/qa_portais_56.html",*[ROOT/"portal"/p for p in
         ("index.html","auditoria.html","versoes.html")]]

class BrowserContractTests(unittest.TestCase):
    def test_real_browser_harness_and_offline_surfaces_declared(self):
        source=NODE.read_text(encoding="utf-8")
        workflow=WORKFLOW.read_text(encoding="utf-8")
        for snippet in (
            'from "playwright"', "await chromium.launch({headless:true})",
            "page.waitForEvent(\"download\")", "setInputFiles",
            "await p.keyboard.press(\"ArrowRight\")",
            "await p.keyboard.press(\"Home\")",
            "await p.keyboard.press(\"End\")",
            "testViewport", # not a function; adapt below if needed
        ):
            if snippet=="testViewport":snippet="checkViewport("
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,source)
        for snippet in ("npx playwright install --with-deps chromium",
                        "node tests/browser_cycle57.mjs",
                        "playwright@1.56.1",
                        "if: always()",
                        "operationalAuthorityGranted"):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,workflow)
        self.assertIn('await page.route(/^https?:\\/\\//',source)
        self.assertIn("actualHumanQAExecutions:0",source)
        self.assertIn("screenReaderAudited:false",source)
        self.assertIn('decision:"NO GO"',source)

    def test_all_four_local_htmls_have_visible_no_go_and_no_external_js(self):
        for path in PORTALS:
            content=path.read_text(encoding="utf-8")
            with self.subTest(path=str(path)):
                self.assertIn("NO GO",content)
                self.assertNotIn("<script src=",content)
                self.assertNotIn("fetch(",content)
                self.assertIn("prefers-reduced-motion",content)

    def test_browser_success_schema_cannot_certify_humans(self):
        schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
        fields=schema["properties"]
        self.assertEqual(fields["actualHumanQAExecutions"]["const"],0)
        self.assertEqual(fields["WCAGConformanceCertified"]["const"],False)
        self.assertEqual(fields["screenReaderAudited"]["const"],False)
        self.assertEqual(fields["mechanicalReliabilityValidated"]["const"],False)
        self.assertEqual(fields["SAPWriteAuthorized"]["const"],False)
        self.assertEqual(fields["operationalAuthorityGranted"]["const"],False)
        self.assertEqual(fields["externalStudyGatesVerified"]["const"],0)
        self.assertEqual(fields["decision"]["const"],"NO GO")
        self.assertEqual(fields["failedBrowserScenarios"]["const"],0)
        self.assertEqual(fields["executedBrowserScenarios"]["const"],9)
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            return
        Draft202012Validator.check_schema(schema)
        forged={
            name: prop["const"] for name,prop in fields.items() if "const" in prop
        }
        forged.update({
            "testedLocalOfflineHtmlFiles":[x["const"] for x in fields["testedLocalOfflineHtmlFiles"]["prefixItems"]],
            "responsiveWidthsCssPx":[x["const"] for x in fields["responsiveWidthsCssPx"]["prefixItems"]],
            "screenshots":[x["const"] for x in fields["screenshots"]["prefixItems"]],
            "results":[{"name":x["properties"]["name"]["const"],"passed":True,"detail":""}
                       for x in fields["results"]["prefixItems"]],
        })
        validator=Draft202012Validator(schema)
        self.assertTrue(validator.is_valid(forged))
        forged["actualHumanQAExecutions"]=8
        self.assertFalse(validator.is_valid(forged))

if __name__=="__main__":
    unittest.main()
