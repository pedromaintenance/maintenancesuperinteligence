# Ciclo 60 — Laboratório de metrologia dimensional sintética

**08/11/2026 · P&D · proposta sobre Ciclo 59 · NO GO**

## Problema atacado

O C58 formalizou hipóteses concorrentes e o C59 comparou **rótulos textuais** entre previsões e observações fictícias. Nenhum desses ciclos executava operações com unidades e grandezas. O C60 introduz verificação dimensional e propagação **intervalar determinística** para duas identidades didáticas, sem converter essa consistência em diagnóstico mecânico.

## Implementado

- `benchmarks/cycle60_metrology.py`: aceita exclusivamente `origin=synthetic_training_only` e `nature=invented_example_only`, três quantidades por caso e flags negativas obrigatórias.
- Conversões suportadas: pressão Pa/kPa/bar/MPa; vazão volumétrica m³/s e L/min; potência W/kW; torque N·m; velocidade angular rad/s e rpm; tempo s/min (reservado a expansão, não aceito como entrada das duas fórmulas).
- Fórmulas de **compatibilidade dimensional**, em unidades SI: `P = Δp × Q` (potência hidráulica ideal) e `P = T × ω` (potência mecânica de eixo).
- Entradas não negativas com incerteza absoluta delimitada (`0 ≤ u ≤ x`), rejeitando NaN, infinito, booleanos, texto e overflow.
- Intervalos de entrada `[x-u, x+u]` transformados para SI e multiplicação de limites para grandezas não negativas. O cálculo **não** representa distribuição probabilística, confiabilidade do instrumento nem percentil de confiança.
- Resultado apenas compara intervalo calculado e intervalo do resultado informado. `intervalsOverlap` indica sobreposição matemática dos intervalos fictícios, **não valida acurácia, conservação de energia em equipamento, parâmetro OEM ou condição de campo**.
- `tests/test_cycle60_metrology.py`: 14 métodos de regressão com casos válidos e negações adversariais.
- `.github/workflows/cycle60-metrology.yml`: suíte C58–C60 em ambiente sem segredos ou sistemas industriais.

## Restrições físicas explícitas

### Fórmula hidráulica

`P = Δp Q` é uma relação ideal de potência transmitida pelo fluido associada à diferença de pressão e à vazão. Não considera eficiência, vazamentos, compressibilidade, perdas térmicas, regime transitório ou condição de projeto. A ferramenta não sabe se a pressão informada é diferencial, absoluta, medida no local correto ou compatível com o circuito.

### Fórmula no eixo

`P = Tω` calcula potência instantânea associada a torque e velocidade angular. Não representa necessariamente potência útil ou potência nominal. O laboratório não determina direção da rotação, sinal do torque, perdas, variações temporais ou fator de serviço. **Entradas negativas são rejeitadas** para manter o algoritmo intervalar simples; isso não significa que grandezas físicas reais nunca sejam negativas.

### Riscos de evidência

- Os valores são exclusivamente inventados e publicáveis; não há coleta de telemetria, sensor, calibração, documento OEM ou dados de equipamentos reais.
- Sobreposição de intervalos pode ocorrer mesmo com modelo físico incorreto; ausência de sobreposição pode decorrer de hipótese equivocada, unidades erradas, condições incompatíveis ou incerteza subestimada.
- Não é motor genérico de verificação física, nem teste de conformidade, nem catálogo de tolerâncias.
- Não há autorização de execução de testes, OS, escrita SAP/ECM ou liberação de equipamento.
- Recibo não sobrescreve arquivo já existente; conteúdo de entrada não é automaticamente sanitizado para dados restritos — **não inserir dados reais neste módulo público**.

## Comandos

```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology -v
python -m benchmarks.cycle60_metrology --input /tmp/exemplo-sintetico.json --output /tmp/recibo-c60-novo.json
```

A função `fixture()` em `tests/test_cycle60_metrology.py` fornece casos artificiais reproduzíveis.

## Critérios de saída e continuidade

O incremento só estará com implementação automatizada confirmada após aprovação do workflow no commit exato. Mesmo nesse caso, **NO GO** permanece para análise real, revisão externa, parâmetros OEM e autoridade operacional.

**Ciclo 61 candidato:** separar modelo de incerteza, origem/calibração das medições e domínio de validade; submeter as relações físicas a revisores mecânicos independentes antes de ampliar conclusões ou conectar dados privados.
