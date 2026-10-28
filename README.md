# MaintenanceSuperinteligence

**Uma arquitetura aberta, incremental e auditável de conhecimento para gestão de ativos, engenharia de manutenção e equipamentos móveis de mineração.**

> **Estado: taxonomia mecânica de hipóteses com referências rastreáveis P&D v3.3.0 (28/10/2026).** Este repositório ainda **não é** um sistema de diagnóstico homologado, software embarcado ou agente capaz de controlar máquinas. Os documentos definem pesquisa, requisitos, ontologia, interfaces e validação futura.

## Visão

Desenvolver, progressivamente, um sistema capaz de explicar a função de um ativo, reconhecer seus sistemas e componentes, investigar sintomas, comparar hipóteses e evidências, orientar a consulta a literatura OEM aplicável, recomendar opções de manutenção e apoiar decisões de custo, risco e ciclo de vida. Cada resposta deve expor o que é conhecido, de onde veio, a qual configuração se aplica e o que ainda precisa ser comprovado.

**Não construir um chatbot que pareça especialista; construir uma infraestrutura na qual o conhecimento especializado possa ser adquirido, revisado, testado e reutilizado.**

## Princípios inegociáveis

1. **Função antes da falha:** função, requisito, condição operacional, falha funcional, modo de falha, mecanismo, dano, sintoma, evidência, hipótese, consequência e ação são entidades distintas.
2. **Conhecimento não é ocorrência:** catálogo, caso simulado, evidência real e instrução aprovada nunca são equivalentes.
3. **Aplicabilidade importa:** qualquer dado OEM específico depende de fabricante, modelo, série/arranjo, sistema, componente, revisão da literatura e, quando pertinente, versão de ECM/software.
4. **Referências e contraprovas:** toda afirmação técnica significativa precisa de fonte, limites e testes que possam refutá-la.
5. **Sem autoridade operacional automática:** análises assistivas e *human-in-the-loop*. Nenhum ajuste em ECM, flashing, calibração, desbloqueio, mudança de parâmetro, comando de máquina, abertura de OS ou liberação operacional sem integração autorizada, procedimento aplicável e aprovação humana.
6. **Segurança e custódia:** conhecimento genérico público separado de dados privados, manuais OEM licenciados, dados SAP, laudos e telemetria identificáveis.
7. **Crescimento verificável:** uma área só evolui após testes, revisão e observabilidade; quantidade de textos não é indicador de maturidade.

## Ecossistema

