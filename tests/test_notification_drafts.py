"""Ciclo 16: fake maintenance notifications must never become SAP instructions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from connectors.fmea_public import ImportRejected
from methods.library import ROOT, validate_catalog as genuine_catalog
from casefiles.integrated import load_dependencies, build_collection
from notifications.drafts import (SPEC_PATH, build_notifications, validate_spec,
                                   render_html, verify_notifications, main)


class NotificationDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot={"records":[{"id":f"FC-FD-{i:03d}","family":"comando_final",
                                  "confirmedRootCause":False} for i in range(1,5)]}
        with patch("casefiles.integrated.validate_catalog",
                   side_effect=lambda cat,registry,snapshot:
                   genuine_catalog(cat,registry)):
            cls.deps=load_dependencies(cls.snapshot)

    def setUp(self):
        self.deps=copy.deepcopy(type(self).deps)
        self.spec=json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        self.fixtures=json.loads(
            (ROOT/"casefiles/technical-cases.v1.json").read_text(encoding="utf-8"))

    def source(self):
        original=json.loads(
            (ROOT/"examples/777e_additives_only.json").read_text())
        fake={"caseId":original["caseId"],"confirmedRootCause":None,
              "mayReleaseEquipment":False,"mayCreateWorkOrder":False,
              "hypotheses":[{"id":x["hypothesisId"]}
                            for x in self.deps["families"]["final_drive"]["hypotheses"]],
              "plannedInvestigations":[{"status":"not_performed"} for _ in range(8)],
              "decision":"needs_evidence","observations":[],
              "conflicts":[],"knowledgeGaps":[]}
        with patch("casefiles.integrated.build_consumer_index",return_value={}):
            with patch("casefiles.integrated.investigate",return_value=fake):
                return build_collection(self.fixtures,self.deps,self.snapshot)

    def notification(self):
        source=self.source()
        return build_notifications(self.spec,source["cases"],
                                   source["investigationTrees"])

    def reject_spec(self):
        with self.assertRaises(ImportRejected):
            validate_spec(self.spec,self.source()["cases"])

    def test_four_drafts_and_fictional_sap_barrier(self):
        r=self.notification()
        self.assertEqual(r["draftCount"],4)
        self.assertEqual(len(r["drafts"]),4)
        self.assertEqual(r["realNotificationsCreated"],0)
        self.assertEqual(r["workOrdersCreated"],0)
        self.assertFalse(r["mayConnectToSap"])
        self.assertFalse(r["mayReleaseEquipment"])
        for d in r["drafts"]:
            self.assertEqual(d["draftKind"],"training_only_not_sap_importable")
            self.assertTrue(d["title"].startswith("SIMULAÇÃO"))
            self.assertEqual(d["trainingBanner"],
                             "SIMULAÇÃO EDUCACIONAL — NÃO É NOTA OU ORDEM SAP")
            self.assertFalse(d["mayExportToSap"])
            self.assertFalse(d["approvedForMaintenance"])

    def test_four_distinct_domains_have_delimited_scope(self):
        docs=self.notification()["drafts"]
        self.assertEqual([x["planningConstraint"]["discipline"] for x in docs],
                         ["Mecânica / Lubrificação","Mecânica / Hidráulica",
                          "Elétrica / Eletrônica","Elétrica / Eletrônica"])
        self.assertTrue(all(len(x["inspectionScope"]["description"])>80
                            and x["inspectionScope"]["activity"]
                            =="plan_human_investigation_only" for x in docs))
        self.assertEqual(docs[1]["inspectionScope"]["dataState"],"contradicted")
        self.assertEqual(docs[3]["inspectionScope"]["originTreeNodeId"],"EL-P02")

    def test_no_numeric_planning_or_machine_identifier(self):
        for d in self.notification()["drafts"]:
            p=d["planningConstraint"]
            for key in ("workHours","oemPressureOrWearLimits","cost",
                        "numericPriority","equipmentSerial","sapEquipmentNumber",
                        "sapNotificationNumber"):
                self.assertIsNone(p[key])
            self.assertEqual(p["materials"],[])
            self.assertEqual(p["executionProcedures"],[])
            self.assertFalse(d["symptom"]["physicallyObserved"])
            self.assertFalse(d["postponementRisk"]["fieldRiskAssessed"])
            self.assertIsNone(d["postponementRisk"]["quantifiedRisk"])
            self.assertFalse(d["postponementRisk"]["continuedOperationApproved"])

    def test_all_hypotheses_remain_open_and_trace_to_tree(self):
        src=self.source()
        res=build_notifications(self.spec,src["cases"],src["investigationTrees"])
        for case,tree,d in zip(src["cases"],src["investigationTrees"]["trees"],res["drafts"]):
            self.assertEqual(d["hypothesisRegister"]["hypothesisIds"],
                             tree["unresolvedHypothesisSet"]["hypothesisIds"])
            self.assertTrue(d["hypothesisRegister"]["allOpen"])
            self.assertFalse(d["hypothesisRegister"]["probabilitiesAssigned"])
            self.assertEqual(d["hypothesisRegister"]["excludedCount"],0)
            self.assertEqual(d["inspectionScope"]["originTreeNodeId"],tree["rootNodeId"])
            self.assertEqual(d["causalAssessment"]["rootCauseStatus"],
                             "unknown_not_established")
            self.assertIsNone(d["causalAssessment"]["confirmedDefect"])
            self.assertEqual(d["provenance"]["sourceTreeQuestionId"],tree["rootNodeId"])
            self.assertEqual(d["provenance"]["casefileBenchmarkFixtureId"],
                             case["provenance"]["caseBenchmarkFixtureId"])

    def test_documents_have_human_and_oem_gates_pending(self):
        for d in self.notification()["drafts"]:
            self.assertEqual(len(d["reviewGates"]),9)
            self.assertTrue(all(value is False for value in d["reviewGates"].values()))
            self.assertTrue(d["planningConstraint"]["externalHumanApprovalRequired"])
            self.assertTrue(d["planningConstraint"]["externalSafetyReviewRequired"])
            self.assertTrue(d["inspectionScope"]["requiresOemMethodReview"])
            self.assertEqual(d["requestedEvidence"]["presentMeasurementCount"],0)
            self.assertEqual(d["requestedEvidence"]["externalOriginalEvidenceReferences"],[])

    def test_json_is_reproducible_and_verifiable(self):
        src=self.source()
        value=build_notifications(self.spec,src["cases"],src["investigationTrees"])
        self.assertEqual(value,build_notifications(self.spec,src["cases"],
                                                   src["investigationTrees"]))
        self.assertEqual(verify_notifications(value,self.spec,src["cases"],
                                              src["investigationTrees"]),value)

    def test_html_is_static_and_escaped(self):
        html=render_html(self.notification())
        self.assertEqual(html.count("<section>"),4)
        self.assertIn("Content-Security-Policy",html)
        self.assertNotIn("<script",html)
        self.assertNotIn("<form",html)
        self.assertIn("não registrar no SAP",html)

    def test_html_escapes_text(self):
        r=self.notification()
        r["drafts"][0]["symptom"]["description"]="<script>alert(1)</script>"
        html=render_html(r)
        self.assertNotIn("<script>",html)
        self.assertIn("&lt;script&gt;",html)

    def test_duplicate_draft_id_rejected(self):
        self.spec["entries"][1]["draftId"]="SIM-NOTE-001"
        self.reject_spec()

    def test_false_real_notification_permission_rejected(self):
        self.spec["entries"][0]["mayIssueRealNotification"]=True
        self.reject_spec()

    def test_missing_one_case_rejected(self):
        self.spec["entries"].pop()
        self.reject_spec()

    def test_fabricated_execution_claim_in_spec_rejected(self):
        self.spec["entries"][1]["actionPerformed"]=True
        self.reject_spec()

    def test_real_field_observation_in_spec_rejected(self):
        self.spec["entries"][2]["fieldObserved"]=True
        self.reject_spec()

    def test_unreviewed_procedure_in_spec_rejected(self):
        self.spec["entries"][0]["executionProcedure"]="remove bearing"
        self.reject_spec()

    def test_false_sap_integration_in_spec_rejected(self):
        self.spec["sapIntegrationEnabled"]=True
        self.reject_spec()

    def test_unknown_real_case_identity_rejected(self):
        self.spec["entries"][0]["caseFileId"]="REAL-MINE-IDENTIFIER"
        self.reject_spec()

    def test_unapproved_planning_discipline_rejected(self):
        self.spec["entries"][0]["discipline"]="Operador SAP"
        self.reject_spec()

    def test_missing_educational_banner_rejected(self):
        self.spec["entries"][0]["title"]="SUBSTITUIR REDUTOR"
        self.reject_spec()

    def test_forged_root_cause_rejected(self):
        s=self.source()
        s["cases"][0]["causalLevels"]["rootCauseEstablished"]=True
        with self.assertRaises(ImportRejected):
            build_notifications(self.spec,s["cases"],s["investigationTrees"])

    def test_forged_oem_effectivity_rejected(self):
        s=self.source()
        s["cases"][0]["assetContext"]["oemEffectivityVerified"]=True
        with self.assertRaises(ImportRejected):
            build_notifications(self.spec,s["cases"],s["investigationTrees"])

    def test_fabricated_serial_rejected(self):
        s=self.source()
        s["cases"][0]["assetContext"]["realMachineIdentifier"]="777-001"
        with self.assertRaises(ImportRejected):
            build_notifications(self.spec,s["cases"],s["investigationTrees"])

    def test_fabricated_probability_rejected(self):
        s=self.source()
        s["cases"][1]["hypotheses"][0]["probability"]=0.85
        with self.assertRaises(ImportRejected):
            build_notifications(self.spec,s["cases"],s["investigationTrees"])

    def test_legacy_tree_with_execution_rejected(self):
        s=self.source()
        s["investigationTrees"]["trees"][0]["mayCreateWorkOrder"]=True
        with self.assertRaises(ImportRejected):
            build_notifications(self.spec,s["cases"],s["investigationTrees"])

    def test_tree_with_open_hypotheses_removed_rejected(self):
        s=self.source()
        s["investigationTrees"]["trees"][0]["unresolvedHypothesisSet"]["allOpen"]=False
        with self.assertRaises(ImportRejected):
            build_notifications(self.spec,s["cases"],s["investigationTrees"])

    def test_html_forged_sap_document_number_rejected(self):
        r=self.notification()
        r["drafts"][0]["planningConstraint"]["sapNotificationNumber"]="1234"
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_fake_material_purchase_rejected(self):
        r=self.notification()
        r["drafts"][0]["planningConstraint"]["materials"]=["final-drive"]
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_authorized_spare_part_replacement_rejected(self):
        r=self.notification()
        r["drafts"][0]["reviewGates"]["mayOrderParts"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_fake_time_budget_rejected(self):
        r=self.notification()
        r["drafts"][0]["planningConstraint"]["workHours"]=4
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_html_false_released_operation_rejected(self):
        r=self.notification()
        r["mayReleaseEquipment"]=True
        with self.assertRaises(ImportRejected):
            render_html(r)

    def test_altered_root_link_rejected_by_verifier(self):
        s=self.source()
        r=build_notifications(self.spec,s["cases"],s["investigationTrees"])
        r["drafts"][2]["inspectionScope"]["originTreeNodeId"]="EL-P03"
        with self.assertRaises(ImportRejected):
            verify_notifications(r,self.spec,s["cases"],s["investigationTrees"])

    def test_cli_rejects_untrusted_source_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.json"
            lock=Path(tmp)/"snapshot.json"
            out=Path(tmp)/"output.html"
            canonical=self.source()
            changed=copy.deepcopy(canonical)
            changed["cases"][0]["assetContext"]["realMachineIdentifier"]="PRIVATE-007"
            p.write_text(json.dumps(changed))
            lock.write_bytes(b"MOCK-ONLY-NOT-A-FMEA-SNAPSHOT")
            with (patch("notifications.drafts.validate_snapshot",
                        return_value=self.snapshot),
                  patch("notifications.drafts.load_dependencies",
                        return_value=self.deps),
                  patch("notifications.drafts.build_collection",
                        return_value=canonical),
                  patch("sys.stderr")):
                result=main(["--source",str(p),"--snapshot",str(lock),
                             "--html",str(out)])
            self.assertEqual(result,2)
            self.assertFalse(out.exists())

    def test_cli_rejects_unreviewed_editorial_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"source.json"
            spec=Path(tmp)/"spec.json"
            lock=Path(tmp)/"snapshot.json"
            out=Path(tmp)/"output.json"
            canonical=self.source()
            src.write_text(json.dumps(canonical))
            changed=copy.deepcopy(self.spec)
            changed["entries"][0]["investigationScope"] += " Confirmar peça danificada."
            spec.write_text(json.dumps(changed))
            lock.write_bytes(b"MOCK-ONLY-NOT-A-FMEA-SNAPSHOT")
            with (patch("notifications.drafts.validate_snapshot",
                        return_value=self.snapshot),
                  patch("notifications.drafts.load_dependencies",
                        return_value=self.deps),
                  patch("notifications.drafts.build_collection",
                        return_value=canonical),
                  patch("sys.stderr")):
                result=main(["--source",str(src),"--spec",str(spec),
                             "--snapshot",str(lock),"--output",str(out)])
            self.assertEqual(result,2)
            self.assertFalse(out.exists())

    def test_cli_writes_documents_for_canonical_public_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"source.json"
            lock=Path(tmp)/"snapshot.json"
            out=Path(tmp)/"output.json"
            html=Path(tmp)/"notes.html"
            canonical=self.source()
            src.write_text(json.dumps(canonical))
            lock.write_bytes(b"MOCK-ONLY-NOT-A-FMEA-SNAPSHOT")
            with (patch("notifications.drafts.validate_snapshot",
                        return_value=self.snapshot),
                  patch("notifications.drafts.load_dependencies",
                        return_value=self.deps),
                  patch("notifications.drafts.build_collection",
                        return_value=canonical),
                  patch("builtins.print")):
                result=main(["--source",str(src),"--snapshot",str(lock),
                             "--output",str(out),"--html",str(html)])
            self.assertEqual(result,0)
            self.assertTrue(out.is_file())
            self.assertTrue(html.is_file())
            self.assertEqual(json.loads(out.read_text())["draftCount"],4)


if __name__=="__main__":
    unittest.main()
