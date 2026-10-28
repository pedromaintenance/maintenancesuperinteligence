# Changelog

## 2.8.0 — 2026-10-27 — Ciclo 28

- Construído conjunto adicional de 34 desafios sintéticos fora das sequências fixas do Ciclo 27: 32 em quatro domínios conhecidos e 2 domínios não modelados.
- Comparada seleção original de perguntas com uma barreira de confiabilidade documental que explicita fontes não verificadas, contraditórias, obsoletas e revogadas.
- Resultados discriminados por casos modelados, não modelados, concordância editorial de linha-base e versão com barreira.
- Criados contratos JSON Schema, testes metamórficos/adversariais, relatório JSON/HTML offline e validação no CI.
- **Limite:** dados sintéticos, gabarito autoral, sem avaliação cega externa ou precisão diagnóstica de campo.


## 2.7.0 — 2026-10-27 — Ciclo 27

- Introduzidos 24 cenários de teste de raciocínio diferencial em quatro domínios (comando final, hidráulica, eletrônica e arrefecimento).
- Motor determinístico identifica contradições e lacunas documentais antes de escolher pergunta; mantém todas as hipóteses abertas e recomenda revisão ao completar o contexto.
- Gabarito editorial separado da lógica, métricas de concordância por domínio, testes metamórficos/adversariais, contratos JSON Schema e relatório JSON/HTML estático.
- Integração ao CI, sem limites OEM inventados, diagnóstico validado, medição física, OS, testes ou liberação de equipamento.

**Limite:** benchmark de regressão autoral, sem revisão mecânica independente, validade empírica ou precisão diagnóstica demonstrada.


## 2.6.0 — 2026-10-27 — Ciclo 26

- Criados dez cenários sintéticos de contestação, revogação, versões obsoletas, conflitos de interesse, dissenso e alegações de aprovação.
- Cadeia SHA-256 reconstruível por cenário; duas perspectivas fictícias preservadas, sete gates não comprovados e veto persistente.
- Dois contratos JSON Schema, testes adversariais, relatório offline JSON/HTML e gate CI derivado dos Ciclos 24 e 25 verificados.
- Zero assinaturas reais, revisores autenticados, aceite OEM, dados corporativos ou autorização SAP/ECM.

## 2.5.0 — 2026-10-27 — Ciclo 25

- Dez pacotes de revisão documental a partir de propostas do Ciclo 24, sete lacunas por proposta e cinco objeções por áreas simuladas.
- Hash de vínculo ao relatório de origem, contrato JSON Schema de envelope, testes adversariais e CI com publicação de relatórios.
- Sem alteração do grafo canônico e decisão `no_go`.


## 2.4.0 — 2026-10-27 — Ciclo 24

- Criado revisor independente de **dez propostas fictícias de alteração do grafo** dos Ciclos 20–23, com diff de arestas, trocas de responsáveis, rejeição de supressão, ciclo e IDs desconhecidos.
- Comparação de **169 pares possíveis** de alcance por grafo válido, distância mínima, contagem de caminhos e impacto em **100 casos** de regressão documental, usando oráculo Floyd–Warshall e precondições canônicas.
- Testes de monotonicidade (adição não elimina alcance; remoção não cria alcance), veto de inversão sem parecer humano, invalidação editorial após hipótese de revisão OEM e controle de sigilo.
- Gerados `pilot/graph-change-proposals.v1.json`, `pilot/graph_change_review.py`, 11 contratos JSON Schema, testes adversariais, CI e relatório offline JSON/HTML.
- Nenhuma proposta edita o arquivo vigente; assinatura, identidade, competência, efetividade OEM e alçada real permanecem não verificadas.

**Limite:** regressão sintética sobre dependências documentais, não conformidade de engenharia, decisão de intervenção, operação SAP ou mudança corporativa autorizada.


## 2.3.0 — 2026-10-27 — Ciclo 23

