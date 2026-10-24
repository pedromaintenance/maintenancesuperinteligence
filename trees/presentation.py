"""Static HTML visualization of public synthetic decision paths (no JavaScript)."""
from html import escape
from connectors.fmea_public import require

def render_tree_html(bundle):
    require(bundle.get("schema")
            == "maintenance-superinteligence.investigation-tree-collection.v1"
            and bundle.get("treeCount")==4
            and bundle.get("nodeCount")==13
            and bundle.get("physicalTestsExecuted")==0
            and bundle.get("hypothesesExcluded")==0
            and bundle.get("operationalAuthorization") is False,
            "tree HTML: impossible field or permission claim")
    trees=bundle.get("trees")
    require(isinstance(trees,list) and len(trees)==4,
            "tree HTML: missing synthetic cases")
    for t in trees:
        require(t.get("decision")=="abstain_pending_verified_evidence"
                and t.get("mayCreateWorkOrder") is False
                and t.get("mayModifyECM") is False
                and t.get("mayReleaseEquipment") is False
                and t.get("testsExecuted")==0
                and t.get("unresolvedHypothesisSet",{}).get("allOpen") is True
                and t.get("unresolvedHypothesisSet",{}).get("hypothesesExcluded")==0,
                "tree HTML: field conclusion or authorization")
        for node in t["nodes"]:
            gate=node["evidenceGate"]
            check=node["reviewCheckpoint"]
            require(node["testStatus"]=="not_performed"
                    and node["mayExecute"] is False
                    and gate["currentState"] in {"not_measured","contradicted","inconclusive"}
                    and gate["doesNotTakeConditionalBranch"] is True
                    and gate["mayDiscardHypothesis"] is False
                    and check["allProofsVerified"] is False
                    and check["humanReviewAuthenticated"] is False
                    and check["oemEffectivityVerified"] is False
                    and check["physicalMethodAuthorized"] is False
                    and check["decision"]=="abstain_pending_verified_evidence"
                    and all(b["branchNature"]=="hypothetical_unobserved"
                            and b["observed"] is False
                            and b["hypothesesExcluded"]==0
                            for b in node["conditionalBranches"]),
                    "tree HTML: forged hypothetical branch or review")
    e=lambda x:escape(str(x),quote=True)
    sections=[]
    for t in trees:
        nodes=[]
        for n in t["nodes"]:
            hypotheses=" × ".join(n["hypothesisIds"])
            paths="".join("<li><strong>"+e(b["branchId"])+"</strong>: "
                          +e(b["interpretation"])
                          +" <em>(hipotético; "+e(b["effectFirstIfObserved"])
                          +" / "+e(b["effectSecondIfObserved"])
                          +")</em></li>" for b in n["conditionalBranches"])
            alternatives="".join("<li>"+e(a)+"</li>" for a in n["counterexamples"])
            needs="".join("<li>"+e(a)+"</li>"
                          for a in n["reviewCheckpoint"]["requiredProofs"])
            nodes.append("<details><summary>"+e(n["pairId"])+" — "
                         +e(hypotheses)+" | "+e(n["evidenceGate"]["currentState"])
                         +"</summary><p><strong>Pergunta:</strong> "+e(n["question"])
                         +"</p><h4>Ramos contrafactuais, não observados</h4><ol>"
                         +paths+"</ol><h4>Contraexemplos</h4><ul>"+alternatives
                         +"</ul><h4>Provas para futura revisão humana</h4><ul>"+needs
                         +"</ul><p class='stop'>Transição do exercício: "
                         "ABSTER-SE. Nenhuma hipótese descartada.</p></details>")
        sections.append("<section><h2>"+e(t["caseFileId"])
                        +"</h2><p>Primeira pergunta editorial: "
                        +e(t["rootNodeId"])
                        +" | hipóteses abertas: "
                        +e(", ".join(t["unresolvedHypothesisSet"]["hypothesisIds"]))
                        +"</p>"+"".join(nodes)+"</section>")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src '
            + "&apos;none&apos;; style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; "
            + "form-action &apos;none&apos;" + '"><title>Árvores de investigação didáticas</title>'
            '<style>body{font:15px system-ui,sans-serif;max-width:1100px;margin:2rem auto;'
            'padding:0 1rem;background:#fafafa;color:#252525}section{background:white;'
            'border:1px solid #ddd;margin:1rem 0;padding:1rem}details{padding:1rem;'
            'border-top:1px solid #ddd}summary{cursor:pointer;font-weight:600}'
            '.stop{background:#fff0f0;border-left:4px solid #922;padding:.6rem}</style>'
            '</head><body><h1>Árvores de investigação — SOMENTE SIMULAÇÃO</h1>'
            '<p class="stop">Ramos supports/weakens são hipóteses editoriais,'
            ' NÃO resultados. Sem teste, diagnóstico, OS, ajuste ECM ou liberação.</p>'
            + "".join(sections)
            + '<footer>Conteúdo público fictício; nenhuma integração externa.'
              ' Clique nos títulos para expandir perguntas (HTML nativo, sem scripts).'
              '</footer></body></html>\n')
