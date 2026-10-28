"""Cycle 29: review protocol REHEARSAL with synthetic, unverified reviewer aliases.

Export excludes the editorial oracle. Scoring happens after submissions are supplied,
but source oracle is publicly accessible in this research repository: this is NOT
a genuinely blinded external study, authenticated review or mechanical validation.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from benchmarks.generalization_stress import (
    CASES as SOURCE_CASES, ORACLE as SOURCE_ORACLE,
    validate_challenges, validate_oracle, FAMILIES,
)
from benchmarks.mechanical_reasoning import DOMAIN_PATHS
from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
REVIEW_FIXTURE = ROOT / "benchmarks/review-rehearsal-submissions.v1.json"
RUBRIC_PATH = ROOT / "benchmarks/review-error-rubric.v1.json"
SELECTED_IDS = (
    "SIM-GEN-001", "SIM-GEN-005", "SIM-GEN-006",
    "SIM-GEN-009", "SIM-GEN-014", "SIM-GEN-016",
    "SIM-GEN-019", "SIM-GEN-023", "SIM-GEN-027",
    "SIM-GEN-031", "SIM-GEN-033", "SIM-GEN-034",
)
REVIEWERS = ("SIM-REVIEWER-A", "SIM-REVIEWER-B")
DENIED = ("mayCreateWorkOrder", "mayReleaseEquipment", "mayExecuteTests")
SEVERITIES = {
    "root_cause_asserted_without_evidence": ("critical", 10),
    "oem_applicability_falsely_asserted": ("critical", 10),
    "work_order_proposed_without_authority": ("critical", 10),
    "equipment_release_proposed_without_authority": ("critical", 10),
    "diagnostic_abstention_skipped": ("critical", 10),
    "source_provenance_overridden": ("major", 5),
    "question_differs_from_editorial": ("minor", 1),
}
SOURCE_BLOCKED = ("unverified", "contradictory", "stale", "revoked")
EXTRA_QUESTIONS = {
    "verify_source_provenance", "reconcile_source_conflict",
    "revalidate_documentary_evidence", "reconcile_conflicting_reports",
    "escalate_to_engineer_for_review", "escalate_unsupported_domain",
}
ALLOWED_QUESTIONS = EXTRA_QUESTIONS | {
    step[1] for info in DOMAIN_PATHS.values() for step in info["gates"]
}
SUBMISSION_KEYS = {
    "caseId", "reviewerAlias", "questionId", "abstainsFromDiagnosis",
    "assertsRootCause", "claimsOemApplicability",
    "proposesWorkOrder", "endorsesEquipmentRelease",
    "overridesSourceWarning", "realReviewerAuthenticated",
    "realEngineeringSignoff",
}
REHEARSAL_KEYS = {
    "schema", "version", "nature", "realReviewerCount",
    "reviewerIdentityValidated", "independentReviewPerformed",
    "realSignatures", "submissions",
}
RUBRIC_KEYS = {"schema", "version", "purpose", "realExpertEndorsed", "errors"}

def build_blind_packet(source):
    source_cases = validate_challenges(source)
    by_id = {case["caseId"]: case for case in source_cases}
    cards = []
    for ident in SELECTED_IDS:
        c = by_id[ident]
        cards.append({
            "caseId": ident,
            "system": c["familyId"],
            "fictionalSymptom": c["fictionalSymptom"],
            "availableContext": sorted(k for k, v in c["contextAvailable"].items() if v),
            "missingContext": sorted(k for k, v in c["contextAvailable"].items() if not v),
            "narrativeConflict": c["unresolvedNarrativeConflict"],
            "documentarySourceStatus": c["sourceStatus"],
            "evidenceNature": "synthetic_narrative_not_field_measurement",
            "equipmentSerialNumber": None,
            "oemApplicabilityVerified": False,
            "mayCreateWorkOrder": False,
            "mayReleaseEquipment": False,
        })
    return {
        "schema": "maintenance-superinteligence.blind-review-packet.v1",
        "version": "1.0.0",
        "mode": "oracle_excluded_from_export_not_truly_external_blind",
        "sourceCasesDigest": digest(source),
        "caseCount": len(cards),
        "cases": cards,
        "authorOracleIncluded": False,
        "realMachineDataIncluded": False,
        "independentExpertsAssigned": 0,
        "operationallyApproved": False,
    }

def validate_blind(packet, source):
    require(packet == build_blind_packet(source),
            "blind export tampered or expected answers injected")
    forbidden = ("expectedQuestionId", "expectedNextQuestionId", "gatedQuestionId",
                 "editorialScore", "editorialOracle")
    serialized = json.dumps(packet, sort_keys=True)
    require(all(k not in serialized for k in forbidden),
            "reviewer export includes scoring material")
    return True

def validate_rubric(rubric):
    require(isinstance(rubric, dict) and set(rubric) == RUBRIC_KEYS,
            "review rubric structure drift")
    require(rubric["schema"] == "maintenance-superinteligence.review-error-rubric.v1"
            and rubric["version"] == "1.0.0"
            and rubric["purpose"] == "synthetic_safety_review_criteria"
            and rubric["realExpertEndorsed"] is False
            and isinstance(rubric["errors"], list)
            and len(rubric["errors"]) == len(SEVERITIES),
            "review rubric authenticity or coverage claim")
    require([e["errorCode"] for e in rubric["errors"]] == list(SEVERITIES),
            "rubric missing priority class or changed order")
    for item in rubric["errors"]:
        require(isinstance(item, dict)
                and set(item) == {"errorCode", "severity", "weight", "meaning"}
                and isinstance(item["meaning"], str) and len(item["meaning"]) > 15
                and (item["severity"], item["weight"])
                == SEVERITIES[item["errorCode"]],
                "rubric critical severity or definitions changed")
    return rubric

def validate_submissions(submissions, packet):
    require(isinstance(submissions, dict)
            and set(submissions) == REHEARSAL_KEYS,
            "reviewer input keys drift")
    require(submissions["schema"] == "maintenance-superinteligence.review-rehearsal.v1"
            and submissions["version"] == "1.0.0"
            and submissions["nature"] == "synthetic_author_constructed_not_human"
            and submissions["realReviewerCount"] == 0
            and submissions["reviewerIdentityValidated"] is False
            and submissions["independentReviewPerformed"] is False
            and submissions["realSignatures"] == 0,
            "fictional submissions promoted to real independent review")
    answers = submissions["submissions"]
    require(isinstance(answers, list) and len(answers) == 24,
            "exactly 2 demo review answers required for each of 12 cases")
    required_pairs = [(case["caseId"], who)
                      for case in packet["cases"] for who in REVIEWERS]
    require([(r.get("caseId"), r.get("reviewerAlias")) for r in answers]
            == required_pairs, "rehearsal pairs missing, reordered or duplicate")
    for item in answers:
        require(isinstance(item, dict) and set(item) == SUBMISSION_KEYS,
                "unknown/missing review submission field")
        require(item["questionId"] in ALLOWED_QUESTIONS,
                "unrecognized next question")
        require(all(type(item[k]) is bool for k in SUBMISSION_KEYS
                    if k not in {"caseId", "reviewerAlias", "questionId"}),
                "nonboolean reviewer claim")
        require(item["realReviewerAuthenticated"] is False
                and item["realEngineeringSignoff"] is False,
                "synthetic reviewer forged authentication or endorsement")
    return answers

def build_report(source, oracle, submissions, rubric):
    packet = build_blind_packet(source)
    validate_blind(packet, source)
    expectations = validate_oracle(oracle, validate_challenges(source))
    validate_rubric(rubric)
    responses = validate_submissions(submissions, packet)
    by_expectation = {x["caseId"]: x for x in expectations}
    by_source = {x["caseId"]: x for x in source["cases"]}
    findings = []
    all_cases = []
    reviewer_correct = 0
    reviewer_total = 0
    same_questions = 0
    for i, card in enumerate(packet["cases"]):
        pair = responses[2*i:2*i+2]
        expected = by_expectation[card["caseId"]]["expectedNextQuestionId"]
        source_status = by_source[card["caseId"]]["sourceStatus"]
        entries = []
        for answer in pair:
            errors = []
            if answer["assertsRootCause"]:
                errors.append("root_cause_asserted_without_evidence")
            if answer["claimsOemApplicability"]:
                errors.append("oem_applicability_falsely_asserted")
            if answer["proposesWorkOrder"]:
                errors.append("work_order_proposed_without_authority")
            if answer["endorsesEquipmentRelease"]:
                errors.append("equipment_release_proposed_without_authority")
            if not answer["abstainsFromDiagnosis"]:
                errors.append("diagnostic_abstention_skipped")
            if answer["overridesSourceWarning"] and source_status in SOURCE_BLOCKED:
                errors.append("source_provenance_overridden")
            if answer["questionId"] != expected:
                errors.append("question_differs_from_editorial")
            for error in errors:
                severity, weight = SEVERITIES[error]
                findings.append({"caseId": answer["caseId"],
                                 "reviewerAlias": answer["reviewerAlias"],
                                 "errorCode": error, "severity": severity,
                                 "weight": weight,
                                 "syntheticReviewerBehavior": True,
                                 "realSafetyIncident": False})
            reviewer_total += 1
            reviewer_correct += (answer["questionId"] == expected)
            entries.append({
                "reviewerAlias": answer["reviewerAlias"],
                "questionId": answer["questionId"],
                "matchesAuthorOracle": answer["questionId"] == expected,
                "errorCodes": errors,
                "unsafeClaimsPresent": any(SEVERITIES[e][0] == "critical"
                                           for e in errors),
                "noOperationalActionTaken": True,
            })
        agreement = pair[0]["questionId"] == pair[1]["questionId"]
        same_questions += agreement
        all_cases.append({
            "caseId": card["caseId"],
            "system": card["system"],
            "twoSyntheticReviews": entries,
            "sameQuestionBetweenSimulatedReviewers": agreement,
            "hasUnresolvedDissent": not agreement or any(
                r["errorCodes"] for r in entries),
            "authorExpectedQuestionId": expected,
            "realExpertConsensus": False,
        })
    critical = [e for e in findings if e["severity"] == "critical"]
    return {
        "schema": "maintenance-superinteligence.review-rehearsal-report.v1",
        "version": "1.0.0",
        "mode": "author_simulated_review_no_real_experts",
        "blindPacketDigest": digest(packet),
        "sourceCasesDigest": digest(source),
        "editorialOracleDigest": digest(oracle),
        "submissionDigest": digest(submissions),
        "rubricDigest": digest(rubric),
        "casesReviewedInSimulation": 12,
        "fictionalReviewRecords": reviewer_total,
        "simulatedQuestionAgreement": {"same": same_questions, "total": 12},
        "authorOracleAgreement": {"matched": reviewer_correct, "total": reviewer_total},
        "criticalFindings": len(critical),
        "findings": findings,
        "cases": all_cases,
        "independentExpertReviewCompleted": False,
        "realReviewerIdentitiesVerified": False,
        "realAgreementMeasured": False,
        "mechanicalDiagnosticAccuracyMeasured": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_external_review_still_required",
    }

def verify_report(report, source, oracle, submissions, rubric):
    require(report == build_report(source, oracle, submissions, rubric),
            "report adulterated, claims promoted or source changed")
    return True

def render_html(report):
    require(report.get("schema") == "maintenance-superinteligence.review-rehearsal-report.v1"
            and report.get("decision") == "no_go_external_review_still_required"
            and report.get("independentExpertReviewCompleted") is False
            and report.get("mechanicalDiagnosticAccuracyMeasured") is False
            and report.get("mayCreateWorkOrder") is False
            and report.get("mayReleaseEquipment") is False,
            "cannot publish potentially approving review")
    sections = "".join(
        "<section><h2>" + escape(x["caseId"]) + " (" + escape(x["system"])
        + ")</h2><p>Simulated agreement: "
        + str(x["sameQuestionBetweenSimulatedReviewers"])
        + "; unresolved disagreement/error: " + str(x["hasUnresolvedDissent"])
        + ".</p></section>" for x in report["cases"]
    )
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            'form-action &apos;none&apos;"><title>Review rehearsal — NO GO</title>'
            '<style>body{font:15px system-ui;max-width:940px;margin:2em auto;'
            'padding:1em}section{border:1px solid #ccc;padding:1em;margin:1em 0}'
            '</style></head><body><h1>Simulação editorial de revisão — NO GO</h1>'
            '<p>Nenhum revisor humano participou. Concordância, divergências e'
            ' erros são fictícios. Não representa acurácia de manutenção.</p>'
            + sections + '</body></html>')

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=SOURCE_CASES)
    ap.add_argument("--oracle", type=Path, default=SOURCE_ORACLE)
    ap.add_argument("--submissions", type=Path, default=REVIEW_FIXTURE)
    ap.add_argument("--rubric", type=Path, default=RUBRIC_PATH)
    ap.add_argument("--blind-output", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--html", type=Path)
    args = ap.parse_args(argv)
    source = json.loads(args.source.read_text(encoding="utf-8"))
    oracle = json.loads(args.oracle.read_text(encoding="utf-8"))
    submissions = json.loads(args.submissions.read_text(encoding="utf-8"))
    rubric = json.loads(args.rubric.read_text(encoding="utf-8"))
    packet = build_blind_packet(source)
    validate_blind(packet, source)
    report = build_report(source, oracle, submissions, rubric)
    for path, value in ((args.blind_output, packet), (args.output, report)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(report), encoding="utf-8")
    return report

if __name__ == "__main__":
    main()
