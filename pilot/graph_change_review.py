"""Cycle 24 — hypothetical graph-change reviewer; every proposal is VETOED.

Graph semantics here are DOCUMENTARY only. No physical failure probability,
OEM applicability, human qualification, private pilot or SAP authority inferred.
No mutable access to the canonical DAG or its original 100-case oracle.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import sys

from connectors.fmea_public import ImportRejected, require, load_lock, validate_snapshot
from evidence.ledger import sha
from methods.library import ROOT
from pilot.go_nogo import PACKAGE_PATH as GNG_PACKAGE, DEPENDENCIES, build_report as build_gng
from pilot.evidence_sequence import SPEC_PATH as SEQ_SPEC, build_report as build_seq
from pilot.evidence_contradictions import FIXTURE_PATH as CONF_SPEC, build_report as build_conf
from pilot.reopen_coverage import (
    SPEC_PATH as COV_SPEC, IDS, EDGE_LIST, independent_oracle, _is_acyclic,
    build_report as build_coverage
)
from pilot.readiness import FIXTURE_PATH as READY_SPEC, build_report as build_readiness
from editorial.review_protocol import FIXTURE_PATH as EDIT_SPEC, build_report as build_edit
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as build_quality
from notifications.drafts import SPEC_PATH as NOTE_SPEC, build_notifications
from casefiles.integrated import FIXTURE_PATH as CASE_SPEC, load_dependencies, build_collection

SPEC_PATH=ROOT/"pilot/graph-change-proposals.v1.json"
AREAS=("IT","InformationSecurity","Engineering","Legal","MaintenanceManagement")
PROPOSAL_DEFS=(
    ("SIM-GDIFF-01","edge_add","identity-proof","trusted-audit",None,None,"redundant_shortcut_path"),
    ("SIM-GDIFF-02","edge_remove","signed-decision","operational-firewall",None,None,"remove_redundant_link"),
    ("SIM-GDIFF-03","edge_reverse","trusted-audit","operational-firewall",None,None,"reverse_documentary_dependency"),
    ("SIM-GDIFF-04","owner_change",None,None,"oem-effectivity","IT","unauthorized_engineering_owner_change"),
    ("SIM-GDIFF-05","control_remove",None,None,"oem-effectivity",None,"critical_control_suppression"),
    ("SIM-GDIFF-06","edge_add","oem-effectivity","revocation-reopen",None,None,"oem_context_revision_requires_reopen"),
    ("SIM-GDIFF-07","edge_remove","equipment-configuration","oem-effectivity",None,None,"discard_oem_configuration_prerequisite"),
    ("SIM-GDIFF-08","edge_add","identity-proof","operational-firewall",None,None,"redundant_direct_path"),
    ("SIM-GDIFF-09","edge_add","operational-firewall","identity-proof",None,None,"attempted_cycle"),
    ("SIM-GDIFF-10","edge_add","unknown-node","oem-effectivity",None,None,"unknown_source_injection"),
)
POLICY_FALSE=("identityVerified","competenceVerified","independentReviewVerified",
              "oemEffectivityVerified","legalReviewVerified","signatureVerified",
              "externalAuditVerified","mayWaiveReview","mayWriteSap","mayModifyEcm",
              "mayCreateWorkOrder","mayOrderParts","mayReleaseEquipment")
TOP_KEYS={"schema","version","mode","baseGraph","baseQualityOracle","sourceNoGo",
          "canonicalNodeCount","canonicalEdgeCount","referenceCaseCount",
          "allProposalsUnapproved","realExpertReviewsCompleted","proposals","reviewPolicy"}
PROPOSAL_KEYS={"proposalId","changeType","sourceId","targetId","controlId",
               "newOwner","rationale","intent","sourceAuthenticated",
               "technicalCompetenceVerified","mayModifyCanonicalFixture","mayMerge"}

def exact(d, keys, where):
    require(isinstance(d,dict) and set(d)==keys,
            "graph change: unknown or missing fields in "+where)
    return d

def validate_spec(spec,coverage,gng):
    f=exact(spec,TOP_KEYS,"spec")
    require(f["schema"]=="maintenance-superinteligence.graph-change-proposals.v1"
            and f["version"]=="1.0.0"
            and f["mode"]=="synthetic_proposals_no_contract_mutation"
            and f["baseGraph"]=="pilot/reopen-coverage.v1.json"
            and f["baseQualityOracle"]=="pilot/reopen-coverage.v1.json"
            and f["sourceNoGo"]=="pilot/go-nogo-package.v1.json"
            and f["canonicalNodeCount"]==13 and f["canonicalEdgeCount"]==17
            and f["referenceCaseCount"]==100
            and f["allProposalsUnapproved"] is True
            and f["realExpertReviewsCompleted"]==0
            and isinstance(f["proposals"],list)
            and len(f["proposals"])==len(PROPOSAL_DEFS),
            "graph change: proposal corpus changed or external claim injected")
    policy=exact(f["reviewPolicy"],{"requiredAreas","decision",*POLICY_FALSE},"review policy")
    require(policy["requiredAreas"]==list(AREAS)
            and policy["decision"]=="no_go"
            and all(policy[k] is False for k in POLICY_FALSE),
            "graph change: fabricated review, signature or operating permission")
    require(coverage["schema"]=="maintenance-superinteligence.reopen-coverage-report.v1"
            and coverage["controlCount"]==13 and coverage["edgeCount"]==17
            and coverage["scenarioCount"]==100 and coverage["decision"]=="no_go"
            and gng["schema"]=="maintenance-superinteligence.go-nogo-report.v1"
            and gng["decision"]=="no_go"
            and gng["verifiedEvidenceCount"]==0
            and gng["verifiedSignoffs"]==0
            and gng["noOperationalAuthority"]["mayWriteSap"] is False,
            "graph change: only pinned synthetic 100-case oracle and NO GO allowed")
    require(len(IDS)==13 and len(EDGE_LIST)==17
            and set(DEPENDENCIES)==set(IDS) and _is_acyclic(DEPENDENCIES)
            and len(coverage["coverageCases"])==100,
            "graph change: source DAG or independent oracle invalid")
    for p,parts in zip(f["proposals"],PROPOSAL_DEFS):
        exact(p,PROPOSAL_KEYS,"proposal")
        keys=("proposalId","changeType","sourceId","targetId","controlId",
              "newOwner","rationale")
        require(tuple(p[k] for k in keys)==parts
                and p["intent"]=="unapproved_editorial_proposal_only"
                and all(p[k] is False for k in
                        ("sourceAuthenticated","technicalCompetenceVerified",
                         "mayModifyCanonicalFixture","mayMerge")),
                "graph change: unauthorized modification or unknown proposal")
    return f

def all_pair_matrix(pred):
    """Independent comparison via Cycle 23 Floyd–Warshall oracle for each root."""
    return {
        root:{
            target:{
                "reachable":target in metrics,
                "minimumSteps":metrics[target]["minimumSteps"] if target in metrics else None,
                "possiblePathCount":metrics[target]["possiblePathCount"] if target in metrics else 0,
            } for target in IDS
        } for root in IDS for affected,_,metrics in [independent_oracle([root],pred)]
    }

def propose(pred,proposal,owner_map):
    """Return isolated candidate, never modify canonical or input dictionaries."""
    p=proposal
    candidate={k:tuple(v) for k,v in pred.items()}
    owners=dict(owner_map)
    typ=p["changeType"]
    a,b=p["sourceId"],p["targetId"]
    if typ=="owner_change":
        if owners.get(p["controlId"]) is None:
            return None,owners,"unknown_control"
        owners[p["controlId"]]=p["newOwner"]
        return candidate,owners,"owner_role_boundary_violation"
    if typ=="control_remove":
        # No partial DAG is accepted: control IDs and coverage corpus are immutable.
        return None,owners,"protected_control_removed"
    if a not in candidate or b not in candidate:
        return None,owners,"unknown_endpoint"
    if a==b:
        return None,owners,"self_dependency"
    before=set((up,down) for down,ps in candidate.items() for up in ps)
    if typ=="edge_add":
        if (a,b) in before:
            return None,owners,"duplicate_edge"
        before.add((a,b))
    elif typ=="edge_remove":
        if (a,b) not in before:
            return None,owners,"missing_edge"
        before.remove((a,b))
    elif typ=="edge_reverse":
        if (a,b) not in before or (b,a) in before:
            return None,owners,"invalid_reversal"
        before.remove((a,b))
        before.add((b,a))
    else:
        return None,owners,"unsupported_change"
    changed={k:tuple(x for x in IDS if (x,k) in before) for k in IDS}
    if not _is_acyclic(changed):
        return None,owners,"cycle_detected"
    return changed,owners,"candidate_dag_only_not_approved"

def _compare_matrices(original,changed):
    diffs=[]
    for root in IDS:
        for target in IDS:
            a,b=original[root][target],changed[root][target]
            if a!=b:
                diffs.append({
                    "rootControlId":root,
                    "targetControlId":target,
                    "oldReachable":a["reachable"],"newReachable":b["reachable"],
                    "oldMinimumSteps":a["minimumSteps"],
                    "newMinimumSteps":b["minimumSteps"],
                    "oldPossiblePathCount":a["possiblePathCount"],
                    "newPossiblePathCount":b["possiblePathCount"],
                    "newPathIntroduced":not a["reachable"] and b["reachable"],
                    "oldPathLost":a["reachable"] and not b["reachable"],
                    "documentaryChangeOnly":True,
                    "physicalSafetyEstablished":False,
                })
    return diffs

def _case_delta(c,original,proposed):
    roots=c["rootControlIds"]
    old_a,_,old_m=independent_oracle(roots,original)
    new_a,_,new_m=independent_oracle(roots,proposed)
    changed=[t for t in IDS if (t in old_a)!=(t in new_a)
             or old_m.get(t)!=new_m.get(t)]
    return {
        "caseId":c["caseId"],
        "rootControlIds":list(roots),
        "oldAffectedCount":len(old_a),
        "newAffectedCount":len(new_a),
        "introducedAffectedControls":[x for x in IDS if x in new_a and x not in old_a],
        "lostAffectedControls":[x for x in IDS if x in old_a and x not in new_a],
        "changedMetricControlIds":changed,
        "noFieldEvidence":True,
        "mayAuthorizeMaintenance":False,
    }

def build_report(spec,coverage,gng):
    validate_spec(spec,coverage,gng)
    original=dict(DEPENDENCIES)
    baseline=all_pair_matrix(original)
    owner_map={c["controlId"]:c["owner"]
               for c in json.loads(GNG_PACKAGE.read_text(encoding="utf-8"))["controlPlan"]}
    require(set(owner_map)==set(IDS),"graph change: canonical control ownership missing")
    results=[]
    for p in spec["proposals"]:
        candidate,owners,validation=propose(original,p,owner_map)
        valid=candidate is not None and validation=="candidate_dag_only_not_approved"
        # The owner change is syntactically modeled, but violates governance.
        owner_violated=validation=="owner_role_boundary_violation"
        if candidate is None:
            differences=[]
            impacts=[]
            add_roots=[]
            lost_roots=[]
        else:
            mutated=all_pair_matrix(candidate)
            differences=_compare_matrices(baseline,mutated)
            impacts=[_case_delta(c,original,candidate) for c in coverage["coverageCases"]]
            add_roots=sorted({d["rootControlId"] for d in differences if d["newPathIntroduced"]})
            lost_roots=sorted({d["rootControlId"] for d in differences if d["oldPathLost"]})
            if p["changeType"]=="edge_add":
                require(not lost_roots,"graph change: addition removed reachability")
            if p["changeType"]=="edge_remove":
                require(not add_roots,"graph change: removal created reachability")
            if p["changeType"]=="owner_change":
                require(not differences and owners!=owner_map,
                        "graph change: owner change cannot modify edges")
        kinds=(
            "rejected_invalid_candidate" if candidate is None else
            "owner_governance_violation" if owner_violated else
            "reachability_changed" if any(d["newPathIntroduced"] or d["oldPathLost"]
                                          for d in differences) else
            "path_metrics_changed_only" if differences else
            "no_graph_metric_change"
        )
        edge_diff={
            "addedEdges":([] if candidate is None else [
                {"sourceId":a,"targetId":b} for a,b in
                sorted(set((u,v) for v,ps in candidate.items() for u in ps)
                       -set(EDGE_LIST))]),
            "removedEdges":([] if candidate is None else [
                {"sourceId":a,"targetId":b} for a,b in
                sorted(set(EDGE_LIST)-
                       set((u,v) for v,ps in candidate.items() for u in ps))]),
            "ownerDifference":(
                {"controlId":p["controlId"],"oldOwner":owner_map[p["controlId"]],
                 "proposedOwner":p["newOwner"],"verifiedNewOwner":False}
                if owner_violated else None),
        }
        results.append({
            "proposalId":p["proposalId"],"changeType":p["changeType"],
            "rationale":p["rationale"],
            "syntheticProposal":True,
            "candidateDagValid":candidate is not None,
            "candidateContractValid":valid,
            "validationReason":validation,
            "impactClassification":kinds,
            "edgeDiff":edge_diff,
            "graphNodeCount":13,
            "canonicalEdgeCount":17,
            "candidateEdgeCount":sum(len(x) for x in candidate.values()) if candidate is not None else None,
            "reachabilityImpact":{
                "changedRootTargetPairs":differences,
                "changedPairCount":len(differences),
                "introducedPairs":sum(d["newPathIntroduced"] for d in differences),
                "lostPairs":sum(d["oldPathLost"] for d in differences),
                "rootsWithNewReachability":add_roots,
                "rootsWithLostReachability":lost_roots,
                "allEffectsDocumentary":True,
            },
            "coverageRegression":{
                "referenceScenarioCount":100,
                "comparableScenarioCount":len(impacts),
                "affectedScenarios":[x for x in impacts if x["changedMetricControlIds"]],
                "unchangedScenarioCount":(100-sum(bool(x["changedMetricControlIds"]) for x in impacts) if candidate is not None else None),
                "allOneHundredScenariosCompared":len(impacts)==100,
                "realOutcomesMeasured":False,
            },
            "reviewerAssignmentRequirement":{
                "areas":list(AREAS),
                "individualReviewersAuthenticated":False,
                "independentTechnicalApprovalVerified":False,
                "oemEffectivityVerified":False,
                "legalAndDataReviewVerified":False,
                "signedChangeAcceptance":False,
            },
            "changeAdjudication":{
                "decision":"veto_no_merge",
                "reason":"hypothetical_change_requires_external_review",
                "oldGraphModified":False,
                "proposalAppliedToMain":False,
                "realPilotAuthorized":False,
                "mayWriteSap":False,
                "mayModifyEcm":False,
                "mayCreateWorkOrder":False,
                "mayOrderParts":False,
                "mayReleaseEquipment":False,
            },
        })
    return {
        "schema":"maintenance-superinteligence.graph-change-review-report.v1",
        "version":"1.0.0",
        "mode":"comparison_only_not_change_authorization",
        "fixtureSha256":sha(spec),
        "sourceCoverageSha256":sha(coverage),
        "sourceGoNoGoSha256":sha(gng),
        "canonicalDagSha256":sha({k:list(v) for k,v in original.items()}),
        "sourceOracleScenarioCount":100,
        "baselineControlCount":13,
        "baselineEdgeCount":17,
        "proposalCount":len(results),
        "proposals":results,
        "allProposalsVetoed":True,
        "realChangesCommitted":0,
        "verifiedHumanReviewCount":0,
        "realMachineFailureProbabilityCalculated":False,
        "operationalAuthority":{
            "mayWriteSap":False,"mayModifyEcm":False,
            "mayCreateWorkOrder":False,"mayOrderParts":False,
            "mayReleaseEquipment":False,"mayAuthorizePrivatePilot":False,
        },
        "decision":"no_go",
    }

def verify_report(report,spec,coverage,gng):
    require(report==build_report(spec,coverage,gng),
            "graph change: forged diff, witness, owner, proof or decision")
    return report

def render_html(report):
    require(report.get("schema")=="maintenance-superinteligence.graph-change-review-report.v1"
            and report.get("decision")=="no_go"
            and report.get("proposalCount")==10
            and report.get("baselineControlCount")==13
            and report.get("baselineEdgeCount")==17
            and report.get("sourceOracleScenarioCount")==100
            and report.get("allProposalsVetoed") is True
            and report.get("realChangesCommitted")==0
            and report.get("verifiedHumanReviewCount")==0
            and report.get("realMachineFailureProbabilityCalculated") is False
            and all(x is False for x in report.get("operationalAuthority",{}).values())
            and len(report.get("proposals",[]))==10
            and all(p.get("changeAdjudication",{}).get("decision")=="veto_no_merge"
                    and p.get("changeAdjudication",{}).get("proposalAppliedToMain") is False
                    and p.get("reachabilityImpact",{}).get("allEffectsDocumentary") is True
                    and p.get("reviewerAssignmentRequirement",{}).get("signedChangeAcceptance") is False
                    and p.get("coverageRegression",{}).get("referenceScenarioCount")==100
                    for p in report["proposals"]),
            "graph change HTML: untrusted review or operational authority")
    e=lambda x:escape(str(x),quote=True)
    cards=[]
    for p in report["proposals"]:
        edges=p["edgeDiff"]
        impacts=p["reachabilityImpact"]
        scenario=p["coverageRegression"]
        pairs="".join("<li>"+e(x["rootControlId"])+" → "+e(x["targetControlId"])
                      +" — caminhos "+e(x["oldPossiblePathCount"])+" → "
                      +e(x["newPossiblePathCount"])+
                      ", distância "+e(x["oldMinimumSteps"])+" → "
                      +e(x["newMinimumSteps"])+"</li>"
                      for x in impacts["changedRootTargetPairs"][:12])
        cards.append("<section><h2>"+e(p["proposalId"])+" — "
                     +e(p["impactClassification"])+"</h2><p>"
                     +e(p["rationale"])+"</p><p>Arestas adicionadas: "
                     +e(len(edges["addedEdges"]))+"; removidas: "
                     +e(len(edges["removedEdges"]))+"; pares alterados: "
                     +e(impacts["changedPairCount"])+
                     "; casos com métricas diferentes: "
                     +e(len(scenario["affectedScenarios"]))+"</p>"
                     "<details><summary>Primeiros 12 pares afetados</summary><ul>"
                     +pairs+"</ul></details><p class='stop'>VETO. Sem aprovação"
                     " humana autenticada; não modificar grafo, SAP ou equipamento.</p>"
                     "</section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            + "form-action &apos;none&apos;" + '"><title>Diff de grafo — NO GO</title>'
            '<style>body{font:15px system-ui,sans-serif;max-width:1050px;'
            'margin:2rem auto;padding:1rem;color:#222;background:#fafafa}'
            'section{border:1px solid #ddd;background:white;padding:1rem;margin:1rem 0}'
            '.stop{border-left:5px solid #a22;background:#fff0f0;padding:.8rem}</style>'
            '</head><body><h1>Propostas fictícias de mudança de grafo — NO GO</h1>'
            '<p class="stop">Dez propostas rejeitadas. Alcance documental não comprova'
            ' falha mecânica, efetividade OEM ou autorização para qualquer operação.</p>'
            + "".join(cards)
            + '<footer>HTML offline; sem JavaScript, formulários, rede ou login.'
              '</footer></body></html>\n')

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",required=True,type=Path)
    parser.add_argument("--gng",required=True,type=Path)
    parser.add_argument("--sequence",required=True,type=Path)
    parser.add_argument("--contradictions",required=True,type=Path)
    parser.add_argument("--coverage",required=True,type=Path)
    parser.add_argument("--spec",type=Path,default=SPEC_PATH)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        deps=load_dependencies(snapshot)
        cases=build_collection(json.loads(CASE_SPEC.read_text(encoding="utf-8")),deps,snapshot)
        notes=build_notifications(json.loads(NOTE_SPEC.read_text(encoding="utf-8")),
                                  cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,
                              json.loads(RUBRIC_PATH.read_text(encoding="utf-8")),
                              json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
        ed=build_edit(json.loads(EDIT_SPEC.read_text(encoding="utf-8")),quality,notes)
        ready=build_readiness(json.loads(READY_SPEC.read_text(encoding="utf-8")),ed)
        gng=build_gng(json.loads(GNG_PACKAGE.read_text(encoding="utf-8")),ready)
        seq=build_seq(json.loads(SEQ_SPEC.read_text(encoding="utf-8")),gng)
        conf=build_conf(json.loads(CONF_SPEC.read_text(encoding="utf-8")),seq,gng)
        cov=build_coverage(json.loads(COV_SPEC.read_text(encoding="utf-8")),conf,seq,gng)
        supplied=[json.loads(x.read_text(encoding="utf-8"))
                  for x in (args.gng,args.sequence,args.contradictions,args.coverage)]
        require(supplied==[gng,seq,conf,cov],
                "graph change: source corpus or 100-case oracle adulterated")
        spec=json.loads(args.spec.read_text(encoding="utf-8"))
        require(spec==json.loads(SPEC_PATH.read_text(encoding="utf-8")),
                "graph change: proposals must match reviewed public fixture")
        result=build_report(spec,cov,gng)
        payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(payload,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(result),encoding="utf-8")
        print(payload)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed","reason":str(exc),
                          "mayWriteSap":False},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
