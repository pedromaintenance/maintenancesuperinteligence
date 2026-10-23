# Changelog

## 0.5.0 — 2026-10-23 — Ciclo 05

- Criado catálogo de 14 métodos diagnósticos conceituais nas áreas de óleo, hidráulica, mecânica, vibração e eletrônica.
- Criados seis contratos JSON Schema para método, pré-requisito, observação esperada, limite de interpretação, efetividade e catálogo, além de schema do registro de fontes.
- Criado registro de seis fontes técnicas gerais de fabricantes, preservando limitações e procedência FMEA onde aplicável.
- Vinculados os seis códigos únicos `EV-*` às oito investigações das quatro cadeias de comandos finais no snapshot FMEA público pinado.
- Implementada CLI que reconstrói a investigação validada, confere a procedência, emite perguntas e lacunas sem realizar testes nem importar parâmetros OEM.
- Adicionados testes adversariais por disciplina e geração automatizada dos quatro planos conceituais no CI.

**Limite:** biblioteca não é um manual de execução; métodos sem literatura por série permanecem não homologados.


## 0.4.0 — 2026-10-22 — Ciclo 04

- Criados cinco contratos versionados para observação, método de teste, resultado, evidência e avaliação de hipótese, além do contrato agregador `EvidenceLedger`.
- Ampliado o investigador didático CAT 777E para saída v2 contendo observações com origem, oito métodos propostos, interpretações vinculadas, sete hipóteses abertas e revisão humana pendente.
- Incluída possibilidade de `TestResult` explicitamente sintético, sem inferir execução OEM, causalidade confirmada ou nova liberação operacional.
- Adicionada cadeia determinística de seis hashes SHA-256 e validação cruzada com o caso original e as hipóteses, inclusive contra adulterações localmente recalculadas.
- Estendidos os testes adversariais e a execução CI para validar os quatro cenários e um resultado simulado separado.

**Limite:** hashes não substituem autenticação, assinatura digital nem cadeia de custódia de evidência de campo.


## 0.3.0 — 2026-10-22 — Ciclo 03

- Implementado primeiro investigador diferencial **estritamente didático** de comandos finais, contextualizado à CAT 777E sem fingir homologação OEM.
- Usadas quatro cadeias FMEA do snapshot público pinado; mantidas três alternativas autorais explícitas e oito investigações não executadas.
- Criados contrato JSON Schema, 4 cenários sintéticos, testes de ausência de diagnósticos indevidos e avaliação de divergência.
- Implementado vínculo forte entre o snapshot SHA-256 real e o índice de consumo para evitar resultados de arquivo local adulterado.
- CI gera relatórios JSON didáticos como artefatos temporários, sem confundir testes simulados com resultados de campo.

**Fora de escopo:** telemetria real, laudos corporativos, interpretação livre por LLM, efetividade OEM por série, decisões SAP e autorização operacional.


## 0.2.0 — 2026-10-22 — Ciclo 02

- Implementado importador **read-only** do snapshot público FMEA Mining conteúdo 1.0.0 (preview histórico 1.3.12), pinado por commit e SHA-256.
- Adicionados gates de integridade, campos autorizados, aplicabilidade vazia por série e proibição de causa/evidência/uso operacional confirmados.
- Criado índice conceitual transitório de 24 cadeias e 20 fontes, com recibo auditável.
- Adicionada suíte de testes adversariais e CI com importação efetiva do snapshot público e artefato temporário.
- Delimitado o próximo piloto em comandos finais, **sem** alegar aplicabilidade OEM para CAT 777E.

**Não implementado:** raciocínio diagnóstico interativo, execução de testes, previsão de falhas, escrita SAP, software embarcado e controle de equipamentos.


## 0.1.0 — 2026-10-22

- Formalizada arquitetura de P&D, fronteiras de segurança e diretrizes de validação.
- Mapeadas 56 habilidades existentes no jogo (22 disciplinas, 25 sistemas e 9 modelos).
- Registradas capacidades, limites, estatísticas e contrato público do FMEA Database.
- Criados registro inicial de fontes, afirmações atômicas, lacunas e schemas de referência.
- Criado validador **offline básico** de integridade de metadados e referências.
- Definido primeiro piloto didático de diagnóstico diferencial de comando final.

Nenhuma funcionalidade de IA, telemetria, SAP ou integração OEM de execução foi implementada.
