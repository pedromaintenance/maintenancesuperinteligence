#!/usr/bin/env python3
"""Importador de leitura do snapshot PUBLICO congelado do FMEA Mining.

Integra SOMENTE hipoteses didaticas; nao aceita eventos ou homologacao operacional.
Sem dependencias externas: Python 3.11+ (biblioteca padrao).
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCK = ROOT / "connectors/fmea-source-lock.v1.json"
MAX_SNAPSHOT_BYTES = 2_000_000

TOP_FIELDS = {
    "schema", "version", "contentStatus", "approvedForOperationalUse",
    "recordNature", "sourceScope", "warnings", "counts", "records", "sources"
}
CAUSAL_FIELDS = {
    "observedPhenomenon", "immediatePhysicalMechanismCandidate",
    "contributingConditionCandidates", "rootCauseCandidates",
    "rootCauseNotEstablishedBecause"
}
ALT_FIELDS = {"id", "description", "discriminator"}
TEST_FIELDS = {"id", "methodId", "purpose", "status"}
EFFECT_FIELDS = {"description", "status"}
APPLICABILITY_FIELDS = {"modelId", "locationId", "serialOrArrangement"}


class ImportRejected(ValueError):
    """A fonte ou a semantica nao atende ao contrato de seguranca."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ImportRejected(reason)


def exact_fields(obj: object, expected: set[str], context: str) -> dict:
    require(isinstance(obj, dict), f"{context}: deve ser objeto")
    require(set(obj) == expected,
            f"{context}: campos divergentes; ausentes={sorted(expected - set(obj))}, "
            f"extras={sorted(set(obj) - expected)}")
    return obj


