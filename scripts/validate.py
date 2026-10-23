#!/usr/bin/env python3
"""Baseline offline checks for public metadata. Not full JSON Schema validation."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_DOCS = (
    "README.md", "docs/ARQUITETURA.md", "docs/COMPETENCIAS.md",
    "docs/DOMINIOS.md", "docs/INTEGRACAO_FMEA.md",
    "docs/METODO_DE_PESQUISA.md", "docs/GOVERNANCA.md",
    "docs/ROADMAP.md", "docs/CASO_PILOTO.md", "docs/FONTES.md",
)
ALLOWED_STATUSES = {
    "proposed", "reviewed", "didactic_validated",
    "oem_applicability_verified", "operationally_approved"
}


def fail(message: str) -> None:
    raise SystemExit("VALIDATION FAILED: " + message)


def load(path: str):
    file = ROOT / path
    if not file.is_file():
        fail("missing " + path)
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(path + ": " + str(error))


def unique(records, field, path):
    values = [item.get(field) for item in records]
    if any(not isinstance(value, str) or not value for value in values):
        fail(path + ": missing " + field)
    if len(values) != len(set(values)):
        fail(path + ": duplicated " + field)
    return set(values)


def main():
    for path in REQUIRED_DOCS:
        if not (ROOT / path).is_file():
            fail("missing documentation " + path)
    for path in ("contracts/claim.schema.json", "contracts/source.schema.json"):
        schema = load(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail("invalid declared schema dialect: " + path)

    sources = load("data/sources.json")
    claims = load("data/claims.json")
    gaps = load("research/gaps.v1.json")
    if not all(isinstance(collection, list) and collection for collection in (sources, claims, gaps)):
        fail("all metadata catalogues must be non-empty lists")
    source_ids = unique(sources, "sourceId", "data/sources.json")
    unique(claims, "claimId", "data/claims.json")
    unique(gaps, "gapId", "research/gaps.v1.json")

    for source in sources:
        if not str(source.get("url", "")).startswith("https://"):
            fail(source["sourceId"] + ": missing HTTPS source URL")
        if source.get("licenseStatus") not in (
            "metadata_only", "open_licensed", "authorised_restricted", "rights_unverified"
        ):
            fail(source["sourceId"] + ": unknown license status")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", source.get("accessedAt", "")):
            fail(source["sourceId"] + ": invalid accessedAt")

    for claim in claims:
        cid = claim["claimId"]
        if claim.get("reviewStatus") not in ALLOWED_STATUSES:
            fail(cid + ": invalid review status")
        if not isinstance(claim.get("statement"), str) or len(claim["statement"]) < 15:
            fail(cid + ": no meaningful statement")
        if not claim.get("sourceIds") or not set(claim["sourceIds"]).issubset(source_ids):
            fail(cid + ": orphan or absent source")
        if not claim.get("limitations"):
            fail(cid + ": missing limitations")
        applicability = claim.get("applicability") or {}
        for field in ("manufacturer", "model", "serialRange", "softwareVersion"):
            if field not in applicability:
                fail(cid + ": missing applicability." + field)
        if claim.get("reviewStatus") != "proposed" and not claim.get("reviewerId"):
            fail(cid + ": advanced review status without identified reviewer")
        if claim.get("reviewStatus") in ("oem_applicability_verified", "operationally_approved"):
            if not all(applicability.get(f) for f in ("manufacturer", "model")):
                fail(cid + ": OEM-specific claim missing manufacturer/model")
        if claim.get("kind") == "specific_procedure":
            if not all(applicability.get(f) for f in ("manufacturer", "model", "serialRange")):
                fail(cid + ": procedure needs exact OEM applicability")
            if claim.get("reviewStatus") in ("proposed", "reviewed"):
                fail(cid + ": no unverified specific procedure in released catalogue")
    print(f"OK: {len(sources)} sources, {len(claims)} claims, {len(gaps)} research gaps")
    print("Status: metadata/referential checks passed (not an OEM validation).")


if __name__ == "__main__":
    main()
