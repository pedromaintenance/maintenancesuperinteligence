"""Testes locais sintéticos; nao inferem acuracia diagnóstica do FMEA."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from connectors.fmea_public import (
    ImportRejected, build_consumer_index, build_receipt,
    load_lock, pinned_url, validate_snapshot
)


def fake_source():
    return {
        "id": "SRC-A", "title": "Referência didática de teste",
        "organization": "Exemplo sintético", "url": "https://example.org/sample",
        "role": "synthetic", "limitation": "Nao é fonte OEM",
    }


def fake_record():
    return {
        "id": "FC-TEST-001", "title": "Somente um experimento sintético",
        "family": "hydraulic", "operatingFunction": "Conter fluido",
        "functionalFailureId": "FF-TEST",
        "failureMode": "Perda de estanqueidade potencial",
        "mechanismIds": ["ME-TEST"], "sourceIds": ["SRC-A"],
        "causalLevels": {
            "observedPhenomenon": "Possivel manifestacao de perda",
            "immediatePhysicalMechanismCandidate": "Vedacao pode perder capacidade",
            "contributingConditionCandidates": ["Variacao de carga"],
            "rootCauseCandidates": ["Fator ainda nao demonstrado"],
            "rootCauseNotEstablishedBecause": "Nao ha ensaio nem evento real"
        },
        "localEffect": {"description": "Efeito local possivel", "status": "possible_unobserved"},
        "systemEffect": {"description": "Efeito geral possivel", "status": "possible_unobserved"},
        "competingHypotheses": [
            {"id": "ALT1", "description": "Condicao A", "discriminator": "Teste A"},
            {"id": "ALT2", "description": "Condicao B", "discriminator": "Teste B"}
        ],
        "investigations": [
            {"id": "I1", "methodId": "EV-01", "purpose": "Inspeção segura proposta", "status": "not_performed"},
            {"id": "I2", "methodId": "EV-02", "purpose": "Teste adicional proposto", "status": "not_performed"}
        ],
        "applicability": {"modelId": None, "locationId": None, "serialOrArrangement": None},
        "reviewStatus": "inferido_com_literatura_geral", "nature": "hypothesis_not_event",
        "confirmedRootCause": False, "empiricalOccurrences": 0,
    }


def fake_snapshot():
    return {
        "schema": "fmea-mining.public-knowledge-preview.v1", "version": "1.3.12",
        "contentStatus": "conceptual_inferred_unvalidated",
        "approvedForOperationalUse": False,
        "recordNature": "hypotheses_only",
        "sourceScope": "general_principles_not_serial_effective",
        "warnings": ["Nao executado", "Nao OEM", "Nao operacional"],
        "counts": {"causalChains": 1, "sources": 1, "confirmedRootCauses": 0, "empiricalOccurrences": 0},
        "records": [fake_record()], "sources": [fake_source()],
    }


def serialize(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


class ImporterAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.data = fake_snapshot()
        self.lock = copy.deepcopy(load_lock())
        self.lock["recordCount"] = 1
        self.lock["sourceCount"] = 1

    def _validate(self, data=None, lock=None):
        data = self.data if data is None else data
        lock = copy.deepcopy(self.lock if lock is None else lock)
        raw = serialize(data)
        lock["sha256"] = hashlib.sha256(raw).hexdigest()
        return validate_snapshot(raw, lock)

    def _reject(self, snippet):
        with self.assertRaises(ImportRejected) as caught:
            self._validate()
        self.assertIn(snippet, str(caught.exception))

    def test_pinned_producer(self):
        self.assertEqual(pinned_url(self.lock), (
            "https://raw.githubusercontent.com/pedromaintenance/fmea-database-mining/"
            "06541f688773f101e586cceed848d0140e73ba09/"
            "data/governance/snapshots/public-knowledge.content-1.0.0.json"
        ))

    def test_baseline_is_valid_only_as_inferred(self):
        result = self._validate()
        self.assertEqual(len(result["records"]), 1)
        index = build_consumer_index(result, self.lock)
        self.assertFalse(index["approvedForOperationalUse"])
        self.assertFalse(index["records"][0]["confirmedRootCause"])
        self.assertEqual(index["records"][0]["plannedInvestigations"][0]["status"], "not_performed")
        receipt = build_receipt(result, self.lock)
        self.assertEqual(receipt["result"], "accepted_read_only_hypotheses")
        self.assertEqual(receipt["familyCoverage"], {"hydraulic": 1})

    def test_corrupted_hash_is_rejected_before_parsing(self):
        with self.assertRaisesRegex(ImportRejected, "SHA-256 divergente"):
            validate_snapshot(serialize(self.data), self.lock)

    def test_injected_record_field_is_rejected(self):
        self.data["records"][0]["approvedForOperationalUse"] = True
        self._reject("campos divergentes")

    def test_extra_top_level_field_is_rejected(self):
        self.data["confidentialCorporateOrder"] = "FAKE-OS"
        self._reject("campos divergentes")

    def test_missing_source_is_rejected(self):
        self.data["records"][0]["sourceIds"] = ["MISSING"]
        self._reject("fonte nao encontrada")

    def test_source_http_is_rejected(self):
        self.data["sources"][0]["url"] = "http://insecure.example.org"
        self._reject("URL externa invalida")

    def test_duplicate_chain_is_rejected(self):
        self.data["records"].append(copy.deepcopy(self.data["records"][0]))
        self.data["counts"]["causalChains"] = 2
        self.lock["recordCount"] = 2
        self._reject("ID duplicado")

    def test_root_cause_is_not_confirmed(self):
        self.data["records"][0]["confirmedRootCause"] = True
        self._reject("causa raiz indevidamente confirmada")

    def test_empirical_occurrence_is_not_allowed(self):
        self.data["records"][0]["empiricalOccurrences"] = 1
        self._reject("ocorrencia empirica indevida")

    def test_event_is_not_accepted_as_hypothesis(self):
        self.data["records"][0]["nature"] = "event_observed"
        self._reject("simulacao apresentada como evento")

    def test_effect_is_not_promoted(self):
        self.data["records"][0]["systemEffect"]["status"] = "measured"
        self._reject("efeito nao observado")

    def test_test_is_not_marked_performed(self):
        self.data["records"][0]["investigations"][0]["status"] = "performed"
        self._reject("teste simulado como executado")

    def test_serial_cannot_be_assumed(self):
        self.data["records"][0]["applicability"]["serialOrArrangement"] = "fictional serial"
        self._reject("aplicabilidade por modelo/serie nao comprovada")

    def test_no_approval_in_snapshot(self):
        self.data["approvedForOperationalUse"] = True
        self._reject("tenta aprovar uso operacional")

    def test_review_status_must_remain_inferred(self):
        self.data["records"][0]["reviewStatus"] = "validated"
        self._reject("status passou a aprovado")

    def test_competing_hypotheses_required(self):
        self.data["records"][0]["competingHypotheses"] = [self.data["records"][0]["competingHypotheses"][0]]
        self._reject("faltam alternativas concorrentes")

    def test_proposed_investigations_required(self):
        self.data["records"][0]["investigations"] = [self.data["records"][0]["investigations"][0]]
        self._reject("faltam testes complementares")

    def test_unknown_extra_effect_field_rejected(self):
        self.data["records"][0]["localEffect"]["measuredValue"] = 42
        self._reject("campos divergentes")

    def test_inconsistent_counts_rejected(self):
        self.data["counts"]["confirmedRootCauses"] = 1
        self._reject("root causes nao podem ser confirmadas")

    def test_orphan_sources_rejected(self):
        self.data["sources"].append({"id": "SRC-B", "title": "Orfã", "organization": "Sintética",
                                     "url": "https://example.org/orphan", "role": None,
                                     "limitation": None})
        self.data["counts"]["sources"] = 2
        self.lock["sourceCount"] = 2
        self._reject("fontes orfas")

    def test_unknown_source_lock_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = copy.deepcopy(load_lock())
            lock["producerCommit"] = "main"
            path = Path(tmp) / "lock.json"
            path.write_text(json.dumps(lock), encoding="utf-8")
            with self.assertRaisesRegex(ImportRejected, "SHA completo"):
                load_lock(path)


if __name__ == "__main__":
    unittest.main()
