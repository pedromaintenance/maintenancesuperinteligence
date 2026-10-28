"""Cycle 35: adversarial editorial dissent and frozen private intake."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from knowledge.causal_review import (
    ROOT,SUBMISSIONS,POLICY,MATRIX,MAP_PATH,MECHANICAL_POLICY,
    DISCRIMINATION_POLICY,TRIAGE,validate_policy,validate_submissions,
    freeze_receipt,verify_receipt,evaluate,verify_report,render_html,main,
)
from pilot.change_review_packets import ReviewRejected


class Cycle35CausalReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=json.loads(SUBMISSIONS.read_text(encoding="utf-8"))
        cls.policy=json.loads(POLICY.read_text(encoding="utf-8"))
        cls.matrix=json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.parent=json.loads(MAP_PATH.read_text(encoding="utf-8"))
        cls.mpolicy=json.loads(MECHANICAL_POLICY.read_text(encoding="utf-8"))
        cls.dpolicy=json.loads(DISCRIMINATION_POLICY.read_text(encoding="utf-8"))

    def kwargs(self,batch=None,receipt=None):
        b=batch if batch is not None else self.batch
        r=receipt if receipt is not None else freeze_receipt(b,self.matrix,self.policy)
        return dict(batch=b,matrix=self.matrix,parent=self.parent,
                    mechanical_policy=self.mpolicy,
                    discrimination_policy=self.dpolicy,
                    policy=self.policy,receipt=r)

    def test_complete_fictional_contestation_does_not_validate_any_rule(self):
        report=evaluate(**self.kwargs())
        self.assertTrue(verify_report(report,**self.kwargs()))
        self.assertEqual(report["sourceRuleCount"],36)
        self.assertEqual(report["recordedUnverifiedChallenges"],72)
        self.assertEqual(report["verifiedExpertReviewers"],0)
        self.assertEqual(report["editorialTriageCounts"],{
            "unresolved_dissent":12,
            "revision_proposed_unapproved":12,
            "removal_proposed_unapproved":0,
            "support_insufficient":12,
            "retain_as_unverified_hypothesis":0,
        })
        self.assertEqual(report["pendingIndependentResolutionCount"],36)
        self.assertEqual(report["decision"],"no_go_independent_causal_review_required")
        self.assertFalse(report["rulesExternallyReviewed"])
        self.assertFalse(report["causalMechanismsFieldValidated"])
        self.assertFalse(report["sourceApplicabilityPerSerialVerified"])
        self.assertFalse(report["upstreamRulesAmended"])
        self.assertFalse(report["mayExecuteTest"])
        self.assertFalse(report["mayCreateWorkOrder"])
        self.assertFalse(report["mayReleaseEquipment"])
        self.assertEqual(len(report["auditChain"]),72)
        for r in report["reviewedRules"]:
            self.assertTrue(r["requiresIndependentTechnicalResolution"])
            self.assertFalse(r["technicalRelationValidated"])
            self.assertFalse(r["mayChangeUpstreamRule"])

    def test_audit_chain_is_replayable_but_not_a_signature(self):
        report=evaluate(**self.kwargs())
        self.assertFalse(report["auditChainAuthenticatesPeople"])
        entries=report["auditChain"]
        self.assertEqual(entries[0]["sequence"],1)
        self.assertEqual(entries[-1]["linkDigest"],report["auditChainHead"])
        self.assertEqual(entries[-1]["sequence"],72)
        for left,right in zip(entries,entries[1:]):
            self.assertEqual(left["linkDigest"],right["previousDigest"])
        forged=copy.deepcopy(report)
        forged["auditChain"][40]["recordDigest"]="0"*64
        with self.assertRaises(ReviewRejected):
            verify_report(forged,**self.kwargs())
        forged=copy.deepcopy(report)
        forged["auditChainHead"]="a"*64
        with self.assertRaises(ReviewRejected):
            verify_report(forged,**self.kwargs())

    def test_bad_sources_duplicate_reviewer_or_unrecognized_outcome_rejected(self):
        changes=[
            ("sourceIds",["OEM-LICENCED-MANUAL-NOT-AVAILABLE"]),
            ("sourceIds",[]),
            ("disposition","approved_causal_relation"),
            ("challengeType","proven_test_result"),
            ("sourceScope","verified_model_specific"),
            ("reviewerAlias","SIM-CRITIC-A"),
            ("ruleId","DISC-888-1"),
            ("ruleText","Altered editorial observation not present in frozen rule"),
            ("parentRecordId","MECH-KB-777"),
        ]
        for key,value in changes:
            batch=copy.deepcopy(self.batch)
            batch["submissions"][1][key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_submissions(batch,self.matrix,self.parent,self.mpolicy,
                                     self.dpolicy,self.policy)

    def test_false_identity_engineering_signoff_field_and_maintenance_authority(self):
        for field in [
            "reviewerIdentityVerified","independentExpertStatusVerified",
            "observedCaseEvidence","rootCauseEstablished",
            "oemEffectivityVerified","engineeringSignoff",
            "mayAuthorizeTest","mayCreateWorkOrder","mayReleaseEquipment",
        ]:
            batch=copy.deepcopy(self.batch)
            batch["submissions"][0][field]=True
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_submissions(batch,self.matrix,self.parent,self.mpolicy,
                                     self.dpolicy,self.policy)
        batch=copy.deepcopy(self.batch)
        batch["authenticHumanReviewCount"]=2
        with self.assertRaises(ReviewRejected):
            validate_submissions(batch,self.matrix,self.parent,self.mpolicy,
                                 self.dpolicy,self.policy)
        batch=copy.deepcopy(self.batch)
        batch["independentTechnicalReviewCompleted"]=True
        with self.assertRaises(ReviewRejected):
            validate_submissions(batch,self.matrix,self.parent,self.mpolicy,
                                 self.dpolicy,self.policy)

    def test_revisions_are_proposals_not_overwrites(self):
        report=evaluate(**self.kwargs())
        revision=report["reviewedRules"][1]
        self.assertEqual(revision["editorialTriage"],"revision_proposed_unapproved")
        self.assertTrue(revision["hasProposedUnapprovedRevision"])
        self.assertFalse(revision["mayChangeUpstreamRule"])
        batch=copy.deepcopy(self.batch)
        batch["submissions"][2]["proposedRevision"]=None
        with self.assertRaises(ReviewRejected):
            validate_submissions(batch,self.matrix,self.parent,self.mpolicy,
                                 self.dpolicy,self.policy)
        batch=copy.deepcopy(self.batch)
        batch["submissions"][0]["proposedRevision"]="Unexpected editorial revision"
        with self.assertRaises(ReviewRejected):
            validate_submissions(batch,self.matrix,self.parent,self.mpolicy,
                                 self.dpolicy,self.policy)

    def test_source_matrix_mutation_and_frozen_receipt_detected(self):
        receipt=freeze_receipt(self.batch,self.matrix,self.policy)
        modified=copy.deepcopy(self.batch)
        modified["submissions"][0]["argument"]+=" Arbitrary appended comment."
        with self.assertRaises(ReviewRejected):
            verify_receipt(receipt,modified,self.matrix,self.policy)
        modified=copy.deepcopy(self.matrix)
        modified["rules"][0]["causalInterpretation"]+=" Updated interpretation."
        with self.assertRaises(ReviewRejected):
            evaluate(self.batch,modified,self.parent,self.mpolicy,
                     self.dpolicy,self.policy,receipt)

    def test_policy_and_report_cannot_claim_approval(self):
        for key in ("realCausalValidationCompleted","canAmendUpstreamRules",
                    "mayExecuteTest","mayCreateWorkOrder","mayReleaseEquipment"):
            altered=copy.deepcopy(self.policy)
            altered[key]=True
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_policy(altered)
        report=evaluate(**self.kwargs())
        report["rulesExternallyReviewed"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(report,**self.kwargs())

    def test_external_private_unverified_intake_and_receipt_replay(self):
        batch=copy.deepcopy(self.batch)
        batch["nature"]="unverified_private_reviewer_submissions"
        for i,r in enumerate(batch["submissions"]):
            r["reviewId"]=f"REV-CR-{i//2+1:03d}-{i%2+1}"
            r["reviewerAlias"]="REV-ALPHA" if i%2==0 else "REV-BETA"
        with tempfile.TemporaryDirectory(prefix="cycle35-private-") as tmp:
            root=Path(tmp)
            submissions=root/"submissions.json"
            seal=root/"receipt.json"
            out=root/"report.json"
            submissions.write_text(json.dumps(batch),encoding="utf-8")
            main(["--submissions",str(submissions),"--seal-only",
                  "--output",str(seal)])
            self.assertTrue(seal.exists())
            main(["--submissions",str(submissions),"--receipt",str(seal),
                  "--output",str(out)])
            report=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["mode"],"unverified_private_submission_triage")
            self.assertEqual(report["verifiedExpertReviewers"],0)
            self.assertEqual(report["pendingIndependentResolutionCount"],36)
            self.assertFalse(report["rulesExternallyReviewed"])
            with self.assertRaises(FileExistsError):
                main(["--submissions",str(submissions),"--receipt",str(seal),
                      "--output",str(out)])
            changed=copy.deepcopy(batch)
            changed["submissions"][0]["argument"]+=" Second version not frozen."
            submissions.write_text(json.dumps(changed),encoding="utf-8")
            with self.assertRaises(ReviewRejected):
                main(["--submissions",str(submissions),"--receipt",str(seal),
                      "--output",str(root/"not-created.json")])
            self.assertFalse((root/"not-created.json").exists())

    def test_private_path_boundary_and_html_escaping(self):
        with tempfile.TemporaryDirectory(prefix="cycle35-public-boundary-") as tmp:
            from benchmarks.heldout_study import private_path
            with self.assertRaises(ValueError):
                private_path(ROOT/"build"/"external-review-answers.json")
            output=Path(tmp)/"report.json"
            report=main(["--output",str(output)])
            html=render_html(report,**self.kwargs())
            self.assertEqual(html.count("<section>"),36)
            self.assertNotIn("<script",html.lower())
            self.assertNotIn("<form",html.lower())
            self.assertIn("NO GO",html)
            self.assertTrue(output.exists())

    def test_four_schemas_present(self):
        for name in (
            "causal-review-policy.schema.json",
            "causal-review-submissions.schema.json",
            "causal-review-receipt.schema.json",
            "causal-review-report.schema.json",
        ):
            obj=json.loads((ROOT/"contracts"/name).read_text())
            self.assertEqual(obj["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(obj["additionalProperties"])


if __name__=="__main__":
    unittest.main()
