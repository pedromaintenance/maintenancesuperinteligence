"""Ciclo 18: nenhuma persona fictícia fornece aprovação humana autêntica."""
import copy
import json
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as original_catalog
from casefiles.integrated import load_dependencies, build_collection
from notifications.drafts import SPEC_PATH, build_notifications
from quality.notifications import (RUBRIC_PATH, ORACLE_PATH,
                                   build_report as build_quality)
from editorial.review_protocol import (FIXTURE_PATH, validate_fixture,
                                       build_report, render_html, verify_report)

class EditorialProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,registry,snapshot:original_catalog(cat,registry)):
            cls.dependencies=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).dependencies)
        self.fixture=json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def corpus(self):
        raw=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        example={
            "caseId":raw["caseId"],"confirmedRootCause":None,
            "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
            "hypotheses":[{"id":x["hypothesisId"]}
                           for x in self.deps["families"]["final_drive"]["hypotheses"]],
            "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
            "decision":"needs_evidence","observations":[],
            "conflicts":[],"knowledgeGaps":[],
        }
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=example)):
            fixture=json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text())
            cases=build_collection(fixture,self.deps,self.snapshot)
        spec=json.loads(SPEC_PATH.read_text())
        notes=build_notifications(spec,cases["cases"],cases["investigationTrees"])
        rubric=json.loads(RUBRIC_PATH.read_text())
        oracle=json.loads(ORACLE_PATH.read_text())
        quality=build_quality(notes,cases,rubric,oracle)
        return notes,quality

    def report(self):
        notes,quality=self.corpus()
        return build_report(self.fixture,quality,notes)

    def reject(self):
        notes,quality=self.corpus()
        with self.assertRaises(ImportRejected):
            build_report(self.fixture,quality,notes)

    def test_four_cases_roles_and_sixteen_events(self):
        report=self.report()
        self.assertEqual(report["caseCount"],4)
        self.assertEqual(report["simulatedEventCount"],16)
        self.assertEqual([x["decision"] for x in report["cases"]],[
            "requires_revision","unresolved_disagreement",
            "pending_real_review","pending_real_review"])
        self.assertEqual(report["realReviewsCompleted"],0)
        self.assertEqual(report["realApprovalsGranted"],0)
        self.assertFalse(report["mayWriteToSap"])
        self.assertFalse(report["mayReleaseEquipment"])

    def test_versions_disagreement_and_reopen_invalidate_old_reviews(self):
        c=self.report()["cases"]
        self.assertEqual(c[0]["currentRevision"],1)
        self.assertEqual(c[1]["decision"],"unresolved_disagreement")
        self.assertTrue(c[1]["adjudicationPerformedInSimulation"])
        self.assertEqual(c[2]["currentRevision"],3)
        self.assertEqual([x["trigger"] for x in c[2]["documentRevisions"]],
                         ["submit","revise","reopen_context"])
        self.assertTrue(all(not x["validForCurrentRevision"]
                            for x in c[2]["reviewRecords"]))
        self.assertEqual(c[3]["revokedPersonaIds"],["SIM-REVIEWER-4-B"])
        self.assertEqual(c[3]["fictionalCurrentReviewerCount"],1)

    def test_audit_chain_is_deterministic_and_not_signed(self):
        report=self.report()
        self.assertEqual(report,self.report())
        for c in report["cases"]:
            for prev,event in zip(c["auditTrail"],c["auditTrail"][1:]):
                self.assertEqual(prev["eventDigest"],event["previousEventDigest"])
            self.assertEqual(c["auditFinalDigest"],
                             c["auditTrail"][-1]["eventDigest"])
            self.assertFalse(c["externalAuditAnchorVerified"])
            self.assertTrue(c["auditDigestRecomputedFromFixture"])
            self.assertTrue(all(not e["verifiedCryptographicSignature"]
                                and not e["externalImmutabilityVerified"]
                                for e in c["auditTrail"]))

    def test_personas_not_authenticated_or_qualified(self):
        report=self.report()
        self.assertFalse(report["signaturesVerified"])
        self.assertFalse(report["externalImmutableAuditLogVerified"])
        self.assertFalse(report["interRaterReliabilityMeasured"])
        for c in report["cases"]:
            self.assertEqual(c["independentRealReviewerCount"],0)
            self.assertTrue(all(v is False for v in c["acceptanceBoundary"].values()))
            self.assertFalse(c["humanEditorialAgreementEstablished"])
            self.assertFalse(c["reviewerCompetenceVerified"])
            self.assertFalse(c["mayBeImportedToSap"])

    def test_duplicate_persona_alias_rejected(self):
        self.fixture["actors"][2]["personaKey"]=self.fixture["actors"][1]["personaKey"]
        self.reject()

    def test_reviewer_self_author_role_rejected(self):
        self.fixture["cases"][0]["reviewerIds"][0]=self.fixture["cases"][0]["authorId"]
        self.reject()

    def test_wrong_reviewer_discipline_rejected(self):
        self.fixture["actors"][1]["declaredCompetence"]="electronics"
        self.reject()

    def test_fake_credential_rejected(self):
        self.fixture["actors"][1]["qualificationVerified"]=True
        self.reject()

    def test_fake_human_identity_rejected(self):
        self.fixture["actors"][1]["identityVerified"]=True
        self.reject()

    def test_fake_signature_rejected(self):
        self.fixture["cases"][0]["events"][1]["signature"]="FAKE-SIGNATURE"
        self.reject()

    def test_duplicate_nonce_rejected(self):
        self.fixture["cases"][1]["events"][1]["nonce"]=(
            self.fixture["cases"][0]["events"][0]["nonce"])
        self.reject()

    def test_duplicate_reviewer_in_same_version_rejected(self):
        self.fixture["cases"][0]["events"][2]["actorId"]=(
            self.fixture["cases"][0]["events"][1]["actorId"])
        self.reject()

    def test_stale_review_version_rejected(self):
        self.fixture["cases"][2]["events"][2]["targetRevision"]=2
        self.reject()

    def test_revision_skipping_rejected(self):
        self.fixture["cases"][2]["events"][3]["targetRevision"]=4
        self.reject()

    def test_reopen_by_reviewer_rejected(self):
        self.fixture["cases"][2]["events"][4]["actorId"]="SIM-REVIEWER-3-A"
        self.reject()

    def test_unauthorized_custodian_action_rejected(self):
        self.fixture["cases"][3]["events"][3]["actorId"]="SIM-REVIEWER-4-A"
        self.reject()

    def test_cannot_hide_review_disagreement(self):
        self.fixture["cases"][1]["events"][2]["action"]="review_requires_revision"
        self.fixture["cases"][1]["events"][2]["reason"]="scope_needs_clarification"
        self.reject()

    def test_no_real_approval_action_allowed(self):
        self.fixture["cases"][1]["events"][3]["action"]="approve_for_field"
        self.reject()

    def test_not_allowed_to_invent_oem_field_evidence(self):
        self.fixture["mayPersistPrivateEvidence"]=True
        self.reject()

    def test_cannot_attach_private_identity_or_actor_key(self):
        self.fixture["actors"][0]["privateBadgeNumber"]="DEMO"
        self.reject()

    def test_hash_provenance_and_verification(self):
        notes,quality=self.corpus()
        out=build_report(self.fixture,quality,notes)
        self.assertEqual(len(out["fixtureSha256"]),64)
        self.assertEqual(len(out["qualityReportSha256"]),64)
        self.assertEqual(verify_report(out,self.fixture,quality,notes),out)
        out["cases"][0]["auditTrail"][1]["eventDigest"]="0"*64
        with self.assertRaises(ImportRejected):
            verify_report(out,self.fixture,quality,notes)

    def test_html_static_escapes_and_blocks_forged_status(self):
        report=self.report()
        html=render_html(report)
        self.assertEqual(html.count("<section>"),4)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        report["cases"][0]["reviewRecords"][0]["reason"]="<script>inert</script>"
        self.assertIn("&lt;script&gt;",render_html(report))
        report["mayWriteToSap"]=True
        with self.assertRaises(ImportRejected):
            render_html(report)

    def test_html_denies_authentic_signature_claim(self):
        report=self.report()
        report["cases"][1]["reviewRecords"][0]["signatureVerified"]=True
        with self.assertRaises(ImportRejected):
            render_html(report)

if __name__=="__main__":
    unittest.main()
