# Ciclo 08 — Governança de revisão técnica e qualificação de afirmações

**Versão:** v0.8.0 • **Data:** 24/10/2026 • **Escopo:** simulação de processo de governança, sem validação técnica de campo.

**Issue:** [#16](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/16)

## Problema

Os Ciclos 02–07 organizaram o conhecimento e os mecanismos hipotéticos, construíram perguntas técnicas e testaram a regressão de cenários fictícios. Isso, por si só, **não prova que uma afirmação seja verdadeira**, que determinada literatura OEM seja aplicável à série, ou que a questão discriminante detecte um defeito real.

Este ciclo acrescenta uma etapa de **qualificação governada de afirmações** antes de qualquer futura alegação de aplicabilidade, acurácia ou autorização. O fluxo é explicitamente **simulado**: nenhuma pessoa assinou qualquer parecer e não foi verificada a competência nem a independência de um engenheiro. IDs de revisores distintos significam apenas identidades fictícias diferentes no exercício.

## Modelagem e implementação

| Objeto | Regra / significado |
| --- | --- |
| `TechnicalClaim` | afirmação curta e interpretável, método e par de hipóteses a que se relaciona, alternativa/contraexemplo e limite interpretativo obrigatórios |
| `EvidenceCitation` | referência pública geral existente no registro de fontes e no método da biblioteca; não contém texto licenciado nem se declara literatura por série |
| `ApplicabilityEvidence` | fabricante, modelo, série/arranjo, publicação e revisão vazios; status `not_verified`, jamais autorização OEM |
| `ReviewerAssessment` | parecer **simulado** com ID de personagem fictício, disciplina, rodada, justificativa, referências e escolha `support_general`, `insufficient` ou `challenge` |
| `ReviewDisagreement` | preserva ambas as posições e o contraexemplo, com `resolution=not_adjudicated` |
| `ReviewDecision` | estado **derivado pelo software**, nunca importado de campo e nunca interpretado como assinatura real |

Os seis contratos acima, além dos de `SyntheticReviewer` e `TechnicalReviewPacket`, estão em `contracts/*.schema.json`. A integridade entre IDs, método, par, fonte, domínio, parecer e revisão é validada por `governance/review.py` usando a origem técnica do Ciclo 05 e a matriz do Ciclo 06.

O pacote `governance/review-packet.v1.json` contém **8 afirmações autorais**, **9 vínculos de citação a referências gerais** e **13 pareceres fictícios**, de óleo, hidráulica, eletrônica, inspeção mecânica e vibração.

### Os estados e suas regras

A máquina de estados suporta seis termos. **Somente cinco podem aparecer neste simulador público**:

- `draft`: nenhum parecer, afirmação ainda não avaliada.
- `under_review`: um parecer fictício na rodada atual.
- `needs_evidence`: dois pareceres, ao menos um insuficiente, sem discordância explícita tipo `challenge`.
- `disputed`: a rodada inclui `challenge`, com registro explícito da divergência e contraexemplo.
- `general_reference_supported`: dois IDs fictícios distintos marcaram suporte geral; **status exclusivo do exercício, não uma aprovação técnica real**.
- `oem_series_verified`: **estado reservado para arquitetura futura privada/autorizada e proibido neste código público**. Mesmo o grupo hipotético `general_reference_supported` não se eleva a esse nível.

Não basta informar um campo de estado manualmente: o sistema o calcula a partir dos pareceres. Não há atalho por resposta do modelo, aprovação de pipeline, indicação de fabricante ou booleans de entrada.

### A segunda rodada e divergências

Uma rodada só pode ter até dois pareceres fictícios. A segunda exige **dois novos IDs distintos** e só é aceita depois de dois pareceres na primeira rodada que não produziram unanimidade de suporte. O histórico permanece no pacote, e o estado é calculado pela rodada mais recente.

Isso permite **simular** um processo de reavaliação de divergência, mas não representa imparcialidade, competência, autenticação ou consenso de especialistas reais. Esses elementos precisam de um sistema de identidade e revisão externa à base pública, inclusive controle de conflito de interesse e logs assinados.

## Vinculação das fontes

As nove citações fazem referência ao catálogo `data/diagnostic-method-sources.v1.json` e são compatibilizadas com `methods/catalog.v1.json`. O pacote aceita, por exemplo, referências gerais de Caterpillar para análise de óleo, inspeção de bujões e diagnóstico ET, SKF para rolamentos/vibração, e Bosch Rexroth para discussão conceitual de hidráulica.

Uma URL apontando para fonte de fabricante **não demonstra** que a afirmação específica foi confirmada por ele. O campo `interpretationRole=public_general_context_only` delimita precisamente isso. Não há extração literal de manual, critério OEM por número de série, medição de campo ou verificação de publicação/revisão técnica efetiva.

A execução do CI consulta o **snapshot FMEA público fixado por SHA-256**, e os métodos e pares de hipótese só são aceitos se continuarem consistentes com o catálogo e suas fontes. O checksum prova a integridade da versão consumida; não confere assinatura a parecer fictício.

## Resultado didático inicial

| Estado derivado | Total | Uso da informação |
| --- | ---: | --- |
| Rascunho | 1 | falta iniciar revisão |
| Em revisão | 1 | falta segundo parecer |
| Necessita evidência | 2 | revisar metodologia ou buscar dados |
| Divergente | 2 | manter controvérsia visível; nenhuma adjudicação |
| Referência geral suportada **na simulação** | 2 | exercício de consenso entre personagens |
| Efetividade OEM por série verificada | **0** | bloqueada no repositório público |

**Nenhum parecer humano real foi executado.** Todos os estados terminam com `requiresRealTechnicalReview=true`, `oemSeriesVerified=false`, `approvedForOperationalUse=false` e `rootCauseConfirmed=false`.

## Integração com o benchmark

O benchmark do Ciclo 07 passou a validar o pacote de governança e anexar `technicalReviewGate` ao relatório:

- Oito afirmações têm referências rastreáveis.
- Dois exercícios produziram consenso fictício e dois registraram divergência.
- `realReviewerIdentityAuthenticated=false`.
- `realReviewerIndependenceVerified=false`.
- `oemSeriesEffectivityVerified=false`.
- `mayClaimFieldDiagnosticValidity=false`.
- `status=blocked_pending_independent_real_expert_review`.

**A conformidade de todos os fixtures e a concordância entre dois personagens fictícios não autorizam alegar acurácia diagnóstica real.**

## Executar

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m governance.review \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --packet governance/review-packet.v1.json \
  --output build/governance/technical-review.v1.report.json

python -m benchmarks.quality \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --review-packet governance/review-packet.v1.json \
  --output build/benchmarks/question-quality.v1.report.json
```

O CI executa essas rotas e bloqueia identidade de revisor falsamente verificada, assinatura fabricada, dois pareceres pelo mesmo personagem, citação órfã, relação entre método e disciplina errada, revisão circular, documento OEM ou série inseridos sem aprovação e habilitação automática de serviços. Também verifica o gate de qualificação do benchmark.

## Fronteiras de aplicabilidade e plano de evolução

Este código **não autentica seres humanos**. Uma futura transição para revisão real exigirá identidade corporativa, competências verificadas e matrizes de atribuição por disciplina, controle de conflito de interesse, acesso por perfil, trilha de autoria/timestamp não regravável, licenciamento de literatura e fonte de dados de campo aprovada.

A próxima etapa recomendada é construir um **ambiente de revisão técnica restrito** ou uma especificação de segurança para tal ambiente, com protocolo de dupla revisão, registro de divergências e adjudicação. Não se deve implementar autenticação fictícia em GitHub público nem armazenar laudos/telemetria corporativos neste repositório.

O objetivo deste ciclo não foi «validar tecnicamente as hipóteses». Foi **formalizar as condições necessárias para não alegar uma validade que ainda não existe**.
