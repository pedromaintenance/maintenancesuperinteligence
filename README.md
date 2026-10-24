# MaintenanceSuperinteligence

**Uma arquitetura aberta, incremental e auditável de conhecimento para gestão de ativos, engenharia de manutenção e equipamentos móveis de mineração.**

> **Estado: protótipo de prontidão de implantação P&D v1.1.0 (24/10/2026).** Este repositório ainda **não é** um sistema de diagnóstico homologado, software embarcado ou agente capaz de controlar máquinas. Os documentos definem pesquisa, requisitos, ontologia, interfaces e validação futura.

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
