"""Cycle 45: synthetic-only blind paired-review and private custody tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from benchmarks.cycle45_blinded_pairwise import (
    balanced_assignment, build_packet, check_custody, cli, freeze_receipt,
    prepare, score, validate_candidates, validate_packet,
    validate_receipt, validate_submission, verify_report,
)
from benchmarks.private_quality_gate import (
    case_digest, record_digest, test_narrative,
)
from benchmarks.heldout_study import private_path
from pilot.change_review_packets import ReviewRejected, digest


DOMAINS = ("mechanics", "hydraulics", "electronics", "cooling")
QUESTION_FAMILIES = (
    ("Qual registro descreve a identidade do fluido e do compartimento com segurança?",
     "Qual dado documental distingue formulação conhecida de erro na origem da amostra?"),
    ("Quais condições de serviço e carga documentadas existem para o sistema hidráulico?",
     "Que informação separa variação de demanda de limitação documentada do circuito?"),
    ("Qual cronologia documental associa o módulo eletrônico ao evento relatado?",
     "Que comparação documental distingue evento transitório de sinal não confiável?"),
    ("Que condição de ciclo térmico e carga consta dos registros disponíveis?",
     "Que comparação documental distingue demanda térmica e rejeição de calor?"),
)


def private_fixture():
    cases = []
    for i, domain in enumerate(DOMAINS, 1):
        cases.append({
            "caseId": f"HLD-{i:03d}", "domain": domain,
            "symptom": (
                f"Situação inteiramente fictícia do sistema {domain}, "
                "sem medição real, causa demonstrada ou aplicação de OEM"
            ),
            "observations": [
                f"Há apenas registros documentais hipotéticos para {domain}."
            ],
            "evidenceNature": "synthetic_demo_only",
            "documentaryStatus": "unverified",
            "oemEffectivityVerified": False,
            "causeConfirmed": False,
            "mayReleaseEquipment": False,
        })
    source = {
        "schema": "maintenance-superinteligence.heldout-cases.v1",
        "version": "1.0.0", "mode": "private_custodian_input",
        "cases": cases, "operationallyApproved": False,
    }
    candidate_rows = []
    for case, texts in zip(cases, QUESTION_FAMILIES):
        candidate_rows.append({
            "caseId": case["caseId"],
            "baseline": {
                "questionId": "document_context_" + case["domain"],
                "questionText": texts[0], "physicalTestAuthorized": False,
            },
            "experimental": {
                "questionId": "differential_context_" + case["domain"],
                "questionText": texts[1], "physicalTestAuthorized": False,
            },
        })
    candidates = {
        "schema": "maintenance-superinteligence.cycle45-candidate-source.v1",
        "version": "1.0.0", "mode": "private_custodian_pair_source",
        "cases": candidate_rows, "realExpertReviewCompleted": False,
        "mayExecuteTest": False,
    }
    records = []
    for i, (split, ident, domain, text) in enumerate((
        ("train", "TRN-001", "mechanics",
         "Treinamento fictício dedicado a documentos de lubrificação, "
         "com origem distinta e nenhuma confirmação de causa."),
        ("dev", "DEV-001", "cooling",
         "Desenvolvimento inteiramente sintético para contexto térmico "
         "e condição de rejeição de calor sem temperatura real."),
    ), 1):
        r = {
            "caseId": ident, "split": split, "domain": domain,
            "narrative": text, "caseDigest": "",
            "lineage": f"SIM-LIN-{i:03d}",
            "sourceGroup": f"SIM-GRP-{i:03d}",
            "evidenceRef": f"SIM-EVD-{i:03d}",
            "mechanismTag": "documentary_alternative",
            "documentaryStatus": "unverified",
            "abstentionRequired": True, "causeConfirmed": False,
        }
        r["caseDigest"] = record_digest(r)
        records.append(r)
    mechanisms = ("fluid_trace", "flow_path", "signal_path", "heat_rejection")
    for i, (case, mechanism) in enumerate(zip(cases, mechanisms), 3):
        records.append({
            "caseId": case["caseId"], "split": "test",
            "domain": case["domain"],
            "narrative": test_narrative(case),
            "caseDigest": case_digest(case),
            "lineage": f"SIM-LIN-{i:03d}",
            "sourceGroup": f"SIM-GRP-{i:03d}",
            "evidenceRef": f"SIM-EVD-{i:03d}",
            "mechanismTag": mechanism,
            "documentaryStatus": "unverified",
            "abstentionRequired": True, "causeConfirmed": False,
        })
    metadata = {
        "schema": "maintenance-superinteligence.private-quality-metadata.v1",
        "version": "1.0.0", "mode": "private_custodian_metadata",
        "independentReviewCompleted": False, "operationallyApproved": False,
        "records": records,
    }
    policy = {
        "schema": "maintenance-superinteligence.private-quality-policy.v1",
        "version": "1.0.0",
        "splitMinimums": {"train": 1, "dev": 1, "test": 4},
        "requiredTestDomains": list(DOMAINS),
        "requiredTestStatuses": ["unverified"],
        "requiredTestMechanisms": {
            "mechanics": ["fluid_trace"],
            "hydraulics": ["flow_path"],
            "electronics": ["signal_path"],
            "cooling": ["heat_rejection"],
        },
        "nearDuplicateThreshold": 0.82,
        "independentExpertEndorsed": False,
    }
    return source, candidates, metadata, policy


def fabricated_submission(packet, alias, choices=None, flags=None):
    choices = choices or ("A", "A", "A", "B")
    flags = flags or {}
    return {
        "schema": "maintenance-superinteligence.cycle45-review-submission.v1",
        "version": "1.0.0",
        "packetDigest": digest(packet),
        "reviewerAlias": alias,
        "realHumanIdentityAuthenticated": False,
        "independentExpertReviewVerified": False,
        "assessments": [
            {
                "caseId": case["caseId"], "preference": choice,
                "reason": "Interpretação exclusivamente simulada "
                          "para testar a estrutura de comparação documental.",
                "riskFlags": flags.get(i, []),
                "physicalTestAuthorized": False,
                "technicalApprovalVerified": False,
            }
            for i, (case, choice) in enumerate(zip(packet["cases"], choices))
        ],
    }


class Cycle45BlindPairwiseTests(unittest.TestCase):
    def setUp(self):
        self.source, self.candidates, self.metadata, self.policy = private_fixture()
        self.key = b"synthetic-research-key-only-for-tests-longer-than-32-bytes"
        self.assignment = ["A", "B", "A", "B"]
        self.packet, self.lock, self.quality = prepare(
            self.source, self.candidates, self.metadata, self.policy,
            self.key, assignment=self.assignment
        )
        self.a = fabricated_submission(
            self.packet, "REV-SYNTHA", flags={3: ["unsafe_question"]}
        )
        self.b = fabricated_submission(
            self.packet, "REV-SYNTHB", choices=("A", "A", "B", "B")
        )
        self.ra = freeze_receipt(self.packet, self.a)
        self.rb = freeze_receipt(self.packet, self.b)

    def invoke_score(self, a=None, b=None, ra=None, rb=None,
                     packet=None, lock=None, quality=None):
        return score(
            self.source, self.candidates, self.metadata, self.policy,
            packet or self.packet, lock or self.lock, quality or self.quality,
            self.key, (a or self.a, b or self.b),
            (ra or self.ra, rb or self.rb)
        )

    def test_source_quality_gate_and_custody_are_required(self):
        self.assertEqual(check_custody(
            self.source, self.candidates, self.metadata, self.policy,
            self.packet, self.lock, self.quality, self.key
        ), self.assignment)
        self.assertEqual(self.lock["packetDigest"], digest(self.packet))
        self.assertEqual(len(self.lock["commitmentHmacSha256"]), 64)
        self.assertFalse(self.lock["externalExpertReviewCompleted"])
        bad_meta = copy.deepcopy(self.metadata)
        bad_meta["records"][2]["sourceGroup"] = bad_meta["records"][0]["sourceGroup"]
        with self.assertRaises(ReviewRejected):
            prepare(self.source, self.candidates, bad_meta,
                    self.policy, self.key, self.assignment)

    def test_blind_packet_never_exposes_arm_provenance(self):
        validate_packet(self.packet)
        visible = json.dumps(self.packet)
        for secret in ("baselineArm", "candidateDigest", "armMapping",
                       "questionId", "experimentOrigin", '"baseline"',
                       '"experimental"', self.key.decode()):
            self.assertNotIn(secret, visible)
        self.assertFalse(self.packet["armProvenanceIncluded"])
        self.assertTrue(self.packet["privateCustodyRequired"])
        self.assertEqual(self.packet["caseCount"], 4)
        for idx, case in enumerate(self.packet["cases"]):
            src = self.candidates["cases"][idx]
            expected_a = src["baseline" if self.assignment[idx] == "A"
                             else "experimental"]["questionText"]
            self.assertEqual(case["questionA"], expected_a)

    def test_balanced_allocation_for_even_and_odd_cohorts(self):
        for size in (2, 3, 4, 5, 49, 50):
            for _ in range(10):
                assignments = balanced_assignment(size)
                self.assertEqual(len(assignments), size)
                self.assertLessEqual(abs(assignments.count("A") -
                                         assignments.count("B")), 1)

    def test_masked_custody_and_key_changes_fail_closed(self):
        tampered_packet = copy.deepcopy(self.packet)
        tampered_packet["cases"][0]["questionA"] = (
            "Adulteração introduzida no texto de uma pergunta para enganar."
        )
        with self.assertRaises(ReviewRejected):
            check_custody(self.source, self.candidates, self.metadata,
                          self.policy, tampered_packet, self.lock,
                          self.quality, self.key)
        tampered_lock = copy.deepcopy(self.lock)
        tampered_lock["armMapping"][0]["baselineArm"] = "B"
        with self.assertRaises(ReviewRejected):
            check_custody(self.source, self.candidates, self.metadata,
                          self.policy, self.packet, tampered_lock,
                          self.quality, self.key)
        with self.assertRaises(ReviewRejected):
            check_custody(self.source, self.candidates, self.metadata,
                          self.policy, self.packet, self.lock, self.quality,
                          b"another-key-long-enough-for-a-custody-commitment")

    def test_invalid_candidates_and_false_authority_are_rejected(self):
        for path, value in (
            (("realExpertReviewCompleted",), True),
            (("mayExecuteTest",), True),
            (("cases", 0, "experimental", "physicalTestAuthorized"), True),
            (("cases", 0, "experimental", "questionText"),
             self.candidates["cases"][0]["baseline"]["questionText"]),
            (("cases", 0, "experimental", "questionId"), "replace motor"),
            (("cases", 1, "caseId"), "HLD-999"),
        ):
            mutated = copy.deepcopy(self.candidates)
            node = mutated
            for k in path[:-1]:
                node = node[k]
            node[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                validate_candidates(mutated, self.source)

    def test_freeze_and_duplicate_reviewer_aliases_are_blocked(self):
        self.assertTrue(validate_receipt(self.packet, self.a, self.ra))
        altered = copy.deepcopy(self.a)
        altered["assessments"][0]["preference"] = "B"
        with self.assertRaises(ReviewRejected):
            validate_receipt(self.packet, altered, self.ra)
        another_a = copy.deepcopy(self.a)
        with self.assertRaises(ReviewRejected):
            self.invoke_score(b=another_a, rb=self.ra)
        altered = copy.deepcopy(self.a)
        altered["realHumanIdentityAuthenticated"] = True
        with self.assertRaises(ReviewRejected):
            validate_submission(self.packet, altered)
        altered = copy.deepcopy(self.a)
        altered["assessments"][0]["physicalTestAuthorized"] = True
        with self.assertRaises(ReviewRejected):
            validate_submission(self.packet, altered)

    def test_pairwise_reconciliation_never_forges_consensus(self):
        report = self.invoke_score()
        self.assertEqual(report["rawReviewerAgreement"], {"same": 3, "total": 4})
        counts = report["preferenceCounts"]
        self.assertEqual(counts["baseline_preferred"], 1)
        self.assertEqual(counts["experimental_preferred"], 1)
        self.assertEqual(counts["risk_flagged_requires_adjudication"], 1)
        self.assertEqual(counts["disagreement_requires_adjudication"], 1)
        self.assertEqual([r["state"] for r in report["cases"]], [
            "baseline_preferred", "experimental_preferred",
            "disagreement_requires_adjudication",
            "risk_flagged_requires_adjudication"
        ])
        self.assertTrue(report["cases"][2]["requiresIndependentAdjudication"])
        self.assertTrue(report["cases"][3]["requiresIndependentAdjudication"])
        self.assertFalse(report["independentMechanicalReviewVerified"])
        self.assertFalse(report["mechanicalDiagnosticAccuracyMeasured"])
        self.assertFalse(report["fieldDiagnosticImprovementEstablished"])
        self.assertFalse(report["reviewerIdentitiesAuthenticated"])
        self.assertEqual(
            report["decision"],
            "no_go_unattested_blinded_preferences_not_mechanical_validity"
        )
        for key in ("mayExecuteTest", "mayCreateWorkOrder",
                    "mayModifyECM", "mayReleaseEquipment"):
            self.assertFalse(report[key])

    def test_abstain_and_tie_are_not_counted_as_preference(self):
        aa = fabricated_submission(self.packet, "REV-SYNTHA",
                                   choices=("tie", "abstain", "A", "A"))
        bb = fabricated_submission(self.packet, "REV-SYNTHB",
                                   choices=("tie", "abstain", "B", "A"))
        report = self.invoke_score(
            a=aa, b=bb, ra=freeze_receipt(self.packet, aa),
            rb=freeze_receipt(self.packet, bb)
        )
        self.assertEqual(report["preferenceCounts"]["tied"], 1)
        self.assertEqual(report["preferenceCounts"]["both_abstain"], 1)
        self.assertEqual(report["preferenceCounts"]["baseline_preferred"], 1)
        self.assertEqual(report["preferenceCounts"]["experimental_preferred"], 1)

    def test_report_can_be_reconstructed_but_not_promoted(self):
        report = self.invoke_score()
        args = (
            self.source, self.candidates, self.metadata, self.policy,
            self.packet, self.lock, self.quality, self.key,
            (self.a, self.b), (self.ra, self.rb)
        )
        self.assertTrue(verify_report(report, *args))
        forged = copy.deepcopy(report)
        forged["fieldDiagnosticImprovementEstablished"] = True
        with self.assertRaises(ReviewRejected):
            verify_report(forged, *args)
        forged = copy.deepcopy(report)
        forged["preferenceCounts"]["experimental_preferred"] = 4
        with self.assertRaises(ReviewRejected):
            verify_report(forged, *args)

    def test_private_cli_prepare_freeze_score_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            files = {}
            for name, value in (
                ("source", self.source), ("candidates", self.candidates),
                ("quality-metadata", self.metadata),
                ("quality-policy", self.policy),
            ):
                target = folder / (name + ".json")
                target.write_text(json.dumps(value), encoding="utf-8")
                files[name] = target
            key_path = folder / "key.bin"
            key_path.write_bytes(self.key)
            key_path.chmod(0o600)
            files["key"] = key_path
            for name in ("packet", "lock", "quality-receipt",
                         "submission-a", "submission-b",
                         "receipt-a", "receipt-b", "output"):
                files[name] = folder / (name + ".json")
            def args_for(names):
                return [piece for name in names for piece in
                        ("--" + name, str(files[name]))]
            prepare_args = ["prepare"] + args_for(
                ("source", "candidates", "quality-metadata", "quality-policy",
                 "key", "packet", "lock", "quality-receipt")
            )
            cli(prepare_args)
            with self.assertRaises(FileExistsError):
                cli(prepare_args)
            packet = json.loads(files["packet"].read_text(encoding="utf-8"))
            self.assertFalse(packet["armProvenanceIncluded"])
            for suffix, alias in (("a", "REV-TESTA"), ("b", "REV-TESTB")):
                sub = fabricated_submission(
                    packet, alias, choices=("A", "A", "tie", "abstain")
                )
                files["submission-" + suffix].write_text(
                    json.dumps(sub), encoding="utf-8"
                )
                cli(["freeze"] + args_for(
                    ("packet", "submission-" + suffix, "receipt-" + suffix)
                ))
            cli(["score"] + args_for(
                ("source", "candidates", "quality-metadata", "quality-policy",
                 "key", "packet", "lock", "quality-receipt",
                 "submission-a", "submission-b", "receipt-a", "receipt-b",
                 "output")
            ))
            report = json.loads(files["output"].read_text(encoding="utf-8"))
            self.assertEqual(report["caseCount"], 4)
            self.assertFalse(report["independentMechanicalReviewVerified"])
            with self.assertRaises(FileExistsError):
                cli(["score"] + args_for(
                    ("source", "candidates", "quality-metadata",
                     "quality-policy", "key", "packet", "lock",
                     "quality-receipt", "submission-a", "submission-b",
                     "receipt-a", "receipt-b", "output")
                ))
            with self.assertRaises(ValueError):
                private_path(Path(__file__).resolve().parents[1] /
                             "benchmarks/cycle44-symbolic-trials.v1.json")


if __name__ == "__main__":
    unittest.main()
