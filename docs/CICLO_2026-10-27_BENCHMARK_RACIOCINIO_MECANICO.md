# Ciclo 27 — Benchmark de raciocínio diferencial de manutenção

**Versão P&D:** 2.7.0 · **Data:** 27/10/2026

## Objetivo e fronteira de validade
Após os Ciclos 24–26, que aprofundaram a confiabilidade documental, este ciclo passa a medir o comportamento do **seletor de perguntas técnicas**, ainda sem alegar inteligência diagnóstica autônoma.

O programa trabalha com **24 cenários exclusivamente fictícios** (6 por domínio), nenhum baseado em dados de campo ou OEM específico. Os cenários cobrem **comandos finais**, **hidráulica**, **eletrônica/ECM** e **arrefecimento**. Arrefecimento amplia o escopo educacional pré-existente.

## Construção dos cenários
Em cada domínio há seis estados: narrativa contraditória; quatro estágios sucessivos de contexto documental ausente; e contexto narrativo completo que exige encaminhamento a especialista. Um mapa determinístico associa cada lacuna a uma pergunta. Cada domínio mantém **três hipóteses concorrentes, sempre não confirmadas**. Presença de contexto no exercício significa apenas **documento fictício assinalado**, jamais observação física, medição, configuração OEM verificada ou liberação de testes.

| Domínio | Questões em sequência (não são procedimentos executáveis) |
| --- | --- |
| Comando final | Identidade do lubrificante; histórico de troca; rastreabilidade da amostra; tendência comparável |
| Hidráulica | Carga e ciclo; condição térmica; circuito/arranjo; plano de medição aprovado |
| Eletrônica | Identidade ECM; ativo x registrado; cronologia; verificação independente autorizada |
| Arrefecimento | Carga/ciclo; rejeição de calor/fluxo de ar; contexto do fluido; plano de medição térmica aprovado |

Uma contradição registrada tem precedência sobre qualquer outra pergunta. Se os quatro campos estão presentes e não existem contradições, o sistema **não declara causa:** encaminha para revisão especializada.

## Verificação e métrica
- `benchmarks/mechanical-reasoning-cases.v1.json` — entradas com sintomas e disponibilidade documental fictícia; **sem campo contendo resposta correta**.
- `benchmarks/mechanical-reasoning-oracle.v1.json` — gabarito editorial elaborado separadamente, sem revisão de especialista independente.
- `benchmarks/mechanical_reasoning.py` — seletor determinístico, comparador, sumário por família, integridade e relatórios offline.
- `tests/test_mechanical_reasoning.py` — invariantes contra emissão de OS, condenação de componentes, falsa validação OEM, alteração de casos, fraude de gabarito/relatório e metamorfismo ao alterar contexto.
- `contracts/mechanical-reasoning-*.schema.json` — três contratos de estrutura e proibições operacionais.

**Métrica:** concordância `matched / total` com expectativa editorial. Não reportar `diagnosticAccuracy`, sensibilidade, especificidade, poder preditivo, qualidade causal em campo ou concordância com especialista: nada disso foi medido. O fato de seis casos por domínio resultarem em concordância perfeita apenas documenta que o seletor segue as regras autorais.

### Ameaças à validade
1. O mesmo projeto define o gabarito e as regras; existe risco de circularidade e sobreajuste editorial.
2. Os sintomas são descrições gerais sem grandezas, pressão/torque/temperatura, incerteza de medição ou situação operacional efetiva.
3. Os domínios não cobrem a heterogeneidade por fabricante/série, variantes de arranjo, firmware ou modos de falha reais.
4. Não foi feita avaliação humana cega nem comparação de decisões com equipes de campo.
5. O mecanismo testa **seleção de perguntas documentais**, não seleção de intervenções ou acurácia na identificação de causa.

## Reproduzir
```bash
python -m unittest discover -s tests -v
python -m benchmarks.mechanical_reasoning \
  --output build/benchmarks/cycle27-mechanical-reasoning.json \
  --html build/benchmarks/cycle27-mechanical-reasoning.html
```

## Próxima etapa recomendada
Criar um **conjunto de casos novos não vistos**, revisado independentemente por especialistas, com descrição de evidência, variantes e solução conhecida quando legalmente autorizada; registrar divergência interavaliadores e desempenho em subconjuntos difíceis. Somente em ambiente privado apropriado poderão entrar laudos reais, códigos de máquina ou literatura OEM licenciada. Este benchmark público não autoriza testar, desmontar, condenar peça, gerar ordem SAP ou liberar ativo.
