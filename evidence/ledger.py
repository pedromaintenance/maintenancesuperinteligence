"""Ledger DIDÁTICO de evidências: observação != ensaio != interpretação.

Nenhum status deste módulo confirma causa, teste OEM, serviço ou dado real.
Hashes encadeados detectam mutação acidental; não são assinaturas de autenticidade.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from connectors.fmea_public import ImportRejected, require


LEDGER_SCHEMA = "maintenance-superinteligence.evidence-ledger.v1"
HEX64 = re.compile(r"^[a-f0-9]{64}$")
EVENT_NAMES = ("case_input", "observation_register", "planned_tests",
               "simulated_test_results", "qualitative_evidence", "hypothesis_review")
RECORD_KEYS = {"schema", "caseId", "sourceBinding", "caseDigest", "observations",
               "testMethods", "testResults", "evidence", "hypothesisAssessments",
               "humanReview", "auditTrail"}
CONTEXT_KEYS = {"machineCondition", "samplePoint", "observedAt", "meterHours",
                "instrumentId", "calibrationReference"}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _fields(obj: object, fields: set[str], label: str) -> dict:
    require(isinstance(obj, dict) and set(obj) == fields,
            f"{label}: expected exact fields {sorted(fields)}")
    return obj


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2048


def _sim_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"SIM-[A-Za-z0-9_-]+", value) is not None


def _unique(items: list[dict], field: str, scope: str) -> set[str]:
    ids = [x[field] for x in items]
    require(all(isinstance(x, str) and x for x in ids), f"{scope}: invalid IDs")
    require(len(ids) == len(set(ids)), f"{scope}: duplicate IDs")
    return set(ids)


def _check_context(context: object, name: str) -> None:
    _fields(context, CONTEXT_KEYS, name)
    # A baseline ausente não é inferida; metadados contextuais são opcionais.
    for key in ("machineCondition", "samplePoint", "observedAt",
                "instrumentId", "calibrationReference"):
        require(context[key] is None or _text(context[key]),
                f"{name}.{key}: invalid text")
    require(context["meterHours"] is None or
            (type(context["meterHours"]) in (float, int)
             and 0 <= context["meterHours"] < 1_000_000),
            f"{name}.meterHours: invalid meter value")


def _empty_context() -> dict:
    return {key: None for key in sorted(CONTEXT_KEYS)}


def _sections(ledger: dict) -> dict:
    return {
        "case_input": {"caseId": ledger["caseId"], "inputDigest": ledger["caseDigest"],
                       "sourceBinding": ledger["sourceBinding"]},
        "observation_register": ledger["observations"],
        "planned_tests": ledger["testMethods"],
        "simulated_test_results": ledger["testResults"],
        "qualitative_evidence": ledger["evidence"],
        "hypothesis_review": {
            "assessments": ledger["hypothesisAssessments"],
            "review": ledger["humanReview"],
        },
    }


def _seal(ledger: dict) -> list:
    """Deterministic hash chain over all sections; not proof of identity."""
    chain = []
    previous = "0" * 64
    for seq, (kind, payload) in enumerate(_sections(ledger).items(), start=1):
        digest = sha(payload)
        event = {"sequence": seq, "kind": kind, "payloadSha256": digest,
                 "previousSha256": previous}
        event["eventSha256"] = sha(event)
        previous = event["eventSha256"]
        chain.append(event)
    return chain


def build_ledger(case: dict, investigation: dict, simulated_test_results: list | None = None) -> dict:
    """Deriva observações reportadas do cenário; jamais converte relatos em testes executados."""
    require(investigation.get("caseId") == case.get("caseId"),
            "ledger: caseId mismatch")
    observations = [{
        "observationId": "OBS-000", "kind": "operator_report",
        "signalCode": None, "result": "reported",
        "description": case["complaint"], "sourceRef": f"SIM-{case['caseId']}",
        "evidenceNature": "simulation", "context": _empty_context(),
        "limitations": ["Relato fictício não medido, sem confirmação independente."],
    }]
    code_to_observation = {}
    for number, s in enumerate(case["signals"], start=1):
        oid = f"OBS-{number:03d}"
        code_to_observation[s["code"]] = oid
        observations.append({
            "observationId": oid, "kind": "coded_report",
            "signalCode": s["code"], "result": s["result"],
            "description": f"Código didático reportado: {s['code']}",
            "sourceRef": s["sourceRef"], "evidenceNature": "simulation",
            "context": _empty_context(),
            "limitations": ["Código de cenário é relato estruturado; não equivale a medição ou ensaio executado."],
        })

    methods = []
    for i, t in enumerate(investigation["plannedInvestigations"], 1):
        methods.append({
            "testMethodId": f"TM-{i:03d}",
            "fmeaChainId": t["referenceFmeaId"],
            "methodId": t["methodId"], "purpose": t["purposeFromSource"],
            "status": "proposed_not_executed",
            "applicability": "unverified_oem_series",
            "safetyGate": t["requiredGate"],
            "sourceVersion": investigation["provenance"]["fmeaContentVersion"],
        })
    results = list(simulated_test_results or [])
    evidence = []
    evidence_number = 1
    assessments = []
    for h in investigation["hypotheses"]:
        links = []
        for relation, signal_codes in (
            ("consistent_with", h["supportingSignals"]),
            ("inconsistent_with", h["weakeningSignals"]),
        ):
            for code in signal_codes:
                evid_id = f"EVD-{evidence_number:03d}"
                evidence_number += 1
                evidence.append({
                    "evidenceId": evid_id,
                    "observationId": code_to_observation[code],
                    "testResultId": None, "hypothesisId": h["id"],
                    "relation": relation, "nature": "didactic_inference",
                    "sourceRef": next(s["sourceRef"] for s in case["signals"]
                                      if s["code"] == code),
                    "limitations": [
                        "Compatibilidade conceitual não discrimina necessariamente causa.",
                        "Nenhum ensaio foi executado pelo sistema.",
                    ],
                })
                links.append(evid_id)
        assessments.append({
            "hypothesisId": h["id"], "evidenceIds": links,
            "disposition": h["disposition"],
            "rootCauseConfirmed": False,
            "confidence": None,
            "reviewStatus": "pending_independent_review",
        })
    # Todo sinal sem uso interpretativo é registrado como indício não-discriminante,
    # não convertido em evidência contra/para uma hipótese.
    used_observations = {e["observationId"] for e in evidence}
    for s in case["signals"]:
        oid = code_to_observation[s["code"]]
        if oid not in used_observations:
            evidence.append({
                "evidenceId": f"EVD-{evidence_number:03d}",
                "observationId": oid, "testResultId": None,
                "hypothesisId": None, "relation": "not_discriminating",
                "nature": "didactic_inference", "sourceRef": s["sourceRef"],
                "limitations": [
                    "Observação não discriminante; não justifica identificar defeito.",
                ],
            })
            evidence_number += 1
    ledger = {
        "schema": LEDGER_SCHEMA,
        "caseId": case["caseId"],
        "sourceBinding": {
            "fmeaInputSha256": investigation["provenance"]["fmeaInputSha256"],
            "contentVersion": investigation["provenance"]["fmeaContentVersion"],
            "sourceKind": "pinned_public_hypotheses",
        },
        "caseDigest": sha(case),
        "observations": observations,
        "testMethods": methods,
        "testResults": results,
        "evidence": evidence,
        "hypothesisAssessments": assessments,
        "humanReview": {
            "required": True,
            "status": "pending",
            "reviewerId": None,
            "oemApplicabilityVerified": False,
            "operationalReleaseAuthorized": False,
        },
        "auditTrail": [],
    }
    ledger["auditTrail"] = _seal(ledger)
    validate_ledger(ledger, case=case, investigation=investigation)
    return ledger


def validate_ledger(ledger: object, *, case: dict | None = None,
                    investigation: dict | None = None) -> dict:
    """Verifica relações, ontologia, resultados e integridade de todo o ledger."""
    _fields(ledger, RECORD_KEYS, "ledger")
    require(ledger["schema"] == LEDGER_SCHEMA, "ledger: schema incompatible")
    require(_sim_id(ledger["caseId"]), "ledger: only SIM-* cases allowed")
    binding = _fields(ledger["sourceBinding"],
                      {"fmeaInputSha256", "contentVersion", "sourceKind"},
                      "sourceBinding")
    require(isinstance(binding["fmeaInputSha256"], str)
            and HEX64.fullmatch(binding["fmeaInputSha256"]),
            "ledger: invalid FMEA checksum")
    require(binding["sourceKind"] == "pinned_public_hypotheses"
            and binding["contentVersion"] == "1.0.0",
            "ledger: unsupported knowledge source")
    require(isinstance(ledger["caseDigest"], str)
            and HEX64.fullmatch(ledger["caseDigest"]),
            "ledger: invalid case digest")
    if case is not None:
        require(sha(case) == ledger["caseDigest"] and case["caseId"] == ledger["caseId"],
                "ledger: input case was mutated or changed")
    for section in ("observations", "testMethods", "testResults",
                    "evidence", "hypothesisAssessments"):
        require(isinstance(ledger[section], list), f"ledger: {section} is not a list")
    require(len(ledger["observations"]) >= 1, "ledger: operator report missing")
    observation_ids = _unique(ledger["observations"], "observationId", "observations")
    require(len(ledger["observations"]) <= 14, "ledger: too many synthetic observations")
    for obs in ledger["observations"]:
        _fields(obs, {"observationId", "kind", "signalCode", "result",
                      "description", "sourceRef", "evidenceNature", "context", "limitations"},
                "observation")
        require(obs["kind"] in ("operator_report", "coded_report"),
                "observation: invalid kind")
        require(obs["evidenceNature"] == "simulation" and _sim_id(obs["sourceRef"]),
                "observation: real or unsupported origin")
        require(_text(obs["description"]) and obs["limitations"]
                and all(_text(x) for x in obs["limitations"]),
                "observation: missing caveat")
        _check_context(obs["context"], "observation.context")
        if obs["kind"] == "operator_report":
            require(obs["signalCode"] is None and obs["result"] == "reported",
                    "observation: operator report is not a measurement")
        else:
            require(_text(obs["signalCode"])
                    and obs["result"] in ("present", "absent", "inconclusive"),
                    "observation: invalid coded report")
    require(ledger["observations"][0]["kind"] == "operator_report",
            "ledger: first observation must be operator report")

    methods = {}
    for method in ledger["testMethods"]:
        _fields(method, {"testMethodId", "fmeaChainId", "methodId", "purpose",
                         "status", "applicability", "safetyGate", "sourceVersion"},
                "testMethod")
        require(method["status"] == "proposed_not_executed",
                "testMethod: source test falsely marked performed")
        require(method["applicability"] == "unverified_oem_series"
                and method["sourceVersion"] == "1.0.0",
                "testMethod: OEM applicability not verified")
        require(all(_text(method[k]) for k in
                    ("testMethodId", "fmeaChainId", "methodId", "purpose", "safetyGate")),
                "testMethod: missing traceability")
        require(method["testMethodId"] not in methods, "testMethod: duplicate ID")
        methods[method["testMethodId"]] = method
    require(len(methods) == 8, "ledger: expected eight proposed FMEA investigations")
    test_result_ids = _unique(ledger["testResults"], "testResultId", "testResults")
    for result in ledger["testResults"]:
        _fields(result, {"testResultId", "testMethodId", "nature", "status",
                         "result", "sourceRef", "context", "limitations"},
                "testResult")
        require(_sim_id(result["testResultId"]) and _sim_id(result["sourceRef"]),
                "testResult: synthetic IDs required")
        require(result["testMethodId"] in methods, "testResult: orphan method")
        require(result["nature"] == "simulation"
                and result["status"] == "simulated_execution"
                and result["result"] in ("indicator_present", "indicator_absent", "inconclusive"),
                "testResult: real execution or result not allowed")
        _check_context(result["context"], "testResult.context")
        require(_text(result["context"]["machineCondition"])
                and _text(result["context"]["samplePoint"])
                and _text(result["context"]["observedAt"])
                and _text(result["context"]["instrumentId"])
                and _text(result["context"]["calibrationReference"])
                and type(result["context"]["meterHours"]) in (int, float),
                "testResult: simulated execution needs full measurement context")
        require(isinstance(result["limitations"], list)
                and result["limitations"] and all(_text(x) for x in result["limitations"]),
                "testResult: limitations required")
    evidence_ids = _unique(ledger["evidence"], "evidenceId", "evidence")
    assessment_ids = _unique(ledger["hypothesisAssessments"], "hypothesisId",
                             "hypothesisAssessments")
    assessment_map = {x["hypothesisId"]: x for x in ledger["hypothesisAssessments"]}
    require(len(assessment_ids) == 7, "ledger: seven competing hypotheses required")
    for ev in ledger["evidence"]:
        _fields(ev, {"evidenceId", "observationId", "testResultId", "hypothesisId",
                     "relation", "nature", "sourceRef", "limitations"}, "evidence")
        require(ev["nature"] == "didactic_inference" and _sim_id(ev["sourceRef"]),
                "evidence: not a measured or field fact")
        require(ev["relation"] in ("consistent_with", "inconsistent_with",
                                  "not_discriminating"),
                "evidence: relation invalid")
        refs = (ev["observationId"] is not None) + (ev["testResultId"] is not None)
        require(refs == 1, "evidence: exactly one origin (no circular references)")
        require(ev["observationId"] is None or ev["observationId"] in observation_ids,
                "evidence: orphan observation")
        require(ev["testResultId"] is None or ev["testResultId"] in test_result_ids,
                "evidence: orphan test result")
        require(ev["hypothesisId"] is None or ev["hypothesisId"] in assessment_ids,
                "evidence: orphan hypothesis")
        if ev["relation"] == "not_discriminating":
            require(ev["hypothesisId"] is None, "evidence: neutral cannot assert a hypothesis")
        else:
            require(ev["hypothesisId"] in assessment_ids,
                    "evidence: non-neutral relationship needs hypothesis")
        require(isinstance(ev["limitations"], list) and ev["limitations"]
                and all(_text(x) for x in ev["limitations"]),
                "evidence: limitations missing")
    for a in ledger["hypothesisAssessments"]:
        _fields(a, {"hypothesisId", "evidenceIds", "disposition",
                    "rootCauseConfirmed", "confidence", "reviewStatus"}, "assessment")
        require(a["rootCauseConfirmed"] is False and a["confidence"] is None
                and a["reviewStatus"] == "pending_independent_review",
                "assessment: unreviewed hypothesis falsely confirmed/scored")
        require(a["disposition"] in (
            "open_not_confirmed", "mixed_evidence_open_not_confirmed",
            "indications_only_not_confirmed", "weakened_not_excluded"),
            "assessment: inadmissible disposition")
        require(isinstance(a["evidenceIds"], list)
                and len(a["evidenceIds"]) == len(set(a["evidenceIds"]))
                and set(a["evidenceIds"]).issubset(evidence_ids),
                "assessment: orphan/duplicate evidence link")
        require(all(next(e for e in ledger["evidence"] if e["evidenceId"] == eid)["hypothesisId"]
                    == a["hypothesisId"] for eid in a["evidenceIds"]),
                "assessment: evidence linked to wrong hypothesis")
    for e in ledger["evidence"]:
        if e["hypothesisId"] is not None:
            require(e["evidenceId"] in assessment_map[e["hypothesisId"]]["evidenceIds"],
                    "evidence: assessment missing backlink")
    review = _fields(ledger["humanReview"],
                     {"required", "status", "reviewerId", "oemApplicabilityVerified",
                      "operationalReleaseAuthorized"}, "review")
    require(review == {"required": True, "status": "pending", "reviewerId": None,
                       "oemApplicabilityVerified": False,
                       "operationalReleaseAuthorized": False},
            "review: false human/OEM/operational approval")
    if investigation is not None:
        require(investigation["caseId"] == ledger["caseId"]
                and investigation["provenance"]["fmeaInputSha256"] ==
                binding["fmeaInputSha256"], "ledger: FMEA/case provenance mismatch")
        hypothesis_map = {h["id"]: h for h in investigation["hypotheses"]}
        require(set(hypothesis_map) == assessment_ids, "ledger: hypothesis drift")
        require(all(a["disposition"] == hypothesis_map[a["hypothesisId"]]["disposition"]
                    for a in ledger["hypothesisAssessments"]),
                "ledger: modified hypothesis status")
        require(len(investigation["plannedInvestigations"]) == len(methods),
                "ledger: method mismatch")
        for i, (m, t) in enumerate(zip(ledger["testMethods"],
                                       investigation["plannedInvestigations"]), 1):
            require(m["testMethodId"] == f"TM-{i:03d}"
                    and m["fmeaChainId"] == t["referenceFmeaId"]
                    and m["methodId"] == t["methodId"] and m["purpose"] == t["purposeFromSource"],
                    "ledger: FMEA test source altered")
        if case is not None:
            expected_observations = len(case["signals"]) + 1
            require(len(ledger["observations"]) == expected_observations,
                    "ledger: missing or invented observations")
            report = ledger["observations"][0]
            require(report["description"] == case["complaint"]
                    and report["sourceRef"] == f"SIM-{case['caseId']}",
                    "ledger: operator report provenance drift")
            for obs, signal in zip(ledger["observations"][1:], case["signals"]):
                require(obs["kind"] == "coded_report"
                        and obs["signalCode"] == signal["code"]
                        and obs["result"] == signal["result"]
                        and obs["sourceRef"] == signal["sourceRef"],
                        "ledger: observation and case signal provenance drift")
            expected_relations = set()
            for hyp in investigation["hypotheses"]:
                expected_relations.update(
                    (code, "consistent_with", hyp["id"])
                    for code in hyp["supportingSignals"])
                expected_relations.update(
                    (code, "inconsistent_with", hyp["id"])
                    for code in hyp["weakeningSignals"])
            actual_relations = set()
            for ev in ledger["evidence"]:
                if ev["observationId"] is not None:
                    observed = next(o for o in ledger["observations"]
                                    if o["observationId"] == ev["observationId"])
                    require(ev["sourceRef"] == observed["sourceRef"],
                            "ledger: evidence source reference drift")
                    require(observed["kind"] == "coded_report",
                            "ledger: operator narrative cannot act as measured evidence")
                    if ev["relation"] != "not_discriminating":
                        actual_relations.add(
                            (observed["signalCode"], ev["relation"], ev["hypothesisId"]))
            require(actual_relations == expected_relations,
                    "ledger: evidence causal mapping differs from pilot rubric")
            interpreted_codes = {code for code, _, _ in expected_relations}
            neutral_expected = {s["code"] for s in case["signals"]} - interpreted_codes
            neutral_actual = {next(o["signalCode"] for o in ledger["observations"]
                                   if o["observationId"] == e["observationId"])
                              for e in ledger["evidence"]
                              if e["relation"] == "not_discriminating"}
            require(neutral_expected == neutral_actual,
                    "ledger: missing or invented neutral observations")
    trail = ledger["auditTrail"]
    require(isinstance(trail, list) and len(trail) == len(EVENT_NAMES),
            "ledger: audit trail missing")
    require(trail == _seal(ledger), "ledger: hash chain or payload mismatch")
    return ledger
