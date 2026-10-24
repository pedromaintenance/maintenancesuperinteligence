"""Educational investigation paths only: never a field diagnosis or permission."""
from pathlib import Path
from html import escape
import json
from connectors.fmea_public import require
from evidence.ledger import sha
from methods.library import ROOT

SPEC_PATH = ROOT / "trees/spec.v1.json"
IDS = ["SIM-TECH-FD-01","SIM-TECH-HYD-01",
       "SIM-TECH-ECM-LOG-01","SIM-TECH-ECM-ACT-01"]
STATES = {"not_measured","contradicted","inconclusive"}
PROOFS = [
    "OEM publication, revision, equipment arrangement and configuration",
    "Safe approved method, isolation and competent personnel",
    "Comparable and traceable physical evidence",
    "Resolution of missing or contradictory context",
    "Independent qualified human engineering review",
]

def validate_spec(spec, cases):
    require(set(spec) == {"schema","version","mode","evidenceSource",
                          "oracleSource","authorizedForOperations",
                          "fieldEvidenceAvailable","trees"}
            and spec["schema"] == "maintenance-superinteligence.investigation-tree-spec.v1"
            and spec["version"] == "1.0.0"
            and spec["mode"] == "public_synthetic_only"
            and spec["evidenceSource"] == "evidence/qualitative-discrimination.v1.json"
            and spec["oracleSource"] == "benchmarks/qualitative-oracle.v1.json"
            and spec["authorizedForOperations"] is False
            and spec["fieldEvidenceAvailable"] is False,
            "tree: source or authority invalid")
    require([c["caseFileId"] for c in cases] == IDS
            and len(spec["trees"]) == 4,
            "tree: four fixed synthetic cases required")
    result={}
    for i, row in enumerate(spec["trees"]):
        c=cases[i]
        pairs=c["qualitativeEvidence"]["comparisons"]
        root=c["selectedQuestion"]["pairId"]
        current=next(p["currentEvidenceState"] for p in pairs if p["pairId"] == root)
        require(set(row)=={"caseFileId","rootPairId","currentContextState",
                           "pairCount","terminalState","canConfirmRootCause",
                           "canReleaseMachine"}
                and row["caseFileId"] == IDS[i]
                and row["rootPairId"] == root
                and row["currentContextState"] == current
                and current in STATES
                and type(row["pairCount"]) is int
                and row["pairCount"] == len(pairs)
                and row["terminalState"] == "abstain_pending_verified_evidence"
                and row["canConfirmRootCause"] is False
                and row["canReleaseMachine"] is False,
                "tree: changed branch, root or declared approval")
        result[IDS[i]]=row
    return result

def build_tree(case, entry):
    comparisons=case["qualitativeEvidence"]["comparisons"]
    hypotheses=case["hypotheses"]
    require(case["confirmedComponent"] is None
            and case["approvedForOperationalUse"] is False
            and case["qualitativeEvidence"]["hypothesesExcluded"] == 0
            and all(x["status"] == "open_not_confirmed"
                    and x["probability"] is None for x in hypotheses),
            "tree: cannot confirm or rank actual faults")
    nodes=[]
    trace=[]
    for p in comparisons:
        pid=p["pairId"]
        require(p["currentEvidenceState"] in STATES
                and p["fieldResult"] is None
                and p["observedPhysicalEvidence"] is False
                and p["cannotDismissEitherHypothesis"] is True
                and len(p["conditionalObservations"]) == 3
                and len(p["alternativeExplanations"]) == 2
                and all(o["hasBeenObserved"] is False for o in p["conditionalObservations"]),
                "tree: physical evidence or automated exclusion disallowed")
        branches=[]
        for i,o in enumerate(p["conditionalObservations"]):
            require(o["observationNature"] == "counterfactual_not_observed"
                    and o["mayExcludeHypothesis"] is False,
                    "tree: hypothetical observation promoted")
            branches.append({
                "branchId":pid+"-HYP-"+str(i+1),
                "branchNature":"hypothetical_unobserved",
                "interpretation":o["conditionalReading"],
                "effectFirstIfObserved":o["effectOnFirstIfObserved"],
                "effectSecondIfObserved":o["effectOnSecondIfObserved"],
                "observed":False,
                "hypothesesExcluded":0,
                "toNodeId":pid+"-REVIEW",
            })
        state=p["currentEvidenceState"]
        nodes.append({
            "nodeId":pid, "nodeType":"investigation_question",
            "pairId":pid, "hypothesisIds":p["hypothesisIds"],
            "question":next(m["question"] for m in case["methods"]
                            if m["pairId"] == pid),
            "methodIds":[m["methodId"] for m in p["methodPlanning"]],
            "publicSources":p["evidenceProvenance"]["generalSourceIds"],
            "counterexamples":[a["statement"] for a in p["alternativeExplanations"]],
            "evidenceGate":{"currentState":state,
                            "actualTransition":pid+"-REVIEW",
                            "doesNotTakeConditionalBranch":True,
                            "mayDiscardHypothesis":False},
            "conditionalBranches":branches,
            "reviewCheckpoint":{
                "nodeId":pid+"-REVIEW",
                "requiredProofs":PROOFS[:],
                "allProofsVerified":False,
                "humanReviewAuthenticated":False,
                "oemEffectivityVerified":False,
                "physicalMethodAuthorized":False,
                "decision":"abstain_pending_verified_evidence",
            },
            "testStatus":"not_performed",
            "mayExecute":False,
        })
        trace.append({
            "fromNodeId":pid,"toNodeId":pid+"-REVIEW",
            "contextState":state,
            "hypotheticalBranchesTaken":0,
            "reason":("reconcile_conflict" if state=="contradicted" else
                      "collect_missing_context" if state=="not_measured" else
                      "insufficient_discrimination"),
            "conclusion":"abstain_pending_verified_evidence",
        })
    return {
        "schema":"maintenance-superinteligence.investigation-tree.v1",
        "caseFileId":case["caseFileId"],
        "rootNodeId":entry["rootPairId"],
        "nodes":nodes, "decisionTrace":trace,
        "unresolvedHypothesisSet":{
            "hypothesisIds":[h["id"] for h in hypotheses],
            "allOpen":True, "hypothesesExcluded":0,
            "rootCauseConfirmed":False,
        },
        "traceSelectedRoot":next(t for t in trace if t["fromNodeId"]==entry["rootPairId"]),
        "fieldAccuracyMeasured":False,
        "testsExecuted":0,
        "mayCreateWorkOrder":False,
        "mayModifyECM":False,
        "mayReleaseEquipment":False,
        "decision":"abstain_pending_verified_evidence",
    }

def build_trees(spec,cases):
    valid=validate_spec(spec,cases)
    trees=[build_tree(c, valid[c["caseFileId"]]) for c in cases]
    require(sum(len(t["nodes"]) for t in trees)==13,
            "tree: all comparison nodes required")
    return {"schema":"maintenance-superinteligence.investigation-tree-collection.v1",
            "version":"1.0.0",
            "specSha256":sha(spec),
            "treeCount":4,"nodeCount":13,"trees":trees,
            "physicalTestsExecuted":0,"hypothesesExcluded":0,
            "operationalAuthorization":False}

def verify_trees(value,spec,cases):
    require(value==build_trees(spec,cases),
            "tree: altered decision trace or forged operational authority")
    return value
