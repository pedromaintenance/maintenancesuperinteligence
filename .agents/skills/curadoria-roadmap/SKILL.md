---
name: curadoria-roadmap
description: Rastrear iniciativas, dependências, pendências e fontes de verdade sem inventar progresso na Maintenance Superintelligence.
---

# Skill — Curadoria de roadmap e interfaces

## Quando usar
Ao solicitar novo ciclo, priorização de backlog, documentação de capacidades ou atualização de portais.

## Procedimento
1. Leia `AGENTS.md`, `docs/ROADMAP.md` e `interfaces/catalog.v1.json`.
2. Distinga o histórico do roadmap (visão de P&D) do catálogo de navegação (snapshot público).
3. Para cada item, informe: **objetivo, estado verificável, origem, dependência, risco, critério de aceite e próximo responsável**.
4. Se houver referência a PR/checks **atuais**, consulte GitHub. Não declare status live a partir do catálogo estático.
5. Ao alterar entradas do catálogo, confirme caminhos e status de NO GO. Rode `python scripts/sync_interfaces.py --write`, seguido de `--check`.
6. Inspecione impacto nos portais standalone `portal/index.html` e `portal/auditoria.html`.
7. Para alterações de engenharia, mantenha PR em revisão; nunca faça merge ou modifique permissões apenas por testes sintéticos.

## Saída
`ID | descrição | dependências | status | fonte | evidência faltante | próximo passo | gate de aprovação`.

## Proibições
Não dar por concluído gate externo por contagem de testes. Não tratar agentes de Markdown como processos em execução, nem HTML como dashboard com integração real.

## Referências
`governance/cycle48-study-readiness.v1.json`, `docs/CICLO_2026-11-05_PRONTIDAO_ESTUDO_48.md`, `docs/ROADMAP.md`.
