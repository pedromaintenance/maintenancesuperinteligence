"""Ciclo 23: independent reachability oracle, readable dependency witnesses.

All paths are documentary relationships on a fixed PUBLIC synthetic graph.
No machinery, physical failure, OEM effectivity or real human review inferred.
"""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
import sys

from connectors.fmea_public import ImportRejected, require, load_lock, validate_snapshot
from evidence.ledger import sha
from methods.library import ROOT
from casefiles.integrated import FIXTURE_PATH as CASE_FIXTURE, load_dependencies, build_collection
from notifications.drafts import SPEC_PATH as NOTE_SPEC, build_notifications
from quality.notifications import RUBRIC_PATH, ORACLE_PATH, build_report as build_quality
from editorial.review_protocol import FIXTURE_PATH as EDIT_FIXTURE, build_report as build_editorial
from pilot.readiness import FIXTURE_PATH as READY_FIXTURE, build_report as build_readiness
from pilot.go_nogo import PACKAGE_PATH as GNG_PACKAGE, DEPENDENCIES, build_report as build_gng
from pilot.evidence_sequence import SPEC_PATH as SEQ_SPEC, build_report as build_sequence
from pilot.evidence_contradictions import (
    FIXTURE_PATH as CONFLICT_FIXTURE, build_report as build_conflicts,
    SCENARIO_DEFS, descendant_cascade, validate_fixture as validate_conflicts
)

SPEC_PATH=ROOT/"pilot/reopen-coverage.v1.json"
IDS=tuple(DEPENDENCIES)
EDGE_LIST=tuple((p,t) for t,ps in DEPENDENCIES.items() for p in ps)
TRIGGERS=(("revoked_identity",("identity-proof",)),
          ("oem_revision_changed",("oem-effectivity",)),
          ("machine_configuration_changed",("equipment-configuration",)))
KINDS=("single_root","root_pair","version_identity_trigger","conflict_pair")
MUTATIONS=(("edge_removed","competence","two-independent-reviews"),
           ("edge_reversed","trusted-audit","operational-firewall"),
           ("edge_added","oem-effectivity","identity-proof"),
           ("threat_removed","duplicate-principal",None),
           ("closure_forged","identity-proof","operational-firewall"))
STAKEHOLDERS=("IT","InformationSecurity","Engineering","Legal",
              "MaintenanceManagement")
SPEC_KEYS={"schema","version","mode","sourceGoNoGo","sourceConflict",
           "oracleAlgorithm","graphControlIds","canonicalDependencies",
           "graphEdges","cases","mutations","crossReview","policy"}
CASE_KEYS={"caseId","kind","rootControlIds","reason",
           "expectedAffectedControlIds","expectedUnaffectedControlIds",
           "expectedPathMetrics","fieldObserved","externalApproval"}
MUT_KEYS={"mutationCaseId","mutationId","sourceId","targetId",
          "expectedResult","fieldObservation"}
REVIEW_KEYS={"owner","controlIds","authenticHumanReview","engineeringAcceptance"}
POLICY_KEYS={"allClaimsSynthetic","realEvidenceAvailable","fieldFaultConfirmed",
             "expertApprovalVerified","mayWriteSap","mayAlterEcm",
             "mayCreateWorkOrder","mayReleaseEquipment",
             "mayAuthorizePrivatePilot","decision"}

def exact(value,keys,where):
    require(isinstance(value,dict) and set(value)==keys,
            f"coverage: unexpected or missing {where}")
    return value

def _roots_for_cases(conflicts):
    require([x["scenarioId"] for x in conflicts["scenarios"]]
            ==[f"SIM-CONFLICT-{i:02}" for i in range(1,7)],
            "coverage: conflict scenario IDs missing")
    return [
        *(("single_root",[x],"synthetic_single_control_reopen") for x in IDS),
        *(("root_pair",[IDS[i],IDS[j]],"synthetic_pair_reopen")
          for i in range(len(IDS)) for j in range(i+1,len(IDS))),
        *(("version_identity_trigger",list(x),label) for label,x in TRIGGERS),
        *(("conflict_pair",c["sourceControls"],c["conflictMechanism"])
          for c in conflicts["scenarios"]),
    ]

