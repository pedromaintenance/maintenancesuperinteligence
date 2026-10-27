# Ciclo 23 — Cobertura estrutural e explicação de reaberturas

**27/10/2026 · P&D v2.3.0 · Issue [#46](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/46)**

## Objetivo

Verificar a completude da propagação de reaberturas **de controles documentais** no grafo público dos Ciclos 20–22, fornecendo caminhos legíveis desde cada raiz até os controles atingidos. O problema é de **alcançabilidade em grafo dirigido**, não de probabilidade de falha, comportamento físico de componentes, eficácia de inspeções ou autorização de manutenção.

**Resultado de P&D esperado:** `no_go`; nenhuma validação OEM por série, autenticação de pessoa, aprovação da manutenção ou evidência física é introduzida.

## Corpus e critérios de cobertura

O grafo canônico contém **13 controles, 17 arestas**, todas dirigidas de pré-requisito para controle dependente. O fixture `pilot/reopen-coverage.v1.json` cobre:

| Família de regressão | Casos | Finalidade |
| --- | ---: | --- |
| Raiz individual | 13 | Confirmar fecho transitivo de cada um dos controles |
| Par não ordenado de raízes | 78 | Confirmar união de alcances e impedir perda/duplicação indevida |
| Mudança de contexto | 3 | Revogação de identidade, troca hipotética da revisão OEM e alteração de configuração |
| Conflitos editoriais do Ciclo 22 | 6 | Reproduzir raízes e justificativas dos seis conflitos documentais |
| **Total** | **100** | Alcançabilidade exaustiva para estes casos definidos |

Todos os casos têm `fieldObserved=false` e `externalApproval=false`. O fixture fixa, para cada cenário, nós atingidos, nós não atingidos, distância mínima documental e quantidade de caminhos distintos. São **resultados esperados estruturais**, não medidas de risco ou confiabilidade industrial.

## Oráculo de comparação independente

A referência é produzida por uma **matriz de alcançabilidade Floyd–Warshall**, com cálculo de distância mínima e número de caminhos em um DAG. O motor expõe explicações reconstruídas por **DFS sobre arestas dirigidas** e confronta o resultado com essa referência estática e com a cascata de reabertura do Ciclo 22.

A verificação deve satisfazer, para cada cenário:

1. Todo nó afetado possui ao menos um caminho dirigido válido a partir de uma das raízes.
2. A sequência selecionada é de distância mínima em arestas, com a regra de desempate determinística documentada no algoritmo.
3. Quando há dois ou mais caminhos, o relatório apresenta uma alternativa distinta e o número de alternativas.
4. Todo nó não afetado contém testemunho de ausência de caminho dirigido desde as raízes **neste grafo**. Isso não significa que a máquina está segura ou o controle está dispensado.
5. A união entre atingidos e não atingidos contém exatamente os 13 controles, sem omissão ou duplicação.
6. O fecho ordenado preserva o grafo e o conteúdo dos Ciclos 20–22; um upstream alterado deve ser recusado.

As explicações `DependencyPathExplanation` apresentam raiz, controle-destino, caminho, etapas e razão `downstream_documentary_control_depends_on_upstream`, com `physicalMechanismClaimed=false`. Um percurso no grafo **não descreve propagação de dano, pressão hidráulica, contaminação, códigos de falha, consequências operacionais nem causalidade física**.

## Regressões adversariais

A matriz de mutações inclui cinco classes:

- **Aresta retirada:** um pré-requisito obrigatório é omitido.
- **Aresta invertida:** dependência é interpretada na direção incorreta.
- **Aresta acrescentada:** surge caminho sem base no contrato canônico.
- **Ameaça suprimida:** o registro das dez ameaças perde um dos casos exigidos.
- **Atalho de fecho fabricado:** um salto documental é apresentado como aresta justificada.

Todas devem receber `rejected_noncanonical`. Testes adicionais adulteram caminhos, testemunhos de não alcance, distâncias, número de alternativas, raízes, perguntas, estados de aprovação, resultados de medição e dados upstream. O verificador reconstitui os documentos sintéticos e não aceita alteração apenas porque o JSON está estruturalmente correto.

**Nota metodológica:** a cobertura de 100 casos e cinco mutações é uma medida de **cobertura dos testes especificados**, não 100% de cobertura possível de futuras configurações de sistemas, condições reais de falha ou riscos de segurança da informação. O relatório não atribui probabilidade diagnóstica.

## Revisão cruzada

A matriz `crossFunctionalReview` conserva as cinco áreas de responsabilidade da origem: TI, Segurança da Informação, Engenharia, Jurídico e Gestão de Manutenção. Para cada área, identifica os controles sob responsabilidade declarada e cenários cuja propagação a atingiria. Em todos os casos:

`externalTechnicalReviewPerformed=false`, `authenticatedSignoffReceived=false`, `mayReleaseEquipment=false`.

Nenhuma responsabilidade é convertida em assinatura. A matriz só ajuda a visualizar **quais atores organizacionais precisariam participar de um futuro processo privado autorizado**.

## Contratos e implementação

- `pilot/reopen-coverage.v1.json` — oráculo versionado, grafo/arestas canônicos, 100 casos e cinco mutações;
- `pilot/reopen_coverage.py` — validação do fixture, matriz independente, caminhos DFS, testemunhos de não alcance, verificação determinística e geração JSON/HTML offline;
- `tests/test_reopen_coverage.py` — regressões de cobertura, caminhos e redundâncias, negativas de alterações e preservação de NO GO;
- **Dez JSON Schemas**, incluindo `DependencyPathExplanation`, `ReopenCoverageCase`, `AlternativePathWitness`, `UnreachableControlWitness`, `MutationCoverageResult` e `NoGoBoundary`, além dos envelopes de contrato;
- GitHub Actions — executa os testes dos ciclos anteriores, reconstrói o corpus FMEA público fixado, gera relatório offline, confronta caminhos contra o oráculo e testa seis versões adulteradas do fixture.

O HTML apresenta 19 seções expansíveis (13 raízes individuais e seis conflitos) sem JavaScript, formulário ou conexão externa. Os 100 casos completos ficam preservados no JSON.

## Reprodução

Depois de gerar os artefatos públicos dos Ciclos 13–22:

```bash
python -m unittest discover -s tests -v

python -m pilot.reopen_coverage \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --gng build/go-nogo/no-go-report.v1.json \
  --sequence build/sequencing/evidence-sequence.v1.json \
  --contradictions build/contradictions/contradictions.v1.json \
  --output build/coverage/reopen-coverage.v1.json \
  --html build/coverage/reopen-coverage.v1.html
```

O programa compara os três relatórios de entrada com uma reconstrução completa do corpus público autorizado e exige igualdade do oráculo com o fixture versionado.

## Limitações e segurança

A base pública não inclui dados corporativos, laudos, série real, pessoal identificado, telemetria, informação SAP, credenciais, manual OEM licenciado, assinaturas válidas ou medições de campo. A classificação `no_go` é obrigatória; não há piloto privado, intervenção física, compra de peças, alteração de ECM, emissão de OS ou liberação da máquina.

SHA-256 permite apenas comparação de conteúdo sintético versionado. Não valida autenticidade de pessoas, fontes OEM nem imutabilidade externa.

**Próxima hipótese de P&D:** testar a sensibilidade do grafo a alterações propostas e criar uma ferramenta de revisão de mudanças de contrato (diff de arestas, justificativas, impacto no fecho, autorização humana externa necessária), sem tornar o grafo autoeditável ou homologado.