- Criado oráculo versionado de 100 casos estruturais: 13 raízes, 78 pares, três mudanças de versão/identidade/configuração e seis cenários de contradição herdados.
- Implementada verificação independente por matriz Floyd–Warshall de distâncias e caminhos, confrontada com reconstrução DFS e fecho transitivo do Ciclo 22; 13 controles e 17 arestas canônicos preservados.
- Adicionados caminhos documentais explicáveis por etapa, alternativas redundantes e testemunhos de controles não alcançados sem concluir segurança de máquina.
- Fixadas cinco mutações adversariais de remoção, inversão, adição, supressão de ameaça e atalho indevido; testes de falsificação de resultado, metadados e permissões.
- Publicados `pilot/reopen-coverage.v1.json`, `pilot/reopen_coverage.py`, dez JSON Schemas, testes, documentação e relatório JSON/HTML offline de 100 casos.
- GitHub Actions valida o corpus completo FMEA público e os ciclos anteriores; decisão obrigatória `no_go`, sem comprovação OEM, identidade humana ou intervenção.

**Limite:** cobertura de regressões sintéticas do grafo público, não validação de engenharia de campo nem garantia universal de software.


## 2.2.0 — 2026-10-27 — Ciclo 22

- Criados `pilot/evidence-contradictions.v1.json` e `pilot/evidence_contradictions.py`, com seis cenários sintéticos de conflito documental e seis perguntas de revisão entre áreas.
- Implementado o fecho transitivo de reabertura para controles dependentes do grafo público de 13 nós/17 arestas, com rejeição de dependências retiradas, revisão alterada ou falsa prova autenticada.
- Cada conflito invalida duas afirmações obsoletas no exercício, mas preserva incerteza mecânica: zero medições, zero falhas físicas comprovadas e `no_go` obrigatório.
- Publicados dez contratos JSON Schema, testes adversariais e relatórios JSON/HTML offline para não exposição de informação corporativa, literatura OEM licenciada ou alçada operacional.
- GitHub Actions reconstrói o corpus canônico e rejeita evidência fictícia marcada como real, falso aceite humano, prova OEM alterada, conflito oculto e autorização SAP.

**Limite:** resultados de P&D sintético, sem dados de mina, assinaturas, conformidade comprovada ou liberação de equipamento.


## 2.1.0 — 2026-10-27 — Ciclo 21

- Adicionada ordenação topológica de Kahn dos 13 controles e 17 predecessores do pacote Go/No-Go anterior, com verificação de ciclos, autoprecedência, duplicidade de vínculos e fase incompatível.
- Definido `pilot/evidence-sequencing.v1.json` com sete fases documentais propostas, cinco handoffs conceituais e dez cenários adversariais herdados do registro de ameaças.
- Criado `pilot/evidence_sequence.py` para rastreabilidade integral ao FMEA público fixado, geração offline JSON/HTML, raízes estruturais e profundidade das dependências, sem inventar duração, HH ou custo.
- Publicados 11 contratos JSON Schema e testes negativos contra autorização OEM/SAP/ECM, evidência antecipada, fase prematura, alteração de origem, acordo humano fictício ou liberação de máquina.
- CI integra a cadeia de testes dos 20 ciclos anteriores e publica relatório executivo com decisão `no_go` permanente no repositório público.

**Limite:** organização documental de requisitos, não plano de obra validado, aceitação de áreas, cadastro corporativo ou piloto privado em operação.


## 2.0.0 — 2026-10-27 — Ciclo 20

- Convertidos os requisitos do Ciclo 19 em pacote Go/No-Go com 13 controles dependentes, cinco áreas externas, dez achados sintéticos e zero evidência/assinatura verificada.
- Adicionados `pilot/go-nogo-package.v1.json`, `pilot/go_nogo.py` e **15 novos contratos JSON Schema**, contemplando `EvidenceSubmissionManifest`, `AcceptanceReview`, `GoNoGoDecision`, `ApprovalDependency`, `FindingRemediation` e `NoOperationalAuthority`.
- Avaliação estática de pré-requisitos, metodologia futura de revisores independentes, retenção sem política aprovada e bloqueios completos de SAP/ECM, materiais, execução e liberação.
- Relatório HTML/JSON offline e testes adversariais de proveniência, falso aceite, numeração SAP, efetividade OEM, retenção, política de revisão e estatísticas de concordância inexistentes.
- CI recompõe integralmente o corpus público FMEA e os artefatos dos ciclos anteriores antes da avaliação Go/No-Go.

