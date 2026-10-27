"""Cycle 23 — 100 synthetic roots/pairs/changes and independent path oracle."""
import copy
import json
from pathlib import Path
import tempfile
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
from pilot.evidence_contradictions import FIXTURE_PATH as CONFLICT_SPEC,build_report as build_conflict
from pilot.reopen_coverage import (SPEC_PATH,build_report,validate_spec,independent_oracle,
                                   _enumerate_simple_paths,_mutation_checks,render_html,
                                   verify_report,main,IDS)

class ReopenCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                              "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,registry,snap:validate_catalog(cat,registry)):
            deps=load_dependencies(snapshot)
        raw=json.loads((ROOT/"examples/777e_additives_only.json").read_text())
        mock={"caseId":raw["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":h["hypothesisId"]} for h in deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],"conflicts":[],"knowledgeGaps":[]}
        with (patch("casefiles.integrated.build_consumer_index",return_value={}),
              patch("casefiles.integrated.investigate",return_value=mock)):
            cases=build_collection(json.loads((ROOT/"casefiles/technical-cases.v1.json").read_text()),deps,snapshot)
        notes=build_notifications(json.loads(NOTES_SPEC.read_text()),cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,json.loads(RUBRIC_PATH.read_text()),json.loads(ORACLE_PATH.read_text()))
        editorial=build_editorial(json.loads(EDIT_SPEC.read_text()),quality,notes)
        ready=build_readiness(json.loads(READY_SPEC.read_text()),editorial)
        gng=build_gng(json.loads(PACKAGE_PATH.read_text()),ready)
        seq=build_seq(json.loads(SEQ_SPEC.read_text()),gng)
        contradictions=build_conflict(json.loads(CONFLICT_SPEC.read_text()),seq,gng)
        cls.original=(gng,seq,contradictions)

    def setUp(self):
        self.gng,self.seq,self.conf=copy.deepcopy(type(self).original)
        self.spec=json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def result(self):
        return build_report(self.spec,self.conf,self.seq,self.gng)

    def assert_rejected(self):
        with self.assertRaises(ImportRejected):
            self.result()

    def test_hundred_cases_breakdown_and_no_go(self):
        r=self.result()
        self.assertEqual(r["scenarioCount"],100)
        self.assertEqual([r[k] for k in ("singleRootCount","pairCount","triggerCount","conflictCount")],
                         [13,78,3,6])
        self.assertEqual(r["controlCount"],13)
        self.assertEqual(r["edgeCount"],17)
        self.assertEqual(r["decision"],"no_go")
        self.assertEqual(r["verifiedExternalHumanReviews"],0)
        self.assertEqual(r["physicalFailuresVerified"],0)
        self.assertEqual(r["unverifiedEvidenceCount"],13)
        for attr in ("realPilotApproved","mayTransmitSap","mayModifyEcm",
                     "mayCreateWorkOrder","mayReleaseEquipment"):
            self.assertFalse(r[attr])

    def test_every_control_as_single_root_exact_closure(self):
        r=self.result()
        self.assertEqual([c["rootControlIds"][0] for c in r["coverageCases"][:13]],
                         list(IDS))
        for item in r["coverageCases"][:13]:
            affected,unaffected,metrics=independent_oracle(item["rootControlIds"],DEPENDENCIES)
            self.assertEqual(item["affectedControlIds"],affected)
            self.assertEqual(item["unaffectedControlIds"],unaffected)
            self.assertIn(item["rootControlIds"][0],affected)
            self.assertEqual(item["coveredControlCount"],13)

    def test_all_seventy_eight_distinct_unordered_pairs(self):
        r=self.result()
        pairs=[tuple(x["rootControlIds"]) for x in r["coverageCases"][13:91]]
        self.assertEqual(len(pairs),78)
        self.assertEqual(len(set(pairs)),78)
        self.assertTrue(all(len(p)==2 and p[0]!=p[1] for p in pairs))

    def test_triggers_and_conflicts_retained(self):
        r=self.result()
        self.assertEqual([c["syntheticTrigger"] for c in r["coverageCases"][91:94]],
                         ["revoked_identity","oem_revision_changed",
                          "machine_configuration_changed"])
        self.assertEqual([c["caseKind"] for c in r["coverageCases"][94:]],
                         ["conflict_pair"]*6)
        for a,b in zip(r["coverageCases"][94:],self.conf["scenarios"]):
            self.assertEqual(a["rootControlIds"],b["sourceControls"])
            self.assertEqual(a["syntheticTrigger"],b["conflictMechanism"])

    def test_each_node_has_valid_explanation_path_and_edge_reason(self):
        for case in self.result()["coverageCases"]:
            self.assertEqual(case["coveredControlCount"],13)
            self.assertEqual(case["affectedCount"]+case["unaffectedCount"],13)
            for witness in case["pathExplanations"]:
                p=witness["selectedPath"]
                self.assertIn(p[0],case["rootControlIds"])
                self.assertEqual(p[-1],witness["targetControlId"])
                self.assertEqual(witness["stepCount"],len(p)-1)
                self.assertFalse(witness["physicalFaultConfirmed"])
                self.assertFalse(witness["evidenceActuallyVerified"])
                for step in witness["explanationSteps"]:
                    self.assertIn(step["upstreamControlId"],
                                  DEPENDENCIES[step["downstreamControlId"]])
                    self.assertFalse(step["physicalMechanismClaimed"])
            for unattainable in case["unreachableControlWitnesses"]:
                self.assertNotIn(unattainable["targetControlId"],case["affectedControlIds"])
                self.assertFalse(unattainable["physicalSafetyEstablished"])
                self.assertFalse(unattainable["maySkipExternalReview"])

    def test_independent_oracle_agrees_with_dfs_for_100_cases(self):
        for case in self.result()["coverageCases"]:
            roots=case["rootControlIds"]
            affected,unaffected,metrics=independent_oracle(roots,DEPENDENCIES)
            self.assertEqual(affected,case["affectedControlIds"])
            self.assertEqual(unaffected,case["unaffectedControlIds"])
            for target in affected:
                paths=_enumerate_simple_paths(roots,DEPENDENCIES,target)
                self.assertEqual(len(paths),metrics[target]["possiblePathCount"])
                self.assertEqual(len(paths[0])-1,metrics[target]["minimumSteps"])

    def test_alternative_path_has_distinct_valid_edges(self):
        r=self.result()
        redundant=[x for c in r["coverageCases"] for x in c["pathExplanations"]
                   if x["alternativePathCount"]>0]
        self.assertTrue(redundant)
        for p in redundant:
            alternate=p["alternativePathWitness"]
            self.assertIsNotNone(alternate)
            self.assertNotEqual(alternate,p["selectedPath"])
            for a,b in zip(alternate,alternate[1:]):
                self.assertIn(a,DEPENDENCIES[b])

    def test_unreachable_does_not_mean_safe(self):
        witnesses=[x for c in self.result()["coverageCases"]
                   for x in c["unreachableControlWitnesses"]]
        self.assertTrue(len(witnesses)>0)
        self.assertTrue(all(x["reason"]=="no_directed_documentary_dependency_path"
                            and not x["physicalSafetyEstablished"]
                            and not x["maySkipExternalReview"] for x in witnesses))

    def test_graph_mutations_all_rejected(self):
        x=self.result()["graphMutationChecks"]
        self.assertEqual([m["mutationType"] for m in x],[
            "edge_removed","edge_reversed","edge_added",
            "threat_removed","closure_forged"])
        self.assertEqual(len(x),5)
        self.assertTrue(all(m["mutatedInputRejected"] and m["canonicalGraphUnchanged"]
                            and not m["operationalAuthorityGranted"] for m in x))

    def test_five_cross_functional_owners_are_unverified(self):
        r=self.result()["crossFunctionalReview"]
        self.assertEqual([c["owner"] for c in r],[
            "IT","InformationSecurity","Engineering","Legal","MaintenanceManagement"])
        self.assertTrue(all(c["controlsOwned"] and not c["authenticatedSignoffReceived"]
                            and not c["externalTechnicalReviewPerformed"] for c in r))

    def test_sha_recomputation_rejects_forged_path(self):
        r=self.result()
        self.assertEqual(verify_report(r,self.spec,self.conf,self.seq,self.gng),r)
        r["coverageCases"][0]["pathExplanations"][0]["selectedPath"].append("oem-effectivity")
        with self.assertRaises(ImportRejected):
            verify_report(r,self.spec,self.conf,self.seq,self.gng)

    def test_sha_recomputation_rejects_forged_unreachable_witness(self):
        r=self.result()
        r["coverageCases"][0]["unreachableControlWitnesses"][0]["physicalSafetyEstablished"]=True
        with self.assertRaises(ImportRejected):
            verify_report(r,self.spec,self.conf,self.seq,self.gng)

    def test_sha_recomputation_rejects_forged_mutation_status(self):
        r=self.result()
        r["graphMutationChecks"][2]["mutatedInputRejected"]=False
        with self.assertRaises(ImportRejected):
            verify_report(r,self.spec,self.conf,self.seq,self.gng)

    def test_html_offline_summary_and_escaped_text(self):
        r=self.result()
        html=render_html(r)
        self.assertEqual(html.count("<details>"),19)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        r["coverageCases"][0]["caseId"]="<script>inert</script>"
        self.assertIn("&lt;script&gt;",render_html(r))

    def test_html_rejects_real_operational_status(self):
        r=self.result()
        r["mayTransmitSap"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_rejects_physical_fault_claim(self):
        r=self.result()
        r["coverageCases"][0]["pathExplanations"][0]["physicalFaultConfirmed"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_refuse_missing_edge_from_spec(self):
        self.spec["graphEdges"].pop()
        self.assert_rejected()

    def test_refuse_reversed_edge_from_spec(self):
        self.spec["graphEdges"][0]["source"],self.spec["graphEdges"][0]["target"]=(
            self.spec["graphEdges"][0]["target"],self.spec["graphEdges"][0]["source"])
        self.assert_rejected()

    def test_refuse_spurious_edge_in_spec(self):
        self.spec["graphEdges"].append({"source":"oem-effectivity","target":"identity-proof"})
        self.assert_rejected()

    def test_refuse_missing_single_root_case(self):
        self.spec["cases"].pop(0)
        self.assert_rejected()

    def test_refuse_missing_pair_case(self):
        self.spec["cases"].pop(13)
        self.assert_rejected()

    def test_refuse_wrong_oracle_closure(self):
        self.spec["cases"][0]["expectedAffectedControlIds"].pop()
        self.assert_rejected()

    def test_refuse_wrong_path_count(self):
        c=self.spec["cases"][0]
        k=next(iter(c["expectedPathMetrics"]))
        c["expectedPathMetrics"][k]["possiblePathCount"]+=1
        self.assert_rejected()

    def test_refuse_wrong_minimum_distance(self):
        c=self.spec["cases"][0]
        k=next(iter(c["expectedPathMetrics"]))
        c["expectedPathMetrics"][k]["minimumSteps"]+=1
        self.assert_rejected()

    def test_refuse_fake_field_evidence(self):
        self.spec["cases"][0]["fieldObserved"]=True
        self.assert_rejected()

    def test_refuse_fake_human_approval(self):
        self.spec["cases"][0]["externalApproval"]=True
        self.assert_rejected()

    def test_refuse_fake_oem_operational_release(self):
        self.spec["policy"]["mayReleaseEquipment"]=True
        self.assert_rejected()

    def test_refuse_a_missing_mutation(self):
        self.spec["mutations"].pop()
        self.assert_rejected()

    def test_refuse_omitted_cross_review_owner(self):
        self.spec["crossReview"].pop()
        self.assert_rejected()

    def test_refuse_fake_real_cross_review(self):
        self.spec["crossReview"][0]["authenticHumanReview"]=True
        self.assert_rejected()

    def test_refuse_missing_conflict_source(self):
        self.conf["scenarios"].pop()
        self.assert_rejected()

    def test_refuse_false_upstream_evidence(self):
        self.seq["verifiedEvidenceCount"]=1
        self.assert_rejected()

    def test_refuse_modified_upstream_control_dependency(self):
        self.gng["approvalDependencies"][3]["predecessors"].pop()
        self.assert_rejected()

    def test_deterministic_reconstruction(self):
        self.assertEqual(self.result(),self.result())

if __name__=="__main__":
    unittest.main()
