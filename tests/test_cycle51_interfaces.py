"""C51: source-to-snapshot AI/human interface consistency and NO GO tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts import sync_interfaces as ui


class Cycle51InterfacesTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ui.load()

    def test_two_portals_embed_exactly_same_frozen_public_catalog(self):
        self.assertTrue(ui.validate(self.catalog))
        self.assertTrue(ui.check())
        for file in ui.PORTALS:
            html, match, embedded = ui.embedded(file)
            self.assertEqual(embedded, self.catalog)
            self.assertIn("NO GO", html)
            self.assertIn("SAP/ECM", html)
            self.assertEqual(html.count('id="catalog"'), 1)
            self.assertTrue(match.group(2).lstrip().startswith("{"))
            self.assertNotIn("cdn.jsdelivr", html)
            self.assertNotIn("<script src=", html)
            self.assertNotIn("fetch(", html)

    def test_root_machine_roadmap_is_derived_from_one_catalog(self):
        roadmap = json.loads(ui.checked_file("ROADMAP.json").read_text(
            encoding="utf-8"))
        self.assertEqual(roadmap, ui.machine_roadmap(self.catalog))
        self.assertEqual(roadmap["externalGatesPending"], 13)
        self.assertEqual(roadmap["mainCycle"], 42)
        self.assertEqual(roadmap["decision"], "NO GO")
        self.assertFalse(roadmap["operationalAuthorityGranted"])
        self.assertFalse(roadmap["humanApprovalVerified"])
        self.assertEqual(roadmap["items"], self.catalog["roadmap"])

    def test_agent_roles_and_skills_are_portable_and_auditable(self):
        self.assertEqual(len(self.catalog["agents"]), 3)
        self.assertEqual(len(self.catalog["skills"]), 3)
        text = (ui.ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for row in self.catalog["agents"]:
            self.assertIn(row["file"], text)
            agent = ui.checked_file(row["file"]).read_text(encoding="utf-8")
            self.assertIn(row["skill"], agent)
            self.assertIn("não", agent.lower())
        for row in self.catalog["skills"]:
            self.assertIn(row["file"], text)
            skill = ui.checked_file(row["file"]).read_text(encoding="utf-8")
            self.assertTrue(skill.startswith("---\n"))
            self.assertIn("\nname: " + row["id"] + "\n", skill)

    def test_external_gates_remain_in_declared_order_with_no_authority(self):
        external = json.loads(ui.checked_file(
            "governance/cycle48-study-readiness.v1.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual([x["id"] for x in external["gates"]],
                         [x["id"] for x in self.catalog["gates"]])
        self.assertEqual(self.catalog["snapshot"]["externalGatesVerified"], 0)
        self.assertEqual(self.catalog["snapshot"]["externalGatesTotal"], 13)
        self.assertEqual(len(self.catalog["gates"]), 13)
        for gate in self.catalog["gates"]:
            self.assertEqual(gate["status"],
                             "unverified_requires_external_evidence")
        for key in ui.DENIED:
            self.assertIs(self.catalog["snapshot"][key], False)

    def test_forged_pilot_status_and_operational_claims_are_denied(self):
        for key in ui.DENIED:
            forged = copy.deepcopy(self.catalog)
            forged["snapshot"][key] = True
            with self.subTest(field=key), self.assertRaises(ui.InterfaceRejected):
                ui.validate(forged)
        for attr,val in (
            ("externalGatesVerified", 1),
            ("externalGatesTotal", 12),
            ("mainCycle", 50),
            ("nature", "live_github_verified"),
            ("date", "2028-01-01"),
        ):
            forged = copy.deepcopy(self.catalog)
            forged["snapshot"][attr] = val
            with self.subTest(attr=attr), self.assertRaises(ui.InterfaceRejected):
                ui.validate(forged)

    def test_agent_or_gate_upgraded_to_running_or_verified_is_denied(self):
        changed = copy.deepcopy(self.catalog)
        changed["agents"][0]["status"] = "running_automatically"
        with self.assertRaises(ui.InterfaceRejected):
            ui.validate(changed)
        changed = copy.deepcopy(self.catalog)
        changed["capabilities"][0]["status"] = "certified_for_field_diagnosis"
        with self.assertRaises(ui.InterfaceRejected):
            ui.validate(changed)
        changed = copy.deepcopy(self.catalog)
        changed["gates"][0]["status"] = "approved"
        with self.assertRaises(ui.InterfaceRejected):
            ui.validate(changed)
        changed = copy.deepcopy(self.catalog)
        changed["prs"][0]["status"] = "merged"
        with self.assertRaises(ui.InterfaceRejected):
            ui.validate(changed)

    def test_pr_snapshot_does_not_claim_live_or_post_merge_state(self):
        self.assertEqual(
            [x["number"] for x in self.catalog["prs"]],
            list(range(69, 77)),
        )
        self.assertEqual(
            [x["cycle"] for x in self.catalog["prs"]],
            list(range(43, 51)),
        )
        self.assertEqual(
            self.catalog["snapshot"]["nature"],
            "curated_public_repository_snapshot_not_live_github",
        )
        self.assertTrue(all(x["status"] == "draft_not_merged_snapshot"
                            for x in self.catalog["prs"]))
        self.assertTrue(all(x["url"].startswith(
            "https://github.com/pedromaintenance/maintenancesuperinteligence/pull/"
        ) for x in self.catalog["prs"]))

    def test_malformed_paths_and_missing_agent_skill_are_denied(self):
        for path in ("../../etc/passwd", "/tmp/secret", "docs/../SECURITY.md",
                     "docs/NOT_A_REAL_SOURCE.md", "https://evil.invalid/test"):
            with self.subTest(path=path), self.assertRaises(ui.InterfaceRejected):
                ui.checked_file(path)
        forged = copy.deepcopy(self.catalog)
        forged["agents"][0]["skill"] = "not-in-catalog"
        with self.assertRaises(ui.InterfaceRejected):
            ui.validate(forged)
        forged = copy.deepcopy(self.catalog)
        forged["documents"][0]["path"] = "../password.txt"
        with self.assertRaises(ui.InterfaceRejected):
            ui.validate(forged)

    def test_html_documents_have_working_static_navigation_controls(self):
        overview = ui.PORTALS[0].read_text(encoding="utf-8")
        audit = ui.PORTALS[1].read_text(encoding="utf-8")
        for key in ('id="search"', 'id="domain"', 'id="download"',
                    'id="capabilities"', 'id="agentGrid"',
                    'id="skillGrid"', 'id="milestones"'):
            self.assertIn(key, overview)
        for key in ('id="query"', 'id="owner"', 'id="gatelist"',
                    'id="prgrid"', 'id="export"', 'id="copy"'):
            self.assertIn(key, audit)
        self.assertIn('role="tablist"', audit)
        self.assertIn('aria-live="polite"', audit)
        self.assertIn('auditoria.html', overview)
        self.assertIn('index.html', audit)

    def test_catalog_json_schema_is_executable_and_blocks_authority_upgrade(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("CI pins jsonschema==4.23.0 for this test")
        schema = json.loads(ui.checked_file(
            "contracts/interfaces-catalog.schema.json"
        ).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(self.catalog)), [])
        for attr in ui.DENIED:
            changed = copy.deepcopy(self.catalog)
            changed["snapshot"][attr] = True
            with self.subTest(field=attr):
                self.assertGreater(len(list(validator.iter_errors(changed))), 0)
        changed = copy.deepcopy(self.catalog)
        changed["gates"][1]["status"] = "approved"
        self.assertGreater(len(list(validator.iter_errors(changed))), 0)
        changed = copy.deepcopy(self.catalog)
        changed["project"]["decision"] = "GO"
        self.assertGreater(len(list(validator.iter_errors(changed))), 0)


if __name__ == "__main__":
    unittest.main()
