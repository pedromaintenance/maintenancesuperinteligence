# Ciclo 15 — Árvores de investigação com abstenção obrigatória

**Data:** 24/10/2026. **Versão P&D:** 1.5.0. **Issue:** [#30](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/30).

## Objetivo de engenharia

Transformar perguntas discriminantes e contraexemplos dos Ciclos 13–14 em uma navegação didática das hipóteses, **sem atribuir resultados de campo àquilo que é somente uma possibilidade**. A função do mecanismo é demonstrar qual informação seria necessária antes de justificar uma investigação técnica mais específica.

As árvores produzidas representam **um conjunto de perguntas por caso**, não uma sequência executável de manutenção. Os ramos condicionais conduzem a um checkpoint humano e **não** reduzem o conjunto de hipóteses. As transições reais de cada caso sintético permanecem em **abstenção**.

## Entregas estruturais

- `trees/spec.v1.json`: fixa os quatro casos, perguntas iniciais, estados de contexto e quantidade de pares.
- `trees/investigation.py`: valida a origem do cenário, reúne hipóteses, perguntas, três possibilidades condicionais por par, contraexemplos, rastreabilidade das fontes, decisão de abstenção e gate de revisão humana.
- `trees/presentation.py`: produz HTML standalone com seções `details/summary` nativas, sem JavaScript ou formulário. Cada comparação apresenta três ramos contrafactuais, duas explicações alternativas e requisitos de revisão.
- `casefiles/integrated.py`: anexa a coleção `investigationTrees` ao JSON original dos quatro dossiês e acrescenta a opção de CLI `--tree-html`.
- Contratos JSON Schema: `InvestigationNode`, `EvidenceGate`, `BranchInterpretation`, `HumanReviewCheckpoint`, `DecisionTrace`, `UnresolvedHypothesisSet`, envelope de árvore e coleção.

O motor reaproveita a proveniência original dos métodos e fontes públicas. Um SHA-256 da especificação sintética é incluído no relatório para tornar mudanças identificáveis, mas **não** representa assinatura humana ou prova de integridade externa.

## Casos e estados esperados

| Caso | Pergunta de entrada | Estado fictício | Encaminhamento |
| --- | --- | --- | --- |
| Comando final 777E / aditivos | FD-P01 | `not_measured` | Levantar identificação do fluido e histórico antes de interpretação |
| Hidráulica / carga contraditória | HYD-P01 | `contradicted` | Reconciliar condição de carga antes de qualquer atribuição de falha |
| ECM / DTC registrado | EL-P01 | `not_measured` | Identificar módulo/contexto e comparar evidências independentes |
| ECM / DTC ativo | EL-P02 | `not_measured` | Distinguir código/tempo de registro e condição atual, com revisão de aplicabilidade |

São **4 árvores educacionais**, **13 nós de comparação instanciados**, **39 ramos condicionais não observados** e **26 contraexemplos exibidos**. Os dois casos ECM compartilham parte da base de pares. Permanecem **19 instâncias de hipóteses abertas**, zero ensaios e zero causas raiz comprovadas.

### Semântica técnica dos estados

- `supports` e `weakens` descrevem apenas o sentido **condicional** que uma observação validada *poderia* ter. Não representam um resultado presente na máquina.
- `not_measured`: não há resultado físico. A ausência de teste não é um resultado negativo.
- `contradicted`: os próprios metadados de contexto entram em conflito, como na carga hidráulica; deve-se reconciliar a origem e a comparabilidade.
- `inconclusive`: o contexto não é suficiente para discriminar.
- Qualquer um desses três últimos estados produz `abstain_pending_verified_evidence`, com `hypotheticalBranchesTaken=0`.

O algoritmo **não calcula probabilidade, pontuação de dano, sensibilidade, especificidade, ganho informacional nem frequência de falha**, e não escolhe desfecho provável a partir de lacunas. A ordem é herdada da matriz editorial versionada.

## Gates de revisão

O `HumanReviewCheckpoint` exige, futuramente e em ambiente aprovado:

1. Literatura OEM vigente e aplicável a modelo, arranjo/configuração e revisão.
2. Método e condições seguras para intervenção, isolamento e pessoal competente.
3. Evidência física comparável, rastreável e de qualidade revisada.
4. Conciliação de contradições e separação entre sintomas relatados e medições.
5. Avaliação por profissional de engenharia independente, com alçada pertinente.

No projeto público, `allProofsVerified=false`, `humanReviewAuthenticated=false`, `oemEffectivityVerified=false` e `physicalMethodAuthorized=false` são invariantes. Nenhum gate torna possível executar teste, abrir OS, comandar ECM ou liberar máquina.

## Execução local

```bash
python -m unittest discover -s tests -v

python connectors/fmea_public.py --fetch --output build/fmea-public

python -m casefiles.integrated \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --output build/trees/technical-cases.v1.json \
  --tree-html build/trees/investigation-trees.v1.html
```

O HTML gerado pode ser aberto offline em navegador, usando o clique nativo dos elementos expansíveis para comparar possibilidades. Não recebe dados, não realiza login e não faz requisições de rede. Para verificar resultados técnicos, o CI confronta o relatório com a especificação e mantém os mesmos vínculos de métodos, perguntas e hipóteses dos ciclos anteriores.

## Limites e segurança

Este ciclo **não homologa** procedimentos, não acessa dados SAP, CAT ET, VisionLink, informações de funcionários, literatura OEM licenciada ou histórico real de equipamento. Qualquer informação real deve ser processada exclusivamente em infraestrutura corporativa adequada, após autorização e revisão, e não importada para o repositório público.

Os testes adversariais cobrem ramos falsamente marcados como observados, elevação de causa, exclusão de hipótese, liberação ou abertura de OS indevida, falso parecer OEM, seleção trocada e alteração de transição. CI verde significa **consistência sintética**, não acurácia diagnóstica nem autorização de operação.

**Próximo passo recomendado:** modelar exercícios didáticos de conversão de sintomas e lacunas em notificações tecnicamente bem delimitadas, diferenciando descrição de sintoma, hipótese, escopo de inspeção e risco de postergação, sempre sem registrar dados corporativos no repositório público.
