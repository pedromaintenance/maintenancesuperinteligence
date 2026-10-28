"""Cycle 32: pre-distribution QA gate for externally held-out cases.

Works on PRIVATE metadata outside the repository. A metadata audit is not field
validation, evidence authentication, or proof that a training set is complete.
"""
from __future__ import annotations
from collections import Counter
import re
import unicodedata
from benchmarks.heldout_study import validate_cases
from pilot.change_review_packets import digest, require

KNOWN = ("mechanics", "hydraulics", "electronics", "cooling")
ALL = KNOWN + ("unsupported",)
STATUSES = ("unverified","conflicting","stale","revoked","synthetic_complete")
SPLITS = ("train","dev","test")
ERRORS = ("lineage_cross_split","source_cross_split","evidence_cross_split",
          "narrative_exact_cross_split","narrative_near_cross_split",
          "duplicate_within_split","missing_split","missing_domain_test",
          "missing_status_test","missing_mechanism_test")
ITEM_KEYS = {"caseId","split","domain","narrative","caseDigest","lineage",
             "sourceGroup","evidenceRef","mechanismTag","documentaryStatus",
             "abstentionRequired","causeConfirmed"}
META_KEYS = {"schema","version","mode","independentReviewCompleted",
             "operationallyApproved","records"}
POLICY_KEYS = {"schema","version","splitMinimums","requiredTestDomains",
               "requiredTestStatuses","requiredTestMechanisms",
               "nearDuplicateThreshold","independentExpertEndorsed"}


def normalized_tokens(value):
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    return frozenset(re.findall(r"[a-z0-9]+",value))


def test_narrative(case):
    return case["symptom"]+" | "+" | ".join(case["observations"])


def record_digest(record):
    return digest({"caseId":record["caseId"],"narrative":record["narrative"]})


def case_digest(case):
    return digest({k:case[k] for k in ("caseId","domain","symptom","observations")})


def validate_policy(policy):
    require(isinstance(policy,dict) and set(policy)==POLICY_KEYS
            and policy["schema"]=="maintenance-superinteligence.private-quality-policy.v1"
            and policy["version"]=="1.0.0"
            and policy["independentExpertEndorsed"] is False,
            "private study quality policy has unverified authority")
    mins=policy["splitMinimums"]
    require(isinstance(mins,dict) and set(mins)==set(SPLITS)
            and type(mins["train"]) is int and mins["train"]>=1
            and type(mins["dev"]) is int and mins["dev"]>=1
            and type(mins["test"]) is int and mins["test"]>=2,
            "quality gate needs train/dev/test cohorts")
    domains=policy["requiredTestDomains"]
    statuses=policy["requiredTestStatuses"]
    mechanisms=policy["requiredTestMechanisms"]
    require(isinstance(domains,list) and domains
            and len(set(domains))==len(domains)
            and all(x in ALL for x in domains)
            and isinstance(statuses,list) and "unverified" in statuses
            and len(set(statuses))==len(statuses)
            and all(x in STATUSES for x in statuses)
            and isinstance(mechanisms,dict)
            and set(mechanisms).issubset(set(KNOWN))
            and all(isinstance(v,list) and v
                    and len(set(v))==len(v)
                    and all(isinstance(tag,str) and
                            re.fullmatch(r"[a-z][a-z0-9_]{2,63}",tag) for tag in v)
                    for v in mechanisms.values())
            and type(policy["nearDuplicateThreshold"]) is float
            and 0.75<=policy["nearDuplicateThreshold"]<=0.95,
            "invalid or weakened quality coverage policy")
    return policy


def validate_metadata(meta,source,policy):
    validate_policy(policy)
    cases=validate_cases(source)
    require(isinstance(meta,dict) and set(meta)==META_KEYS
            and meta["schema"]=="maintenance-superinteligence.private-quality-metadata.v1"
            and meta["version"]=="1.0.0"
            and meta["mode"]=="private_custodian_metadata"
            and meta["independentReviewCompleted"] is False
            and meta["operationallyApproved"] is False,
            "metadata claims real approval or wrong schema")
    rows=meta["records"]
    require(isinstance(rows,list) and 4<=len(rows)<=250,
            "invalid private corpus size")
    ids=set()
    for x in rows:
        require(isinstance(x,dict) and set(x)==ITEM_KEYS
                and isinstance(x["caseId"],str)
                and x["caseId"] not in ids,
                "duplicate or malformed metadata case")
        ids.add(x["caseId"])
        split=x["split"]
        require(split in SPLITS
                and re.fullmatch(("HLD-" if split=="test" else
                                  "TRN-" if split=="train" else "DEV-")+r"[0-9]{3}",
                                 x["caseId"])
                and x["domain"] in ALL
                and isinstance(x["narrative"],str)
                and 20<=len(x["narrative"])<=1200
                and len(normalized_tokens(x["narrative"]))>=5
                and x["documentaryStatus"] in STATUSES
                and isinstance(x["mechanismTag"],str)
                and re.fullmatch(r"[a-z][a-z0-9_]{2,63}",x["mechanismTag"])
                and isinstance(x["caseDigest"],str)
                and re.fullmatch(r"[a-f0-9]{64}",x["caseDigest"])
                and all(isinstance(x[f],str) and
                        re.fullmatch(r"[A-Z0-9-]{5,80}",x[f])
                        for f in ("lineage","sourceGroup","evidenceRef"))
                and x["abstentionRequired"] is True
                and x["causeConfirmed"] is False,
                "metadata has invalid values or claimed diagnosis")
        if split!="test":
            require(x["caseDigest"]==record_digest(x),
                    "train/dev narrative digest not consistent")
    test_rows=[x for x in rows if x["split"]=="test"]
    require(len(test_rows)==len(cases)
            and {x["caseId"] for x in test_rows}==
                {c["caseId"] for c in cases},
            "private quality metadata must describe EXACT released cases")
    by_id={c["caseId"]:c for c in cases}
    for x in test_rows:
        c=by_id[x["caseId"]]
        require(x["domain"]==c["domain"]
                and x["narrative"]==test_narrative(c)
                and x["caseDigest"]==case_digest(c)
                and x["documentaryStatus"]==c["documentaryStatus"]
                and (x["mechanismTag"]=="unmodeled") is
                    (c["domain"]=="unsupported"),
                "metadata diverges from heldout case or claims wrong domain")
    return rows