**Limite:** decisão necessariamente `no_go` neste repositório. Nenhum piloto privado ou operação industrial foi aprovado.


## 1.9.0 — 2026-10-27 — Ciclo 19

- Formalizados 13 requisitos de prova externa e cinco áreas proponentes de aceite antes de qualquer piloto privado, todos sem comprovação ou assinatura real.
- Criados 10 cenários de ameaças envolvendo identidade duplicada, credencial revogada, assinatura forjada, mudança OEM/configuração, conflito de interesse, nota SAP, vazamento de dados, adulteração de auditoria e licenças.
- Implementados quatro cenários de invalidação e reabertura, todos `blocked_pending_external_verification`.
- Criados `pilot/readiness-fixture.v1.json`, `pilot/readiness.py`, testes adversariais, 13 contratos JSON Schema e relatório HTML/JSON offline.
- Separadas fontes NIST SP 800-63-4, OWASP ASVS 5.0.0, LGPD e a lacuna OEM não comprovada; explicitado plano de validação interavaliadores apenas para uso futuro autorizado.
- CI reproduz FMEA público pinado, revisão editorial e requisitos, rejeita falsas alegações de identidade, consentimento, assinatura, efetividade OEM ou alçada SAP.

**Limite:** nenhuma implantação privada, homologação OEM, identidade autenticada, conformidade certificada, nota SAP ou liberação operacional.


## 1.8.0 — 2026-10-27 — Ciclo 18

- Introduzido protocolo de revisão editorial **totalmente fictício** para quatro rascunhos de notificações sintéticas: 14 personas, 16 eventos e três estados sem aprovação operacional.
- Segregados autor, dois revisores por documento, adjudicador e custodiante; competência por disciplina declarada, duplicidade de persona, conflitos, alteração de revisão, revogação e discordância são validados.
- Revisões lógicas e trilha de evento encadeadas por SHA-256, sem assinatura digital, timestamp ou evidência externa de imutabilidade.
- Doze novos contratos JSON Schema e testes adversariais de identidade, competência, assinatura, autoaprovação, papéis, nonce, versão obsoleta, revogação e alteração de saída.
- Fluxo CI reconstitui FMEA público pinado, dossiês e notificações, gera JSON/HTML e rejeita personas/pareceres falsos.
- Nenhuma revisão autêntica de engenharia, medição física, validação interavaliadores, abertura SAP ou liberação de equipamento.


## 1.7.0 — 2026-10-26 — Ciclo 17

- Criada rubrica editorial de 12 critérios com explicações de não conformidade, severidade, campos afetados e ações de correção documental.
- Quatro rascunhos sintéticos avaliados como adequados **apenas para treinamento**; permanecem lacunas OEM, medição de campo, revisão humana e segurança operacional.
- Oráculo independente versionado com quatro resultados-base e 14 cenários adversariais: falso diagnóstico, número SAP, HH/risco inventados, método executado, lacunas e falsificação de revisão técnica.
- Adicionados `quality/notifications.py`, `quality/notification-rubric.v1.json`, `benchmarks/notification-quality-oracle.v1.json`, testes adversariais e nove contratos JSON Schema.
- CLI reconstitui o corpus a partir do snapshot FMEA público pinado e rejeita qualquer conteúdo de entrada ou rubrica alterados; exportação offline JSON e HTML não conecta SAP.
- CI publica relatório de qualidade sintético, bloqueia alegação falsa de revisão especializada e arquivos com HH adulterada.

**Limite:** `adequate_for_synthetic_training` não representa parecer de engenharia, eficácia diagnóstica nem autorização de manutenção.


## 1.6.0 — 2026-10-24 — Ciclo 16