| Repositório | Papel | Contrato proposto |
| --- | --- | --- |
| [P.O.R.C.A.R.I.A.](https://github.com/pedromaintenance/porcaria-voce-quebra-eu-conserto) | Simulador de competências, formação, investigação e decisões PCM | Consumidor de cenários educacionais versionados; catálogo de 56 habilidades como inspiração da ontologia |
| [FMEA Database Mining](https://github.com/pedromaintenance/fmea-database-mining) | Produtor de taxonomias, cadeias causais, hipóteses, testes, evidências e pacotes públicos | Importação sob contrato e versão; não copiar o banco inteiro; nunca promover hipótese automaticamente |
| **MaintenanceSuperinteligence** | Orquestração de conhecimento, currículo de pesquisa, serviços de consulta, avaliação e governança | Agrega fontes, cria vínculos, realiza consultas fundamentadas, explicita lacunas, propõe investigações |

## Documentação inicial

- [Arquitetura do sistema](docs/ARQUITETURA.md)
- [Mapa de competências](docs/COMPETENCIAS.md)
- [Domínios da manutenção e mineração](docs/DOMINIOS.md)
- [Integração com o FMEA Database](docs/INTEGRACAO_FMEA.md)
- [Método de aquisição e validação do conhecimento](docs/METODO_DE_PESQUISA.md)
- [Governança e limites de segurança](docs/GOVERNANCA.md)
- [Plano de desenvolvimento e entregáveis](docs/ROADMAP.md)
- [Primeiro caso vertical para testar a arquitetura](docs/CASO_PILOTO.md)
- [Fontes públicas prioritárias](docs/FONTES.md)
- [Ciclo 02 — Importação verificável do FMEA](docs/CICLO_2026-10-22_IMPORTADOR_FMEA.md)
- [Ciclo 03 — Investigador didático CAT 777E](docs/CICLO_2026-10-22_INVESTIGADOR_777E.md)
- [Ciclo 04 — Modelo de evidências auditáveis](docs/CICLO_2026-10-22_MODELO_EVIDENCIAS.md)
- [Ciclo 05 — Biblioteca de métodos diagnósticos](docs/CICLO_2026-10-23_METODOS_DIAGNOSTICOS.md)
- [Ciclo 06 — Seleção discriminante de perguntas](docs/CICLO_2026-10-23_SELECAO_DISCRIMINANTE.md)
- [Ciclo 07 — Benchmark de qualidade de perguntas](docs/CICLO_2026-10-23_BENCHMARK_PERGUNTAS.md)
- [Ciclo 08 — Governança de revisão técnica simulada](docs/CICLO_2026-10-24_GOVERNANCA_REVISAO.md)
- [Ciclo 09 — Arquitetura restrita, identidade e modelo de ameaças](docs/CICLO_2026-10-24_ARQUITETURA_RESTRITA.md)
- [Ciclo 10 — Contratos de integração restrita e testes de confiança](docs/CICLO_2026-10-24_CONTRATOS_INTEGRACAO.md)
- [Ciclo 11 — Matriz de prontidão e compatibilidade](docs/CICLO_2026-10-24_PRONTIDAO_IMPLANTACAO.md)
- [Ciclo 12 — Dossiê de aceite técnico e revisão de prontidão](docs/CICLO_2026-10-24_DOSSIE_ACEITE.md)
- [Ciclo 13 — Dossiês integrados de investigação de manutenção](docs/CICLO_2026-10-24_DOSSIES_DIAGNOSTICOS.md)
- [Ciclo 14 — Evidência discriminante, níveis causais e contraexemplos](docs/CICLO_2026-10-24_EVIDENCIA_DISCRIMINANTE.md)
- [Ciclo 15 — Árvores de investigação e abstenção](docs/CICLO_2026-10-24_ARVORES_INVESTIGACAO.md)
- [Ciclo 16 — Rascunhos didáticos de notificações de manutenção](docs/CICLO_2026-10-24_NOTIFICACOES_DIDATICAS.md)
- [Ciclo 17 — Rubrica de qualidade documental de notificações](docs/CICLO_2026-10-26_QUALIDADE_NOTIFICACOES.md)
- [Ciclo 18 — Revisão editorial fictícia e governança de versões](docs/CICLO_2026-10-27_REVISAO_EDITORIAL.md)
- [Ciclo 19 — Protocolo de prontidão para futuro piloto privado](docs/CICLO_2026-10-27_PRONTIDAO_PILOTO_PRIVADO.md)
- [Ciclo 20 — Pacote Go/No-Go de piloto privado](docs/CICLO_2026-10-27_PACOTE_GO_NO_GO.md)
- [Ciclo 21 — Sequenciamento de evidências e dependências](docs/CICLO_2026-10-27_SEQUENCIAMENTO_EVIDENCIAS.md)
- [Ciclo 22 — Contradições documentais e reabertura de dependências](docs/CICLO_2026-10-27_CONTRADICOES_EVIDENCIAS.md)
- [Ciclo 23 — Cobertura estrutural das reaberturas](docs/CICLO_2026-10-27_COBERTURA_REABERTURAS.md)
- [Ciclo 24 — Revisão de mudanças do grafo e veto](docs/CICLO_2026-10-27_REVISAO_MUDANCAS_GRAFO.md)
- [Ciclo 25 — Dossiês sintéticos de mudanças](docs/CICLO_2026-10-27_DOSSIES_REVISAO_GRAFO.md)
- [Ciclo 26 — Contestação e revogação](docs/CICLO_2026-10-27_CONTESTACAO_REVOGACAO.md)
- [Ciclo 27 — Benchmark de raciocínio mecânico](docs/CICLO_2026-10-27_BENCHMARK_RACIOCINIO_MECANICO.md)
- [Ciclo 28 — Generalização sintética e qualidade da proveniência](docs/CICLO_2026-10-27_GENERALIZACAO_ADVERSARIAL.md)
- [Ciclo 29 — Protocolo para revisão independente](docs/CICLO_2026-10-28_PROTOCOLO_REVISAO_INDEPENDENTE.md)
- [Ciclo 30 — Custódia separada de casos inéditos e gabarito](docs/CICLO_2026-10-28_CUSTODIA_AVALIACAO_EXTERNA.md)
- [Ciclo 31 — Qualidade de conjuntos e controle de vazamento](docs/CICLO_2026-10-28_QUALIDADE_CONJUNTO_VALIDACAO.md)
- [Ciclo 32 — Qualidade privada obrigatória antes da distribuição](docs/CICLO_2026-10-28_QUALIDADE_CUSTODIA_PRIVADA.md)
- [Ciclo 33 — Taxonomia mecânica com fontes técnicas verificáveis](docs/CICLO_2026-10-28_TAXONOMIA_MECANICA_FUNDAMENTADA.md)

## Estrutura inicial e arquitetura futura

```text
contracts/        # dois JSON Schemas versionados (presentes); outros planejados
data/             # fontes e afirmações atômicas propostas (presente)
research/         # lacunas de conhecimento (presente)
scripts/          # validador offline de integridade mínima (presente)
.github/workflows # validação GitHub Actions (presente)
docs/             # arquitetura e especificações (presente)
connectors/       # importador público do FMEA e lock de fonte (presentes)
tests/            # testes unitários adversariais do importador e do piloto (presentes)
investigations/   # investigador diferencial didático CAT 777E (presente)
evidence/         # ontologia de observação, teste e evidência + auditoria (presente)
methods/          # catálogo, matriz de hipóteses e seletores didáticos (presentes)
examples/         # quatro cenários sintéticos (presentes)
evaluation/       # benchmark de diagnóstico amplo (futuro)
services/         # busca e orquestração assistiva (futuro)
```

## Importador público do FMEA — ciclo 02

O importador `connectors/fmea_public.py` consome **somente o snapshot público do release 1.0.0**, pinado por commit e SHA-256. Ele rejeita promoções para causa raiz confirmada, evento real, teste executado e aplicabilidade OEM ou aprovação operacional sem evidência. O resultado é um **índice didático de hipóteses**, não um banco de falhas reais.

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public
```

O CI verifica o pacote real: **24 cadeias, 20 fontes, zero ocorrências reais**, com artefato temporário de índice e recibo. A fonte original permanece no repositório FMEA. [Consultar ciclo 02](docs/CICLO_2026-10-22_IMPORTADOR_FMEA.md).

## Primeiro investigador didático — ciclo 03

A CLI `investigations/final_drive.py` analisa **somente casos sintéticos CAT 777E**, via quatro cadeias genéricas de comandos finais do FMEA e três alternativas do piloto (formulação, coleta, ruído externo). Ela preserva hipóteses concorrentes, identifica resultados divergentes, lista lacunas OEM e sugere investigação **não executada**. Não diagnostica, não condena peças e não libera máquinas.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m investigations.final_drive \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --index build/fmea-public/fmea-public.index.json \
  --case examples/777e_additives_only.json \
  --output build/investigations/777e_additives_only.json
```

A execução **revalida o hash real do snapshot**, e, se houver índice informado, compara todo o seu conteúdo com a reconstrução autenticada. Quatro cenários sintéticos integram o CI. [Documentação e limites](docs/CICLO_2026-10-22_INVESTIGADOR_777E.md).

## Camada de evidências — Ciclo 04

O relatório de investigação **v2** inclui um `evidenceLedger` com cinco entidades distintas: `Observation`, `TestMethod`, `TestResult`, `Evidence` e `HypothesisAssessment`. Relatos codificados não viram automaticamente medições ou resultados de ensaio. O ledger possui seis etapas de hash encadeado e validação cruzada contra o caso e a rubrica de hipóteses; isso **não constitui assinatura ou prova de autenticidade da fonte**.

O parâmetro opcional `--simulated-test-results examples/777e_simulated_test_results.json` demonstra um resultado de **execução fictícia explícita**. Não há testes reais nem mudança de aprovação dos métodos genéricos do FMEA. [Relatório completo](docs/CICLO_2026-10-22_MODELO_EVIDENCIAS.md).

## Biblioteca de métodos — Ciclo 05

O catálogo `methods/catalog.v1.json` registra **14 métodos conceituais** em cinco disciplinas: óleo (4), hidráulica (3), mecânica (3), vibração (2) e eletrônica (2). Seis códigos de método do FMEA (`EV-*`) são reconciliados com as **oito investigações** do caso CAT 777E; as fontes de referência e limitações são rastreadas em `data/diagnostic-method-sources.v1.json`.

A CLI `python -m methods.library --snapshot ... --case ... --investigation ... --output ...` gera perguntas e campos a levantar, nunca medições ou procedimentos autorizados. Cada método traz requisitos de contexto, riscos que exigem avaliação e limites da inferência. O relatório original precisa coincidir integralmente com a investigação reconstruída do snapshot autenticado. [Detalhes do Ciclo 05](docs/CICLO_2026-10-23_METODOS_DIAGNOSTICOS.md).

## Verificação e desenvolvimento

A rotina **Validate public knowledge and FMEA importer** executa testes de metadados, testes adversariais e importação controlada. **Isso não constitui validação técnica OEM de diagnósticos nem JSON Schema completo.** [Ver CI](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/workflows/validate.yml).

**Backlog criado:** [#1 Ontologia e schemas](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/1) · [#2 Importador FMEA](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/2) · [#3 Piloto 777E](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/3) · [#4 Currículo](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/4) · [#5 Governança](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/5).

## O que podemos fazer primeiro

1. Converter as **56 competências reais do jogo** em um catálogo rastreável e extensível, sem converter pontos de jogo em habilitação profissional.
2. **Concluído no ciclo 02:** consumir o snapshot público versionado do FMEA com verificação de hash, sem misturar combinações heurísticas, cenários didáticos e observações reais.
3. **Protótipo didático no ciclo 03:** observações simuladas → hipóteses concorrentes → investigações propostas → lacunas → recomendação de revisão humana. O fluxo real de evidências e decisão operacional permanece pendente.
4. Registrar lacunas OEM/SAP/segurança antes de afirmar especificações, frequências, torques, pressões ou peças.
5. Criar testes de qualidade para evitar respostas causais circularmente justificadas ou citações falsas.

## Licença e colaboração

Licença **a definir**. Até a escolha formal, não se deve presumir permissão de reutilização de material, especialmente fontes de terceiros ou conteúdo proprietário. Links para fontes não transferem direitos autorais. Contribuições devem citar origem, classe de evidência, aplicabilidade e revisão.

---
**MaintenanceSuperinteligence não substitui o técnico, o engenheiro, o manual do fabricante ou o procedimento de segurança. Seu propósito é ampliar a capacidade humana de compreender, decidir e aprender.**


## Ciclo 06 — Próxima pergunta para discriminar hipóteses

A matriz `methods/discrimination-matrix.v1.json` compara dez pares de hipóteses em **três famílias sintéticas**: comando final, hidráulica e diagnóstico eletrônico. `methods/discrimination.py` seleciona deterministicamente **uma pergunta** a partir de contradições e lacunas, sem executar testes e sem probabilidades/custos inventados.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m methods.discrimination --snapshot build/fmea-public/fmea-public.snapshot.json --case examples/discrimination_hydraulics.json --output build/discrimination/hydraulics.selection.json
```

O cenário hidráulico parte de carga contraditória e não condena bomba; o eletrônico parte de DTC não caracterizado e não condena sensor/ECM. Fontes gerais de fabricantes permanecem **não específicas para série**. Leia [o relatório do Ciclo 06](docs/CICLO_2026-10-23_SELECAO_DISCRIMINANTE.md).


## Ciclo 07 — Benchmark sintético de qualidade das perguntas

O pacote `benchmarks/question-quality.v1.json` reúne **15 casos editoriais sintéticos** (5 por família) com expectativas de escolha e abstenção. A rubrica `benchmarks/question-quality-rubric.v1.json` cobre nove classes de regressão, incluindo proveniência, contradições, dados faltantes, interpretação indevida, segurança, efetividade OEM e reprodutibilidade. O executável `benchmarks/quality.py` constrói relatório com falhas por categoria, denominadores e SHA-256, valendo-se do snapshot público FMEA original e dos métodos do projeto.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m benchmarks.quality --snapshot build/fmea-public/fmea-public.snapshot.json --output build/benchmarks/question-quality.v1.report.json
```

**Atenção:** conformidade no benchmark é **regressão de software**, não sensibilidade/especificidade de detecção de falha nem aprovação por especialista. Acurácia diagnóstica real, critérios OEM por série e autorizações operacionais continuam fora do escopo. Veja [relatório técnico](docs/CICLO_2026-10-23_BENCHMARK_PERGUNTAS.md).


## Ciclo 08 — Governança de afirmações e revisão técnica

O núcleo `governance/review.py` valida referências gerais de fabricantes, oito afirmações editoriais e pareceres **exclusivamente simulados**. O pacote `governance/review-packet.v1.json` conserva duas divergências, controla IDs distintos, disciplina, referências e rodadas de reavaliação. **Não há engenheiro real revisando ou assinando.** O status `general_reference_supported` é apenas ilustrativo, nunca aprovação operacional/OEM.

O benchmark do Ciclo 07 ganhou um gate explícito de qualificação técnica: por mais que os casos sintéticos passem, `mayClaimFieldDiagnosticValidity=false` até existir revisão independente real e aplicabilidade OEM documentada em ambiente autorizado.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m governance.review --snapshot build/fmea-public/fmea-public.snapshot.json --output build/governance/technical-review.v1.report.json
```

Leia o [relatório do Ciclo 08](docs/CICLO_2026-10-24_GOVERNANCA_REVISAO.md).


## Ciclo 09 — Especificação de ambiente restrito (não implantado)

A arquitetura `docs/CICLO_2026-10-24_ARQUITETURA_RESTRITA.md` separa contratos públicos de identidade, laudos, séries, registros ECM/SAP e conteúdo OEM que devem permanecer em **ambiente privado autorizado**. Inclui critérios de autenticação, atribuição de papéis, assinatura, custódia, retenção e LGPD, além de um modelo de ameaças com controles propostos.

O protótipo `governance/restricted_blueprint.py` executa três sequências e nove eventos **estritamente fictícios** a partir de `examples/restricted-review-threat-fixture.v1.json`. Ele modela atribuição de papéis, revisão independente apenas por ID, conflitos, nonces contra replay e vínculo à versão da afirmação. O validador rejeita parecer adulterado em comparação à entrada original. **Não existe IdP, assinatura, auditoria externa, aplicação privada nem autorização operacional implantados neste projeto.**

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m governance.restricted_blueprint --snapshot build/fmea-public/fmea-public.snapshot.json --output build/restricted-review/threat-fixture.report.json
```

O CI demonstra consistência e gates de um fluxo de simulação; não avalia conformidade NIST, OWASP, LGPD ou eficácia de segurança real.


## Ciclo 10 — Contratos de integração futura (sem implantação)

O projeto definiu **oito contratos JSON Schema** para principal, asserção de credencial, qualificação técnica, versão de afirmação, decisão independente, manifesto de evidência, âncora de auditoria e efetividade OEM. A política `governance/integration-policy.v1.json` separa sete papéis, seus atos propostos e ações operacionais expressamente negadas.

O adaptador fake `governance/integration_contracts.py` valida `examples/integration-fixture.v1.json` com oito personagens sintéticos, dois pareceres divergentes e dez requisitos externos não implementados. A saída **não valida credenciais**, **não homologa documentos OEM**, **não decide serviço de manutenção** e **não interage com sistemas corporativos**.

```bash
python -m governance.integration_contracts --output build/integration/contracts.report.json
```

Consulte o [relatório completo do Ciclo 10](docs/CICLO_2026-10-24_CONTRATOS_INTEGRACAO.md) antes de propor qualquer implantação privada.


## Ciclo 11 — Prontidão, dependências e compatibilidade contratual

O protótipo `governance/deployment_readiness.py` mantém **dez controles de infraestrutura privada** como pendências, organiza dependências em ordem topológica, testa compatibilidade dos esquemas e versões públicas dos Ciclos 08–10 e define **cinco gatilhos de requalificação** (afirmação, revisão OEM, configuração, identidade e competência).

A avaliação `governance/deployment-readiness.v1.json` contém somente planos e metadados **sintéticos**. O relatório preserva `acceptance=blocked_private_deployment` e `independentlyVerifiedControls=0` mesmo se alguns controles estão marcados `available_unverified`. Nenhum IdP ou backend empresarial foi configurado.

```bash
python -m governance.deployment_readiness --output build/readiness/deployment-readiness.v1.report.json
```

Os [detalhes do Ciclo 11](docs/CICLO_2026-10-24_PRONTIDAO_IMPLANTACAO.md) explicam matriz, donos por função, critérios e limites de confiança.


## Ciclo 12 — Dossiê para revisão de arquitetura (dados fictícios)

O gerador `governance/readiness_dossier.py` transforma os dez controles de prontidão em um **dossiê JSON e HTML standalone**, com responsáveis funcionais, evidências necessárias, risco de postergação e ações ainda não executadas. O pacote `governance/readiness-dossier-fixture.v1.json` acrescenta duas exceções ilustrativas (ambas rejeitadas) e seis mudanças que obrigariam requalificação, incluindo conflito de interesses.

```bash
python -m governance.readiness_dossier --output build/readiness/acceptance-dossier.v1.json --html build/readiness/acceptance-dossier.v1.html
```

O HTML é offline, sem JavaScript, sem login, sem formulário e sem conexão com a empresa. Os sete esquemas de apoio restringem campos e bloqueiam falsos pareceres. **Todas as evidências reais permanecem não recebidas e todas as autorizações permanecem negadas.** Veja o [relatório técnico](docs/CICLO_2026-10-24_DOSSIE_ACEITE.md).


## Ciclo 13 — Dossiês de investigação mecânica e eletrônica

O núcleo `casefiles/integrated.py` conecta o **snapshot público FMEA travado por SHA-256**, hipóteses didáticas, biblioteca de 14 métodos, matriz discriminante, benchmark de 15 cenários e gates de revisão dos ciclos anteriores. Gera **quatro dossiês sintéticos**, em JSON e HTML standalone: comando final de CAT 777E (perfil de aditivos isolado), hidráulica com contexto de carga contraditório, ECM com código registrado e ECM com código ativo fictício.

Os relatórios exibem função, requisito, sintoma, efeito, alternativas imediatas/raiz **não confirmadas**, 19 instâncias de hipóteses abertas, próximas perguntas, segurança, riscos qualitativos e fontes técnicas gerais. Ordem das hipóteses é editorial, não probabilística. O gerador não acessa ECM/SAP e mantém todas as permissões, resultados de ensaio e homologações OEM **bloqueados ou não realizados**.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m casefiles.integrated --snapshot build/fmea-public/fmea-public.snapshot.json --output build/casefiles/integrated-differential.v1.json --html build/casefiles/integrated-differential.v1.html
```

Consulte o [relatório do Ciclo 13](docs/CICLO_2026-10-24_DOSSIES_DIAGNOSTICOS.md) para escopo técnico, fontes, limitação de inferências e execução.


## Ciclo 14 — Matriz de evidência qualitativa e alternativas concorrentes

O arquivo `evidence/qualitative-discrimination.v1.json` acrescenta **10 pares de hipóteses**, **30 observações condicionais** e **20 contraexemplos diferentes**, todos vinculados à matriz discriminante e aos métodos públicos. Como quatro dossiês compartilham alguns pares, a visualização final exibe **13 comparações e 26 contraexemplos instanciados**.

Um oráculo sintético independente em `benchmarks/qualitative-oracle.v1.json` registra as respostas esperadas de quatro casos para detectar alterações silenciosas de estado/contexto e seleção, sem alegar veracidade mecânica.

Cada dossiê apresenta quais padrões *poderiam* fortalecer ou enfraquecer uma interpretação, quais explicações alternativas permanecem possíveis e qual informação ainda precisa ser obtida. O módulo `evidence/qualitative.py` não aceita promover tais padrões a resultados medidos: `supports`/`weakens` são apenas condicionais; estados presentes no caso são `not_measured`, `contradicted` e `inconclusive`. **Nenhuma hipótese é descartada, nenhum teste é considerado executado e não existe aprovação de equipamento.**

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m casefiles.integrated --snapshot build/fmea-public/fmea-public.snapshot.json --output build/casefiles/integrated-differential.v1.json --html build/casefiles/integrated-differential.v1.html
```

Veja a [documentação do Ciclo 14](docs/CICLO_2026-10-24_EVIDENCIA_DISCRIMINANTE.md) para a interpretação correta dos estados, hipóteses mecânicas e limitações de campo.


## Ciclo 15 — Árvores didáticas com revisão humana obrigatória

O núcleo `trees/investigation.py` integra perguntas, hipóteses, fontes e contextos dos Ciclos 13–14 em quatro árvores de investigação, com **13 nós, 39 ramos contrafactuais não observados e 26 contraexemplos**. Cada saída termina em abstenção: nenhuma causa confirmada, método físico executado, OS ou liberação. A visualização `trees/presentation.py` gera HTML standalone expansível usando `<details>`, sem JS, rede, login ou dados corporativos.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m casefiles.integrated --snapshot build/fmea-public/fmea-public.snapshot.json --output build/trees/technical-cases.v1.json --tree-html build/trees/investigation-trees.v1.html
```

Consulte o [relatório completo do Ciclo 15](docs/CICLO_2026-10-24_ARVORES_INVESTIGACAO.md).


## Ciclo 16 — Notificações técnicas para treinamento

O gerador `notifications/drafts.py` transforma os **quatro dossiês/árvores sintéticos** em rascunhos completos de descrição de sintoma, hipótese aberta, escopo de investigação, disciplina, evidências a levantar e risco qualitativo. Todos são identificados como `SIM-NOTE-001` a `SIM-NOTE-004`, com banner de **simulação educacional**, sem número SAP, série, materiais, HH, custo, prioridade numérica ou procedimento de execução inventado.

```bash
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m casefiles.integrated --snapshot build/fmea-public/fmea-public.snapshot.json --output build/trees/technical-cases.v1.json
python -m notifications.drafts --source build/trees/technical-cases.v1.json --snapshot build/fmea-public/fmea-public.snapshot.json --output build/notifications/maintenance-drafts.v1.json --html build/notifications/maintenance-drafts.v1.html
```

Antes da geração, o programa reconstitui o corpus didático com o snapshot FMEA público fixado e rejeita qualquer fonte externa alterada ou texto editorial não correspondente ao exemplar do projeto. O HTML é standalone, somente leitura e sem interface SAP. Nenhum rascunho tem autoridade para abrir notas/ordens, condenar componente ou liberar equipamento. Consulte o [relatório técnico do Ciclo 16](docs/CICLO_2026-10-24_NOTIFICACOES_DIDATICAS.md).


## Ciclo 17 — Rubrica de qualidade de notificações didáticas

O módulo `quality/notifications.py` verifica **12 critérios editoriais** para cada um dos quatro rascunhos fictícios de manutenção, identificando completude, clareza causal, evidências pendentes, segurança do escopo, fonte pública e responsabilidade técnica. Um oráculo independente `benchmarks/notification-quality-oracle.v1.json` cobre **14 alterações adversariais** (entre elas causa raiz confirmada sem prova, HH inventada, identificação SAP, execução fictícia, falsa medição e falso parecer OEM). O relatório é emitido em JSON e HTML standalone.

As quatro notas originais são classificadas como `adequate_for_synthetic_training` **somente para completude documental de exemplos sintéticos**. Isso não autoriza registrar nota/ordem SAP, substituir peça, liberar equipamento ou interpretar que houve revisão de engenheiro. Os quatro bloqueios externos — OEM por série, evidência física, revisão humana e riscos de execução — permanecem não atendidos.

```bash
python -m quality.notifications --source build/trees/technical-cases.v1.json --drafts build/notifications/maintenance-drafts.v1.json --snapshot build/fmea-public/fmea-public.snapshot.json --output build/quality/notification-quality.v1.json --html build/quality/notification-quality.v1.html
```

Para preparar os arquivos de entrada, siga a [documentação do Ciclo 17](docs/CICLO_2026-10-26_QUALIDADE_NOTIFICACOES.md).


## Ciclo 18 — Revisão editorial simulada e independência por papel

O motor `editorial/review_protocol.py` usa **14 personas totalmente fictícias** e **16 eventos** em quatro rascunhos, incluindo dupla revisão por versão, divergência preservada, correção editorial simulada, mudança de contexto/OEM e revogação de perfil. Os estados são `requires_revision`, `unresolved_disagreement` e `pending_real_review` — **nunca aprovado por engenheiro**. Os digests SHA-256 permitem somente regressão e detecção de adulterações contra o corpus canônico, sem assinatura, identidade autenticada nem âncora externa.

O GitHub Actions publica relatórios JSON/HTML temporários, e os testes bloqueiam autoaprovação, persona duplicada, competência incompatível, avaliação de revisão obsoleta, falso parecer, falsificação de assinatura e qualquer autorização SAP/ECM/liberação. A documentação é [Ciclo 18](docs/CICLO_2026-10-27_REVISAO_EDITORIAL.md).


## Ciclo 19 — Contratos de aceite para futuro piloto privado

O módulo `pilot/readiness.py` verifica uma **matriz pública de requisitos** para um futuro ambiente corporativo privado. A saída contém **13 controles sem evidências autenticadas**, **5 aceites externos pendentes**, **10 ameaças de segurança e governança** e quatro cenários fictícios de revalidação. A decisão permanece `blocked_no_external_evidence`; nenhum piloto foi iniciado ou aprovado.

As exigências de identidade e aplicação usam referências primárias NIST SP 800-63-4, OWASP ASVS 5.0.0 e LGPD, com **efetividade OEM explicitamente separada como lacuna de engenharia não suprida**. O programa não importa documentos licenciados, dados de colaboradores, SAP, ECM ou telemetria. Contratos versionados, testes adversariais e relatórios HTML/JSON offline em `pilot/` compõem a entrega.

```bash
python -m pilot.readiness --snapshot build/fmea-public/fmea-public.snapshot.json --editorial build/editorial/review-protocol.v1.json --output build/pilot/readiness-report.v1.json --html build/pilot/readiness-report.v1.html
```

A reprodução exige gerar os arquivos públicos sintéticos dos Ciclos 13–18. Veja o [relatório técnico do Ciclo 19](docs/CICLO_2026-10-27_PRONTIDAO_PILOTO_PRIVADO.md).


## Ciclo 20 — Decisão Go/No-Go de piloto privado

O módulo `pilot/go_nogo.py` transforma os 13 controles do Ciclo 19 em dependências de aprovação, **13 manifestações de evidência não submetida**, **cinco revisões externas pendentes** e **10 correções de achados sintéticos**. O resultado é necessariamente `no_go`, sem acesso real, consentimento, efetividade OEM comprovada ou autorização operacional. São **15 contratos JSON Schema** de evidências, aceites, dependências, decisão, remediação, classificação e limites de autoridade.

```bash
python -m pilot.go_nogo --snapshot build/fmea-public/fmea-public.snapshot.json --readiness build/pilot/readiness-report.v1.json --output build/go-nogo/no-go-report.v1.json --html build/go-nogo/no-go-report.v1.html
```

A saída é somente JSON/HTML offline e o CI testa recusas de falso aceite, decisão `go`, alteração ECM/SAP, retenção não autorizada ou métricas interavaliadores inventadas. Veja a [documentação completa do Ciclo 20](docs/CICLO_2026-10-27_PACOTE_GO_NO_GO.md).


## Ciclo 21 — Sequenciamento documental das evidências necessárias

O módulo `pilot/evidence_sequence.py` organiza **13 controles e 17 vínculos de dependência** em ordem topológica determinística, com **sete fases propostas**, **cinco handoffs conceituais** e **dez cenários adversariais**. Três controles sem precedentes (identidade, configuração do equipamento e retenção) aparecem como pontos de entrada estruturais, não como cronograma real ou escore de risco.

As evidências continuam ausentes, as cinco áreas não assinaram aceite e a decisão segue `no_go`. Nenhuma fase é executada, nenhum HH/custo/data é fabricado e não existe integração SAP/ECM, licença OEM comprovada ou liberação operacional.

```bash
python -m pilot.evidence_sequence --snapshot build/fmea-public/fmea-public.snapshot.json --gng build/go-nogo/no-go-report.v1.json --output build/sequencing/evidence-sequence.v1.json --html build/sequencing/evidence-sequence.v1.html
```

O comando requer entradas sintéticas dos Ciclos 13–20. Os relatórios HTML e JSON são gerados offline e verificados no CI. Consulte a [documentação metodológica do Ciclo 21](docs/CICLO_2026-10-27_SEQUENCIAMENTO_EVIDENCIAS.md).


## Ciclo 22 — Contradições documentais e revisão cruzada

O núcleo `pilot/evidence_contradictions.py` analisa **seis pares de afirmações fictícias** para identidade duplicada, competência expirada, revisão OEM substituída, configuração alterada, opiniões divergentes e inconsistência jurídica de retenção. A propagação percorre todos os descendentes do **grafo canônico de 13 controles e 17 dependências**. O motor cria seis perguntas de revisão cruzada e registra a invalidação lógica de doze afirmações de evidência, sem inferir falha física ou descartar hipóteses.

Todas as conclusões permanecem `no_go`; não há comprovação OEM por série, parecer humano, prova corporativa, SAP/ECM, OS ou liberação de equipamento. Geram-se JSON e HTML offline com verificador por reconstrução do corpus público FMEA pinado:

```bash
python -m pilot.evidence_contradictions --snapshot build/fmea-public/fmea-public.snapshot.json --sequence build/sequencing/evidence-sequence.v1.json --gng build/go-nogo/no-go-report.v1.json --output build/contradictions/contradictions.v1.json --html build/contradictions/contradictions.v1.html
```

Consulte a [documentação técnica do Ciclo 22](docs/CICLO_2026-10-27_CONTRADICOES_EVIDENCIAS.md).


## Ciclo 23 — Caminhos de reabertura e cobertura documental

O módulo `pilot/reopen_coverage.py` avalia **100 cenários fictícios** (13 raízes individuais, 78 pares, três alterações de contexto e seis conflitos do Ciclo 22), mantendo **13 controles/17 dependências**. O fixture `pilot/reopen-coverage.v1.json` fixa um oráculo de alcançabilidade Floyd–Warshall, comparado aos caminhos reconstruídos por DFS e à cascata do Ciclo 22.

A saída demonstra caminhos mínimos, alternativas redundantes, testemunhos de não alcançabilidade e verificação de cinco mutações estruturais. O status permanece `no_go`: caminho documental **não é falha física, previsão de dano, segurança comprovada ou autorização SAP/ECM/OS**.

```bash
python -m pilot.reopen_coverage --snapshot build/fmea-public/fmea-public.snapshot.json --gng build/go-nogo/no-go-report.v1.json --sequence build/sequencing/evidence-sequence.v1.json --contradictions build/contradictions/contradictions.v1.json --output build/coverage/reopen-coverage.v1.json --html build/coverage/reopen-coverage.v1.html
```

A documentação detalhada está em [Ciclo 23 — Cobertura estrutural](docs/CICLO_2026-10-27_COBERTURA_REABERTURAS.md).


## Ciclo 24 — Revisão de mudanças de dependências (P&D v2.4.0)

`pilot/graph_change_review.py` compara **10 propostas totalmente fictícias** (adicionar, remover ou inverter arestas, trocar dono de controle, suprimir um controle, reabrir por hipótese OEM) com o DAG público de **13 controles/17 arestas**. O relatório compara pares, distâncias e caminhos e verifica o impacto documental sobre os **100 cenários canônicos** do Ciclo 23; candidatos com ciclo ou ponta desconhecida não são classificados como inalterados.

Todos os resultados são `veto_no_merge` e `no_go`: o motor não edita o grafo original, não atesta um procedimento OEM e não pode executar SAP, ECM, OS, compra ou liberação. A visualização HTML e o JSON são offline.

```bash
python -m pilot.graph_change_review --snapshot build/fmea-public/fmea-public.snapshot.json --gng build/go-nogo/no-go-report.v1.json --sequence build/sequencing/evidence-sequence.v1.json --contradictions build/contradictions/contradictions.v1.json --coverage build/coverage/reopen-coverage.v1.json --output build/graph-change/graph-change-review.v1.json --html build/graph-change/graph-change-review.v1.html
```

Veja a [documentação técnica do Ciclo 24](docs/CICLO_2026-10-27_REVISAO_MUDANCAS_GRAFO.md).

## Ciclo 26 — Contestação e revogação documental

O gerador `pilot/change_review_adjudication.py` preserva duas opiniões fictícias de áreas distintas por cenário, modela dez eventos de revisão obsoleta, retirada de prova, conflito e alegação de aprovação, e reconstrói uma cadeia de auditoria local. Os **13 controles/17 arestas do grafo permanecem inalterados**, nenhum parecer é real, e a decisão é sempre `no_go`. A cadeia de proveniência anterior deve ser validada em CI antes de consumir os dossiês. [Documentação do Ciclo 26](docs/CICLO_2026-10-27_CONTESTACAO_REVOGACAO.md).

## Ciclo 27 — Benchmark editorial de investigação mecânica

O módulo `benchmarks/mechanical_reasoning.py` avalia a seleção determinística da **próxima pergunta** diante de lacunas e contradições em 24 cenários **sintéticos** de comando final, hidráulica, eletrônica e arrefecimento. Um gabarito editorial separado permite detectar regressões e alterações de comportamento em quatro famílias de sistemas. As 3 hipóteses por domínio permanecem abertas em cada cenário; nenhuma informação presente no teste constitui medição real ou comprovação de causa. A concordância com esse gabarito **não é acurácia diagnóstica nem revisão independente**. Veja [o dossiê do Ciclo 27](docs/CICLO_2026-10-27_BENCHMARK_RACIOCINIO_MECANICO.md).

## Ciclo 28 — Generalização adversarial controlada

O benchmark `benchmarks/generalization_stress.py` avalia **34 cenários sintéticos novos** que não estavam no conjunto fixado do Ciclo 27. Uma camada separada bloqueia a progressão quando a proveniência está ausente, contraditória, obsoleta ou revogada; domínios não modelados levam a abstenção e encaminhamento. Compara o seletor inalterado do Ciclo 27 e o mesmo seletor precedido pela nova barreira documental. **A concordância é medida contra gabarito editorial criado pelo próprio projeto; não há revisão externa, casos reais nem acurácia diagnóstica mensurada.** Detalhes em [Ciclo 28](docs/CICLO_2026-10-27_GENERALIZACAO_ADVERSARIAL.md).

## Ciclo 29 — Ensaio de revisão técnica

O módulo `benchmarks/blind_review_protocol.py` exporta **12 casos fictícios sem o gabarito embutido**, compara **24 pareceres sintéticos** de dois personagens revisores e aponta erros críticos, relevantes e leves. O arquivo exportado omite expectativas, mas **o repositório público contém o gabarito**, portanto não se realizou avaliação efetivamente cega, revisão humana nem medição de acurácia diagnóstica. Divergências são preservadas; não geram consenso ou autorização de manutenção. [Método e limitações](docs/CICLO_2026-10-28_PROTOCOLO_REVISAO_INDEPENDENTE.md).

## Ciclo 30 — Custódia de avaliação externa, sem dados no repositório

O utilitário **offline** `benchmarks/heldout_study.py` separa arquivos de casos, gabarito, chave de custódia, pacotes de perguntas, pareceres e relatório. Por construção, o CLI **rejeita arquivos de entrada ou saída localizados dentro deste repositório público**. Uma trava HMAC vincula os casos ao gabarito sob chave mantida pelo custodiante e cada submissão recebe um recibo de congelamento antes de eventual comparação. Os testes de CI usam apenas casos sintéticos temporários, sem publicar chave, respostas privadas ou pareceres reais. **Não há avaliadores independentes conectados, autenticação humana ou validação mecânica demonstrada.** [Manual e ameaças à validade](docs/CICLO_2026-10-28_CUSTODIA_AVALIACAO_EXTERNA.md).

## Ciclo 31 — Auditoria de qualidade e contaminação entre divisões

O módulo `benchmarks/validation_set_quality.py` examina **26 casos sintéticos**, divididos em treinamento (8), desenvolvimento (4) e teste (14), com **12 etiquetas de hipóteses** nas famílias comando final, hidráulica, eletrônica e arrefecimento, mais casos não modelados de freios e transmissão. Identifica reuso de linhagem, origem, evidência e texto quase idêntico entre divisões, lacunas de etiquetas no teste e ausência de situações que exigem abstenção. A auditoria rejeita conjuntos contaminados, mas sua cobertura **não comprova mecanismo físico nem generalização para dados inéditos**; o banco permanece público e autoral. Não se altera a custódia privada nem se habilita diagnóstico operacional. [Escopo e riscos](docs/CICLO_2026-10-28_QUALIDADE_CONJUNTO_VALIDACAO.md).

## Ciclo 32 — Qualidade privada obrigatória antes de distribuir casos

O CLI `benchmarks/heldout_study.py prepare` exige agora manifesto e política de qualidade privados, mantidos fora do Git. O auditor compara casos de teste ao pacote custodial por ID, narrativa, domínio, status documental e digest, verifica vazamentos e exige cobertura mínima. **Falha de qualidade bloqueia a geração do pacote, lock e recibo.** O `score` reavalia metadados e comprovante antes da pontuação. Os controles são documentais, não validação mecânica independente. [Detalhes técnicos](docs/CICLO_2026-10-28_QUALIDADE_CUSTODIA_PRIVADA.md).

## Ciclo 33 — Taxonomia técnica com rastreabilidade das hipóteses

O arquivo `knowledge/mechanical-evidence-map.v1.json` distingue **9 mecanismos físicos candidatos** de **3 fatores que confundem a interpretação**, organizados em quatro sistemas: comando final, hidráulica, eletrônica e arrefecimento. Cada relação contém função, falha funcional, relato, alternativa, próxima pergunta discriminante, fonte pública do fabricante ou resumo público de norma e **limite explícito de aplicabilidade**. Uma fonte genérica não comprova falha, causa raiz, série OEM ou procedimento autorizado de um equipamento específico. Executável local, três contratos, testes adversariais e relatório JSON/HTML offline em `knowledge/mechanical_evidence.py`. [Fundamentação e limitações](docs/CICLO_2026-10-28_TAXONOMIA_MECANICA_FUNDAMENTADA.md).
