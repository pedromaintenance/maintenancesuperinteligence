# Ciclo 46 — Auditoria de cegamento e preparo de adjudicação técnica

**P&D v4.6.0 · 04/11/2026 · incremento em branch dependente do Ciclo 45.**

> **NO GO:** nenhum parecer humano qualificado foi coletado, a identidade de nenhum adjudicador foi verificada e nenhum caso foi homologado. Este ciclo cria um **encaminhamento privado, não uma decisão técnica**. Não autoriza inspeção, teste físico, intervenção, OS, escrita SAP, ajuste ECM nem liberação de equipamento.

## 1. Problema a resolver

O Ciclo 45 criou um protocolo de perguntas A/B, com duas submissões congeladas por hash e atribuição oculta dos métodos. A concordância entre aliases fictícios, entretanto, poderia ser confundida com aprovação técnica. Além disso, uma pergunta pode revelar o método que a produziu por termos explícitos ou desbalanceamento da redação, mesmo com posições A/B sorteadas.

O Ciclo 46 acrescenta dois controles **não equivalentes à homologação**:

1. Uma **triagem heurística e não conclusiva do mascaramento** das perguntas: identifica indícios lexicais e disparidade extrema de tamanho. Não identifica todo vazamento semântico, não prova cegamento e não reescreve perguntas.
2. Uma **fila formal de pendências para adjudicação externa**: vincula o relatório do Ciclo 45 às submissões privadas e classifica divergências, riscos, empates, abstenções e possíveis sinais de desmascaramento. A fila não decide vencedores nem substitui um parecer independente.

## 2. Fronteira de custódia e integridade

O módulo `benchmarks/cycle46_adjudication.py` usa, antes de qualquer triagem, a cadeia já consolidada:

`casos custodiais C30 → qualidade e isolamento C32 → candidatos e pacote A/B C45 → mapa HMAC privado → duas submissões congeladas → relatório C45 reconstruído → triagem C46`.

Alterar a fonte, um candidato, o pacote, o mapa, a chave, a política de qualidade, uma resposta ou seu recibo invalida a reconstrução. O novo relatório também vincula os digests de todos os insumos relevantes.

**Hash/HMAC não equivale a identificação, assinatura de engenheiro, autoridade OEM, cadeia de custódia institucional ou imutabilidade fora do ambiente.** Uma pessoa que controla chave e entradas pode construir outro conjunto válido. A organização deve gerir guarda, acesso, titulares, retenção, revisão e auditoria externa independentemente do código.

O relatório de triagem inclui apenas IDs de caso, domínios, **códigos de alerta**, estados de encaminhamento e digests. Não repete os textos das perguntas, as respostas narrativas ou os segredos no artefato de saída. **A saída ainda é privada**, por estar associada aos IDs dos casos sob custódia.

## 3. Heurísticas de neutralidade: escopo estrito

A política pública `governance/cycle46-neutrality-policy.v1.json` é versionada e imutável para este ciclo. O detector normaliza caixa e acentos e identifica:

- Termos de revelação metodológica, como `baseline`, `experimental`, `algoritmo`, `inteligência artificial` e expressões correlatas;
- Desbalanceamento significativo na quantidade de palavras entre A e B, com razão **maior ou igual a 2,5**.

Os alertas são `question_origin_cue` e `question_length_imbalance`. Eles indicam necessidade de **revisão humana do mascaramento**, não evidência de fraude, nem prova de que um texto sem alertas realmente foi apresentado cegamente.

Limitações: a análise não compreende semântica profunda, vocabulário técnico do OEM, pistas de estilo, familiaridade dos revisores com ferramentas, identidade da fonte ou mudanças sutis na complexidade das perguntas. Um falso negativo é possível. A política não afirma mensurar taxa de desmascaramento ou validade diagnóstica.

## 4. Regra causal de adjudicação

| Ocorrência no estudo privado | Encaminhamento do Ciclo 46 |
| --- | --- |
| Sinal de origem do método ou comprimento desbalanceado | `possible_blinding_leak` |
| Flag de risco em qualquer avaliação | `reviewer_risk_flag` |
| Preferências A/B discordantes | `reviewer_disagreement` |
| Empate ou duas abstenções | `reviewer_uncertainty` |
| Concordância sem flags nem alertas | `pending_external_validation_no_adjudication` |

