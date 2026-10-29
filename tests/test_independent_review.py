"""Cycle 37: strict independent review preparation with zero fake approval."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from knowledge.independent_review import (
    ROOT, PROTOCOL, WORKLIST, CHECKS, MISSING, ROLES, SLOTS,
    validate_protocol, validate_worklist, build_packets, assess,
    verify_report, render_html, main,
)
from knowledge.causal_adjudication import (
    PLAN, POLICY as ADJ_POLICY, SUBMISSIONS, MATRIX, MAP_PATH,
    MECHANICAL_POLICY, DISCRIMINATION_POLICY, REVIEW_POLICY, load
)
from pilot.change_review_packets import ReviewRejected


class Cycle37ReviewReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol=load(PROTOCOL)
        cls.worklist=load(WORKLIST)
        cls.plan=load(PLAN)
        cls.policy=load(ADJ_POLICY)
        cls.batch=load(SUBMISSIONS)
        cls.matrix=load(MATRIX)
        cls.parent=load(MAP_PATH)
        cls.mp=load(MECHANICAL_POLICY)
        cls.dp=load(DISCRIMINATION_POLICY)
        cls.rp=load(REVIEW_POLICY)

    def parameters(self,protocol=None,worklist=None,plan=None,matrix=None):
        return (
            protocol if protocol is not None else self.protocol,
            worklist if worklist is not None else self.worklist,
            plan if plan is not None else self.plan,
            self.policy,self.batch,
            matrix if matrix is not None else self.matrix,
            self.parent,self.mp,self.dp,self.rp,
        )

    def test_all_36_tasks_blocked_and_roles_unassigned(self):
        packets=build_packets(*self.parameters())
        report=assess(*self.parameters())
        self.assertTrue(verify_report(report,packets,*self.parameters()))
        self.assertEqual(report["reviewTaskCount"],36)
        self.assertEqual(report["requestedReviewerOpinionSlots"],72)
        self.assertEqual(report["requestedAdjudicatorSlots"],36)
        self.assertEqual(report["unassignedParticipantRoleSlots"],5)
        self.assertEqual(report["missingGateCounts"],{k:36 for k in MISSING})
        self.assertEqual(report["relationsPendingIndependentReview"],36)
        self.assertEqual(report["relationsEligibleForTechnicalAcceptance"],0)
        self.assertEqual(report["relationsEligibleForTechnicalRejection"],0)
        self.assertEqual(report["sourceRuleVersionsModified"],0)
        self.assertEqual(report["actualVerifiedReviewers"],0)
        self.assertEqual(report["opinionsCollected"],0)
        self.assertEqual(report["qualifiedIndependentAdjudications"],0)
        self.assertFalse(report["readyToDispatchToVerifiedReviewers"])
        self.assertFalse(report["independentTechnicalReviewCompleted"])
        self.assertFalse(report["technicalDiagnosticAccuracyEstablished"])
        self.assertFalse(report["mayExecuteTest"])
        self.assertFalse(report["mayCreateWorkOrder"])
        self.assertFalse(report["mayReleaseEquipment"])
        self.assertEqual(report["decision"],
                         "no_go_collect_real_credentials_and_review_evidence")
        self.assertEqual(packets["packetCount"],36)
        self.assertEqual(packets["reviewerOpinionSlots"],72)
        self.assertEqual(packets["adjudicatorSlots"],36)
        for p in packets["packets"]:
            self.assertEqual(p["unmetQualificationAndEvidenceGates"],list(MISSING))
            self.assertEqual(p["opinionCount"],0)
            self.assertFalse(p["technicalRelationAccepted"])
            self.assertFalse(p["mayChangeUpstreamRule"])
            self.assertEqual(p["status"],"blocked_unassigned_reviewers_and_evidence")

    def test_independence_and_accept_reject_requirements_are_explicit(self):
        requirements=self.protocol["reviewRequirements"]
        self.assertEqual(requirements["independentReviewerCount"],2)
        self.assertTrue(requirements["requiresDifferentTechnicalReviewers"])
        self.assertTrue(requirements["adjudicatorSeparateFromReviewers"])
        self.assertTrue(requirements["authorsCannotApprove"])
        self.assertEqual(requirements["technicalAcceptanceRequiredGates"],list(MISSING))
        self.assertEqual(len(requirements["technicalRejectionRequires"]),4)
        self.assertTrue(requirements["noAutomaticTechnicalAcceptance"])
        self.assertTrue(requirements["noAutomaticTechnicalRejection"])
        self.assertTrue(requirements["deferredIfAnyGateMissing"])
        self.assertTrue(requirements["deferredIfDissentUnresolved"])
        self.assertTrue(requirements["technicalRevisionNeedsFrozenDiff"])
        self.assertEqual([x["role"] for x in self.protocol["roleSlots"]],
                         [x[0] for x in ROLES])
        self.assertEqual(len({x["slotAlias"] for x in self.protocol["roleSlots"]}),5)

    def test_bad_role_segregation_or_spoofed_credentials_rejected(self):
        for key,value in (
            ("slotAlias","SIM-SLOT-AUTHOR"),
            ("role","author"),
            ("actualHumanAssigned",True),
            ("identityVerified",True),
            ("disciplineCredentialsVerified",True),
            ("conflictOfInterestCleared",True),
            ("independenceFromAuthorsVerified",True),
            ("technicalSourceAccessAuthorized",True),
        ):
            protocol=copy.deepcopy(self.protocol)
            protocol["roleSlots"][2][key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_protocol(protocol)
        for key in (
            "externalTechnicalReviewCompleted","realCaseDataIncluded",
            "causalValidityEstablished","canPromoteRevision",
            "mayExecuteTest","mayCreateWorkOrder","mayReleaseEquipment",
        ):
            protocol=copy.deepcopy(self.protocol)
            protocol[key]=True
            with self.subTest(field=key),self.assertRaises(ReviewRejected):
                validate_protocol(protocol)

    def test_criteria_cannot_be_weakened(self):
        for key,value in (
            ("independentReviewerCount",1),
            ("adjudicatorSeparateFromReviewers",False),
            ("authorsCannotApprove",False),
            ("requiredEvidenceCategories",list(CHECKS)[:-1]),
            ("technicalAcceptanceRequiredGates",list(MISSING)[:-1]),
            ("technicalRejectionRequires",[]),
            ("deferredIfAnyGateMissing",False),
            ("deferredIfDissentUnresolved",False),
            ("noAutomaticTechnicalAcceptance",False),
            ("noAutomaticTechnicalRejection",False),
            ("technicalRevisionNeedsFrozenDiff",False),
        ):
            protocol=copy.deepcopy(self.protocol)
            protocol["reviewRequirements"][key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                validate_protocol(protocol)
        protocol=copy.deepcopy(self.protocol)
        protocol["verifiedExternalReviewers"]=2
        with self.assertRaises(ReviewRejected):
            validate_protocol(protocol)

    def test_forged_submission_or_permission_in_task_rejected(self):
        bad_flags=(
            "reviewerAOpinionSubmitted","reviewerBOpinionSubmitted",
            "independentReviewerQualificationsVerified",
            "identityAndConflictChecksVerified","oemSeriesEffectivityVerified",
            "realEvidenceProvenanceVerified","counterexampleResolved",
            "adjudicatorSignoffVerified","mayApproveTechnicalRelation",
            "mayChangeUpstreamRule","mayAuthorizeTest","mayCreateWorkOrder",
            "mayReleaseEquipment",
        )
        for field in bad_flags:
            work=copy.deepcopy(self.worklist)
            work["tasks"][1][field]=True
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_worklist(*self.parameters(worklist=work))
        for field,value in (
            ("externalReviewInvitationsSent",1),
            ("authenticatedExternalSignatures",1),
            ("nature","real_signed_independent_review"),
        ):
            work=copy.deepcopy(self.worklist)
            work[field]=value
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_worklist(*self.parameters(worklist=work))

    def test_source_or_version_mismatch_rejected(self):
        for field,value in (
            ("ruleId","DISC-999-1"),
            ("parentRecordId","MECH-KB-777"),
            ("priorReviewIds",["SIM-CR-002-1","SIM-CR-002-2"]),
            ("priorAdjudicationId","SIM-ADJ-777"),
            ("frozenRuleText","Alteração não autorizada do histórico"),
            ("proposedDraftText","Texto candidato aprovado automaticamente"),
            ("sourceIds",["NOT-IN-SOURCE"]),
            ("requiredEvidenceCategories",list(CHECKS)[1:]),
            ("requestedRoles",["author","technical_reviewer_a","adjudicator"]),
        ):
            work=copy.deepcopy(self.worklist)
            work["tasks"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_worklist(*self.parameters(worklist=work))
        old=copy.deepcopy(self.matrix)
        old["rules"][0]["causalInterpretation"]+=" Revisão não aprovada."
        with self.assertRaises(ReviewRejected):
            build_packets(*self.parameters(matrix=old))

    def test_counterexamples_and_scope_are_transmitted_without_approval(self):
        packets=build_packets(*self.parameters())
        for i,p in enumerate(packets["packets"]):
            source=self.worklist["tasks"][i]
            self.assertEqual(p["frozenRuleText"],source["frozenRuleText"])
            self.assertEqual(p["candidateTextForChallengeOnly"],source["proposedDraftText"])
            self.assertEqual(p["recordedObjection"],source["challengeSummary"])
            self.assertEqual(p["unresolvedCounterexample"],source["counterexampleStatus"])
            self.assertEqual(p["requestedReviewerSlots"],SLOTS)
            self.assertGreater(len(p["generalBackgroundSources"]),0)
            for s in p["generalBackgroundSources"]:
                self.assertTrue(s["url"].startswith("https://"))
                self.assertGreater(len(s["notEstablished"]),20)
            self.assertFalse(p["independentReviewCompleted"])
            self.assertTrue(p["openCounterexample"])

    def test_digests_and_report_not_promoted_by_edit(self):
        packet=build_packets(*self.parameters())
        report=assess(*self.parameters())
        altered=copy.deepcopy(report)
        altered["actualVerifiedReviewers"]=2
        with self.assertRaises(ReviewRejected):
            verify_report(altered,packet,*self.parameters())
        altered=copy.deepcopy(packet)
        altered["packets"][2]["opinionCount"]=2
        with self.assertRaises(ReviewRejected):
            verify_report(report,altered,*self.parameters())
        altered=copy.deepcopy(packet)
        altered["packets"][0]["technicalRelationAccepted"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(report,altered,*self.parameters())

    def test_cli_json_html_and_no_manual_external_fake_input(self):
        with tempfile.TemporaryDirectory(prefix="cycle37-") as tmp:
            root=Path(tmp)
            report=root/"report.json"
            packets=root/"packets.json"
            html=root/"report.html"
            main(["--output",str(report),"--packets",str(packets),
                  "--html",str(html)])
            self.assertEqual(json.loads(report.read_text())["reviewTaskCount"],36)
            self.assertEqual(json.loads(packets.read_text())["packetCount"],36)
            htmltext=html.read_text()
            self.assertEqual(htmltext.count("<section>"),36)
            self.assertNotIn("<script",htmltext)
            self.assertNotIn("<form",htmltext)
            self.assertIn("NO GO",htmltext)
            with self.assertRaises(ReviewRejected):
                main(["--output",str(report),"--packets",str(report)])
            protocol=root/"manual-policy.json"
            protocol.write_text(json.dumps(self.protocol))
            with self.assertRaises(ReviewRejected):
                main(["--output",str(report),"--packets",str(packets),
                      "--protocol",str(protocol)])
            fake_work=root/"manual-worklist.json"
            fake_work.write_text(json.dumps(self.worklist))
            with self.assertRaises(ReviewRejected):
                main(["--output",str(report),"--packets",str(packets),
                      "--worklist",str(fake_work)])

    def test_four_json_schemas(self):
        for filename in (
            "independent-review-protocol.schema.json",
            "independent-review-worklist.schema.json",
            "independent-review-packets.schema.json",
            "independent-review-readiness.schema.json",
        ):
            schema=load(ROOT/"contracts"/filename)
            self.assertEqual(schema["$schema"],
                             "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
