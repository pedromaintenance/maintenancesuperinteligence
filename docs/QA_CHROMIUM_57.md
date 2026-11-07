# Ciclo 57 — Regressão automatizada em Chromium dos portais públicos

**07/11/2026 · P&D · branch `research/cycle57-browser-replay-qa-and-static-fixes` · PR draft sobre o Ciclo 56.**

> **NO GO:** o objetivo deste ciclo é executar ações observáveis em **Chromium headless**, com dados públicos sintéticos, e coletar evidência reproduzível sobre comportamento de interface. A automação não é uma pessoa, não usa NVDA/VoiceOver, não realiza análise de conteúdo OEM, não valida um diagnóstico e não habilita operação de equipamentos.

## O problema identificado

Até o Ciclo 56, os três HTMLs dos portais e a bancada de QA tinham contratos de marcação, sintaxe JavaScript e relatórios de estado fixos, mas não havia uma rodada de interações em navegador efetivamente executada. Uma falha em exportação/importação, seleção de abas ou scroll em telas móveis poderia passar por um teste puramente estático.

O Ciclo 57 introduz `tests/browser_cycle57.mjs`, que usa `playwright@1.56.1` e Chromium headless em GitHub Actions, executando quatro arquivos HTML locais via `file://`:

| Superfície | Arquivo |
| --- | --- |
| Bancada de revisão | `review/qa_portais_56.html` |
| Portal de conhecimento | `portal/index.html` |
| Portal de auditoria | `portal/auditoria.html` |
| Portal de publicações | `portal/versoes.html` |

Nenhuma ação do teste depende de uma API de produção. O script rejeita requisições HTTP(S) a partir das páginas, registra erros JavaScript e captura **somente a parte visível** de cada superfície em viewport de 375px. Não captura formulários reais de usuários nem acessa SAP/ECM.

## Nove cenários de regressão

1. **Estado inicial da bancada:** oito itens originais `not_tested` e NO GO visível.
2. **Exportação / reimportação:** um relatório sintético com uma falha e um resultado positivo é salvo, reaberto em nova sessão, restaurado e exportado novamente, sem perda de conteúdo.
3. **Importação adulterada:** o navegador recusa JSON que falsifica `humanReviewCompleted`, `operationalAuthorityGranted` ou `decision`. Inclui verificação de que texto HTML inserido num campo não vira elemento executável.
4. **Oito resultados autodeclarados:** mesmo quando o teste sintetiza oito `passed`, o JSON permanece `humanReviewCompleted:false`, sem autorização operacional.
5. **Auditoria por teclado:** setas, Home/End, aba ativa, painel visível, pesquisa sem correspondência e exportação dos 13 gates.
6. **Conhecimento:** filtros, estado vazio, alternância de tema e exportação do catálogo.
7. **Versões:** alternância de snapshots, diff vazio entre versões idênticas, diff positivo entre versões distintas e exportação JSON com autoridade falsa.
8. **Responsividade:** quatro superfícies em 320, 375, 390 e 768 pixels CSS, sem overflow horizontal não planejado; screenshots públicas e sintéticas na largura de 375px.
9. **Atalho por teclado:** foco inicial no link de salto para conteúdo, ativação e navegação ao `main` nos quatro documentos.

O artefato `build/browser-cycle57/summary.json` inclui resultados por cenário, o navegador realmente usado e a contagem de falhas. O workflow anexa esse relatório e **quatro screenshots sintéticas** ao GitHub Actions, mesmo quando a rodada falha, para depuração.

## Contratos e controles

- `contracts/cycle57-browser-report.schema.json`: contrato fechado para exatamente nove cenários, resultados positivos e ausência obrigatória de afirmações humanas ou operacionais.
- `tests/test_cycle57_browser_contract.py`: verifica os controles estáticos e impede que o relatório seja usado como substituto de certificação humana.
- `.github/workflows/cycle57-browser-tests.yml`: instala Chromium real num runner **Ubuntu 24.04 fixado**; a instalação no `ubuntu-latest` falhou inicialmente porque o runner foi atualizado para Ubuntu 26.04, incompatível com `playwright@1.56.1`.
- O workflow carrega apenas fontes HTML sintéticas e scripts auditáveis. Qualquer erro na execução faz o job falhar, e seu relatório permanece para diagnóstico.

## Execução final confirmada — navegador e publicação

A [execução de Chromium #42422866865](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42422866865) concluiu com **success** no commit de pesquisa `76836c964cd2ef9af2baab916262b2d139590ef7`, com **9/9 cenários aprovados, 0 falhas**. Seu artefato público e sintético `cycle57-browser-qa-synthetic-public` contém `summary.json` e quatro capturas de 375px (bancada, conhecimento, auditoria e versões), retidas por 14 dias. A regressão geral do mesmo commit [#42422944440](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42422944440) também passou.

O teste detectou, antes da correção, overflow horizontal real no portal de versões: `documentElement.scrollWidth = 834px` para viewport de 320px, provocado pelo `span#limit` com identificador de proveniência longo sem quebra. A correção local `overflow-wrap:anywhere;word-break:break-word` eliminou o problema nas larguras ensaiadas, preservando todo o texto. A publicação isolada de **somente `versoes.html`** na `main` ocorreu no commit `e0789a780c07cdd19ea1ddf3f11a1f24481c7ad0`, sem merge dos PRs de pesquisa. O [deploy Pages #42423090773](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42423090773) concluiu com sucesso e confirmou **três respostas HTTP com SHA-256 idêntico ao conteúdo enviado**; o recibo `pages-release-evidence-42423090773` está temporariamente retido no GitHub Actions, até sua política de expiração.

**Nenhum dos oito testes humanos foi realizado pela automação.** Capturas e resultados são sintéticos; não se afirma WCAG, NVDA/VoiceOver, competência de profissional ou qualquer validade de manutenção.

## Critérios de conclusão

O ciclo estará pronto para revisão quando **todos os nove cenários** passarem no HEAD final e a regressão geral também estiver verde. Se a inspeção identificar defeitos, eles devem ser corrigidos na branch com novo commit e novos testes, nunca ocultados nem classificados como `passed` por conveniência.

### O que fica pendente de pessoa

Teste de leitor de tela real, julgamento de contraste e legibilidade, revisão de conteúdo público e licenças, julgamento contextual de usabilidade e confirmação por responsável independente. Esses itens continuam `not_tested` no `review/portal_qa_template.v1.json`.

**Separação de alçadas:** Chromium automatizado confirma comportamentos testados. O checklist humano exige execução humana. Engenharia mecânica exige evidências técnicas externas, ainda com 13/13 gates não verificados. **NO GO para testes físicos, ordens, SAP/ECM ou liberação.**
