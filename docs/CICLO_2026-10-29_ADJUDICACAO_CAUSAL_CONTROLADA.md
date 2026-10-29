# Ciclo 36 — Adjudicação controlada de contestações causais

**P&D v3.6.0 · 29/10/2026.** Continuação da revisão crítica do Ciclo 35, sem parecer de especialista independente verificado.

## Objetivo

Converter as 72 contestações fictícias do Ciclo 35 em **36 registros editoriais de adjudicação**, com uma justificativa explícita por relação causal, prioridade de revisão e tratamento do contraexemplo. Impedir que a mera existência de comentários seja usada como comprovação diagnóstica ou aprovação de alteração na matriz técnica.

## Distinção entre gravidade, decisão e autorização

A prioridade `high_review_priority`, `medium_review_priority` ou `watch_review_priority` representa somente **ordem editorial de análise**. **Não corresponde à criticidade de ativo, gravidade de falha, risco de acidente, prioridade de OS SAP ou decisão de operação.** A classificação deriva da triagem de dissenso, necessidade de reformulação ou falta de suporte do ciclo anterior, não de dados de equipamento.

| Entrada do Ciclo 35 | Destino editorial | Quantidade | Efeito sobre as versões |
| --- | --- | ---: | --- |
| Dois comentários divergentes | Adiar até adjudicação técnica independente | 12 | Preservar v1 sem criar substituição |
| Dois comentários solicitam reformulação | Registrar texto candidato v2 ainda não aprovado | 12 | Preservar v1 e anexar v2-proposed-unapproved |
| Dois comentários não conseguem avaliar | Rejeitar a inferência como fundamento de diagnóstico | 12 | Preservar v1 no histórico sem exclusão automática |

Todas as 36 relações continuam abertas à análise independente. A decisão autoral não tem eficácia operacional.

## Histórico reconstituível

A saída `cycle36-version-ledger.json` contém **48 eventos**. Para cada uma das 36 relações, o histórico guarda o texto original do Ciclo 34, seu digest e a versão `v1-frozen`; somente 12 registros com proposta consensual fictícia recebem um segundo evento `v2-proposed-unapproved` com redação condicional acrescida de limites explícitos. O texto v2 permanece rascunho — não altera `knowledge/discriminating-evidence-matrix.v1.json` nem valida o mecanismo causal.

Cada evento inclui `sourceRuleDigest`, `frozenMatrixDigest`, `reviewBatchDigest`, `policyDigest`, `priorVersionDigest` (para v2), `previousLedgerDigest` e `eventDigest`. O relatório vincula seus hashes a esse histórico e ao lote de revisões.

**Limite de integridade:** a cadeia é inteiramente reconstituível por código público, sem assinaturas, carimbo de tempo externo ou armazenamento WORM. Quem controla simultaneamente as fontes e o histórico pode recalcular todos os hashes; portanto ela permite detectar alterações apenas em comparação com um estado anterior preservado separadamente.

## Regras de aceitação editorial

- Justificativa descritiva de pelo menos 100 caracteres, com ID da relação original e fonte geral já associada aos comentários.
- Uma proposta v2 só pode existir quando ambos os comentários do Ciclo 35 solicitaram a mesma revisão; a frase candidata preserva a condição original com ressalvas explícitas de evidência, aplicabilidade e causa.
- Relações contestadas ou sem suporte não podem receber versão substituta.
- Contraexemplos permanecem abertos; discordância não é decidida automaticamente por maioria ou por texto mais persuasivo.
- O campo `independentReviewCompleted` permanece `false`, assim como aprovação OEM, autorização de teste, ordens SAP, liberação e permissão de modificação da matriz upstream.

## Implementação

- `knowledge/causal_adjudication.py`: valida decisões, confere contestações, produz histórico e relatório.
- `knowledge/causal-adjudication-plan.v1.json`: 36 adjudicações autorais simuladas, com raciocínio vinculado a IDs.
- `knowledge/causal-adjudication-policy.v1.json`: política conservadora de classificação e bloqueios.
- `contracts/causal-adjudication-plan.schema.json`, `causal-adjudication-policy.schema.json`, `causal-version-ledger.schema.json`, `causal-adjudication-report.schema.json`.
- `tests/test_causal_adjudication.py`: testes de integridade referencial, prioridades, preservação de v1, impossibilidade de aprovação, adulteração de histórico e segurança dos relatórios.

```bash
python -m unittest tests.test_causal_adjudication -v
python -m knowledge.causal_adjudication \
  --output build/benchmarks/cycle36-adjudication.json \
  --ledger build/benchmarks/cycle36-version-ledger.json \
  --html build/benchmarks/cycle36-adjudication.html
```

Se uma proposta experimental externa for fornecida em diretório diferente do repositório, o CLI exige que seus arquivos de saída também permaneçam fora da árvore pública. Ele não habilita ingestão de dados de máquina, pareceres humanos autenticados ou reescrita de regras originais. A escrita de múltiplos arquivos não é uma transação atômica de sistema de arquivos; para custódia real seria necessário mecanismo transacional, assinatura e controle de acesso.

## Próximo patamar

Para adjudicação real, ainda faltam confirmação de identidade e competência dos revisores por processo organizacional, literatura OEM aplicável ao número de série, evidência operacional legitimamente coletada, política de conflito de interesse e decisão formal documentada por profissional habilitado.

**Conclusão:** `no_go_editorial_drafts_require_independent_engineering_adjudication`. Nem concordância editorial nem texto v2 equivalem a confirmação de falha, causa raiz ou intervenção aprovada.
