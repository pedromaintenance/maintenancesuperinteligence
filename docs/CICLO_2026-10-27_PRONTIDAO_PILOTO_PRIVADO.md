# Ciclo 19 — Critérios de aceite externo para futuro piloto privado

**Data:** 27/10/2026 · **Versão P&D:** 1.9.0 · **Issue:** [#38](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/38)

## Resumo executivo

Este ciclo converte os bloqueios dos Ciclos 10 e 18 em **critérios de prontidão que podem ser auditados futuramente**, mas não autoriza, implanta ou inicia um piloto com dados reais. O código publicado apenas verifica a consistência de requisitos sintéticos, rejeita provas fabricadas e gera relatórios offline.

A saída obrigatória é `blocked_no_external_evidence`, com **13 controles não verificados**, **5 aceites externos não solicitados**, **10 ameaças cuja mitigação não foi demonstrada**, quatro exemplos de invalidação de revisão e **zero operações permitidas**. Nenhum teste é uma certificação NIST/OWASP, conformidade LGPD, validação mecânica ou aprovação por engenheiro.

## Referências técnicas verificadas e limites

- **NIST SP 800-63-4 (2025)** — identidade digital, verificação, autenticação e federação. Documentação primária: https://csrc.nist.gov/pubs/sp/800/63/4/final . Fornece contexto para exigir integração corporativa de identidade, sem demonstrar a existência desse controle.
- **OWASP ASVS 5.0.0 (2025)** — requisitos para desenho e teste de segurança de aplicações e serviços: https://asvs.owasp.org/ . Apoia a especificação de autorização, validação e registros seguros; não valida o código corporativo inexistente.
- **Lei nº 13.709/2018, LGPD, texto oficial vigente** — princípios de finalidade, necessidade, adequação, segurança e requisitos de tratamento, incluindo análise de base legal aplicável: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm . Este repositório não escolhe uma base legal em nome de uma empresa e não assume que consentimento seja sempre o fundamento adequado.
- **OEM-APPLICABILITY-PENDING** — *não é fonte publicada*. É um marcador de lacuna de engenharia: somente publicação do fabricante obtida licitamente, revisão, configuração e efetividade por máquina, verificadas por pessoal autorizado, poderiam atender esse controle futuro. NIST, OWASP e LGPD não comprovam limites de serviço, sequência de manutenção, peças ou efetividade de publicação Caterpillar/Sandvik.

Os controles abaixo são **propostas de projeto** a validar pelas respectivas áreas, não trechos normativos reproduzidos integralmente ou alegações de conformidade.

## Matriz de 13 evidências externas exigidas

| Controle | Área proponente | Evidência esperada fora do GitHub público |
| --- | --- | --- |
| identity-proof | TI | Principal individual autenticado em IdP corporativo e controle de unicidade |
| competence | Engenharia | Credencial e competência técnica verificáveis por disciplina, validade e escopo |
| conflict-screen | Jurídico | Política e avaliação de conflito de interesses com revisão independente |
| two-independent-reviews | Engenharia | Duas pessoas distintas revisando a mesma versão vigente, sem autoverificação |
| signed-decision | Segurança da Informação | Prova de autoria/integridade validada no servidor; não confiar em marcação enviada pelo cliente |
| trusted-audit | Segurança da Informação | Trilhas protegidas, imutabilidade verificável fora da aplicação e tempo confiável |
| oem-effectivity | Engenharia | Publicação autorizada, revisão OEM e efetividade por série/arranjo |
| equipment-configuration | Gestão de Manutenção | Configuração atual do equipamento e histórico de alterações |
| evidence-legitimacy | Jurídico | Autorização de uso, licenças e finalidade de tratamento das evidências |
| version-lock | TI | Hash/trava da revisão vigente, invalidação de decisões sobre versões obsoletas |
| revocation-reopen | TI | Revogação/expiração de credenciais, reabertura e rejeição de parecer antigo |
| privacy-retention | Jurídico | Classificação, minimização e retenção justificadas/aprovadas, tratamento de PII e logs |
| operational-firewall | Gestão de Manutenção | Separação da revisão técnica em relação a OS, requisição de peças, ECM e liberação operacional |

As cinco instâncias de aceite são **TI**, **Segurança da Informação**, **Engenharia**, **Jurídico** e **Gestão de Manutenção**. Todas permanecem `not_requested`. Essas áreas deverão negociar alçadas, responsáveis, evidências e responsabilidades específicas em um projeto privado; o GitHub público não nomeia pessoas nem presume aprovação.

## Registro de dez ameaças e condição de falha segura

| Ameaça | Consequência lógica exigida |
| --- | --- |
| Duas contas vinculadas ao mesmo indivíduo | Negar independência; conferir principal real em IdP |
| Credencial expirada/revogada | Invalidar parecer; reabrir revisão |
| Assinatura falsa ou flag do cliente | Negar comprovação de autoria; buscar verificação externa |
| Mudança da revisão do manual OEM | Invalidar efetividade anterior; nova revisão técnica |
| Alteração de configuração da máquina | Exigir nova verificação de aplicabilidade |
| Conflito de interesses não declarado | Bloquear aceite e exigir avaliação por pessoa independente |
| Criação não autorizada de nota SAP | Bloquear transmissão; manter sistema operacional isolado |
| Exposição de PII ou telemetria em logs públicos | Minimizar e restringir acesso; nunca anexar dados reais ao projeto |
| Adulteração do histórico | Exigir trilha protegida e âncora externa confiável |
| Cópia de manual OEM sem licença | Impedir ingestão e publicação; validar direitos em ambiente restrito |

A decisão esperada em todos os casos simulados é `deny_and_require_external_revalidation`. O sistema **não afirma que uma dessas ameaças ocorreu no campo**; são exercícios de projeto e teste de controle.

## Quatro cenários de versão/reabertura

O módulo simula, sobre os quatro documentos fictícios:

1. `SIM-NOTE-001`: ausência de evidências reais — permanecer bloqueado.
2. `SIM-NOTE-002`: credencial de revisor hipoteticamente revogada — reabrir avaliação de identidade.
3. `SIM-NOTE-003`: revisão de documento OEM hipoteticamente substituída — revalidar publicação, versão e aplicabilidade.
4. `SIM-NOTE-004`: alteração fictícia de configuração de equipamento — reavaliar arranjo, efetividade e escopo.

Em nenhum cenário há parecer vigente autenticado ou máquina real. A cadeia SHA-256 é apenas um encadeamento verificável **em relação ao fixture canônico preservado**; não é assinatura, timestamp confiável ou auditoria imutável no mundo real.

## Governança de dados e licenças

**Público-sintético:** identificadores `SIM-*`, requisitos, resultados falsos de autorização e metadados de documentação pública. Não há PII, dados operacionais ou credenciais.

**Corporativo-privado:** registros de SAP PM, condição, telemetria, laudos, evidências de revisão, identificadores de pessoal e logs. Só em repositório/sistema privado formalmente aprovado, com acesso mínimo e finalidade definida. Não podem ser importados para esta implementação.

**OEM licenciado:** manuais, séries, procedimentos e dados de configuração protegidos. Repositório segregado com gestão de licenças e controle de efetividade aplicável, somente após validação jurídica e de engenharia.

Prazos de retenção ficam `null`: não existe política aprovada. Coleta, retenção, descarte, compartilhamento e base legal precisam ser documentados antes de qualquer uso de dados reais; logs de segurança também exigem minimização, segregação de segredos e política de acesso.

## Plano metodológico para futuro teste humano

Antes de começar qualquer estudo real, definir por escrito: finalidade e base legal do tratamento; responsabilidades das áreas e participantes; amostragem suficiente de notificações reais autorizadas e anonimizadas quando viável; critérios por classe de equipamento; revisores competentes e independentes; instruções de avaliação padronizadas; instrumento de rubrica congelado; estratégia para pontos discordantes; avaliação cega entre revisores; método estatístico de concordância ajustado à escala da rubrica; e processo de governança para contestação e correção.

Um simples percentual de concordância pode ocultar coincidências esperadas por acaso. Dependendo da natureza dos dados, avaliar **Cohen's kappa** para dois avaliadores e categorias nominais, versões ponderadas para ordinais, ou outros modelos mais apropriados quando houver múltiplos revisores e amostragem adequada. Nenhuma estatística foi calculada neste ciclo.

Não extrapolar os 12 critérios editoriais do Ciclo 17 para acurácia de manutenção real. Revisão documental competente, diagnóstico físico, planejamento seguro e autorização de operação são decisões distintas.

## Implementação e reprodução

Arquivos centrais: `pilot/readiness-fixture.v1.json` (13 controles, 5 áreas, 10 ameaças, 4 cenários), `pilot/readiness.py` (validador estrito, abstenção determinística, verificação e relatórios HTML/JSON), `tests/test_private_pilot_readiness.py` (testes adversariais), contratos em `contracts/` (incluindo os oito centrais pedidos na Issue #38).

Gerar os artefatos sintéticos de dossiê, notificação, qualidade e revisão editorial seguindo a documentação anterior. Depois:

```bash
python -m pilot.readiness \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --editorial build/editorial/review-protocol.v1.json \
  --output build/pilot/readiness-report.v1.json \
  --html build/pilot/readiness-report.v1.html
```

A CLI reconstitui o corpus público a partir do snapshot FMEA fixado e verifica igualdade integral dos relatórios e fixture. Modificações não autorizadas são recusadas antes de exportar. O HTML é offline, com CSP, sem scripts/formulários ou rede.

## Critérios de conclusão deste ciclo

- Treze controles/ cinco aceites continuam sem evidência autenticada.
- Dez ameaças conservam decisão de negação e necessidade de revalidação externa.
- Três eventos hipotéticos de revogação/mudança exigem reabertura sem herdar validade de parecer anterior.
- Zero comprovação OEM efetiva, zero credencial autenticada, zero concordância real, zero piloto privado executado, zero SAP/ECM/OS/liberação de máquina.
- CI mede apenas consistência do software e *fixtures* públicos. Não certifica conformidade normativa ou prontidão de implantação.

**Próxima etapa candidata:** modelar um *pacote de aceite por área*, com evidências a produzir, critérios objetivos de go/no-go para um piloto privado formalmente autorizado e um plano de validação com especialistas e dados sob controle corporativo. Não iniciar piloto real a partir do repositório público.
