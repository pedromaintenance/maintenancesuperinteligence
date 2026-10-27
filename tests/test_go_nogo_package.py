"""Ciclo 20: no-go contract, dependency graph, confidentiality and provenance."""
import copy
import json
import unittest
from unittest.mock import patch
from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as original_catalog
from casefiles.integrated import load_dependencies, build_collection
from notifications.drafts import SPEC_PATH, build_notifications
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as quality_report
from editorial.review_protocol import FIXTURE_PATH as EDITORIAL_FIXTURE, build_report as editorial_report
from pilot.readiness import FIXTURE_PATH as READINESS_FIXTURE, build_report as readiness_report
from pilot.go_nogo import PACKAGE_PATH, build_report, validate_package, render_html, verify_report

class GoNoGoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,reg,snapshot:original_catalog(cat,reg)):
            cls.deps=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).deps)
        self.package=json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))

    def readiness(self):
        f=json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text())
        raw=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        fake={"caseId":raw["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":x["hypothesisId"]}
                            for x in self.deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],"conflicts":[],"knowledgeGaps":[]}
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=fake)):
            cases=build_collection(f,self.deps,self.snapshot)
        notes=build_notifications(json.loads(SPEC_PATH.read_text()),
                                  cases["cases"],cases["investigationTrees"])
        quality=quality_report(notes,cases,json.loads(RUBRIC_PATH.read_text()),
                               json.loads(ORACLE_PATH.read_text()))
        editorial=editorial_report(json.loads(EDITORIAL_FIXTURE.read_text()),
                                  quality,notes)
        return readiness_report(json.loads(READINESS_FIXTURE.read_text()),editorial)

    def reject(self):
        with self.assertRaises(ImportRejected):
            build_report(self.package,self.readiness())

    def report(self):
        return build_report(self.package,self.readiness())

    def test_go_nogo_all_requirements_blocked(self):
        r=self.report()
        self.assertEqual(r["decision"],"no_go")
        self.assertEqual(r["requirementsPhase"],"requirements_defined")
        self.assertEqual(r["evidenceState"],"evidence_not_submitted")
        self.assertEqual(r["externalReviewState"],"externally_review_pending")
        self.assertEqual(r["evidencePackageCount"],13)
        self.assertEqual(r["verifiedEvidenceCount"],0)
        self.assertEqual(r["stakeholderCount"],5)
        self.assertEqual(r["verifiedSignoffs"],0)
        self.assertEqual(r["findingCount"],10)
        self.assertEqual(r["verifiedRemediations"],0)
        self.assertFalse(r["realPilotExecuted"])
        self.assertFalse(r["realGoDecisionSigned"])
        self.assertFalse(r["expertAgreementMeasured"])
        self.assertTrue(all(x is False for x in r["noOperationalAuthority"].values()))
        self.assertTrue(all(x is False for x in r["acceptanceGates"].values()))

    def test_dependency_mapping_exact_and_no_go_by_owner(self):
        r=self.report()
        self.assertEqual(len(r["approvalDependencies"]),13)
        self.assertEqual(r["dependencyCount"],13)
        self.assertEqual(r["approvalDependencies"][3]["predecessors"],
                         ["competence","conflict-screen","version-lock"])
        self.assertEqual(r["approvalDependencies"][-1]["predecessors"],
                         ["signed-decision","trusted-audit","oem-effectivity"])
        for item in r["stakeholderReviews"]:
            self.assertEqual(item["outcome"],"no_go")
            self.assertIsNone(item["reviewProof"])
            self.assertFalse(item["signedAcceptance"])
            self.assertFalse(item["verifiedReviewer"])

    def test_no_evidence_data_ever_exported(self):
        for row in self.report()["evidenceManifest"]:
            self.assertIsNone(row["evidenceBytes"])
            self.assertIsNone(row["evidenceReference"])
            self.assertFalse(row["authenticatedSubmitterVerified"])
            self.assertFalse(row["oemSeriesEffectivityVerified"])

    def test_all_ten_adversarial_threats_need_remediation(self):
        for row in self.report()["findingRemediations"]:
            self.assertEqual(row["remediationStatus"],"not_started")
            self.assertFalse(row["verifiedClosure"])
            self.assertFalse(row["mayLiftBlock"])
            self.assertIsNone(row["assignedPerson"])

    def test_retention_requires_external_signoff(self):
        self.assertEqual([c["dataClass"] for c in self.report()["classification"]],
                         ["public-synthetic","corporate-private","oem-licensed"])
        self.assertTrue(all(c["retentionDays"] is None
                            and c["retentionApproved"] is False
                            for c in self.report()["classification"]))

    def test_no_inter_rater_statistics_fabricated(self):
        p=self.report()["studyProtocol"]
        self.assertEqual(p["scope"],"future_private_authorized_study_only")
        self.assertTrue(all(v is False for k,v in p.items() if k!="scope"))

    def test_reject_fabricated_go_state(self):
        self.package["transitionPolicy"]["current"]="go"
        self.reject()

    def test_reject_fake_pilot_go_live(self):
        self.package["transitionPolicy"]["realGoLivePermitted"]=True
        self.reject()

    def test_reject_fabricated_external_evidence(self):
        self.package["controlPlan"][0]["evidenceUri"]="https://private.example.com/secret"
        self.reject()

    def test_reject_forged_reviewer_acceptance(self):
        self.package["controlPlan"][0]["independentAcceptanceRecorded"]=True
        self.reject()

    def test_reject_fake_oem_signature(self):
        self.package["controlPlan"][6]["evidenceSha256"]="0"*64
        self.reject()

    def test_reject_missing_oem_dependency(self):
        self.package["controlPlan"][6]["dependsOn"]=[]
        self.reject()

    def test_reject_duplicate_dependency(self):
        self.package["controlPlan"][3]["dependsOn"]=["competence","competence","version-lock"]
        self.reject()

    def test_reject_unassigned_owner(self):
        self.package["controlPlan"][6]["owner"]="Legal"
        self.reject()

    def test_reject_suppressed_control(self):
        self.package["controlPlan"].pop()
        self.reject()

    def test_reject_fake_it_signoff(self):
        self.package["workstreams"][0]["signoffVerified"]=True
        self.reject()

    def test_reject_omitted_juridical_gate(self):
        self.package["workstreams"]=[x for x in self.package["workstreams"]
                                     if x["owner"]!="Legal"]
        self.reject()

    def test_reject_sap_authorization(self):
        self.package["operationalAuthority"]["mayWriteSap"]=True
        self.reject()

    def test_reject_ecm_authorization(self):
        self.package["operationalAuthority"]["mayChangeEcm"]=True
        self.reject()

    def test_reject_confidential_import(self):
        self.package["realEvidenceImported"]=True
        self.reject()

    def test_reject_private_retention_period_without_approval(self):
        self.package["retentionClassification"][1]["retentionDays"]=365
        self.reject()

    def test_reject_false_study_agreement(self):
        self.package["studyDesign"]["nominalKappaMeasured"]=True
        self.reject()

    def test_reject_false_study_consent(self):
        self.package["studyDesign"]["legalBasisAndParticipantInformationApproved"]=True
        self.reject()

    def test_reject_threat_nonconformance_suppression(self):
        self.package["scenarios"][6]["expectedOutcome"]="go"
        self.reject()

    def test_reject_real_user_name_in_remediation(self):
        self.package["scenarios"][0]["assignedPerson"]="real.person"
        self.reject()

    def test_reject_unknown_secret(self):
        self.package["operationalAuthority"]["secret"]="never"
        self.reject()

    def test_reject_bogus_upstream_readiness(self):
        r=self.readiness()
        r["realPilotAuthorized"]=True
        with self.assertRaises(ImportRejected):
            build_report(self.package,r)

    def test_verify_report_recomputes_full_payload(self):
        ready=self.readiness()
        r=build_report(self.package,ready)
        self.assertEqual(verify_report(r,self.package,ready),r)
        r["approvalDependencies"][0]["permissionToProceed"]=True
        with self.assertRaises(ImportRejected):
            verify_report(r,self.package,ready)

    def test_html_static_and_escape_unsafe_text(self):
        r=self.report()
        html=render_html(r)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("NO GO",html)
        r["evidenceManifest"][0]["controlId"]="<script>x</script>"
        self.assertIn("&lt;script&gt;",render_html(r))

    def test_html_rejects_forged_approval_or_fake_proof(self):
        r=self.report()
        r["verifiedEvidenceCount"]=1
        with self.assertRaises(ImportRejected):
            render_html(r)
        r=self.report()
        r["noOperationalAuthority"]["mayReleaseEquipment"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_consistent_report_hashes_and_determinism(self):
        r=self.report()
        self.assertEqual(len(r["packageSha256"]),64)
        self.assertEqual(len(r["sourceReadinessSha256"]),64)
        self.assertEqual(r,self.report())

if __name__=="__main__":
    unittest.main()
