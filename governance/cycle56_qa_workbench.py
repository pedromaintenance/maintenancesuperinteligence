"""C56: integrity checks for offline manual QA workbench and public custody mirror.

Static inspection verifies that the HTML embeds the original eight untested
procedures and never grants professional approval. It does NOT execute
browser accessibility tests and does NOT evaluate any human results.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
WORKBENCH=ROOT/"review/qa_portais_56.html"
TEMPLATE=ROOT/"review/portal_qa_template.v1.json"
SCHEMA=ROOT/"contracts/human-qa-session.schema.json"
SCRIPT=re.compile(r'<script id="qa-template" type="application/json">\s*(.*?)\s*</script>',re.DOTALL)

class QAGateRejected(ValueError):
    pass

def require(test,reason):
    if not test:raise QAGateRejected(reason)

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate_template(t):
    require(isinstance(t,dict)
            and t["schema"]=="maintenance-superinteligence.human-pages-qa-template.v1"
            and t["version"]=="1.0.0"
            and t["humanReviewCompleted"] is False
            and t["humanReviewerIdentityCollectedHere"] is False
            and t["operationalAuthorityGranted"] is False
            and t["mechanicalDiagnosticAccuracyValidated"] is False
            and t["decision"]=="NO GO",
            "QA template claims approval")
    checks=t.get("checks",[])
    ids=["mobile_layout","zoom_reflow","keyboard_skip_focus",
         "audit_tabs","screen_reader","status_clarity",
         "export_integrity","sources_permissions"]
    require(isinstance(checks,list) and [x["id"] for x in checks]==ids
            and all(x["status"]=="not_tested"
                    and x["observations"]==""
                    and x["evidenceReference"]=="" for x in checks),
            "original QA template was changed or prefilled")
    return t

def check():
    template=validate_template(load(TEMPLATE))
    html=WORKBENCH.read_text(encoding="utf-8")
    copies=SCRIPT.findall(html)
    require(len(copies)==1,"HTML must contain one embedded QA template")
    embedded=json.loads(copies[0])
    require(embedded==template,
            "offline QA workbook embeds stale or falsified evidence")
    require(html.startswith("<!doctype html>")
            and 'lang="pt-BR"' in html
            and "NO GO OPERACIONAL" in html
            and 'href="#content"' in html
            and 'id="content"' in html
            and 'aria-live="polite"' in html
            and "prefers-reduced-motion" in html,
            "workbench lacks essential visible warnings or accessibility primitives")
    require("<script src=" not in html and "fetch(" not in html
            and "localStorage" not in html
            and "XMLHttpRequest" not in html
            and "WebSocket(" not in html,
            "workbench includes dynamic network or persistent browser storage")
    for needle in ("id=\"import\"","id=\"export\"","id=\"reset\"",
                   "validateImport(doc)","doc.humanReviewCompleted!==false",
                   'doc.decision!=="NO GO"',"document.createElement",
                   "JSON.stringify(state,null,2)","missingEvidence(item)"):
        require(needle in html, "missing reviewed UI feature: "+needle)
    schema=load(SCHEMA)
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:
        raise QAGateRejected("jsonschema must be installed for QA checks") from error
    Draft202012Validator.check_schema(schema)
    validator=Draft202012Validator(schema)
    require(validator.is_valid(template),"human QA template fails strict session schema")
    return {
        "schema":"maintenance-superinteligence.cycle56-qa-workbench-audit.v1",
        "version":"1.0.0",
        "qaChecksAvailable":8,
        "humanChecksActuallyExecuted":0,
        "offlineTemplateIdentical":True,
        "staticJsAndMarkupContractsChecked":True,
        "browserAccessibilityVerified":False,
        "qualifiedHumanSignoff":False,
        "mechanicalAccuracyVerified":False,
        "externalStudyGatesVerified":0,
        "operationalAuthorityGranted":False,
        "decision":"NO GO"
    }

def main(argv=None):
    p=argparse.ArgumentParser(description="Verify offline human QA workbench; never attest review")
    p.add_argument("--check",action="store_true")
    p.add_argument("--output",type=Path)
    args=p.parse_args(argv)
    require(args.check or args.output is not None,"Provide --check or --output")
    result=check()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    return result

if __name__=="__main__":
    main()
