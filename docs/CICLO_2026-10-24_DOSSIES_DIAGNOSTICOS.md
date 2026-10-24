# Ciclo 13 — Dossiês integrados de investigação mecânica e elétrica

**Versão:** 1.3.0 · **Data:** 24/10/2026 · **Issue:** [#26](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/26)

## Resultado entregue

O projeto produz, usando exclusivamente arquivos públicos e fixtures fictícios, um relatório integrado que começa pela **função do sistema**, interpreta um **sintoma simulado**, distingue **efeitos** de **mecanismos de falha hipotéticos**, apresenta **hipóteses concorrentes abertas**, enumera **evidências e contextos ausentes**, seleciona **perguntas discriminantes**, indica **pré-requisitos de segurança** e termina com **ação proposta de investigação e revisão humana**.

A saída está em JSON versionado e HTML standalone estático. A aplicação não acessa CAT ET, SAP, manual SIS, laudo real, telemetria, banco de dados pessoal ou máquinas e **não autoriza testes, OS, ajustes ECM, condenação de peça ou liberação operacional**.

**Importante:** o termo *dossiê técnico* não equivale a laudo de campo, diagnóstico comprovado nem parecer assinado de engenheiro.

## Casos sintéticos

| ID | Sistema | Sintoma fictício | Discriminação que precisa ser feita |
| --- | --- | --- | --- |
| `SIM-TECH-FD-01` | CAT 777E — comando final | Mudança isolada de perfil de aditivos em análise de óleo | Mudança de produto/formulação ou baseline versus lubrificação, contaminação, amostragem ou desgaste |
| `SIM-TECH-HYD-01` | Circuito hidráulico genérico | Lentidão de atuação com carga contraditória | Condições de carga e demanda versus regulação/válvula, bomba ou estado térmico |
| `SIM-TECH-ECM-LOG-01` | ECM genérico | Código **registrado** sem evidência de estado ativo | Registro histórico, intermitência, anomalia de circuito ou fenômeno físico |
| `SIM-TECH-ECM-ACT-01` | ECM genérico | Código **ativo apenas no exercício** | Evento contextual/transitório versus registro histórico e sinal físico; ainda sem identificação de ECM e temporalidade suficiente |

As hipóteses são 7 para comando final e 4 para cada família restante, perfazendo **19 hipóteses mantidas em aberto nos quatro exercícios**. As mesmas hipóteses eletrônicas aparecem nos dois cenários ECM; portanto, o total refere-se às *instâncias de hipótese nos relatórios*, não a 19 mecanismos exclusivos.

### Causalidade e risco

O dossiê diferencia:
1. **Função/requisito:** o que deveria ser entregue por cada sistema, ainda sem tolerâncias ou configuração OEM homologadas.
2. **Sintoma:** o que o cenário informa; não é dado de equipamento real.
3. **Efeito:** consequência funcional possível, sem confirmação por medição.
4. **Mecanismo imediato:** alternativas causais plausíveis, não ocorrências confirmadas.
5. **Causa raiz:** **não estabelecida**. Nenhuma falha é condenada a partir da mudança isolada de aditivos, DTC genérico ou lentidão hidráulica.
6. **Risco de postergação:** descrito qualitativamente apenas para explicar a necessidade de investigação; não é RPN, FMEA empírica, risco residual nem autorização para continuar operando.

A ordem das hipóteses é **a ordem editorial da matriz de investigação**, não ranking de probabilidade/criticidade. Os status permanecem `open_not_confirmed`, e cada `probability` é `null`.

## Integração real de módulos públicos (sem dados de frota)

O código `casefiles/integrated.py` utiliza:

| Camada existente | O que está integrado |
| --- | --- |
| FMEA público fixado por SHA-256 (Ciclo 02) | `validate_snapshot` sobre os **bytes originais**; `build_consumer_index` e identificadores dos quatro mecanismos FMEA de comando final |
| `investigations/final_drive.py` (Ciclo 04) | Execução de cenário CAT 777E `SIM-777E-ADDITIVES-ONLY`, com sete hipóteses abertas, histórico/linha de base ausente e investigações não executadas |
| `methods/catalog.v1.json` (Ciclo 05) | Catálogo validado de 14 métodos conceituais, fontes públicas gerais, limitações e travas de segurança |
| `methods/discrimination-matrix.v1.json` (Ciclo 06) | Perguntas entre pares de hipóteses e seleção determinística que prioriza conflito, lacuna, aplicabilidade e revisão |
| Benchmark `benchmarks/question-quality.v1.json` (Ciclo 07) | Exigência de regressão sintética **15/15** e bloqueio de alegação de acurácia de campo |
| Gates de revisão/implantação (Ciclos 08–12) | Validação do dossiê de prontidão de dez controles e bloqueio de autoridade real; não há parecer autenticado |

Os identificadores de fontes são extraídos dos métodos realmente citados; o gerador não atribui uma referência de fabricante a um par que não a possui no catálogo. Os hashes de entrada permitem distinguir versões públicas, **não** autenticam engenheiro, equipamento ou cadeia de custódia corporativa.

Os quatro casos são autorados em `casefiles/technical-cases.v1.json`. O contrato é estrito: liga cada ID ao fixture de benchmark correto, bloqueia caminhos arbitrários e recusa entrada de série real, valores OEM, riscos numéricos, probabilidade de falha ou testagem supostamente concluída.

## Literatura técnica e alcance das afirmações

As referências abaixo fundamentam **somente princípios gerais** usados para formular perguntas, não verificam valores ou aplicação em CAT 777E, ECM específico ou circuito hidráulico:

- [Caterpillar — Fluid Analysis 101](https://www.cat.com/en_US/support/maintenance/sos-services/analysis-101.html/): análise de lubrificante, contaminantes, partículas e metais de desgaste, incluindo comandos finais. A interpretação depende da amostra, produto, tendência e contexto.
- [Caterpillar — How to Take a Sample & Read Results](https://www.cat.com/en_US/support/maintenance/sos-services/take-sample.html): amostragem limpa, identificação e construção de tendência. A referência não demonstra causa raiz em uma amostra isolada.
- [Caterpillar — Cat ET Overview](https://www.cat.com/en_US/by-industry/oil-and-gas/learning/program/caterpillar-electronic-technician-cat-et-overview.html/): capacidades gerais de ferramenta eletrônica; não permite inferir defeito de sensor a partir de um registro genérico.
- [Bosch Rexroth — CytroConnect Solutions](https://www.boschrexroth.com/pt/br/connected-hydraulics/produtos/cytroconnect-solutions/): referência geral a dados de monitoramento; **não fornece** pressão-alvo por modelo/circuito de mina.
- [SKF — Condition monitoring](https://evolution.skf.com/parallel-condition-monitoring/): princípio de monitoramento condicional; não define limite, posição nem culpabilidade de componente para a frota.

A documentação fonte segue no catálogo de `data/diagnostic-method-sources.v1.json`; o novo relatório não copia páginas de manuais licenciados nem fabrica tabelas OEM.

## Contratos e apresentação

Foram acrescentados quatro JSON Schemas:
- `contracts/technical-case-entry.schema.json`: vínculo entre caso, benchmark e simulação, com proibições de informação real e autoridade;
- `contracts/technical-casefile-fixture.schema.json`: envelope com os quatro casos;
- `contracts/technical-casefile.schema.json`: campos do dossiê de manutenção;
- `contracts/technical-casefile-collection.schema.json`: coleção versionada, quatro casos, testes executados zero, causas confirmadas zero e liberação negada.

O HTML mostra primeiro função, requisito e sintoma, depois alternativas causais, riscos, hipóteses, próxima pergunta, métodos conceituais, segurança, lacunas e referências. É **somente leitura**, sem JS, login, formulários, acesso de rede ou manipulação de dados corporativos. A renderização verifica os bloqueios de causalidade e operação antes de montar a página.

## Executar

```bash
# Consultar/baixar apenas o snapshot público pinado pelo projeto
python connectors/fmea_public.py --fetch --output build/fmea-public

# Testes offline adversariais
python -m unittest discover -s tests -v

# Geração integrada — JSON + HTML
python -m casefiles.integrated \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --fixture casefiles/technical-cases.v1.json \
  --output build/casefiles/integrated-differential.v1.json \
  --html build/casefiles/integrated-differential.v1.html
```

Os dois artefatos são disponibilizados temporariamente pelo GitHub Actions. A base de testes adversariais rejeita casos fora do corpus autorizado, identificação de frota real, inventário OEM fabricado, falso `testPerformed`, criação de OS, alteração ECM, falso desempenho de algoritmo, autorização de máquina e manipulação do resultado publicado.

## Aceite do Ciclo 13

- Quatro dossiês sintéticos coerentes e determinísticos com **19 instâncias de hipóteses em aberto**.
- Matriz, métodos, FMEA público e benchmark versionados vinculados por ID e SHA; **15 fixtures regressivos** aprovados, sem alegação de acurácia mecânica.
- Zero ensaios executados, zero defeitos confirmados, zero custo/pressão/limite OEM inventados.
- Revisão técnica humana efetiva, literatura por série, prontidão privada e permissão operacional **continuam pendentes**.
- HTML estático legível para Engenharia, com riscos qualitativos e critérios de investigação, e não uma ordem de manutenção.

**Próximo avanço recomendado:** expandir a biblioteca de *casos educacionais técnicos* com matrizes de evidência e observações condicionais mais detalhadas, incluindo limites claros entre falso positivo, efeito e mecanismo, antes de propor integração privada ou avaliação de desempenho com dados reais autorizados.
