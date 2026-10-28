"""Cycle 27: independent authored synthetic differential question regression.

This is NOT a field diagnostic accuracy study. Context booleans represent fictional
DOCUMENTARY availability, never measurements, OEM applicability or permission.
"""
from __future__ import annotations
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

from pilot.change_review_packets import digest, require, ReviewRejected

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "benchmarks/mechanical-reasoning-cases.v1.json"
ORACLE_PATH = ROOT / "benchmarks/mechanical-reasoning-oracle.v1.json"

DOMAIN_PATHS = {
  "final_drive": {
    "symptom": "Amostra de óleo de comando final com interpretação inicialmente indeterminada",
    "hypotheses": [
      "fluid_baseline_change",
      "sample_provenance_error",
      "wear_or_contamination_unconfirmed"
    ],
    "gates": [
      [
        "fluid_identity",
        "confirm_fluid_product_identity",
        "Confirmar identificação de produto e formulação antes de interpretar perfil químico."
      ],
      [
        "service_history",
        "reconcile_service_history",
        "Verificar histórico documental de substituição e mistura antes de inferir deterioração."
      ],
      [
        "sampling_trace",
        "confirm_sampling_trace",
        "Verificar origem, ponto e rastreabilidade da amostra antes de atribuir contaminante ao compartimento."
      ],
      [
        "comparable_trend",
        "request_comparable_trend",
        "Comparar resultados tecnicamente equivalentes e tendência antes de atribuir mecanismo de desgaste."
      ]
    ]
  },
  "hydraulics": {
    "symptom": "Atuação hidráulica lenta sem condição de ensaio caracterizada",
    "hypotheses": [
      "load_demand_difference",
      "control_valve_or_regulation",
      "supply_or_temperature_condition"
    ],
    "gates": [
      [
        "load_context",
        "reconcile_load_and_duty",
        "Esclarecer demanda e carga, pois lentidão isolada não caracteriza bomba defeituosa."
      ],
      [
        "temperature_context",
        "establish_temperature_context",
        "Identificar condição térmica de operação antes de comparar desempenho hidráulico."
      ],
      [
        "circuit_documentation",
        "locate_applicable_circuit",
        "Identificar arranjo do circuito e documentação aplicável antes de indicar ponto de medição."
      ],
      [
        "authorized_measurement_plan",
        "request_authorized_test_plan",
        "Solicitar plano e método de teste aprovado, sem criar pressão nominal ou autorizar instrumentação."
      ]
    ]
  },
  "electronics": {
    "symptom": "Código eletrônico informado sem correlação física comprovada",
    "hypotheses": [
      "historical_or_transient_event",
      "sensor_or_wiring_circuit",
      "physical_system_condition"
    ],
    "gates": [
      [
        "ecm_identity",
        "identify_ecm_and_configuration",
        "Identificar módulo e configuração antes de interpretar significado do código."
      ],
      [
        "active_logged_context",
        "distinguish_active_from_logged",
        "Distinguir código ativo de registro histórico antes de imputar falha física."
      ],
      [
        "event_timeline",
        "reconcile_event_time",
        "Confrontar tempo do evento e condição operacional antes de concluir recorrência."
      ],
      [
        "independent_signal_plan",
        "request_independent_signal_check",
        "Solicitar verificação independente autorizada, sem condenar sensor ou ECM."
      ]
    ]
  },
  "cooling": {
    "symptom": "Aquecimento reportado em sistema de arrefecimento sem diagnóstico de causa",
    "hypotheses": [
      "airflow_heat_rejection",
      "coolant_circulation_or_inventory",
      "instrumentation_or_duty_cycle"
    ],
    "gates": [
      [
        "duty_cycle",
        "confirm_load_and_duty",
        "Identificar carga e ciclo operacional antes de comparar comportamento térmico."
      ],
      [
        "airflow_condition",
        "characterize_airflow",
        "Caracterizar condição de rejeição de calor/fluxo de ar sem supor falha de ventilador."
      ],
      [
        "coolant_inventory",
        "check_coolant_context",
        "Confirmar contexto de nível e fluido por procedimento seguro, sem presumir vazamento."
      ],
      [
        "thermal_measurement_plan",
        "request_thermal_measurement_plan",
        "Solicitar método de medição térmica aprovado e limites OEM efetivos, sem inventar especificação."
      ]
    ]
  }
}
# Domain dictionaries above are frozen author-curated qualitative context requirements.
FAMILIES = tuple(DOMAIN_PATHS)
DENY_KEYS = ("mayCreateWorkOrder", "mayReleaseEquipment", "mayRunTests")
CASE_KEYS = {"caseId", "familyId", "scenarioVariant", "fictionalSymptom",
             "unresolvedContradiction", "contextAvailable",
             "observationNature", "confirmedRootCause", *DENY_KEYS}
