# Roadmap de pesquisa e desenvolvimento

O sucesso da primeira versão não é possuir todas as respostas; é **provar que o método para adquiri-las funciona**.

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