def audit(meta,source,policy):
    rows=validate_metadata(meta,source,policy)
    findings=[]
    seen=set()
    def emit(code,cases,details):
        key=(code,tuple(sorted(cases)),details)
        if key not in seen:
            seen.add(key)
            findings.append({"code":code,"caseIds":sorted(cases),
                             "detail":details})
    for i,left in enumerate(rows):
        a=normalized_tokens(left["narrative"])
        for right in rows[i+1:]:
            ids=[left["caseId"],right["caseId"]]
            cross=left["split"]!=right["split"]
            for key,code in (
                ("lineage","lineage_cross_split"),
                ("sourceGroup","source_cross_split"),
                ("evidenceRef","evidence_cross_split")):
                if left[key]==right[key]:
                    emit(code if cross else "duplicate_within_split",ids,key)
            b=normalized_tokens(right["narrative"])
            if a==b:
                emit("narrative_exact_cross_split" if cross else
                     "duplicate_within_split",ids,"exact_narrative")
            elif cross and len(a & b)/len(a | b)>=policy["nearDuplicateThreshold"]:
                emit("narrative_near_cross_split",ids,"near_narrative")
    count=Counter(x["split"] for x in rows)
    for split in SPLITS:
        if count[split]<policy["splitMinimums"][split]:
            emit("missing_split",[],split)
    test=[x for x in rows if x["split"]=="test"]
    by_domain=Counter(x["domain"] for x in test)
    by_status=Counter(x["documentaryStatus"] for x in test)
    tag_counts=Counter((x["domain"],x["mechanismTag"]) for x in test)
    for domain in policy["requiredTestDomains"]:
        if by_domain[domain]<1:
            emit("missing_domain_test",[],domain)
    for status in policy["requiredTestStatuses"]:
        if by_status[status]<1:
            emit("missing_status_test",[],status)
    for domain,tags in policy["requiredTestMechanisms"].items():
        for tag in tags:
            if tag_counts[(domain,tag)]==0:
                emit("missing_mechanism_test",[],domain+"/"+tag)
    findings.sort(key=lambda f:(f["code"],f["caseIds"],f["detail"]))
    return {
        "schema":"maintenance-superinteligence.private-quality-audit.v1",
        "version":"1.0.0","mode":"metadata_preflight_not_expert_validation",
        "metadataDigest":digest(meta),"policyDigest":digest(policy),
        "caseSourceDigest":digest(source),
        "recordCount":len(rows),
        "splits":{s:count[s] for s in SPLITS},
        "testDomains":dict(sorted(by_domain.items())),
        "findings":findings,
        "qualityPreflightPassed":not findings,
        "independentReviewCompleted":False,
        "realWorldDiagnosticAccuracyMeasured":False,
        "mayCreateWorkOrder":False,"mayReleaseEquipment":False,
        "decision":"preflight_pass_not_operational_go" if not findings
                   else "quality_rejected_no_go",
    }


def receipt(source,meta,policy,packet):
    from benchmarks.heldout_study import reviewer_packet
    require(packet==reviewer_packet(source),"packet not derived from quality source")
    result=audit(meta,source,policy)
    require(result["qualityPreflightPassed"],
            "quality gate rejected: no case release permitted")
    return {
        "schema":"maintenance-superinteligence.private-quality-receipt.v1",
        "version":"1.0.0","packetDigest":digest(packet),
        "metadataDigest":digest(meta),"policyDigest":digest(policy),
        "auditDigest":digest(result),"passed":True,
        "independentExpertApproval":False,"operationallyApproved":False,
    }


def verify_receipt(proof,source,meta,policy,packet):
    require(proof==receipt(source,meta,policy,packet),
            "quality receipt stale, forged or bound to different release")
    return True
