# Ciclo 49 — Validação executável de contratos entre os Ciclos 44–48

**P&D v4.9.0 · 05/11/2026 · branch dependente do Ciclo 48.**

> **NO GO:** aprovação de contrato não equivale a acerto diagnóstico, competência mecânica, autenticação de engenheiros, aderência documental OEM, autorização de estudo humano ou permissão para intervir em equipamentos. Não houve coleta de casos reais ou assinatura técnica.

## 1. Por que interromper o acúmulo de novos simuladores?

A arquitetura está com seis PRs abertos em cadeia, #69–74, todos em *draft*, com workflows específicos e regressão geral aprovados nos commits revisados em 05/11/2026. A `main` segue no Ciclo 42. Antes de ampliar o comportamento, é necessário verificar se os contratos formais são de fato compatíveis com os objetos emitidos pelas diferentes etapas de pesquisa.

Os Ciclos 44–47 acrescentaram schemas estritos, mas grande parte dos testes anteriores verificava apenas presença de arquivo, campos e atributos críticos, **sem executar o validador JSON Schema contra todos os objetos criados pelo código**. O Ciclo 48 iniciou essa prática para dois contratos de prontidão.

O Ciclo 49 amplia essa validação, **sem alegar revisão independente de código**.

## 2. Escopo material do teste

A ferramenta `governance/cycle49_contract_integration.py` gera instâncias **somente sintéticas e em memória** usando as fixtures já existentes e os módulos dos Ciclos 44–48. Ela executa o JSON Schema Draft 2020-12 com `jsonschema==4.23.0` contra os **16 contratos de origem**, distribuídos da seguinte forma:

| Ciclo | Contratos executados | Tipo de prova |
| --- | ---: | --- |
| 44 | 2 | Ensaio de perguntas simbólicas e seu relatório |
| 45 | 6 | Candidatos, pacote A/B, mapa custodial fictício, submissão, recibo e relatório |
| 46 | 4 | Política lexical, handoff, rascunho de adjudicação e recibo |
| 47 | 2 | Política adversarial e relatório de bloqueios de evidência |
| 48 | 2 | Snapshot de PRs e relatório de prontidão |
| **Total** | **16** | **Amostras sintéticas de consistência estrutural** |

Não se cria nenhum estudo humano novo, nem se exporta o pacote A/B ou os textos das perguntas. O relatório público contém somente identificadores de contratos, quantidades de mutações rejeitadas e proibições operacionais.

## 3. Red team dos contratos

Para cada contrato são produzidas mudanças adversariais, verificando se a validação rejeita:

- Um atributo extra não previsto na raiz;
- A ausência do campo `version`;
- A troca de cada campo `const: false` efetivamente presente na amostra, **inclusive em estruturas aninhadas**, por `true`;
- A promoção de `decision` ou `status` para um estado de aceite fictício, quando o contrato explicita um valor obrigatório.

Todas essas operações usam cópias profundas para não alterar o objeto válido nem mascarar o resultado seguinte. O código **falha** quando o contrato aceita uma mutação que deveria recusar. A rotina também rejeita qualquer contrato fora da lista fechada ou ausente da árvore.

O número resultante de mutações rejeitadas é **cobertura de alterações artificiais nos contratos**, não número de falhas mecânicas, probabilidade de um evento no campo ou percentual de casos diagnosticados.

### Limites importantes

O teste de sucesso é apenas `Draft202012Validator(schema).validate(instance)`. Isso verifica o modelo estrutural que os autores definiram; **não verifica a verdade material dos fatos presentes no JSON**.

É possível que autor e código compartilhem o mesmo erro conceitual. Uma representação bem tipada de um componente ainda pode conter dados mecânicos incorretos.

O exercício cobre uma instância válida por contrato e mutações estruturais específicas. Não executa validação de todos os cenários possíveis, não resolve problemas de segurança de rede, semântica, identidade ou licenciamento, nem fornece validação formal completa.

Alguns campos de contratos representam mapas de hipóteses com chaves dinâmicas. Essas estruturas não devem ser rotuladas automaticamente como abertas por erro; precisam ser avaliadas à luz da semântica e do controle de chaves do domínio.

## 4. Resultados reproduzíveis e CI

A rotina:

```bash
python -m pip install jsonschema==4.23.0
python -m unittest tests.test_cycle49_contract_integration -v
python -m governance.cycle49_contract_integration \
  --output build/governance/cycle49-contract-audit.json \
  --markdown build/governance/cycle49-contract-audit.md
```

O workflow `.github/workflows/cycle49-contract-integration.yml` reproduz o mesmo processo em Python 3.12, verifica também o contrato do próprio relatório `contracts/cycle49-contract-audit.schema.json` e faz upload **somente das contagens e estados não confidenciais**.

A regressão geral do repositório continua obrigatória no PR. Uma aprovação do workflow específico não substitui a inspeção das mudanças por uma pessoa autorizada.

### Critérios de aceite

1. Cada uma das 16 instâncias artificiais deve passar no respectivo contrato;
2. Todos os casos de mutação previstos devem ser recusados por pelo menos uma regra do contrato;
3. A soma das mutações negativas não deve ser zero e seu denominador precisa constar no relatório;
4. O próprio relatório deve passar em JSON Schema, mantendo **NO GO**;
5. Nenhum dado privado de máquina, trabalho, pessoal, manual OEM, chave, gabarito ou parecer pode ser publicado;
6. Não pode haver promoção de `studyMayStart`, diagnóstico mecânico, escrita SAP/ECM, criação de OS ou liberação de equipamento.

## 5. Posição no fluxo de integração

O PR deste ciclo deve permanecer empilhado sobre o Ciclo 48. **Nenhum PR da cadeia #69–74 será mesclado automaticamente.**

A consolidação requer revisão de engenharia de software e segurança por um profissional, começando pelo PR #69 e seguindo a dependência. Alterações no código ou no contrato após essa revisão precisam repetir os testes de integração.

Também permanecem **13 gates externos não verificados** do Ciclo 48. A matriz nova não resolve nenhum deles: apenas reduz o risco de divergência entre contratos e objetos simulados.

**Decisão formal: `no_go_contract_alignment_is_not_external_mechanical_validation`.**

### Próximo passo concreto

Usar o relatório de contratos como material de apoio ao code review, investigar cada incompatibilidade que o CI encontrar e revisar os seis PRs em ordem. Só depois de avaliação humana da cadeia considerar integração à `main`. O estudo técnico independente continuará bloqueado enquanto faltarem autorização de casos, custódia, especialistas, OEM aplicável e método estatístico aprovado.
