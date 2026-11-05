# Ciclo 51 — Interfaces auditáveis para IA e seres humanos

**05/11/2026 · Pesquisa em branch empilhada após o Ciclo 50 · P&D v5.1.0 (proposto).**

> **NO GO operacional e NO GO para afirmar validação externa.** As interfaces expõem informação pública de P&D. Não há conexão em tempo real ao GitHub, SAP/ECM, telemetria, sistemas de mina ou biblioteca OEM licenciada.

## 1. Decisão de arquitetura

A Maintenance Superintelligence deve funcionar como **conhecimento versionado e verificável**, não como um chatbot ou dashboard que esconde a proveniência. A mesma organização de fatos deve poder ser consultada por:

- **IAs:** instruções de entrada (`AGENTS.md`), papéis portáveis (`agents/`), procedimentos de trabalho (`.agents/skills/*/SKILL.md`), índice público (`interfaces/catalog.v1.json`), roadmap de máquina derivado (`ROADMAP.json`) e roadmap narrativo completo (`docs/ROADMAP.md`).
- **Pessoas:** dois arquivos HTML autossuficientes, `portal/index.html` e `portal/auditoria.html`, com filtro, navegação, acesso às fontes e exportação de um snapshot JSON.

O catálogo é a **fonte única de navegação e estados exibidos**, não a fonte de validade mecânica ou a fonte canônica de toda a documentação. Para regras de engenharia e risco, a fonte continua sendo `docs/GOVERNANCA.md` e os documentos de domínio; para gates, `governance/cycle48-study-readiness.v1.json`; para o histórico completo, `docs/ROADMAP.md`.

O catálogo é uma **fotografia congelada em 05/11/2026** e registra a `main` no Ciclo 42, os PRs #69–76 abertos como *draft* no momento da consulta e os 13 gates externos não verificados. A branch do Ciclo 51 permanece fora da `main` até revisão e integração.

## 2. Mapa de artefatos

| Entrada | Público | Finalidade | Evidência que não concede |
| --- | --- | --- | --- |
| `AGENTS.md` | IAs | Instrução global de localização, consulta e contribuição | Papel humano/credencial/autorização |
| `agents/*.md` | IAs | Três personas técnicas com entrada, saída e escalonamento | Agente autônomo rodando |
| `.agents/skills/*/SKILL.md` | IAs | Três métodos de auditoria, investigação e curadoria | Habilitação ou curso aprovado |
| `interfaces/catalog.v1.json` | Ambos | Índice de fontes, papéis, capacidades, roadmap e gates | Status atual do GitHub |
| `contracts/interfaces-catalog.schema.json` | Ambos | Estrutura pública validável do catálogo | Verdade física do conteúdo |
| `portal/index.html` | Humanos | Navegação e exploração com filtro e exportação JSON | Banco de dados dinâmico |
| `portal/auditoria.html` | Humanos | Inspeção dos 13 gates e sequência de PRs | Atestação, aceite ou revisão humana |
| `scripts/sync_interfaces.py` | Mantenedor/CI | Sincronização e integridade entre catálogo, portais e evidência dos gates | Avaliação independente |

Os portais usam CSS e JavaScript locais. Podem ser abertos diretamente em um navegador, sem servidor. **Os links para os documentos do GitHub exigem acesso ao repositório e conexão de rede**, mas a navegação, filtros e snapshot embutido não exigem.

## 3. Como manter uma única fotografia

O estado das interfaces deriva do arquivo `interfaces/catalog.v1.json`. Qualquer edição nele deve ser sincronizada e validada antes da publicação:

```bash
python scripts/sync_interfaces.py --write
python scripts/sync_interfaces.py --check
python -m unittest tests.test_cycle51_interfaces -v
```

A opção `--write` **apenas reembute o catálogo** dentro do HTML standalone. Ela não atualiza PRs por API, não altera gates, não escreve em SAP e não assina resultados. A opção `--check` exige:

