# Ciclo 09 — Arquitetura restrita para revisão técnica autenticada

**Data:** 24/10/2026 • **Versão:** protótipo P&D 0.9.0 • **Issue:** [#18](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/18)

## 1. Resultado e limite do ciclo

Foi especificada uma arquitetura de confiança para **uma futura implantação privada**, juntamente com um simulador offline de permissões, sequência de revisão, versões e auditoria. **Nenhum ambiente privado foi implantado, nenhum indivíduo foi autenticado e nenhuma assinatura digital foi produzida ou verificada.**

O nome de um projeto GitHub, o identificador de um revisor ou um hash SHA-256 não demonstram identidade, competência técnica, independência, validade de evidências ou aplicabilidade OEM. O estado `qualified_general_claim_simulation` corresponde somente ao consenso de dois **personagens fictícios**; não equivale a conhecimento tecnicamente qualificado por profissionais.

Este ciclo deliberadamente **não integra** SAP PM, CAT ET/ECM, telemetria, análise de óleo real, SIS licenciado, documentos de clientes ou perfis pessoais.

## 2. Arquitetura proposta e fronteiras de confiança

```text
PUBLIC KNOWLEDGE / GitHub                       RESTRICTED CORPORATE ENVIRONMENT (not deployed)
+--------------------------------------+         +--------------------------------------------+
| FMEA pinned by SHA, research schemas |         | Corporate IdP (identity / MFA / federation)|
| Generic reference IDs, synthetic     |         | Verified competency and COI declarations  |
| hypotheses, methods and benchmark     |         | Role assignment + revocation + separation |
+------------------+-------------------+         +----------+---------------------------------+
                   | published schema /              |
                   | reference ID only               v
                   |                      +----------+---------------------------------+
                   +--------------------> | Review API with policy enforcement       |
                                          | immutable claim version and source IDs   |
                                          | reviewer A + reviewer B + adjudicator    |
                                          +-----------+------------------------------+
                                                      |
                  +-----------------------------------+-----------------------+
                  |                                                           |
      +-----------v-------------------------+                 +---------------v------------------+
      | Private evidence and OEM document   |                 | Audit/event store and signer      |
      | vault / licensed access / retention |                 | external timestamps + KMS/HSM     |
      | SAP / oils / series / ECM events     |                 | append-only + monitored export    |
      +-------------------------------------+                 +----------------------------------+

OPERATIONS GATE — separate approval workflow. Reviewing a claim NEVER creates OS,
controls equipment, authorizes release, changes ECM, or performs hydraulic testing.
```

A seta representa **um contrato a ser desenhado**, não conexão atualmente instalada. A implantação deve evitar **qualquer** transmissão de conteúdo corporativo de volta ao repositório público por commit, log, artefato de CI, issue, relatório ou comentário.

### Zonas de dados e decisões

| Zona | Exemplos | Permissão de publicação |
| --- | --- | --- |
| **Pública** | Contratos, fontes abertas, hashes de snapshots públicos e exercícios `SIM-*` | GitHub, mediante revisão de conteúdo |
| **Restrita — engenharia** | Laudos e tendências SOS, horímetro, inspeções, DTC, relatórios de falha, configuração e série de equipamento | Somente repositório privado aprovado com política de acesso |
| **Restrita — conteúdo licenciado** | Manuais SIS/ET, desenhos OEM, boletins condicionados a licença e documentos de fabricante | Respeitar titularidade e licença; não republicar |
| **Restrita — identidade** | Nome, matrícula, papel, competência, empresa, registros de autenticação, assinaturas e possível COI | Diretório e trilha de revisão protegidos; minimização de dados |
| **Auditoria protegida** | Autor, revisão, hash do *payload*, evento, versão e decisão de autorização | Retenção e acesso específicos; não conter amostra bruta nem dados pessoais desnecessários |

O identificador público de uma afirmação pode ser preservado no sistema privado, mas seu vínculo com uma ocorrência real e sua evidência devem ficar em armazenamento controlado. Um *hash* de informação sensível também exige avaliação de risco de reidentificação, especialmente se o domínio é pequeno ou previsível.

## 3. Modelo de identidade e autorização ainda não implementado

O ambiente futuro deverá ter os seguintes *gates*, com verificação **no servidor** e sem confiar em atributos enviados pelo próprio navegador, pelo usuário ou por uma IA:

1. **Autenticação e ciclo de identidade:** diretório corporativo/IdP, MFA e mecanismo de federação, provas de autenticação verificadas pelo backend, validade de sessão, revogação e auditoria de login. O padrão NIST SP 800-63-4 serve de referência de engenharia, não significa certificação NIST deste projeto.
2. **Competência e atribuição:** matriz por disciplina e sistema; a pessoa não pode autodeclarar competência suficiente para obter alçada. Credenciais e treinamento precisam de fonte corporativa controlada e prazo de validade.
3. **Separação de funções:** autor não revisa a própria afirmação; dois revisores precisam de **identidades corporativas distintas** (incluindo detecção de alias para mesma pessoa), independência organizacional quando apropriada e COI documentado. O adjudicador é um terceiro, não um dos revisores.
4. **Revisão versionada:** revisão refere-se ao *hash* da versão integral da afirmação, evidências, citações e seus metadados de efetividade. Qualquer mudança relevante invalida pareceres anteriores para a nova revisão.
5. **Ciclo de assinatura:** se for adotado, assinar *payload* canônico com identificação do signatário, chave autorizada, contexto e instante confiável, verificar certificado e revogação segundo política vigente. Não presumir equivalência entre assinatura técnica, assinatura legal e aprovação de serviço.
6. **Custódia e logs:** registro imutável/append-only, com carimbo de tempo de fonte confiável, assinatura do serviço ou ancoragem periódica externa, monitoramento independente, retenção, privacidade e resposta a incidentes. Hash encadeado sozinho não impede substituição de toda a cadeia pelo seu operador.
7. **Segregação operacional:** qualificação do conhecimento não libera máquina, não altera ECM, não permite execução de teste com energia armazenada e não gera nota/OS SAP. Essas ações precisariam de fluxos separados e aprovados.

### Máquina de estados proposta (ambiente autorizado)

```text
draft
  -> under_review
      -> needs_evidence ------------------------> under_review (new revision)
      -> disputed -> independent_adjudication -> needs_evidence / under_review
      -> qualified_general_claim              (only with verified reviewers)
           -> applicability_assessment_pending
                 -> oem_series_verified        (only with OEM source+revision+scope)
                 -> rejected_or_out_of_scope
```

Uma aprovação de referência geral e a efetividade OEM são **portas distintas**. `oem_series_verified` requer no mínimo modelo, série/arranjo ou faixa efetiva, documento técnico autorizado, revisão/versionamento e evidência de aprovação verificável. Nenhuma saída desse estado representa automaticamente instrução de trabalho ou aprovação para operar.

## 4. Modelo de ameaças

| Ameaça | Falha a evitar | Controle futuro | Simulação offline |
| --- | --- | --- | --- |
| Impersonação / conta compartilhada | pessoa errada assina como engenheiro | identidade forte, sessão e MFA com prova no servidor | apenas rejeita campos `identityVerified=true`; **não autentica** |
| Autor revisa a própria análise | viés e conflito de função | alçada por identidade corporativa e relação autor/claim | rejeita papel `author` em parecer |
| Dois aliases da mesma pessoa | falsa independência | vínculo com identificador imutável no IdP, diretório e COI | bloqueia mesmo ID; **não detecta aliases reais** |
| Papel ou competência incorretos | parecer de disciplina não habilitada | competência validada por RH/engenharia e atribuição do projeto | rejeita papel e disciplina divergentes |
| Revogação / conflito declarado | parecer posterior ao desligamento ou COI | revogação, validade de sessão/credencial e política de histórico | rejeita `revoked=true` ou COI em fixture; **não consulta IdP** |
| *Replay* / envio duplicado | duplicação de parecer ou execução de evento antigo | nonce durável exclusivo por tenant, transação única/anti-replay | rejeita nonce e event ID repetidos na mesma fixture |
| Revisão obsoleta / TOCTOU | resultado apoiado em versão alterada | controle de versão concorrente e vínculo assinatura-hash | exige `targetRevision=1` e hash da versão do claim |
| Adulteração após parecer | registro editado ou substituído | armazenamento imutável, verificação externa de âncoras e logs | compara relatório reconstituído com entrada original |
| Falsa publicação OEM | generalização sem efetividade real | licença, documentação por série, revisão e gate independente | nega `mayVerifyOemSeries` e todos os direitos operacionais |
| Vazamento de dados | exposição de laudos, séries, pessoas e conteúdo licenciado | segregação, RBAC/ABAC, criptografia, DLP, revisão de logs e backups | fixture `SIM-*` e nenhum conector; **não é DLP real** |

**Risco residual:** um atacante com controle simultâneo sobre fixture, código validador e âncora de armazenamento pode regravar um exercício e seus hashes. CI verde **não** substitui infraestrutura de identidade, gestão de chaves, assinatura, custódia ou controle de acesso real.

## 5. Protótipo offline implementado

Arquivos:
- `examples/restricted-review-threat-fixture.v1.json`: três sequências de exercícios, sete personas e nove eventos.
- `governance/restricted_blueprint.py`: validação estrita, transições de estados, separação de papéis, nonce e evento únicos, revisão vinculada ao claim e cadeia de hashes.
- `contracts/restricted-review-{actor,event,case,threat-fixture,audit-event}.schema.json`: contratos de entradas e registro auditável, exclusivamente `SIM-*`.
- `tests/test_restricted_blueprint.py`: regressões adversariais de impersonação, replay, conflito, revisão obsoleta, adulteração e falsificação de aprovação.

**Exercícios:**
- Água no lubrificante: uma opinião de suporte, uma divergência e adjudicação fictícia para `needs_evidence`, mantendo a controvérsia registrada.
- Formulação de óleo: dois pareceres fictícios de suporte produzem `qualified_general_claim_simulation`, jamais suporte real autenticado.
- Pressão e carga hidráulica: um parecer insuficiente mantém `under_review` e demanda um segundo parecer independente.

O gerador oferece `verify_report`, que reconstrói integralmente a saída a partir da entrada original e rejeita adulterações no relatório (mesmo que o adulterador tente recalcular hashes). Essa comparação é útil **apenas se a entrada original estiver sob controle independente**, condição que não foi implementada fora do próprio GitHub.

### Executar

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public
python -m governance.restricted_blueprint \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --fixture examples/restricted-review-threat-fixture.v1.json \
  --output build/restricted-review/threat-fixture.report.json
```

O snapshot público FMEA é validado contra o checksum do lock. A fonte real de confiança aqui é somente o **conteúdo público fixado**. Nenhuma origem corporativa externa é consultada.

**Garantias explícitas:** `authenticatedIdentityCount=0`, `verifiedReviewSignatureCount=0`, `qualifiedClaimsForRealWorldUse=0`, `reviewAuthenticity=not_achieved`, `canApproveMaintenance=false`, `oemEffectivityVerified=false`.

## 6. Fontes externas verificadas e sua função

- [NIST SP 800-63-4, Digital Identity Guidelines (2025)](https://csrc.nist.gov/pubs/sp/800/63/4/final): orientação de referência para prova de identidade, autenticação, federação e seus níveis de garantia. **Não** demonstra que a futura implementação cumpre um IAL/AAL.
- [NIST SP 800-63B-4, Authentication and Authenticator Management (2025)](https://csrc.nist.gov/pubs/sp/800/63/b/4/final): requisitos de autenticador, gestão e asseguração; seleção de nível exige avaliação de risco concreta.
- [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS): catálogo de requisitos de verificação de controles para aplicações. Não substitui arquitetura de acesso licenciado e política de organização.
- [OWASP ASVS — V16 Security Logging](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md): orienta registro de eventos sensíveis à segurança e a proteção dos próprios logs.
- [Lei nº 13.709/2018 (LGPD), texto compilado no Planalto](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm): fundamento legal brasileiro de proteção de dados pessoais; a análise concreta de base legal, retenção, controlador e operador caberá à equipe jurídica e de privacidade.

Essas referências orientam **especificação e revisão futura**, não constituem certificado de conformidade do protótipo.

## 7. Critérios para um próximo passo autorizado

1. Patrocínio de TI/Segurança/Engenharia e definição de controlador e responsável por dados.
2. Ambiente privado aprovado com acesso nominal, IdP, MFA, segregação e mecanismo de revogação verificáveis.
3. Política de documentação OEM, contrato e efetividade por série, sem republicação indevida.
4. Definição de anexação de evidências, retenção, assinaturas, versionamento e auditoria que seja independente do administrador do serviço.
5. Dois revisores técnicos **reais** e adjudicador independente, com habilitações e conflitos documentados.
6. Testes de penetração, privacidade, recuperabilidade, logs e incidentes, além de revisão de engenharia antes de qualquer caso real.

**Próximo ciclo proposto:** formalizar o contrato da infraestrutura privada e um plano de integração progressiva sob autorização corporativa; não desenvolver um login caseiro ou publicar dados reais no GitHub.