- Convertidos os quatro dossiês/árvores de investigação em rascunhos técnicos fictícios, com sintomas, efeitos, hipóteses abertas, escopo delimitado, disciplina e lacunas de evidência.
- Criados `notifications/training-spec.v1.json` e `notifications/drafts.py`, gerando JSON/HTML de treinamento com rastreabilidade ao nó original e às fontes públicas.
- Publicados oito contratos JSON Schema para sintomas, hipóteses, escopo, planejamento, risco de postergação, rascunho e seus envelopes.
- O planejamento mantém HH, peças, prioridade, custo, equipamento, número SAP e procedimentos de execução deliberadamente ausentes; nenhuma operação é permitida.
- Adicionados testes adversariais e CI para rejeitar observação física inventada, causa confirmada, efetividade OEM fictícia, número SAP, peças/HH, falso registro de ordem e liberação de máquina.
- Relatório técnico do Ciclo 16 especifica fronteira entre exercício documental e processos corporativos reais.

**Limite:** não há criação de notas SAP, teste físico, diagnóstico real ou revisão profissional autenticada.


## 1.5.0 — 2026-10-24 — Ciclo 15

- Criadas quatro árvores didáticas de investigação com seleção de pergunta editorial, perguntas concorrentes, três ramos contrafactuais por comparação e checkpoints obrigatórios de revisão humana.
- O motor `trees/investigation.py` constrói 13 nós com 39 possibilidades condicionais, 26 contraexemplos instanciados e preserva 19 instâncias de hipóteses em aberto.
- `trees/presentation.py` produz HTML offline expansível, sem JavaScript ou integração empresarial.
- Integração ao dossiê `casefiles/integrated.py`, nova opção `--tree-html`, especificação versionada `trees/spec.v1.json` e oito contratos JSON Schema.
- Testes adversariais e CI rejeitam ramo falsamente observado, confirmação automática, revisão OEM inexistente, operação de máquina e alteração não rastreada de seleção/perguntas.
- Os estados `not_measured`, `contradicted` e `inconclusive` terminam em `abstain_pending_verified_evidence`; resultados `supports`/`weakens` continuam apenas hipotéticos.

**Limite:** nenhuma aprovação real, teste de campo, assinatura autenticada ou literatura OEM por série efetiva.


## 1.4.0 — 2026-10-24 — Ciclo 14

- Acrescentada matriz versionada de evidência qualitativa, ligada exatamente aos dez pares de hipóteses da matriz discriminante: 30 padrões condicionais, 20 explicações alternativas e ausência explícita de resultados físicos.
- Integrados ao gerador de quatro dossiês um objeto de evidência por par, proveniência dos métodos/fontes públicas, pré-requisitos de segurança, estado de contexto e avaliação dos níveis causais.
- Relatório HTML mostra padrões **hipotéticos**, contraexemplos, contextos contraditórios/não medidos e razões pelas quais nenhuma hipótese pode ser descartada.
- Criado benchmark/oráculo sintético versionado para quatro casos (contexto contraditório, ausente ou inconclusivo), com regressão de perguntas selecionadas; mudanças editoriais exigem revisão.
- Criados nove contratos JSON Schema, atualizados schemas dos dossiês, e incorporado SHA-256 da matriz qualitativa na proveniência.
- Adicionados testes adversariais contra promover contexto a medição, falsear causalidade, inserir literatura OEM específica, fabricar autorização/limite operacional, declarar falsos negativos ou descartar hipóteses por ausência de evidência.
- CI confere a nova matriz contra o FMEA público pinado, testa as quatro saídas integradas e rejeita evidência/efeito fabricados. Dez pares únicos aparecem 13 vezes e produzem 26 contraexemplos exibidos nos quatro casos.

**Limite:** `supports` e `weakens` são somente leituras condicionais; nenhuma validação diagnóstica ou atividade física ocorreu.


## 1.3.0 — 2026-10-24 — Ciclo 13

