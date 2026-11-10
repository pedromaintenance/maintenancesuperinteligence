# Ciclo 61 — Contexto metrológico, proveniência e comparabilidade

**08/11/2026 · P&D · proposta empilhada sobre C60 · NO GO**

## Problema
O Ciclo 60 converte grandezas para SI, verifica duas identidades didáticas e compara intervalos de valores inventados. Seu resultado pode ser matematicamente consistente mesmo que os valores correspondam a **condições operacionais distintas**, a um alvo nominal em vez de medição, ou a um instrumento sem caracterização metrológica. O Ciclo 61 não adiciona diagnóstico: implementa **barreiras estruturais para esse tipo de confusão**.

## Entregas
- `benchmarks/cycle61_metrology_context.py`: executa o validador do C60 e exige um registro contextual para cada papel `input_a`, `input_b`, `reported_result`.
- `tests/test_cycle61_metrology_context.py`: 15 métodos de teste, inclusive inconsistências de estado de carga, temperatura, janela, incerteza declarada, instrumento e promoção de autoridade.
- `.github/workflows/cycle61-metrology-context.yml`: regressão offline dos ciclos 60–61 no piloto isolado C70 (o histórico original executava 58–61).
- Contrato validado em Python, com apenas identificadores `SIM-` e dados inventados. Não são admitidas IDs de ativos reais nem certificados reais.

## Portas lógicas
1. **Comparabilidade de contexto**: carga, regime térmico, cenário e janela de amostragem devem coincidir entre as duas entradas. Se o valor de saída é uma leitura fictícia, seu contexto também precisa coincidir.
2. **Observado vs nominal**: `invented_observation` é uma leitura inventada; `invented_nominal_target` é uma referência hipotética, nunca evidência de medição. **Comparação observacional é bloqueada para alvo nominal**. O C60 pode continuar calculando a sobreposição matematicamente, mas o C61 não a divulga como observação comparável.
3. **Instrumento**: leituras exigem identificador sintético `SIM-`. Calibração permanece `unverified_synthetic` e evidência de calibração obrigatoriamente `null`. Nenhum campo autoriza afirmar instrumento calibrado.
4. **Resolução e faixa declarada**: uma regra conservadora de auditoria exige incerteza absoluta declarada igual ou superior a metade da resolução informada, na mesma unidade da grandeza. **Não é aplicação da GUM, nem determinação de incerteza expandida, nem garantia de cobertura estatística**.
5. **Segurança**: todo caso continua `synthetic_training_only`; todas as flags de evidência, validação e autoridade permanecem falsas. Recibos são novos, sem sobrescrita.

## Limitações
- O programa **não verifica autenticidade, data de calibração, rastreabilidade ao SI, adequação do instrumento, range, temperatura ou erros sistemáticos**. É uma auditoria de metadados ficcionais.
- Estado operacional declarado como igual não prova simultaneidade nem estabilidade na máquina; não há data/hora real, conectividade ou telemetria.
- A regra de meia resolução é somente um teste de coerência mínima dos dados sintéticos; não substitui modelo de incerteza, curva de calibração ou critérios normativos.
- Não existe banco aprovado de limites OEM. Valor nominal, limite superior/inferior, faixa de alarme e faixa de aceitação são conceitos diferentes; o contrato atual permite alvo nominal fictício **sem criar julgamento de conformidade**.
- O cálculo ideal de potência hidráulica do C60 presume `Δp×Q`; não há vínculo com ponto físico de medição, eficiência ou perdas reais.
- Nenhuma pessoa realizou validação independente de casos reais ou homologação operacional.

## Execução
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context -v
python -m benchmarks.cycle61_metrology_context --input /tmp/caso-ficticio.json --output /tmp/recibo-c61-novo.json
```
A função `fixture()` de `tests/test_cycle61_metrology_context.py` gera uma entrada inteiramente fictícia para testes.

## Critério de continuidade
C61 só pode ser anunciado como **verificação automatizada concluída** quando o CI do commit exato passar. Não confundir essa condição com competência diagnóstica ou governança real.

**Ciclo 62 sugerido:** contrato de referência e limites com proveniência, efetividade aplicável e semântica distinta de nominal, limite de segurança, alarme e aceitação, ainda sem importar literatura restrita ou autorizar execução.

**Decisão formal: NO GO.**

## Nota de isolamento — Ciclo 70

Este incremento foi extraído da cadeia de pesquisa como PR pequeno em Draft, baseado **na branch do seu único predecessor direto** (C60), e não sobre todo o histórico até C69. O CI da integração executa somente C60 e C61. Não foram carregados dados de campo, parâmetros OEM ou permissões de escrita/execução. O PR permanece sujeito a revisão humana de código e à integração previamente aprovada da dependência; **NO GO** para qualquer uso operacional.