Os quatro primeiros casos exigem a fila `pending_external_adjudication`. Concordância sem indícios detectáveis **não produz aceitação técnica**: o estado continua `pending_external_validation_no_adjudication`.

Nenhum dos dois estados representa uma decisão de engenheiro. O software não conclui que a questão selecionada teria poder discriminante no campo.

## 5. Dossiê documental de adjudicação

O contrato `cycle46-adjudication-draft.schema.json` descreve somente tarefas pendentes, sem decisão:

- `request_reblinding`;
- `request_independent_safety_review`;
- `request_independent_disagreement_review`;
- `request_additional_documentary_evidence`.

Cada tarefa exige justificativa, identificação do caso e referência ao hash do relatório recebido. O alias reservado ao papel de adjudicador deve ser **diferente** dos dois aliases de revisores. Isso só testa segregação de identificadores; **não autentica três pessoas diferentes**.

Os campos `independentIdentityVerified`, `externalEngineeringOpinionReceived`, `technicalDecisionApproved`, `signedByQualifiedEngineer` e `contradictionResolved` precisam permanecer falsos. Uma tentativa de mudar qualquer um deles para verdadeiro é rejeitada. A rotina de congelamento cria recibo de integridade com `externalTechnicalAdjudicationCompleted=false`.

**Limite relevante:** um recibo de rascunho, consultado isoladamente, não comprova a cadeia original; quem auditar deve reconstruir a triagem a partir de todos os insumos privados e verificar a vinculação. Não inserir esses insumos no repositório público, em issues, PRs ou artefatos do CI.

## 6. Artefatos e execução

- `benchmarks/cycle46_adjudication.py`: triagem privada, regeneração de evidências, relatório, rascunhos e CLI;
- `governance/cycle46-neutrality-policy.v1.json`: regras imutáveis e proibições de autoridade;
- `contracts/cycle46-{neutrality-policy,handoff,adjudication-draft,draft-receipt}.schema.json`: quatro contratos públicos tipados;
- `tests/test_cycle46_adjudication.py`: falhas de custódia, falsificação, pistas metodológicas, empates, abstenções, conflito de revisores e supostos pareceres;
- `.github/workflows/cycle46-adjudication.yml`: teste apenas com casos e aliases artificiais em diretórios temporários; **sem upload de dados de estudo**.

Para testar o código com fixtures públicas sintéticas criadas em memória:

```bash
python -m unittest tests.test_cycle46_adjudication -v
```

Para executar a triagem privada em ambiente autorizado, utilizar:

```bash
python -m benchmarks.cycle46_adjudication handoff \
  --source /private/cases.json \
  --candidates /private/candidates.json \
  --quality-metadata /private/quality-metadata.json \
  --quality-policy /private/quality-policy.json \
  --packet /private/reviewer-packet.json \
  --lock /private/mapping-lock.json \
  --quality-receipt /private/quality-receipt.json \
  --key /private/custodian.key \
  --submission-a /private/reviewer-a.json \
  --submission-b /private/reviewer-b.json \
  --receipt-a /private/receipt-a.json \
  --receipt-b /private/receipt-b.json \
  --output /private/cycle46-handoff.json
```

A saída é criada com exclusividade e não sobrescreve arquivos preexistentes. Um rascunho produzido separadamente, com todos os campos de autoridade falsos, pode receber recibo através do subcomando `freeze-draft`. Não existe integração com IdP, SAP, ECM ou documentação privada para publicação.

## 7. O que falta para adjudicação genuína

**Engenharia:** validação física e documental de contexto, efetividade OEM por modelo/série, adequação do método diagnóstico e segurança de quaisquer testes sugeridos.

**Governança:** identificação, qualificação e independência dos revisores e do adjudicador, verificação de conflitos, custódia de pareceres, controle de acesso, aceite de responsáveis e retenção.

**Método científico:** pré-registro do estudo, blindagem efetiva da origem das perguntas, amostra justificada, critérios de preferência e abstenção, resolução fundamentada de dissensos e reporte de resultados com incerteza e denominadores.

**Próximo ciclo candidato:** avaliação adversarial de neutralidade e vazamento semântico, com protocolo de revisão humana independente e cenário de qualidade de evidência; não produzir novas alegações de acurácia mecânica sem dados e pareceres reais.

**Decisão formal:** `no_go_adjudication_and_blinding_unverified`.
