# Ciclo 48 — Consolidação da fila de PRs e prontidão para estudo independente

**P&D v4.8.0 · 05/11/2026 · proposta em branch dependente do Ciclo 47.**

> **NO GO para estudo com pessoas, utilização de casos reais sem autorização, conclusão de competência mecânica e quaisquer ações operacionais.** Este ciclo organiza o trabalho necessário para obter evidências externas; ele NÃO fornece essas evidências.

## 1. Decisão técnica

Os Ciclos 43–47 foram implementados em PRs empilhados e seus workflows específicos e gerais passaram nos commits verificados em 05/11/2026. Entretanto, os PRs permanecem *draft*, abertos e sem revisão independente de código registrada como aprovada. A `main` ainda está no Ciclo 42.

O status **CI aprovado** significa que os testes automáticos existentes passaram. Não significa código aceito, validade diagnóstica, gabarito independente, autenticação de especialistas, autorização de campo ou elegibilidade para experimento humano.

**A decisão do Ciclo 48 é não mesclar automaticamente uma cadeia de cinco PRs que não passou por revisão formal.** Criamos um instrumento reproduzível que identifica a ordem correta de integração, fixa o recorte do GitHub e especifica as lacunas que precisam ser resolvidas por responsáveis humanos e institucionais.

## 2. Inventário de integração — snapshot de 05/11/2026

| PR | Ciclo | Base | Situação | Ação técnica seguinte |
| --- | --- | --- | --- | --- |
| #69 | 43 — auditoria de maturidade | `main` | Draft, CI verificado, não mesclado | Revisão humana do contrato de evidência e dos testes |
| #70 | 44 — poder discriminante simbólico | Branch do #69 | Draft, CI verificado, não mesclado | Validar interpretação teórica e limites da comparação |
| #71 | 45 — comparação cega pareada | Branch do #70 | Draft, CI verificado, não mesclado | Rever custódia de casos, randomização, alias e segurança |
| #72 | 46 — fila de adjudicação | Branch do #71 | Draft, CI verificado, não mesclado | Rever heurísticas, integridade e diferenciação de alçada |
| #73 | 47 — red team de mascaramento | Branch do #72 | Draft, CI verificado, não mesclado | Rever falsos negativos, proveniência e instruções adversariais |

**Dependência:** #69 → #70 → #71 → #72 → #73 → #74 (este ciclo, quando aberto).

A ordem de revisão e eventual integração é por dependência, nunca por número isolado. Depois de integrar um PR, deve-se reavaliar a base do seguinte, atualizar a branch conforme política do repositório e reexecutar seus checks. Um teste verde num SHA anterior não garante sucesso após rebase/merge.

A informação acima está congelada em `governance/cycle48-study-readiness.v1.json`, com os cinco SHAs conhecidos. O programa é **offline** e não detecta mudanças futuras automaticamente. Para atualizar a fotografia, um responsável deve consultar novamente o GitHub e produzir uma nova versão; não converter a fotografia em fonte de verdade eterna.

## 3. Treze evidências externas obrigatórias

| Grupo | Gate | Evidência esperada |
| --- | --- | --- |
| Engenharia de software | `pr_chain_review` | Revisões humanas aprovadas, ordem de merge e status pós-integração |
| Método científico | `baseline_freeze` | Comparadores, versões e hipóteses congelados antes da coleta |
| Jurídico e governança | `legal_case_authorization` | Direitos de uso, finalidade, retenção e confidencialidade por caso |
| Custódia | `independent_custodian` | Custodiante independente e responsável identificado por termo externo |
| Segurança informacional | `data_privacy_access` | Ambiente privado, controle de acesso, gestão de segredo e auditoria |
| Qualidade de dados | `corpus_leakage_review` | Auditoria de linhagem e vazamento semântico entre conjuntos |
| Revisão humana | `reviewer_identity_independence` | Duas identidades humanas distintas, conflitos e aceite |
| Conhecimento técnico | `mechanical_competence` | Competência pertinente aos sistemas e limites de responsabilidade |
| OEM e engenharia | `oem_case_effectivity` | Aplicabilidade de literatura por modelo, série e configuração |
| SST | `safety_and_stop_rules` | Regras de suspensão, riscos, veto e não intervenção |
| Neutralidade do experimento | `blinding_qualified_audit` | Auditoria humana das perguntas, sem vazamentos de origem |
| Estatística | `design_statistics_approval` | Tamanho de amostra justificado, estratos, denominadores e análise |
| Adjudicação | `adjudicator_independence` | Terceiro revisor autenticado, separado dos dois julgadores |

