"""Cycle 36 — controlled editorial adjudication of unverified causal claims.

This module stages WRITING proposals, never decides a real diagnostic outcome.
Versions and hash chains detect drift against a retained independent reference;
they do not prove human identity, immutable history, or OEM approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

from knowledge.causal_review import (
    SUBMISSIONS, POLICY as REVIEW_POLICY, freeze_receipt, evaluate as evaluate_review,
    triage_pair,
)
from knowledge.discriminating_evidence import (
    MATRIX, MAP_PATH, MECHANICAL_POLICY, POLICY as DISCRIMINATION_POLICY,
)
from pilot.change_review_packets import digest, require

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "knowledge/causal-adjudication-plan.v1.json"
POLICY = ROOT / "knowledge/causal-adjudication-policy.v1.json"
ACTIONS = (
    "defer_disputed_relation",
    "propose_unapproved_wording_revision",
    "reject_unsubstantiated_inference",
)
PRIORITIES = ("high_review_priority", "medium_review_priority",
              "watch_review_priority")
PRIOR_REVIEW_TRIAGES = (
    "unresolved_dissent", "revision_proposed_unapproved", "support_insufficient",
)
COUNTEREXAMPLE_TREATMENT = (
    "open_counterexample_pending_independent_review",
    "counterexample_not_resolved_by_wording",
    "no_causal_claim_accepted_due_to_insufficient_evidence",
)
DRAFT_SUFFIX = (
    "; caso confirmada por procedimento autorizado e aplicável, essa "
    "condição terá somente valor discriminante relativo e não comprovará "
    "causa raiz, efetividade OEM por série ou autorização operacional"
)
PLAN_KEYS = {"schema", "version", "nature", "humanAdjudicatorAuthenticated",
             "independentExpertAdjudicationCompleted", "items"}
ITEM_KEYS = {"adjudicationId", "ruleId", "parentRecordId", "reviewIds",
             "originalRuleText", "editorialPriority", "proposedDisposition",
             "reasoning", "counterexampleDisposition", "referencedGeneralSources",
             "draftWording", "reviewerQualifiedIndependently",
             "externalTechnicalApproval", "physicalCaseVerification",
             "oemEffectivityVerified", "mayAmendUpstream", "mayAuthorizeTest",
             "mayCreateWorkOrder", "mayReleaseEquipment"}
DENIALS = (
    "reviewerQualifiedIndependently", "externalTechnicalApproval",
    "physicalCaseVerification", "oemEffectivityVerified",
    "mayAmendUpstream", "mayAuthorizeTest", "mayCreateWorkOrder",
    "mayReleaseEquipment",
)
POLICY_KEYS = {"schema", "version", "minimumArgumentsLength",
               "expectedRuleCount", "expectedCandidateVersions",
               "expectedBaseVersions", "priorityLevels", "allowedDispositions",
               "independentSignoffVerified", "diagnosticValidityEstablished",
               "mayAmendUpstreamRules", "mayExecuteTests", "mayCreateWorkOrder",
               "mayReleaseEquipment"}
REVIEW_DENIALS = ("independentSignoffVerified", "diagnosticValidityEstablished",
                  "mayAmendUpstreamRules", "mayExecuteTests",
                  "mayCreateWorkOrder", "mayReleaseEquipment")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) == POLICY_KEYS
            and policy["schema"] == "maintenance-superinteligence.causal-adjudication-policy.v1"
            and policy["version"] == "1.0.0"
            and type(policy["minimumArgumentsLength"]) is int
            and policy["minimumArgumentsLength"] >= 100
            and type(policy["expectedRuleCount"]) is int
            and policy["expectedRuleCount"] == 36
            and type(policy["expectedBaseVersions"]) is int
            and policy["expectedBaseVersions"] == 36
            and type(policy["expectedCandidateVersions"]) is int
            and policy["expectedCandidateVersions"] == 12
            and policy["priorityLevels"] == list(PRIORITIES)
            and policy["allowedDispositions"] == list(ACTIONS)
            and all(policy[k] is False for k in REVIEW_DENIALS),
            "adjudication policy weakens safeguards or asserts approval")
    return True


def validate_plan(plan, policy, batch, matrix, parent, mechanical_policy,
                  discrimination_policy, review_policy):
    validate_policy(policy)
    review_receipt = freeze_receipt(batch, matrix, review_policy)
    review_report = evaluate_review(batch, matrix, parent, mechanical_policy,
                                    discrimination_policy, review_policy,
                                    review_receipt)
    require(review_report["pendingIndependentResolutionCount"] == 36
            and review_report["rulesExternallyReviewed"] is False
            and review_report["verifiedExpertReviewers"] == 0,
            "prior review unexpectedly treated as externally validated")
    require(isinstance(plan, dict) and set(plan) == PLAN_KEYS
            and plan["schema"] == "maintenance-superinteligence.causal-adjudication-plan.v1"
            and plan["version"] == "1.0.0"
            and plan["nature"] ==
                "author_synthetic_adjudication_drafts_not_engineering_approval"
            and plan["humanAdjudicatorAuthenticated"] is False
            and plan["independentExpertAdjudicationCompleted"] is False,
            "adjudication plan is not an unverified editorial rehearsal")
    items = plan["items"]
    require(isinstance(items, list)
            and len(items) == policy["expectedRuleCount"]
            and len(items) == len(matrix["rules"]),
            "not all frozen causal relations adjudicated")
    for i, item in enumerate(items):
        require(isinstance(item, dict) and set(item) == ITEM_KEYS,
                "adjudication entry has unexpected fields")
        rule = matrix["rules"][i]
        pair = batch["submissions"][2*i:2*i+2]
        triage = triage_pair(pair)
        require(triage in PRIOR_REVIEW_TRIAGES,
                "unsupported review triage: independent adjudication still required")
        idx = PRIOR_REVIEW_TRIAGES.index(triage)
        require(item["adjudicationId"] == f"SIM-ADJ-{i+1:03d}"
                and item["ruleId"] == rule["ruleId"]
                and item["parentRecordId"] == rule["parentRecordId"]
                and item["reviewIds"] == [r["reviewId"] for r in pair]
                and item["originalRuleText"] == rule["hypotheticalObservation"],
                "outdated rule/review reference or attempted historic overwrite")
        require(item["proposedDisposition"] == ACTIONS[idx]
                and item["editorialPriority"] == PRIORITIES[idx]
                and item["counterexampleDisposition"] ==
                    COUNTEREXAMPLE_TREATMENT[idx],
                "adjudication disagrees with recorded reviewer conflict")
        refs = sorted({ref for r in pair for ref in r["sourceIds"]})
        require(item["referencedGeneralSources"] == refs,
                "adjudication source references changed or removed")
        require(isinstance(item["reasoning"], str)
                and len(item["reasoning"].strip()) >=
                    policy["minimumArgumentsLength"]
                and rule["ruleId"] in item["reasoning"]
                and item["counterexampleDisposition"] != "",
                "decision requires technical rationale tied to the rule")
        for comment in pair:
            require(isinstance(comment["counterexample"], str)
                    and len(comment["counterexample"]) >= 55,
                    "counterexample silently omitted from upstream")
        if idx == 1:
            require(pair[0]["proposedRevision"] is not None
                    and pair[0]["proposedRevision"] == pair[1]["proposedRevision"]
                    and item["draftWording"] ==
                        rule["hypotheticalObservation"] + DRAFT_SUFFIX,
                    "v2 editorial draft must be based on same reviewed statement")
        else:
            require(item["draftWording"] is None,
                    "a rejected/deferred relation cannot create a candidate version")
        require(all(item[k] is False for k in DENIALS),
                "decision alleges verified diagnosis, signoff or operational right")
    return review_report


def _version_event(rule, version, text, decision_id, prior_version_digest,
                   previous_event_digest, matrix_digest, review_digest, policy_digest):
    status = ("frozen_historic_reference_unvalidated" if version == "v1-frozen"
              else "editorial_candidate_pending_independent_review")
    event = {
        "sequence": None,
        "eventId": "SIM-HIST-" + rule["ruleId"][5:] +
                   ("-1" if version == "v1-frozen" else "-2"),
        "ruleId": rule["ruleId"],
        "versionLabel": version,
        "text": text,
        "sourceRuleDigest": digest(rule),
        "frozenMatrixDigest": matrix_digest,
        "reviewBatchDigest": review_digest,
        "policyDigest": policy_digest,
        "decisionId": decision_id,
        "priorVersionDigest": prior_version_digest,
        "previousLedgerDigest": previous_event_digest,
        "technicalState": status,
        "independentExpertApproved": False,
        "replacesSourceRule": False,
        "mayExecuteTest": False,
        "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
    }
    return event


def build_ledger(plan, policy, batch, matrix, parent, mechanical_policy,
                 discrimination_policy, review_policy):
    validate_plan(plan, policy, batch, matrix, parent, mechanical_policy,
                  discrimination_policy, review_policy)
    matrix_hash = digest(matrix)
    batch_hash = digest(batch)
    policy_hash = digest(policy)
    previous = digest({
        "matrixDigest": matrix_hash, "reviewBatchDigest": batch_hash,
        "planDigest": digest(plan), "policyDigest": policy_hash,
    })
    events = []
    for rule, decision in zip(matrix["rules"], plan["items"]):
        original = _version_event(rule, "v1-frozen",
                    rule["hypotheticalObservation"], None, None, previous,
                    matrix_hash, batch_hash, policy_hash)
        original["sequence"] = len(events)+1
        original["eventDigest"] = digest(original)
        events.append(original)
        previous = original["eventDigest"]
        if decision["proposedDisposition"] == ACTIONS[1]:
            candidate = _version_event(rule, "v2-proposed-unapproved",
                        decision["draftWording"], decision["adjudicationId"],
                        original["eventDigest"], previous,
                        matrix_hash, batch_hash, policy_hash)
            candidate["sequence"] = len(events)+1
            candidate["eventDigest"] = digest(candidate)
            events.append(candidate)
            previous = candidate["eventDigest"]
    ledger = {
        "schema": "maintenance-superinteligence.causal-version-ledger.v1",
        "version": "1.0.0",
        "mode": "replayable_synthetic_snapshots_not_immutable_history",
        "matrixDigest": matrix_hash, "reviewBatchDigest": batch_hash,
        "planDigest": digest(plan), "policyDigest": policy_hash,
        "baseVersionCount": policy["expectedBaseVersions"],
        "candidateVersionCount": policy["expectedCandidateVersions"],
        "eventCount": len(events), "events": events,
        "chainHead": previous, "externallyTimestamped": False,
        "cryptographicallySigned": False, "upstreamChanged": False,
        "independentExpertApproval": False, "mayReleaseEquipment": False,
    }
    require(len(events) == 48, "version history must preserve 36 originals and 12 drafts")
    return ledger


def verify_ledger(ledger, plan, policy, batch, matrix, parent,
                  mechanical_policy, discrimination_policy, review_policy):
    require(ledger == build_ledger(plan, policy, batch, matrix, parent,
                                   mechanical_policy, discrimination_policy,
                                   review_policy),
            "version history edited, reordered or inconsistent with frozen inputs")
    return True


def adjudicate(plan, policy, batch, matrix, parent, mechanical_policy,
               discrimination_policy, review_policy):
    prior = validate_plan(plan, policy, batch, matrix, parent, mechanical_policy,
                          discrimination_policy, review_policy)
    ledger = build_ledger(plan, policy, batch, matrix, parent, mechanical_policy,
                          discrimination_policy, review_policy)
    dispositions = Counter(x["proposedDisposition"] for x in plan["items"])
    priorities = Counter(x["editorialPriority"] for x in plan["items"])
    decisions = []
    for item in plan["items"]:
        decisions.append({
            "adjudicationId": item["adjudicationId"],
            "ruleId": item["ruleId"],
            "sourceReviewIds": item["reviewIds"],
            "editorialPriority": item["editorialPriority"],
            "editorialDisposition": item["proposedDisposition"],
            "rationaleDigest": digest(item["reasoning"]),
            "openCounterexample": True,
            "candidateVersionWritten": item["draftWording"] is not None,
            "independentExpertApproval": False,
            "causeRootVerified": False,
            "mayAmendUpstream": False,
            "mayExecuteTest": False, "mayCreateWorkOrder": False,
            "mayReleaseEquipment": False,
        })
    return {
        "schema": "maintenance-superinteligence.causal-adjudication-report.v1",
        "version": "1.0.0",
        "mode": "synthetic_editorial_adjudication_no_operational_signoff",
        "matrixDigest": digest(matrix), "reviewBatchDigest": digest(batch),
        "reviewReceiptDigest": digest(freeze_receipt(batch, matrix, review_policy)),
        "reviewReportDigest": digest(prior),
        "planDigest": digest(plan), "policyDigest": digest(policy),
        "versionLedgerDigest": digest(ledger), "versionLedgerHead": ledger["chainHead"],
        "sourceRelations": len(matrix["rules"]),
        "dispositionCounts": {k: dispositions[k] for k in ACTIONS},
        "editorialReviewPriorityCounts": {k: priorities[k] for k in PRIORITIES},
        "historicBaselinesPreserved": ledger["baseVersionCount"],
        "unapprovedCandidateVersions": ledger["candidateVersionCount"],
        "unresolvedIndependentReviews": len(plan["items"]),
        "decisions": decisions,
        "realWorldSafetySeverityAssigned": False,
        "reviewersAuthenticated": False, "independentReviewCompleted": False,
        "causalDiagnosticValidityEstablished": False,
        "upstreamSourceRulesUpdated": False,
        "ledgerIsImmutable": False, "auditHashesProveIdentity": False,
        "mayExecuteTest": False, "mayCreateWorkOrder": False,
        "mayReleaseEquipment": False,
        "decision": "no_go_editorial_drafts_require_independent_engineering_adjudication",
    }


def verify_report(report, ledger, plan, policy, batch, matrix, parent,
                  mechanical_policy, discrimination_policy, review_policy):
    verify_ledger(ledger, plan, policy, batch, matrix, parent, mechanical_policy,
                  discrimination_policy, review_policy)
    require(report == adjudicate(plan, policy, batch, matrix, parent,
                                 mechanical_policy, discrimination_policy,
                                 review_policy),
            "report falsified, stale or inconsistent with full source chain")
    return True


def render_html(report, ledger, plan, policy, batch, matrix, parent,
                mechanical_policy, discrimination_policy, review_policy):
    verify_report(report, ledger, plan, policy, batch, matrix, parent,
                  mechanical_policy, discrimination_policy, review_policy)
    sections = []
    for decision in report["decisions"]:
        sections.append(
            "<section><h2>" + escape(decision["ruleId"]) + "</h2>"
            "<p>Prioridade editorial: " + escape(decision["editorialPriority"]) + "</p>"
            "<p>Destino editorial: " + escape(decision["editorialDisposition"]) + "</p>"
            "<p>Relação técnica não homologada; contraexemplo em aberto.</p>"
            "</section>"
        )
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; "
        'base-uri &apos;none&apos;; form-action &apos;none&apos;">'
        '<title>Ciclo 36 — Adjudicação editorial não homologada</title>'
        '<style>body{font:15px system-ui;max-width:980px;margin:2em auto;'
        'padding:1em}section{border:1px solid #aaa;margin:1em 0;padding:1em}'
        '</style></head><body><h1>Adjudicação controlada — NO GO</h1>'
        '<p>36 relações, 12 candidatas v2; 0 pareceres independentes confirmados.'
        ' A gravidade é prioridade de revisão editorial, não risco operacional.'
        ' Hashes detectam mudanças apenas com referência preservada; sem assinatura.'
        '</p>' + "".join(sections) + "</body></html>"
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, default=PLAN)
    ap.add_argument("--policy", type=Path, default=POLICY)
    ap.add_argument("--submissions", type=Path, default=SUBMISSIONS)
    ap.add_argument("--review-policy", type=Path, default=REVIEW_POLICY)
    ap.add_argument("--matrix", type=Path, default=MATRIX)
    ap.add_argument("--parent", type=Path, default=MAP_PATH)
    ap.add_argument("--mechanical-policy", type=Path, default=MECHANICAL_POLICY)
    ap.add_argument("--discrimination-policy", type=Path, default=DISCRIMINATION_POLICY)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--html", type=Path)
    args = ap.parse_args(argv)
    from benchmarks.heldout_study import private_path, save_private
    external = args.plan.resolve() != PLAN.resolve()
    if external:
        for path in (args.plan, args.output, args.ledger, args.html):
            if path is not None:
                private_path(path)
        require(args.submissions.resolve() == SUBMISSIONS.resolve()
                and args.review_policy.resolve() == REVIEW_POLICY.resolve()
                and args.matrix.resolve() == MATRIX.resolve()
                and args.parent.resolve() == MAP_PATH.resolve()
                and args.mechanical_policy.resolve() == MECHANICAL_POLICY.resolve()
                and args.discrimination_policy.resolve() == DISCRIMINATION_POLICY.resolve()
                and args.policy.resolve() == POLICY.resolve(),
                "external proposals must reference committed synthetic review fixtures")
    paths = (args.plan, args.policy, args.submissions, args.matrix, args.parent,
             args.mechanical_policy, args.discrimination_policy, args.review_policy)
    plan, policy, batch, matrix, parent, mp, dp, rp = [load(p) for p in paths]
    ledger = build_ledger(plan, policy, batch, matrix, parent, mp, dp, rp)
    report = adjudicate(plan, policy, batch, matrix, parent, mp, dp, rp)
    html = (render_html(report, ledger, plan, policy, batch, matrix, parent, mp, dp, rp)
            if args.html else None)
    if external:
        require(len({p.resolve() for p in
                     (args.output, args.ledger, args.html) if p is not None}) ==
                2 + int(args.html is not None), "private outputs must be distinct")
        for p in (args.output, args.ledger, args.html):
            if p is not None:
                require(not p.exists(), "private output already exists")
        save_private(args.output, report)
        save_private(args.ledger, ledger)
        if args.html:
            path=private_path(args.html)
            with path.open("x",encoding="utf-8") as out:
                out.write(html)
    else:
        require(args.output.resolve()!=args.ledger.resolve(),
                "report and version ledger cannot use same output path")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.ledger.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                               encoding="utf-8")
        args.ledger.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+"\n",
                               encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(html,encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
