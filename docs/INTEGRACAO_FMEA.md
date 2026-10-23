# Integração com FMEA Database Mining

**Fonte:** [fmea-database-mining](https://github.com/pedromaintenance/fmea-database-mining), README, manifests, docs/ARQUITETURA_DO_CONHECIMENTO.md, docs/MODELO_DE_DADOS.md, consulta em 22/10/2026.

## Acordo de responsabilidade

- **FMEA:** dono do catálogo, ontologia causal, validação mecânica, hipóteses, testes diferenciais e versionamento do pacote de conhecimento.
- **Superinteligence:** consumidora e integradora de pacotes **aprovados para exportação**, pesquisa de lacunas, composição com ativos/PCM e avaliação de respostas.
- **P.O.R.C.A.R.I.A.:** consumidor didático opcional, cujo gabarito não pode vazar na apresentação do caso.

A superinteligência **não edita silenciosamente** o FMEA, não promove hipóteses e não copia o banco integral.

## Inventário verificado

**Manifesto v1:** 19 famílias/modelos; 1.466 locais; 670 caminhos completos; 486 códigos de componentes; 66 danos; 81 causas; 518.832 combinações candidatas; 17 pacotes gerados.

**Biblioteca de simuladores v1.1:** 72 casos eletrônicos + 72 de óleo, 144 sintomas, 288 observações simuladas, 144 hipóteses, 54 entradas de índice de código (23 FMI), 39 referências de texto técnico.

**Preventivas v1.2:** extração de 1.018 tarefas distintas em 7 arquivos para 8 máquinas/famílias, 25 padrões genéricos; nenhuma contagem constitui ocorrência de falha.

**Cadeias e qualidade v1.3:** relações causais, efeitos possíveis, testes discriminantes, governança de revisão, controles de publicação e verificação contra deriva semântica. README v1.3.49 registra 16/25 regras PM com *bundles* ontológicos, 9 ainda pendentes; isso **não é** 16 FMEAs homologadas.

## Regra de classificação

| Entrada do FMEA | Tratamento na superinteligência |
| --- | --- |
| Hierarquia SAP/catalogada | metadado cadastral, **não** comprova arranjo de ativo individual |
| Combinação de dano/causa | `candidate`, não é fato nem frequência |
| Cenário de jogo | `simulation`, permitido para educação e avaliação |
| Cadeia causal com fonte | `technical_hypothesis` até critérios de revisão satisfeitos |
| Evidência de método planejado | `planned_test`, jamais `observed_test` |
| Revisor e efetividade OEM ausentes | `blocked_for_operational_specificity` |
| Resultado real autorizado | `operational_evidence` em ambiente privado, com auditoria |

## Implementação parcial — ciclo 02

O importador de leitura **já existe** em [`connectors/fmea_public.py`](../connectors/fmea_public.py) e usa [lock imutável](../connectors/fmea-source-lock.v1.json). A execução usa o snapshot de conteúdo público **1.0.0**, de **preview 1.3.12**, hash do registro upstream e commit fixo. A versão interna do FMEA pode evoluir independentemente. O consumidor preserva IDs do produtor em campos `fmeaId`/`sourceIds`; namespacing universal ainda é um trabalho de evolução, não uma conversão já implementada.

Esta versão somente produz um índice de hipóteses e recibo; **não implementa** `investigate(...)`, importação de eventos reais, sincronização automática, metrologia OEM ou revisão humana de campo. [Registro de execução e limites](CICLO_2026-10-22_IMPORTADOR_FMEA.md).

## Contrato de importação

1. Ler `data/governance/public-contract.v1.json` e política de exportação do FMEA.
2. Consumir **somente** o *preview/export* autorizado, identificado por `schema`, `contractVersion`, `contentVersion`, hash e revisão.
3. Aplicar **whitelist** de campos compatíveis e verificar IDs estáveis, status, tipos e fontes.
4. Normalizar identificadores para o espaço `fmea-mining:<sourceId>` **sem alterar os IDs de origem**.
5. Preservar o `nature`, `limitations`, `reviewStatus` e `applicability` em cada vínculo.
6. Rejeitar promoção semântica: `possible_unobserved` ≠ evento medido; `plausible` ≠ raiz confirmada; `test_planned` ≠ executado.
7. Gerar relatório de importação com versão, data, registros aceitos/rejeitados, lacunas e hash.
8. Não publicar nova versão do conhecimento nem atualizar consumidores automaticamente.

**Atenção:** versão do **conteúdo público = 1.0.0**, versão do **contrato público = 1.0.0**; o campo histórico **preview.version = 1.3.12**. A versão interna do repositório FMEA (1.3.49 no registro consultado) é independente destas três. Não há promoção operacional.

## Primeira funcionalidade

`investigate(symptom, modelContext, evidence[])` devolve:
- fatos e fontes;
- hipóteses concorrentes;
- testes aptos a distinguir hipóteses;
- contexto de segurança e pré-requisitos;
- o que os resultados favorável, desfavorável e inconclusivo significariam;
- lacunas (principalmente série, literatura OEM e baseline);
- recomendação **de investigação**, não ordem de reparo.

## Testes adversariais essenciais

- DTC ativo tomado como peça avariada → **reprovar**.
- Material rodante confundindo roda-guia e rolete → **reprovar**.
- Mudança conhecida da formulação de óleo tratada como falha mecânica → **reprovar**.
- Correlação entre código de dano SAP e código de causa usada como prova causal → **reprovar**.
- Método de teste cadastrado classificado como teste realizado → **reprovar**.
- Série/arranjo não informado, mas resposta apresenta torque/pressão OEM → **reprovar**.
- Hipótese B passa a ser menos plausível após contraprova, mas é descartada sem discriminação → **reprovar**.

A integração poderá gerar propostas de pesquisa para o FMEA; a aprovação permanece com a curadoria do repositório produtor.
