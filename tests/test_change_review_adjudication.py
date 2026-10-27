"""Adversarial checks for Cycle 26's documentary veto and revocation cascade."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from pilot.change_review_packets import AREAS, DENIED, PROOFS
from pilot.change_review_adjudication import (
    FIXTURE, EVENTS, ReviewRejected, build_report, render_html,
    validate_fixture, verify_report,
)


def source_packets():
    packets = []
    for i in range(1, 11):
        packets.append({
            "proposalId": f"SIM-GDIFF-{i:02}",
            "sourceProposalSha256": f"simulated-sha-{i:02}",
            "graphRevisionSha256": "synthetic-canonical-revision",
            "humanReviewsPerformed": 0, "realSignatures": 0,
            "adjudication": "veto_no_merge",
            "documentaryEvidenceGaps": [
                {"proof": p, "verified": False, "receipt": None}
                for p in PROOFS],
            "objections": [
                {"area": a, "status": "synthetic_unresolved_not_a_real_reviewer"}
                for a in AREAS],
            "noOperationalAuthority": {k: False for k in DENIED},
        })
    return {
        "schema": "maintenance-superinteligence.graph-change-review-packets.v1",
        "decision": "no_go", "packetCount": 10, "packets": packets,
        "graphRevisionSha256": "synthetic-canonical-revision",
        "independentReviewActual": False, "sourceAuthenticityProven": False,
        "noOperationalAuthority": {k: False for k in DENIED},
    }


class Cycle26Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_all_ten_scenarios_and_sha_chain(self):
        packets = source_packets()
        report = build_report(self.spec, packets)
        self.assertTrue(verify_report(report, self.spec, packets))
        self.assertEqual(report["decision"], "no_go")
        self.assertEqual(len(report["results"]), 10)
        self.assertEqual(len(report["auditTrail"]), 10)
        self.assertEqual(report["auditTrail"][0]["previousDigest"], "0" * 64)
        self.assertEqual(report["auditTailDigest"], report["auditTrail"][-1]["entryDigest"])
        self.assertEqual({r["eventType"] for r in report["results"]}, set(EVENTS))
        for i, r in enumerate(report["results"]):
            self.assertEqual(r["resolution"], EVENTS[r["eventType"]])
            self.assertEqual(r["adjudication"], "veto_no_merge")
            self.assertFalse(r["mayMerge"])
            self.assertFalse(any(r["noOperationalAuthority"].values()))
            self.assertEqual(len(r["objectionsPreserved"]), 2)
            self.assertEqual(len(r["reopenedDocumentaryGates"]), 7)
            self.assertEqual(r["actualIndependentReviews"], 0)
            if i:
                self.assertEqual(report["auditTrail"][i]["previousDigest"],
                                 report["auditTrail"][i - 1]["entryDigest"])

    def test_strict_fixture_rejection(self):
        mutations = [
            (("schema",), "not-ours"),
            (("scenarioCount",), 9),
            (("scenarios", 0, "scenarioId"), "SIM-ADJ-99"),
            (("scenarios", 0, "eventType"), "approve_all"),
            (("scenarios", 0, "claimedGraphRevision"), "baseline"),
            (("scenarios", 1, "evidenceReference"), None),
            (("scenarios", 2, "perspectives", 1, "area"), "Engineering"),
            (("scenarios", 2, "perspectives", 1, "position"), "objection"),
            (("scenarios", 3, "reviewerAlias"), "SIM-REVIEWER-B"),
            (("scenarios", 4, "purportedSignature"), False),
            (("scenarios", 5, "ownerChanged"), False),
            (("scenarios", 6, "oemRevisionChanged"), False),
            (("scenarios", 7, "objectionSuppressed"), False),
            (("scenarios", 8, "purportedApproval"), False),
            (("scenarios", 9, "evidenceReference"), "oem_effectivity"),
            (("scenarios", 9, "reviewerAlias"), "real person's name"),
        ]
        for path, value in mutations:
            fixture = copy.deepcopy(self.spec)
            node = fixture
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                validate_fixture(fixture, source_packets())

    def test_reject_source_promotions_and_hidden_objections(self):
        mutations = [
            (("decision",), "go"),
            (("independentReviewActual",), True),
            (("noOperationalAuthority", "mayWriteSap"), True),
            (("packets", 0, "adjudication"), "approved"),
            (("packets", 1, "realSignatures"), 1),
            (("packets", 2, "humanReviewsPerformed"), 1),
            (("packets", 3, "graphRevisionSha256"), "alternate"),
            (("packets", 4, "documentaryEvidenceGaps", 0, "verified"), True),
            (("packets", 5, "objections", 0, "status"), "withdrawn"),
            (("packets", 6, "noOperationalAuthority", "mayReleaseEquipment"), True),
        ]
        for path, value in mutations:
            packets = source_packets()
            node = packets
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                build_report(self.spec, packets)

    def test_digest_and_report_forgery_rejection(self):
        packets = source_packets()
        report = build_report(self.spec, packets)
        paths = [
            (("decision",), "go"),
            (("auditTailDigest",), "f" * 64),
            (("auditTrail", 0, "entryDigest"), "bad"),
            (("results", 0, "adjudication"), "merge_approved"),
            (("results", 1, "actualIndependentReviews"), 2),
            (("results", 4, "realSignaturesVerified"), 1),
            (("results", 8, "objectionsPreserved"), []),
            (("noOperationalAuthority", "mayModifyEcm"), True),
        ]
        for path, value in paths:
            copy_report = copy.deepcopy(report)
            node = copy_report
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                verify_report(copy_report, self.spec, packets)

    def test_html_static_no_approval_controls(self):
        h = render_html(build_report(self.spec, source_packets()))
        self.assertEqual(h.count("<section>"), 10)
        self.assertNotIn("<script", h)
        self.assertNotIn("<form", h)
        self.assertIn("NO GO", h)

    def test_schemas_parse(self):
        root = Path(__file__).resolve().parents[1] / "contracts"
        for file in ("review-contestation-spec.schema.json",
                     "review-adjudication-report.schema.json"):
            j = json.loads((root / file).read_text(encoding="utf-8"))
            self.assertEqual(j["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(j["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
