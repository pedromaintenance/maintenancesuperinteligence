"""Cycle 33: adversarial checks for traceable technical background vs diagnosis."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
from knowledge.mechanical_evidence import (
    ROOT, MAP_PATH, POLICY_PATH, FAMILIES, TRUSTED_HOSTS,
    validate_map, check_policy, evaluate, verify_report, render_html,
)
from pilot.change_review_packets import ReviewRejected

class TechnicalEvidenceMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(MAP_PATH.read_text(encoding="utf-8"))
        cls.policy=json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_12_traces_6_linked_sources_and_unconfirmed_mechanisms(self):
        result=evaluate(self.data,self.policy)
        self.assertTrue(verify_report(result,self.data,self.policy))
        self.assertEqual(result["recordCount"],12)
        self.assertEqual(result["sourceCount"],7)
        self.assertEqual(result["linkedSourceCount"],6)
        self.assertEqual(result["domains"],{x:3 for x in FAMILIES})
        self.assertEqual(result["physicalMechanismCandidates"],9)
        self.assertEqual(result["diagnosticInterpretationConfounders"],3)
        self.assertEqual(result["realPhysicalFailureCasesReviewed"],0)
        self.assertFalse(result["independentlyExpertValidated"])
        self.assertFalse(result["oemSerialEffectivityValidated"])
        self.assertFalse(result["realDiagnosticAccuracyEstablished"])
        self.assertFalse(result["mayApproveTest"])
        self.assertFalse(result["mayCreateWorkOrder"])
        self.assertFalse(result["mayReleaseEquipment"])
        self.assertEqual(result["decision"],"technical_reference_only_no_go")
        for r in self.data["records"]:
            self.assertFalse(r["rootCauseConfirmed"])
            self.assertFalse(r["measurementsPerformed"])
            self.assertFalse(r["oemEffectivityVerified"])
            self.assertFalse(r["permissionToTest"])
            self.assertFalse(r["permissionToCreateWorkOrder"])
            self.assertFalse(r["permissionToReleaseMachine"])
            self.assertGreaterEqual(len(r["sourceIds"]),1)
            self.assertTrue(r["alternativeExplanation"])
            self.assertTrue(r["nextDiscriminatingQuestion"])

    def test_confuser_cannot_be_reclassified_as_damage(self):
        for index in (0,6,8):
            m=copy.deepcopy(self.data)
            m["records"][index]["branchType"]="physical_mechanism_candidate"
            with self.subTest(index=index),self.assertRaises(ReviewRejected):
                validate_map(m,self.policy)

    def test_no_source_cannot_be_passed_off_as_evidence(self):
        for field,value in [
            ("sourceIds",[]),
            ("sourceIds",["OEM-SECRET-PROPRIETARY"]),
            ("sourceIds",["CAT-SOS-READ","CAT-SOS-READ"]),
            ("supportType","direct_oem_serial_validation"),
            ("informationState","confirmed_in_field"),
            ("contextGate","not_applicable_to_system"),
        ]:
            m=copy.deepcopy(self.data)
            m["records"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_map(m,self.policy)

    def test_trusted_public_reference_is_not_any_link(self):
        for value in [
            "http://www.cat.com/guidance",
            "https://malicious.example.com/approved-rules",
            "https://www.cat.com@malicious.example.com/test",
            "file:///tmp/secret-manual",
        ]:
            m=copy.deepcopy(self.data)
            m["sourceCatalog"][0]["url"]=value
            with self.subTest(url=value),self.assertRaises(ReviewRejected):
                validate_map(m,self.policy)
        m=copy.deepcopy(self.data)
        m["sourceCatalog"][0]["notSupported"]=""
        with self.assertRaises(ReviewRejected):
            validate_map(m,self.policy)

    def test_never_allow_claims_to_become_oem_approved(self):
        for field in [
            "rootCauseConfirmed","measurementsPerformed",
            "oemEffectivityVerified","expertReviewCompleted","permissionToTest",
            "permissionToCreateWorkOrder","permissionToReleaseMachine",
        ]:
            m=copy.deepcopy(self.data)
            m["records"][1][field]=True
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_map(m,self.policy)
        for field in [
            "realDataIncluded","oemSeriesEffectivityEstablished",
            "externalReviewCompleted","operationallyApproved",
        ]:
            m=copy.deepcopy(self.data)
            m[field]=True
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_map(m,self.policy)

    def test_policy_does_not_certify_diagnostic_validity(self):
        for field in [
            "externalTechnicalReviewCompleted","validationAgainstFieldCases",
            "mayApproveRepair","mayApproveTest","mayReleaseEquipment",
        ]:
            p=copy.deepcopy(self.policy)
            p[field]=True
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                check_policy(p)
        p=copy.deepcopy(self.policy)
        p["minimumRecordsByDomain"]=2
        with self.assertRaises(ReviewRejected):
            check_policy(p)

    def test_report_hard_fails_on_forged_or_changed_source(self):
        original=evaluate(self.data,self.policy)
        changed=copy.deepcopy(original)
        changed["realDiagnosticAccuracyEstablished"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(changed,self.data,self.policy)
        changed=copy.deepcopy(self.data)
        changed["records"][3]["nextDiscriminatingQuestion"]+=" nova alternativa documental"
        with self.assertRaises(ReviewRejected):
            verify_report(original,changed,self.policy)

    def test_html_offline_no_untrusted_diagnostic_controls(self):
        html=render_html(self.data,evaluate(self.data,self.policy))
        self.assertEqual(html.count("<article>"),12)
        self.assertNotIn("<script",html.lower())
        self.assertNotIn("<form",html.lower())
        self.assertIn("não diagnósticos",html)
        self.assertIn("https://",html)
        self.assertNotIn("private",html)
        for s in self.data["sourceCatalog"]:
            from urllib.parse import urlparse
            self.assertIn(urlparse(s["url"]).hostname,TRUSTED_HOSTS)

    def test_three_json_schemas_exist(self):
        for name in (
            "mechanical-evidence-map.schema.json",
            "mechanical-evidence-policy.schema.json",
            "mechanical-evidence-report.schema.json",
        ):
            obj=json.loads((ROOT/"contracts"/name).read_text(encoding="utf-8"))
            self.assertEqual(obj["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(obj["additionalProperties"])

if __name__=="__main__":
    unittest.main()
