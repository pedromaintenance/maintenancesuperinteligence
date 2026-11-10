# Ciclo 67 — Auditoria de consolidação e estratégia de integração

**09/11/2026 · P&D · base: Ciclo 66 · PR em Draft · NO GO**

## Decisão de arquitetura

Interromper temporariamente a adição de novos motores de diagnóstico e **auditar o conjunto existente**. Os Ciclos 58–66 acrescentaram nove módulos de pesquisa com testes sintéticos, mas estão empilhados sobre o Ciclo 57 e não foram integrados à `main`. A qualidade de testes locais não basta para aprovar integração nem prontidão operacional.

**Observação verificada na criação do C67 (snapshot, não monitoramento ao vivo):** PRs #83–#92 `open` e `draft`; cada PR #84–#92 é baseado na branch anterior. Na comparação GitHub `main...research/cycle66-independent-study-preregistration`, a árvore estava **diverged**, com **286 commits à frente, 11 atrás e 159 arquivos no diff**. Esses números são fotografia da consulta de 09/11 e podem mudar. O commit `main` da comparação foi `e0789a780c07cdd19ea1ddf3f11a1f24481c7ad0`. Não selecionar `merge` ou `rebase` sem revisão de conflitos com mudanças recentes da `main`.

## Artefatos do ciclo

- `benchmarks/cycle67-consolidation-inventory.v1.json`: inventário congelado da cadeia de PRs, paths por ciclo, dependência direta, sobreposição conceitual e impedimentos humanos/externos. **Não** consulta GitHub em tempo real.
- `benchmarks/cycle67_architecture_audit.py`: valida paths de módulos/testes/workflows/docs, árvore AST, imports declarados, número de métodos de teste definidos, cobertura de invocação acumulada nos workflows, smoke de `fixture()` e invariantes `NO GO` de C58–C66.
- `tests/test_cycle67_architecture_audit.py`: testes positivos e de adulteração do inventário, caminhos ausentes, dependências incorretas, falsa confirmação de merge e divergência de branch.
- `.github/workflows/cycle67-consolidation-audit.yml`: executa a regressão C58–C67, gera um recibo JSON e o publica como artefato do GitHub Actions. Não acessa SAP, ECM, dados de campo nem manual OEM.

O status `inventoryStatus=pass` significa **consistência estrutural do inventário e smoke dos exemplos artificiais**. `testMethodDefinitions` é contagem de testes declarados no código, **não cobertura de linhas ou validação de física**. `readyForMerge=false` e `decision=NO GO` são invariantes independentes do resultado.

## Matriz técnica de dependências

| Ciclo | Função do incremento | Dependência de código direta |
| --- | --- | --- |
| 58 | Portão de hipóteses e previsões | Independente |
| 59 | Rótulos de observação versus previsões | C58 |
| 60 | Dimensões e incerteza intervalar | Independente |
| 61 | Contexto da medida e instrumento fictício | C60 |
| 62 | Semântica de referências | C60 (conversões SI) e C61 (contexto) |
| 63 | Metadados de aplicabilidade | C62 |
| 64 | Linhagens, revogação e conflitos de fonte | C63 |
| 65 | Pareceres e contestação simulados | C64 |
| 66 | Pré-registro sintético de estudo independente | C65 |

**Nota:** dependência de código não é equivalente a ordem de PRs; a cadeia Git contém C57–66 em sequência. C58–59 e C60 são linhas parcialmente independentes que podem ser analisadas separadamente antes de consolidar.

## Achados e riscos a resolver

