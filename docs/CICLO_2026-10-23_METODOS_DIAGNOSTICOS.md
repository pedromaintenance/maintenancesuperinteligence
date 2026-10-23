# Ciclo 05 — Biblioteca de métodos diagnósticos por disciplina

**Versão do protótipo:** 0.5.0  
**Data:** 23/10/2026  
**Issue:** [#10](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/10)  
**Escopo efetivo:** catálogo público de pesquisa e exercícios estruturados, sem execução de testes, limiares OEM ou dados reais.

## Objetivo técnico

O Ciclo 04 separou relato, observação, teste e hipótese. O Ciclo 05 define **o que perguntar antes de uma investigação**, quais dados necessários registrar, quais alternativas não podem ser descartadas e que salvaguardas devem anteceder qualquer coleta.

Um método de diagnóstico deve responder: **que fenômeno pretende discriminar, em qual condição, com qual tipo de evidência, que outra causa poderia explicar o mesmo resultado e qual é o limite da interpretação?**

Este catálogo **não contém procedimentos passo a passo de campo**. Identificar uma forma de aquisição de dados é diferente de especificar ou autorizar a intervenção.

## Catálogo inicial

| Área | Métodos | Perguntas e limites |
|---|---:|---|
| Análise de óleo | 4 | rastreabilidade de amostra; tendências; confirmação de água; formulação e baseline. Sinais sem histórico não identificam peça |
| Hidráulica | 3 | contexto de pressão, vazão e temperatura. Nunca assumir ponto, carga, valor-limite ou configuração |
| Mecânica | 3 | depósitos magnéticos, caminho de ingresso, metrologia de superfície. Dano visual, limalha e dimensão não condenam componente automaticamente |
| Vibração | 2 | localização de ruído e tendência comparável. A assinatura depende de rotação, carga, ponto e método |
| Eletrônica | 2 | DTC ativo/registrado e contexto ECM. Código não equivale a sensor, chicote ou ECM defeituoso |

**Total:** 14 métodos conceituais, cinco disciplinas. Cada registro inclui `DiagnosticMethod`, `Prerequisite`, `ExpectedObservation`, `InterpretationLimit` e `ApplicabilityGate`; a coleção é publicada em `methods/catalog.v1.json`.

### Vínculo com FMEA Mining

O snapshot público do FMEA, de conteúdo **1.0.0** e preview histórico **1.3.12**, continua sendo a única fonte para os oito testes propostos das quatro cadeias `FC-FD`. Os códigos que ocorrem no piloto são:

| Código FMEA | Método de pesquisa neste ciclo | Contexto |
|---|---|---|
| `EV-11` | `MET-MECH-MAGNET` | bujão magnético/partículas, aplicável a duas cadeias hipotéticas |
| `EV-08` | `MET-OIL-TREND` | histórico, viscosidade, contaminação e tendência em duas cadeias |
| `EV-10` | `MET-OIL-WATER` | possível água, coleta/ensaio representativo |
| `EV-01` | `MET-MECH-SEAL` | tampas, respiros, vedações, histórico de lavagem |
| `EV-13` | `MET-OIL-PRODUCT` | produto, horas de óleo, reabastecimento e baseline |
| `EV-04` | `MET-VIB-LOCALIZE` | contexto de localização de ruído/vibração |

Isso produz **seis métodos únicos e oito vínculos de investigação** (porque `EV-11` e `EV-08` aparecem em mais de uma cadeia). O nome/identificador do método e a descrição exata de cada investigação continuam pertencendo ao FMEA. A nova biblioteca acrescenta perguntas de levantamento que são **elaboração didática deste projeto**; não representam texto ou homologação OEM.

Para cada vínculo, a execução confere o `referenceFmeaId`, `methodId`, propósito **textualmente igual** ao registro do snapshot e `status=not_performed`. Uma divergência interrompe o processo.

## Referências e limites

Este ciclo distingue fontes públicas do fabricante da literatura efetiva aplicável ao equipamento.

- **Caterpillar, [Fluid Analysis 101](https://www.cat.com/en_US/support/maintenance/sos-services/analysis-101.html/):** escopo geral de análise de contaminantes e metais; não autoriza inferir origem da avaria nem limite por série.
- **Caterpillar, [How to Inspect Cat Drive Train Magnetic Plugs](https://www.cat.com/en_US/blog/inspect-drive-train-magnetic-plugs.html):** contexto geral de inspeção; não substitui procedimento aplicável ao comando final da CAT 777E.
- **SKF, [Bearing damage analysis — ISO 15243](https://evolution.skf.com/us/bearing-damage-analysis-iso-15243-is-here-to-help-you/):** mecanismos e classificação geral; não identifica rolamento específico nem condição da máquina.
- **SKF, [Parallel condition monitoring](https://evolution.skf.com/parallel-condition-monitoring/):** uso conceitual de parâmetros vibracionais para acompanhamento de condição; não define limite ou método por frota.
- **Bosch Rexroth, [CytroConnect Solutions](https://www.boschrexroth.com/pt/br/connected-hydraulics/produtos/cytroconnect-solutions/):** exemplo de aquisição de pressão, temperatura e fluxo para análise de integridade hidráulica; não é procedimento de prova de bomba ou válvula de CAT.
- **Caterpillar, [Electronic Technician Overview](https://www.cat.com/en_US/by-industry/oil-and-gas/learning/program/caterpillar-electronic-technician-cat-et-overview.html/):** funcionalidades e formação sobre diagnóstico eletrônico; não concede acesso, licença ou autorização para calibração.

O papel de cada fonte e sua limitação são registrados em `data/diagnostic-method-sources.v1.json`. Referências já existentes no FMEA têm URL cruzada com o snapshot. Fontes novas são explicitamente separadas. Não foi copiado manual técnico licenciado para o repositório.

## Modelo de segurança

`ApplicabilityGate` possui fabricante, modelo, série/arranjo, publicação e revisão como `null`. Esses campos não são preenchidos por inferência a partir da CAT 777E do cenário. O catálogo inteiro mantém:

- `approvedForOperationalUse=false`;
- `reviewStatus=generic_conceptual_not_oem`;
- `executionStatus=proposed_not_executed`;
- `thresholds=null` e `parameterValues=null`;
- `ExpectedObservation.nature=potential_not_measured`;
- `InterpretationLimit.permittedInference=question_or_hypothesis_only`.

Os `safetyGates` são apenas **categorias de riscos e pré-requisitos para futura revisão** — por exemplo, energias hidráulicas armazenadas, isolamento, partes rotativas, acesso seguro, instrumento apropriado, proteção ambiental e permissão de diagnóstico eletrônico. Listar esses riscos **não** significa que o catálogo estabeleceu um procedimento de segurança ou autorização de trabalho.

## Interface funcional

A CLI `methods/library.py` valida o snapshot do FMEA com o checksum congelado e **reconstrói a investigação por meio da função do Ciclo 03/04** para comparar o relatório recebido. Assim, um relatório adulterado não pode tornar um ensaio proposto em ensaio executado.

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m investigations.final_drive \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --index build/fmea-public/fmea-public.index.json \
  --case examples/777e_additives_only.json \
  --output build/investigations/777e_additives_only.json

python -m methods.library \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --case examples/777e_additives_only.json \
  --investigation build/investigations/777e_additives_only.json \
  --output build/methods/777e_additives_only.methods.json
```

Saída `maintenance-superinteligence.diagnostic-method-plan.v1`: oito `suggestedQuestions` vinculadas ao FMEA, pré-requisitos, campos a registrar ainda **não medidos**, limites de interpretação, categorias de segurança e fontes; além de cobertura e bloqueios de efetividade. Trata-se de um **plano de investigação conceitual**. `mayExecuteTests=false`; `confirmedComponentFailure=null`.

## Critérios de verificação

O CI executa validação offline e cenários adversariais das cinco disciplinas, incluindo **dois casos negativos por disciplina** que tentam promover observação potencial a medição real e remover salvaguardas. Também verifica inserção de valores-limite, falso aceite OEM, falsificação de fontes, alteração de propósito original e execução de teste inexistente. O resultado é confrontado com o snapshot de referência real.

**Advertência:** teste verde comprova apenas consistência e invariantes do modelo dentro da cobertura atual. Não comprova que o conjunto de perguntas é suficiente, que a fonte atende a uma série de equipamento, que sensores estão calibrados ou que o método é adequado a todas as condições.

## Critério de expansão para o próximo ciclo

O catálogo possui cinco disciplinas, mas o plano automatizado só é gerado para os **oito métodos já referenciados pelo piloto de comandos finais**; métodos de hidráulica e eletrônica ainda não estão ligados a casos verticais completos. O próximo desenvolvimento deverá estabelecer cenários seguros por circuito/sistema (sem controles de máquina), revisão por especialista e critérios de escolha entre métodos com custos, disponibilidade e **capacidade discriminante demonstrável**, não pesos inventados.
