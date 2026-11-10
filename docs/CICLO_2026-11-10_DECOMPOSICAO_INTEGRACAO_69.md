# Ciclo 69 — Desmembramento real da pilha de pesquisa e plano de integração por dependência

**10/11/2026 · P&D Maintenance Superintelligence · NO GO · sem merge**

## Decisão

O objetivo deixou de ser somar módulos ao PR empilhado. O C69 **extraiu dois módulos autocontidos para PRs pequenos baseados diretamente na `main`**, criou um mapa de dependências para os demais e manteve os blocos antigos de pesquisa sem merge automático.

### Comparação observada antes da extração

A ferramenta de comparação GitHub informou `main...research/cycle68-integration-ci-remediation` com estado **diverged**, **311 commits à frente**, **11 atrás** e **169 arquivos no diff**. A referência da `main` era `e0789a780c07cdd19ea1ddf3f11a1f24481c7ad0`. É uma fotografia da consulta, **não** atualização em tempo real nem confirmação de mergeability futura. O risco é levar mudanças não relacionadas e disputas de histórico se toda a cadeia for mesclada de uma só vez.

## Pilotos concretos preparados (base `main`)

| Piloto | PR em Draft | Head do piloto | Escopo (4 arquivos) |
|---|---|---|---|
| C58, hipóteses e previsões estruturais | [#95](https://github.com/pedromaintenance/maintenancesuperinteligence/pull/95) | `integration/cycle69-pilot-c58-causal-gate` | `benchmarks/cycle58_causal_gate.py`, `tests/test_cycle58_causal_gate.py`, workflow próprio e documentação |
| C60, metrologia dimensional sintética | [#96](https://github.com/pedromaintenance/maintenancesuperinteligence/pull/96) | `integration/cycle69-pilot-c60-metrology` | `benchmarks/cycle60_metrology.py`, `tests/test_cycle60_metrology.py`, workflow próprio e documentação |

**Os dois PRs são paralelos e independentes entre si.** Em `main`, os oito caminhos não existiam no momento da consulta. O C58 não importa C59 nem C57; o C60 não importa C58–59 nem C61–68. São módulos offline de biblioteca padrão para **somente dados inventados**.

### Achado e correção no piloto C60

A primeira execução do workflow C60 falhou: o módulo não dependia de C58/C59, mas seu workflow carregado da pesquisa ainda invocava `tests.test_cycle58_causal_gate` e `tests.test_cycle59_observation_consistency`, ausentes propositalmente no PR pequeno. O workflow do piloto foi corrigido para executar **somente** `tests.test_cycle60_metrology`. Essa correção foi aplicada apenas na branch do PR #96 e o CI específico foi aprovado no commit `37965c7`. É evidência de isolamento efetivo do piloto, não validação física.

## Mapa de extrações futuras

Cada unidade abaixo deve ser criada como **novo PR pequeno sobre uma base efetivamente contendo suas dependências aprovadas**, nunca por copiar a cadeia inteira. Não foram abertos PRs desses módulos neste ciclo.

| Ordem | Módulo | Dependência direta | Situação |
|---|---|---|---|
| 1 | C58: causalidade estrutural | Nenhuma | PR #95 em Draft |
| 2 | C60: metrologia sintética | Nenhuma | PR #96 em Draft |
| 3 | C59: previsões × observações | C58 | Planejado |
| 4 | C61: contexto de medição | C60 | Planejado |
| 5 | C62: semântica de referências | C60 e C61 | Planejado |
| 6 | C63: efetividade sintética | C62 | Planejado |
| 7 | C64: governança documental | C63 | Planejado |
| 8 | C65: trilha de revisão fictícia | C64 | Planejado |
| 9 | C66: pré-registro de estudo | C65 | Planejado |

A ordem é **topológica**, não uma ordem obrigatória de aprovação: unidades em ramos diferentes podem ser revisadas em paralelo; uma unidade dependente só deve ser proposta contra base contendo suas dependências e revisões aceitas.

Os módulos de auditoria C67 e C68 permanecem na pesquisa, pois seu inventário e contratos apontam para a cadeia original; precisarão de reestruturação após as extrações, não de *cherry-pick* cego.

## Artefatos desta fase

- `benchmarks/cycle69-isolated-integration-plan.v1.json`: fotografia da `main`, dois PRs pilotos, nove módulos e suas dependências diretas, grupos temáticos, escopos, revisão obrigatória e bloqueios.
- `benchmarks/cycle69_release_plan.py`: auditor offline de ordem topológica, imports Python declarados, existência de artefatos, vínculo com inventário C67, composição de pilotos, base `main` e flags de autoridade.
- `tests/test_cycle69_release_plan.py`: regressão positiva e adulterações adversariais (ordem, dependência, arquivo, SHA, suposta aprovação, falsa leitura ao vivo, merge incorreto).
- `.github/workflows/cycle69-release-plan.yml`: produz recibo JSON sintético e roda testes da pesquisa C58–69.

O auditor **não consulta GitHub ao vivo**, não verifica estados reais de CI/branch protection, não autentica o PR e **não executa merge**. Sua declaração `planStatus=pass` significa coerência do manifesto e dos imports, não aptidão para a `main`.

## Portões antes de aprovar cada PR pequeno

1. CI verde na SHA exata, diff apenas dos arquivos esperados, sem dependências residuais ou dados restritos.
2. Revisão humana do código, políticas de licenciamento e acesso, comportamento sem escrita/execução, e documentação da semântica `NO GO`.
3. Verificar novamente a `main` e a branch base no momento da decisão; não usar snapshots antigos.
4. Se um módulo depender de outro, exigir base contendo a dependência aprovada e rodar regressão de todos os módulos da sua subcadeia.
5. Revisão de engenharia e documentação OEM reais **não** acontecem neste ciclo. O resultado sintético não pode autorizar medição, OS, SAP/ECM ou liberação.

## Comandos

```bash
python -m unittest tests.test_cycle69_release_plan -v
python -m benchmarks.cycle69_release_plan --output /tmp/c69-plano-auditado-novo.json
```

A suíte no workflow C69 também inclui C58–68 para regressão. O módulo não depende de bibliotecas externas; os resultados são públicos e fictícios.

**Decisão:** `NO GO` operacional. Nenhuma proposta foi mesclada à `main`. PRs #95 e #96 só se tornam candidatos a aprovação após revisão humana explícita.