1. **Integração divergiu da `main` (bloqueante para merge indiscriminado):** 286 ahead/11 behind no snapshot. A diferença inclui trabalho de muitos ciclos, não apenas C58–66. É necessário comparar, revisar e reduzir escopo antes de reaplicar commits.
2. **Gatilhos de CI incompletos em dependências:** C61–C66 executam testes cumulativos, mas seus filtros `paths` não incluem o módulo/teste imediatamente anterior. A auditoria marca esses seis workflows como `upstream_path_filter_gap` (sete relações ausentes: C62 depende diretamente de C60 e C61). Uma modificação posterior de C60, por exemplo, não garante a execução do workflow específico de C61. Corrigir os filtros ou adotar um workflow único de regressão obrigatório antes do merge.
3. **Sobreposição deliberada:** C58–59 compartilham semântica de hipótese; C60–62 trabalham a mesma estrutura de quantidades; C64–66 formalizam partes de um fluxo documental. Não são necessariamente duplicações erradas, mas ainda carecem de interfaces e dono de contrato formal.
4. **Revisão e custódia já existem na pesquisa anterior:** C29–30–32 descrevem cegamento e custódia privados. C65–66 são simulações de conflito e pré-registro e não devem substituí-los. Conciliar denominadores, escopo, taxonomia e controle de identidade.
5. **Evidência humana e externa ausente:** o relatório C57 registra oito verificações humanas `not_tested` e 13 gates externos não verificados. Não houve homologação independente de precisão mecânica nem efetividade OEM em C58–66.
6. **Cadeias SHA-256 não significam autoria ou custódia imutável:** a simulação C65 permite reconstruir os hashes após edição integral do arquivo. Qualquer audit trail efetivo precisará de infraestrutura externa de custódia, identidade, acesso e registro temporal.

## Estratégia de integração proposta — sem merge neste ciclo

**Etapa A — Reconciliação da pesquisa.** Atualizar a comparação com `main`, revisar os 159 caminhos do snapshot conforme diff atual, separar arquivos já incorporados seletivamente e registrar riscos de histórico. Atualizar inventário com evidências atuais após qualquer rebase.

**Etapa B — Higiene de contratos e CI.** Corrigir os seis filtros incompletos; documentar APIs estáveis entre C58–66; evitar repetir regras de autoridade de forma inconsistente. Exercitar adversarialmente todas as saídas que mencionem validade ou decisão e não tratar 156+ métodos declarados como medição de qualidade mecânica.

**Etapa C — Revisão por disciplina.** Separar módulos em: `hipóteses/evidências textuais` (58–59), `metrologia/referências` (60–63) e `governança documental/estudos` (64–66). Engenharia mecânica, gestão documental e segurança/TI devem revisar os pressupostos correspondentes. Esses revisores **ainda não foram envolvidos**.

**Etapa D — Integração de baixo risco.** Só após A–C e aprovação humana do código, selecionar integração **offline e com escopo mínimo**, preferencialmente em PR pequeno sobre a `main`, mantendo todos os flags de autoridade negados. Não ativar entrada de dados reais, conexões a SAP/ECM, avaliação OEM ou decisão automatizada.

**Etapa E — Estudo independente verdadeiro.** Preparar autorização institucional, permissão de literatura/casos, custódia privada, cegamento de gabaritos e revisão externa conforme C29–32 e os requisitos planejados do C66. Isso permanece independente do merge de utilitários públicos.

## Como executar a auditoria

```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics tests.test_cycle63_effectivity tests.test_cycle64_source_governance tests.test_cycle65_review_ledger tests.test_cycle66_study_preregistration tests.test_cycle67_architecture_audit -v
mkdir -p build/cycle67
python -m benchmarks.cycle67_architecture_audit --output build/cycle67/consolidation-audit.json
```

O recibo fica no GitHub Actions para inspeção. O script falha com retorno não zero se houver erro estrutural, mas retorna `NO GO` mesmo após auditoria bem-sucedida. Nenhum resultado do CI é apresentado como prova de teste humano, valoração OEM, causa raiz ou autorização para OS, SAP, ECM, teste físico ou liberação de máquina.

**Decisão C67: NO GO operacional e NÃO MESCLAR AUTOMATICAMENTE.**
