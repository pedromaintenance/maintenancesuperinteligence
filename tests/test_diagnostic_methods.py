"""Ciclo 05: catálogo e métodos diagnósticos — invariantes adversariais."""
import copy
import json
from pathlib import Path
import unittest

from connectors.fmea_public import ImportRejected
from methods.library import (ROOT, build_method_plan, validate_catalog,
                             validate_sources, DOMAIN_MINIMUM)

DEMO_FMEA = [
    ("FC-FD-001", [("I1", "EV-11", "Comparar depósito magnético"),
                   ("I2", "EV-08", "Confrontar fluido e histórico")]),
    ("FC-FD-002", [("I1", "EV-10", "Confirmar presença de água"),
                   ("I2", "EV-01", "Inspecionar caminhos de ingresso")]),
    ("FC-FD-003", [("I1", "EV-13", "Reconciliar produto"),
                   ("I2", "EV-08", "Comparar viscosidade")]),
    ("FC-FD-004", [("I1", "EV-11", "Inspecionar fragmentos"),
                   ("I2", "EV-04", "Examinar ruído/vibração")]),
]


def synthetic_fmea():
    return {"records": [
        {"id": rid, "investigations": [
            {"id": iid, "methodId": method_id,
             "purpose": purpose, "status": "not_performed"}
            for iid, method_id, purpose in pairs]}
        for rid, pairs in DEMO_FMEA]}


def synthetic_report():
    fmea = synthetic_fmea()
    return {"caseId": "SIM-777E-TEST",
            "provenance": {"fmeaInputSha256": "a" * 64},
            "plannedInvestigations": [
                {"referenceFmeaId": record["id"],
                 "methodId": item["methodId"],
                 "purposeFromSource": item["purpose"],
                 "status": "not_performed"}
                for record in fmea["records"]
                for item in record["investigations"]]}


class DiagnosticMethodsTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "methods/catalog.v1.json").read_text())
        self.registry = json.loads(
            (ROOT / "data/diagnostic-method-sources.v1.json").read_text())
        self.sources = validate_sources(self.registry)
        self.methods = validate_catalog(self.data, self.sources)
        self.case = {"caseId": "SIM-777E-TEST"}
        self.report = synthetic_report()
        self.fmea = synthetic_fmea()

    def reject_catalog(self, part):
        with self.assertRaises(ImportRejected) as caught:
            validate_catalog(self.data, self.sources)
        self.assertIn(part, str(caught.exception))

    def test_five_domain_coverage(self):
        from collections import Counter
        self.assertEqual(dict(Counter(x["domain"] for x in self.methods.values())),
                         DOMAIN_MINIMUM)
        self.assertEqual(len(self.methods), 14)

    def test_six_fmea_codes_have_unique_methods(self):
        ids = {m["fmeaMethodId"] for m in self.methods.values()
               if m["fmeaMethodId"] is not None}
        self.assertEqual(ids, {"EV-11", "EV-08", "EV-10", "EV-01", "EV-13", "EV-04"})

    def test_eight_linked_fmea_investigations(self):
        out = build_method_plan(self.case, self.report, self.fmea,
                                self.methods, self.sources)
        self.assertEqual(out["fmeaInvestigationsLinked"], 8)
        self.assertEqual(out["methodsCataloged"], 14)
        self.assertEqual(out["fmeaMethodsLinked"], 6)
        self.assertFalse(out["mayExecuteTests"])
        self.assertTrue(all(x["executionStatus"] == "proposed_not_executed"
                            for x in out["suggestedQuestions"]))
        self.assertTrue(all(x["oemApplicability"] == "not_verified"
                            for x in out["suggestedQuestions"]))
        self.assertTrue(all(x["expectedObservationFields"]
                            for x in out["suggestedQuestions"]))

    def test_no_methods_are_oem_approved(self):
        self.assertTrue(all(m["thresholds"] is None and
                            m["parameterValues"] is None and
                            m["applicabilityGate"]["manufacturer"] is None
                            and m["executionStatus"] == "proposed_not_executed"
                            for m in self.methods.values()))

    def test_reject_missing_source_reference(self):
        self.data["methods"][0]["sourceIds"] = ["PRIVATE-SAP-OS"]
        self.reject_catalog("source not registered")

    def test_reject_false_oem_applicability(self):
        self.data["methods"][0]["applicabilityGate"]["serialOrArrangement"] = "SIM-ARR"
        self.reject_catalog("model/serial/operational approval not verified")

    def test_reject_executed_method(self):
        self.data["methods"][0]["executionStatus"] = "performed"
        self.reject_catalog("execution/threshold/authority not allowed")

    def test_reject_unsupported_external_source(self):
        self.registry["sources"][0]["url"] = "http://source.example.com"
        with self.assertRaisesRegex(ImportRejected, "source not public"):
            validate_sources(self.registry)

    def test_reject_fmea_missing_from_catalog(self):
        self.data["methods"][0]["fmeaMethodId"] = "EV-99"
        self.reject_catalog("unauthorized FMEA method code")

    def test_reject_tampered_fmea_purpose(self):
        report = copy.deepcopy(self.report)
        report["plannedInvestigations"][0]["purposeFromSource"] = "CONFIRM ROLAMENTO"
        with self.assertRaisesRegex(ImportRejected, "purpose or status changed"):
            build_method_plan(self.case, report, self.fmea,
                              self.methods, self.sources)

    def test_reject_synthetic_fmea_test_marked_done(self):
        record = self.fmea["records"][0]["investigations"][0]
        record["status"] = "performed"
        with self.assertRaisesRegex(ImportRejected, "purpose or status changed"):
            build_method_plan(self.case, self.report, self.fmea,
                              self.methods, self.sources)

    def test_reject_case_mismatch(self):
        self.case["caseId"] = "SIM-OTHER"
        with self.assertRaisesRegex(ImportRejected, "do not match"):
            build_method_plan(self.case, self.report, self.fmea,
                              self.methods, self.sources)

    def test_each_discipline_two_adversaries(self):
        """Dois gates negativos por disciplina: falsa medição e perda de segurança."""
        for domain in DOMAIN_MINIMUM:
            with self.subTest(domain=domain, mutation="measurement"):
                edited = copy.deepcopy(self.data)
                m = next(x for x in edited["methods"] if x["domain"] == domain)
                m["expectedObservations"][0]["nature"] = "measured"
                with self.assertRaisesRegex(ImportRejected, "masquerading as proposal"):
                    validate_catalog(edited, self.sources)
            with self.subTest(domain=domain, mutation="safety"):
                edited = copy.deepcopy(self.data)
                m = next(x for x in edited["methods"] if x["domain"] == domain)
                m["safetyGates"] = m["safetyGates"][1:]
                with self.assertRaisesRegex(ImportRejected, "safety prerequirements"):
                    validate_catalog(edited, self.sources)

    def test_each_discipline_rejects_oem_threshold(self):
        for domain in DOMAIN_MINIMUM:
            with self.subTest(domain=domain):
                edited = copy.deepcopy(self.data)
                m = next(x for x in edited["methods"] if x["domain"] == domain)
                m["thresholds"] = {"maxPressure": 420}
                with self.assertRaisesRegex(ImportRejected, "execution/threshold/authority"):
                    validate_catalog(edited, self.sources)

    def test_each_discipline_rejects_confident_conclusion(self):
        for domain in DOMAIN_MINIMUM:
            with self.subTest(domain=domain):
                edited = copy.deepcopy(self.data)
                m = next(x for x in edited["methods"] if x["domain"] == domain)
                m["interpretationLimits"][0]["permittedInference"] = "confirmed_root_cause"
                with self.assertRaisesRegex(ImportRejected, "unsupported certainty"):
                    validate_catalog(edited, self.sources)

    def test_reject_invented_oem_brochure(self):
        self.data["methods"][0]["applicabilityGate"]["technicalPublication"] = "OEM-MANUAL"
        self.reject_catalog("model/serial/operational approval not verified")

    def test_reject_claimed_review(self):
        self.data["methods"][0]["reviewStatus"] = "reviewed_oem_777e"
        self.reject_catalog("execution/threshold/authority not allowed")


if __name__ == "__main__":
    unittest.main()
