# Ciclo 31 — Auditoria da qualidade de conjuntos de validação

**P&D 3.1.0 · 28/10/2026.** Continuação da custódia privada do Ciclo 30, sem revisão externa executada.

## Objetivo

Um teste com casos repetidos e poucos mecanismos pode produzir concordância artificialmente alta, mesmo quando o seletor não generaliza. Este ciclo cria barreiras de qualidade para metadados de casos **sintéticos**, sem assumir que etiquetas de hipótese representam falhas efetivamente identificadas.

## Corpus ilustrativo

- 26 registros artificiais: 8 de treino, 4 de desenvolvimento e 14 de teste.
- Quatro sistemas previamente modelados (comando final, hidráulica, eletrônica e arrefecimento), cada qual com três etiquetas distintas de hipótese e pelo menos um caso de cada etiqueta no teste.
- Dois casos no teste pertencentes a domínios deliberadamente não suportados (freios e transmissão), exigindo abstenção.
- O teste contém exemplos de proveniência contraditória, revogada e não verificada. Nenhum registro é amostra de campo, evidência física ou verdade causal validada.

## Portas de qualidade

| Verificação | Resultado de falha |
| --- | --- |
| Linhagem de caso repetida em conjuntos diferentes | Crítica: contaminação treino/teste |
| Grupo de origem repetido entre conjuntos | Crítica: dependência entre exemplos |
| Mesmo identificador de evidência em conjuntos diferentes | Crítica: reutilização de fonte |
| Texto narrativo idêntico após normalização | Crítica entre conjuntos; relevante dentro do mesmo conjunto |
| Narrativa quase idêntica entre conjuntos (Jaccard dos tokens) | Relevante: revisar possível derivação |
| Falta de mecanismo didático, caso não modelado ou provenance challenge no teste | Relevante: cobertura insuficiente |
| Registro declara causa confirmada, teste físico, OEM ou OS | Rejeição estrutural imediata |

Os sinais são **heurísticas conservadoras de qualidade**, não provas suficientes de independência: paráfrases, famílias correlacionadas, origem oculta e casos reais equivalentes podem escapar. Similaridade Jaccard é apenas triagem lexical e pode gerar falsos positivos ou falsos negativos.

## Entradas e saídas

- `benchmarks/validation-quality-manifest.v1.json` — manifest público sintético, sem gabarito técnico.
- `benchmarks/validation-quality-policy.v1.json` — taxonomia e exigências de cobertura.
- `benchmarks/validation_set_quality.py` — verificação estrutural, comparação entre registros e relatório reproduzível.
- `contracts/validation-quality-{manifest,policy,report}.schema.json` — contratos de entrada e saída.
- `tests/test_validation_set_quality.py` — mutações adversariais contra duplicação, contaminação, falha de abstenção, fraude de causa e autorização.

```bash
python -m unittest discover -s tests -v
python -m benchmarks.validation_set_quality \
  --output build/benchmarks/cycle31-quality.json \
  --html build/benchmarks/cycle31-quality.html
```

O comando retorna código 2 quando encontra uma falha de qualidade, mesmo depois de gravar o relatório com os achados.

## Custódia e restrições

A demonstração pública utiliza apenas dados inventados; o CI não processa casos ou gabaritos reservados. Para uso com metadados externos, o CLI exige que entrada e saída estejam fora da árvore pública. A versão atual exige o contrato de demonstração sintética, de modo que não constitui ainda ingestão homologada de registros reais.

Os identificadores e etiquetas não devem ser confundidos com equipamentos, causas confirmadas ou fontes OEM. A lógica é um **pré-filtro de qualidade de datasets**, ainda não uma trava obrigatória na etapa `prepare` do Ciclo 30. Para um estudo real, o custodiante deverá exigir este gate ou um equivalente independentemente auditado antes de distribuir casos.

**Permanecem NO GO:** avaliação técnica independente não realizada, ausência de validação OEM, nenhum acesso SAP/ECM, teste físico, substituição de componente, OS ou liberação de ativo.