- Integrados FMEA público pinado, investigação CAT 777E, 14 métodos conceituais, discriminações editoriais, benchmark de 15 cenários e gates de revisão em dossiês técnicos de manutenção sintéticos.
- Implementado gerador `casefiles/integrated.py` com saídas JSON e HTML offline, descrevendo função, requisito, sintoma, hipóteses concorrentes, causalidade ainda não comprovada, risco qualitativo de postergação, fontes e perguntas de investigação.
- Quatro casos versionados: aditivos no comando final CAT 777E, carga hidráulica contraditória e eventos ECM sintéticos em estados registrado ou ativo; 19 hipóteses abertas nos relatórios.
- Adicionados quatro contratos JSON Schema e testes adversariais contra falsa confirmação de causa, medição/ensaio inventado, limiar ou probabilidade OEM, identificação real de frota, autorização SAP/ECM e liberação operacional.
- CI verifica a origem FMEA travada por SHA-256, produz JSON/HTML temporários, confirma abstinência, bloqueios de segurança e regressões do benchmark.

**Limite:** nenhuma inspeção, coleta, diagnóstico homologado, revisão independente real ou autorização operacional foi realizada.


## 1.2.0 — 2026-10-24 — Ciclo 12

- Gerador offline de dossiê de aceite em JSON e HTML estático para revisão futura de arquitetura corporativa, com escape de conteúdo e nenhuma integração de rede.
- Dez achados de prontidão, dez solicitações de evidência e dez ações funcionais ainda não executadas, derivados e cruzados com os controles do Ciclo 11.
- Duas exceções hipotéticas obrigatoriamente rejeitadas, mais seis cenários de requalificação, inclusive conflito de interesses.
- Sete contratos JSON Schema novos para achado, solicitação, ação, exceção, gate de revisão, cenário e fixture de dossiê.
- Verificação de cinco referências de compatibilidade, abrangendo os contratos públicos dos Ciclos 08–11.
- Testes adversariais contra supressão de controles, falsa execução, evidência real indevidamente incluída, aprovação de exceção, revisão obsoleta, reaprovação automática e renderização de HTML adulterado.
- CI publica artefatos JSON/HTML exclusivamente fictícios e não autorizadores.

**Limite:** não houve aprovação humana, sistema corporativo conectado, manual OEM efetivo nem evidência confidencial. Trata-se de material preparatório para avaliação futura.


## 1.1.0 — 2026-10-24 — Ciclo 11

- Criados dez controles de prontidão com responsáveis funcionais genéricos, riscos de ausência, dependências e critérios de aceite; todos permanecem sem comprovação externa.
- Publicados seis JSON Schemas (DeploymentControl, ControlEvidence, AcceptanceDecision, CompatibilityMatrix, ChangeImpact e pacote versionado).
- Avaliador offline gera lista ordenada por dependências, contagens de status, bloqueios, referências de versão e hashes dos quatro arquivos públicos relacionados aos Ciclos 08–10.
- Cinco mudanças exigem reabertura de qualificação: afirmação, revisão OEM, configuração do equipamento, identidade revogada e competência alterada.
- Testes adversariais e CI verificam rejeição de status falsamente verificado, evidência corporativa, contrato incompatível, ciclo de dependência, alterações de efetividade e aprovação operacional simulada.

**Limite:** software de avaliação sintética, não avaliação real de maturidade corporativa nem autorização de implantação.


## 1.0.0 — 2026-10-24 — Ciclo 10

- Definidos oito contratos de integração futura (principal, asserção, competência, versão de afirmação, revisão, evidência, auditoria e efetividade OEM).
- Criada política de sete papéis com segregação de responsabilidades, dez provas externas obrigatórias e negação explícita de atos operacionais.
- Adicionado adaptador fictício de testes: aceita apenas identidades SIM, pareceres sintéticos e referências públicas; nunca declara aprovação ou autenticação.
- Incluídos testes adversariais de duplicidade, falsificação de assinatura, competência, efetividade, adulteração de campos e versão.
- CI verifica contratos e publica exclusivamente relatório sintético; nenhuma integração corporativa foi estabelecida.

**Limite:** não existem identidade autenticada, assinatura verificada, documentação por série qualificada nem autorização real.


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