def independent_oracle(roots,pred):
    """Independent all-pairs Warshall + dag path recurrence.

    DOES NOT call descendant_cascade, topological_sequence or the report's DFS.
    """
    ids=list(pred)
    reach={u:{v:u==v for v in ids} for u in ids}
    dist={u:{v:(0 if u==v else 10**6) for v in ids} for u in ids}
    for v in ids:
        for u in pred[v]:
            reach[u][v]=True
            dist[u][v]=1
    for k in ids:
        for u in ids:
            for v in ids:
                if reach[u][k] and reach[k][v]:
                    reach[u][v]=True
                dist[u][v]=min(dist[u][v],dist[u][k]+dist[k][v])
    def ways(src,target,memo):
        if target==src:
            return 1
        if target in memo:
            return memo[target]
        memo[target]=sum(ways(src,p,memo) for p in pred[target])
        return memo[target]
    affected=[v for v in ids if any(reach[r][v] for r in roots)]
    metrics={
        v:{
            "minimumSteps":min(dist[r][v] for r in roots),
            "possiblePathCount":sum(ways(r,v,{}) for r in roots if reach[r][v]),
        } for v in affected
    }
    return affected,[v for v in ids if v not in affected],metrics

def _is_acyclic(pred):
    ids=set(pred)
    state={}
    def visit(v):
        if state.get(v)==1: return False
        if state.get(v)==2: return True
        state[v]=1
        for p in pred[v]:
            if p not in ids or not visit(p): return False
        state[v]=2
        return True
    return all(visit(v) for v in pred)

