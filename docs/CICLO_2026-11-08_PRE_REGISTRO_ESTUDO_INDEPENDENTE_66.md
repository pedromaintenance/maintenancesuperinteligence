# Ciclo 66 — Pré-registro e lacunas de evidência para estudo independente

**08/11/2026 · P&D · proposta empilhada sobre o Ciclo 65 · NO GO**

## Problema real

Os ciclos 58–65 expandiram os ensaios estruturais de hipóteses, medições inventadas, referências fictícias, aplicabilidade de metadados, revisões documentais e personagens simulados em contestações. O risco metodológico permanece: uma sequência crescente de testes sintéticos pode criar aparência de validação diagnóstica **sem casos inéditos, fontes OEM efetivas, custódia real ou especialistas externos**.

Este ciclo não inventa uma nova avaliação cega. Ele **liga a pesquisa de conflitos do C65 aos requisitos já especificados nos ciclos 29 (revisão independente), 30 (custódia fora do Git) e 32 (qualidade obrigatória antes de distribuição)** e produz uma lista verificável de impedimentos — não uma licença para executar estudo com pessoas ou usar referências reais.

## Artefatos

- `benchmarks/cycle66_study_preregistration.py`: valida primeiro a trilha C65; exige pelo menos uma referência sintética ainda conflituosa, um plano pré-registrável e os 12 controles abaixo.
- `tests/test_cycle66_study_preregistration.py`: 24 métodos de regressão sobre alegações falsas de aprovação, ausência de dados, cegamento, denominadores e desvio das regras de segurança.
- `.github/workflows/cycle66-study-preregistration.yml`: testes offline C58–C66, sem dados restritos, chaves ou acesso à infraestrutura de manutenção.
- Este documento registra justificativa, interpretação e critérios para revisão futura.

## Controles que dependem de prova independente

Os 12 controles do **recorte de estudo do C66** são:

| Controle | Evidência externa necessária antes de um estudo real |
| --- | --- |
| `source_use_permission` | Direito de uso e escopo de distribuição documentados |
| `oem_effectivity_and_revision` | Aplicabilidade documental por série/arranjo/revisão, verificada por responsável autorizado |
| `case_origin_and_provenance` | Proveniência e autorização dos casos inéditos |
| `heldout_contamination_screen` | Auditoria de vazamento entre treino, desenvolvimento e casos inéditos |
| `independent_custodian` | Custodiante autorizado independente do desenvolvimento |
| `sealed_oracle_outside_repository` | Gabarito fechado fora do Git, sem vazamento ao revisor |
| `reviewer_competency` | Qualificação técnica comprovada em ambiente próprio |
| `reviewer_conflict_disclosure` | Declaração de conflitos de interesse |
| `blind_case_distribution` | Protocolo de entrega sem revelar respostas esperadas |
| `frozen_individual_submissions` | Pareceres individuais congelados antes da abertura do gabarito |
| `critical_disagreement_adjudication` | Terceiro parecer quando houver divergência técnica crítica |
| `data_protection_and_retention` | Privacidade, acesso e retenção sob controle institucional |

**Não confundir:** estes 12 controles são o recorte de **pré-registro do estudo C66**; não substituem nem certificam os 13 gates externos de prontidão mencionados em outros ciclos. A contagem de controles não mede maturidade técnica.

No repositório público, cada controle aceita apenas `not_recorded` ou `synthetic_rehearsal`. Campos de evidência e identidade do verificador são obrigatoriamente `null`. Um ensaio marcado como realizado não altera a lista de 12 exigências externas não verificadas.

## Plano pré-registrável, ainda não congelado

O módulo exige a *intenção* de fazer uma avaliação cega: 2 revisores e 1 potencial adjudicador, 2–50 casos didáticos declarados, gabarito externo planejado, respostas futuras congeladas antes de revelar expectativas, e `preRegistrationStatus=not_frozen`. Isso **não** é evidência de pré-registro efetivo, compromisso institucional ou estudo executado.

Cinco classes críticas devem constar na rubrica: (1) afirmação de causa raiz sem prova; (2) alegação falsa de aplicabilidade OEM; (3) ordem de serviço não autorizada; (4) liberação não autorizada de equipamento; (5) incapacidade de abster-se de conclusão. Uma ocorrência crítica no estudo futuro bloqueia conclusões aprovadoras conforme a regra planejada; o módulo não observa ocorrências reais.

Quatro indicadores são especificados com denominadores claros, para evitar números favoráveis calculados seletivamente:
- contagem de erros críticos / todas as respostas congeladas de casos;
- taxa de abstenção / todas as respostas congeladas de casos;
- concordância com pergunta discriminante / respostas congeladas elegíveis, com regra futura de elegibilidade pré-definida;
- desacordo entre revisores / casos avaliados por ambos.

A especificação do denominador **não basta para medir validade**: critérios de elegibilidade, definição de caso independente, confiabilidade da rubrica, amostragem e tratamento de itens sem adjudicação ainda exigem pré-registro humano efetivo.

## Resultado e negações

`externallyVerifiedControls=0`, `metricValuesComputed=false`, `realHumanReviewCompleted=false`, `readyForIndependentStudy=false` e `decision=NO GO` são invariantes. O recibo vincula o plano ao snapshot sintético do C65 por SHA-256 canônico, que **não é assinatura, timestamp confiável, identidade ou custódia externa**.

O algoritmo rejeita alegações de gabarito publicado, seleção de métricas a posteriori, desaparecimento de categorias críticas, falsos aceites, validação independente simulada como real e autorizações operacionais. Não coleta dados OEM, SAP, ECM, laudos ou telemetria.

## Reproduzir

```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics tests.test_cycle63_effectivity tests.test_cycle64_source_governance tests.test_cycle65_review_ledger tests.test_cycle66_study_preregistration -v
python -m benchmarks.cycle66_study_preregistration --input /tmp/plano-sintetico.json --output /tmp/recibo-c66-novo.json
```

`fixture()` no módulo de testes cria o plano fictício completo.

## Aceitação e próximo passo

A regressão automatizada aprovada significa somente **correção das invariantes de software testadas**, não que exista estudo independente pronto, revisão humana ou diagnóstico mecânico validado.

O próximo ciclo deve privilegiar a **reconciliação da cadeia de PRs e da matriz de evidências**: detectar lacunas, artefatos sobrepostos, dependências, documentos desatualizados e critérios para eventual consolidação na `main`. Isso reduz dívida de integração antes de acrescentar novas camadas sintéticas.

**NO GO:** nenhuma autorização de teste de campo, OS, SAP, ECM, parâmetro OEM, condenação ou liberação de máquina.
