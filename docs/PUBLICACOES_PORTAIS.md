# Ciclo 52 — Proveniência de publicação e comparação de snapshots

**Data do snapshot: 05/11/2026. Proposta de P&D em branch sobre o Ciclo 51.**

## Objetivo

Permitir a uma pessoa ou IA identificar **qual conteúdo foi entregue no GitHub Pages, por qual execução, a partir de qual commit** e distinguir o catálogo do primeiro deploy do catálogo atualizado nesta branch. Não inventar autenticação, aprovações ou acesso operacional.

## Atualização incremental do Ciclo 53

O deploy do Pages de 05/11/2026 foi confirmado novamente no commit `1ffa398b8d328a1f67dd49fbff7e37c3f0b82911`, execução [42057123105](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42057123105), com três HTMLs. O registro **`interfaces/publications.v2.json`** mantém a primeira entrada do v1 sem reescrevê-la e acrescenta um segundo recibo com hash Git de cada arquivo. O portal `versoes.html` permite comparar snapshots C51, C52 e a proposta atual. O terceiro ciclo de publicação, caso ocorra, exigirá conferência e novo recibo; não pode ser registrado antecipadamente. [Análise técnica](ACESSIBILIDADE_HISTORICO_53.md).

## Registro de publicação

O arquivo `interfaces/publications.v1.json` documenta o primeiro deploy do Pages, cujo workflow foi confirmado como concluído com sucesso em 05/11/2026. O registro preserva os identificadores do commit `ad9a9b3e321dfe696a8a816e5cdc17637f9f0afc`, da execução `42052320131`, o endereço informado no ambiente `github-pages` e os hashes Git dos dois HTMLs publicados. Esses dados foram obtidos do GitHub no ciclo; **não houve verificação HTTP independente da página, auditoria de identidade ou teste humano de acessibilidade**. Um hash Git é um identificador de conteúdo, não uma assinatura de especialista.

`interfaces/snapshots/c51-pages-deploy.v1.json` preserva o catálogo original da primeira publicação. `interfaces/catalog.v1.json` continua sendo a fonte de navegação ativa do código proposto e recebe um link de acesso a `portal/versoes.html`. O arquivo do baseline é **um snapshot histórico**, não outra fonte de edição.

## Interface humana

O novo `portal/versoes.html` fornece:

- Histórico do deploy confirmado, com fonte do GitHub Actions e links imutáveis para os arquivos no commit publicado;
- Comparação do **baseline do primeiro deploy** com o catálogo incorporado na versão consultada, incluindo inclusões, exclusões e alterações de campos;
- Filtro por caminho textual e tipo de mudança; exportação da diferença em JSON;
- Explicação de que diferenças de metadados não demonstram diagnóstico mecânico, validação de manuais OEM, competência de revisor ou autorização de manutenção.

A comparação **não é uma auditoria independente do GitHub ao vivo**. É uma comparação local de duas estruturas JSON preservadas nesta entrega, sem chamadas de rede do navegador. As páginas de conhecimento e auditoria recebem link de navegação para a nova visão, mas continuam estáticas e funcionais offline.

## Interface de IA e integridade

O script `governance/cycle52_publication_audit.py` valida o registro histórico, a estrutura do baseline, a igualdade entre os catálogos incorporados no portal e seus arquivos de origem, a sequência de releases, os limites de autoridade e as referências ao commit publicado. O script `scripts/sync_interfaces.py` passa a sincronizar três portais, e a comparação permanece reproduzível:

```bash
python -m pip install jsonschema==4.23.0
python scripts/sync_interfaces.py --write
python scripts/sync_interfaces.py --check
python -m governance.cycle52_publication_audit --check
python -m unittest tests.test_cycle51_interfaces tests.test_cycle52_publication -v
```

O novo workflow de CI também confirma a sintaxe JavaScript das três páginas e valida os schemas de publicação.

## Critérios de segurança e publicação

**NO GO** para testes físicos, OS, SAP, ECM, liberação de equipamentos e estudo técnico real. Os 13 gates externos do Ciclo 48 seguem não verificados. O histórico não deve publicar informações corporativas, manuais OEM licenciados, dados pessoais, telemetria nem segredos.

O primeiro deploy do Pages é evidência de publicação automatizada, não confirmação de que pessoas conseguem interpretar os resultados corretamente. Para uma nova publicação, revisar a interface e publicar **apenas HTMLs estáticos selecionados** por um workflow restrito, sem fazer merge dos PRs de pesquisa e sem disponibilizar material privado.

## Pendências reais

- Revisão humana do conteúdo e da usabilidade em desktop/mobile.
- Verificação HTTP independente do site e, se necessário, acessibilidade com navegador real.
- Revisão dos PRs #69–78 em sua ordem de dependências.
- Aprovação institucional de dados e estudo, quando for o caso.

**Decisão:** `no_go_publication_receipt_is_not_mechanical_or_human_certification`.
