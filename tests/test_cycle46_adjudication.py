"""Cycle 46: all reviews and cases below are fictitious, without human attestation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from benchmarks import cycle46_adjudication as c46
from benchmarks.cycle45_blinded_pairwise import (
    prepare, freeze_receipt as freeze45,
)
from tests.test_cycle45_blinded_pairwise import private_fixture, fabricated_submission
from pilot.change_review_packets import digest, ReviewRejected


class Cycle46AdjudicationTests(unittest.TestCase):
    def setUp(self):
        self.source, self.candidates, self.metadata, self.policy45 = private_fixture()
        self.key = b"only-synthetic-cycle46-key-not-authority-or-human-identity"
        self.packet, self.lock, self.quality = prepare(
            self.source, self.candidates, self.metadata, self.policy45,
            self.key, assignment=["A", "B", "A", "B"]
        )
        self.a = fabricated_submission(
            self.packet, "REV-SYNTHA", flags={3: ["unsafe_question"]}
        )
        self.b = fabricated_submission(
            self.packet, "REV-SYNTHB", choices=("A", "A", "B", "B")
        )
        self.subs = (self.a, self.b)
        self.receipts = (freeze45(self.packet, self.a),
                         freeze45(self.packet, self.b))
        self.policy46 = c46.load(c46.POLICY)
        self.args = (
            self.source, self.candidates, self.metadata, self.policy45,
            self.packet, self.lock, self.quality, self.key,
            self.subs, self.receipts, self.policy46,
        )
        self.handoff = c46.prepare_handoff(*self.args)

    def test_rechecks_private_custody_and_never_promotes_authority(self):
        self.assertTrue(c46.validate_handoff(self.handoff, *self.args))
        h = self.handoff
        self.assertEqual(h["caseCount"], 4)
        self.assertEqual(h["flaggedForAdjudicationCount"], 2)
        self.assertEqual(h["sourceReviewReportDigest"],
                         digest(c46.score(
                             self.source, self.candidates, self.metadata,
                             self.policy45, self.packet, self.lock,
                             self.quality, self.key, self.subs, self.receipts
                         )))
        self.assertEqual(h["decision"],
                         "no_go_adjudication_and_blinding_unverified")
        self.assertEqual([x["reviewReasons"] for x in h["caseHandoffs"]], [
            [], [], ["reviewer_disagreement"], ["reviewer_risk_flag"]
        ])
        self.assertTrue(all(x["automaticallyResolved"] is False and
                            x["operationallyApproved"] is False
                            for x in h["caseHandoffs"]))
        for key in ("neutralityScreenPassedAsExpertProof",
                    "reviewerIdentitiesAuthenticated",
                    "independentMechanicalReviewCompleted",
                    "mechanicalDiagnosticAccuracyMeasured",
                    "mayExecuteTest", "mayCreateWorkOrder",
                    "mayWriteSAP", "mayModifyECM", "mayReleaseEquipment"):
            self.assertIs(h[key], False, key)
        self.assertEqual(h["automatedAdjudicationsCompleted"], 0)
        self.assertNotIn("questionA", json.dumps(h))
        self.assertNotIn("questionB", json.dumps(h))
        self.assertNotIn("armMapping", json.dumps(h))

    def test_lexical_and_length_screen_flags_but_no_proof_of_masking(self):
        c46.validate_policy(self.policy46)
        original = self.packet["cases"][0]
        self.assertEqual(c46.screening_warnings(original, self.policy46), [])
        disguised = copy.deepcopy(original)
        disguised["questionA"] += " Texto GERADO POR IA."
        self.assertEqual(c46.screening_warnings(disguised, self.policy46),
                         ["question_origin_cue"])
        exaggerated = copy.deepcopy(original)
        exaggerated["questionB"] += (
            " É necessário verificar a documentação geral, "
            "a cronologia, os registros, a fonte e o histórico. " * 12
        )
        self.assertIn("question_length_imbalance",
                      c46.screening_warnings(exaggerated, self.policy46))
        both = copy.deepcopy(exaggerated)
        both["questionA"] += " Algoritmo experimental."
        self.assertEqual(c46.screening_warnings(both, self.policy46),
                         ["question_origin_cue", "question_length_imbalance"])

    def test_policy_mutations_and_claimed_independence_are_rejected(self):
        changes = (
            ("lengthRatioThreshold", 100.0),
            ("originDisclosureCues", []),
            ("screenedWarnings", []),
            ("requiresReviewReasons", []),
            ("independentNeutralityVerified", True),
            ("independentAdjudicationCompleted", True),
            ("operationallyApproved", True),
        )
        for k, val in changes:
            altered = copy.deepcopy(self.policy46)
            altered[k] = val
            with self.subTest(k=k), self.assertRaises(ReviewRejected):
                c46.validate_policy(altered)

    def test_stale_private_evidence_and_forged_handoff_fail_closed(self):
        altered = copy.deepcopy(self.receipts[0])
        altered["submissionDigest"] = "a" * 64
        args = self.args[:-2] + ((altered, self.receipts[1]), self.policy46)
        with self.assertRaises(ReviewRejected):
            c46.prepare_handoff(*args)
        wrong_key = self.args[:7] + (b"wrong-key-long-enough-for-study-fixture-123",) + self.args[8:]
        with self.assertRaises(ReviewRejected):
            c46.prepare_handoff(*wrong_key)
        wrong = copy.deepcopy(self.handoff)
        wrong["flaggedForAdjudicationCount"] = 0
        with self.assertRaises(ReviewRejected):
            c46.validate_handoff(wrong, *self.args)
        wrong = copy.deepcopy(self.handoff)
        wrong["mayReleaseEquipment"] = True
        with self.assertRaises(ReviewRejected):
            c46.validate_handoff(wrong, *self.args)

    def make_draft(self):
        pending = [r["caseId"] for r in self.handoff["caseHandoffs"]
                   if r["requiresIndependentAdjudication"]]
        return {
            "schema": "maintenance-superinteligence.cycle46-adjudication-draft.v1",
            "version": "1.0.0",
            "handoffDigest": digest(self.handoff),
            "adjudicatorAlias": "REV-SYNTHC",
            "independentIdentityVerified": False,
            "externalEngineeringOpinionReceived": False,
            "entries": [
                {"caseId": c, "proposedNextAction": (
                    "request_independent_disagreement_review" if i == 0 else
                    "request_independent_safety_review"
                 ), "rationale":
                    "Caso sintético pendente de revisão especializada "
                    "e resolução documentada de evidências.",
                 "signedByQualifiedEngineer": False,
                 "contradictionResolved": False}
                for i, c in enumerate(pending)
            ],
            "technicalDecisionApproved": False,
            "mayReleaseEquipment": False,
        }

    def test_draft_only_records_pending_actions_and_freezes_without_signoff(self):
        draft = self.make_draft()
        self.assertTrue(c46.validate_draft(draft, self.handoff, self.subs))
        receipt = c46.freeze_draft(draft, self.handoff, self.subs)
        self.assertTrue(c46.validate_draft_receipt(
            receipt, draft, self.handoff, self.subs
        ))
        self.assertTrue(receipt["frozen"])
        self.assertFalse(receipt["authenticatesHumanIdentity"])
        self.assertFalse(receipt["externalTechnicalAdjudicationCompleted"])
        self.assertEqual(receipt["decision"], "pending_real_independent_review_no_go")
        self.assertEqual(receipt["draftDigest"], digest(draft))

    def test_self_review_and_fake_signatures_never_pass(self):
        for field, value in (
            ("adjudicatorAlias", "REV-SYNTHA"),
            ("independentIdentityVerified", True),
            ("externalEngineeringOpinionReceived", True),
            ("technicalDecisionApproved", True),
            ("mayReleaseEquipment", True),
            ("handoffDigest", "0"*64),
        ):
            bad = self.make_draft()
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ReviewRejected):
                c46.validate_draft(bad, self.handoff, self.subs)
        for key in ("signedByQualifiedEngineer", "contradictionResolved"):
            bad = self.make_draft()
            bad["entries"][0][key] = True
            with self.subTest(key=key), self.assertRaises(ReviewRejected):
                c46.validate_draft(bad, self.handoff, self.subs)

    def test_missing_dissent_duplicated_case_and_approval_decision_rejected(self):
        bad = self.make_draft()
        bad["entries"].pop()
        with self.assertRaises(ReviewRejected):
            c46.validate_draft(bad, self.handoff, self.subs)
        bad = self.make_draft()
        bad["entries"][1]["caseId"] = bad["entries"][0]["caseId"]
        with self.assertRaises(ReviewRejected):
            c46.validate_draft(bad, self.handoff, self.subs)
        bad = self.make_draft()
        bad["entries"][0]["proposedNextAction"] = "release_equipment"
        with self.assertRaises(ReviewRejected):
            c46.validate_draft(bad, self.handoff, self.subs)
        receipt = c46.freeze_draft(self.make_draft(), self.handoff, self.subs)
        receipt["externalTechnicalAdjudicationCompleted"] = True
        with self.assertRaises(ReviewRejected):
            c46.validate_draft_receipt(
                receipt, self.make_draft(), self.handoff, self.subs
            )

    def test_tie_and_abstention_become_review_required(self):
        aa = fabricated_submission(
            self.packet, "REV-SYNTHA",
            choices=("tie", "abstain", "A", "A")
        )
        bb = fabricated_submission(
            self.packet, "REV-SYNTHB",
            choices=("tie", "abstain", "A", "A")
        )
        args = self.args[:8] + (
            (aa, bb), (freeze45(self.packet, aa), freeze45(self.packet, bb)),
            self.policy46,
        )
        report = c46.prepare_handoff(*args)
        self.assertEqual(report["caseHandoffs"][0]["reviewReasons"],
                         ["reviewer_uncertainty"])
        self.assertEqual(report["caseHandoffs"][1]["reviewReasons"],
                         ["reviewer_uncertainty"])
        self.assertTrue(report["caseHandoffs"][0]["requiresIndependentAdjudication"])

    def test_cli_uses_only_private_files_outside_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            contents = {
                "source": self.source, "candidates": self.candidates,
                "quality-metadata": self.metadata,
                "quality-policy": self.policy45,
                "packet": self.packet, "lock": self.lock,
                "quality-receipt": self.quality,
                "submission-a": self.a, "submission-b": self.b,
                "receipt-a": self.receipts[0], "receipt-b": self.receipts[1],
            }
            paths = {}
            for name, obj in contents.items():
                path = p / (name + ".json")
                path.write_text(json.dumps(obj), encoding="utf-8")
                paths[name] = path
            key_file = p / "private-key.bin"
            key_file.write_bytes(self.key)
            key_file.chmod(0o600)
            paths["key"] = key_file
            paths["output"] = p / "handoff.json"
            def args_for(names):
                return [element for name in names for element in (
                    "--" + name, str(paths[name])
                )]
            cmd = ["handoff"] + args_for((
                "source", "candidates", "quality-metadata",
                "quality-policy", "packet", "lock", "quality-receipt",
                "key", "submission-a", "submission-b",
                "receipt-a", "receipt-b", "output"
            ))
            c46.cli(cmd)
            self.assertEqual(c46.load(paths["output"]), self.handoff)
            with self.assertRaises(FileExistsError):
                c46.cli(cmd)
            draft = self.make_draft()
            draft_path = p / "adjudication-draft.json"
            draft_path.write_text(json.dumps(draft), encoding="utf-8")
            freeze_path = p / "adjudication-receipt.json"
            c46.cli([
                "freeze-draft", "--handoff", str(paths["output"]),
                "--draft", str(draft_path),
                "--submission-a", str(paths["submission-a"]),
                "--submission-b", str(paths["submission-b"]),
                "--receipt", str(freeze_path),
            ])
            self.assertEqual(
                c46.load(freeze_path),
                c46.freeze_draft(draft, self.handoff, self.subs)
            )

    def test_declared_contracts_are_strict_about_no_go(self):
        root = Path(__file__).resolve().parents[1] / "contracts"
        for name in ("cycle46-neutrality-policy", "cycle46-handoff",
                     "cycle46-adjudication-draft", "cycle46-draft-receipt"):
            path = root / (name + ".schema.json")
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"],
                             "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
        receipt = json.loads((root / "cycle46-draft-receipt.schema.json")
                             .read_text(encoding="utf-8"))
        self.assertIs(
            receipt["properties"]["externalTechnicalAdjudicationCompleted"]["const"],
            False
        )


if __name__ == "__main__":
    unittest.main()
