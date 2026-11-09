"""Cycle 64: synthetic source custody is NOT document authentication."""
import copy
import unittest

from benchmarks.cycle64_source_governance import DENIED, validate
from tests.test_cycle63_effectivity import fixture as previous_fixture


def source(source_id="SIM-SRC001", lineage="SIM-LIN001",
           claim="SIM-VALUE1", status="active", revision=1, supersedes=None):
    return {
        "sourceId": source_id, "referenceId": "SIM-REF001",
        "lineageId": lineage, "revisionOrdinal": revision,
        "status": status, "supersedes": supersedes,
        "claimToken": claim, "sourceNature": "invented_document_only",
        "provenanceVerified": False,
    }


def fixture():
    return {
        "schema": "maintenance-superinteligence.synthetic-source-governance.v1",
        "effectivityCase": previous_fixture(),
        "sources": [source()],
        "claims": {key: False for key in DENIED},
    }


class SourceGovernanceTests(unittest.TestCase):
    def test_single_active_source_not_authenticated(self):
        out = validate(fixture())
        self.assertEqual(out["unresolvedConflicts"], 0)
        self.assertFalse(out["sourceAuthenticityVerified"])
        self.assertFalse(out["references"][0]["referenceApproved"])
        self.assertEqual(out["decision"], "NO GO")

    def test_conflicting_active_lineages_are_flagged(self):
        p = fixture()
        p["sources"].append(source("SIM-SRC002", "SIM-LIN002", "SIM-VALUE2"))
        out = validate(p)
        self.assertEqual(out["unresolvedConflicts"], 1)
        self.assertIn("active_sources_disagree", out["references"][0]["reasonCodes"])

    def test_same_claim_across_lineages_is_not_expert_agreement(self):
        p = fixture()
        p["sources"].append(source("SIM-SRC002", "SIM-LIN002", "SIM-VALUE1"))
        out = validate(p)
        self.assertEqual(out["unresolvedConflicts"], 0)
        self.assertFalse(out["revisionApproved"])

    def test_explicit_supersession_chain(self):
        p = fixture()
        p["sources"][0]["status"] = "superseded"
        p["sources"].append(source("SIM-SRC002", revision=2, supersedes="SIM-SRC001"))
        out = validate(p)
        self.assertEqual(out["references"][0]["activeSources"], 1)
        self.assertFalse(out["oemEffectivityVerified"])

    def test_revoked_only_is_not_active(self):
        p = fixture()
        p["sources"][0]["status"] = "revoked"
        out = validate(p)
        self.assertIn("no_active_source", out["references"][0]["reasonCodes"])
        self.assertIn("revoked_source_present", out["references"][0]["reasonCodes"])

    def test_reject_orphan_superseded_source(self):
        p = fixture()
        p["sources"][0]["status"] = "superseded"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_missing_supersession_parent(self):
        p = fixture()
        p["sources"].append(source("SIM-SRC002", revision=2, supersedes="SIM-GHOST1"))
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_revision_regression(self):
        p = fixture()
        p["sources"][0]["status"] = "superseded"
        p["sources"][0]["revisionOrdinal"] = 2
        p["sources"].append(source("SIM-SRC002", revision=1, supersedes="SIM-SRC001"))
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_cross_lineage_supersession(self):
        p = fixture()
        p["sources"][0]["status"] = "superseded"
        p["sources"].append(source("SIM-SRC002", "SIM-LIN002",
                                   revision=2, supersedes="SIM-SRC001"))
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_multiple_active_revisions_same_lineage(self):
        p = fixture()
        p["sources"].append(source("SIM-SRC002", revision=2))
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_ambiguous_supersession_fork(self):
        p = fixture()
        p["sources"][0]["status"] = "superseded"
        p["sources"].extend([
            source("SIM-SRC002", revision=2, supersedes="SIM-SRC001"),
            source("SIM-SRC003", revision=3, supersedes="SIM-SRC001"),
        ])
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_false_provenance(self):
        p = fixture()
        p["sources"][0]["provenanceVerified"] = True
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_real_document_claim(self):
        p = fixture()
        p["sources"][0]["sourceNature"] = "licensed_oem_document"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_duplicate_id(self):
        p = fixture()
        p["sources"].append(copy.deepcopy(p["sources"][0]))
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_unknown_reference(self):
        p = fixture()
        p["sources"][0]["referenceId"] = "SIM-REF999"
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_missing_source_list(self):
        p = fixture()
        p["sources"] = []
        with self.assertRaises(ValueError):
            validate(p)

    def test_reject_authority_promotions(self):
        for key in DENIED:
            p = fixture()
            p["claims"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(p)

    def test_reject_hidden_operational_metadata(self):
        p = fixture()
        p["sources"][0]["sapOrderId"] = "INTERNAL"
        with self.assertRaises(ValueError):
            validate(p)

    def test_inputs_untouched(self):
        p = fixture()
        before = copy.deepcopy(p)
        validate(p)
        self.assertEqual(p, before)


if __name__ == "__main__":
    unittest.main()
