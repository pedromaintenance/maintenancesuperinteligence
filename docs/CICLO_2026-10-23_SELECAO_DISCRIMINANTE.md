# Ciclo 06 — Matriz discriminante e próxima pergunta de investigação

**Data:** 23/10/2026  
**Versão:** protótipo P&D v0.6.0  
**Issue:** [#12](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/12)  
**Natureza:** exclusivamente **pesquisa didática e simulada**, não serviço técnico executável.

## Qual problema este ciclo resolve?

O Ciclo 05 responde **quais métodos conceituais existem**. O Ciclo 06 começa a responder **qual informação ainda precisa ser obtida para distinguir duas hipóteses concorrentes**, sem converter uma associação teórica em causalidade provada.

A saída não é «realize o ensaio X». É «a próxima pergunta a resolver, dadas as lacunas e contradições registradas no cenário, é Y». O seletor não calcula ganhos de informação, probabilidade, custo, duração ou risco residual; a sequência entre perguntas é **uma convenção editorial auditável**, até que haja base empírica para outra decisão.

## Três famílias simuladas

| Família | Hipóteses em aberto | Comparações | Enfoque |
| --- | ---: | ---: | --- |
| Comando final CAT 777E | 7 | 4 | formulação × degradação; coleta × ingresso de água; ruído externo × rolamento; ingresso abrasivo × fadiga |
| Hidráulica genérica | 4 | 3 | capacidade de bomba × válvula; contexto de carga × bomba; efeito térmico × válvula |
| Diagnóstico eletrônico ECM/DTC | 4 | 3 | circuito de sensor × alteração física; intermitência × registro histórico; alteração física × intermitência |

**Todas são hipóteses didáticas não comprovadas.** A família de comando final usa como identificadores as quatro cadeias `FC-FD` do snapshot FMEA público congelado e as três alternativas próprias do piloto. A matriz de vínculos e interpretações é **editorial deste projeto**, não alegação de que o FMEA atestou resultados discriminantes. Hidráulica e eletrônica utilizam apenas métodos genéricos do catálogo — não possuem FMEA vertical validado nem caso de frota.

## Elementos de domínio

- **HypothesisPair:** dois mecanismos alternativos, não a mesma hipótese referenciada duas vezes, com pergunta de investigação e pelo menos dois métodos conceituais da disciplina correspondente.
- **DiscriminationMatrix:** dez pares versionados, métodos rastreados ao catálogo e três **padrões hipotéticos** por par: indício compatível com A, compatível com B, ou inconclusivo. Os padrões são condicionais; `hasObservedOutcome=false`.
- **TestPrecondition / ContextState:** campo indispensável no cenário com estado `unknown`, `available_simulated`, `contradicted` ou `not_applicable`. A ausência de campo equivale a `unknown`; `contradicted` exige conciliação. Nenhum estado significa que OEM ou instrumento foram aprovados.
- **TestSelectionRationale:** identifica par, método, pergunta e regra de desempate. O motor jamais produz valor-limite, executa ensaio, condena peça ou autoriza ECM/SAP.

## Lógica de escolha

O motor conserva todos os pares em aberto e emite alternativas. Para selecionar **uma pergunta inicial**:

1. Prioriza o par que contém contexto **contraditório** (investigar divergência de origem e registro).
2. Depois prioriza **desconhecidos** (identificar lacunas antes de interpretar medidas).
3. Depois examina contexto marcado **não aplicável** (exige justificativa, não o considera aprovado).
4. Se tudo foi preenchido **com dados fictícios**, prepara pergunta de revisão humana do método, ainda sem autorização OEM.

Empates seguem a ordem editorial dos pares e dos métodos no catálogo. Isso é uma **regra determinística de workflow**, e não classificação clínica/estatística da capacidade real de discriminação, nem ranking de criticidade operacional. A afirmação de que um teste é «melhor» depende de estudos de acurácia, custo, segurança e condições não disponíveis neste repositório.

## Exemplos de saída

**Hidráulica:** um relato fictício de cilindro lento sob carga não caracterizada não prova baixa vazão da bomba. O cenário possui `load_context=contradicted`; a próxima pergunta é **conciliar as fontes de carga**, antes de comparar pressão ou vazão. O sistema mantém em aberto bomba, válvula, demanda e efeito térmico.

**Eletrônica:** um DTC de exemplo sem identificação de ECM, estado ativo/histórico e contexto temporal não permite concluir que sensor, chicote ou ECM estão danificados. A próxima pergunta é obter a identificação e o contexto do evento. Os dois estados possíveis não são tratados como defeito confirmado.

**Comando final:** aditivos diferentes em resultado de óleo não são evidência independente de fratura, desgaste ou dano em rolamento; primeiro é necessário reconciliar produto/baseline e histórico.

## Proteções e fontes

O seletor usa a biblioteca conceitual do Ciclo 05, com 14 métodos e registros de fontes. Para execução CLI, **sempre verifica os bytes originais** do snapshot FMEA contra o SHA-256 fixado no lock do Ciclo 02, antes de validar as hipóteses e os métodos. A família `final_drive` precisa conter exatamente as quatro cadeias públicas e as três alternativas do piloto, sem causa confirmada.

As demais famílias usam os registros metodológicos gerais da biblioteca, **não** um suposto manual de ensaios por série. Os campos de série/arranjo, publicação OEM e revisão continuam vazios; `mayRunTests=false`, `mayModifyECM=false`, `mayCreateWorkOrder=false`, `mayReleaseEquipment=false`.

A matriz não coleta dados reais, números de série ou leituras protegidas. Os únicos `sourceRef` aceitos nos estados de contexto são marcadores didáticos `SIM-*`.

## Executar e reproduzir

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m methods.discrimination \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --case examples/discrimination_777e.json \
  --output build/discrimination/777e.selection.json

python -m methods.discrimination \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --case examples/discrimination_hydraulics.json \
  --output build/discrimination/hydraulics.selection.json

python -m methods.discrimination \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --case examples/discrimination_electronics.json \
  --output build/discrimination/electronics.selection.json
```

Arquivos principais: `methods/discrimination-matrix.v1.json`, `methods/discrimination.py`, exemplos `examples/discrimination_*.json`, quatro contratos JSON Schema e `tests/test_discrimination.py`. O CI executa os três cenários e rejeita uma falsificação de resultado observado.

## Lacunas e continuidade

**Não foi demonstrada eficácia diagnóstica real**, comparação de sensibilidade/especificidade ou desempenho de equipamento. Também não foram produzidos procedimentos de teste CAT 777E por número de série, esquemas hidráulicos de máquina, métodos de calibração ECM ou acesso SAP.

Antes de aplicar à engenharia de campo, ainda será necessário vincular literatura OEM efetiva, configurar dados reais sob autorização e sigilo, medir a capacidade de discriminação em casos validados e submeter a decisão à revisão humana.

**Próxima direção proposta:** ciclo 07 de validação metodológica, biblioteca de casos adversariais e avaliação da qualidade das perguntas, com critérios verificáveis para aceitar/rejeitar cada ligação causal. A lógica futura de custo, risco e disponibilidade deverá usar variáveis medidas e fontes, nunca pesos arbitrários.
