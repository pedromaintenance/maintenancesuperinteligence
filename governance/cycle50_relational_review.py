"""Cycle 50: integration review of JSON Schema vs relational runtime guards.

This is a *synthetic-only* comparison. It exposes gaps that JSON Schema
Draft 2020-12 cannot express as simple local const/type checks, then verifies
that the existing Python validators still reject those altered objects.

It also recomputes the Cycle 49 coverage report to reject forged counts.
No live GitHub access, no private inputs, no human/engineering attestation.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from pilot.change_review_packets import digest, require
from benchmarks import cycle44_discrimination as c44
from benchmarks import cycle45_blinded_pairwise as c45
from governance import cycle48_readiness as c48
from governance import cycle49_contract_integration as c49

PREFIX = "maintenance-superinteligence.cycle50"
CHECK_IDS = (
    "c44_hypothesis_key_binding",
    "c44_registered_baseline_binding",
    "c44_contradiction_status_binding",
    "c45_case_count_binding",
    "c45_distinct_question_binding",
    "c45_unique_case_id_binding",
    "c48_frozen_sha_binding",
    "c48_parent_branch_binding",
)
TAMPER_IDS = (
    "inflated_mutation_count",
    "inflated_per_contract_mutation_count",
    "forged_contract_identity",
)
FALSE_FLAGS = (
    "independentCodeReviewVerified", "realReviewerAuthenticated",
    "oemEffectivityVerified", "mechanicalDiagnosticAccuracyEstablished",
    "mayStartHumanStudy", "mayExecuteTest", "mayCreateWorkOrder",
    "mayWriteSAP", "mayModifyECM", "mayReleaseEquipment",
)


def _set_new_baseline(value):
    value["trials"][0]["baselineQuestionId"] = (
        value["trials"][0]["questions"][1]["questionId"]
    )


def _set_bad_hypothesis(value):
    row = value["trials"][0]
    outcomes = row["questions"][0]["symbolicOutcomesByHypothesis"]
    first = row["hypothesisIds"][0]
    outcomes["synthetic_extra_alias"] = outcomes.pop(first)


def _set_false_contradiction(value):
    row = next(x for x in value["trials"] if x["scenarioKind"] == "normal")
    row["sourceStatus"] = "contradictory"


def _set_wrong_count(value):
    value["caseCount"] -= 1


def _set_same_question(value):
    value["cases"][0]["questionA"] = value["cases"][0]["questionB"]


def _set_duplicate_case(value):
    value["cases"][1]["caseId"] = value["cases"][0]["caseId"]


def _set_forged_sha(value):
    value["stack"][4]["headSha"] = "a" * 40


def _set_bad_base(value):
    value["stack"][1]["base"] = "main"


# Each row has both a schema and a *distinct* semantic validator.
# The mutation must be schema-accepted but runtime-rejected. This deliberate
# contrast is the finding, not an attempt to characterize all schema defects.
PROBES = (
    (CHECK_IDS[0], "cycle44-trials", _set_bad_hypothesis,
     c44.validate_fixture),
    (CHECK_IDS[1], "cycle44-trials", _set_new_baseline,
     c44.validate_fixture),
    (CHECK_IDS[2], "cycle44-trials", _set_false_contradiction,
     c44.validate_fixture),
    (CHECK_IDS[3], "cycle45-reviewer-packet", _set_wrong_count,
     c45.validate_packet),
    (CHECK_IDS[4], "cycle45-reviewer-packet", _set_same_question,
     c45.validate_packet),
    (CHECK_IDS[5], "cycle45-reviewer-packet", _set_duplicate_case,
     c45.validate_packet),
    (CHECK_IDS[6], "cycle48-study-readiness", _set_forged_sha,
     c48.validate_manifest),
    (CHECK_IDS[7], "cycle48-study-readiness", _set_bad_base,
     c48.validate_manifest),
)


def _schema(name):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(
            "Cycle50 requires pinned jsonschema==4.23.0 for contract execution"
        ) from exc
    contract_path = c49._contract_path(name)
    raw = json.loads(contract_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(raw)
    return Draft202012Validator(raw)


def _schema_errors(validator, value):
    return list(validator.iter_errors(value))


def _semantic_rejects(validator, value):
    """Only declared ValueError rejection counts; unrelated errors fail."""
    try:
        validator(value)
    except ValueError:
        return True
    return False


def relational_review(instances=None):
    if instances is None:
        instances = c49.build_instances()
    require(set(c49.CONTRACTS).issubset(instances),
            "a required Cycle 49 synthetic input was not provided")
    rows = []
    for identifier, name, mutator, semantic_validator in PROBES:
        contract_validator = _schema(name)
        original = instances[name]
        require(not _schema_errors(contract_validator, original),
                "base synthetic instance fails contract: " + name)
        semantic_validator(original)
        mutated = copy.deepcopy(original)
        mutator(mutated)
        require(not _schema_errors(contract_validator, mutated),
                identifier + ": mutation unexpectedly rejected structurally")
        require(_semantic_rejects(semantic_validator, mutated),
                identifier + ": semantic validator no longer rejects corruption")
        rows.append({
            "probeId": identifier,
            "contract": name,
            "syntheticStructuralSchemaAccepted": True,
            "relationalRuntimeValidatorRejected": True,
            "requiresBothValidationLayers": True,
            "usesRealCases": False,
            "humanApprovalClaimed": False,
        })
    return rows


def report_integrity_review():
    """Recompute Cycle49 report; prove schema alone can't bind its counts."""
    base = c49.execute_contract_review()
    require(c49.verify_report(base), "C49 baseline cannot be recalculated")
    schema = _schema("cycle49-contract-audit")
    require(not _schema_errors(schema, base),
            "Cycle49 baseline incompatible with own declared schema")
    cases = []
    for ident in TAMPER_IDS:
        changed = copy.deepcopy(base)
        if ident == "inflated_mutation_count":
            changed["mutationsRejected"] += 1
        elif ident == "inflated_per_contract_mutation_count":
            changed["checks"][0]["forgedMutationsRejected"] += 1
        else:
            changed["checks"][0]["contract"] = (
                "cycle47-readiness-report"
            )
        require(not _schema_errors(schema, changed),
                ident + ": schema now rejects mutation; update the review")
        require(_semantic_rejects(c49.verify_report, changed),
                ident + ": C49 recomputation accepted forged coverage")
        cases.append({
            "probeId": ident,
            "syntheticStructuralSchemaAccepted": True,
            "recomputedReportRejected": True,
            "independentlyAuthenticated": False,
        })
    return base, cases