def validate_spec(spec,contradictions,sequence,gng):
    f=exact(spec,SPEC_KEYS,"coverage spec")
    require(f["schema"]=="maintenance-superinteligence.reopen-coverage-spec.v1"
            and f["version"]=="1.0.0"
            and f["mode"]=="synthetic_graph_structural_regression_only"
            and f["sourceGoNoGo"]=="pilot/go-nogo-package.v1.json"
            and f["sourceConflict"]=="pilot/evidence-contradictions.v1.json"
            and f["oracleAlgorithm"]=="floyd_warshall_static_fixture",
            "coverage: invalid source or claimed oracle")
    policy=exact(f["policy"],POLICY_KEYS,"no-go policy")
    require(policy["allClaimsSynthetic"] is True
            and policy["decision"]=="no_go"
            and all(policy[k] is False for k in POLICY_KEYS
                    if k not in {"allClaimsSynthetic","decision"}),
            "coverage: real engineering or operational approval forged")
    require(f["graphControlIds"]==list(IDS)
            and f["canonicalDependencies"]=={k:list(v) for k,v in DEPENDENCIES.items()}
            and f["graphEdges"]==[{"source":a,"target":b} for a,b in EDGE_LIST]
            and _is_acyclic(DEPENDENCIES)
            and len(EDGE_LIST)==17,
            "coverage: changed canonical dependency/edge orientation")
    require(contradictions["schema"]
            =="maintenance-superinteligence.evidence-contradiction-report.v1"
            and contradictions["decision"]=="no_go"
            and contradictions["sourceControlCount"]==13
            and contradictions["sourceDependencyCount"]==17
            and contradictions["scenarioCount"]==6
            and contradictions["verifiedPhysicalFaults"]==0
            and contradictions["externalProofsVerified"]==0
            and contradictions["independentRealReviewsCompleted"]==0
            and contradictions["canReleaseEquipment"] is False
            and sequence["schema"]=="maintenance-superinteligence.evidence-sequencing-report.v1"
            and sequence["decision"]=="no_go"
            and sequence["verifiedEvidenceCount"]==0
            and gng["schema"]=="maintenance-superinteligence.go-nogo-report.v1"
            and gng["decision"]=="no_go"
            and gng["verifiedSignoffs"]==0
            and gng["approvalDependencies"]==[
                {"controlId":k,"predecessors":list(DEPENDENCIES[k]),
                 "allPrerequisitesVerified":False,"permissionToProceed":False}
                for k in IDS],
            "coverage: source graph, review or NO GO boundaries compromised")
    require(isinstance(f["cases"],list) and len(f["cases"])==100,
            "coverage: require all 100 single/pair/trigger/conflict cases")
    expected=_roots_for_cases(contradictions)
    require(len(expected)==100,
            "coverage: incorrect case enumeration")
    for i,(c,(kind,roots,reason)) in enumerate(zip(f["cases"],expected),1):
        exact(c,CASE_KEYS,"case")
        affected,unaffected,metrics=independent_oracle(roots,DEPENDENCIES)
        require(c["caseId"]==f"SIM-RPATH-{i:03}"
                and c["kind"]==kind and c["rootControlIds"]==roots
                and c["reason"]==reason
                and c["expectedAffectedControlIds"]==affected
                and c["expectedUnaffectedControlIds"]==unaffected
                and c["expectedPathMetrics"]==metrics
                and c["fieldObserved"] is False
                and c["externalApproval"] is False,
                "coverage: independent oracle, root, edge or claim altered")
    require(isinstance(f["mutations"],list) and len(f["mutations"])==5,
            "coverage: all five graph mutation fixtures required")
    for i,(m,expected_mut) in enumerate(zip(f["mutations"],MUTATIONS),1):
        exact(m,MUT_KEYS,"mutation")
        require(m["mutationCaseId"]==f"SIM-MUT-{i:02}"
                and (m["mutationId"],m["sourceId"],m["targetId"])==expected_mut
                and m["expectedResult"]=="rejected_noncanonical"
                and m["fieldObservation"] is False,
                "coverage: suppressed or invented mutation outcome")
    require(isinstance(f["crossReview"],list) and len(f["crossReview"])==5
            and [r.get("owner") for r in f["crossReview"]]==list(STAKEHOLDERS),
            "coverage: five responsibility areas required")
    sources={c["controlId"]:c["owner"] for c in json.loads(
        (ROOT/"pilot/go-nogo-package.v1.json").read_text(encoding="utf-8")
    )["controlPlan"]}
    for r in f["crossReview"]:
        exact(r,REVIEW_KEYS,"cross review")
        require(r["controlIds"]==[cid for cid in IDS if sources[cid]==r["owner"]]
                and r["authenticHumanReview"] is False
                and r["engineeringAcceptance"] is False,
                "coverage: cross-review scope or real decision forged")
    return f

def _enumerate_simple_paths(roots,pred,target):
    """DFS forward over documented edges; different from matrix oracle."""
    children={u:[] for u in pred}
    for v,parents in pred.items():
        for u in parents: children[u].append(v)
    paths=[]
    def walk(node,path):
        if node==target:
            paths.append(list(path))
            return
        for child in children[node]:
            if child not in path:
                walk(child,path+[child])
    for r in roots: walk(r,[r])
    idx={k:i for i,k in enumerate(pred)}
    paths.sort(key=lambda path:(len(path),tuple(idx[x] for x in path)))
    return paths

def _mutation_checks():
    base=set(EDGE_LIST)
    out=[]
    for i,(kind,a,b) in enumerate(MUTATIONS,1):
        if kind=="edge_removed":
            changed=base-{(a,b)}
            detected=(a,b) in base and changed!=base
        elif kind=="edge_reversed":
            changed=(base-{(a,b)})|{(b,a)}
            detected=(a,b) in base and changed!=base
        elif kind=="edge_added":
            changed=base|{(a,b)}
            detected=(a,b) not in base and changed!=base
        elif kind=="threat_removed":
            detected=a in [t["threatId"] for t in json.loads(
                (ROOT/"pilot/readiness-fixture.v1.json").read_text(encoding="utf-8")
            )["threats"]]
        else: # Independently check that fabricated shortcut skips a prerequisite.
            detected=(a,b) not in base and (a,b) not in {
                (path[i],path[i+1])
                for path in _enumerate_simple_paths([a],DEPENDENCIES,b)
                for i in range(len(path)-1)
            }
        require(detected,"coverage: mutation fail-closed witness not detected")
        out.append({
            "mutationCaseId":f"SIM-MUT-{i:02}",
            "mutationType":kind,"canonicalGraphUnchanged":True,
            "mutatedInputRejected":True,"threatListPreserved":True,
            "operationalAuthorityGranted":False,
            "realWorldDefectObserved":False,
        })
    return out

