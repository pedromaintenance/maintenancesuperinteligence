# Roadmap de pesquisa e desenvolvimento

O sucesso da primeira versão não é possuir todas as respostas; é **provar que o método para adquiri-las funciona**.

## Marco de pesquisa: Ciclo 51 (branch proposta; interfaces para IA e humanos)

**Objetivo:** transformar o repositório em uma base **consultável e auditável** por agentes de IA e profissionais humanos, com navegação e status derivados de um mesmo catálogo público versionado, sem alterar a fronteira de autoridade operacional.

**Entregáveis em proposta:** `AGENTS.md` (entrada para IAs), três papéis em `agents/`, três skills em `.agents/skills/`, `interfaces/catalog.v1.json` com JSON Schema e duas páginas standalone `portal/index.html` (conhecimento) e `portal/auditoria.html` (gates/PRs). O verificador `scripts/sync_interfaces.py` garante que ambas exibam o mesmo snapshot, que as fontes existam e que os 13 gates do Ciclo 48 permaneçam não verificados. [Arquitetura e instruções](INTERFACES_IA_HUMANOS.md).

**Marco de validade:** o portal e os agentes não possuem backend live, não consultam SAP/ECM, não autenticam engenheiros, não validam literatura OEM por série nem concedem autorizações; toda referência a PRs é um snapshot datado de 05/11/2026, não uma consulta dinâmica. Os PRs anteriores (#69–76) continuam sujeitos à revisão e integração em sequência. Um `ROADMAP.json` na raiz apresenta os marcos em formato consumível por IA, derivado do catálogo público para evitar duplicação manual. **NO GO.**

**Próximo passo:** validar no CI, testar consulta humana e legibilidade em dispositivos móveis, revisar a política de publicação e decidir se o portal deve ser hospedado no Pages após integração. Não converter filtros ou cliques em assinaturas, aprovações ou observações de campo.

## Marco de pesquisa: Ciclo 50 (branch proposta; revisão estrutural e relacional)

**Encontrado no código e coberto por testes:** oito vínculos cruzados dos Ciclos 44, 45 e 48 não são rejeitados pela validação estritamente estrutural de um JSON Schema, embora já sejam negados pelos validadores Python. A cobertura agora testa explicitamente ambos os estágios e demonstra a necessidade de executá-los juntos. No Ciclo 49, foi adicionada a recomputação do relatório para detectar três adulterações de contagens ou identidade de contrato que poderiam permanecer formalmente válidas no schema. [Auditoria do Ciclo 50](CICLO_2026-11-05_REVISAO_RELACIONAL_50.md).

**Escopo:** provas sintéticas, sem dados privados, engenharia de campo ou identidade humana validada. O relatório não promove diagnóstico, prontidão de estudo ou autorização SAP/ECM/OS. Os 13 gates externos de validação continuam abertos; **NO GO**.

**Prioridade:** revisão humana e integração dos PRs #69–76 em ordem, com novas verificações após cada merge ou rebase. Avaliar semântica de domínio e requisitos externos antes de expandir mecanismos de pesquisa.

## Marco de pesquisa: Ciclo 49 (branch proposta; integração de contratos executáveis)

**Entregue em pesquisa sintética:** execução real de 16 contratos JSON Schema dos Ciclos 44–48 contra objetos fabricados em memória, com teste de adulterações de versão, atributos inesperados e promoção de campos de autoridade falsos, inclusive aninhados. O relatório é público apenas com contagens; nenhum corpus, mapa privado, chave ou parecer real é exportado. [Auditoria executável](CICLO_2026-11-05_INTEGRACAO_CONTRATOS_49.md).

**Limitação:** aderência entre instância sintética e schema confirma consistência estrutural de um cenário, não competência diagnóstica, causalidade mecânica ou autenticidade da documentação OEM. Não há estudo humano nem revisão independente dos PRs concluída. A matriz não dá autorização para inspeção, abertura de OS, SAP, ECM ou liberação. **NO GO.**

**Próxima etapa de maior valor:** usar resultados do CI na revisão efetiva dos PRs #69–75 em ordem de dependências, corrigir eventuais contratos mal especificados e formalizar responsáveis pelos 13 gates de estudo externo definidos no Ciclo 48, sem reclassificar testes autorais como evidências independentes.

## Marco de pesquisa: Ciclo 48 (branch proposta; prontidão para revisão e estudo)

**Consolidação verificável:** snapshot público de 05/11/2026 registra a `main` no Ciclo 42 e cinco PRs abertos em cadeia (#69–73, Ciclos 43–47), com SHAs e CI dedicado/geral aprovados nos respectivos HEADs. Os PRs seguem *draft*, sem revisão humana concluída ou merge. O validador `governance/cycle48_readiness.py` reconstrói a cadeia declarada e os hashes dos documentos existentes; dois contratos JSON Schema são executados no CI. **Não consulta estado live nem autoriza merge.**

**Prontidão para estudo externo:** inventário formal de **13 gates pendentes** (aprovação de código, congelamento, direitos de dados, custódia independente, privacidade, origem de casos, identidade/competência de revisores, efetividade OEM, SST, neutralidade humana, estatística e adjudicação). Cinco métricas em forma de numerador/denominador são propostas **somente para discussão**, sem resultados observados nem pré-registro aprovado. [Documento de prontidão](CICLO_2026-11-05_PRONTIDAO_ESTUDO_48.md).

**Critério de avanço:** fechar a cadeia de revisões de PR de forma ordenada e só depois tratar recrutamento ou coleta real em ambiente privado sob custódia institucional e direitos de uso. Nenhum status externo pode ser declarado por testes autorais. **NO GO** para estudo ativo, causa raiz confirmada, SAP, ECM, OS ou liberação.

## Marco de pesquisa: Ciclo 47 (branch proposta; red team de texto e proveniência)

**Entregue em pesquisa sintética:** inspeção conservadora de pistas de identidade metodológica em perguntas pareadas, inclusive caracteres Unicode invisíveis, scripts misturados, instruções indevidas, identificadores internos e perguntas quase duplicadas. O auditor reconstrói os controles de custódia e revisão dos Ciclos 30–32, 45 e 46 antes de emitir um relatório privado de flags. Lacunas de fonte, natureza sintética e efetividade OEM permanecem separadas de alertas linguísticos, com encaminhamento para revisão externa e **NO GO permanente**.

**Limites:** heurísticas de sintaxe não constituem análise semântica ou prova de cegamento; similaridade lexical não equivale a poder discriminante, histórico de manutenção ou adequação OEM. Alias, hashes e HMAC não autenticam revisores, habilitação e autorização institucional. Nenhuma mudança SAP/ECM, nota, teste ou liberação é realizada. [Documentação do Ciclo 47](CICLO_2026-11-04_RED_TEAM_MASCARAMENTO_47.md).

**Prioridade posterior:** antes de crescer a suíte editorial, concluir a cadeia de PRs pendentes e estruturar um gate institucional externo para estudo independente: protocolo pré-registrado, revisão de neutralidade humana, casos com proveniência autorizada, pareceres tecnicamente qualificados e adjudicação documentada. Sem essas condições, não promover validação diagnóstica.

## Marco de pesquisa: Ciclo 46 (branch proposta; triagem e adjudicação pendente)

**Implementado exclusivamente em pesquisa sintética:** auditoria heurística de potenciais pistas de origem da pergunta (termos reveladores e relação de tamanho ≥2,5), reconciliação dos dois pareceres fictícios e encaminhamento explícito de conflitos, alertas de segurança, empates e abstenções para análise externa. O programa reconstrói os insumos custodiais dos Ciclos 30–32 e 45, emite dossiê privado de pendências e permite congelar rascunhos sem promover alçada, assinatura ou decisão. [Ver Ciclo 46](CICLO_2026-11-04_ADJUDICACAO_E_CEGAMENTO_46.md).

**Limites:** análise lexical não prova neutralidade; ausência de alerta não significa cegamento efetivo. Dois aliases e um terceiro alias não confirmam três humanos distintos. Hash/HMAC não autentica pessoas, fonte OEM, autorização de empresa ou comportamento físico. Concordância de preferência permanece distinta de validade diagnóstica. Nenhuma revisão humana real aconteceu. **NO GO** para execução física, SAP, ECM, ordem ou liberação.

**Próxima evidência essencial:** custódia institucional e estudo humano pré-registrado com perguntas efetivamente mascaradas, especialistas verificados, avaliação externa de segurança e critérios de adjudicação de divergência; medir não só concordância, mas qualidade técnica comparativa com incerteza, somente em casos lícitos e autorizados. Enquanto esses gates não existirem, não promover aprovação no repositório público.

## Marco de pesquisa: Ciclo 45 (branch proposta; comparação cega pareada)

**Implementado para ensaio sintético:** criação privada de pacotes A/B com posições quase balanceadas, vínculo HMAC entre fontes, candidatos e mapeamento confidencial; gate de qualidade obrigatório dos Ciclos 30–32; congelamento de duas submissões; relatório de concordância simples, preferência descritiva, empate, abstenção, flags de risco e dissenso aguardando adjudicação. Arquivos de estudo não entram no checkout público. [Ver documentação](CICLO_2026-11-04_REVISAO_CEGA_PAREADA_45.md).

**Limites:** aliases sintéticos não comprovam pessoas distintas; HMAC não prova identidade; posicionamento balanceado não garante ocultação do método quando o estilo das perguntas o revela; concordância de preferência não é correção diagnóstica; não há casos de campo nem OEM por série homologados. **NO GO** para testes físicos, abertura de ordem, escrita SAP/ECM ou liberação.

**Gate seguinte:** desenho e auditoria institucional de um estudo humano real. Congelar os objetivos e hipóteses, garantir independência de custódia, qualificação e alçada dos revisores, verificar o cegamento das perguntas, descrever critérios estatísticos prévios e obter consentimento/autorização. Somente depois coletar e analisar os primeiros pareceres com adjudicação externa. Sem esses requisitos, continuar apenas com pesquisa sintética, sem promover status.

## Marco de pesquisa: Ciclo 44 (branch proposta; estudo simbólico)

**Entregue em pesquisa:** oito cenários didáticos em comandos finais, hidráulica, ECM e arrefecimento, com três hipóteses rivais e três perguntas por cenário. A métrica conta somente quantos dos três pares de hipóteses teriam resultados simbólicos distintos conforme premissas criadas pelo autor; a métrica **não equivale** a probabilidade posterior, qualidade física do ensaio, valor esperado de informação, diagnóstico ou recomendação operacional. Contradição, empate ou pré-requisito ausente obrigam a abstenção/indisponibilidade.

**Testes e gates:** Python offline, contratos JSON Schema, verificação de previsões incompletas, pré-requisitos, falsa prova OEM, causalidade não confirmada, claims de revisão externa e ações proibidas. Sem acesso real, sem solicitações SAP e sem execução física.

**Próxima entrega não substituível pelo código:** usar, sob custódia privada e com autorização, a estrutura de casos inéditos dos Ciclos 30–32 para avaliação cega pareada de perguntas. Congelar o protocolo antes da revisão; proteger identidade, origem, direitos de uso e conflitos de interesse. Obter duas avaliações independentes reais e adjudicação dos dissensos antes de qualquer alegação de validade técnica. [Ler Ciclo 44](CICLO_2026-11-03_ESTUDO_DISCRIMINACAO_44.md).

## Marco de pesquisa: Ciclo 43 (branch proposta, sem homologação)

**Papel:** consolidar rastreabilidade e limites de validação, antes de novos serviços ou de declarar competência diagnóstica. O auditor offline registra cinco afirmações de maturidade, quatro issues abertas no snapshot de 03/11/2026 e fingerprints de evidências. Executa 24 casos de regressão editorial e 128 combinações contrafactuais **estruturais**, mantendo NO GO. A regra e a expectativa ainda são autorais; não representam 128 casos inéditos validados.

**Critérios de aceite internos:** testes adversariais contra promoção indevida, travessia de caminhos, adulteração de relatório e fechamento automático; CI exclusivo sem rede; reconstrução determinística; compatibilidade com a suíte anterior.

**Dependências externas não atendidas:** casos independentes sob custódia adequada, dois pareceres técnicos efetivamente autônomos, qualificação e conflito de interesses verificados, literatura OEM com efetividade comprovada, autorização corporativa para eventual piloto. Sem esses requisitos, não promover estados de validade causal.

**Foco seguinte:** corpus inédito, protocolo de avaliação cega com revisão de terceiros, métricas de discordância e comparação com o seletor documental simples; especificações OEM e dados corporativos permanecem fora deste repositório público. [Ver auditoria](CICLO_2026-11-03_AUDITORIA_MATURIDADE_43.md).


## Fase 0 — Fundação documental (v0.1, em curso)

**Entrega:** missão, catálogo das 56 competências do jogo, domínio expandido, contrato de integração FMEA, arquitetura, governança, fontes e caso-piloto. **Aceite:** links íntegros, fontes e status claros, sem alegar serviço funcional inexistente.

## Fase 1 — Núcleo de conhecimento (MVP)

**Progresso (ciclo 02):** item 4 implementado e verificado com importação real do snapshot público FMEA 1.0.0; parte do item 6 implementada com testes adversariais de integridade e semântica. Os demais itens continuam em desenvolvimento.

**Backlog:**
1. Schemas para `Source`, `Claim`, `AssetContext`, `Evidence`, `Hypothesis`, `DiagnosticTest`, `KnowledgeGap`.
2. Um registro inicial de fontes e 10–20 afirmações técnicas pequenas e verificáveis.
3. Uma CLI que valide JSON/Markdown/links internos, IDs, versões, ausência de números OEM não justificados e fonte obrigatória.
4. Importador de **um pacote público versionado do FMEA**, com `dry-run`, manifesto e hash.
5. Busca textual determinística com filtros por modelo, sistema, idioma, natureza e status.
6. Benchmark sintético: casos com evidências faltantes, dados conflitantes e hipóteses concorrentes.

**Aceite:** validações automatizadas, zero autopromoção de status e capacidade de dizer quando faltam série/OEM/evidência.

## Fase 2 — Primeiro fluxo vertical ponta-a-ponta

**Progresso (ciclo 03):** investigador e quatro casos sintéticos implementados; quatro cadeias FMEA consultadas em índice verificado, sete hipóteses abertas, oito testes apenas propostos. Foram realizados testes adversariais da estrutura e rejeição de conhecimento adulterado. A execução de testes reais, documentação OEM efetiva e a avaliação por especialista **continuam pendentes**.

**Caso:** diagnóstico de condição de comando final em caminhão de mineração, distinguindo mudança de formulação do óleo, contaminação e desgaste como hipóteses **não equivalentes**.

**Entrega:** entrada estruturada → seleção de fontes → geração de diferenciais → escolha justificada de testes → registro de observações *simuladas* → revisão humana → saída técnica com risco e pendências. **Aceite:** nenhum componente condenado só por metal ou diferença de aditivos; nenhum limite inventado; contraprovas documentadas.

## Fase 3 — Atlas de máquinas e disciplinas

**Progresso (ciclo 05):** biblioteca inicial de 14 métodos conceituais com cinco áreas disciplinares, contratos versionados, fontes técnicas gerais e ligação aos oito testes propostos do piloto. Métodos de hidráulica e eletrônica ainda não possuem casos verticais específicos, e nenhuma instrução OEM por série foi homologada.

**Progresso transversal (ciclo 04):** contratos e validador de evidências implementados exclusivamente nos casos didáticos da CAT 777E. Esse núcleo permite estender o modelo de observações e ensaios a outros sistemas sem confundir relatos, dados simulados, medições e hipóteses. A etapa de dados reais e validação OEM permanece pendente.

**Prioridade inicial:** 777E, 6030, DR410i, D9, além de sistemas transversais (hidráulico, arrefecimento, rodante, elétrico/eletrônico). Avançar por **circuito e função**, não por documento inteiro.

**Entrega por submódulo:** mapa funcional, princípios, desenhos conceituais próprios, modos de falha, sintomas, testes, segurança, fontes, variantes de modelo, biblioteca didática e lacunas. **Aceite:** revisão técnica + casos adversariais.

## Fase 4 — Estratégia de ativos, manutenção e PCM

**Ciclo 24:** propostas hipotéticas de mudança do grafo canônico (13 nós/17 arestas), delta de alcance, distância e redundância cruzado contra 100 cenários. Rejeição de ciclos e violações de responsabilidade, com veto permanente e nenhuma edição automática do grafo. Próxima etapa: pacote de revisão de mudanças, dependência de provas externas e manifestação de discordância/impugnação documental, sem autorizações no projeto público.

**Ciclo 23:** 100 casos estruturais de reabertura documental e oráculo independente de fecho transitivo em 13 controles/17 arestas; caminhos mínimos, alternativas e testemunhos de não alcance. Cinco mutações adversariais e revisão por cinco áreas inteiramente não autenticadas. Próximo candidato: revisão de propostas de alteração do grafo com diff versionado, análise de impacto e veto automático a mudanças de contrato não homologadas.

**Ciclo 22:** seis contradições editoriais simuladas e seis revisões cruzadas sobre o DAG canônico de 13 controles/17 vínculos. Propagação de invalidação aos descendentes com estado `no_go`, sem comprovação OEM, medição real ou dados corporativos. Próximo: medir cobertura estrutural e qualidade da explicação de reabertura em novos contrafactuais públicos.

**Ciclo 21:** plano executivo *documental* por dependências dos 13 controles (17 vínculos), em sete fases e cinco áreas, com relatório offline e dez ameaças bloqueadas. A ordenação topológica não representa duração ou caminho crítico temporal; nenhuma fase executada. Próximo: protocolo sintético de revisão cruzada e contradições entre evidências, preservando a separação de autoridade e o veto `no_go`.

**Ciclo 20:** pacote sintético de decisão Go/No-Go com 13 dependências de aprovação, cinco áreas de revisão externa, dez achados e rastreabilidade ao Ciclo 19. Estados de aprovação real proibidos, zero evidências privadas e relatório offline. Evolução seguinte: arquitetura de avaliação externa ou priorização de evidências para um projeto corporativo, com autorizações reais fora do GitHub.

**Ciclo 19:** matriz de 13 evidências externas, cinco aceites multidisciplinares, dez ameaças e quatro reaberturas de revisão hipotéticas. Relatório público offline mantém todas as provas não verificadas. Referências NIST/OWASP/LGPD separadas da efetividade OEM. Próximo: pacote formal de requisitos go/no-go por área para projeto privado, sem simular aprovações reais.

**Ciclo 18:** quatro fluxos fictícios de revisão editorial sobre rascunhos documentais, separação de papéis, controle de versão obsoleta, divergência, reabertura por contexto OEM e revogação; logs SHA-256 somente simulados e bloqueio integral de alçadas reais. Próximo: especificação de um protocolo externo de aceite de revisões humanas com requisitos de segurança, evidência e infraestrutura privada.

**Ciclo 17:** rubrica de 12 critérios para qualidade documental e 14 mutações sintéticas adversariais, com relatório offline JSON/HTML e rastreabilidade ao FMEA público, árvore e rascunho de notificação. Nenhuma validação de campo ou alçada SAP. Próximo candidato: desenho de protocolo para revisão humana independente de qualidade documental em ambiente restrito.

**Ciclo 16:** rascunhos técnicos sintéticos de notificações de manutenção para quatro dossiês, contemplando sintomas, hipóteses abertas, disciplina, escopo de investigação, evidências pendentes e risco qualitativo de postergação. Exportações offline JSON/HTML não possuem integração SAP, dados privados, materiais, HH, ou autorização operacional. Próximo: rubrica didática de qualidade de notificações e integridade documental.

**Ciclo 15:** árvores didáticas para os quatro dossiês técnicos, preservando 13 comparações, 39 alternativas não observadas e 26 contraexemplos instanciados. Pontos de abstenção e revisão humana impedem avançar da ausência de evidência à condenação de componente. Próxima etapa: transformar perguntas e lacunas em descrições de notificações didáticas, sem criar ordens reais.

**Ciclo 14:** modelo causal e matriz de observações qualitativas para 10 pares de hipóteses, incluindo 20 contraexemplos por mecanismo e 30 padrões condicionais (sem resultado observado). Dossiês exibem 13 comparações instanciadas com contextos desconhecidos ou contraditórios; nenhuma hipótese é excluída e nenhum parâmetro físico é presumido. Próximo: árvore didática de decisão com gates de abstenção e revisão técnica.

**Ciclo 13:** aplicação demonstrativa dos contratos à engenharia de manutenção: quatro casos diferenciais sintéticos (CAT 777E, hidráulica e ECM registrado/ativo), fontes públicas rastreadas, 19 instâncias de hipóteses abertas, saída HTML/JSON e proteção contra diagnóstico confirmado indevidamente. Próximo investimento recomendado: enriquecer os mecanismos de diferenciação com testes editoriais validados por especialistas, sem ingressar dados reais no repositório público.

**Ciclo 12:** dossiê estático JSON/HTML para revisão de arquitetura, dez evidências solicitadas mas não recebidas, duas exceções rejeitadas, seis cenários sintéticos de requalificação. Cinco referências de compatibilidade pública sem migração aprovada; a documentação não substitui parecer corporativo.

**Ciclo 11:** checklist de dez provas externas, cinco gatilhos de requalificação e quatro vínculos de compatibilidade pública implementados; a ordem de implementação pode ser calculada, mas nenhuma condição está independentemente verificada. Implantação restrita e homologação por série continuam bloqueadas.

**Ciclo 10:** contratos para integração futura, matriz de sete papéis e dez provas de confiança, validados apenas por testes sintéticos. Os ambientes de identidade, revisão, evidência, auditoria e OEM reais não estão implantados. A próxima etapa deverá avaliar formalmente prontidão e dependências institucionais, sem coletar dados corporativos no repositório público.

**Progresso (ciclo 09):** arquitetura segregada proposta para revisão autenticada, com ameaças/controles, rastreabilidade de versões e um ensaio estritamente sintético de papéis, replay e auditoria. Ainda não há IdP, vault restrito, trilha imutável, assinatura real ou competência pessoal verificada. Os contratos públicos não substituem validação de TI, Engenharia, Jurídico e fabricantes.

**Progresso (ciclo 08):** qualificação editorial de afirmações, referências e pareceres simulados com divergências explicitadas. Não existe identidade autenticada de engenheiro, parecer técnico real, OEM por série ou autorização de serviço. O benchmark passou a recusar alegações de validade diagnóstica sem gate humano/efetividade autorizado.

**Progresso (ciclo 07):** benchmark de regressão de 15 casos sintéticos e nove categorias auditáveis. A qualidade medida é a preservação de lógica, origem, lacunas e abstenção, **não** acurácia de diagnóstico de campo. A fase seguinte depende de qualificação de fontes e revisão técnica independente para permitir qualquer alegação de validade mecânica.

**Progresso (ciclo 06):** dez comparações hipotéticas divididas entre comando final, hidráulica e eletrônica. O seletor escolhe perguntas com justificativa explícita e bloqueia atuação operacional. Ainda são necessários estudos de sensibilidade, especificidade, custos reais, literatura por série e validação técnica em casos autorizados.

Construir modelos assistivos de política preventiva/por condição/corretiva deliberada; criticidade; oportunidades de inspeção; estoque MRO; prazos; programação; custo de ciclo de vida; desempenho operacional e integridade de notas SAP.

**Aceite:** métricas com denominador, período, unidade e fonte; nenhuma decisão de postergação de risco crítico automatizada; nenhuma escrita em SAP.

## Fase 5 — Preditiva e dados dinâmicos

Trabalhar com conjuntos anonimizados/autorizados de análises de óleo, vibração, telemetria e histórico; controle de qualidade, baseline por contexto, teste temporal, validação fora da amostra, alertas com explicação e taxa de falsos alarmes.

**Aceite:** desempenho comparado com regra simples, regressão em conjunto separado, erro e incerteza mensurados, revisão de campo.

## Fase 6 — Assistente multi-especialista

Orquestração de funções de **mecânico**, **eletricista/eletrônica**, **hidráulica**, **confiabilidade**, **monitoramento**, **PCM**, **engenharia de ativos**, **documentação OEM**, **estatística/dados** e **segurança**. Cada especialista será um conjunto de ferramentas, bases e testes — não apenas um personagem ou prompt.

**Aceite:** benchmark por domínio, registro da ferramenta usada, decisões auditáveis, avaliação humana e falha segura.

## Fase 7 — Uso institucional (somente mediante autorização)

Infraestrutura privada, RBAC, autenticação, logs, isolamento de dados, aprovação da segurança OT, gestão documental, governança de mudanças, validação operacional e responsáveis formais. Nunca confundir com o MVP público.

## Estratégia de execução

Preferir **fatias verticais pequenas**: escolher uma falha → mapear função → obter fontes → testar hipóteses → registrar evidências → escrever um caso didático → validar → integrar. Só depois escalar a novos sistemas.

**Definition of Done de qualquer módulo:** (a) fontes revisadas; (b) limites de aplicação; (c) conteúdo autoral; (d) pelo menos uma hipótese alternativa; (e) testes e condições de interpretação; (f) resultado adversarial; (g) dono e revisão; (h) nenhum dado confidencial vazado.