def evaluate():
    relationships = relational_review()
    c49_report, count_mutations = report_integrity_review()
    require([row["probeId"] for row in relationships] == list(CHECK_IDS),
            "cross-document review probes missing")
    require([row["probeId"] for row in count_mutations] == list(TAMPER_IDS),
            "coverage report tamper probes missing")
    return {
        "schema": PREFIX + "-integration-review.v1",
        "version": "1.0.0",
        "nature": "author_executed_synthetic_relational_validation_review",
        "integratedWithCycle49Digest": digest(c49_report),
        "relationalProbeCount": len(relationships),
        "relationalSchemaAcceptedCount": len(relationships),
        "relationalRuntimeRejectedCount": len(relationships),
        "relationalChecks": relationships,
        "reportTamperProbeCount": len(count_mutations),
        "reportTamperRejectedCount": len(count_mutations),
        "reportTamperChecks": count_mutations,
        "remainingExternalStudyGates": 13,
        **{key: False for key in FALSE_FLAGS},
        "decision": "no_go_relational_integrity_is_not_external_validation",
    }


def verify_report(report):
    require(report == evaluate(),
            "Cycle50 review report changed, stale or externally promoted")
    return True


def markdown(report):
    require(report["decision"] ==
            "no_go_relational_integrity_is_not_external_validation"
            and all(report[k] is False for k in FALSE_FLAGS),
            "report claims unverified authority")
    lines = [
        "# Ciclo 50 — Validação estrutural × relacional (NO GO)",
        "", "Resultado inteiramente sintético; nenhuma revisão humana foi feita.",
        "", "| Prova | Schema | Validador relacional |",
        "| --- | --- | --- |",
    ]
    for row in report["relationalChecks"]:
        lines.append(
            f"| {row['probeId']} | aceita objeto adulterado | "
            "rejeita relação inválida |"
        )
    lines.extend([
        "",
        f"Relações contrastadas: **{report['relationalProbeCount']}**.",
        f"Falsificações do relatório C49 rejeitadas ao recalcular: "
        f"**{report['reportTamperRejectedCount']}**.",
        "",
        "O esquema JSON valida formato; o validador de domínio precisa "
        "verificar vínculos entre campos. Nem um nem outro confirma a verdade "
        "física dos casos ou a identidade dos revisores.",
        "",
        "**NO GO:** 13 requisitos externos permanecem não verificados. "
        "Não executar ensaios, abrir ordens, operar SAP/ECM, iniciar estudo "
        "humano ou liberar equipamentos.",
        "",
    ])
    return "\n".join(lines)


def cli(argv=None):
    ap = argparse.ArgumentParser(
        description="Cycle50 in-memory semantic-vs-schema integration audit"
    )
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--markdown", type=Path)
    args = ap.parse_args(argv)
    result = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)
                           + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(result), encoding="utf-8")
    return result


if __name__ == "__main__":
    cli()
