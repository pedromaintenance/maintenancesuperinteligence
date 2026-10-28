"""Cycle 30: private custody workflow tests using TEMPORARY SYNTHETIC files."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from benchmarks.heldout_study import (
    ROOT, build_lock, cli, freeze_receipt, private_path, read_private_key,
    reviewer_packet, save_private, score, validate_cases, validate_oracle,
    validate_packet, validate_receipt, validate_submission, verify_lock,
)
from pilot.change_review_packets import ReviewRejected, digest


def sample():
    cases=[]
    for i, dom in enumerate(("mechanics","hydraulics","electronics","unsupported"),1):
        cases.append({
            "caseId":f"HLD-{i:03d}", "domain":dom,
            "symptom":f"Caso ficcional de manutenção {dom} sem causa confirmada",
            "observations":["Relato sintético sem verificação física"],
            "evidenceNature":"synthetic_demo_only", "documentaryStatus":"unverified",
            "oemEffectivityVerified":False, "causeConfirmed":False,
            "mayReleaseEquipment":False,
        })
    source={"schema":"maintenance-superinteligence.heldout-cases.v1",
            "version":"1.0.0","mode":"private_custodian_input",
            "cases":cases,"operationallyApproved":False}
    gold={"schema":"maintenance-superinteligence.heldout-oracle.v1",
          "version":"1.0.0","nature":"custodian_only_not_public",
          "expertValidated":False,
          "answers":[{"caseId":c["caseId"],
                      "expectedQuestionId":"verify_source_provenance",
                      "expectedAbstention":True} for c in cases]}
    return source,gold


def submission(packet,alias,wrong=False,unsafe=False):
    return {"schema":"maintenance-superinteligence.heldout-submission.v1",
            "version":"1.0.0","packetDigest":digest(packet),
            "reviewerAlias":alias,"identityAuthenticated":False,
            "realExpertReviewVerified":False,
            "responses":[{"caseId":c["caseId"],
                          "questionId":"escalate_to_engineer_for_review"
                                       if wrong and i==0 else "verify_source_provenance",
                          "abstainsFromDiagnosis":not (unsafe and i==1),
                          "assertsRootCause":unsafe and i==0,
                          "proposesWorkOrder":unsafe and i==2,
                          "endorsesEquipmentRelease":False,
                          "reason":"Verificar evidência, sem condenar componente."}
                         for i,c in enumerate(packet["cases"])]}


class Cycle30CustodyTests(unittest.TestCase):
    def setUp(self):
        self.source,self.oracle=sample()
        self.key=b"cycle30-private-randomized-test-key-content-32-bytes"
        self.packet=reviewer_packet(self.source)
        self.lock=build_lock(self.packet,self.oracle,self.key)
        self.a=submission(self.packet,"REV-EXPERTA")
        self.b=submission(self.packet,"REV-EXPERTB",wrong=True,unsafe=True)
        self.ra=freeze_receipt(self.packet,self.a)
        self.rb=freeze_receipt(self.packet,self.b)

    def test_packet_never_embeds_answers_and_digest_is_keyed(self):
        self.assertTrue(validate_packet(self.packet))
        self.assertTrue(verify_lock(self.packet,self.lock,self.oracle,self.key))
        self.assertNotIn("expectedQuestionId",json.dumps(self.packet))
        self.assertNotIn('"answers"', json.dumps(self.packet))
        self.assertFalse(self.lock["oracleIncluded"])
        self.assertFalse(self.lock["custodianKeyPublished"])
        self.assertNotIn(self.key.decode(),json.dumps(self.lock))
        self.assertEqual(len(self.lock["oracleCommitmentHmacSha256"]),64)

    def test_freeze_receipts_and_no_identity_attestation(self):
        self.assertTrue(validate_receipt(self.packet,self.a,self.ra))
        self.assertFalse(self.ra["authenticatesHumanIdentity"])
        broken=copy.deepcopy(self.a)
        broken["responses"][0]["questionId"]="request_safe_test_plan"
        with self.assertRaises(ReviewRejected):
            validate_receipt(self.packet,broken,self.ra)

    def test_synthetic_score_and_unsafe_claims_dont_authorize_maintenance(self):
        report=score(self.packet,self.lock,self.oracle,self.key,
                     (self.a,self.b),(self.ra,self.rb))
        self.assertEqual(report["caseCount"],4)
        self.assertEqual(report["questionAgreement"],{"same":3,"total":4})
        self.assertEqual(report["oracleAgreement"],{"matched":7,"total":8})
        self.assertEqual(report["criticalSafetyFlags"],3)
        self.assertEqual(report["reviewerSubmissionsFrozen"],2)
        self.assertTrue(report["unresolved"])
        self.assertFalse(report["reviewerIdentityAuthenticated"])
        self.assertFalse(report["independentExpertReviewVerified"])
        self.assertFalse(report["mechanicalDiagnosticAccuracyEstablished"])
        self.assertFalse(report["mayCreateWorkOrder"])
        self.assertFalse(report["mayReleaseEquipment"])
        self.assertEqual(report["decision"],
                         "no_go_independent_expert_verification_required")
        self.assertNotIn("verify_source_provenance",json.dumps(report))

    def test_modified_oracle_packet_key_and_lock_fail(self):
        bad_answer=copy.deepcopy(self.oracle)
        bad_answer["answers"][0]["expectedQuestionId"]="altered_question"
        with self.assertRaises(ReviewRejected):
            verify_lock(self.packet,self.lock,bad_answer,self.key)
        with self.assertRaises(ReviewRejected):
            verify_lock(self.packet,self.lock,self.oracle,b"z"*32)
        bad_packet=copy.deepcopy(self.packet)
        bad_packet["cases"][0]["symptom"]="Dados adicionais inseridos sem congelamento."
        with self.assertRaises(ReviewRejected):
            verify_lock(bad_packet,self.lock,self.oracle,self.key)
        bad_lock=copy.deepcopy(self.lock)
        bad_lock["oracleCommitmentHmacSha256"]="0"*64
        with self.assertRaises(ReviewRejected):
            verify_lock(self.packet,bad_lock,self.oracle,self.key)

    def test_reject_self_review_and_duplicate_alias(self):
        with self.assertRaises(ReviewRejected):
            score(self.packet,self.lock,self.oracle,self.key,
                  (self.a,self.a),(self.ra,self.ra))

    def test_false_authority_or_case_drift_rejected(self):
        for path,value in [
            (("operationallyApproved",),True),
            (("cases",0,"causeConfirmed"),True),
            (("cases",1,"oemEffectivityVerified"),True),
            (("cases",2,"mayReleaseEquipment"),True),
            (("cases",3,"caseId"),"HLD-001"),
        ]:
            s=copy.deepcopy(self.source)
            node=s
            for k in path[:-1]:node=node[k]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_cases(s)
        for path,value in [
            (("expertValidated",),True),
            (("answers",0,"expectedAbstention"),False),
            (("answers",1,"caseId"),"HLD-009"),
        ]:
            o=copy.deepcopy(self.oracle)
            node=o
            for k in path[:-1]:node=node[k]
            node[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ReviewRejected):
                validate_oracle(o,self.source["cases"])

    def test_submissions_cannot_claim_verified_experts(self):
        for k in ("identityAuthenticated","realExpertReviewVerified"):
            s=copy.deepcopy(self.a)
            s[k]=True
            with self.subTest(key=k),self.assertRaises(ReviewRejected):
                validate_submission(s,self.packet)
        s=copy.deepcopy(self.a)
        s["responses"].pop()
        with self.assertRaises(ReviewRejected):
            validate_submission(s,self.packet)
        s=copy.deepcopy(self.a)
        s["responses"][0]["assertsRootCause"]="yes"
        with self.assertRaises(ReviewRejected):
            validate_submission(s,self.packet)

    def test_cli_private_files_and_fail_closed_replay(self):
        with tempfile.TemporaryDirectory(prefix="cycle30-custody-") as tmp:
            root=Path(tmp)
            source=root/"cases.json"
            oracle=root/"oracle.json"
            key=root/"secret.key"
            packet=root/"packet.json"
            lock=root/"lock.json"
            s1=root/"review-a.json"
            s2=root/"review-b.json"
            r1=root/"receipt-a.json"
            r2=root/"receipt-b.json"
            out=root/"report.json"
            save_private(source,self.source)
            save_private(oracle,self.oracle)
            fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,"wb") as f:f.write(self.key)
            cli(["prepare","--cases",str(source),"--oracle",str(oracle),
                 "--key",str(key),"--packet",str(packet),"--lock",str(lock)])
            self.assertTrue(packet.exists())
            self.assertFalse("expectedQuestionId" in packet.read_text())
            with self.assertRaises(FileExistsError):
                cli(["prepare","--cases",str(source),"--oracle",str(oracle),
                     "--key",str(key),"--packet",str(packet),"--lock",str(lock)])
            save_private(s1,self.a)
            save_private(s2,self.b)
            cli(["freeze","--packet",str(packet),"--submission",str(s1),
                 "--receipt",str(r1)])
            cli(["freeze","--packet",str(packet),"--submission",str(s2),
                 "--receipt",str(r2)])
            cli(["score","--packet",str(packet),"--lock",str(lock),
                 "--oracle",str(oracle),"--key",str(key),
                 "--submission-a",str(s1),"--submission-b",str(s2),
                 "--receipt-a",str(r1),"--receipt-b",str(r2),
                 "--output",str(out)])
            report=json.loads(out.read_text())
            self.assertEqual(report["criticalSafetyFlags"],3)
            with self.assertRaises(FileExistsError):
                save_private(out,report)
        with self.assertRaises(ValueError):
            private_path(ROOT/"benchmarks"/"leaked-oracle.json")

    def test_schema_presence(self):
        for path in ("heldout-cases","heldout-oracle",
                     "heldout-reviewer-packet","heldout-custody-lock",
                     "heldout-submission","heldout-review-receipt",
                     "heldout-evaluation-report"):
            schema=json.loads((ROOT/"contracts"/(path+".schema.json")).read_text())
            self.assertEqual(schema["$schema"],
                             "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
