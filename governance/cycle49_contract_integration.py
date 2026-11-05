"""Cycle 49 — executable cross-cycle JSON Schema integration review.

Uses only synthetic, author-created fixtures from existing unit tests.
It exercises each C44-C48 contract with an actual generated instance, then
tries fail-closed structural and authority mutations. It does not validate
physical hypotheses, real human experts, OEM effectivity, or any operation.

jsonschema is imported ONLY when this audit is explicitly executed. Default
unittest discovery therefore does not require a new runtime dependency.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from pilot.change_review_packets import digest, require
from benchmarks import cycle44_discrimination as c44
from benchmarks import cycle45_blinded_pairwise as c45
from benchmarks import cycle46_adjudication as c46
from benchmarks import cycle47_evidence_leakage as c47
from governance import cycle48_readiness as c48
from tests.test_cycle45_blinded_pairwise import private_fixture, fabricated_submission

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "maintenance-superinteligence.cycle49"

CONTRACTS = (
    "cycle44-trials", "cycle44-report",
    "cycle45-candidate-source", "cycle45-reviewer-packet",
    "cycle45-private-arm-lock", "cycle45-review-submission",
    "cycle45-review-receipt", "cycle45-private-review-report",
    "cycle46-neutrality-policy", "cycle46-handoff",
    "cycle46-adjudication-draft", "cycle46-draft-receipt",
    "cycle47-adversarial-policy", "cycle47-readiness-report",
    "cycle48-study-readiness", "cycle48-readiness-report",
)
NO_GO_TERMINAL_FIELDS = ("decision", "status")
PROHIBITIONS = (
    "diagnosticAccuracyEstablished", "mayExecuteTest",
    "mayExecuteTests", "mayCreateWorkOrder", "mayWriteSAP",
    "mayModifyECM", "mayModifyEcm", "mayReleaseEquipment",
    "independentMechanicalReviewCompleted", "studyMayStart",
)
_REPORT_DENIALS = (
    "mayExecuteTests", "mayCreateWorkOrder", "mayWriteSAP", "mayModifyECM",
    "mayReleaseEquipment", "independentMechanicalReviewVerified",
    "humanReviewPerformed", "realFieldEvidenceObtained",
)


def _contract_path(name):
    require(name in CONTRACTS, "non-allowlisted schema requested")
    path = (ROOT / "contracts" / (name + ".schema.json")).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(),
            "contract is absent from checkout")
    return path


def build_instances():
    """In-memory objects only. Never save generated synthetic 'private' records."""
    source, candidates, metadata, policy32 = private_fixture()
    key = b"synthetic-C49-only-not-a-real-hmac-custodian-key-000000"
    packet, lock, quality = c45.prepare(
        source, candidates, metadata, policy32, key,
        assignment=["A", "B", "A", "B"],
    )
    a = fabricated_submission(
        packet, "REV-SYNTHA", flags={3: ["unsafe_question"]}
    )
    b = fabricated_submission(
        packet, "REV-SYNTHB", choices=("A", "A", "B", "B")
    )
    submissions = (a, b)
    ra, rb = c45.freeze_receipt(packet, a), c45.freeze_receipt(packet, b)
    receipts = (ra, rb)
    score45 = c45.score(
        source, candidates, metadata, policy32,
        packet, lock, quality, key, submissions, receipts,
    )
    policy46 = c46.load(c46.POLICY)
    handoff46 = c46.prepare_handoff(
        source, candidates, metadata, policy32, packet, lock, quality,
        key, submissions, receipts, policy46,
    )
    pending = [case["caseId"] for case in handoff46["caseHandoffs"]
               if case["requiresIndependentAdjudication"]]
    draft46 = {
        "schema": "maintenance-superinteligence.cycle46-adjudication-draft.v1",
        "version": "1.0.0",
        "handoffDigest": digest(handoff46),
        "adjudicatorAlias": "REV-SYNTHC",
        "independentIdentityVerified": False,
        "externalEngineeringOpinionReceived": False,
        "entries": [
            {
                "caseId": case_id,
                "proposedNextAction": "request_independent_disagreement_review",
                "rationale": (
                    "Synthetic draft only: request qualified independent "
                    "review before interpreting any proposed question."
                ),
                "signedByQualifiedEngineer": False,
                "contradictionResolved": False,
            }
            for case_id in pending
        ],
        "technicalDecisionApproved": False,
        "mayReleaseEquipment": False,
    }
    receipt46 = c46.freeze_draft(draft46, handoff46, submissions)
    policy47 = c47.load(c47.POLICY)
    report47 = c47.evaluate(
        source, candidates, metadata, policy32, packet, lock, quality,
        key, submissions, receipts, handoff46, policy46, policy47,
    )
    trials44 = c44.load(c44.ROOT / "benchmarks/cycle44-symbolic-trials.v1.json")
    report44 = c44.evaluate(trials44)
    manifest48 = c48.load_manifest()
    report48 = c48.build_report(manifest48)
    return {
        "cycle44-trials": trials44,
        "cycle44-report": report44,
        "cycle45-candidate-source": candidates,
        "cycle45-reviewer-packet": packet,
        "cycle45-private-arm-lock": lock,
        "cycle45-review-submission": a,
        "cycle45-review-receipt": ra,
        "cycle45-private-review-report": score45,
        "cycle46-neutrality-policy": policy46,
        "cycle46-handoff": handoff46,
        "cycle46-adjudication-draft": draft46,
        "cycle46-draft-receipt": receipt46,
        "cycle47-adversarial-policy": policy47,
        "cycle47-readiness-report": report47,
        "cycle48-study-readiness": manifest48,
        "cycle48-readiness-report": report48,
    }


def _iter_const_false(schema, value, trail=()):
    """Return all boolean false const fields reachable in the concrete sample."""
    if not isinstance(schema, dict):
        return
    if schema.get("const") is False and value is False:
        yield trail
    if isinstance(value, dict):
        for key, prop_schema in schema.get("properties", {}).items():
            if key in value:
                yield from _iter_const_false(
                    prop_schema, value[key], trail + (key,)
                )
    elif isinstance(value, list):
        child_schema = schema.get("items")
        if isinstance(child_schema, dict):
            for index, item in enumerate(value):
                yield from _iter_const_false(
                    child_schema, item, trail + (index,)
                )


def _mutate_at_path(instance, trail, value):
    changed = copy.deepcopy(instance)
    slot = changed
    for k in trail[:-1]:
        slot = slot[k]
    slot[trail[-1]] = value
    return changed


def _error_count(validator, instance):
    return sum(1 for _ in validator.iter_errors(instance))


def execute_contract_review():
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(
            "Install the pinned jsonschema dependency for schema execution"
        ) from exc

    instances = build_instances()
    require(set(instances) == set(CONTRACTS),
            "contract coverage no longer complete")
    outcomes = []
    for name in CONTRACTS:
        path = _contract_path(name)
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        good = instances[name]
        errors = list(validator.iter_errors(good))
        require(not errors,
                f"{name}: synthesized instance does not match contract: "
                + "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:3]))
        rejected = 0
        # Root-level structural changes must always be rejected.
        require(_error_count(validator, {**good, "_unapprovedField": 1}) > 0,
                name + ": extra root field allowed")
        rejected += 1
        require("version" in good, "schema contract misses version")
        without_version = copy.deepcopy(good)
        del without_version["version"]
        require(_error_count(validator, without_version) > 0,
                name + ": missing version allowed")
        rejected += 1
        # Exercise ALL explicit false-valued authorities across nested arrays.
        false_targets = list(_iter_const_false(schema, good))
        require(false_targets, name + ": no explicit denial gate in schema")
        for trail in false_targets:
            injected = _mutate_at_path(good, trail, True)
            require(_error_count(validator, injected) > 0,
                    f"{name}: denied flag {trail} could be promoted to true")
            rejected += 1
        # NO GO decision/status strings must not permit arbitrary promotion.
        for field in NO_GO_TERMINAL_FIELDS:
            if field in good:
                if schema["properties"][field].get("const") is not None:
                    mutated = copy.deepcopy(good)
                    mutated[field] = "accepted_independent_field_validation"
                    require(_error_count(validator, mutated) > 0,
                            name + ": decision/status promoted")
                    rejected += 1
        outcomes.append({
            "contract": name,
            "acceptedSyntheticSample": True,
            "forgedMutationsRejected": rejected,
            "explicitFalseAuthorityFieldsExercised": len(false_targets),
            "schemaDraft202012Checked": True,
            "realCasesUsed": False,
            "humanReviewPerformed": False,
            "operationallyApproved": False,
        })
    return {
        "schema": PREFIX + "-contract-audit.v1",
        "version": "1.0.0",
        "mode": "in_memory_synthetic_contract_execution_only",
        "cycleSpan": "44-48",
        "contractCount": len(outcomes),
        "syntheticSamplesAccepted": len(outcomes),
        "mutationsRejected": sum(x["forgedMutationsRejected"] for x in outcomes),
        "checks": outcomes,
        "schemaValidationCompleted": True,
        "mechanicalDiagnosticAccuracyMeasured": False,
        "independentExpertReviewPerformed": False,
        "studyMayRecruitParticipants": False,
        "studyMayStart": False,
        "mayExecuteTests": False,
        "mayCreateWorkOrder": False,
        "mayWriteSAP": False,
        "mayModifyECM": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_contract_alignment_is_not_external_mechanical_validation",
    }


def format_markdown(report):
    lines = [
        "# Ciclo 49 — Auditoria executável de contratos (NO GO)", "",
        "Amostras são sintéticas, geradas em memória sem saída com casos privados.", "",
        "| Contrato | Amostra sintética | Mutações rejeitadas |",
        "| --- | --- | ---: |",
    ]
    for item in report["checks"]:
        lines.append(
            f"| {item['contract']} | aceita | "
            f"{item['forgedMutationsRejected']} |"
        )
    lines.extend([
        "",
        f"Contratos executados: **{report['contractCount']}**.",
        f"Mutações estruturais/de autoridade rejeitadas: "
        f"**{report['mutationsRejected']}**.",
        "",
        "**NO GO:** testes de contrato não demonstram capacidade de "
        "diagnóstico, revisão por engenheiros, qualidade de fontes ou "
        "autorização operacional.",
        "",
    ])
    return "\n".join(lines)


def cli(argv=None):
    ap = argparse.ArgumentParser(description="C49 synthetic contract matrix")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--markdown", type=Path)
    args = ap.parse_args(argv)
    report = execute_contract_review()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n",
                           encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(format_markdown(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    cli()