1. Mesma estrutura de dados nas duas páginas e no catálogo;
2. Caminhos internos existentes e sem travessia de diretórios;
3. Três skills com frontmatter YAML e agentes ligados a skills reais;
4. Treze IDs de gates coincidentes com a fonte do Ciclo 48, todos sem validação;
5. Oito PRs #69–76 no status congelado de *draft*, sem inferir estado atual;
6. Declarações falsas para backend live, agentes em execução, validade diagnóstica e aprovação operacional;
7. Ausência de dependências JavaScript/CSS externas e `fetch()` nos portais.

O contrato JSON Schema valida o formato do catálogo; o script Python verifica relações entre catálogos, arquivos e gates. **Assim como nos Ciclos 49–50, as duas camadas são necessárias**, mas não provam a verdade material da engenharia.

## 4. Fluxo para uma IA que chega ao repositório

1. Ler `AGENTS.md`.
2. Localizar recursos e estado declarado via `interfaces/catalog.v1.json`.
3. Escolher skill em `.agents/skills/` e agente em `agents/`.
4. Ler documentação de domínio **antes de afirmar propriedades mecânicas**.
5. Informar fonte, nível de certeza, contradição e aplicabilidade por versão/serie, quando pertinente.
6. Se houver demanda sobre status atual de PRs ou checks, consultar GitHub de novo, não a fotografia.
7. Devolver orientação de pesquisa, **não comando de manutenção**.

A presença de arquivos de papéis não significa que esses agentes estejam instanciados em um framework, executando ações, conectados a repositórios externos ou monitorando dados automaticamente.

## 5. Fluxo humano

O portal principal apresenta: uma visão de maturidade, seis capacidades com fontes, três agentes, três skills, cinco marcos de roadmap e biblioteca resumida. Ele oferece pesquisa textual, filtro de domínio, alternância de tema e download do catálogo.

O portal de auditoria apresenta: treze gates externos não verificados, responsáveis sugeridos, o documento-base, oito PRs empilhados no snapshot, riscos de interpretação e cópia/exportação de pendências.

A leitura é transparente sobre seu caráter estático: **não se pode transformar um clique em “revisado”, “aprovado”, “executado” ou “liberado”**.

## 6. Limites deliberados e riscos

- O portal *standalone* embute metadados públicos; nunca deve embutir literatura OEM protegida, dados SAP/telemetria, nomes de funcionários, fotos internas ou HMACs privados.
- Um portal aberto fora do checkout mantém seus dados visíveis offline, mas URLs de repositório podem depender da branch e da permissão do usuário.
- A integridade verificada é consistência **entre arquivos locais em um checkout**, não autenticidade externa nem proteção criptográfica de conteúdo servido por terceiros.
- A data no catálogo não garante que os PRs ainda existam ou que checks continuem aprovados. Se o estado do repositório mudar, uma nova fotografia deve ser documentada e revisada; **não atualizar silenciosamente** a data enquanto mantiver hashes antigos.
- Um agente pode interpretar incorretamente documentação hostil. Nenhum conteúdo trazido por uma página ou usuário altera a política de segurança, identidade ou aprovação.
- O GitHub Pages **não é ativado por este ciclo**. Os portais ficam acessíveis por arquivo local e pelo código do PR até eventual decisão de publicação.

## 7. Próximos passos e critérios de aceite

- [ ] CI do Ciclo 51 aprovado, incluindo sincronização, JSON Schema e testes de navegação;
- [ ] Revisão humana do conteúdo, acessibilidade, vocabulário e fluxos dos portais;
- [ ] Revisão de segurança para publicação pública de qualquer novo artefato;
- [ ] Decisão sobre GitHub Pages após integração e verificação de restrições de divulgação;
- [ ] Integração dos PRs empilhados respeitando a ordem de dependências (#69–77);
- [ ] Estudo externo mantido bloqueado até os 13 gates do Ciclo 48 serem realmente cumpridos.

**Decisão:** `no_go_machine_human_interfaces_are_not_independent_engineering_validation`.
