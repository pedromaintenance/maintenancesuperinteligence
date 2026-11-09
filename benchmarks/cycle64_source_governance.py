"""Cycle 64: synthetic source revision, revocation and contradiction gate.

Source statuses and lineage are fictitious author-declared metadata, NOT proof
of document authenticity, OEM applicability, or operational permissions.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from benchmarks.cycle63_effectivity import validate as validate_c63

SCHEMA = "maintenance-superinteligence.synthetic-source-governance.v1"
IDENT = re.compile(r"^SIM-[A-Z0-9]{3,20}$")
STATES = {"active", "superseded", "revoked"}
DENIED = ("sourceAuthenticityVerified", "revisionApproved",
          "oemEffectivityVerified", "technicalConflictResolved",
          "expertReviewCompleted", "mayExecuteTest", "mayWriteSap",
          "mayModifyEcm", "mayReleaseEquipment")


def need(test, message):
    if not test:
        raise ValueError(message)


def exact(value, fields, name):
    need(type(value) is dict and set(value) == set(fields),
         name + ": unknown or missing fields")


def ident(value):
    return type(value) is str and IDENT.fullmatch(value) is not None


def validate(payload):
    exact(payload, ("schema", "effectivityCase", "sources", "claims"), "case")
    need(payload["schema"] == SCHEMA, "unsupported schema")
    upstream = validate_c63(payload["effectivityCase"])
    references = {r["referenceId"] for r in upstream["results"]}
    sources = payload["sources"]
    need(type(sources) is list and 1 <= len(sources) <= 30,
         "one to thirty source records required")
    by_id = {}
    for s in sources:
        exact(s, ("sourceId", "referenceId", "lineageId", "revisionOrdinal",
                  "status", "supersedes", "claimToken", "sourceNature",
                  "provenanceVerified"), "source")
        need(ident(s["sourceId"]) and s["sourceId"] not in by_id,
             "duplicate or malformed source ID")
        need(s["referenceId"] in references, "unknown reference ID")
        need(ident(s["lineageId"]) and ident(s["claimToken"]),
             "synthetic lineage and content tokens required")
        need(type(s["revisionOrdinal"]) is int and 1 <= s["revisionOrdinal"] <= 9999,
             "revision ordinal must be a positive integer")
        need(s["status"] in STATES, "unknown source status")
        need(s["sourceNature"] == "invented_document_only"
             and s["provenanceVerified"] is False,
             "real document provenance cannot be asserted")
        need(s["supersedes"] is None or ident(s["supersedes"]),
             "invalid superseded source link")
        by_id[s["sourceId"]] = s
    # Supersession is explicit, within the same lineage and reference, and
    # strictly increasing in ordinal. This rejects cycles by construction.
    incoming = set()
    for s in sources:
        parent_id = s["supersedes"]
        if parent_id is None:
            continue
        need(parent_id in by_id and parent_id != s["sourceId"],
             "supersedes points to missing or identical source")
        parent = by_id[parent_id]
        need(parent["referenceId"] == s["referenceId"]
             and parent["lineageId"] == s["lineageId"],
             "cross-reference or cross-lineage supersession")
        need(parent["revisionOrdinal"] < s["revisionOrdinal"],
             "revision order cannot regress or cycle")
        need(parent["status"] == "superseded" and s["status"] == "active",
             "supersession requires old superseded and new active")
        need(parent_id not in incoming, "ambiguous supersession fork")
        incoming.add(parent_id)
    for s in sources:
        if s["status"] == "superseded":
            need(s["sourceId"] in incoming, "superseded source lacks successor")
    # Multiple versions of same lineage cannot be simultaneously active.
    active_by_lineage = set()
    for s in sources:
        if s["status"] != "active":
            continue
        key = (s["referenceId"], s["lineageId"])
        need(key not in active_by_lineage,
             "multiple active revisions in same lineage")
        active_by_lineage.add(key)
    exact(payload["claims"], DENIED, "claims")
    need(all(payload["claims"][k] is False for k in DENIED),
         "document metadata cannot grant authority")
    results = []
    for ref in sorted(references):
        subset = [s for s in sources if s["referenceId"] == ref]
        active = [s for s in subset if s["status"] == "active"]
        tokens = {s["claimToken"] for s in active}
        unresolved = len(tokens) > 1
        revoked = sum(s["status"] == "revoked" for s in subset)
        results.append({
            "referenceId": ref, "activeSources": len(active),
            "revokedSources": revoked,
            "unresolvedActiveClaimConflict": unresolved,
            "reasonCodes": (["no_active_source"] if not active else [])
                           + (["active_sources_disagree"] if unresolved else [])
                           + (["revoked_source_present"] if revoked else []),
            "sourceVerified": False, "referenceApproved": False,
        })
    need(all(any(s["referenceId"] == ref for s in sources) for ref in references),
         "every reference requires at least one source")
    return {
        "schema": "maintenance-superinteligence.synthetic-source-governance-result.v1",
        "caseId": upstream["caseId"],
        "references": results,
        "unresolvedConflicts": sum(r["unresolvedActiveClaimConflict"] for r in results),
        "sourceAuthenticityVerified": False,
        "revisionApproved": False,
        "oemEffectivityVerified": False,
        "expertReviewCompleted": False,
        "operationalAuthorityGranted": False,
        "decision": "NO GO"
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output")
    args = p.parse_args()
    result = validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as out:
            out.write(content)
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