VARIANTS = ("conflict", "first_missing", "second_missing",
            "third_missing", "fourth_missing", "context_complete")


def validate_cases(manifest):
    require(isinstance(manifest, dict) and set(manifest) ==
            {"schema", "version", "purpose", "oemEffectivityVerified",
             "realFieldEvidence", "reviewedByIndependentMechanicalExpert",
             "operationallyApproved", "cases"}, "case manifest structure")
    require(manifest["schema"] == "maintenance-superinteligence.mechanical-reasoning-cases.v1"
            and manifest["version"] == "1.0.0"
            and manifest["purpose"] == "authored_synthetic_differential_reasoning_regression"
            and all(manifest[k] is False for k in ("oemEffectivityVerified",
            "realFieldEvidence", "reviewedByIndependentMechanicalExpert",
            "operationallyApproved")), "field/OEM/expert status promoted")
    cases = manifest["cases"]
    require(isinstance(cases, list) and len(cases) == 24, "expected 24 authored cases")
    for idx, case in enumerate(cases, 1):
        require(isinstance(case, dict) and set(case) == CASE_KEYS, "case keys changed")
        family = tuple(FAMILIES)[(idx - 1) // 6]
        variant = VARIANTS[(idx - 1) % 6]
        info = DOMAIN_PATHS[family]
        require(case["caseId"] == f"SIM-MECH-{idx:03d}"
                and case["familyId"] == family
                and case["scenarioVariant"] == variant
                and case["fictionalSymptom"] == info["symptom"]
                and case["observationNature"] == "synthetic_narrative_not_measured"
                and case["confirmedRootCause"] is None
                and all(case[k] is False for k in DENY_KEYS),
                "fixture identity, physical proof or authority mutated")
        gate_names = [x[0] for x in info["gates"]]
        context = case["contextAvailable"]
        require(isinstance(context, dict) and set(context) == set(gate_names)
                and all(type(x) is bool for x in context.values())
                and type(case["unresolvedContradiction"]) is bool,
                "nonboolean or unknown gate in fixture")
        n = (idx - 1) % 6
        require(case["unresolvedContradiction"] is (n == 0)
                and all(context[k] is (n != 0 and j < n - 1)
                        for j, k in enumerate(gate_names)),
                "scenario mutation changed staged evidence availability")
    return cases


def validate_oracle(oracle, cases):
    require(isinstance(oracle, dict) and set(oracle) ==
            {"schema", "version", "nature", "independentExpertValidation",
             "realDiagnosticAccuracyMeasured", "expectations"},
            "unexpected oracle fields")
    require(oracle["schema"] == "maintenance-superinteligence.mechanical-reasoning-oracle.v1"
            and oracle["version"] == "1.0.0"
            and oracle["nature"] == "author_editorial_expectations_not_measured_truth"
            and oracle["independentExpertValidation"] is False
            and oracle["realDiagnosticAccuracyMeasured"] is False,
            "oracle fraudulently claims expert or field accuracy")
    expected = oracle["expectations"]
    require(isinstance(expected, list) and len(expected) == len(cases),
            "oracle coverage incomplete")
    require({x.get("caseId") for x in expected} ==
            {x["caseId"] for x in cases}, "oracle identifiers mismatch")
    require(all(isinstance(x, dict) and set(x) ==
                {"caseId", "familyId", "expectedQuestionId",
                 "expectedAbstention", "expectedOpenHypothesisCount"}
                and x["expectedAbstention"] is True
                and x["expectedOpenHypothesisCount"] == 3
                and isinstance(x["expectedQuestionId"], str)
                for x in expected), "oracle promotes or omits requirements")
    for item, case in zip(expected, cases):
        require(item["caseId"] == case["caseId"]
                and item["familyId"] == case["familyId"],
                "oracle reordering or family drift")
    return expected


def investigate(case):
    info = DOMAIN_PATHS[case["familyId"]]
    context = case["contextAvailable"]
    if case["unresolvedContradiction"]:
        question = "reconcile_conflicting_reports"
        rationale = "Contradições na narrativa impedem comparação válida de mecanismos."
    else:
        question, rationale = "escalate_to_engineer_for_review", (
            "Dados documentais presentes no exercício não confirmam causa, "
            "autorizam teste nem substituem parecer técnico.")
        for gate, candidate, reason in info["gates"]:
            if not context[gate]:
                question, rationale = candidate, reason
                break
    return {"caseId":case["caseId"],"familyId":case["familyId"],
            "selectedQuestionId":question,"selectionRationale":rationale,
            "hypotheses":[{"id":h,"status":"open_not_confirmed","probability":None}
                          for h in info["hypotheses"]],
            "confirmedRootCause":None,"testExecuted":False,
            "reviewRequired":True,"oemEffectivityVerified":False,
            "evidenceIsSimulated":True,"mayCreateWorkOrder":False,
            "mayRunTests":False,"mayReleaseEquipment":False}


def evaluate(manifest, oracle):
    cases = validate_cases(manifest)
    expected = validate_oracle(oracle, cases)
    result = []
    for case, truth in zip(cases, expected):
        answer = investigate(case)  # oracle is NOT consulted by the selector
        matched = (answer["selectedQuestionId"] == truth["expectedQuestionId"])
        require(answer["confirmedRootCause"] is None
                and answer["testExecuted"] is False
                and answer["reviewRequired"] is True
                and answer["oemEffectivityVerified"] is False
                and all(answer[k] is False for k in DENY_KEYS)
                and len(answer["hypotheses"]) == 3
                and all(h["status"] == "open_not_confirmed" and h["probability"] is None
                        for h in answer["hypotheses"]), "unsafe reasoning output")
        result.append({"caseId":case["caseId"],"familyId":case["familyId"],
                       "variant":case["scenarioVariant"],
                       "selectedQuestionId":answer["selectedQuestionId"],
                       "expectedQuestionId":truth["expectedQuestionId"],
                       "agreesWithAuthoredOracle":matched,
                       "abstainsFromDiagnosis":True,
                       "openHypotheses":answer["hypotheses"],
                       "reason":answer["selectionRationale"],
                       "prohibitedOperationalAuthority":True})
    per_domain = {f:{"total":sum(x["familyId"]==f for x in result),
                      "matched":sum(x["familyId"]==f and x["agreesWithAuthoredOracle"] for x in result)}
                  for f in FAMILIES}
    return {"schema":"maintenance-superinteligence.mechanical-reasoning-report.v1",
            "version":"1.0.0","mode":"synthetic_editorial_regression",
            "manifestDigest":digest(manifest),"oracleDigest":digest(oracle),
            "caseCount":len(result),
            "agreementWithAuthoredOracle":{"matched":sum(x["agreesWithAuthoredOracle"] for x in result),
                                             "total":len(result)},
            "byDomain":per_domain,
            "cases":result,
            "diagnosticAccuracyMeasured":False,
            "independentMechanicalReviewCompleted":False,
            "physicalCausesConfirmed":0,"fieldMeasurements":0,
            "mayClaimDiagnosticValidity":False,
            "mayIssueWorkOrders":False,
            "mayReleaseEquipment":False,
            "decision":"educational_only_no_go"}


def verify_report(report, manifest, oracle):
    require(report == evaluate(manifest, oracle), "benchmark output forged or stale")
    return True


def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.mechanical-reasoning-report.v1"
            and report.get("decision")=="educational_only_no_go"
            and report.get("diagnosticAccuracyMeasured") is False
            and report.get("mayClaimDiagnosticValidity") is False
            and report.get("mayReleaseEquipment") is False,
            "HTML unsafe to publish")
    sections = "".join("<section><strong>"+escape(c["caseId"])+" — "+
                       escape(c["familyId"])+"</strong><p>"+escape(c["reason"])+
                       "</p><p>Next question: "+escape(c["selectedQuestionId"])+
                       " | editorial agreement: "+str(c["agreesWithAuthoredOracle"])+
                       ". Causa não confirmada.</p></section>"
                       for c in report["cases"])
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            'form-action &apos;none&apos;"><title>Mechanical reasoning regression</title>'
            '<style>body{font:15px system-ui;max-width:950px;margin:2em auto;'
            'padding:1em}section{border:1px solid #aaa;margin:1em 0;padding:1em}'
            '</style></head><body><h1>Ciclo 27 — Benchmark editorial, NO GO</h1>'
            '<p>24 cenários fictícios. Concordância com roteiro autoral não é '
            'acurácia diagnóstica, parecer OEM ou autorização operacional.</p>'
            + sections + '</body></html>')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases",type=Path,default=CASES_PATH)
    parser.add_argument("--oracle",type=Path,default=ORACLE_PATH)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    manifest=json.loads(args.cases.read_text(encoding="utf-8"))
    oracle=json.loads(args.oracle.read_text(encoding="utf-8"))
    report=evaluate(manifest,oracle)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(report),encoding="utf-8")
    return report

if __name__=="__main__":
    main()
