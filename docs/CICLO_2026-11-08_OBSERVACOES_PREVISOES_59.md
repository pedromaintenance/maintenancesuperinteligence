# Ciclo 59 — Observações versus previsões: coerência não é validade mecânica

**08/11/2026 · P&D · Proposta empilhada sobre Ciclo 58 · NO GO**

## Questão
O Ciclo 58 exige duas ou mais hipóteses, contraprovas e previsões discriminantes, mas **não compara essas previsões com observações**. O Ciclo 59 cria um ensaio propositalmente restrito: comparar **rótulos declarados** de observações fictícias com rótulos previstos. Não interpreta a física e não decide a hipótese correta.

## Implementação
- `benchmarks/cycle59_observation_consistency.py`: chama `validate` do Ciclo 58 antes de aceitar a observação; exige cenário `synthetic_training_only` e observação `synthetic_fictional_record`, `unverified_synthetic`.
- Aceita um registro por verificação proposta, vinculado por `checkId`; cada observação precisa indicar interpretação `supports`, `contradicts` ou `indeterminate` **para todas as hipóteses**.
- Conta *label conflicts* somente entre `supports` versus `contradicts` para a mesma dupla teste/hipótese. Não chama `indeterminate` de oposição. Não eleva a hipótese concorrente, mesmo que haja múltiplas contradições.
- `tests/test_cycle59_observation_consistency.py`: casos negativos de falsa evidência real, mapeamento incompleto, duplicação, elevação de privilégios e causalidade.
- `.github/workflows/cycle59-observation-consistency.yml`: Python stdlib, CI sem acesso a dados privados, fontes externas ou segredos.

## Exemplo conceitual
Hipóteses fictícias A e B; uma verificação declara suporte a A e contradição de B. Uma observação inventada pode trazer interpretação oposta. O programa conta um conflito textual. **Isso não prova sequer que a observação é confiável, quanto menos que A ou B explica uma falha.**

## Barreiras de interpretação
1. `recordedOutcome` tem valores categóricos inventados `pattern_a`, `pattern_b`, `undetermined`; o código **não** relaciona fisicamente resultado medido a uma hipótese.
2. `recordedText`, `reason` e `mechanism` são texto livre não verificado; uma pessoa pode inventar uma justificativa coerente, porém falsa.
3. Não é implementada metrologia (erro, unidade, incerteza, calibração), modelagem de grandezas ou checagem de energia, pressão, vazão, potência, temperatura, desgaste e condição de carga.
4. Não há literatura OEM por série, prova de procedimento aplicável, medição de campo, revisor humano ou autorização corporativa.
5. Campos que tentem promover observações a medidas reais, diagnóstico validado ou autorização são rejeitados. Recibo de saída contém apenas contagens, referências de conflito, `NO GO` e flags negativas.
6. Qualquer uso futuro com dados reais precisa de política privada, LGPD quando aplicável, direitos de conteúdo e revisão independente. O arquivo público **não** é classificador de dados sensíveis; somente inserir exemplos inventados.

## Reproduzir
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency -v
python -m benchmarks.cycle59_observation_consistency --input /tmp/caso-inventado.json --output /tmp/recibo-c59-novo.json
```
A função `fixture()` da suíte de testes contém um exemplo **inteiramente inventado**.

## Próximo experimento
Uma camada de **metrologia e plausibilidade física em cenário didático** deve separar unidade, referência, incerteza e condição de ensaio, sempre sem reivindicar efeito OEM. A revisão humana independente requer casos inéditos externos ao Git, custódia de gabarito, critérios definidos previamente e adjudicação de desacordos.

**Decisão formal: NO GO para diagnóstico validado, ações SAP/ECM, testes físicos, OS ou liberação de equipamento.**