def build_report(spec,contradictions,sequence,gng):
    validate_spec(spec,contradictions,sequence,gng)
    reports=[]
    original=validate_conflicts(
        json.loads(CONFLICT_FIXTURE.read_text(encoding="utf-8")),sequence,gng)
    for c in spec["cases"]:
        roots=c["rootControlIds"]
        closure=descendant_cascade(roots,original)
        require(closure==[k for k in original["order"]
                          if k in set(c["expectedAffectedControlIds"])],
                "coverage: closure differs from independent Floyd oracle")
        affected=[]
        for target in c["expectedAffectedControlIds"]:
            paths=_enumerate_simple_paths(roots,DEPENDENCIES,target)
            stat=c["expectedPathMetrics"][target]
            require(len(paths)==stat["possiblePathCount"]
                    and len(paths[0])-1==stat["minimumSteps"],
                    "coverage: paths, length or redundancy do not match independent oracle")
            p=paths[0]
            affected.append({
                "targetControlId":target,
                "rootControlId":p[0],
                "rootReason":c["reason"],
                "selectedPath":p,
                "stepCount":len(p)-1,
                "explanationSteps":[
                    {"step":i+1,"upstreamControlId":p[i],
                     "downstreamControlId":p[i+1],
                     "because":"downstream_documentary_control_depends_on_upstream",
                     "physicalMechanismClaimed":False}
                    for i in range(len(p)-1)],
                "alternativePathCount":len(paths)-1,
                "alternativePathWitness":paths[1] if len(paths)>1 else None,
                "evidenceActuallyVerified":False,
                "physicalFaultConfirmed":False,
                "mayAuthorizeMaintenance":False,
            })
        unreachable=[{
            "targetControlId":target,
            "testedRootControlIds":list(roots),
            "reason":"no_directed_documentary_dependency_path",
            "noPathWitness":"independent_floyd_warshall_and_dfs_agree",
            "physicalSafetyEstablished":False,
            "maySkipExternalReview":False,
        } for target in c["expectedUnaffectedControlIds"]]
        reports.append({
            "caseId":c["caseId"],"caseKind":c["kind"],
            "syntheticTrigger":c["reason"],
            "rootControlIds":list(roots),
            "affectedControlIds":list(c["expectedAffectedControlIds"]),
            "unaffectedControlIds":list(c["expectedUnaffectedControlIds"]),
            "pathExplanations":affected,
            "unreachableControlWitnesses":unreachable,
            "affectedCount":len(affected),
            "unaffectedCount":len(unreachable),
            "coveredControlCount":len(affected)+len(unreachable),
            "redundantTargetCount":sum(x["alternativePathCount"]>0 for x in affected),
            "allPathsDocumentary":True,
            "realFaultDetected":False,"pilotApprovalGranted":False,
            "decision":"no_go",
        })
    source_controls={x["controlId"]:x["owner"] for x in
        json.loads((ROOT/"pilot/go-nogo-package.v1.json").read_text(encoding="utf-8"))["controlPlan"]}
    owners=[{
        "owner":owner,
        "controlsOwned":[k for k in IDS if source_controls[k]==owner],
        "coverageFromSingleRootCases":[
            x["caseId"] for x in reports[:13]
            if any(y in x["affectedControlIds"] for y in IDS if source_controls[y]==owner)
        ],
        "externalTechnicalReviewPerformed":False,
        "authenticatedSignoffReceived":False,
        "mayReleaseEquipment":False,
    } for owner in STAKEHOLDERS]
    return {
        "schema":"maintenance-superinteligence.reopen-coverage-report.v1",
        "version":"1.0.0",
        "mode":"public_structural_reopen_coverage_only",
        "specSha256":sha(spec),
        "sourceContradictionsSha256":sha(contradictions),
        "sourceSequenceSha256":sha(sequence),
        "sourceGoNoGoSha256":sha(gng),
        "sourceFmeaSnapshotSha256":sequence["sourceFmeaSnapshotSha256"],
        "controlCount":13,"edgeCount":17,
        "scenarioCount":100,
        "singleRootCount":13,"pairCount":78,"triggerCount":3,"conflictCount":6,
        "coverageCases":reports,
        "graphMutationChecks":_mutation_checks(),
        "graphMutationCount":5,
        "crossFunctionalReview":owners,
        "unverifiedEvidenceCount":13,
        "verifiedExternalHumanReviews":0,
        "physicalFailuresVerified":0,
        "realPilotApproved":False,
        "mayTransmitSap":False,
        "mayModifyEcm":False,
        "mayCreateWorkOrder":False,
        "mayReleaseEquipment":False,
        "decision":"no_go",
        "structuralCoverageMeaning":"complete_for_fixed_public_fixture_not_real_world",
    }

