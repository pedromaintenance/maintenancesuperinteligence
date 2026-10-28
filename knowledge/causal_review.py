"""Cycle 35 — review challenges, counterexamples and dissent, never signoff.

The public rehearsal contains only fictional author-generated comments. An external
private input MAY be recorded, but identity and technical independence CANNOT be
verified by this tool. SHA-256 linking is not a digital signature or immutable log.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

from knowledge.discriminating_evidence import (
    MATRIX, MAP_PATH, MECHANICAL_POLICY, POLICY as DISCRIMINATION_POLICY,
    validate_matrix,
)
from pilot.change_review_packets import digest, require

ROOT=Path(__file__).resolve().parents[1]
SUBMISSIONS=ROOT/"knowledge/causal-review-submissions.v1.json"
POLICY=ROOT/"knowledge/causal-review-policy.v1.json"
DISPOSITIONS=("retain_for_study","revise_before_use",
              "remove_from_proposed_taxonomy","cannot_assess")
CHALLENGES=("counterexample_unaddressed","causal_direction_uncertain",
            "unverified_source_applicability","insufficient_discriminator")
INVARIANT_DENIALS=("reviewerIdentityVerified","independentExpertStatusVerified",
                   "observedCaseEvidence","rootCauseEstablished",
                   "oemEffectivityVerified","engineeringSignoff",
                   "mayAuthorizeTest","mayCreateWorkOrder","mayReleaseEquipment")
SUBMISSION_FIELDS={"reviewId","ruleId","parentRecordId","ruleText","reviewerAlias",
                   "reviewerIdentityVerified","independentExpertStatusVerified",
                   "disposition","challengeType","argument","counterexample",
                   "sourceIds","sourceScope","proposedRevision","observedCaseEvidence",
                   "rootCauseEstablished","oemEffectivityVerified",
                   "engineeringSignoff","mayAuthorizeTest","mayCreateWorkOrder",
                   "mayReleaseEquipment"}
POLICY_FIELDS={"schema","version","purpose","requiredReviewersPerRule",
               "dispositions","challengeTypes","approvedIndependentReviewerCount",
               "realCausalValidationCompleted","canAmendUpstreamRules",
               "mayExecuteTest","mayCreateWorkOrder","mayReleaseEquipment"}
SUBMISSIONS_FIELDS={"schema","version","nature","authenticHumanReviewCount",
                    "independentTechnicalReviewCompleted","submissions"}
TRIAGE=("unresolved_dissent","revision_proposed_unapproved",
        "removal_proposed_unapproved","support_insufficient",
        "retain_as_unverified_hypothesis")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_policy(policy):
    require(isinstance(policy,dict) and set(policy)==POLICY_FIELDS
            and policy["schema"]=="maintenance-superinteligence.causal-review-policy.v1"
            and policy["version"]=="1.0.0"
            and policy["purpose"]=="open_technical_challenge_triage_not_validation"
            and type(policy["requiredReviewersPerRule"]) is int
            and policy["requiredReviewersPerRule"]==2
            and policy["dispositions"]==list(DISPOSITIONS)
            and policy["challengeTypes"]==list(CHALLENGES)
            and type(policy["approvedIndependentReviewerCount"]) is int
            and policy["approvedIndependentReviewerCount"]==0
            and all(policy[k] is False for k in
                ("realCausalValidationCompleted","canAmendUpstreamRules",
                 "mayExecuteTest","mayCreateWorkOrder","mayReleaseEquipment")),
            "review policy claims external approval or permits action")
    return True


def validate_submissions(batch,matrix,parent,mechanical_policy,discrimination_policy,policy):
    validate_policy(policy)
    validate_matrix(matrix,parent,mechanical_policy,discrimination_policy)
    require(isinstance(batch,dict) and set(batch)==SUBMISSIONS_FIELDS
            and batch["schema"]=="maintenance-superinteligence.causal-review-submissions.v1"
            and batch["version"]=="1.0.0"
            and batch["nature"] in
                ("synthetic_author_simulated_not_independent",
                 "unverified_private_reviewer_submissions")
            and type(batch["authenticHumanReviewCount"]) is int
            and batch["authenticHumanReviewCount"]==0
            and batch["independentTechnicalReviewCompleted"] is False,
            "unverified comments falsely promoted to independent review")
    data=batch["submissions"]
    require(isinstance(data,list)
            and len(data)==len(matrix["rules"])*policy["requiredReviewersPerRule"],
            "two complete challenges for each of 36 rules required")
    parents={r["recordId"]:r for r in parent["records"]}
    aliases=set()
    for i,record in enumerate(data):
        require(isinstance(record,dict) and set(record)==SUBMISSION_FIELDS,
                "missing or unknown critique field")
        rule=matrix["rules"][i//2]
        n=i//2+1
        j=i%2+1
        kind=batch["nature"]
        expected_id=(f"SIM-CR-{n:03d}-{j}" if
                     kind=="synthetic_author_simulated_not_independent"
                     else f"REV-CR-{n:03d}-{j}")
        alias=record["reviewerAlias"]
        require(record["reviewId"]==expected_id
                and record["ruleId"]==rule["ruleId"]
                and record["parentRecordId"]==rule["parentRecordId"]
                and record["ruleText"]==rule["hypotheticalObservation"]
                and isinstance(alias,str)
                and (alias in ("SIM-CRITIC-A","SIM-CRITIC-B")
                     if kind=="synthetic_author_simulated_not_independent"
                     else bool(re.fullmatch(r"REV-[A-Z0-9]{2,18}",alias))),
                "stale rule reference or reviewer alias/record mismatch")
        if kind=="synthetic_author_simulated_not_independent":
            require(alias==("SIM-CRITIC-A" if j==1 else "SIM-CRITIC-B"),
                    "public rehearsal not reproducible")
        else:
            # Two aliases in consistent order for every case; no identity proof.
            if i<2:
                aliases.add(alias)
            else:
                require(alias in aliases and alias==
                        data[i%2]["reviewerAlias"],"reviewer assignment changed")
        require(record["disposition"] in DISPOSITIONS
                and record["challengeType"] in CHALLENGES
                and record["sourceScope"]==
                    "generic_manufacturer_context_not_case_specific_proof"
                and isinstance(record["argument"],str)
                and len(record["argument"].strip())>=65
                and isinstance(record["counterexample"],str)
                and len(record["counterexample"].strip())>=55,
                "missing technical objection, counterexample or scope")
        valid_sources=parents[rule["parentRecordId"]]["sourceIds"]
        refs=record["sourceIds"]
        require(isinstance(refs,list) and len(refs)>=1
                and len(set(refs))==len(refs)
                and set(refs).issubset(set(valid_sources)),
                "source does not support the parent technical context")
        revision=record["proposedRevision"]
        require((isinstance(revision,str)
                 and len(revision.strip())>=65)
                if record["disposition"]=="revise_before_use"
                else revision is None,
                "proposed revision missing or editorial rewrite not requested")
        require(all(record[k] is False for k in INVARIANT_DENIALS),
                "editorial challenge forged evidence, signoff or permission")
    if batch["nature"]=="unverified_private_reviewer_submissions":
        require(len(aliases)==2 and
                data[0]["reviewerAlias"]!=data[1]["reviewerAlias"],
                "two distinct reviewer aliases required (identity still unverified)")
    return data


def freeze_receipt(batch,matrix,policy):
    return {
        "schema":"maintenance-superinteligence.causal-review-receipt.v1",
        "version":"1.0.0",
        "matrixDigest":digest(matrix),
        "batchDigest":digest(batch),
        "policyDigest":digest(policy),
        "signsOrAuthenticatesReviewer":False,
        "independentReviewValidated":False,
        "frozen":True,
    }


def verify_receipt(receipt,batch,matrix,policy):
    require(receipt==freeze_receipt(batch,matrix,policy),
            "review submission changed after freeze or receipt falsified")
    return True


def triage_pair(pair):
    opinions=[x["disposition"] for x in pair]
    if opinions[0]!=opinions[1]:
        return "unresolved_dissent"
    return {
        "retain_for_study":"retain_as_unverified_hypothesis",
        "revise_before_use":"revision_proposed_unapproved",
        "remove_from_proposed_taxonomy":"removal_proposed_unapproved",
        "cannot_assess":"support_insufficient",
    }[opinions[0]]


def evaluate(batch,matrix,parent,mechanical_policy,discrimination_policy,policy,receipt):
    answers=validate_submissions(batch,matrix,parent,mechanical_policy,
                                 discrimination_policy,policy)
    verify_receipt(receipt,batch,matrix,policy)
    report_cases=[]
    entries=[]
    previous=digest({"matrixDigest":digest(matrix),"policyDigest":digest(policy),
                     "reviewReceiptDigest":digest(receipt)})
    for i,record in enumerate(answers):
        event={"sequence":i+1,"reviewId":record["reviewId"],
               "recordDigest":digest(record),"previousDigest":previous}
        event["linkDigest"]=digest(event)
        entries.append(event)
        previous=event["linkDigest"]
    for i,rule in enumerate(matrix["rules"]):
        pair=answers[2*i:2*i+2]
        triage=triage_pair(pair)
        report_cases.append({
            "ruleId":rule["ruleId"],
            "parentRecordId":rule["parentRecordId"],
            "sourceRuleOutcome":rule["outcome"],
            "editorialReviewerAliases":[x["reviewerAlias"] for x in pair],
            "recordedDispositions":[x["disposition"] for x in pair],
            "challengeTypes":[x["challengeType"] for x in pair],
            "referencedGenericSources":sorted(set(
                s for r in pair for s in r["sourceIds"])),
            "hasProposedUnapprovedRevision":any(
                r["proposedRevision"] is not None for r in pair),
            "editorialTriage":triage,
            "requiresIndependentTechnicalResolution":True,
            "technicalRelationValidated":False,
            "mayChangeUpstreamRule":False,
        })
    counts=Counter(x["editorialTriage"] for x in report_cases)
    return {
        "schema":"maintenance-superinteligence.causal-review-report.v1",
        "version":"1.0.0",
        "mode":"editorial_review_rehearsal" if batch["nature"].startswith("synthetic")
               else "unverified_private_submission_triage",
        "matrixDigest":digest(matrix),"parentDigest":digest(parent),
        "mechanicalPolicyDigest":digest(mechanical_policy),
        "discriminationPolicyDigest":digest(discrimination_policy),
        "reviewPolicyDigest":digest(policy),
        "submissionDigest":digest(batch),"receiptDigest":digest(receipt),
        "sourceRuleCount":len(matrix["rules"]),
        "recordedUnverifiedChallenges":len(answers),
        "verifiedExpertReviewers":0,
        "editorialTriageCounts":{x:counts[x] for x in TRIAGE},
        "pendingIndependentResolutionCount":len(matrix["rules"]),
        "reviewedRules":report_cases,
        "auditChain":[*entries],
        "auditChainHead":previous,
        "auditChainAuthenticatesPeople":False,
        "rulesExternallyReviewed":False,
        "causalMechanismsFieldValidated":False,
        "sourceApplicabilityPerSerialVerified":False,
        "upstreamRulesAmended":False,
        "mayExecuteTest":False,"mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
        "decision":"no_go_independent_causal_review_required",
    }


def verify_report(report,batch,matrix,parent,mechanical_policy,
                  discrimination_policy,policy,receipt):
    require(report==evaluate(batch,matrix,parent,mechanical_policy,
                             discrimination_policy,policy,receipt),
            "audit trace, review data or decision changed after evaluation")
    return True


def render_html(report,batch,matrix,parent,mechanical_policy,
                discrimination_policy,policy,receipt):
    verify_report(report,batch,matrix,parent,mechanical_policy,
                  discrimination_policy,policy,receipt)
    require(report["decision"]=="no_go_independent_causal_review_required"
            and report["mayReleaseEquipment"] is False
            and report["rulesExternallyReviewed"] is False,
            "attempted release or validation through review HTML")
    blocks=[]
    for row in report["reviewedRules"]:
        blocks.append("<section><h2>"+escape(row["ruleId"])+
                      "</h2><p><b>Triagem autoral:</b> "+
                      escape(row["editorialTriage"])+
                      "</p><p><b>Contestações:</b> "+
                      escape(", ".join(row["challengeTypes"]))+
                      "</p><p><b>Fontes gerais:</b> "+
                      escape(", ".join(row["referencedGenericSources"]))+
                      "</p><p>Pendente revisão técnica independente.</p></section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri "
            '&apos;none&apos;; form-action &apos;none&apos;">'
            '<title>Cycle 35 critical causal review — NO GO</title>'
            '<style>body{font:15px system-ui;max-width:960px;margin:2em auto;'
            'padding:1em}section{border:1px solid #bbb;margin:1em 0;padding:1em}'
            '</style></head><body><h1>Contestações causais — simulação, NO GO</h1>'
            '<p>Os revisores do ensaio são personagens. Hashes não são '
            'assinaturas; sem validação humana, fonte por série ou diagnóstico.</p>'
            +"".join(blocks)+"</body></html>")


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--submissions",type=Path,default=SUBMISSIONS)
    ap.add_argument("--matrix",type=Path,default=MATRIX)
    ap.add_argument("--parent",type=Path,default=MAP_PATH)
    ap.add_argument("--mechanical-policy",type=Path,default=MECHANICAL_POLICY)
    ap.add_argument("--discrimination-policy",type=Path,default=DISCRIMINATION_POLICY)
    ap.add_argument("--policy",type=Path,default=POLICY)
    ap.add_argument("--receipt",type=Path)
    ap.add_argument("--seal-only",action="store_true")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--html",type=Path)
    args=ap.parse_args(argv)
    external=args.submissions.resolve()!=SUBMISSIONS.resolve()
    if external:
        from benchmarks.heldout_study import private_path
        for p in (args.submissions,args.output,args.receipt,args.html):
            if p is not None:
                private_path(p)
        require(args.matrix.resolve()==MATRIX.resolve()
                and args.parent.resolve()==MAP_PATH.resolve()
                and args.policy.resolve()==POLICY.resolve()
                and args.mechanical_policy.resolve()==MECHANICAL_POLICY.resolve()
                and args.discrimination_policy.resolve()==DISCRIMINATION_POLICY.resolve(),
                "private reviewers must refer to version-controlled technical rules")
    else:
        require(not args.seal_only and args.receipt is None,
                "public rehearsal uses a deterministic in-memory receipt")
    batch,matrix,parent,mpolicy,dpolicy,policy=[
        load(p) for p in (args.submissions,args.matrix,args.parent,
                          args.mechanical_policy,args.discrimination_policy,args.policy)]
    validate_submissions(batch,matrix,parent,mpolicy,dpolicy,policy)
    from benchmarks.heldout_study import save_private,read_private
    expected_receipt=freeze_receipt(batch,matrix,policy)
    if args.seal_only:
        save_private(args.output,expected_receipt)
        return expected_receipt
    receipt=(read_private(args.receipt)
             if external and args.receipt is not None else expected_receipt)
    require(not external or args.receipt is not None,
            "unverified private review requires separately frozen receipt")
    report=evaluate(batch,matrix,parent,mpolicy,dpolicy,policy,receipt)
    if external:
        save_private(args.output,report)
    else:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                               encoding="utf-8")
    if args.html:
        html=render_html(report,batch,matrix,parent,mpolicy,dpolicy,policy,receipt)
        if external:
            from benchmarks.heldout_study import private_path
            path=private_path(args.html)
            fd=path.open("x",encoding="utf-8")
            with fd as out:out.write(html)
        else:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(html,encoding="utf-8")
    return report


if __name__=="__main__":
    main()
