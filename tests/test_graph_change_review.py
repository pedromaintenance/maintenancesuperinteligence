"""Cycle 24 — hypothetical DAG diffs, 100-case oracle, no operational authority."""
import copy
import json
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT,validate_catalog as validate_catalog
from casefiles.integrated import load_dependencies,build_collection
from notifications.drafts import SPEC_PATH as NOTES_SPEC,build_notifications
from quality.notifications import RUBRIC_PATH,ORACLE_PATH,build_report as build_quality
from editorial.review_protocol import FIXTURE_PATH as EDIT_SPEC,build_report as build_editorial
from pilot.readiness import FIXTURE_PATH as READY_SPEC,build_report as build_readiness
from pilot.go_nogo import PACKAGE_PATH,DEPENDENCIES,build_report as build_gng
from pilot.evidence_sequence import SPEC_PATH as SEQ_SPEC,build_report as build_seq
from pilot.evidence_contradictions import FIXTURE_PATH as CONF_SPEC,build_report as build_conf
from pilot.reopen_coverage import SPEC_PATH as COVERAGE_SPEC,build_report as build_coverage
from pilot.graph_change_review import (SPEC_PATH,build_report,validate_spec,verify_report,
                                      propose,all_pair_matrix,render_html,IDS,EDGE_LIST)

class GraphChangeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                              "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,registry,snap:validate_catalog(cat,registry)):
            deps=load_dependencies(snapshot)
        raw=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        fake={"caseId":raw["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":h["hypothesisId"]}
                            for h in deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],"conflicts":[],"knowledgeGaps":[]}
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=fake)):
            cases=build_collection(json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text()),
                                   deps,snapshot)
        notes=build_notifications(json.loads(NOTES_SPEC.read_text()),cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,json.loads(RUBRIC_PATH.read_text()),json.loads(ORACLE_PATH.read_text()))
        edit=build_editorial(json.loads(EDIT_SPEC.read_text()),quality,notes)
        ready=build_readiness(json.loads(READY_SPEC.read_text()),edit)
        gng=build_gng(json.loads(PACKAGE_PATH.read_text()),ready)
        seq=build_seq(json.loads(SEQ_SPEC.read_text()),gng)
        conf=build_conf(json.loads(CONF_SPEC.read_text()),seq,gng)
        cov=build_coverage(json.loads(COVERAGE_SPEC.read_text()),conf,seq,gng)
        cls.base=(gng,cov)

    def setUp(self):
        self.gng,self.coverage=copy.deepcopy(type(self).base)
        self.spec=json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def result(self):
        return build_report(self.spec,self.coverage,self.gng)

    def rejected(self):
        with self.assertRaises(ImportRejected):
            self.result()

    def test_ten_proposals_canonical_source_and_no_go(self):
        r=self.result()
        self.assertEqual((r["proposalCount"],r["baselineControlCount"],r["baselineEdgeCount"],
                          r["sourceOracleScenarioCount"]),(10,13,17,100))
        self.assertEqual(r["decision"],"no_go")
        self.assertTrue(r["allProposalsVetoed"])
        self.assertEqual(r["realChangesCommitted"],0)
        self.assertEqual(r["verifiedHumanReviewCount"],0)
        self.assertTrue(all(not v for v in r["operationalAuthority"].values()))
        self.assertTrue(all(p["changeAdjudication"]["decision"]=="veto_no_merge"
                            for p in r["proposals"]))

    def test_canonical_graph_remains_exactly_unchanged(self):
        original=copy.deepcopy(DEPENDENCIES)
        before=SPEC_PATH.read_bytes()
        self.result()
        self.assertEqual(original,DEPENDENCIES)
        self.assertEqual(before,SPEC_PATH.read_bytes())

    def test_compare_all_100_cases_for_valid_proposals(self):
        r=self.result()
        for p in r["proposals"]:
            if p["candidateDagValid"]:
                self.assertTrue(p["coverageRegression"]["allOneHundredScenariosCompared"])
                self.assertEqual(p["coverageRegression"]["comparableScenarioCount"],100)
                self.assertEqual(p["graphNodeCount"],13)
            else:
                self.assertFalse(p["coverageRegression"]["allOneHundredScenariosCompared"])
                self.assertEqual(p["coverageRegression"]["comparableScenarioCount"],0)

    def test_edge_addition_cannot_destroy_reachability(self):
        r=self.result()
        for i in (0,5,7):
            p=r["proposals"][i]
            self.assertTrue(p["candidateDagValid"])
            self.assertEqual(p["reachabilityImpact"]["lostPairs"],0)
            self.assertFalse(p["reachabilityImpact"]["rootsWithLostReachability"])
            self.assertEqual(len(p["edgeDiff"]["addedEdges"]),1)

    def test_edge_removal_cannot_create_reachability(self):
        r=self.result()
        for i in (1,6):
            p=r["proposals"][i]
            self.assertTrue(p["candidateDagValid"])
            self.assertEqual(p["reachabilityImpact"]["introducedPairs"],0)
            self.assertEqual(len(p["edgeDiff"]["removedEdges"]),1)

    def test_redundant_path_changes_metric_without_new_root(self):
        r=self.result()
        p=r["proposals"][0]
        self.assertEqual(p["impactClassification"],"path_metrics_changed_only")
        self.assertEqual(p["reachabilityImpact"]["introducedPairs"],0)
        self.assertGreater(p["reachabilityImpact"]["changedPairCount"],0)
        self.assertTrue(any(v["oldPossiblePathCount"] != v["newPossiblePathCount"]
                            for v in p["reachabilityImpact"]["changedRootTargetPairs"]))

    def test_reverse_edge_is_auditable(self):
        r=self.result()
        p=r["proposals"][2]
        self.assertEqual(p["changeType"],"edge_reverse")
        self.assertEqual(len(p["edgeDiff"]["addedEdges"]),1)
        self.assertEqual(len(p["edgeDiff"]["removedEdges"]),1)
        self.assertGreater(p["reachabilityImpact"]["changedPairCount"],0)

    def test_oem_reopen_changes_documentary_closure_not_machine(self):
        r=self.result()
        p=r["proposals"][5]
        self.assertEqual(p["rationale"],"oem_context_revision_requires_reopen")
        self.assertGreater(p["reachabilityImpact"]["introducedPairs"],0)
        self.assertEqual(p["changeAdjudication"]["decision"],"veto_no_merge")
        for c in p["coverageRegression"]["affectedScenarios"]:
            self.assertTrue(c["noFieldEvidence"])
            self.assertFalse(c["mayAuthorizeMaintenance"])

    def test_invalid_owner_and_control_suppression_vetoed(self):
        r=self.result()
        self.assertEqual(r["proposals"][3]["impactClassification"],"owner_governance_violation")
        self.assertFalse(r["proposals"][3]["candidateContractValid"])
        self.assertIsNotNone(r["proposals"][3]["edgeDiff"]["ownerDifference"])
        self.assertEqual(r["proposals"][4]["validationReason"],"protected_control_removed")
        self.assertFalse(r["proposals"][4]["candidateDagValid"])

    def test_cycles_unknown_endpoints_rejected_without_assuming_zero_impact(self):
        r=self.result()
        self.assertEqual(r["proposals"][8]["validationReason"],"cycle_detected")
        self.assertEqual(r["proposals"][9]["validationReason"],"unknown_endpoint")
        self.assertFalse(r["proposals"][8]["candidateDagValid"])
        self.assertFalse(r["proposals"][9]["candidateDagValid"])

    def test_pair_witness_has_old_new_reachability_distance_and_count(self):
        r=self.result()
        p=r["proposals"][6]
        self.assertGreater(p["reachabilityImpact"]["lostPairs"],0)
        for d in p["reachabilityImpact"]["changedRootTargetPairs"]:
            self.assertIn(d["rootControlId"],IDS)
            self.assertIn(d["targetControlId"],IDS)
            self.assertTrue(d["documentaryChangeOnly"])
            self.assertFalse(d["physicalSafetyEstablished"])
            self.assertIsInstance(d["oldPossiblePathCount"],int)
            self.assertIsInstance(d["newPossiblePathCount"],int)
        self.assertTrue(p["coverageRegression"]["affectedScenarios"])

    def test_forged_physical_truth_in_proposal_rejected(self):
        self.spec["proposals"][0]["sourceAuthenticated"]=True
        self.rejected()

    def test_missing_proposal_rejected(self):
        self.spec["proposals"].pop()
        self.rejected()

    def test_modification_of_proposal_intent_rejected(self):
        self.spec["proposals"][0]["intent"]="automated_merge"
        self.rejected()

    def test_forged_review_signature_rejected(self):
        self.spec["reviewPolicy"]["signatureVerified"]=True
        self.rejected()

    def test_forged_human_independence_rejected(self):
        self.spec["reviewPolicy"]["independentReviewVerified"]=True
        self.rejected()

    def test_elevating_oem_effectivity_rejected(self):
        self.spec["reviewPolicy"]["oemEffectivityVerified"]=True
        self.rejected()

    def test_removing_legal_review_rejected(self):
        self.spec["reviewPolicy"]["requiredAreas"].remove("Legal")
        self.rejected()

    def test_adding_sap_authorization_rejected(self):
        self.spec["reviewPolicy"]["mayWriteSap"]=True
        self.rejected()

    def test_forged_coverage_oracle_rejected(self):
        self.coverage["scenarioCount"]=99
        self.rejected()

    def test_forged_gng_approval_rejected(self):
        self.gng["verifiedSignoffs"]=1
        self.rejected()

    def test_verifier_detects_changed_metrics(self):
        result=self.result()
        result["proposals"][0]["reachabilityImpact"]["changedPairCount"]+=1
        with self.assertRaises(ImportRejected):
            verify_report(result,self.spec,self.coverage,self.gng)

    def test_report_deterministic_hashes(self):
        a=self.result()
        b=self.result()
        self.assertEqual(a,b)
        self.assertEqual(len(a["canonicalDagSha256"]),64)

    def test_html_static_escape_and_no_authentication(self):
        result=self.result()
        html=render_html(result)
        self.assertEqual(html.count("<section>"),10)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("NO GO",html)
        result["proposals"][0]["rationale"]="<script>x</script>"
        self.assertIn("&lt;script&gt;",render_html(result))

    def test_html_refuses_forged_decision(self):
        r=self.result()
        r["proposals"][0]["changeAdjudication"]["decision"]="approve"
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_refuses_sap_authority(self):
        r=self.result()
        r["operationalAuthority"]["mayWriteSap"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

if __name__=="__main__":
    unittest.main()