São **13/13 gates não verificados** neste momento. O arquivo registra o perfil do responsável e o artefato solicitado, mas não armazena identidade, laudo, credencial, caso real ou documento OEM protegido.

Nenhum gate pode passar de `unverified_requires_external_evidence` para aprovado no instrumento atual. Uma futura capacidade de homologação exigiria novo contrato, custodiante autorizado e evidências autenticadas fora do repositório público.

## 4. Esboço de pré-registro — cinco métricas com denominador explícito

O estudo futuro deverá perguntar se a seleção de perguntas favorece a investigação mecânica, mantendo controle de risco e segurança. Uma possibilidade, **ainda não aprovada como plano estatístico**, é:

1. **Preferência final por pergunta experimental** — casos admissíveis com escolha experimental / casos com escolha admissível base ou experimental. Dissensos pendentes, empates e abstenções não viram preferências.
2. **Concordância bruta interavaliadores** — casos com duas respostas iguais / casos com duas avaliações completas. Não confundir concordância com acerto.
3. **Incidência de alertas de segurança** — casos com ao menos um alerta / casos com duas avaliações completas. Ausência de alerta não prova segurança.
4. **Taxa de abstenção** — casos com uma ou mais abstenções / casos com duas avaliações completas. Abstenção pode ser tecnicamente correta.
5. **Rejeição de cegamento** — casos rejeitados após auditoria humana / casos submetidos à auditoria humana. Não equiparar o filtro lexical do Ciclo 47 a essa auditoria.

Até a aprovação externa, essas cinco métricas são **propostas de desenho**. Sem número e composição de casos, justificativa de N, dispersão, critérios de parada, perdas e adjudicação, não existe estimativa válida de resultado nem parâmetro para afirmar superioridade do seletor.

## 5. Ferramenta reproduzível

`governance/cycle48_readiness.py` valida o inventário dos PRs, a ordem das bases, os SHAs conhecidos, os documentos presentes, os 13 gates e o desenho de análise ainda não congelado. Emite JSON e Markdown de prontidão com hashes SHA-256 dos documentos do checkout.

```bash
python -m unittest tests.test_cycle48_readiness -v

python -m governance.cycle48_readiness \
  --output build/governance/cycle48-readiness.json \
  --markdown build/governance/cycle48-readiness.md
```

Contratos:

- `contracts/cycle48-study-readiness.schema.json`
- `contracts/cycle48-readiness-report.schema.json`

O workflow `.github/workflows/cycle48-study-readiness.yml` só consome metadados públicos da árvore Git e verifica a ausência de afirmações indevidas. Pode disponibilizar exclusivamente o resumo público congelado, jamais evidências privadas de pessoas, casos, gabaritos ou chaves. **Os hashes de fontes locais não são assinatura digital, revisão humana ou autenticação de titularidade.**

## 6. Riscos, prioridades e sequência executável

**Primeira fase — code review:** manter PRs #69–73 como draft até revisão do código, do checklist de segurança, das dependências e da documentação. Não atualizar `main` por força de CI somente.

**Segunda fase — governança externa:** definir quem pode custodiar casos; consultar jurídico/SST sobre finalidade, titularidade, consentimento e risco; estabelecer onde e como os dados serão processados sem publicar documentos protegidos.

**Terceira fase — estudo científico:** congelar protocolo, baseline, amostra, critérios de veto, métricas e plano de análise antes de ver qualquer parecer. Identificar e qualificar revisores e terceiro adjudicador independentes. Validar cegamento de forma humana e documental.

**Quarta fase — apenas depois de autorizações verificadas:** estudar casos lícitos, inéditos e devidamente contextualizados; preservar hipóteses alternativas; quantificar divergências e abstenções. Nunca confundir revisão de perguntas com autorização de reparo ou verificação de causa raiz.

### Limitação estrutural descoberta

Uma cadeia longa de módulos com dados sintéticos pode demonstrar **consistência interna** sem acrescentar validade externa. Cada camada tem seu próprio risco de falhas ou falsa sensação de prontidão. O Ciclo 48 interrompe deliberadamente a multiplicação de *benchmarks* autorais, concentrando o ganho em rastreabilidade de integração e redução de lacunas institucionais.

**Decisão formal:** `no_go_review_pr_stack_and_obtain_independent_study_evidence`.
