# Ciclo 24 — Revisão de propostas de alteração do grafo de dependências

**Versão de P&D:** 2.4.0 · **Data:** 27/10/2026 · **Issue:** [#48](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/48)

## Propósito técnico

Este ciclo responde à seguinte pergunta de governança: **o que mudaria na explicação documental de dependências se alguém propusesse alterar o grafo público de controles?**

A análise **não** modifica o grafo canônico, não edita regras de sistema corporativo, não libera manutenção e não atribui probabilidade de falha física. Todos os cenários são contrafactuais e toda decisão final é `veto_no_merge`, com resultado global `no_go`.

O grafo de referência contém **13 controles e 17 arestas dirigidas**. A referência de comparação é o oráculo independente do Ciclo 23 com **100 cenários**: 13 raízes individuais, 78 pares, três mudanças de contexto e seis conflitos editoriais. Cada proposta compara sua eventual alteração ao grafo original. A cobertura do Ciclo 23 é mantida intacta.

## Dez propostas de alteração

| ID | Proposta fictícia | Interpretação e controle |
| --- | --- | --- |
| SIM-GDIFF-01 | Adicionar identidade → auditoria confiável | Caminho direto redundante, com mudanças possíveis de distância e número de caminhos, sem necessidade de aumentar alcance |
| SIM-GDIFF-02 | Remover decisão assinada → barreira operacional | Remoção de aresta com rota documental indireta ainda existente |
| SIM-GDIFF-03 | Inverter auditoria confiável → barreira operacional | Mudança direcional com comparação explícita dos pares alcançáveis e caminhos |
| SIM-GDIFF-04 | Trocar responsável por efetividade OEM de Engenharia para TI | Violação de segregação e responsabilidade técnica; a topologia não muda e o responsável proposto não é aceito |
| SIM-GDIFF-05 | Suprimir controle de efetividade OEM | Violação do contrato de 13 controles. A proposta não gera um grafo válido para comparação |
| SIM-GDIFF-06 | Adicionar efetividade OEM → reabertura/revogação | Relação nova de revisão documental; não prova que qualquer OEM real mudou |
| SIM-GDIFF-07 | Remover configuração → efetividade OEM | Retira pré-condição documental importante, mantendo veto e exigindo nova análise humana |
| SIM-GDIFF-08 | Adicionar identidade → barreira operacional | Novo caminho direto documental para um destino já alcançável |
| SIM-GDIFF-09 | Adicionar barreira operacional → identidade | Produz ciclo; rejeitado sem calcular métricas como se o grafo continuasse sendo válido |
| SIM-GDIFF-10 | Adicionar nó inexistente → efetividade OEM | Origem não cadastrada; rejeitado, sem promover informação externa ao grafo |

Uma proposta com DAG estruturalmente válido **não é um contrato aprovado**. Sua classificação pode ser `reachability_changed`, `path_metrics_changed_only` ou `owner_governance_violation`, mas o veto continua obrigatório. Exemplos inválidos usam `rejected_invalid_candidate`.

## Semântica e cálculo dos efeitos

Uma aresta `A → B` significa exclusivamente: **o controle documental B depende do controle A**. Não significa transmissão física de carga, fluxo hidráulico, componente danificado ou procedimento OEM aplicável.

Para cada proposta válida e cada par ordenado de controles `(raiz, destino)`, o módulo compara:

- `oldReachable` e `newReachable`: existência de caminho direcionado;
- `oldMinimumSteps` e `newMinimumSteps`: menor quantidade de arestas;
- `oldPossiblePathCount` e `newPossiblePathCount`: quantidade de caminhos em DAG;
- `newPathIntroduced` e `oldPathLost`: aparecimento ou desaparecimento de alcance;
- o conjunto de raízes com alteração e a lista exata de pares cuja métrica mudou.

A comparação usa o oráculo Floyd–Warshall do Ciclo 23 para pares individuais e cada um dos 100 cenários de raízes. O arquivo relata as alterações de alcance **e também** as mudanças de distância/contagem de caminhos que podem ocorrer sem mudança do conjunto alcançável.

**Invariantes de monotonicidade:** num grafo acíclico válido, adicionar aresta não pode eliminar pares anteriormente alcançáveis; remover aresta não pode introduzir pares novos. A inversão não obedece necessariamente às duas propriedades: seus ganhos e perdas são relatados separadamente. Pontas desconhecidas, ciclos e supressão de controle são recusados.

Os cenários com grafo candidato inválido são **não comparáveis**: não recebem 100 casos ficticiamente classificados como inalterados. O conjunto de referência não é modificado nem recalculado como autoridade nova.

## Testemunhos de regressão para 100 cenários

Quando a proposta resulta em DAG comparável, o relatório calcula, para cada caso de origem, os conjuntos e quantidades de controles afetados antes/depois e os destinos cuja alcançabilidade, distância mínima ou contagem de caminhos mudou. O JSON contém os testemunhos com IDs canônicos e campos que deixam explícito `noFieldEvidence=true` e `mayAuthorizeMaintenance=false`.

A análise não mede cobertura empírica do mundo real: os 100 casos são uma **bateria de regressão estrutural de um grafo editorial fixo**, e não 100 falhas de equipamentos. Um SHA-256 permite comparar conteúdo de fixtures/reports, mas não prova identidade de revisor, assinatura nem imutabilidade fora da aplicação.

## Revisão humana exigida, ainda não realizada

O conjunto de revisão proposto envolve cinco áreas:

| Área | O que deve avaliar em um projeto privado futuro |
| --- | --- |
| TI | Compatibilidade com integração, identidades, versionamento e política de mudanças |
| Segurança da Informação | Assinaturas, auditoria confiável, segregação, recuperação e controles de acesso |
| Engenharia | Papel técnico dos pré-requisitos, competência dos revisores e efetividade OEM aplicável |
| Jurídico | Finalidade, base legal, direitos de uso, LGPD e retenção |
| Gestão de Manutenção | Consequências para processos de planejamento, SAP, materiais, execução e liberação |

`ReviewerAssignmentRequirement` mantém todos os campos de autenticação, competência, independência, OEM, avaliação jurídica e aceite assinado como **não verificados**. Nem o motor nem o CI produzem decisões `merge approved`, homologação de equipamento ou autorização para implementar alterações reais.

**Fontes de contexto de governança:** NIST SP 800-63-4 (identidade), OWASP ASVS 5.0.0 (segurança de aplicação), LGPD (tratamento de dados). Nenhuma delas substitui fonte primária OEM com arranjo, revisão e efetividade aplicáveis. Consulte as referências e limites detalhados nos Ciclos 19–20.

## Arquitetura e entregáveis

- `pilot/graph-change-proposals.v1.json` — dez propostas editoriais sintéticas, IDs fixos e gates de revisão negados;
- `pilot/graph_change_review.py` — cálculo isolado de propostas, diferenciação de DAG válido/inválido, diff de arestas e donos, oráculo por raiz, 100 cenários de regressão, verifier por reconstrução e HTML estático;
- `contracts/dependency-graph-change-proposal.schema.json`, `graph-edge-diff.schema.json`, `reachability-impact.schema.json`, `coverage-regression-witness.schema.json`, `reviewer-assignment-requirement.schema.json`, `change-adjudication.schema.json`, `graph-change-no-operational-authority.schema.json` e envelopes suplementares — **11 JSON Schemas**;
- `tests/test_graph_change_review.py` — 26 testes adversariais e funcionais de monotonicidade, completude e integridade, adulteração e proibição de autoridade operacional;
- GitHub Actions — recompõe toda a cadeia sintética desde o FMEA público pinado, executa a regressão e publica arquivos JSON/HTML temporários. A entrada externa alterada é rejeitada antes da exportação.

## Reprodução local

Execute primeiro o pipeline documentado até o Ciclo 23, gerando `build/fmea-public`, `build/go-nogo`, `build/sequencing`, `build/contradictions` e `build/coverage`. Em seguida:

```bash
python -m unittest discover -s tests -v

python -m pilot.graph_change_review \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --gng build/go-nogo/no-go-report.v1.json \
  --sequence build/sequencing/evidence-sequence.v1.json \
  --contradictions build/contradictions/contradictions.v1.json \
  --coverage build/coverage/reopen-coverage.v1.json \
  --output build/graph-change/graph-change-review.v1.json \
  --html build/graph-change/graph-change-review.v1.html
```

O HTML é somente leitura, com CSP, sem scripts, formulários ou integrações corporativas. O resultado dos dez casos permanece vetado. Nada é escrito em `pilot/go-nogo-package.v1.json` ou em `pilot/reopen-coverage.v1.json`.

## Limites e evolução candidata

A distinção essencial é **proposta hipotética ≠ adulteração aceita ≠ mudança homologada**. O código pode estimar consequências sobre dependências documentais canônicas, mas não pode inferir se uma dependência é tecnicamente segura nem se ela é válida para uma máquina.

Próximo ciclo candidato: preparar pacotes de revisão de mudanças com evidências externas necessárias, fluxos de contestação e rastreabilidade de decisão, mantendo qualquer execução, aprovação técnica ou alteração no grafo real fora do repositório público.
