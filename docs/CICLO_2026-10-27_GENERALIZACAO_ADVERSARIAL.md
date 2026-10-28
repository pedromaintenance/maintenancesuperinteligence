# Ciclo 28 — Desafios de generalização e qualidade documental

**P&D 2.8.0 • 27/10/2026**. Continuação do Ciclo 27; sem aprovação de intervenção industrial.

## Pergunta de engenharia

O seletor atual continua escolhendo uma pergunta apropriada quando a entrada não repete os cenários ensinados, quando a fonte tem proveniência incompleta ou quando o sistema do equipamento não está modelado?

## Desenho do benchmark

- **34 casos fictícios não incluídos no corpus original do Ciclo 27.** São novos para o seletor anterior; não são blindados perante a equipe que criou este ciclo.
- Quatro famílias conhecidas, oito situações por família: falta da primeira peça de contexto; falta da terceira; narrativa contraditória; contexto completo; proveniência não verificada; proveniência conflitante; informação obsoleta; evidência revogada.
- Dois domínios intencionalmente desconhecidos do seletor (freios e transmissão), para avaliar abstenção em vez de erro de aplicação ou condenação indevida.
- Cada cenário conserva a indicação `synthetic_narrative_not_field_measurement`, zero validação OEM, zero causalidade confirmada e zero autoridade para teste, OS ou liberação.
- Entrada, expectativa editorial e motor de avaliação ficam em arquivos separados. Isso reduz acoplamento de execução, mas não prova independência de elaboração.

## Duas versões comparadas

1. **Linha-base congelada (Ciclo 27)**: pergunta baseada exclusivamente em contradição narrativa e campos documentais presentes/ausentes; não avalia qualidade de proveniência.
2. **Barreira documental adicional**: antes da pergunta técnica, manda verificar fonte não comprovada, conciliar fontes contraditórias ou revalidar evidência obsoleta/revogada. Fontes rotuladas `credible_synthetic` representam confiança apenas dentro da simulação, nunca autenticação real. Caso o domínio seja desconhecido, solicita encaminhamento especializado sem tentar gerar hipóteses.

O código preserva o seletor original, permitindo contraste sem reescrever a linha-base. Não executa investigação física.

## Leitura das métricas

`baselineEditorialAgreement` é calculado apenas para 32 casos de domínios que o seletor antigo conhece; domínios desconhecidos contam separadamente, não como erro arbitrário na taxa. `qualityGatedEditorialAgreement` considera os 34 casos. O gabarito é **autorais de P&D** e NÃO uma verdade mecânica validada. Concordância perfeita no banco autocriado não representa generalização em campo, validação OEM, sensibilidade, especificidade nem melhoria comprovada na prática.

A comparação dos casos de origem não verificada evidencia uma limitação concreta de software: o seletor anterior poderia avançar na sequência de perguntas apesar de uma fonte inadequada. A barreira evita isso no modelo sintético.

## Entregáveis

- `benchmarks/generalization-challenges.v1.json`
- `benchmarks/generalization-expectations.v1.json`
- `benchmarks/generalization_stress.py`
- `tests/test_generalization_stress.py`
- 3 contratos sob `contracts/generalization-*.schema.json`
- CI com execução e publicação de JSON/HTML estáticos.

```bash
python -m unittest discover -s tests -v
python -m benchmarks.generalization_stress \
  --output build/benchmarks/cycle28-generalization.json \
  --html build/benchmarks/cycle28-generalization.html
```

## Limites/risco de circularidade

A bateria continua baseada em classes de perturbação idealizadas; os metadados de confiabilidade são flags didáticas e não evidência autenticada. As expectativas são definidas pela mesma equipe que implementa a nova camada. É possível obter pontuação máxima com regras programadas exatamente para essas categorias, sem robustez mecânica real.

**Próxima etapa:** curadoria independente de casos de falha e contrafalha com fontes de uso autorizado, parecer técnico cego e divergências registradas. Estabelecer matriz de severidade por erro crítico, confusão entre hipótese/causa e decisão de abstenção. Até essa etapa, `educational_only_no_go`.
