"""Biblioteca DIDÁTICA de métodos diagnósticos e teste de vínculos FMEA.

Não executa ensaios. Não homologa valores, parâmetros, torques, série ou OEM.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from connectors.fmea_public import (
    ImportRejected, build_consumer_index, load_lock, require, validate_snapshot
)
from evidence.ledger import validate_ledger
from investigations.final_drive import ALLOWED_CHAIN_IDS, investigate


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "methods/catalog.v1.json"
SOURCES_PATH = ROOT / "data/diagnostic-method-sources.v1.json"
METHOD_KEYS = {
    "methodId", "domain", "title", "diagnosticQuestion", "fmeaMethodId",
    "sourceIds", "prerequisites", "expectedObservations", "interpretationLimits",
    "applicabilityGate", "safetyGates", "reviewStatus", "executionStatus",
    "thresholds", "parameterValues", "outputNature"
}
DOMAIN_SAFETY = {
    "oil": {"environmental_containment", "fluid_temperature_and_pressure",
            "safe_access", "sampling_procedure"},
    "hydraulics": {"lockout_isolation", "stored_hydraulic_energy",
                   "pressure_release", "rated_instruments",
                   "authorized_test_setup"},
    "mechanics": {"lockout_isolation", "hot_surfaces",
                  "stored_mechanical_energy", "safe_access"},
    "vibration": {"rotating_machinery", "safe_access",
                  "authorized_operation", "sensor_attachment"},
    "electronics": {"electrical_safety", "authorized_diagnostic_access",
                    "read_only", "configuration_control"},
}
FMEA_METHODS = {"EV-11", "EV-08", "EV-10", "EV-01", "EV-13", "EV-04"}
DOMAIN_MINIMUM = {"oil": 4, "hydraulics": 3, "mechanics": 3,
                  "vibration": 2, "electronics": 2}


def exact(value: object, required: set[str], where: str) -> dict:
    require(isinstance(value, dict) and set(value) == required,
            f"{where}: incorrect or extra fields")
    return value


def words(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= 1000


def string_array(value: object, where: str) -> list[str]:
    require(isinstance(value, list) and value and all(words(x) for x in value),
            f"{where}: nonempty string array required")
    require(len(value) == len(set(value)), f"{where}: duplicate values")
    return value


def validate_sources(registry: object) -> dict[str, dict]:
    reg = exact(registry, {"schema", "version", "purpose", "sources"},
                "method sources")
    require(reg["schema"] == "maintenance-superinteligence.diagnostic-method-sources.v1"
            and reg["version"] == "1.0.0"
            and reg["purpose"] == "general_sources_not_model_specific_procedures",
            "source registry not supported")
    require(isinstance(reg["sources"], list) and len(reg["sources"]) >= 6,
            "source registry incomplete")
    sources = {}
    for item in reg["sources"]:
        exact(item, {"id", "organization", "title", "url", "role",
                     "limitation", "origin"}, "source")
        require(all(words(item[k]) for k in
                    ("id", "organization", "title", "url", "role", "limitation")),
                "source missing metadata/limitations")
        require(item["url"].startswith("https://")
                and item["origin"] in ("fmea_public_reference", "public_independent"),
                "source not public / invalid origin")
        require(item["id"] not in sources, "duplicate source identifier")
        sources[item["id"]] = item
    return sources


def validate_catalog(catalog: object, registry: dict,
                     fmea_snapshot: dict | None = None) -> dict[str, dict]:
    catalog = exact(catalog, {"schema", "version", "knowledgeScope",
                              "approvedForOperationalUse", "sourceRegistry", "methods"},
                    "method catalog")
    require(catalog["schema"] == "maintenance-superinteligence.diagnostic-method-catalog.v1"
            and catalog["version"] == "1.0.0"
            and catalog["knowledgeScope"] == "general_research_not_oem_procedure"
            and catalog["approvedForOperationalUse"] is False
            and catalog["sourceRegistry"] == "data/diagnostic-method-sources.v1.json",
            "catalog semantics, version or approval invalid")
    require(isinstance(catalog["methods"], list) and len(catalog["methods"]) == 14,
            "expected fourteen explicitly reviewed generic methods")
    methods = {}
    ids_by_origin = set()
    for method in catalog["methods"]:
        exact(method, METHOD_KEYS, "method")
        mid = method["methodId"]
        require(isinstance(mid, str) and re.fullmatch(r"MET-[A-Z]+-[A-Z]+", mid),
                "invalid method ID")
        require(mid not in methods, "duplicate method ID")
        require(method["domain"] in DOMAIN_SAFETY
                and words(method["title"]) and words(method["diagnosticQuestion"]),
                f"{mid}: invalid domain or question")
        string_array(method["sourceIds"], mid + ".sourceIds")
        require(set(method["sourceIds"]).issubset(registry),
                f"{mid}: source not registered")
        if method["fmeaMethodId"] is not None:
            require(method["fmeaMethodId"] in FMEA_METHODS,
                    f"{mid}: unauthorized FMEA method code")
            require(method["fmeaMethodId"] not in ids_by_origin,
                    "FMEA method ID duplicated by catalog")
            ids_by_origin.add(method["fmeaMethodId"])
        require(isinstance(method["prerequisites"], list)
                and len(method["prerequisites"]) >= 2, f"{mid}: prerequisites missing")
        seen = set()
        for item in method["prerequisites"]:
            exact(item, {"prerequisiteId", "category", "description"}, "prerequisite")
            require(all(words(v) for v in item.values()),
                    f"{mid}: prerequisite incomplete")
            require(item["prerequisiteId"] not in seen, "duplicate prerequisite")
            seen.add(item["prerequisiteId"])
        seen.clear()
        require(isinstance(method["expectedObservations"], list)
                and len(method["expectedObservations"]) >= 2,
                f"{mid}: observations insufficient")
        for item in method["expectedObservations"]:
            exact(item, {"observationId", "field", "question", "nature"},
                  "expected observation")
            require(all(words(item[k]) for k in ("observationId", "field", "question"))
                    and item["nature"] == "potential_not_measured",
                    f"{mid}: observed test masquerading as proposal")
            require(item["observationId"] not in seen, "duplicate observation field")
            seen.add(item["observationId"])
        require(isinstance(method["interpretationLimits"], list)
                and method["interpretationLimits"], f"{mid}: interpretation limits missing")
        for limit in method["interpretationLimits"]:
            exact(limit, {"limitId", "description", "permittedInference"},
                  "interpretation limit")
            require(words(limit["limitId"]) and words(limit["description"])
                    and limit["permittedInference"] == "question_or_hypothesis_only",
                    f"{mid}: limits claim unsupported certainty")
        gate = exact(method["applicabilityGate"],
                     {"manufacturer", "model", "serialOrArrangement",
                      "technicalPublication", "revision", "status",
                      "approvedForOperationalUse"}, "applicability")
        require(all(gate[key] is None for key in
                    ("manufacturer", "model", "serialOrArrangement",
                     "technicalPublication", "revision"))
                and gate["status"] == "not_verified"
                and gate["approvedForOperationalUse"] is False,
                f"{mid}: model/serial/operational approval not verified")
        require(set(string_array(method["safetyGates"], mid + ".safetyGates"))
                == DOMAIN_SAFETY[method["domain"]],
                f"{mid}: safety prerequirements altered or missing")
        require(method["reviewStatus"] == "generic_conceptual_not_oem"
                and method["executionStatus"] == "proposed_not_executed"
                and method["thresholds"] is None
                and method["parameterValues"] is None
                and method["outputNature"] == "investigation_questions_only",
                f"{mid}: execution/threshold/authority not allowed")
        methods[mid] = method

    require(ids_by_origin == FMEA_METHODS, "FMEA method coverage incomplete")
    counts = Counter(m["domain"] for m in methods.values())
    require(dict(counts) == DOMAIN_MINIMUM,
            f"discipline coverage drift: {dict(counts)}")
    if fmea_snapshot is not None:
        expected_fmea = {t["methodId"]
                         for r in fmea_snapshot["records"]
                         if r["id"] in ALLOWED_CHAIN_IDS
                         for t in r["investigations"]}
        require(expected_fmea == ids_by_origin,
                "catalog FMEA IDs differ from source snapshot")
        upstream_source_map = {s["id"]: s for s in fmea_snapshot["sources"]}
        for sid, source in registry.items():
            if source["origin"] == "fmea_public_reference":
                require(sid in upstream_source_map
                        and source["url"] == upstream_source_map[sid]["url"],
                        f"registered upstream source {sid} differs from frozen FMEA")
    return methods


def build_method_plan(case: dict, report: dict, snapshot: dict, methods: dict,
                      sources: dict) -> dict:
    """Bind eight *planned* tests exactly to original FMEA references."""
    require(report.get("caseId") == case.get("caseId"),
            "case and investigation do not match")
    chain_map = {r["id"]: r for r in snapshot["records"] if r["id"] in ALLOWED_CHAIN_IDS}
    by_fmea = {m["fmeaMethodId"]: m for m in methods.values()
               if m["fmeaMethodId"] is not None}
    linked = []
    for pos, planned in enumerate(report["plannedInvestigations"], start=1):
        rid, code = planned["referenceFmeaId"], planned["methodId"]
        require(rid in chain_map and code in by_fmea,
                "plan: orphan FMEA chain or method")
        matched = [t for t in chain_map[rid]["investigations"]
                   if t["methodId"] == code and
                   t["purpose"] == planned["purposeFromSource"]
                   and t["status"] == "not_performed"]
        require(len(matched) == 1, "plan: FMEA test purpose or status changed")
        method = by_fmea[code]
        require(planned["status"] == "not_performed", "plan: source method marked done")
        linked.append({
            "planId": f"PLAN-{pos:03d}",
            "fmeaChainId": rid,
            "fmeaInvestigationId": matched[0]["id"],
            "fmeaMethodCode": code,
            "methodCatalogId": method["methodId"],
            "sourcePurpose": planned["purposeFromSource"],
            "diagnosticQuestion": method["diagnosticQuestion"],
            "requiredContextQuestions": [
                x["description"] for x in method["prerequisites"]],
            "expectedObservationFields": [
                {"field": x["field"], "question": x["question"],
                 "status": "not_measured"} for x in method["expectedObservations"]],
            "interpretationLimits": [
                x["description"] for x in method["interpretationLimits"]],
            "safetyGates": method["safetyGates"],
            "sourceIds": method["sourceIds"],
            "executionStatus": "proposed_not_executed",
            "oemApplicability": "not_verified",
            "mayExecuteAutomatically": False,
        })
    require(len(linked) == 8, "plan: FMEA eight source investigations not mapped")
    return {
        "schema": "maintenance-superinteligence.diagnostic-method-plan.v1",
        "caseId": case["caseId"], "purpose": "training_questions_only",
        "catalogVersion": "1.0.0",
        "fmeaContentVersion": "1.0.0",
        "fmeaSourceSha256": report["provenance"]["fmeaInputSha256"],
        "coverage": dict(sorted(Counter(m["domain"]
                                        for m in methods.values()).items())),
        "methodsCataloged": len(methods),
        "fmeaMethodsLinked": len(by_fmea),
        "fmeaInvestigationsLinked": len(linked),
        "suggestedQuestions": linked,
        "researchSources": [
            {"id": sid, "url": s["url"], "limitation": s["limitation"]}
            for sid, s in sorted(sources.items())],
        "decision": "needs_oem_and_independent_review",
        "approvedForOperationalUse": False,
        "mayExecuteTests": False,
        "confirmedComponentFailure": None,
        "notes": [
            "A biblioteca apenas transforma métodos genéricos em perguntas e campos.",
            "Os oito métodos FMEA permanecem não executados; nenhum valor OEM foi importado.",
            "Fontes de fabricantes descrevem princípios; não são procedimento CAT 777E por série.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--investigation", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--sources", type=Path, default=SOURCES_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        lock = load_lock()
        source = validate_snapshot(args.snapshot.read_bytes(), lock)
        case = json.loads(args.case.read_text(encoding="utf-8"))
        report = json.loads(args.investigation.read_text(encoding="utf-8"))
        expected = investigate(case, build_consumer_index(source, lock), lock)
        require(report == expected, "investigation differs from authenticated reconstructed case")
        validate_ledger(report["evidenceLedger"], case=case, investigation=report)
        sources = validate_sources(json.loads(args.sources.read_text(encoding="utf-8")))
        methods = validate_catalog(json.loads(args.catalog.read_text(encoding="utf-8")),
                                   sources, source)
        plan = build_method_plan(case, report, source, methods, sources)
        serialized = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(exc),
                          "mayExecuteTests": False}, ensure_ascii=False),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