def verify_report(report,spec,contradictions,sequence,gng):
    require(report==build_report(spec,contradictions,sequence,gng),
            "coverage: altered path, witness, threat, approval or metric")
    return report

def render_html(report):
    require(report.get("schema")
            =="maintenance-superinteligence.reopen-coverage-report.v1"
            and report.get("decision")=="no_go"
            and report.get("controlCount")==13 and report.get("edgeCount")==17
            and report.get("scenarioCount")==100
            and report.get("graphMutationCount")==5
            and report.get("unverifiedEvidenceCount")==13
            and report.get("verifiedExternalHumanReviews")==0
            and report.get("physicalFailuresVerified")==0
            and all(report.get(k) is False for k in (
                "realPilotApproved","mayTransmitSap","mayModifyEcm",
                "mayCreateWorkOrder","mayReleaseEquipment"))
            and len(report.get("coverageCases",[]))==100
            and len(report.get("crossFunctionalReview",[]))==5
            and all(c.get("decision")=="no_go"
                    and c.get("allPathsDocumentary") is True
                    and c.get("realFaultDetected") is False
                    and c.get("pilotApprovalGranted") is False
                    and c.get("coveredControlCount")==13
                    and all(x.get("physicalFaultConfirmed") is False
                            and x.get("evidenceActuallyVerified") is False
                            and x.get("mayAuthorizeMaintenance") is False
                            for x in c.get("pathExplanations",[]))
                    and all(x.get("physicalSafetyEstablished") is False
                            and x.get("maySkipExternalReview") is False
                            for x in c.get("unreachableControlWitnesses",[]))
                    for c in report["coverageCases"]),
            "coverage HTML: forged structural evidence or operational approval")
    e=lambda v:escape(str(v),quote=True)
    cards=[]
    # Navigation highlights 13 individual roots and all six scenario pairs.
    selected=[c for c in report["coverageCases"] if c["caseKind"] in (
        "single_root","conflict_pair")]
    for c in selected:
        examples=c["pathExplanations"][:5]
        bullet="".join("<li>"+e(" → ".join(x["selectedPath"]))
                       +(" (mais "+e(x["alternativePathCount"])+
                         " caminho(s))" if x["alternativePathCount"] else "")
                       +"</li>" for x in examples)
        cards.append("<details><summary>"+e(c["caseId"])+" — "+
                     e(", ".join(c["rootControlIds"]))+" | "+
                     e(c["affectedCount"])+"/13 controles afetados</summary>"
                     "<p>Justificativa: dependência documental sintética; NÃO é"
                     " mecanismo de falha física, medição ou autorização.</p>"
                     "<ul>"+bullet+"</ul><p>Controles sem caminho desde estas raízes: "
                     +e(", ".join(c["unaffectedControlIds"]))+"</p></details>")
    reviewers="".join("<li>"+e(c["owner"])+": "+
                      e(", ".join(c["controlsOwned"]))+" — revisão real pendente</li>"
                      for c in report["crossFunctionalReview"])
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src '
        +"&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
        +"form-action &apos;none&apos;"+'"><title>Cobertura de reabertura</title>'
        '<style>body{font:15px system-ui,sans-serif;max-width:1150px;margin:2rem auto;'
        'padding:1rem;color:#222;background:#fafafa}details{padding:.8rem;margin:.7rem 0;'
        'border:1px solid #ddd;background:#fff}summary{cursor:pointer;font-weight:600}'
        '.warn{border-left:5px solid #a22;padding:1rem;background:#fff0f0}</style>'
        '</head><body><h1>Cobertura estrutural — 100 cenários sintéticos</h1>'
        '<p class="warn">NO GO. Caminho no grafo não é causalidade mecânica,'
        ' avaliação de risco de campo, homologação OEM ou permissão SAP/ECM.</p>'
        '<p>13 raízes individuais, 78 pares, 3 mudanças de contexto e 6 conflitos;'
        ' 5 mutações estruturais rejeitadas no exercício.</p>'
        '<h2>Explicações e raízes principais</h2>'+"".join(cards)
        +'<h2>Matriz de revisão cruzada — pendente</h2><ul>'+reviewers+'</ul>'
        '<footer>Visualização estática sem JS, rede, login ou formulários.</footer>'
        '</body></html>\n')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--sequence",type=Path,required=True)
    p.add_argument("--gng",type=Path,required=True)
    p.add_argument("--contradictions",type=Path,required=True)
    p.add_argument("--spec",type=Path,default=SPEC_PATH)
    p.add_argument("--output",type=Path)
    p.add_argument("--html",type=Path)
    args=p.parse_args(argv)
    try:
        snapshot=validate_snapshot(args.snapshot.read_bytes(),load_lock())
        dep=load_dependencies(snapshot)
        cases=build_collection(json.loads(CASE_FIXTURE.read_text(encoding="utf-8")),dep,snapshot)
        notes=build_notifications(json.loads(NOTE_SPEC.read_text(encoding="utf-8")),
                                  cases["cases"],cases["investigationTrees"])
        quality=build_quality(notes,cases,json.loads(RUBRIC_PATH.read_text(encoding="utf-8")),
                              json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
        ed=build_editorial(json.loads(EDIT_FIXTURE.read_text(encoding="utf-8")),quality,notes)
        ready=build_readiness(json.loads(READY_FIXTURE.read_text(encoding="utf-8")),ed)
        gng=build_gng(json.loads(GNG_PACKAGE.read_text(encoding="utf-8")),ready)
        seq=build_sequence(json.loads(SEQ_SPEC.read_text(encoding="utf-8")),gng)
        conf=build_conflicts(json.loads(CONFLICT_FIXTURE.read_text(encoding="utf-8")),seq,gng)
        supplied=[json.loads(x.read_text(encoding="utf-8"))
                  for x in (args.gng,args.sequence,args.contradictions)]
        spec=json.loads(args.spec.read_text(encoding="utf-8"))
        require(supplied==[gng,seq,conf]
                and spec==json.loads(SPEC_PATH.read_text(encoding="utf-8")),
                "coverage: untrusted or modified upstream report/spec")
        result=build_report(spec,conf,seq,gng)
        serialized=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(serialized,encoding="utf-8")
        if args.html:
            args.html.parent.mkdir(parents=True,exist_ok=True)
            args.html.write_text(render_html(result),encoding="utf-8")
        print(serialized)
        return 0
    except (ImportRejected,ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"result":"rejected_fail_closed",
                          "reason":str(exc),"mayTransmitSap":False},
                         ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