def meaningful(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_text(value: object, context: str, *, minimum: int = 1) -> list:
    require(isinstance(value, list) and len(value) >= minimum, f"{context}: lista insuficiente")
    require(all(meaningful(x) for x in value), f"{context}: texto invalido")
    return value


def unique_ids(objects: list[dict], context: str) -> set[str]:
    ids = [x.get("id") for x in objects]
    require(all(meaningful(x) for x in ids), f"{context}: ID ausente")
    require(len(ids) == len(set(ids)), f"{context}: ID duplicado")
    return set(ids)


def load_lock(path: Path = DEFAULT_LOCK) -> dict:
    lock = json.loads(path.read_text(encoding="utf-8"))
    require(lock.get("schema") == "maintenance-superinteligence.fmea-source-lock.v1",
            "lock schema desconhecido")
    require(lock.get("producerRepository") == "pedromaintenance/fmea-database-mining",
            "produtor nao permitido")
    require(re.fullmatch(r"[0-9a-f]{40}", lock.get("producerCommit", "")) is not None,
            "commit do produtor deve ser SHA completo")
    require(lock.get("snapshotPath")
            == "data/governance/snapshots/public-knowledge.content-1.0.0.json",
            "caminho de snapshot nao permitido")
    require(lock.get("contractVersion") == "1.0.0" and lock.get("contentVersion") == "1.0.0",
            "versao de contrato/conteudo nao suportada")
    require(re.fullmatch(r"[0-9a-f]{64}", lock.get("sha256", "")) is not None,
            "sha256 ausente")
    require(lock.get("recordCount") == 24 and lock.get("sourceCount") == 20,
            "contagens do release nao suportadas")
    require(len(lock.get("recordFields", [])) == 18
            and len(set(lock["recordFields"])) == 18, "allowlist de cadeias invalida")
    require(len(lock.get("sourceFields", [])) == 6
            and len(set(lock["sourceFields"])) == 6, "allowlist de fontes invalida")
    require(lock.get("approval") == {
        "approvedForOperationalUse": False,
        "rootCausesConfirmed": 0,
        "empiricalOccurrences": 0
    }, "lock incorretamente autoriza uso operacional")
    return lock


def pinned_url(lock: dict) -> str:
    """Nenhum argumento CLI pode alterar dominio/repositorio/commit/snapshot."""
    return ("https://raw.githubusercontent.com/"
            f"{lock['producerRepository']}/{lock['producerCommit']}/{lock['snapshotPath']}")


def fetch_pinned(lock: dict) -> bytes:
    request = Request(pinned_url(lock), headers={
        "User-Agent": "MaintenanceSuperinteligence-FMEA-PublicImporter/0.2",
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=25) as response:
            final_url = response.geturl()
            require(final_url == pinned_url(lock), "redirect inesperado na fonte")
            raw = response.read(MAX_SNAPSHOT_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as error:
        raise ImportRejected(f"download do snapshot falhou: {error}") from error
    require(len(raw) <= MAX_SNAPSHOT_BYTES, "snapshot excede limite de tamanho")
    return raw


def validate_snapshot(raw: bytes, lock: dict) -> dict:
    require(isinstance(raw, bytes), "entrada deve ser bytes brutos")
    require(len(raw) <= MAX_SNAPSHOT_BYTES, "snapshot excede limite de tamanho")
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == lock["sha256"], "SHA-256 divergente (conteudo adulterado ou versao nao aprovada)")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ImportRejected(f"JSON/UTF-8 invalido: {error}") from error

    exact_fields(data, TOP_FIELDS, "snapshot")
    require(data["schema"] == lock["previewSchema"], "schema de preview divergente")
    require(data["version"] == lock["previewVersion"], "versao de preview divergente")
    require(data["contentStatus"] == "conceptual_inferred_unvalidated",
            "snapshot deixou de ser conceitual e nao validado")
    require(data["approvedForOperationalUse"] is False, "snapshot tenta aprovar uso operacional")
    require(data["recordNature"] == "hypotheses_only", "natureza de registro nao hipotetica")
    require(data["sourceScope"] == "general_principles_not_serial_effective",
            "fonte alega aplicabilidade OEM nao validada")
    list_of_text(data["warnings"], "warnings", minimum=3)

    require(isinstance(data["records"], list)
            and len(data["records"]) == lock["recordCount"], "numero incorreto de cadeias")
    require(isinstance(data["sources"], list)
            and len(data["sources"]) == lock["sourceCount"], "numero incorreto de fontes")
    exact_fields(data["counts"],
                 {"causalChains", "sources", "confirmedRootCauses", "empiricalOccurrences"},
                 "counts")
    require(type(data["counts"]["causalChains"]) is int
            and data["counts"]["causalChains"] == lock["recordCount"], "counts.causalChains divergente")
    require(type(data["counts"]["sources"]) is int
            and data["counts"]["sources"] == lock["sourceCount"], "counts.sources divergente")
    require(type(data["counts"]["confirmedRootCauses"]) is int
            and data["counts"]["confirmedRootCauses"] == 0, "root causes nao podem ser confirmadas")
    require(type(data["counts"]["empiricalOccurrences"]) is int
            and data["counts"]["empiricalOccurrences"] == 0, "ocorrencias reais proibidas")

    for source in data["sources"]:
        exact_fields(source, set(lock["sourceFields"]), "source")
        require(meaningful(source["id"]) and meaningful(source["title"]), "source sem identidade")
        require(isinstance(source["url"], str) and source["url"].startswith("https://"),
                f"source {source['id']}: URL externa invalida")
        for name in ("organization", "role", "limitation"):
            require(source[name] is None or isinstance(source[name], str),
                    f"source {source['id']}: tipo incorreto em {name}")
    source_ids = unique_ids(data["sources"], "sources")
    record_ids: set[str] = set()
    used_sources: set[str] = set()
    for record in data["records"]:
        exact_fields(record, set(lock["recordFields"]), "chain")
        rid = record["id"]
        require(meaningful(rid) and rid.startswith("FC-"), "chain ID invalido")
        require(rid not in record_ids, f"chain ID duplicado: {rid}")
        record_ids.add(rid)
        for field in ("title", "family", "operatingFunction", "functionalFailureId", "failureMode"):
            require(meaningful(record[field]), f"{rid}: {field} vazio")
        list_of_text(record["mechanismIds"], f"{rid}.mechanismIds")
        sid = set(list_of_text(record["sourceIds"], f"{rid}.sourceIds"))
        require(sid.issubset(source_ids), f"{rid}: fonte nao encontrada")
        used_sources.update(sid)
        require(record["reviewStatus"] == "inferido_com_literatura_geral",
                f"{rid}: status passou a aprovado")
        require(record["nature"] == "hypothesis_not_event", f"{rid}: simulacao apresentada como evento")
        require(record["confirmedRootCause"] is False, f"{rid}: causa raiz indevidamente confirmada")
        require(type(record["empiricalOccurrences"]) is int and record["empiricalOccurrences"] == 0,
                f"{rid}: ocorrencia empirica indevida")

        causal = exact_fields(record["causalLevels"], CAUSAL_FIELDS, f"{rid}.causalLevels")
        for field in ("observedPhenomenon", "immediatePhysicalMechanismCandidate",
                      "rootCauseNotEstablishedBecause"):
            require(meaningful(causal[field]), f"{rid}: explicacao causal vazia")
        list_of_text(causal["contributingConditionCandidates"], f"{rid}.contributingConditions")
        list_of_text(causal["rootCauseCandidates"], f"{rid}.rootCauseCandidates")

        for field in ("localEffect", "systemEffect"):
            e = exact_fields(record[field], EFFECT_FIELDS, f"{rid}.{field}")
            require(meaningful(e["description"]) and e["status"] == "possible_unobserved",
                    f"{rid}: efeito nao observado nao pode ser promovido")

        context = exact_fields(record["applicability"], APPLICABILITY_FIELDS, f"{rid}.applicability")
        require(all(value is None for value in context.values()),
                f"{rid}: aplicabilidade por modelo/serie nao comprovada")

        alternatives = record["competingHypotheses"]
        require(isinstance(alternatives, list) and len(alternatives) >= 2,
                f"{rid}: faltam alternativas concorrentes")
        for a in alternatives:
            exact_fields(a, ALT_FIELDS, f"{rid}.alternative")
            require(all(meaningful(v) for v in a.values()), f"{rid}: alternativa incompleta")
        unique_ids(alternatives, f"{rid}.alternatives")

        tests = record["investigations"]
        require(isinstance(tests, list) and len(tests) >= 2,
                f"{rid}: faltam testes complementares")
        for t in tests:
            exact_fields(t, TEST_FIELDS, f"{rid}.investigation")
            require(all(meaningful(v) for v in t.values()), f"{rid}: teste incompleto")
            require(t["status"] == "not_performed", f"{rid}: teste simulado como executado")
        unique_ids(tests, f"{rid}.investigations")

    require(source_ids == used_sources, "fontes orfas/nao utilizadas no snapshot")
    return data


def build_consumer_index(data: dict, lock: dict) -> dict:
    """Nucleo de busca conceitual — sem inferir resultado ou operacionalizar ensaio."""
    records = []
    for record in data["records"]:
        records.append({
            "fmeaId": record["id"],
            "title": record["title"],
            "family": record["family"],
            "operatingFunction": record["operatingFunction"],
            "functionalFailureId": record["functionalFailureId"],
            "failureModeCandidate": record["failureMode"],
            "mechanismIds": record["mechanismIds"],
            "causalLevels": record["causalLevels"],
            "potentialEffects": {
                "local": record["localEffect"],
                "system": record["systemEffect"]
            },
            "competingHypotheses": record["competingHypotheses"],
            "plannedInvestigations": record["investigations"],
            "sourceIds": record["sourceIds"],
            "applicability": record["applicability"],
            "evidenceNature": record["nature"],
            "reviewStatus": record["reviewStatus"],
            "confirmedRootCause": False,
            "empiricalOccurrences": 0,
            "approvedForOperationalUse": False,
        })
    return {
        "schema": "maintenance-superinteligence.fmea-concept-index.v1",
        "contentVersion": lock["contentVersion"],
        "contractVersion": lock["contractVersion"],
        "inputSha256": lock["sha256"],
        "producerCommit": lock["producerCommit"],
        "reviewStatus": "inferred_not_operational",
        "approvedForOperationalUse": False,
        "records": records,
        "sources": data["sources"],
    }


def build_receipt(data: dict, lock: dict) -> dict:
    return {
        "schema": "maintenance-superinteligence.import-receipt.v1",
        "result": "accepted_read_only_hypotheses",
        "source": lock["producerRepository"],
        "sourceCommit": lock["producerCommit"],
        "contentVersion": lock["contentVersion"],
        "contractVersion": lock["contractVersion"],
        "previewVersion": lock["previewVersion"],
        "sha256": lock["sha256"],
        "recordsAccepted": len(data["records"]),
        "sourcesAccepted": len(data["sources"]),
        "familyCoverage": dict(sorted(Counter(r["family"] for r in data["records"]).items())),
        "confirmedRootCauses": 0,
        "empiricalOccurrences": 0,
        "operationalApproval": False,
        "warnings": [
            "Registros sao hipoteses editoriais, nao ocorrencias reais.",
            "Testes nao executados; nenhuma causa raiz homologada.",
            "Modelo, serie, configuracao e baseline OEM ainda nao validados."
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch", action="store_true",
                        help="Obtém apenas snapshot publico do commit imutavel aprovado")
    source.add_argument("--input", type=Path,
                        help="Lê arquivo LOCAL para teste ou modo desconectado (mesmo SHA obrigatório)")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK, help="Contrato pinado local")
    parser.add_argument("--output", type=Path,
                        help="Diretório para indice conceitual e recibo JSON (omitido = validar apenas)")
    args = parser.parse_args(argv)
    try:
        lock = load_lock(args.lock)
        raw = fetch_pinned(lock) if args.fetch else args.input.read_bytes()
        data = validate_snapshot(raw, lock)
        receipt = build_receipt(data, lock)
        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "fmea-public.snapshot.json").write_bytes(raw)
            (args.output / "fmea-public.index.json").write_text(
                json.dumps(build_consumer_index(data, lock), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            (args.output / "import-receipt.json").write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (ImportRejected, OSError, UnicodeError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({
            "schema": "maintenance-superinteligence.import-receipt.v1",
            "result": "rejected_fail_closed",
            "reason": str(error),
            "recordsAccepted": 0,
            "operationalApproval": False,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
