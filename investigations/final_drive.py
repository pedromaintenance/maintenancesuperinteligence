#!/usr/bin/env python3
"""Investigação diferencial DIDÁTICA de comando final: não é diagnóstico OEM.

Lê um índice FMEA validado pelo importador público do ciclo 02.
Aceita exclusivamente casos sintéticos e evidências simuladas.
Sem rede, sem LLM, sem inferência de valores OEM, sem comandos a máquinas.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from connectors.fmea_public import ImportRejected, load_lock, require


PILOT_SCHEMA = "maintenance-superinteligence.final-drive-case.v1"
OUTPUT_SCHEMA = "maintenance-superinteligence.final-drive-investigation.v1"
ALLOWED_CHAIN_IDS = ("FC-FD-001", "FC-FD-002", "FC-FD-003", "FC-FD-004")
EXTRA_HYPOTHESES = {
    "PILOT-FORMULATION": "Mudança de formulação ou baseline sem dano demonstrado",
    "PILOT-SAMPLE": "Indício de contaminação originado na coleta ou identificação",
    "PILOT-OTHER-NOISE": "Ruído de freio, pneu ou outro conjunto externo ao redutor",
}
SIGNAL_LABELS = {
    "additive_profile_changed": "Diferença de perfil de aditivos informada",
    "lubricant_change_documented": "Troca de produto/formulação documentada no exercício",
    "sample_identity_disputed": "Identificação/coleta da amostra sob dúvida",
    "water_retest_confirmed": "Recoleta simulada confirmou presença de água",
    "water_retest_not_reproduced": "Recoleta simulada não reproduziu indício de água",
    "particle_trend_increasing": "Tendência de partículas crescente em simulação",
    "magnetic_debris_increasing": "Acúmulo magnético crescente simulado",
    "noise_localized_final_drive": "Ruído localizado no redutor segundo inspeção simulada",
    "noise_localized_external": "Ruído localizado em fonte externa ao redutor em simulação",
    "oil_level_below_reference": "Nível informado abaixo de referência (não OEM)",
    "lubricant_history_unchanged": "Histórico simulado não mostra troca de produto",
    "viscosity_outlier": "Viscosidade atípica em dados simulados",
    "reported_loss_of_function": "Perda funcional relatada no cenário fictício",
}
# Relações propostas pelo piloto: ligações qualitativas, não probabilidades,
# nem inferências OEM ou atribuição de componente danificado.
# Evidência neutra é deliberadamente possível.
SIGNAL_RULES = {
    "additive_profile_changed": ((), ()),
    "lubricant_change_documented": (("PILOT-FORMULATION",), ()),
    "sample_identity_disputed": (("PILOT-SAMPLE",), ()),
    "water_retest_confirmed": (("FC-FD-002",), ("PILOT-SAMPLE",)),
    "water_retest_not_reproduced": (("PILOT-SAMPLE",), ("FC-FD-002",)),
    "particle_trend_increasing": (("FC-FD-001", "FC-FD-003", "FC-FD-004"), ()),
    "magnetic_debris_increasing": (("FC-FD-001", "FC-FD-004"), ()),
    "noise_localized_final_drive": (("FC-FD-004",), ("PILOT-OTHER-NOISE",)),
    "noise_localized_external": (("PILOT-OTHER-NOISE",), ("FC-FD-004",)),
    "oil_level_below_reference": (("FC-FD-003",), ()),
    "lubricant_history_unchanged": ((), ("PILOT-FORMULATION",)),
    "viscosity_outlier": (("FC-FD-003",), ()),
    "reported_loss_of_function": ((), ()),
}
DIVERGENT_PAIRS = (
    ("water_retest_confirmed", "water_retest_not_reproduced",
     "Resultados divergentes de confirmação de água: conferir contexto, método e coleta."),
    ("noise_localized_final_drive", "noise_localized_external",
     "Localizações de ruído discordantes: não condenar rolamento nem descartar origem externa."),
    ("lubricant_change_documented", "lubricant_history_unchanged",
     "Históricos de produto conflitantes: reconciliar documentos e datas da simulação."),
)
REQUIRED_FIELDS = {"schema", "caseId", "purpose", "machine", "complaint", "signals",
                   "availableContext"}
MACHINE_FIELDS = {"manufacturer", "model", "serialOrArrangement", "finalDrivePosition"}
CONTEXT_FIELDS = {"oilHistoryAvailable", "sampleMetadataAvailable", "trendBaselineAvailable",
                  "oemReferenceAvailable"}
SIGNAL_FIELDS = {"code", "result", "evidenceNature", "sourceRef"}
INDEX_FIELDS = {"schema", "contentVersion", "contractVersion", "inputSha256", "producerCommit",
                "reviewStatus", "approvedForOperationalUse", "records", "sources"}


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_case(case: object) -> dict:
    require(isinstance(case, dict) and set(case) == REQUIRED_FIELDS,
            "caso: contrato de campos inválido")
    require(case["schema"] == PILOT_SCHEMA and case["purpose"] == "training_simulation",
            "somente casos de simulação didática são aceitos")
    require(_is_text(case["caseId"]) and case["caseId"].startswith("SIM-"),
            "caseId deve iniciar com SIM-")
    require(_is_text(case["complaint"]) and len(case["complaint"]) <= 2000,
            "relato fictício ausente ou excessivamente longo")
    machine = case["machine"]
    require(isinstance(machine, dict) and set(machine) == MACHINE_FIELDS,
            "contexto de máquina inválido")
    require(machine["manufacturer"] == "Caterpillar" and machine["model"] == "777E",
            "piloto cobre apenas CAT 777E como contexto educacional")
    for key in ("serialOrArrangement", "finalDrivePosition"):
        val = machine[key]
        require(val is None or (_is_text(val) and len(val) <= 100),
                f"machine.{key} inválido")
    context = case["availableContext"]
    require(isinstance(context, dict) and set(context) == CONTEXT_FIELDS,
            "availableContext inválido")
    require(all(type(x) is bool for x in context.values()),
            "availableContext usa apenas valores booleanos")
    require(isinstance(case["signals"], list) and len(case["signals"]) <= len(SIGNAL_LABELS),
            "signals deve ser uma lista limitada")
    seen: set[str] = set()
    for item in case["signals"]:
        require(isinstance(item, dict) and set(item) == SIGNAL_FIELDS,
                "signal com campos inesperados")
        code = item["code"]
        require(code in SIGNAL_LABELS, f"signal desconhecido: {code}")
        require(code not in seen, f"signal duplicado: {code}")
        seen.add(code)
        require(item["result"] in ("present", "absent", "inconclusive"),
                f"signal {code}: resultado inválido")
        require(item["evidenceNature"] == "simulation",
                f"signal {code}: somente evidência simulada; dados reais não autorizados")
        require(_is_text(item["sourceRef"]) and item["sourceRef"].startswith("SIM-")
                and len(item["sourceRef"]) <= 100,
                f"signal {code}: sourceRef deve identificar simulação")
    return case


def validate_index(index: object, lock: dict) -> tuple[dict, dict]:
    require(isinstance(index, dict) and set(index) == INDEX_FIELDS,
            "índice FMEA inválido")
    require(index["schema"] == "maintenance-superinteligence.fmea-concept-index.v1",
            "índice FMEA desconhecido")
    require(index["contentVersion"] == lock["contentVersion"]
            and index["contractVersion"] == lock["contractVersion"]
            and index["inputSha256"] == lock["sha256"]
            and index["producerCommit"] == lock["producerCommit"],
            "índice não corresponde ao conteúdo FMEA pinado")
    require(index["reviewStatus"] == "inferred_not_operational"
            and index["approvedForOperationalUse"] is False,
            "índice tenta aprovar conhecimento não homologado")
    require(isinstance(index["records"], list) and len(index["records"]) == 24,
            "índice FMEA incompleto")
    require(isinstance(index["sources"], list) and len(index["sources"]) == 20,
            "fontes FMEA incompletas")
    records = {r.get("fmeaId"): r for r in index["records"] if isinstance(r, dict)}
    require(len(records) == 24 and set(ALLOWED_CHAIN_IDS).issubset(records),
            "cadeias de comando final ausentes/duplicadas")
    source_map = {s.get("id"): s for s in index["sources"] if isinstance(s, dict)}
    require(len(source_map) == 20, "fontes FMEA duplicadas")
    for rid, record in records.items():
        require(record.get("approvedForOperationalUse") is False
                and record.get("confirmedRootCause") is False
                and type(record.get("empiricalOccurrences")) is int
                and record["empiricalOccurrences"] == 0
                and record.get("reviewStatus") == "inferido_com_literatura_geral"
                and record.get("evidenceNature") == "hypothesis_not_event",
                f"{rid}: promoção causal indevida")
        require(isinstance(record.get("plannedInvestigations"), list)
                and all(t.get("status") == "not_performed"
                        for t in record["plannedInvestigations"]),
                f"{rid}: investigação marcada como executada")
        require(isinstance(record.get("applicability"), dict)
                and set(record["applicability"]) == {
                    "modelId", "locationId", "serialOrArrangement"}
                and all(v is None for v in record["applicability"].values()),
                f"{rid}: efetividade específica não comprovada")
        require(set(record.get("sourceIds", [])).issubset(source_map),
                f"{rid}: referência bibliográfica órfã")
    return records, source_map


def investigate(case: dict, index: dict, lock: dict | None = None) -> dict:
    lock = lock or load_lock()
    case = validate_case(case)
    records, source_map = validate_index(index, lock)
    positives = {s["code"] for s in case["signals"] if s["result"] == "present"}
    hypotheses: dict[str, dict] = {}
    for rid in ALLOWED_CHAIN_IDS:
        r = records[rid]
        hypotheses[rid] = {
            "id": rid, "title": r["title"], "nature": "inferred_fmea_hypothesis",
            "supportingSignals": [], "weakeningSignals": [],
            "sourceIds": r["sourceIds"],
            "reviewStatus": r["reviewStatus"], "disposition": "open_not_confirmed",
            "causalLimit": r["causalLevels"]["rootCauseNotEstablishedBecause"],
        }
    for hid, title in EXTRA_HYPOTHESES.items():
        hypotheses[hid] = {
            "id": hid, "title": title, "nature": "pilot_alternative_not_oem",
            "supportingSignals": [], "weakeningSignals": [],
            "sourceIds": [], "reviewStatus": "didactic_proposal",
            "disposition": "open_not_confirmed",
            "causalLimit": "Hipótese concorrente pedagógica; exige investigação específica.",
        }

    for signal in positives:
        supporting, weakening = SIGNAL_RULES[signal]
        for hid in supporting:
            hypotheses[hid]["supportingSignals"].append(signal)
        for hid in weakening:
            hypotheses[hid]["weakeningSignals"].append(signal)
    for h in hypotheses.values():
        h["supportingSignals"].sort()
        h["weakeningSignals"].sort()
        if h["supportingSignals"] and h["weakeningSignals"]:
            h["disposition"] = "mixed_evidence_open_not_confirmed"
        elif h["supportingSignals"]:
            h["disposition"] = "indications_only_not_confirmed"
        elif h["weakeningSignals"]:
            h["disposition"] = "weakened_not_excluded"

    conflicts = [
        {"codes": [a, b], "reason": message}
        for a, b, message in DIVERGENT_PAIRS if a in positives and b in positives
    ]
    missing = []
    machine = case["machine"]
    context = case["availableContext"]
    if not machine["serialOrArrangement"]:
        missing.append("Identificar série/arranjo da máquina; contexto simulado não comprova aplicabilidade OEM.")
    if not machine["finalDrivePosition"]:
        missing.append("Identificar posição/lado do comando final antes de ligar sintomas ao conjunto.")
    if not context["oilHistoryAvailable"]:
        missing.append("Reconciliar produto, formulação, trocas e horas do óleo no exercício.")
    if not context["sampleMetadataAvailable"]:
        missing.append("Disponibilizar ponto, rastreabilidade e condições de coleta da amostra simulada.")
    if not context["trendBaselineAvailable"]:
        missing.append("Obter série temporal comparável e baseline de laboratório do caso didático.")
    if not context["oemReferenceAvailable"]:
        missing.append("Obter publicação OEM vigente e efetiva para o arranjo antes de testar limites.")
    if "additive_profile_changed" in positives and "lubricant_change_documented" not in positives:
        missing.append("Diferença de aditivos isolada: confirmar se houve alteração de produto/baseline.")
    if "water_retest_confirmed" not in positives and "water_retest_not_reproduced" not in positives:
        missing.append("Se água for suspeita, obter recoleta controlada e método de ensaio adequado.")

    alerts = []
    if "reported_loss_of_function" in positives:
        alerts.append("Perda funcional relatada: solicitar avaliação imediata por responsável técnico; sem liberação automática.")
    if "magnetic_debris_increasing" in positives:
        alerts.append("Depósito magnético crescente simulado: avaliar integridade e necessidade de restrição com especialista.")
    if conflicts:
        alerts.append("Evidência divergente: reconciliar origem, contexto e métodos antes de decidir.")
    if "oil_level_below_reference" in positives:
        alerts.append("Nível baixo informado sem referência OEM: não atribuir limite ou procedimento automaticamente.")
    for h in hypotheses.values():
        if h["disposition"] == "mixed_evidence_open_not_confirmed":
            alerts.append(f"Indícios opostos para {h['id']}; manter hipótese em aberto.")

    tests = []
    seen_tests = set()
    for rid in ALLOWED_CHAIN_IDS:
        for t in records[rid]["plannedInvestigations"]:
            key = (rid, t["id"])
            if key not in seen_tests:
                tests.append({
                    "referenceFmeaId": rid, "methodId": t["methodId"],
                    "purposeFromSource": t["purpose"], "status": "not_performed",
                    "requiredGate": "Procedimento OEM efetivo, controle de riscos e revisão humana.",
                })
                seen_tests.add(key)

    sources = [
        {"id": sid, "title": source_map[sid]["title"],
         "url": source_map[sid]["url"], "limitation": source_map[sid]["limitation"]}
        for sid in sorted({sid for rid in ALLOWED_CHAIN_IDS for sid in records[rid]["sourceIds"]})
    ]
    return {
        "schema": OUTPUT_SCHEMA,
        "caseId": case["caseId"],
        "purpose": "didactic_hypothesis_discussion_only",
        "provenance": {
            "fmeaContentVersion": lock["contentVersion"],
            "fmeaInputSha256": lock["sha256"],
            "fmeaRecordIds": list(ALLOWED_CHAIN_IDS),
            "simulatedEvidenceOnly": True,
            "operationalApplicability": "not_verified",
        },
        "question": case["complaint"],
        "machineContext": {
            "manufacturer": "Caterpillar", "model": "777E",
            "seriesProvided": machine["serialOrArrangement"] is not None,
            "drivePositionProvided": machine["finalDrivePosition"] is not None,
            "oemApplicabilityVerified": False,
        },
        "observations": [
            {"code": s["code"], "label": SIGNAL_LABELS[s["code"]],
             "result": s["result"], "evidenceNature": "simulation",
             "sourceRef": s["sourceRef"]}
            for s in case["signals"]
        ],
        "hypotheses": [hypotheses[rid] for rid in (*ALLOWED_CHAIN_IDS, *EXTRA_HYPOTHESES)],
        "conflicts": conflicts,
        "knowledgeGaps": list(dict.fromkeys(missing)),
        "plannedInvestigations": tests,
        "bibliography": sources,
        "riskAlerts": list(dict.fromkeys(alerts)),
        "decision": "escalate_to_specialist" if alerts else "needs_evidence",
        "decisionReason": (
            "Discussão de risco/indícios divergentes requer avaliação de especialista."
            if alerts else "Faltam evidência discriminante e efetividade OEM; hipóteses permanecem abertas."
        ),
        "humanReviewRequired": True,
        "confirmedRootCause": None,
        "condemnedComponent": None,
        "mayReleaseEquipment": False,
        "mayCreateWorkOrder": False,
        "limitations": [
            "Não utilizar para intervenção, limiares, liberação, condenação de peça ou SAP.",
            "Os quatro caminhos FMEA são hipóteses genéricas, não homologação para CAT 777E.",
            "Regras de indícios são rubricas didáticas, não probabilidades nem diagnóstico.",
            "Dados informados são exclusivamente simulados; não representam medições de frota.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Saída JSON opcional; imprime no stdout também")
    args = parser.parse_args(argv)
    try:
        index = json.loads(args.index.read_text(encoding="utf-8"))
        case = json.loads(args.case.read_text(encoding="utf-8"))
        result = investigate(case, index)
        data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(data, encoding="utf-8")
        print(data)
        return 0
    except (ImportRejected, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"result": "rejected_fail_closed", "reason": str(error),
                          "mayReleaseEquipment": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
