# Ciclo 14 — Evidência qualitativa discriminante e contraexemplos mecânicos

**Data:** 24/10/2026 · **Versão de P&D:** 1.4.0 · **Issue:** [#28](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/28)

## Objetivo e escopo

O Ciclo 13 gerou quatro dossiês de investigação com 19 instâncias de hipóteses abertas e perguntas de discriminação. O Ciclo 14 explicita **quais observações poderiam alterar a interpretação de cada hipótese** e, sobretudo, quais **explicações alternativas e lacunas** impedem conclusões prematuras. 

A matriz `evidence/qualitative-discrimination.v1.json` tem **10 comparações distintas**, que recebem 30 padrões condicionais e **20 contraexemplos escritos especificamente para os mecanismos considerados**. Ao utilizá-la nos quatro dossiês (o contexto eletrônico aparece em dois cenários), aparecem **13 comparações e 26 contraexemplos instanciados**.

**Nenhum desses registros constitui medição de máquina.** Os padrões são contrafactuais editoriais, sem ensaio, validade diagnóstica estatística, homologaçăo OEM ou observação de campo. O algoritmo nunca atribui pontuação de probabilidade, exclui hipótese ou cria uma decisão operacional.

## Como interpretar os estados

A distinção central da biblioteca é entre **resultado que poderia ocorrer** e **resultado que de fato foi observado**:

| Estado | Onde pode aparecer | Interpretação correta |
| --- | --- | --- |
| `supports` | Somente hipótese **condicional**, no cenário “SE tal resultado fosse observado” | Tornaria uma alternativa merecedora de investigação; não confirma mecanismo |
| `weakens` | Somente hipótese **condicional** | Enfraqueceria explicação sob pressupostos validados; não exclui defeito |
| `inconclusive` | Padrão condicional ou estado real do contexto **fictício** | Os dados não discriminam mecanismos, ou o contexto disponível não equivale a ensaio |
| `contradicted` | Metadados de contexto sintético conflitando entre fontes | Necessário reconciliar a origem e comparabilidade; não prova resultado de teste |
| `not_measured` | Informações contextuais ainda ausentes | Não se trata de teste negativo e **não pode** ser usado para enfraquecer hipótese |

A matriz marca toda observação potencial `counterfactual_not_observed`. Nenhum relatório contém `observedOutcome`, resultado de instrumento ou `hasBeenObserved=true`. A avaliação executada usa exclusivamente os estados `inconclusive`, `contradicted` e `not_measured`, com `observedSupportCount=0`, `observedWeakeningCount=0` e `hypothesesExcluded=0`.

A mesma regra vale para `CausalLevelAssessment`: **sintoma relatado ≠ efeito medido ≠ mecanismo imediato comprovado ≠ causa raiz determinada**. O exercício apenas torna a progressão causal explícita.

## Comparações mecânicas por domínio

### Comando final de caminhão CAT 777E — simulação de óleo e componentes

1. `FD-P01` compara **mudança de formulação** com possível problema de lubrificação. Uma troca de produto pode modificar o perfil de aditivos sem dano; por outro lado, óleo com aditivos semelhantes não impede desgaste ou contaminação independente.
2. `FD-P02` compara **erro de coleta/identificação** com água/ingresso. Não reproduzir água na segunda amostra pode ter diferentes explicações; reproduzir água não aponta qual vedação, respiro ou rota falhou.
3. `FD-P03` compara **ruído externo** com hipótese de dano interno. Propagação estrutural e ruído de conjunto vizinho exigem cuidado antes de localizar o redutor; partículas do bujão não condenam rolamento sem morfologia e inspeção.
4. `FD-P04` contrapõe hipóteses de **ingresso externo e fragmentos internos**. Poeira e desgaste podem coexistir; partícula magnética não identifica automaticamente um componente.

### Hidráulica

1. `HYD-P01`: possível bomba versus válvula/restrição. Pressão isolada, sem esquema e carga comparáveis, não diferencia plenamente as origens.
2. `HYD-P02`: demanda/carga versus deficiência de bomba. Mudança de carga pode explicar lentidão sem avaria; manter carga estável não identifica automaticamente defeito da bomba.
3. `HYD-P03`: influência térmica versus válvula. Temperatura pode ser causa, efeito secundário ou condição de operação; sem método aplicável o circuito não fica caracterizado.

**Segurança:** todos os métodos hidráulicos continuam `not_performed`; ensaios precisariam de isolamento, tratamento de energia hidráulica armazenada, instrumentos apropriados, procedimento OEM por máquina e avaliação de riscos.

### ECM / monitoramento eletrônico

1. `EL-P01`: circuito/sensor versus fenômeno físico monitorado. Duas indicações concordantes podem ter a mesma origem de erro; uma medição independente precisa ter unidades e método compatíveis.
2. `EL-P02`: ocorrência ativa ou transitória versus código histórico. A ausência de evento ativo na consulta não comprova que nunca ocorreu; a presença isolada não prova persistência ou causa.
3. `EL-P03`: evento físico versus condição transitória. Repetições podem refletir alimentação, circuito ou contexto e não necessariamente dano físico.

O dossiê mantém distintos os **eventos genéricos registrados e ativos** em seus dois casos simulados. Não há acesso CAT ET, identificação de software ECM real, reset, teste invasivo ou autorização de ajuste.

## Rastreabilidade

A biblioteca `evidence/qualitative.py` valida:

- Os 10 `pairId` pertencem exatamente à matriz `methods/discrimination-matrix.v1.json` e preservam ambos `hypothesisId`, `methodId` e `requiredContextKey`;
- Os `sourceIds` são extraídos dos **métodos do catálogo público** e devem existir no registro de fontes, sem inclusão de suposto procedimento por série;
- Cada par contém três padrões exatamente correspondentes aos padrões publicados na matriz anterior (primeiro, segundo e indeterminado), com estados e ordem fixados;
- Cada par apresenta dois contraexemplos distintos e declara `cannotExcludeHypotheses=true`, `causalMechanismVerified=false`;
- Cada avaliação dos quatro casos preserva `testsPerformed=0`, `observedPhysicalEvidence=false`, `fieldResult=null`, hipóteses abertas e bloqueios dos Ciclos 08–12;
- `sha256` da entrada qualitativa passa a aparecer na proveniência do dossiê junto aos hashes do snapshot FMEA, catálogo e benchmark.

O SHA-256 comprova que duas cópias públicas são iguais; **não** comprova origem de campo, autoria profissional ou efetividade OEM.

A interface HTML standalone apresenta, por par: hipóteses ainda abertas, estado de contexto, resultados que *poderiam* diferenciá-las, alternativas que limitam a inferência e lacunas de rastreabilidade. O texto é escapado antes de gerar células HTML e não há scripts, formulários ou acesso externo.

## Novos contratos JSON Schema

Foram adicionados os seguintes contratos:

1. `evidence-claim.schema.json` — naturezas editorial e não comprovada da afirmação.
2. `evidence-provenance.schema.json` — metadados sintéticos e fontes públicas gerais, sem efetividade OEM.
3. `conditional-evidence-pattern.schema.json` — padrão hipotético que nunca se transforma automaticamente em medição.
4. `alternative-explanation.schema.json` — contraexemplo que mantém alternativas abertas.
5. `causal-level-assessment.schema.json` — distinção sintoma, efeito, mecanismo e causa raiz.
6. `discriminating-observation.schema.json` — par, contexto, padrão, método, segurança e interpretação.
7. `qualitative-evidence-pair.schema.json` — contrato editorial de cada par.
8. `qualitative-evidence-matrix.schema.json` — envelope da matriz.
9. `qualitative-oracle.schema.json` — resultados sintéticos esperados por caso.

Também foi incorporado `benchmarks/qualitative-oracle.v1.json` como fonte independente de expectativas editoriais: quatro casos, seleção de pergunta e estados por par, sem alegação de eficácia mecânica. Seu SHA-256 é registrado no relatório. Testes adversariais rejeitam tratar falta de observação como resultado negativo ou apagar uma contradição do caso hidráulico.

Foram também atualizados os contratos de dossiê técnico para exigir o objeto `qualitativeEvidence` e o estado global de zero evidências observadas e zero exclusões.

## Execução

```bash
python -m unittest discover -s tests -v

python connectors/fmea_public.py --fetch --output build/fmea-public

python -m casefiles.integrated \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --fixture casefiles/technical-cases.v1.json \
  --output build/casefiles/integrated-differential.v1.json \
  --html build/casefiles/integrated-differential.v1.html
```

O GitHub Actions testa a matriz contra as fontes públicas e o snapshot FMEA pinado, rejeita falsificação de evidência medida ou descarte automático de hipótese e publica os dois dossiês de saída (JSON e HTML) exclusivamente como artefatos temporários.

## Limites e próximo refinamento

- **Não validamos poder discriminante de testes no campo.** Nem `supports` nem `weakens` têm probabilidades, sensibilidade, especificidade ou taxas de falso positivo.
- **Não oferecemos sequência operacional de ensaio.** Limites físicos, pressão, vazão, desgaste e métodos dependem de OEM por configuração e risco de tarefa.
- **Não autorizamos liberar máquina, criar OS, modificar ECM, condenar componente ou importar dados privados**.
- A seleção original de perguntas permanece um ordenamento editorial de lacunas/contradições, não uma ordenação otimizada por ganho de informação.

**Próxima etapa recomendada:** verificar completude das cadeias causais e sua apresentação como árvore de decisão didática, com pontos de abstenção e revisão humana. Isso pode ajudar mecânicos e inspetores a formular notificações melhores sem inventar diagnósticos.
