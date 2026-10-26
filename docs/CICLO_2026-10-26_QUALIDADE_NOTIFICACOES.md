# Ciclo 17 — Qualidade documental de notificações sintéticas

**Data:** 26/10/2026 · **Versão de P&D:** 1.7.0 · **Issue:** [#34](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/34)

## Objetivo

Verificar a **completude documental** dos quatro rascunhos de treinamento gerados pelo Ciclo 16, sem alegar validade mecânica, exatidão diagnóstica, homologação OEM ou aprovação para execução. Um documento pode estar completo **para ensinar a redação de uma notificação** e continuar integralmente bloqueado para registro SAP, manutenção, compra de peças ou liberação de equipamento.

O ciclo introduz três instrumentos: rubrica editorial de 12 critérios, oráculo independente de regressão com 14 adversários fictícios e motor `quality/notifications.py` que produz relatório JSON e HTML offline. Os rascunhos originais não são alterados.

## Doze critérios — interpretação técnica

| Critério | Tipo | O que verifica |
| --- | --- | --- |
| `training_identification` | Crítico | Banner e IDs de exercício, nenhuma pretensão de nota SAP |
| `symptom_objective` | Crítico | Relato fictício não promovido a medição de campo |
| `function_and_effect` | Documental | Função/requisito e possível efeito separados |
| `causality_not_confirmed` | Crítico | Mecanismo hipotético distinto de causa raiz comprovada |
| `alternatives_open` | Crítico | Hipóteses mantidas abertas, sem probabilidade ou descarte |
| `missing_evidence_explicit` | Crítico | Registro explícito de contexto ausente/contraditório e provas pendentes |
| `discipline_consistent` | Documental | Mecânica/lubrificação, hidráulica ou elétrica coerentes com o caso |
| `scope_is_investigation` | Crítico | Escopo limitado a investigação proposta, sem teste ou substituição executada |
| `planning_without_invention` | Crítico | HH, materiais, custo, prioridade, limites e numeração SAP permanecem ausentes |
| `risk_is_qualitative` | Crítico | Risco descrito qualitativamente, sem avaliação física nem escore fabricado |
| `provenance_public_trace` | Crítico | Vínculos coerentes com dossiê, árvore, método, fontes e hashes públicos |
| `oem_human_safety_pending` | Crítico | Revisão técnica, método OEM, segurança e autorização ainda pendentes |

O resultado de cada critério é `met` ou `needs_revision`, com campos pertinentes e **ação de correção documental**. O agregado é `adequate_for_synthetic_training` se os doze forem cumpridos, `needs_documentary_revision` se somente critérios documentais falharem, ou `blocked_unsafe_claims` se algum critério crítico não for atendido. As categorias são **regras editoriais escritas pelo projeto**, e não uma escala calibrada de risco real.

Há uma diferença importante: `adequate_for_synthetic_training` **não** significa que a notificação contenha evidência física suficiente. Os quatro relatórios conservam os mesmos **quatro bloqueios externos**: efetividade OEM por série não verificada, medição física não realizada, parecer de profissional independente não autenticado e riscos de execução não avaliados no campo. Todos permanecem `evidenceReceived=false` e `remainsBlockingForOperationalUse=true`.

## Cenários sintéticos avaliados

Os quatro rascunhos continuam sendo: `SIM-NOTE-001` comando final CAT 777E (perfil de aditivos), `SIM-NOTE-002` hidráulica com carga contraditória, `SIM-NOTE-003` ECM com DTC registrado e `SIM-NOTE-004` ECM com indicação ativa fictícia. A classificação editorial esperada, **somente para os arquivos originais fornecidos neste repositório**, é `adequate_for_synthetic_training` nos quatro casos, com 12 critérios satisfeitos cada.

O oráculo independente `benchmarks/notification-quality-oracle.v1.json` fixa quatro resultados de referência e 14 adulterações editoriais sintéticas, incluindo:

- defeito ou causa raiz falsamente confirmados;
- substituição de `workHours=null` por HH inventada, número SAP fictício ou permissão de exportação;
- ausência do escopo ou da lista de evidências;
- fechamento indevido do registro de hipóteses;
- disciplina incorreta ou requisito funcional vazio;
- parecer humano ou efetividade OEM alegados como comprovados;
- relato promovido a medição, risco numérico fabricado e inspeção declarada executada.

A cada alteração, o avaliador aponta a não conformidade e a ação documental requerida. **Nenhum valor original adulterado é copiado para o texto dos achados**, reduzindo o risco de reprodução de informações de fonte não autorizada.

## Origem e proteção contra falsificação

A CLI de geração exige os arquivos de notificação e dossiês sintéticos, além do snapshot FMEA público. Antes de emitir qualquer avaliação, ela:

1. Confere os bytes do FMEA com o hash pinado na base pública.
2. Reconstitui dossiês/árvores com as regras e oráculo já versionados nos Ciclos 13–15.
3. Reconstitui os quatro rascunhos do Ciclo 16.
4. Exige **igualdade integral** com os documentos submetidos. Arquivos alterados, textos não revisados e identificadores adicionais são rejeitados.
5. Exige igualdade da rubrica e do oráculo com o exemplar publicado e recalcula os achados.

Os hashes SHA-256 conectam rubrica, notificações, dossiês, matriz qualitativa, árvores e FMEA público. Esses hashes verificam identidade de conteúdo neste exercício, **não** validam autoria humana, integridade criptográfica externa ou evidência de manutenção real.

## Governança de revisão

O objeto `HumanEditorialReview` sempre conserva `engineeringExpertAuthenticated=false`, `independentReviewerAuthenticated=false`, `documentAcceptedByRealReviewer=false`, `fieldDiagnosticValidityEstablished=false` e `interRaterReliabilityMeasured=false`. O projeto não fabrica avaliações de especialistas nem estima concordância entre revisores sem observações humanas autênticas.

As regras editoriais **não** pontuam eficácia de testes, sensibilidade, especificidade, severidade real ou confiança diagnóstica. A quantidade de critérios atendidos é apenas um contador de completude de campos em exemplos didáticos; não é probabilidade de acerto nem maturidade operacional.

## Arquivos e contratos

- `quality/notification-rubric.v1.json`: rubrica de 12 critérios e recomendações documentais.
- `quality/notifications.py`: motor determinístico, relatório JSON/HTML e CLI fail-closed.
- `benchmarks/notification-quality-oracle.v1.json`: quatro bases e 14 alterações adversariais.
- Nove contratos JSON Schema: `NotificationQualityCriterion`, `QualityFinding`, `MissingInformation`, `ScopeSafetyFinding`, `HumanEditorialReview`, `QualityAssessment`, envelopes de rubrica, relatório e oráculo.
- `tests/test_notification_quality.py`: regressões de documentos, fontes, rubricagem, achados, revisão fictícia, integridade e exportação.
- Workflow GitHub Actions: executa testes, gera relatório JSON/HTML temporários e rejeita fonte adulterada, falso parecer especialista e horas inventadas.

## Reproduzir

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m casefiles.integrated \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --output build/trees/technical-cases.v1.json

python -m notifications.drafts \
  --source build/trees/technical-cases.v1.json \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --output build/notifications/maintenance-drafts.v1.json

python -m quality.notifications \
  --source build/trees/technical-cases.v1.json \
  --drafts build/notifications/maintenance-drafts.v1.json \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --output build/quality/notification-quality.v1.json \
  --html build/quality/notification-quality.v1.html
```

A página HTML é de leitura offline, sem formulários, login, scripts ou chamadas a serviços corporativos. Não há interface de envio de notificações ao SAP PM.

## Limites e evolução proposta

O projeto não substitui o processo real de inspeção/planejamento nem valida procedimentos OEM ou condição operacional. A utilidade atual é ensinar como registrar sintoma, hipótese, escopo e informação faltante com rastreabilidade. A extensão futura deve avaliar se diferentes profissionais, **em ambiente autorizado e usando apenas dados adequadamente tratados**, concordam sobre os mesmos critérios — após uma política de revisão humana e proteção de dados. Até lá, a rubrica não tem validade empírica de campo.
