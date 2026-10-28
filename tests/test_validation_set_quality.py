"""Cycle 31: synthetic validation-set QA, split leakage and abstention tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from benchmarks.validation_set_quality import (
    ROOT, MANIFEST, POLICY, audit, validate_manifest, validate_policy,
    verify_report, render_html, tokens, main,
)
from pilot.change_review_packets import ReviewRejected


class Cycle31DatasetQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.policy=json.loads(POLICY.read_text(encoding="utf-8"))

    def test_complete_synthetic_split_and_mechanism_coverage(self):
        report=audit(self.manifest,self.policy)
        self.assertTrue(verify_report(report,self.manifest,self.policy))
        self.assertTrue(report["qualityPreflightPassed"])
        self.assertEqual(report["caseCount"],26)
        self.assertEqual(report["splits"],{"train":8,"dev":4,"test":14})
        self.assertEqual(report["testUnsupportedCount"],2)
        self.assertEqual(len(report["testHypothesisTagCoverage"]),4)
        for domain, tags in report["testHypothesisTagCoverage"].items():
            self.assertEqual(len(tags),3)
            self.assertTrue(all(v==1 for v in tags.values()))
        self.assertEqual(report["testSourceQualityChallengeCount"],
                         {"contradictory":4,"revoked":4,"unverified":2})
        self.assertEqual(report["criticalFindingCount"],0)
        self.assertEqual(report["majorFindingCount"],0)
        self.assertEqual(report["findings"],[])
        self.assertFalse(report["blindnessOrRealNoveltyEstablished"])
        self.assertFalse(report["realCaseDiagnosticsVerified"])
        self.assertFalse(report["independentExpertValidationCompleted"])
        self.assertFalse(report["mayApproveOperationalUse"])
        self.assertEqual(report["decision"],
                         "synthetic_quality_pass_not_diagnostic_validation")

    def test_cross_split_reused_lineage_source_group_evidence(self):
        for field,code in (
            ("incidentLineage","lineage_reused_cross_split"),
            ("sourceGroup","source_group_reused_cross_split"),
            ("evidenceRef","evidence_reused_cross_split")
        ):
            changed=copy.deepcopy(self.manifest)
            changed["records"][15][field]=changed["records"][0][field]
            report=audit(changed,self.policy)
            with self.subTest(field=field):
                self.assertFalse(report["qualityPreflightPassed"])
                self.assertIn(code,[f["code"] for f in report["findings"]])
                self.assertEqual(report["decision"],"quality_gate_rejected_no_go")

    def test_exact_near_and_intra_split_duplicate_detection(self):
        original=self.manifest["records"][0]["syntheticNarrative"]
        for destination,variation,code in (
            (15,original,"exact_narrative_cross_split"),
            (15,original+" extra","near_narrative_cross_split"),
            (1,original,"duplicate_record_within_split"),
        ):
            changed=copy.deepcopy(self.manifest)
            changed["records"][destination]["syntheticNarrative"]=variation
            report=audit(changed,self.policy)
            with self.subTest(destination=destination,code=code):
                self.assertFalse(report["qualityPreflightPassed"])
                self.assertIn(code,[f["code"] for f in report["findings"]])
        self.assertEqual(tokens("vibração no ROLAMENTO"),
                         tokens("VIBRACAO no rolamento"))

    def test_missing_critical_coverage_and_exclusion(self):
        for field,value,code in [
            ("split","train","missing_mechanism_tag_test"),
            ("sourceReliability","documented_synthetic",
             "missing_source_reliability_test")
        ]:
            changed=copy.deepcopy(self.manifest)
            if field=="split":
                # All cases for one tested mechanism are removed from test.
                # Keep supported hypothetical mechanism tags in the other splits.
                for r in changed["records"]:
                    if r["split"]=="test" and r["mechanismTag"]=="bearing_damage":
                        r["split"]=value
            else:
                # This version needs the reason updated consistently.
                for r in changed["records"]:
                    if r["split"]=="test" and r["sourceReliability"]=="revoked":
                        r["sourceReliability"]=value
                        r["abstentionReason"]="no_physical_confirmation"
            report=audit(changed,self.policy)
            with self.subTest(field=field):
                self.assertFalse(report["qualityPreflightPassed"])
                self.assertIn(code,[x["code"] for x in report["findings"]])
        changed=copy.deepcopy(self.manifest)
        changed["records"]=changed["records"][:-2]
        report=audit(changed,self.policy)
        self.assertIn("missing_unsupported_test",
                      [x["code"] for x in report["findings"]])

    def test_unsafe_claims_or_misclassified_hypothesis_fail_structurally(self):
        mutations=[
            (0,"physicalEvidenceCollected",True),
            (1,"causalMechanismConfirmed",True),
            (2,"oemApplicabilityVerified",True),
            (3,"mayCreateWorkOrder",True),
            (4,"mayReleaseEquipment",True),
            (5,"abstentionRequired",False),
            (6,"mechanismTag","approved_bearing_failure"),
            (7,"abstentionReason","domain_unsupported"),
            (8,"sourceReliability","verified_oem"),
        ]
        for index,key,value in mutations:
            changed=copy.deepcopy(self.manifest)
            changed["records"][index][key]=value
            with self.subTest(case=index,key=key),self.assertRaises(ReviewRejected):
                validate_manifest(changed,self.policy)

    def test_rubric_cannot_be_promoted_to_independent_evidence(self):
        for key,value in (
            ("independentReviewCompleted",True),
            ("realWorldAccuracyMeasured",True),
            ("mayApproveOperationalUse",True),
        ):
            changed=copy.deepcopy(self.policy)
            changed[key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_policy(changed)

    def test_digest_report_rejects_forgery_and_source_change(self):
        report=audit(self.manifest,self.policy)
        modified=copy.deepcopy(report)
        modified["mayReleaseEquipment"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(modified,self.manifest,self.policy)
        different=copy.deepcopy(self.manifest)
        different["records"][0]["syntheticNarrative"]+=" variante alterada"
        with self.assertRaises(ReviewRejected):
            verify_report(report,different,self.policy)

    def test_cli_is_fail_closed_and_privacy_boundary(self):
        with tempfile.TemporaryDirectory(prefix="cycle31-") as tmp:
            public=Path(tmp)/"public-demo.json"
            main(["--output",str(public)])
            report=json.loads(public.read_text())
            self.assertTrue(report["qualityPreflightPassed"])
            self.assertNotIn("Exercício documental",public.read_text())
            private=Path(tmp)/"private-manifest.json"
            private.write_text(json.dumps(self.manifest))
            out=Path(tmp)/"private-result.json"
            main(["--manifest",str(private),"--output",str(out)])
            self.assertTrue(out.exists())
        with tempfile.TemporaryDirectory(prefix="cycle31-") as tmp:
            private=Path(tmp)/"synthetic.json"
            private.write_text(json.dumps(self.manifest))
            # Private input cannot cause output inside checkout.
            with self.assertRaises(ValueError):
                main(["--manifest",str(private),
                      "--output",str(ROOT/"build"/"accidental-private.json")])

    def test_html_and_contracts(self):
        html=render_html(audit(self.manifest,self.policy))
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        for name in ("validation-quality-manifest.schema.json",
                     "validation-quality-policy.schema.json",
                     "validation-quality-report.schema.json"):
            schema=json.loads((ROOT/"contracts"/name).read_text())
            self.assertEqual(schema["$schema"],
                             "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
