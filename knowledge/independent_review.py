"""Cycle 37: independent technical review readiness packets; never certifies reviewers.

All public packets describe UNSENT work for unassigned human role slots. The
software cannot authenticate people, check OEM effectivity, or approve repairs.
It checks that requests remain linked to the reviewed and frozen synthetic data.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

from knowledge.causal_adjudication import (
    PLAN, POLICY as ADJ_POLICY, SUBMISSIONS, MATRIX, MAP_PATH,
    MECHANICAL_POLICY, DISCRIMINATION_POLICY, REVIEW_POLICY,
    load, build_ledger, adjudicate,
)
from pilot.change_review_packets import require, digest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "knowledge/independent-review-protocol.v1.json"
WORKLIST = ROOT / "knowledge/independent-review-worklist.v1.json"
ROLES = (
    ("author", "SIM-SLOT-AUTHOR"),
    ("custodian", "SIM-SLOT-CUSTODIAN"),
    ("technical_reviewer_a", "SIM-SLOT-REVIEW-A"),
    ("technical_reviewer_b", "SIM-SLOT-REVIEW-B"),
    ("adjudicator", "SIM-SLOT-ADJUDICATOR"),
)
SLOTS = ["technical_reviewer_a", "technical_reviewer_b", "adjudicator"]
CHECKS = (
    "oem_series_effectivity",
    "source_provenance",
    "field_case_custody",
    "documentary_counterexample",
    "independent_reviewer_opinions",
    "conflict_of_interest",
    "technical_adjudicator_signoff",
)
OPINION_FIELDS = (
    "reviewer_position", "reasoning", "source_scope",
    "contradictory_evidence", "requested_revision",
)
ACTIONS = ("defer", "retain_for_research", "propose_revision",
           "reject_unsubstantiated_inference")
FORBIDDEN = ("change_original_rule", "authorize_inspection", "authorize_test",
             "create_work_order", "release_equipment")
MISSING = (
    "verified_human_identity", "verified_reviewer_competence",
    "verified_independence_and_conflicts", "oem_series_effectivity",
    "evidence_origin_and_custody", "two_independent_opinions",
    "counterexample_resolution", "independent_adjudicator_signoff",
)
ROLE_KEYS = {"role", "slotAlias", "actualHumanAssigned", "identityVerified",
             "disciplineCredentialsVerified", "conflictOfInterestCleared",
             "independenceFromAuthorsVerified", "technicalSourceAccessAuthorized"}
PROTOCOL_KEYS = {
    "schema", "version", "mode", "purpose", "roleSlots", "reviewRequirements",
    "verifiedExternalReviewers", "externalTechnicalReviewCompleted",
    "realCaseDataIncluded", "causalValidityEstablished", "canPromoteRevision",
    "mayExecuteTest", "mayCreateWorkOrder", "mayReleaseEquipment",
}
REQ_KEYS = {
    "independentReviewerCount", "requiresDifferentTechnicalReviewers",
    "adjudicatorSeparateFromReviewers", "authorsCannotApprove",
    "reviewerQualificationEvidence", "requiredEvidenceCategories",
    "requiredDecisionFields", "acceptedEditorialActions",
    "forbiddenAutomaticActions", "technicalAcceptanceRequiredGates",
    "technicalRejectionRequires", "deferredIfAnyGateMissing",
    "deferredIfDissentUnresolved", "technicalRevisionNeedsFrozenDiff",
    "noAutomaticTechnicalAcceptance", "noAutomaticTechnicalRejection",
}
WORKLIST_KEYS = {
    "schema", "version", "nature", "externalReviewInvitationsSent",
    "authenticatedExternalSignatures", "tasks",
}
TASK_KEYS = {
    "taskId", "ruleId", "parentRecordId", "priorAdjudicationId",
    "priorReviewIds", "frozenRuleText", "proposedDraftText",
    "initialEditorialDisposition", "challengeSummary",
    "counterexampleStatus", "sourceIds", "supportingSourceScopes",
    "requiredEvidenceCategories", "requestedRoles",
    "reviewerAOpinionSubmitted", "reviewerBOpinionSubmitted",
    "independentReviewerQualificationsVerified", "identityAndConflictChecksVerified",
    "oemSeriesEffectivityVerified", "realEvidenceProvenanceVerified",
    "counterexampleResolved", "adjudicatorSignoffVerified",
    "mayApproveTechnicalRelation", "mayChangeUpstreamRule",
    "mayAuthorizeTest", "mayCreateWorkOrder", "mayReleaseEquipment",
}
TASK_DENIALS = (
    "reviewerAOpinionSubmitted", "reviewerBOpinionSubmitted",
    "independentReviewerQualificationsVerified", "identityAndConflictChecksVerified",
    "oemSeriesEffectivityVerified", "realEvidenceProvenanceVerified",
    "counterexampleResolved", "adjudicatorSignoffVerified",
    "mayApproveTechnicalRelation", "mayChangeUpstreamRule", "mayAuthorizeTest",
    "mayCreateWorkOrder", "mayReleaseEquipment",
)
ROLE_DENIALS = (
    "actualHumanAssigned", "identityVerified", "disciplineCredentialsVerified",
    "conflictOfInterestCleared", "independenceFromAuthorsVerified",
    "technicalSourceAccessAuthorized",
)
DENIALS = (
    "externalTechnicalReviewCompleted", "realCaseDataIncluded",
    "causalValidityEstablished", "canPromoteRevision",
    "mayExecuteTest", "mayCreateWorkOrder", "mayReleaseEquipment",
)


def validate_protocol(protocol):
    require(isinstance(protocol, dict) and set(protocol) == PROTOCOL_KEYS,
            "external review protocol unexpected fields")
    require(protocol["schema"] ==
            "maintenance-superinteligence.independent-review-protocol.v1"
            and protocol["version"] == "1.0.0"
            and protocol["mode"] == "synthetic_unassigned_independent_review_design"
            and protocol["purpose"] ==
              "prepare_external_human_review_without_authenticating_or_approving"
            and type(protocol["verifiedExternalReviewers"]) is int
            and protocol["verifiedExternalReviewers"] == 0
            and all(protocol[k] is False for k in DENIALS),
            "review readiness misrepresented as completed certification")
    roles = protocol["roleSlots"]
    require(isinstance(roles, list) and len(roles) == len(ROLES),
            "five separate role slots required")
    for r, (role, alias) in zip(roles, ROLES):
        require(isinstance(r, dict) and set(r) == ROLE_KEYS
                and r["role"] == role and r["slotAlias"] == alias
                and all(r[k] is False for k in ROLE_DENIALS),
                "reviewer role spoofing or fictional qualification claim")
    requirements = protocol["reviewRequirements"]
    require(isinstance(requirements, dict) and set(requirements) == REQ_KEYS
            and type(requirements["independentReviewerCount"]) is int
            and requirements["independentReviewerCount"] == 2
            and requirements["requiresDifferentTechnicalReviewers"] is True
            and requirements["adjudicatorSeparateFromReviewers"] is True
            and requirements["authorsCannotApprove"] is True
            and requirements["reviewerQualificationEvidence"] ==
                "verified_professional_experience_and_domain_competence_by_external_custodian"
            and requirements["requiredEvidenceCategories"] == list(CHECKS)
            and requirements["requiredDecisionFields"] == list(OPINION_FIELDS)
            and requirements["acceptedEditorialActions"] == list(ACTIONS)
            and requirements["forbiddenAutomaticActions"] == list(FORBIDDEN)
            and requirements["technicalAcceptanceRequiredGates"] == list(MISSING)
            and requirements["technicalRejectionRequires"] == [
                "documented_counterevidence_with_source",
                "two_independent_written_opinions",
                "adjudicator_reasoned_record",
                "source_and_version_effectivity",
            ]
            and all(requirements[k] is True for k in (
                "deferredIfAnyGateMissing", "deferredIfDissentUnresolved",
                "technicalRevisionNeedsFrozenDiff", "noAutomaticTechnicalAcceptance",
                "noAutomaticTechnicalRejection")),
            "review acceptance criteria incomplete or segregation loosened")
    return True


def validate_worklist(worklist, protocol, plan, policy, batch, matrix, parent,
                      mechanical_policy, discrimination_policy, review_policy):
    validate_protocol(protocol)
    # Review packages are deliberately restricted to the committed source
    # snapshot. Recomputing a digest of a swapped source is NOT authenticity.
    require(
        plan == load(PLAN)
        and policy == load(ADJ_POLICY)
        and batch == load(SUBMISSIONS)
        and matrix == load(MATRIX)
        and parent == load(MAP_PATH)
        and mechanical_policy == load(MECHANICAL_POLICY)
        and discrimination_policy == load(DISCRIMINATION_POLICY)
        and review_policy == load(REVIEW_POLICY),
        "independent review must use the complete frozen committed source snapshot")
    ledger = build_ledger(plan, policy, batch, matrix, parent,
                          mechanical_policy, discrimination_policy, review_policy)
    require(ledger["eventCount"] == 48
            and ledger["candidateVersionCount"] == 12
            and ledger["independentExpertApproval"] is False,
            "source versions not the frozen Cycle 36 unapproved artifacts")
    require(isinstance(worklist, dict) and set(worklist) == WORKLIST_KEYS
            and worklist["schema"] ==
                "maintenance-superinteligence.independent-review-worklist.v1"
            and worklist["version"] == "1.0.0"
            and worklist["nature"] == "synthetic_unassigned_packets_not_sent_to_reviewers"
            and type(worklist["externalReviewInvitationsSent"]) is int
            and worklist["externalReviewInvitationsSent"] == 0
            and type(worklist["authenticatedExternalSignatures"]) is int
            and worklist["authenticatedExternalSignatures"] == 0,
            "public worklist asserts human participation or was dispatched")
    tasks = worklist["tasks"]
    require(isinstance(tasks, list) and len(tasks) == len(matrix["rules"]) == 36,
            "36 exact reviewed rules required")
    parents = {p["recordId"]: p for p in parent["records"]}
    for i, (task, rule, proposal) in enumerate(zip(tasks, matrix["rules"], plan["items"])):
        require(isinstance(task, dict) and set(task) == TASK_KEYS,
                "task has extra or missing fields")
        original = parents[proposal["parentRecordId"]]
        require(task["taskId"] == f"REV-TASK-{i+1:03d}"
                and task["ruleId"] == rule["ruleId"]
                and task["parentRecordId"] == rule["parentRecordId"]
                and task["priorAdjudicationId"] == proposal["adjudicationId"]
                and task["priorReviewIds"] == proposal["reviewIds"]
                and task["frozenRuleText"] == rule["hypotheticalObservation"]
                and task["proposedDraftText"] == proposal["draftWording"]
                and task["initialEditorialDisposition"] ==
                    proposal["proposedDisposition"]
                and task["challengeSummary"] == proposal["reasoning"]
                and task["counterexampleStatus"] ==
                    proposal["counterexampleDisposition"]
                and task["sourceIds"] == proposal["referencedGeneralSources"]
                and task["supportingSourceScopes"] == original["supportNote"],
                "review task no longer bound to prior versions, dissent or source scope")
        require(task["requiredEvidenceCategories"] == list(CHECKS)
                and task["requestedRoles"] == SLOTS
                and all(task[k] is False for k in TASK_DENIALS),
                "missing evidence gate, reviewer slot or fictional signoff")
    return ledger


def build_packets(protocol, worklist, plan, policy, batch, matrix, parent,
                  mechanical_policy, discrimination_policy, review_policy):
    ledger = validate_worklist(worklist, protocol, plan, policy, batch, matrix, parent,
                               mechanical_policy, discrimination_policy, review_policy)
    source_catalog = {s["id"]: s for s in parent["sourceCatalog"]}
    packets = []
    for task in worklist["tasks"]:
        packets.append({
            "packetId": "IRP-" + task["taskId"][9:],
            "taskId": task["taskId"],
            "ruleId": task["ruleId"],
            "parentRecordId": task["parentRecordId"],
            "priorReviewIds": task["priorReviewIds"],
            "priorAdjudicationId": task["priorAdjudicationId"],
            "frozenRuleText": task["frozenRuleText"],
            "candidateTextForChallengeOnly": task["proposedDraftText"],
            "priorEditorialDisposition": task["initialEditorialDisposition"],
            "recordedObjection": task["challengeSummary"],
            "unresolvedCounterexample": task["counterexampleStatus"],
            "generalBackgroundSources": [
                {"sourceId": ident, "url": source_catalog[ident]["url"],
                 "permittedScope": source_catalog[ident]["supportedScope"],
                 "notEstablished": source_catalog[ident]["notSupported"]}
                for ident in task["sourceIds"]
            ],
            "requestedReviewerSlots": task["requestedRoles"],
            "reviewTemplateFields": list(OPINION_FIELDS),
            "requiredEvidenceCategories": task["requiredEvidenceCategories"],
            "unmetQualificationAndEvidenceGates": list(MISSING),
            "openCounterexample": True,
            "opinionCount": 0,
            "adjudicatorApprovalVerified": False,
            "independentReviewCompleted": False,
            "technicalRelationAccepted": False,
            "mayChangeUpstreamRule": False,
            "mayExecuteTest": False,
            "mayCreateWorkOrder": False,
            "mayReleaseEquipment": False,
            "status": "blocked_unassigned_reviewers_and_evidence",
        })
    return {
        "schema": "maintenance-superinteligence.independent-review-packets.v1",
        "version": "1.0.0",
        "mode": "public_synthetic_review_preparation_not_dispatched",
        "protocolDigest": digest(protocol),
        "worklistDigest": digest(worklist),
        "planDigest": digest(plan),
        "reviewDigest": digest(batch),
        "matrixDigest": digest(matrix),
        "versionLedgerDigest": digest(ledger),
        "packetCount": len(packets),
        "reviewerOpinionSlots": 2*len(packets),
        "adjudicatorSlots": len(packets),
        "realReviewOpinionsReceived": 0,
        "verifiedIndependentReviewers": 0,
        "allPermissionsDenied": True,
        "packets": packets,
        "independentReviewCompleted": False,
        "mayExecuteTest": False, "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
    }


def assess(protocol, worklist, plan, policy, batch, matrix, parent,
           mechanical_policy, discrimination_policy, review_policy):
    packets = build_packets(protocol, worklist, plan, policy, batch, matrix, parent,
                            mechanical_policy, discrimination_policy, review_policy)
    n = packets["packetCount"]
    return {
        "schema": "maintenance-superinteligence.independent-review-readiness.v1",
        "version": "1.0.0", "mode": "readiness_gap_analysis_not_real_expert_signoff",
        "packetDigest": digest(packets),
        "protocolDigest": digest(protocol), "worklistDigest": digest(worklist),
        "planDigest": digest(plan),
        "parentMatrixDigest": digest(matrix),
        "sourceReviewBatchDigest": digest(batch),
        "reviewTaskCount": n, "requestedReviewerOpinionSlots": n*2,
        "requestedAdjudicatorSlots": n,
        "missingGateCounts": {k: n for k in MISSING},
        "unassignedParticipantRoleSlots": len(ROLES),
        "actualVerifiedReviewers": 0,
        "opinionsCollected": 0,
        "qualifiedIndependentAdjudications": 0,
        "relationsEligibleForTechnicalAcceptance": 0,
        "relationsEligibleForTechnicalRejection": 0,
        "relationsPendingIndependentReview": n,
        "sourceRuleVersionsModified": 0,
        "externalHumanCredentialVerificationComplete": False,
        "oemSeriesEvidenceVerified": False,
        "fieldEvidenceProvenanceValidated": False,
        "independentTechnicalReviewCompleted": False,
        "technicalDiagnosticAccuracyEstablished": False,
        "readyToDispatchToVerifiedReviewers": False,
        "mayChangeUpstreamRule": False,
        "mayExecuteTest": False, "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_collect_real_credentials_and_review_evidence",
    }


def verify_report(report, packets, protocol, worklist, plan, policy, batch, matrix,
                  parent, mechanical_policy, discrimination_policy, review_policy):
    require(packets == build_packets(protocol, worklist, plan, policy, batch, matrix,
                                     parent, mechanical_policy, discrimination_policy,
                                     review_policy)
            and report == assess(protocol, worklist, plan, policy, batch, matrix,
                                 parent, mechanical_policy, discrimination_policy,
                                 review_policy),
            "review readiness report or source packets diverge from frozen inputs")
    return True


def render_html(report, packets, protocol, worklist, plan, policy, batch, matrix,
                parent, mechanical_policy, discrimination_policy, review_policy):
    verify_report(report, packets, protocol, worklist, plan, policy, batch, matrix,
                  parent, mechanical_policy, discrimination_policy, review_policy)
    blocks = []
    for p in packets["packets"]:
        sources = ", ".join(s["sourceId"] for s in p["generalBackgroundSources"])
        blocks.append("<section><h2>" + escape(p["ruleId"]) + "</h2>"
                      "<p>Desafio anterior: " + escape(p["recordedObjection"]) + "</p>"
                      "<p>Fontes gerais: " + escape(sources) + "</p>"
                      "<p>Ausentes: " + escape(", ".join(p["unmetQualificationAndEvidenceGates"])) + "</p>"
                      "<p>Decisão técnica: bloqueada. Não há pareceres reais.</p></section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; "
            'base-uri &apos;none&apos;; form-action &apos;none&apos;">'
            '<title>Ciclo 37 — Prontidão revisão independente</title>'
            '<style>body{font:15px system-ui;max-width:960px;margin:2em auto;'
            'padding:1em}section{border:1px solid #aaa;margin:1em 0;padding:1em}'
            '</style></head><body><h1>Protocolo para revisão externa — NO GO</h1>'
            '<p>36 pacotes sintéticos; nenhuma identidade verificada, literatura OEM '
            'por série ou evidência de campo custodiada; nenhuma opinião submetida. '
            'A matriz histórica não é modificada.</p>' + "".join(blocks) +
            '</body></html>')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--packets", type=Path, required=True)
    ap.add_argument("--html", type=Path)
    ap.add_argument("--protocol", type=Path, default=PROTOCOL)
    ap.add_argument("--worklist", type=Path, default=WORKLIST)
    args = ap.parse_args(argv)
    require(args.protocol.resolve() == PROTOCOL.resolve()
            and args.worklist.resolve() == WORKLIST.resolve(),
            "current public CLI only validates the committed synthetic readiness design")
    paths = [p.resolve() for p in (args.output, args.packets, args.html) if p is not None]
    require(len(paths) == len(set(paths)), "report and packet output paths must be distinct")
    for p in paths:
        require(not p.is_dir(), "output destination is a directory")
    protocol, worklist = load(PROTOCOL), load(WORKLIST)
    plan, policy, batch, matrix, parent, mp, dp, rp = [
        load(p) for p in (PLAN, ADJ_POLICY, SUBMISSIONS, MATRIX, MAP_PATH,
                         MECHANICAL_POLICY, DISCRIMINATION_POLICY, REVIEW_POLICY)
    ]
    packets = build_packets(protocol, worklist, plan, policy, batch, matrix,
                            parent, mp, dp, rp)
    report = assess(protocol, worklist, plan, policy, batch, matrix, parent,
                    mp, dp, rp)
    html = (render_html(report, packets, protocol, worklist, plan, policy, batch,
                        matrix, parent, mp, dp, rp) if args.html else None)
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    args.packets.write_text(json.dumps(packets, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    if args.html:
        args.html.write_text(html, encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
