"""Cycle 36: adjudication decisions never grant causal validation or deployment."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from knowledge.causal_adjudication import (
    ROOT, PLAN, POLICY, MATRIX, MAP_PATH, MECHANICAL_POLICY,
    DISCRIMINATION_POLICY, SUBMISSIONS, REVIEW_POLICY,
    ACTIONS, PRIORITIES, DRAFT_SUFFIX,
    load, validate_policy, validate_plan,
    build_ledger, verify_ledger, adjudicate, verify_report, render_html, main,
)
from pilot.change_review_packets import ReviewRejected


class CausalAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(PLAN)
        cls.policy=load(POLICY)
        cls.batch=load(SUBMISSIONS)
        cls.matrix=load(MATRIX)
        cls.parent=load(MAP_PATH)
        cls.mpolicy=load(MECHANICAL_POLICY)
        cls.dpolicy=load(DISCRIMINATION_POLICY)
        cls.rpolicy=load(REVIEW_POLICY)

    def args(self,plan=None,policy=None,batch=None,matrix=None):
        return (plan if plan is not None else self.plan,
                policy if policy is not None else self.policy,
                batch if batch is not None else self.batch,
                matrix if matrix is not None else self.matrix,
                self.parent,self.mpolicy,self.dpolicy,self.rpolicy)

    def test_consistent_triage_of_36_author_only_challenges(self):
        result=adjudicate(*self.args())
        ledger=build_ledger(*self.args())
        self.assertTrue(verify_report(result,ledger,*self.args()))
        self.assertEqual(result["sourceRelations"],36)
        self.assertEqual(result["dispositionCounts"],{
            "defer_disputed_relation":12,
            "propose_unapproved_wording_revision":12,
            "reject_unsubstantiated_inference":12})
        self.assertEqual(result["editorialReviewPriorityCounts"],{
            "high_review_priority":12,"medium_review_priority":12,
            "watch_review_priority":12})
        self.assertEqual(result["historicBaselinesPreserved"],36)
        self.assertEqual(result["unapprovedCandidateVersions"],12)
        self.assertEqual(result["unresolvedIndependentReviews"],36)
        self.assertEqual(len(result["decisions"]),36)
        for decision in result["decisions"]:
            self.assertFalse(decision["independentExpertApproval"])
            self.assertFalse(decision["causeRootVerified"])
            self.assertFalse(decision["mayAmendUpstream"])
            self.assertFalse(decision["mayExecuteTest"])
            self.assertFalse(decision["mayCreateWorkOrder"])
            self.assertFalse(decision["mayReleaseEquipment"])
            self.assertTrue(decision["openCounterexample"])
        for f in ("reviewersAuthenticated","independentReviewCompleted",
                  "causalDiagnosticValidityEstablished","upstreamSourceRulesUpdated",
                  "ledgerIsImmutable","auditHashesProveIdentity","mayExecuteTest",
                  "mayCreateWorkOrder","mayReleaseEquipment",
                  "realWorldSafetySeverityAssigned"):
            self.assertIs(result[f],False)
        self.assertEqual(result["decision"],
            "no_go_editorial_drafts_require_independent_engineering_adjudication")

    def test_version_ledger_frozen_v1_plus_12_separate_candidate_v2(self):
        ledger=build_ledger(*self.args())
        self.assertEqual(ledger["baseVersionCount"],36)
        self.assertEqual(ledger["candidateVersionCount"],12)
        self.assertEqual(ledger["eventCount"],48)
        self.assertEqual(len(ledger["events"]),48)
        self.assertEqual(ledger["chainHead"],ledger["events"][-1]["eventDigest"])
        self.assertFalse(ledger["upstreamChanged"])
        self.assertFalse(ledger["externallyTimestamped"])
        self.assertFalse(ledger["cryptographicallySigned"])
        self.assertTrue(verify_ledger(ledger,*self.args()))
        by_rule={}
        for i,e in enumerate(ledger["events"]):
            self.assertEqual(e["sequence"],i+1)
            self.assertFalse(e["independentExpertApproved"])
            self.assertFalse(e["replacesSourceRule"])
            self.assertFalse(e["mayCreateWorkOrder"])
            if i:
                self.assertEqual(e["previousLedgerDigest"],
                                 ledger["events"][i-1]["eventDigest"])
            by_rule.setdefault(e["ruleId"],[]).append(e)
        self.assertEqual(len(by_rule),36)
        for rule in self.matrix["rules"]:
            versions=by_rule[rule["ruleId"]]
            self.assertEqual(versions[0]["versionLabel"],"v1-frozen")
            self.assertEqual(versions[0]["text"],rule["hypotheticalObservation"])
            if len(versions)==2:
                self.assertEqual(versions[1]["versionLabel"],"v2-proposed-unapproved")
                self.assertEqual(versions[1]["priorVersionDigest"],
                                 versions[0]["eventDigest"])
                self.assertEqual(versions[1]["text"],
                                 rule["hypotheticalObservation"]+DRAFT_SUFFIX)

    def test_priority_risk_is_review_only_never_machine_safety(self):
        for i in range(36):
            item=self.plan["items"][i]
            self.assertEqual(item["editorialPriority"],PRIORITIES[i%3])
            self.assertEqual(item["proposedDisposition"],ACTIONS[i%3])
            self.assertTrue(item["reasoning"])
            self.assertFalse(item["physicalCaseVerification"])

    def test_forged_disposition_severity_source_and_draft_fail_closed(self):
        mutations=[
            (0,"editorialPriority","watch_review_priority"),
            (0,"proposedDisposition","propose_unapproved_wording_revision"),
            (0,"reviewIds",["SIM-CR-001-2","SIM-CR-001-1"]),
            (0,"originalRuleText","Se uma hipótese foi comprovada pela máquina"),
            (0,"referencedGeneralSources",["FORGED-ISO-MANUAL"]),
            (1,"draftWording","Aprovar automaticamente a correção."),
            (1,"draftWording",None),
            (2,"draftWording","Atribuir causa raiz confirmada ao equipamento."),
            (0,"counterexampleDisposition","no_causal_claim_accepted_due_to_insufficient_evidence"),
        ]
        for i,key,value in mutations:
            plan=copy.deepcopy(self.plan)
            plan["items"][i][key]=value
            with self.subTest(index=i,key=key),self.assertRaises(ReviewRejected):
                validate_plan(*self.args(plan=plan))

    def test_unfounded_argument_and_missing_counterexample_fail(self):
        for i,key,value in [
            (0,"reasoning","SEM EVIDÊNCIAS"),
            (0,"reasoning","A análise abstrata pode ser concluída sem citar qualquer regra e sem consultar evidências independentes."*2),
        ]:
            plan=copy.deepcopy(self.plan)
            plan["items"][i][key]=value
            with self.subTest(index=i,key=key),self.assertRaises(ReviewRejected):
                validate_plan(*self.args(plan=plan))
        batch=copy.deepcopy(self.batch)
        batch["submissions"][0]["counterexample"]=""
        with self.assertRaises(ReviewRejected):
            adjudicate(*self.args(batch=batch))

    def test_false_technical_signoff_and_operational_permissions_fail(self):
        denied=("reviewerQualifiedIndependently","externalTechnicalApproval",
                "physicalCaseVerification","oemEffectivityVerified",
                "mayAmendUpstream","mayAuthorizeTest","mayCreateWorkOrder",
                "mayReleaseEquipment")
        for key in denied:
            p=copy.deepcopy(self.plan)
            p["items"][0][key]=True
            with self.subTest(item=key),self.assertRaises(ReviewRejected):
                validate_plan(*self.args(plan=p))
        for k in ("humanAdjudicatorAuthenticated",
                  "independentExpertAdjudicationCompleted"):
            p=copy.deepcopy(self.plan)
            p[k]=True
            with self.subTest(top=k),self.assertRaises(ReviewRejected):
                validate_plan(*self.args(plan=p))
        for k in ("independentSignoffVerified","diagnosticValidityEstablished",
                  "mayAmendUpstreamRules","mayExecuteTests",
                  "mayCreateWorkOrder","mayReleaseEquipment"):
            p=copy.deepcopy(self.policy)
            p[k]=True
            with self.subTest(policy=k),self.assertRaises(ReviewRejected):
                validate_policy(p)

    def test_tampered_version_chain_or_report_never_verify(self):
        ledger=build_ledger(*self.args())
        report=adjudicate(*self.args())
        l=copy.deepcopy(ledger)
        l["events"][20]["text"]="Aprovado por especialista."
        with self.assertRaises(ReviewRejected):
            verify_ledger(l,*self.args())
        l=copy.deepcopy(ledger)
        l["events"][21]["priorVersionDigest"]="0"*64
        with self.assertRaises(ReviewRejected):
            verify_ledger(l,*self.args())
        l=copy.deepcopy(ledger)
        l["chainHead"]="f"*64
        with self.assertRaises(ReviewRejected):
            verify_report(report,l,*self.args())
        r=copy.deepcopy(report)
        r["upstreamSourceRulesUpdated"]=True
        with self.assertRaises(ReviewRejected):
            verify_report(r,ledger,*self.args())

    def test_source_matrix_or_prior_review_change_invalidates_frozen_history(self):
        ledger=build_ledger(*self.args())
        modified=copy.deepcopy(self.matrix)
        modified["rules"][0]["causalInterpretation"]+=" Alterado sem aceite."
        with self.assertRaises(ReviewRejected):
            verify_ledger(ledger,*self.args(matrix=modified))
        revised_batch=copy.deepcopy(self.batch)
        revised_batch["submissions"][0]["argument"]+=" Informação adicionada depois."
        with self.assertRaises(ReviewRejected):
            verify_ledger(ledger,*self.args(batch=revised_batch))

    def test_cli_public_and_private_workflows_never_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="cycle36-pub-") as tmp:
            root=Path(tmp)
            report=root/"report.json"
            ledger=root/"ledger.json"
            html=root/"report.html"
            main(["--output",str(report),"--ledger",str(ledger),
                  "--html",str(html)])
            self.assertEqual(load(report)["sourceRelations"],36)
            self.assertEqual(load(ledger)["eventCount"],48)
            self.assertIn("NO GO",html.read_text(encoding="utf-8"))
            with self.assertRaises(ReviewRejected):
                main(["--output",str(report),"--ledger",str(report)])
        with tempfile.TemporaryDirectory(prefix="cycle36-private-") as tmp:
            root=Path(tmp)
            p=root/"plan.json"
            p.write_text(json.dumps(self.plan),encoding="utf-8")
            report=root/"report.json"
            history=root/"history.json"
            main(["--plan",str(p),"--output",str(report),"--ledger",str(history)])
            self.assertTrue(report.exists())
            self.assertTrue(history.exists())
            with self.assertRaises((FileExistsError,ReviewRejected)):
                main(["--plan",str(p),"--output",str(report),"--ledger",str(history)])
            with self.assertRaises(ValueError):
                main(["--plan",str(p),"--output",str(ROOT/"build"/"not-private.json"),
                      "--ledger",str(root/"different-ledger.json")])

    def test_html_and_four_json_contracts(self):
        report=adjudicate(*self.args())
        ledger=build_ledger(*self.args())
        html=render_html(report,ledger,*self.args())
        self.assertEqual(html.count("<section>"),36)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("NO GO",html)
        for name in ("causal-adjudication-plan.schema.json",
                     "causal-adjudication-policy.schema.json",
                     "causal-version-ledger.schema.json",
                     "causal-adjudication-report.schema.json"):
            schema=load(ROOT/"contracts"/name)
            self.assertEqual(schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
