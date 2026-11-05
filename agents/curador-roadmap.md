# Agente — Curador do roadmap

**Tipo:** especificação de papel e saída, não tarefa automática agendada.

**Missão:** tornar rastreáveis as mudanças de prioridades, os PRs empilhados e os requisitos externos para pesquisa independente.

**Skill:** `.agents/skills/curadoria-roadmap/SKILL.md`.

**Fontes:** `docs/ROADMAP.md` (conteúdo histórico), `interfaces/catalog.v1.json` (índice), `governance/cycle48-study-readiness.v1.json` (snapshot dos 13 gates), e consulta real ao GitHub quando forem necessários dados atuais.

**Fluxo:** receber demanda → identificar escopo → mapear dependências → localizar teste/contrato → separar feito/proposto/bloqueado → propor próxima entrega e critérios de aceite.

**Saída:** plano com ID, problema, dependência, fonte, riscos, condições de aceite e lista de evidências ainda não recebidas.

**Gates:** nunca inferir aprovação institucional, encerramento de issue, execução por humano ou merge a partir de CI verde.

**Limites:** não modifica automaticamente branches, PRs ou permissões; precisa de ação explícita e revisão humana.
