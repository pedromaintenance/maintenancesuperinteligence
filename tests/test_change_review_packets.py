import copy
import unittest
from pilot.change_review_packets import build_packets, verify_packets, ReviewRejected

def source():
    proposals = []
    for i in range(1, 11):
        proposals.append({
            "proposalId": f"SIM-GDIFF-{i:02d}", "syntheticProposal": True,
            "changeType": "edge_add", "impactClassification": "path_metrics_changed_only",
            "graphNodeCount": 13, "canonicalEdgeCount": 17,
            "reachabilityImpact": {"changedPairCount": 1},
            "coverageRegression": {"referenceScenarioCount": 100,
                                   "realOutcomesMeasured": False, "affectedScenarios": []},
            "reviewerAssignmentRequirement": {
                "areas": ["IT","InformationSecurity","Engineering","Legal","MaintenanceManagement"],
                "signedChangeAcceptance": False, "individualReviewersAuthenticated": False,
                "independentTechnicalApprovalVerified": False, "oemEffectivityVerified": False},
            "changeAdjudication": {
                "decision": "veto_no_merge", "proposalAppliedToMain": False,
                "oldGraphModified": False, "mayWriteSap": False, "mayModifyEcm": False,
                "mayCreateWorkOrder": False, "mayOrderParts": False,
                "mayReleaseEquipment": False}
        })
    return {
        "schema": "maintenance-superinteligence.graph-change-review-report.v1",
        "decision": "no_go", "allProposalsVetoed": True, "realChangesCommitted": 0,
        "verifiedHumanReviewCount": 0, "baselineControlCount": 13,
        "baselineEdgeCount": 17, "sourceOracleScenarioCount": 100,
        "proposalCount": 10, "canonicalDagSha256": "synthetic-test-only",
        "operationalAuthority": {k: False for k in
             ("mayWriteSap","mayModifyEcm","mayCreateWorkOrder",
              "mayOrderParts","mayReleaseEquipment","mayAuthorizePrivatePilot")},
        "proposals": proposals
    }

class Cycle25Test(unittest.TestCase):
    def test_ten_packets_vetoed(self):
        s = source()
        result = build_packets(s)
        self.assertTrue(verify_packets(result, s))
        self.assertEqual(len(result["packets"]), 10)
        for p in result["packets"]:
            self.assertEqual(len(p["documentaryEvidenceGaps"]), 7)
            self.assertEqual(len(p["objections"]), 5)
            self.assertEqual(p["adjudication"], "veto_no_merge")
            self.assertFalse(any(p["noOperationalAuthority"].values()))

    def test_reject_false_approval(self):
        for path, value in [
            (("decision",), "go"),
            (("realChangesCommitted",), 1),
            (("proposalCount",), 9),
            (("proposals", 0, "changeAdjudication", "decision"), "approved"),
            (("proposals", 1, "reviewerAssignmentRequirement", "signedChangeAcceptance"), True),
            (("proposals", 2, "coverageRegression", "realOutcomesMeasured"), True),
            (("proposals", 3, "changeAdjudication", "mayWriteSap"), True),
            (("proposals", 4, "graphNodeCount"), 12),
        ]:
            s = source()
            item = s
            for part in path[:-1]:
                item = item[part]
            item[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewRejected):
                build_packets(s)

    def test_tamper_and_stale_source(self):
        s = source()
        p = build_packets(s)
        forged = copy.deepcopy(p)
        forged["packets"][0]["realSignatures"] = 1
        with self.assertRaises(ReviewRejected):
            verify_packets(forged, s)
        stale = copy.deepcopy(s)
        stale["canonicalDagSha256"] = "revised-dag"
        with self.assertRaises(ReviewRejected):
            verify_packets(p, stale)

if __name__ == "__main__":
    unittest.main()
