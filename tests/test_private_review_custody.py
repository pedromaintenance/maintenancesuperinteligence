"""Cycle 38: executable synthetic fixtures for private, offline review custody."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from pilot.change_review_packets import ReviewRejected, digest
from governance.private_review_custody import (
    POLICY, public_packet, inspect, frozen_receipt, verify_receipt,
    safe_report, validated_policy, main
)
from knowledge.causal_adjudication import load


class PrivateReviewCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=load(POLICY)
        cls.packet=public_packet("IRP-001")

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="cycle38-private-")
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)
        self.file=self.path/"fictional-document.bin"
        self.file.write_bytes(b"SIMULATED DOCUMENT ONLY; NO OEM OR HUMAN REVIEW\n")
        self.keyfile=self.path/"custodian.key"
        self.keyfile.write_bytes(b"synthetic-test-custody-key-" + b"Q"*48)
        if os.name=="posix":
            self.keyfile.chmod(0o600)
        self.key=self.keyfile.read_bytes()
        self.submission=self.example()

    def example(self):
        packet=self.packet
        ids=[s["sourceId"] for s in packet["generalBackgroundSources"]]
        roles=("technical_reviewer_a","technical_reviewer_b","adjudicator")
        positions=("conditional_support","conditional_reject","defer_unverified")
        return {
            "schema":"maintenance-superinteligence.private-review-submission.v1",
            "version":"1.0.0",
            "mode":"private_unverified_reviewer_claims_not_operational",
            "packetId":"IRP-001","ruleId":packet["ruleId"],
            "packetDigest":digest(packet),
            "records":[{
                "recordId":"IRP-001-"+("A","B","D")[i],
                "reviewerSlot":roles[i],
                "rolePseudonym":"PSEUDO-"+("ALPHA","BRAVO","DELTA")[i],
                "externalClaimReference":"REF-"+("ALPHA123","BRAVO123","DELTA123")[i],
                "reviewPosition":positions[i],
                "reasoning":(
                    "Parecer hipotético: sem autenticação externa, a comparação "
                    "de evidências apenas organiza uma pergunta e não demonstra "
                    "falha nem causalidade em uma máquina concreta."
                ),
                "counterexampleHandling":(
                    "Contraexemplo hipotético sem evidência física: outra origem "
                    "ou mudança de fluido pode explicar o mesmo sinal relatado."
                ),
                "sourceIds":ids,
                "identityVerified":False,
                "competenceVerified":False,
                "independenceVerified":False,
                "consentVerified":False,
                "digitalSignatureVerified":False,
                "oemEffectivityVerified":False,
                "mayAuthorizeMaintenance":False,
            } for i in range(3)],
            "evidenceFiles":[{
                "path":str(self.file.absolute()),
                "sha256":hashlib.sha256(self.file.read_bytes()).hexdigest(),
            }],
            "identityProofValidated":False,
            "externalAuthorizationValidated":False,
            "oemSeriesEffectivityValidated":False,
            "humanSignoffValidated":False,
            "mayExecuteTest":False,
            "mayCreateWorkOrder":False,
            "mayReleaseEquipment":False,
        }

    def test_private_byte_integrity_and_no_go_report(self):
        receipt=frozen_receipt(self.submission,self.policy,self.key)
        self.assertTrue(verify_receipt(receipt,self.submission,self.policy,self.key))
        report=safe_report(receipt,self.submission,self.policy,self.key)
        self.assertEqual(report["packetId"],"IRP-001")
        self.assertEqual(report["attachmentCount"],1)
        self.assertTrue(report["attachmentByteDigestsChecked"])
        self.assertTrue(report["hmacVerifiedAgainstCustodianKey"])
        self.assertTrue(report["technicalDissentPresent"])
        self.assertEqual(report["claimedReviewerRecords"],2)
        self.assertEqual(report["claimedAdjudicatorRecords"],1)
        self.assertEqual(report["verifiedHumanReviewers"],0)
        for k in ("externalIdentityProviderConnected","humanCredentialsVerified",
                  "organizationalAccessControlVerified","encryptionVerified",
                  "oemBySerialVerified","independentTechnicalReviewCompleted",
                  "upstreamRuleChanged","mayExecuteTest","mayCreateWorkOrder",
                  "mayReleaseEquipment"):
            self.assertFalse(report[k])
        self.assertEqual(report["decision"],
            "no_go_private_integrity_only_external_identity_and_authorization_required")
        body=json.dumps(report)
        self.assertNotIn(str(self.file),body)
        self.assertNotIn("PSEUDO-ALPHA",body)
        self.assertNotIn("Parecer hipotético",body)
        self.assertNotIn("REF-ALPHA123",body)

    def test_cli_seal_then_audit_and_exclusive_file_creation(self):
        data=self.path/"submission.json"
        data.write_text(json.dumps(self.submission),encoding="utf-8")
        receipt=self.path/"receipt.json"
        out=self.path/"report.json"
        main(["seal","--submission",str(data),"--key",str(self.keyfile),
              "--receipt",str(receipt)])
        self.assertTrue(receipt.exists())
        if os.name=="posix":
            self.assertEqual(receipt.stat().st_mode & 0o077,0)
        result=main(["audit","--submission",str(data),"--key",str(self.keyfile),
                     "--receipt",str(receipt),"--report",str(out)])
        self.assertEqual(load(out),result)
        if os.name=="posix":
            self.assertEqual(out.stat().st_mode & 0o077,0)
        with self.assertRaises(ReviewRejected):
            main(["seal","--submission",str(data),"--key",str(self.keyfile),
                  "--receipt",str(receipt)])
        with self.assertRaises(FileExistsError):
            main(["audit","--submission",str(data),"--key",str(self.keyfile),
                  "--receipt",str(receipt),"--report",str(out)])

    def test_changed_attachment_rejected_before_receipt(self):
        receipt=frozen_receipt(self.submission,self.policy,self.key)
        self.file.write_bytes(b"swapped document payload")
        with self.assertRaises(ReviewRejected):
            verify_receipt(receipt,self.submission,self.policy,self.key)
        with self.assertRaises(ReviewRejected):
            frozen_receipt(self.submission,self.policy,self.key)

    def test_wrong_key_or_manipulated_receipt_rejected(self):
        receipt=frozen_receipt(self.submission,self.policy,self.key)
        with self.assertRaises(ReviewRejected):
            verify_receipt(receipt,self.submission,self.policy,b"wrong key"*8)
        altered=copy.deepcopy(receipt)
        altered["custodyHmacSha256"]="0"*64
        with self.assertRaises(ReviewRejected):
            verify_receipt(altered,self.submission,self.policy,self.key)
        altered=copy.deepcopy(receipt)
        altered["identityAuthenticated"]=True
        with self.assertRaises(ReviewRejected):
            verify_receipt(altered,self.submission,self.policy,self.key)

    def test_changed_review_statement_or_source_claim_rejected(self):
        receipt=frozen_receipt(self.submission,self.policy,self.key)
        altered=copy.deepcopy(self.submission)
        altered["records"][0]["reasoning"]+=" Alteração posterior não congelada."
        with self.assertRaises(ReviewRejected):
            verify_receipt(receipt,altered,self.policy,self.key)
        altered=copy.deepcopy(self.submission)
        altered["records"][0]["sourceIds"]=["OEM-SERIAL-NOT-FOUND"]
        with self.assertRaises(ReviewRejected):
            inspect(altered,self.policy)
        altered=copy.deepcopy(self.submission)
        altered["packetDigest"]="0"*64
        with self.assertRaises(ReviewRejected):
            inspect(altered,self.policy)
        altered=copy.deepcopy(self.submission)
        altered["packetId"]="IRP-999"
        with self.assertRaises(ReviewRejected):
            inspect(altered,self.policy)

    def test_role_separation_and_claimed_identity_never_certified(self):
        changes=[
            (1,"rolePseudonym","PSEUDO-ALPHA"),
            (1,"reviewerSlot","technical_reviewer_a"),
            (2,"reviewPosition","conditional_support"),
            (1,"externalClaimReference","alice@example.com"),
            (0,"identityVerified",True),
            (0,"competenceVerified",True),
            (1,"independenceVerified",True),
            (2,"digitalSignatureVerified",True),
            (2,"mayAuthorizeMaintenance",True),
        ]
        for idx,field,value in changes:
            record=copy.deepcopy(self.submission)
            record["records"][idx][field]=value
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                inspect(record,self.policy)

    def test_false_approval_or_external_security_capabilities_denied(self):
        for key in ("identityProofValidated","externalAuthorizationValidated",
                    "oemSeriesEffectivityValidated","humanSignoffValidated",
                    "mayExecuteTest","mayCreateWorkOrder","mayReleaseEquipment"):
            altered=copy.deepcopy(self.submission)
            altered[key]=True
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                inspect(altered,self.policy)
        for key in ("identityVerificationProviderConnected",
                    "perRoleAccessControlImplemented","encryptedStorageImplemented",
                    "externalSignatureVerified","independentHumanReviewConfirmed",
                    "operationalSignoffApproved"):
            policy=copy.deepcopy(self.policy)
            policy[key]=True
            with self.subTest(policy=key),self.assertRaises(ReviewRejected):
                validated_policy(policy)

    def test_private_boundary_key_strength_and_permissions(self):
        inside=Path(__file__).resolve().parents[1]/"build"/"private-review.json"
        altered=copy.deepcopy(self.submission)
        altered["evidenceFiles"][0]["path"]=str(inside)
        with self.assertRaises(ValueError):
            inspect(altered,self.policy)
        weak=self.path/"weak.key"
        weak.write_bytes(b"short")
        with self.assertRaises(ReviewRejected):
            main(["seal","--submission",str(self.path/"foo"),"--key",str(weak),
                  "--receipt",str(self.path/"no.json")])
        if os.name=="posix":
            weak.write_bytes(b"a"*40)
            weak.chmod(0o644)
            data=self.path/"submission.json"
            data.write_text(json.dumps(self.submission))
            with self.assertRaises(ReviewRejected):
                main(["seal","--submission",str(data),"--key",str(weak),
                      "--receipt",str(self.path/"no.json")])

    def test_evidence_symlink_and_duplicate_file_rejected(self):
        alias=self.path/"link-to-fixture.bin"
        try:
            alias.symlink_to(self.file)
        except (OSError,NotImplementedError):
            self.skipTest("symlinks not supported")
        altered=copy.deepcopy(self.submission)
        altered["evidenceFiles"][0]["path"]=str(alias)
        with self.assertRaises(ReviewRejected):
            inspect(altered,self.policy)
        altered=copy.deepcopy(self.submission)
        altered["evidenceFiles"].append(copy.deepcopy(altered["evidenceFiles"][0]))
        with self.assertRaises(ReviewRejected):
            inspect(altered,self.policy)

    def test_policy_sources_and_contracts_present(self):
        validated_policy(self.policy)
        self.assertEqual(len(self.policy["sources"]),3)
        root=Path(__file__).resolve().parents[1]
        for name in (
            "private-review-custody-policy.schema.json",
            "private-review-submission.schema.json",
            "private-review-receipt.schema.json",
            "private-review-custody-report.schema.json",
        ):
            data=json.loads((root/"contracts"/name).read_text())
            self.assertEqual(data["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(data["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
