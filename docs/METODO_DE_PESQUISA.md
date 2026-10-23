# Protocolo de pesquisa e incorporação do conhecimento

## Pergunta inicial

Toda pesquisa começa com uma pergunta delimitada: **qual função, em qual sistema/modelo, sob qual contexto operacional e com qual decisão a sustentar?**

Exemplos úteis:
- Que evidências discriminam restrição de arrefecimento de leitura incorreta de sensor?
- Quais assinaturas em óleo diferenciam desgaste de engrenagens, rolamentos e contaminação externa?
- Qual efeito esperado de alterar a periodicidade de uma preventiva, dado histórico adequado?
- Como interpretar um FMI **no ECM e arranjo corretos**?

## Etapas

1. **Definir escopo e risco:** família, função, modo de falha, consequência e condição de aplicabilidade.
2. **Inventariar fontes:** norma, literatura OEM, publicação técnica, livro, artigo, estudo de caso, documento operacional autorizado. Anotar título, editora, edição, URI, acesso, licença e revisão.
3. **Extrair afirmações atômicas:** uma alegação por registro, em texto autoral, sem copiar páginas licenciadas; cada afirmação inclui ressalvas.
4. **Separar fato, hipótese e observação:** não promover observações indiretas a causas.
5. **Revisar mecânica:** coerência funcional, física, unidades, análise de mecanismos, hipóteses concorrentes, modelos e testes.
6. **Verificar efetividade OEM:** série/arranjo, ECM/software, mudanças de projeto, valores, limitações, método e instrumento.
7. **Executar testes de regressão:** invariantes, adversariais, referências quebradas, falsos positivos e interpretação de resultados inconclusivos.
8. **Revisar por especialista independente:** autor e revisor não são a mesma pessoa para evidências de alto risco.
9. **Publicar sob contrato versionado:** separar conteúdo público de evidências corporativas protegidas.
10. **Aprender com feedback:** divergência registrada como incidente de conhecimento; corrigir com fonte e avaliação, nunca apenas ajustando o prompt.

## Classes obrigatórias

`catalogued` | `inferred` | `reviewed` | `didactic_validated` | `oem_applicability_verified` | `empirical_authorised` | `operationally_approved`

As classes não formam necessariamente uma escada única: um caso didático validado continua sendo fictício; uma medição real autorizada não implica causa raiz confirmada; aprovação operacional depende de autoridade separada.

## Ficha mínima de afirmação

```json
{
  "claimId": "CLAIM-EXAMPLE-001",
  "statement": "Um sintoma sob carga pode ser compatível com múltiplos mecanismos.",
  "language": "pt-BR",
  "domain": "diagnostics",
  "kind": "general_principle",
  "evidenceNature": "literature_synthesis",
  "reviewStatus": "proposed",
  "sourceIds": [],
  "applicability": {
    "manufacturer": null,
    "model": null,
    "serialRange": null,
    "ecmSoftwareVersion": null
  },
  "limitations": ["Exemplo de schema, não afirmação OEM específica."],
  "contradictoryEvidenceIds": [],
  "reviewerId": null,
  "lastReviewedAt": null
}
```

`null` representa informação não verificada, **não** permissão para generalizar.

## Log de lacunas

Cada dúvida vira uma entrada com: `gapId`, questão, decisão impactada, criticidade, fonte necessária, evidência existente, evidência faltante, dono da pesquisa, estado e vínculo com uma competência. O sistema deve conseguir responder "**ainda não sei**" com uma lista priorizada de investigações.

## Referências cruzadas

Apoiar-se nos próprios controles do [FMEA Mining](https://github.com/pedromaintenance/fmea-database-mining/blob/main/docs/CURADORIA.md): curadoria individual, duas hipóteses concorrentes, teste discriminante, limitações de interpretação, revisão e segregação de dados sintéticos/reais.

Critérios editoriais: uma fonte pode ser correta em geral e **inaplicável** à máquina investigada. Conflito de fontes não se resolve pelo número de resultados ou pela fluência da explicação.
