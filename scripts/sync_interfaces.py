"""Cycle 51 — verify/synchronize the offline AI + human interface catalog.

The single versioned index is interfaces/catalog.v1.json. Both standalone
portals embed that catalog; they do NOT query GitHub, SAP, ECM, or private data.
--write only re-embeds catalog JSON. --check rejects stale embedded snapshots,
broken repo paths, mismatched Cycle48 external gates, and authority inflation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "interfaces/catalog.v1.json"
MACHINE_ROADMAP = ROOT / "ROADMAP.json"
PORTALS = (
    ROOT / "portal/index.html",
    ROOT / "portal/auditoria.html",
)
EMBED = re.compile(
    r'(<script id="catalog" type="application/json">\s*)(.*?)(\s*</script>)',
    re.DOTALL,
)
SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
REPO_BROWSE = (
    "https://github.com/pedromaintenance/"
    "maintenancesuperinteligence/blob/"
    "research/cycle51-machine-human-knowledge-interfaces/"
)
DENIED = (
    "humanExpertStudyCompleted", "fieldDiagnosticAccuracyMeasured",
    "portalHasLiveBackend", "aiRolesAreRunningAgents",
    "operationalAuthorityGranted",
)


class InterfaceRejected(ValueError):
    """The public index or its derived presentations make unsafe claims."""


def require(condition, message):
    if not condition:
        raise InterfaceRejected(message)


def checked_file(path):
    require(isinstance(path, str) and path
            and SAFE_PATH.fullmatch(path)
            and not path.startswith("/")
            and all(part not in (".", "..") for part in path.split("/")),
            "path escapes the repository or contains disallowed characters")
    resolved = (ROOT / path).resolve()
    require(resolved.is_relative_to(ROOT) and resolved.is_file(),
            "linked source missing from repository: " + path)
    return resolved


def load():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def validate(data):
    require(isinstance(data, dict) and set(data) == {
        "schema", "version", "snapshot", "project", "sections",
        "agents", "skills", "capabilities", "roadmap", "documents",
        "gates", "prs", "sites",
    }, "catalog root fields changed")
    require(data["schema"] == "maintenance-superinteligence.interfaces-catalog.v1"
            and data["version"] == "1.0.0", "catalog not versioned")
    s = data["snapshot"]
    require(s["date"] == "2026-11-05"
            and s["nature"] ==
                "curated_public_repository_snapshot_not_live_github"
            and s["repo"] ==
                "pedromaintenance/maintenancesuperinteligence"
            and s["browseBase"] == REPO_BROWSE
            and s["mainCycle"] == 42
            and s["mainSha"] ==
                "604c9fa2f98393ca31bef5cf31c40a60566851e7"
            and s["lastResearchCycleInPredecessor"] == 50
            and s["predecessorSha"] ==
                "b38d192af613223622635953dc3d9ac66e847413"
            and s["externalGatesVerified"] == 0
            and s["externalGatesTotal"] == 13
            and all(s[k] is False for k in DENIED),
            "snapshot improperly claims freshness, actual review or authority")
    require(data["project"]["decision"] == "NO GO"
            and "SAP/ECM" in data["project"]["prohibition"],
            "portal omits explicit operational NO GO")
    require([x["id"] for x in data["sections"]] ==
            ["visao", "capacidades", "agentes", "roadmap", "auditoria"],
            "unexpected navigation taxonomy")
    agents, skills = data["agents"], data["skills"]
    require(len(agents) == len(skills) == 3, "missing role/skill")
    require({x["skill"] for x in agents} == {x["id"] for x in skills},
            "agent references missing skill")
    require(len({x["id"] for x in agents}) == len(agents)
            and len({x["id"] for x in skills}) == len(skills),
            "duplicate roles or skills")
    for agent in agents:
        require(agent["status"] == "role_specification_only",
                "Markdown agent falsely marked running")
        checked_file(agent["file"])
    for skill in skills:
        require(skill["status"] == "procedure_documented"
                and skill["file"].startswith(".agents/skills/")
                and skill["file"].endswith("/SKILL.md"),
                "missing standard skill contract")
        text = checked_file(skill["file"]).read_text(encoding="utf-8")
        require(text.startswith("---\n") and
                "\nname: " + skill["id"] + "\n" in text,
                "skill front matter has inconsistent identity")
    require(len(data["capabilities"]) >= 6
            and all(c["status"] in (
                "synthetic_research_only", "design_only"
            ) for c in data["capabilities"]),
            "capability promoted beyond evidence")
    require(len(data["documents"]) >= 6
            and len(data["roadmap"]) >= 5,
            "human navigation incomplete")
    for group, field in (
        (data["capabilities"], "source"),
        (data["roadmap"], "source"),
        (data["documents"], "path"),
    ):
        for row in group:
            checked_file(row[field])
    require(all(x["stage"] in (
        "in_draft", "implemented_in_draft",
        "blocked_external_evidence", "pending_human_review"
    ) for x in data["roadmap"]),
            "roadmap item claims unverified completion")
    require(len(data["gates"]) == 13
            and all(x["status"] ==
                "unverified_requires_external_evidence"
                    for x in data["gates"]),
            "gate silently marked externally validated")
    original = json.loads(checked_file(
        "governance/cycle48-study-readiness.v1.json"
    ).read_text(encoding="utf-8"))
    require([x["id"] for x in data["gates"]] ==
            [x["id"] for x in original["gates"]],
            "gate order/identity drift from Cycle48 evidence manifest")
    require(all(x["state"] ==
            "unverified_requires_external_evidence"
            for x in original["gates"]),
            "Cycle48 gate evidence status no longer matches snapshot")
    for gate in data["gates"]:
        require(gate["source"] ==
                "governance/cycle48-study-readiness.v1.json",
                "gate references unapproved documentation")
    require(len(data["prs"]) == 8
            and [x["number"] for x in data["prs"]] ==
                list(range(69, 77))
            and [x["cycle"] for x in data["prs"]] ==
                list(range(43, 51))
            and all(x["status"] == "draft_not_merged_snapshot"
                    and x["url"] ==
                        "https://github.com/pedromaintenance/"
                        "maintenancesuperinteligence/pull/"
                        + str(x["number"])
                    for x in data["prs"]),
            "historical PR snapshot inconsistent or promoted")
    require([x["path"] for x in data["sites"]] ==
            ["portal/index.html", "portal/auditoria.html"],
            "two standalone portal entries required")
    for site in data["sites"]:
        checked_file(site["path"])
    require("Ciclo 51" in checked_file("docs/ROADMAP.md").read_text(
        encoding="utf-8"), "human roadmap does not mention new interface cycle")
    for path in ("AGENTS.md", "docs/GOVERNANCA.md", "SECURITY.md",
                 "CONTRIBUTING.md", "docs/ARQUITETURA.md"):
        checked_file(path)
    return True


def embedded(path):
    html = Path(path).read_text(encoding="utf-8")
    parts = list(EMBED.finditer(html))
    require(len(parts) == 1, "portal must embed exactly one catalog")
    require("<script src=" not in html.lower()
            and "<link rel=\"stylesheet\" href=\"http" not in html.lower()
            and "fetch(" not in html,
            "portal must stay standalone with no network fetches")
    return html, parts[0], json.loads(parts[0].group(2))


def machine_roadmap(data):
    """Derived machine-readable research plan; no duplicate manual status."""
    return {
        "schema": "maintenance-superinteligence.machine-roadmap.v1",
        "version": "1.0.0",
        "snapshotDate": data["snapshot"]["date"],
        "nature": "public_curated_navigation_snapshot_not_live_github_or_approved_study",
        "sourceCatalog": "interfaces/catalog.v1.json",
        "fullRoadmap": "docs/ROADMAP.md",
        "mainCycle": data["snapshot"]["mainCycle"],
        "externalGatesPending": len(data["gates"]),
        "items": data["roadmap"],
        "humanApprovalVerified": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO",
    }


def check():
    data = load()
    validate(data)
    require(machine_roadmap(data) == json.loads(MACHINE_ROADMAP.read_text(encoding="utf-8")),
            "machine-readable ROADMAP.json differs from source catalog")
    for path in PORTALS:
        html, _, value = embedded(path)
        require(value == data, "portal catalog stale: " + path.name)
        require("NO GO" in html and "SAP/ECM" in html,
                "portal does not show explicit safety constraint")
        require("auditoria.html" in html if path.name == "index.html"
                else "index.html" in html,
                "navigation between portals broken")
    return {
        "schema": "maintenance-superinteligence.interfaces-sync-report.v1",
        "catalogVersion": data["version"],
        "snapshotDate": data["snapshot"]["date"],
        "portalsInSync": len(PORTALS),
        "machineRoadmapInSync": True,
        "agentRoles": len(data["agents"]),
        "proceduralSkills": len(data["skills"]),
        "unverifiedExternalGates": len(data["gates"]),
        "snapshotIsLive": False,
        "operationallyApproved": False,
        "decision": "no_go_human_and_ai_interfaces_are_not_external_validation",
    }


def write():
    data = load()
    validate(data)
    MACHINE_ROADMAP.write_text(json.dumps(machine_roadmap(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # The catalog is metadata, never arbitrary HTML or private evidence.
    require("</script" not in compact.lower(),
            "unsafe HTML script-closing sequence in catalog")
    for path in PORTALS:
        original, match, _ = embedded(path)
        updated = (original[:match.start(2)] + compact
                   + original[match.end(2):])
        if updated != original:
            path.write_text(updated, encoding="utf-8")
    return check()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Sync AI index and offline human portal embedded snapshots"
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    report = write() if args.write else check()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
