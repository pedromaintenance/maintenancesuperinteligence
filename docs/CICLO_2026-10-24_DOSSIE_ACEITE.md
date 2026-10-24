# Ciclo 12 — Dossiê de aceite técnico para revisão de prontidão

**Data:** 24/10/2026 · **Versão P&D:** 1.2.0 · **Issue:** [#24](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/24)

## Objetivo e resultado

Transformar a matriz de implantação privada do Ciclo 11 em um **dossiê técnico legível por Engenharia, TI/Segurança, Privacidade/Jurídico e Gestão Documental**, com ações por função, evidências solicitadas, justificativa de bloqueio, exceções rejeitadas e impactos de alterações.

O dossiê é produzido em **JSON versionado** e **HTML standalone estático**. Ambos são gerados a partir de **fixtures fictícios** sem conexão com máquinas, funcionários, SAP, ECM, análise de óleo, manuais licenciados ou armazenamento corporativo. A página HTML não utiliza JavaScript, formulários, rede, imagens externas nem bibliotecas adicionais. A renderização faz *escape* de conteúdo dinâmico e incorpora uma Content Security Policy restritiva.

**Resultado de aceite:** `blocked_missing_private_verified_trust`. O projeto **não** concluiu que alguma implantação corporativa esteja pronta ou tenha sido aprovada.

## Objetos e contratos

| Tipo | Propósito | Limite do protótipo público |
| --- | --- | --- |
| `ReadinessFinding` | Síntese de um dos dez bloqueios, criticidade, responsável, critérios, dependências e risco de postergação | Sempre `blocked_pending_private_evidence` |
| `AcceptanceEvidenceRequest` | Formalizar qual prova precisa ser verificada no ambiente privado e qual função deve solicitá-la | `not_received`; endereço da evidência nulo |
| `OwnerAction` | Preparar ação para pessoa/função responsável; vincula solicitação e controle | `pending_not_executed` |
| `ExceptionRequest` | Registrar proposta de exceção sem eliminar uma barreira de confiança | `blocked_no_verified_evidence`, sem poder de dispensar controle |
| `IndependentReviewGate` | Delimitar decisões que dependerão de revisão autenticada por humanos | Identidade/independência/OEM/aprovação **sempre falsos** |
| `ReadinessChangeScenario` | Demonstrar gatilho de revisão após alteração contextual | Nenhum evento real ocorreu; sem reaprovação |
| `ReadinessDossierFixture` | Envelope de dez solicitações, dez ações, duas exceções e seis cenários | Somente `SIM-*` e metadados artificiais |

Todos têm JSON Schemas no diretório `contracts/`. O código também verifica **relacionamentos entre objetos**, que não são demonstrados apenas por validação estrutural: ID do controle, proprietário, evidência, solicitação, ação, fonte e ordem do plano.

Os dez controles, criticidades e dependências são derivados de `governance/deployment-readiness.v1.json`. O dossiê **não** aceita que sua fixture modifique um responsável, suprima um controle, marque uma ação executada ou introduza prova autenticada.

## Conteúdo do dossiê

O relatório incorpora:

- Dez achados de prontidão: **oito classificados como críticos e dois como altos** por critério editorial do exercício.
- Dez solicitações de evidência, todas não recebidas, e dez ações funcionais ainda não executadas.
- Duas exceções ilustrativas — indisponibilidade de IdP e ausência de revisão OEM — com decisão obrigatoriamente **bloqueada**.
- Seis cenários de mudança: os cinco gatilhos do Ciclo 11 e **conflito de interesses identificado**, que obriga revisar independência, segregação e decisão operacional.
- Cinco referências de compatibilidade: quatro arquivos públicos dos Ciclos 08–10 e o pacote de prontidão do Ciclo 11.
- Sete critérios para futuro aceite corporativo independente, inclusive documentação OEM efetiva por configuração/série, custódia, competência, privacidade e revisão de fontes.

A escala de risco da matriz **não foi calculada de incidentes reais, RPN ou frequência histórica**; é uma classificação de risco de arquitetura para orientar revisão futura.

### Exceções e requalificação

Exceções de indisponibilidade de infraestrutura ou documentação **não suspendem requisitos de segurança**. O modelo rejeita qualquer modificação que ative `waiveControl`, `mayDeploy` ou `approvedByRealPerson`.

Nos seis cenários, `reopenReview=true`, `previousQualificationRemainsValid=false` e `automaticReapproval=false` são invariantes. Isso não significa revogar uma autorização existente: **não há nenhuma**. É um requisito de desenho para um futuro serviço restrito.

### Compatibilidade de versões

O avaliador anterior confirma o conjunto de fontes públicas dos Ciclos 08–10 com esquema e versão 1.0.0. O dossiê exige adicionalmente o esquema e a versão **v1 do Ciclo 11**. Sua seção de compatibilidade inclui digests SHA-256 dos documentos estruturados e das fontes públicas verificadas. Esses hashes identificam mudanças de conteúdo no exercício, **não validam assinatura humana, migração privada ou cadeia de custódia externa**.

Uma mudança de esquema/versionamento reconhecido exige revisão da migração antes de qualquer implantação.

## Produzir o dossiê

```bash
python -m unittest discover -s tests -v

python -m governance.readiness_dossier \
  --source governance/deployment-readiness.v1.json \
  --fixture governance/readiness-dossier-fixture.v1.json \
  --output build/readiness/acceptance-dossier.v1.json \
  --html build/readiness/acceptance-dossier.v1.html
```

O arquivo HTML gerado pode ser aberto localmente no navegador e impresso para reunião de arquitetura. **Ele não é um portal empresarial**, não possui login, não coleta nem envia dados e não aceita parecer ou assinatura. O CI armazena ambos os formatos temporariamente como artefato de testes, sem encaminhar informações restritas.

## Casos adversariais e bloqueios

A suíte cobre, entre outros: controles ou solicitações suprimidas; duplicação de solicitação/exceção; parecer fictício apresentado como real; alteração de papel responsável; ação preenchida como concluída; prova armazenada em URL corporativa; exceção que dispensa IdP/OEM; mudança de configuração que mantém parecer antigo; ausência de reabertura por conflito; dados pessoais ou conteúdo licenciado marcados para publicação; deriva de versões; inserção de comando SAP; tentativas de injetar tags HTML; e saída fraudulenta apresentada como dossiê aprovado.

O pipeline exige `deploymentApproved=false`, `mayImportCorporateData=false`, `mayCreateWorkOrder=false`, `mayReleaseEquipment=false` e zero evidências recebidas.

## Critérios de transição para revisão real

Uma revisão empresarial futura exigirá autorização explícita para acesso a dados e responsabilidades por Engenharia, TI/Sec, Privacidade/Jurídico e Gestão Documental, infraestrutura IdP, competências verificadas, dois revisores independentes, documentos autorizados por série/arranjo, armazenamento protegido, verificação de assinaturas e auditoria. Esses elementos ainda precisam ser implantados e **não devem ser simulados como aceitos**.

**Próxima etapa sugerida:** desenvolver um protocolo de transição do dossiê sintético para uma checklist corporativa privada, avaliando responsabilidades, política de evidências e critérios de prova, antes de qualquer integração ou coleta de informação real.

O objetivo do Ciclo 12 é oferecer uma estrutura prática para revisar impedimentos e preparar decisões, sem confundir rastreabilidade de software com aprovação de engenharia.
