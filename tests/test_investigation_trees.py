"""Adversarial tests: trees describe unanswered questions, not machine clearance."""
import copy
import json
import unittest
from unittest.mock import patch
from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as original_catalog
from casefiles.integrated import load_dependencies, build_collection
from trees.investigation import SPEC_PATH, build_trees, validate_spec, verify_trees
from trees.presentation import render_tree_html

class InvestigationTreesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat, sources, snapshot:
                   original_catalog(cat, sources)):
            cls.deps=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).deps)
        self.spec=json.loads(SPEC_PATH.read_text())
        self.fixtures=json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text())

    def report(self):
        source=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        fake={"caseId":source["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":h["hypothesisId"]}
                            for h in self.deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],
              "conflicts":[],"knowledgeGaps":[]}
        with patch("casefiles.integrated.build_consumer_index",return_value={}):
            with patch("casefiles.integrated.investigate",return_value=fake):
                return build_collection(self.fixtures,self.deps,self.snapshot)

    def test_four_trees_have_all_thirteen_pair_nodes(self):
        v=self.report()
        t=v["investigationTrees"]
        self.assertEqual(t["treeCount"],4)
        self.assertEqual(t["nodeCount"],13)
        self.assertEqual([len(x["nodes"]) for x in t["trees"]],[4,3,3,3])
        self.assertEqual(v["hypothesesOpen"],19)
        self.assertEqual(t["physicalTestsExecuted"],0)

    def test_all_paths_end_at_human_review(self):
        trees=self.report()["investigationTrees"]["trees"]
        for tree in trees:
            self.assertEqual(tree["decision"],"abstain_pending_verified_evidence")
            self.assertFalse(tree["unresolvedHypothesisSet"]["rootCauseConfirmed"])
            self.assertEqual(tree["traceSelectedRoot"]["hypotheticalBranchesTaken"],0)
            self.assertFalse(tree["mayCreateWorkOrder"])
            self.assertFalse(tree["mayModifyECM"])
            self.assertFalse(tree["mayReleaseEquipment"])
            for node in tree["nodes"]:
                self.assertFalse(node["mayExecute"])
                self.assertEqual(node["testStatus"],"not_performed")
                self.assertEqual(len(node["conditionalBranches"]),3)
                self.assertEqual(len(node["counterexamples"]),2)
                self.assertEqual(node["evidenceGate"]["actualTransition"],
                                 node["reviewCheckpoint"]["nodeId"])
                self.assertFalse(node["reviewCheckpoint"]["allProofsVerified"])
                self.assertFalse(node["reviewCheckpoint"]["humanReviewAuthenticated"])
                for branch in node["conditionalBranches"]:
                    self.assertFalse(branch["observed"])
                    self.assertEqual(branch["hypothesesExcluded"],0)

    def test_states_distinguish_hydraulic_disagreement_from_missing_context(self):
        trees=self.report()["investigationTrees"]["trees"]
        self.assertEqual([x["traceSelectedRoot"]["contextState"] for x in trees],
                         ["not_measured","contradicted","not_measured","not_measured"])
        self.assertEqual(trees[1]["traceSelectedRoot"]["reason"],"reconcile_conflict")
        self.assertEqual(trees[3]["rootNodeId"],"EL-P02")

    def test_html_is_static_click_to_expand_and_safe(self):
        html=render_tree_html(self.report()["investigationTrees"])
        self.assertEqual(html.count("<details>"),13)
        self.assertIn("<summary>",html)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("ABSTER-SE",html)

    def test_deterministic_trace_verification(self):
        t=self.report()["investigationTrees"]
        self.assertEqual(t,self.report()["investigationTrees"])
        self.assertEqual(verify_trees(t,self.spec,self.report()["cases"]),t)

    def test_forged_root_cause_in_input_rejected(self):
        r=self.report()
        r["cases"][0]["hypotheses"][0]["status"]="confirmed"
        with self.assertRaises(ImportRejected):
            build_trees(self.spec,r["cases"])

    def test_forged_measured_outcome_rejected(self):
        r=self.report()
        r["cases"][0]["qualitativeEvidence"]["comparisons"][0][
            "conditionalObservations"][0]["hasBeenObserved"]=True
        with self.assertRaises(ImportRejected):
            build_trees(self.spec,r["cases"])

    def test_forged_hypothesis_exclusion_rejected(self):
        r=self.report()
        r["cases"][0]["qualitativeEvidence"]["hypothesesExcluded"]=1
        with self.assertRaises(ImportRejected):
            build_trees(self.spec,r["cases"])

    def test_modified_graph_not_accepted_as_source(self):
        r=self.report()
        r["investigationTrees"]["trees"][0]["nodes"][0][
            "conditionalBranches"][0]["observed"]=True
        with self.assertRaises(ImportRejected):
            render_tree_html(r["investigationTrees"])

    def test_modified_checkpoint_not_approved(self):
        r=self.report()
        r["investigationTrees"]["trees"][0]["nodes"][0][
            "reviewCheckpoint"]["oemEffectivityVerified"]=True
        with self.assertRaises(ImportRejected):
            render_tree_html(r["investigationTrees"])

    def test_forged_work_order_denied(self):
        r=self.report()
        r["investigationTrees"]["trees"][0]["mayCreateWorkOrder"]=True
        with self.assertRaises(ImportRejected):
            render_tree_html(r["investigationTrees"])

    def test_spec_misidentifies_selected_root(self):
        r=self.report()
        self.spec["trees"][0]["rootPairId"]="FD-P02"
        with self.assertRaises(ImportRejected):
            validate_spec(self.spec,r["cases"])

    def test_spec_claims_real_data(self):
        r=self.report()
        self.spec["fieldEvidenceAvailable"]=True
        with self.assertRaises(ImportRejected):
            validate_spec(self.spec,r["cases"])

    def test_spec_claims_operational_clearance(self):
        r=self.report()
        self.spec["trees"][1]["canReleaseMachine"]=True
        with self.assertRaises(ImportRejected):
            validate_spec(self.spec,r["cases"])

    def test_reordering_nodes_changes_verified_graph(self):
        r=self.report()
        t=copy.deepcopy(r["investigationTrees"])
        t["trees"][0]["nodes"].reverse()
        with self.assertRaises(ImportRejected):
            verify_trees(t,self.spec,r["cases"])

if __name__=="__main__":
    unittest.main()
