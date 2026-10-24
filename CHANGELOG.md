# Changelog

## 0.9.0 — 2026-10-24 — Ciclo 09

- Documentada arquitetura **proposta** de revisão técnica restrita, separando conhecimento público, credenciais, evidências, séries, dados SAP/ECM e literatura OEM licenciada.
- Modelo de ameaças cobre impersonação, autorrevisão, aliases de mesmo revisor, papel/competência, revogação, replay, revisão obsoleta, adulteração e vazamento.
- Criado protótipo offline `governance/restricted_blueprint.py` com três sequências e nove eventos `SIM-*`: separação de papéis, versionamento, nonce único, divergência, adjudicação fictícia e hashes de integridade.
- Introduzidos cinco contratos JSON Schema para pessoa fictícia, evento, caso, fixture e registro auditável.
- Adicionados testes adversariais e etapa CI que rejeita relatório adulterado, nonce repetido, suposta aprovação OEM e autoridade operacional.
- Referências técnicas de especificação: NIST SP 800-63-4, OWASP ASVS 5 e LGPD. **Nenhuma conformidade normativa ou autenticação real é reivindicada.**

**Limite:** não há ambiente restrito implantado, identidade verificada, assinatura, autorização de dados de campo ou aprovação de equipamento.


## 0.8.0 — 2026-10-24 — Ciclo 08

- Implementado workflow de governança `governance/review.py` com 8 afirmações editoriais, 9 citações de referências gerais e 13 pareceres fictícios.
- Introduzidos oito contratos versionados para afirmação, referência, evidência de aplicabilidade, revisor fictício, parecer, divergência, decisão e pacote de revisão.
- Definidos estados derivados de rascunho, revisão pendente, necessidade de evidência, divergência e consenso fictício de referência geral; `oem_series_verified` bloqueado no repositório público.
- Adicionados controles de vínculo método/fonte/par, revisor por competência declarada, duas personas distintas, segunda rodada com IDs novos, contraexemplo obrigatório e rejeição de parecer assinado ou credencial/autorização indevidamente atestada.
- Benchmark do Ciclo 07 agora exige integridade do pacote de governança e informa `technicalReviewGate`, impedindo interpretar resultado sintético como validade diagnóstica real.
- CI verifica relatório de divergências, bloqueios operacionais e rejeição de credenciais falsificadas; adicionados testes adversariais e documentação.

**Limite:** não houve revisão de engenharia por pessoa identificada; critérios OEM por série e cadeia real de custódia seguem pendentes.


## 0.7.0 — 2026-10-23 — Ciclo 07

- Introduzido benchmark versionado de **15 casos sintéticos**, cinco para cada domínio (comando final, hidráulica e eletrônica), com respostas esperadas editoriais independentes da função que executa a seleção.
- Criada rubrica com nove classes de falha e contratos JSON Schema: fixture, evidência disponível, abstenção, rubrica e manifesto.
- Implementado avaliador determinístico de regressões (`benchmarks/quality.py`) para proveniência, ambiguidade, contradições, segurança, efetividade, pré-requisitos, escolha e reprodutibilidade; relatório com hashes e métricas sempre rotuladas como não empíricas.
- Adicionados testes adversariais de manipulação de oráculo, falsa autoridade, vínculos de evidência, contextualização e hipóteses promovidas.
- CI valida casos originais e detecta propositalmente um oráculo corrompido; publica relatório temporário de regressões.

**Limite:** nenhum ground truth de campo, especialista revisor independente, medida de acurácia diagnóstica ou autorização OEM foi adquirido.


## 0.6.0 — 2026-10-23 — Ciclo 06

- Adicionada matriz editorial versionada de dez pares de hipóteses concorrentes em comando final, hidráulica e eletrônica.
- Implementada seleção determinística de perguntas com distinção entre contexto desconhecido, contraditório, não aplicável e simulado disponível, sem ranking probabilístico arbitrário.
- Criados três cenários didáticos, quatro schemas, testes de referências circulares, origem falsa, resultados inventados, informação OEM não verificada e emissão de ordens.
- CI produz três artefatos temporários e verifica que métodos e resultados permanecem pendentes de teste/revisão humana.

**Não implementado:** estimativa validada de acurácia, custos ou decisão real de manutenção.


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
