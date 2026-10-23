# Ciclo 07 — Benchmark de perguntas e validação metodológica inicial

**Versão:** protótipo de engenharia/P&D 0.7.0  
**Data:** 23/10/2026  
**Issue:** [#14](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/14)  
**Status científico:** benchmark **sintético, editorial, sem validação independente por especialista e sem dados de campo**.

## O que está sendo medido

O Ciclo 06 implementou um motor determinístico que propõe a próxima pergunta entre hipóteses concorrentes. O Ciclo 07 acrescenta um benchmark **regressivo versionado**, capaz de responder a perguntas verificáveis sobre o *software*:

- Diante da entrada sintética, a mesma pergunta é selecionada entre duas execuções?
- O seletor preserva as sete/quatro hipóteses em aberto?
- As lacunas de contexto foram reproduzidas, sem apagar condições contraditórias e sem tratar `not_applicable` como `available_simulated`?
- O método apresentado pertence ao catálogo, à disciplina e às referências declaradas?
- Os pré-requisitos e travas de segurança acompanham a pergunta?
- O sistema mantém explicitamente a abstenção, sem autorizar testes, ajuste ECM, OS, liberação ou identificação de componente defeituoso?

**Não está sendo medida** a capacidade de encontrar o defeito real. Percentuais de conformidade e taxa de abstenção nos fixtures **não são** sensibilidade, especificidade, valor preditivo, confiança probabilística ou eficiência operacional.

## Pacote de benchmark

O manifesto `benchmarks/question-quality.v1.json` traz **15 casos sintéticos**, cinco por domínio. Cada `CaseFixture` contém entrada tipada e um **oráculo de expectativa escrito separadamente**, incluindo par, método, estado, parte da pergunta esperada e obrigação de abstenção.

| Domínio | Cinco condições exercitadas |
| --- | --- |
| Comando final | aditivos sem histórico; troca de óleo documentada; cadeia de amostra contraditória; amostragem não aplicável; contexto integralmente fictício |
| Hidráulica | carga contraditória; dados desconhecidos; carga não aplicável; temperatura contraditória; contexto fictício completo |
| Eletrônica/ECM | DTC registrado sem contexto; DTC ativo em cenário com dados incompletos; horário contraditório; tipo de evento não aplicável; contexto fictício completo |

Uma etiqueta *ativo* ou *registrado* nos exemplos **não é um evento efetivamente lido por CAT ET**, assim como um teste de água ou pressão descrito não comprova ensaio em equipamento.

### Contratos independentes

- `contracts/case-fixture.schema.json`: entrada sintética, nota e expectativa vinculadas.
- `contracts/evidence-availability.schema.json`: distingue `unknown`, `available_simulated`, `contradicted` e `not_applicable`, exigindo referência fictícia para estados não desconhecidos.
- `contracts/expected-abstention.schema.json`: codifica expectativa de seleção e `mustAbstain=true`.
- `contracts/question-quality-rubric.schema.json`: catálogo de classes e interpretação permitida.
- `contracts/question-benchmark.schema.json`: envelope do manifesto com 15 casos.

As validações relacionais de IDs, fontes, expectativas e limites são executadas em Python além do JSON Schema.

## Rubrica de qualidade

`benchmarks/question-quality-rubric.v1.json` define nove classes de teste. Cada uma tem descrição, critério e status esperado; o validador recusa exclusão de categorias ou declarações de validação de campo.

| Classe de falha | O que avalia |
| --- | --- |
| `provenance` | identidade do caso, dados simulados e referências do método/FMEA |
| `ambiguity` | alternativas abertas e nenhum padrão hipotético promovido a resultado observado |
| `contradiction` | conflitos preservados e contexto usado no estado correspondente |
| `hypothesis_promotion` | nenhuma hipótese convertida em causa raiz ou peça condenada |
| `safety` | bloqueios a execução, intervenção, OS e liberação |
| `effectivity` | série e literatura OEM não consideradas verificadas |
| `prerequisite` | campos de contexto, condições de medição e gates de segurança preservados |
| `selection` | comparação com o oráculo editorial para par, método, pergunta e regra |
| `reproducibility` | duas saídas canônicas de seleção idênticas no mesmo caso |

O relatório `maintenance-superinteligence.question-benchmark-report.v1` inclui totais e contagens por classe, IDs de cada verificação falha, resultado por fixture, hash SHA-256 do manifesto/rubrica/matriz e resumo. A taxa de abstenção é apenas a razão **casos sem autorização operacional / casos simulados**; o quociente não mede segurança real em campo.

### Limitação técnica dos hashes

O relatório usa SHA-256 para distinguir conteúdo e detectar mudança. O hash **não** é assinatura digital de um especialista, certificação de origem nem cadeia de custódia imutável. Qualquer agente com permissão de alterar manifesto e relatório pode recalcular hashes; futura validação de dados reais exigirá controles externos.

## Seleção sem estatística inventada

A regra do Ciclo 06 permanece inalterada: `reconcile_contradiction` antes de `ask_missing_context`, seguido de `review_applicability` e `prepare_human_method_review`, com desempate editorial por ordem de pares/métodos.

O benchmark verifica a correspondência com esta lógica e com o oráculo sintético. Não cria pesos de disponibilidade, risco, probabilidade ou custo de manutenção. A afirmação **«melhor teste para detectar a falha»** não foi validada; a saída continua sendo **«próxima pergunta para resolver bloqueios de investigação»**.

## Execução

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m benchmarks.quality \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --manifest benchmarks/question-quality.v1.json \
  --rubric benchmarks/question-quality-rubric.v1.json \
  --output build/benchmarks/question-quality.v1.report.json
```

O runner valida **os bytes originais** do snapshot público FMEA Mining conteúdo 1.0.0 contra o SHA-256 fixado, valida a biblioteca e a matriz contra esse pacote e somente então gera resultados. Regressão no oráculo devolve código de falha; alteração indevida de origem, revisão ou fonte causa rejeição imediata.

No GitHub Actions, o relatório é publicado como artefato temporário. Testes adversariais substituem deliberadamente hipóteses, lacunas, vínculos de fonte e permissões para assegurar que cada classe de falha seja detectada.

## Critérios de aceitação

- CI verde: quinze casos passam, nove classes com cobertura e nenhuma promoção causal.
- Cada caso é reexecutado com resultado canônico idêntico; nenhuma máquina ou sistema externo consultado.
- `diagnosticAccuracyMeasured=false`, `technicalExpertReviewComplete=false`, `operationalValidation=false` explicitamente no relatório.
- O relatório rejeita declarações de diagnóstico ou eficácia de campo disfarçadas como metadados.

## Limitações e próximos passos

Os quinze oráculos são **concebidos pela equipe do projeto** e não tiveram avaliação cega de especialistas, casos reais adjudicados nem estudos de sensibilidade/especificidade. A prova atual é de regressão de regras e segurança de contrato, não de *correção mecânica* das relações condicionais.

Uma etapa futura de validação deverá: construir um corpus autorizado de casos anonimizados em armazenamento restrito; definir protocolo de adjudicação independente entre engenheiros; registrar discordâncias, revisões da literatura por série, condições e testes executados; separar benchmark de desenvolvimento do corpus de avaliação; e então avaliar discriminadores, calibração e cobertura com denominadores válidos.

**Próximo ciclo sugerido:** governança de revisão técnica e um fluxo de qualificação de `Claim`/método, com duas avaliações independentes e rastreabilidade da literatura, antes de qualquer alegação de confiabilidade diagnóstica.
