"""Cycle 32: prove quality preflight gates heldout release and private scoring."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from benchmarks.heldout_study import reviewer_packet, cli, save_private
from benchmarks.private_quality_gate import (
    audit,receipt,verify_receipt,validate_metadata,validate_policy,
    normalized_tokens,
)
from pilot.change_review_packets import ReviewRejected
from tests.test_heldout_study import sample,private_quality_fixture


class PrivateQualityGatesTests(unittest.TestCase):
    def setUp(self):
        self.source,self.oracle=sample()
        self.meta,self.policy=private_quality_fixture(self.source)
        self.packet=reviewer_packet(self.source)

    def test_clean_fictional_cohorts_pass_without_claiming_mechanical_accuracy(self):
        r=audit(self.meta,self.source,self.policy)
        self.assertTrue(r["qualityPreflightPassed"])
        self.assertEqual(r["splits"],{"train":1,"dev":1,"test":4})
        self.assertEqual(r["findings"],[])
        self.assertFalse(r["independentReviewCompleted"])
        self.assertFalse(r["realWorldDiagnosticAccuracyMeasured"])
        self.assertFalse(r["mayCreateWorkOrder"])
        self.assertFalse(r["mayReleaseEquipment"])
        proof=receipt(self.source,self.meta,self.policy,self.packet)
        self.assertTrue(verify_receipt(proof,self.source,self.meta,self.policy,self.packet))
        self.assertFalse(proof["independentExpertApproval"])
        self.assertFalse(proof["operationallyApproved"])

    def test_cross_split_lineage_source_evidence_and_text_block_release(self):
        for attr,code in [
            ("lineage","lineage_cross_split"),
            ("sourceGroup","source_cross_split"),
            ("evidenceRef","evidence_cross_split"),
        ]:
            changed=copy.deepcopy(self.meta)
            changed["records"][2][attr]=changed["records"][0][attr]
            result=audit(changed,self.source,self.policy)
            with self.subTest(attr=attr):
                self.assertFalse(result["qualityPreflightPassed"])
                self.assertIn(code,[x["code"] for x in result["findings"]])
                with self.assertRaises(ReviewRejected):
                    receipt(self.source,changed,self.policy,self.packet)
        changed=copy.deepcopy(self.meta)
        changed["records"][0]["narrative"]=changed["records"][2]["narrative"]
        from benchmarks.private_quality_gate import record_digest
        changed["records"][0]["caseDigest"]=record_digest(changed["records"][0])
        r=audit(changed,self.source,self.policy)
        self.assertIn("narrative_exact_cross_split",[x["code"] for x in r["findings"]])

    def test_missing_required_domain_status_or_mechanism_blocks(self):
        for policy_path,value,code in [
            ("requiredTestDomains",["mechanics","hydraulics","cooling"],
             "missing_domain_test"),
            ("requiredTestStatuses",["unverified","revoked"],
             "missing_status_test"),
            ("requiredTestMechanisms",{"mechanics":["fluid_trace","bearing_damage"]},
             "missing_mechanism_test"),
        ]:
            pol=copy.deepcopy(self.policy)
            pol[policy_path]=value
            r=audit(self.meta,self.source,pol)
            with self.subTest(policy_path=policy_path):
                if code=="missing_domain_test":
                    # Adding a domain with no test must fail, not removing one.
                    self.assertIn(code,[x["code"] for x in r["findings"]])
                else:
                    self.assertFalse(r["qualityPreflightPassed"])
                    self.assertIn(code,[x["code"] for x in r["findings"]])

    def test_metadata_cannot_lie_about_released_cases(self):
        for field,value in [
            ("narrative","Invented alternative narrative different from case"),
            ("domain","hydraulics"),
            ("caseDigest","a"*64),
            ("documentaryStatus","revoked"),
            ("causeConfirmed",True),
            ("abstentionRequired",False),
        ]:
            meta=copy.deepcopy(self.meta)
            meta["records"][2][field]=value
            with self.subTest(field=field),self.assertRaises(ReviewRejected):
                validate_metadata(meta,self.source,self.policy)
        meta=copy.deepcopy(self.meta)
        meta["records"].pop()
        with self.assertRaises(ReviewRejected):
            validate_metadata(meta,self.source,self.policy)

    def test_bad_quality_receipt_and_source_change_never_verify(self):
        proof=receipt(self.source,self.meta,self.policy,self.packet)
        for key,value in [
            ("packetDigest","0"*64),
            ("metadataDigest","0"*64),
            ("policyDigest","0"*64),
            ("auditDigest","0"*64),
            ("independentExpertApproval",True),
            ("passed",False),
        ]:
            changed=copy.deepcopy(proof)
            changed[key]=value
            with self.subTest(key=key),self.assertRaises(ReviewRejected):
                verify_receipt(changed,self.source,self.meta,self.policy,self.packet)
        changed=copy.deepcopy(self.policy)
        changed["nearDuplicateThreshold"]=0.8
        with self.assertRaises(ReviewRejected):
            verify_receipt(proof,self.source,self.meta,changed,self.packet)

    def test_policy_cannot_claim_expert_endorsement(self):
        policy=copy.deepcopy(self.policy)
        policy["independentExpertEndorsed"]=True
        with self.assertRaises(ReviewRejected):
            validate_policy(policy)

    def test_cli_prepare_without_private_quality_flags_cannot_release(self):
        with self.assertRaises(SystemExit):
            cli(["prepare","--cases","/tmp/cases.json","--oracle","/tmp/oracle.json",
                 "--key","/tmp/key","--packet","/tmp/packet","--lock","/tmp/lock"])

    def test_failed_quality_gate_does_not_write_packet_or_lock(self):
        with tempfile.TemporaryDirectory(prefix="cycle32-private-") as tmp:
            root=Path(tmp)
            cases=root/"cases.json"
            oracle=root/"oracle.json"
            meta=root/"meta.json"
            policy=root/"policy.json"
            key=root/"key"
            packet=root/"packet.json"
            lock=root/"lock.json"
            proof=root/"proof.json"
            bad=copy.deepcopy(self.meta)
            bad["records"][2]["lineage"]=bad["records"][0]["lineage"]
            for path,data in ((cases,self.source),(oracle,self.oracle),
                              (meta,bad),(policy,self.policy)):
                save_private(path,data)
            key.write_bytes(b"00000000000000000000000000000000000000000000000")
            key.chmod(0o600)
            with self.assertRaises(ReviewRejected):
                cli(["prepare","--cases",str(cases),"--oracle",str(oracle),
                     "--key",str(key),"--packet",str(packet),"--lock",str(lock),
                     "--quality-metadata",str(meta),"--quality-policy",str(policy),
                     "--quality-receipt",str(proof)])
            self.assertFalse(packet.exists())
            self.assertFalse(lock.exists())
            self.assertFalse(proof.exists())

    def test_schema_contracts(self):
        root=Path(__file__).resolve().parents[1]/"contracts"
        for path in ("private-quality-metadata.schema.json",
                     "private-quality-policy.schema.json",
                     "private-quality-receipt.schema.json"):
            schema=json.loads((root/path).read_text())
            self.assertEqual(schema["$schema"],"https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])


if __name__=="__main__":
    unittest.main()
