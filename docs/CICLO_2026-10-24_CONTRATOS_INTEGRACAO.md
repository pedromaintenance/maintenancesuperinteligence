# Ciclo 10 — Contratos para futura integração privada e testes de confiança

**Data:** 24/10/2026 · **Versão:** protótipo P&D 1.0.0 · **Issue:** [#20](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/20).

## Entrega e alcance

Este ciclo **não implanta** serviço corporativo. Entrega oito contratos JSON Schema, política de papéis `governance/integration-policy.v1.json`, um adaptador `governance/integration_contracts.py` que aceita **exclusivamente dados SIM-*** e um conjunto de testes adversariais. A arquitetura privada foi detalhada no [Ciclo 09](CICLO_2026-10-24_ARQUITETURA_RESTRITA.md).

**Nenhuma autenticação, assinatura, validação de competência, auditoria externa, evidência real, documento OEM por série ou autorização de operação foi realizada.**

## Contratos de integração

| Contrato | Prova que precisará vir de ambiente corporativo confiável |
| --- | --- |
| `AuthenticatedPrincipal` | sujeito único, papel ativo e tenant verificados no backend |
| `CredentialAssertion` | emissor, público-alvo, assinatura, prazo, revogação e proteção contra repetição |
| `TechnicalQualification` | competência disciplinar e conflito de interesses validados fora do cliente |
| `ClaimVersion` | revisão vinculada ao conteúdo, com histórico independente |
| `IndependentReviewDecision` | decisão referente à revisão atual e a pessoa independente, com assinatura verificável |
| `EvidenceManifest` | proveniência e direitos de uso, classificação, retenção e acesso à evidência |
| `AuditAnchor` | armazenamento protegido, sequência e tempo verificáveis independentemente |
| `OemEffectivityAttestation` | documentação licenciada, versão, modelo, série/arranjo, condição de configuração e revisão por especialista habilitado |

Os oito esquemas descrevem, **neste repositório**, somente a forma sintética de entrada: os indicadores `*Verified` permanecem `false`, e campos com dados restritos ficam nulos. Não são contratos prontos para aceitar credenciais reais no projeto público. Versões efetivamente privadas deverão usar campos de asserção verificados no servidor, com referências opacas e segregação por tenant. Mesmo em ambiente privado, a aprovação de uma *afirmação* e a autorização para executar manutenção serão fluxos distintos.

## Matriz RBAC/ABAC de intenção

| Papel | Pode propor no desenho futuro | Não pode concluir sozinho |
| --- | --- | --- |
| Autor | criar/revisar afirmação | avaliar sua própria afirmação; autorizar manutenção |
| Revisor | submeter avaliação técnica | revisar sua própria autoria; adjudicar o mesmo caso; autorizar operação |
| Adjudicador | arbitrar divergência fundamentada | substituir os dois revisores independentes |
| Auditor | inspecionar metadados e histórico | editar avaliação ou qualificar a própria decisão |
| Custodiante | gerir acesso às evidências | usar acesso aos dados como autoridade de revisão |
| Administrador | administrar papéis e revogação | obter poderes de aprovação técnica a partir de privilégios de sistema |
| Especialista OEM | propor verificação de aplicabilidade | autoaprovar efetividade ou liberar equipamento |

Na política pública, **todos os papéis permanecem sem poderes efetivos**. Os nomes das ações representam somente requisitos de separação de funções para um serviço futuro. O adaptador bloqueia: criar OS, liberar máquina, modificar ECM, aprovar serviço, homologar efetividade OEM e atestar assinaturas.

## Condições de validação real (não implementadas)

Antes de qualquer revisão com valor técnico e corporativo, a plataforma privada deverá verificar ao menos:

1. Identidade federada e ativa a partir de provedor de identidade empresarial, validada **no backend**, com issuer, audience, assinatura, validade, nonce e revogação. Não aceitar booleans de autenticação enviados pelo cliente.
2. Competência registrada na fonte corporativa e alinhada ao sistema/componente; designação dos revisores por pessoas com alçada, sem autopromoção ou conflito.
3. Dois **indivíduos reais independentes**, distintos do autor, com decisão sobre a mesma revisão imutável. Divergências exigem adjudicador terceiro e justificativa registrada.
4. Assinatura criptográfica verificável, política de chaves, expiração/revogação e registro de tempo confiável; armazenamento de auditoria independente do administrador de aplicação.
5. Confirmação de direito de acesso ao documento, publicação e revisão OEM, série/arranjo/intervalo efetivo, configuração da máquina e condições do procedimento.
6. Reavaliação em caso de mudança de versão de afirmação, revisão da literatura OEM, alteração de configuração, revogação de usuário, conflito detectado ou novos laudos.
7. Política de retenção, minimização, classificação, autorização, exclusão e logs sem vazamento de dados pessoais, SAP, ECM ou conteúdo licenciado.
8. Autorização de serviço operacional como decisão **independente** da qualificação do conhecimento.

Propostas de avaliação futura: NIST SP 800-63-4 (identidade digital), SP 800-63B-4 (autenticação) e SP 800-63C-4 (federação); OWASP ASVS 5.0.0 (controles verificáveis de aplicação e logs). Essas fontes orientam requisitos, **não** certificam o software atual:

- [NIST SP 800-63-4](https://csrc.nist.gov/pubs/sp/800/63/4/final)
- [NIST SP 800-63B-4](https://csrc.nist.gov/pubs/sp/800/63/b/4/final)
- [NIST SP 800-63C-4](https://csrc.nist.gov/pubs/sp/800/63/c/4/final)
- [OWASP ASVS 5.0](https://github.com/OWASP/ASVS)

## Contract testing offline

O arquivo `examples/integration-fixture.v1.json` contém oito personagens fictícios — autor, dois revisores, adjudicador, auditor, custodiante, administrador e especialista OEM. O exercício inclui um parecer de suporte e outro contestatório; o resultado será `disputed_simulation`, nunca revisão humana autenticada.

O validador `governance/integration_contracts.py` impõe campos exatos, identidade `SIM-*`, ausência de provas externas, revisão da afirmação, referências públicas declaradas, dois revisores de papel válido e identificadores distintos. Rejeita entrada que se proclame verificada por si própria. O relatório discrimina explicitamente os dez pré-requisitos externos não implementados.

```bash
python -m unittest discover -s tests -v
python -m governance.integration_contracts \
  --policy governance/integration-policy.v1.json \
  --fixture examples/integration-fixture.v1.json \
  --output build/integration/contracts.report.json
```

A CLI usa biblioteca padrão de Python e não possui cliente HTTP, conector a SAP/ECM ou autenticação caseira. Um CI verde demonstra **consistência de contratos sintéticos e rejeição de adversários conhecidos**, não segurança de produção.

## Critérios de aceite para qualquer projeto privado

- Aval de Engenharia, TI/Sec, gestão documental/OEM, Privacidade/Jurídico e responsável pelos dados, com aprovações explícitas.
- Ambientes e credenciais corporativos configurados, com acesso segregado e testes negativos de autorização feitos por equipe independente.
- Licenciamento de literatura e privacidade demonstrados; dados reais nunca trafegam pelo GitHub Actions público.
- Log externo verificável, carimbo de tempo, chave gerida e procedimentos de investigação de incidente.
- Revisão real por dois profissionais competentes e independentes, adjudicação e reabertura diante de mudanças.
- Medição de desempenho do diagnóstico em corpus autorizado e adjudicado: nenhum percentual de acurácia pode ser atribuído aos fixtures atuais.
- Nenhuma autorização de manutenção ou operação por simples aprovação de literatura.

**Próximo desenvolvimento recomendado:** definir uma camada de avaliação de prontidão de implantação (sem credenciais) com matriz de evidências de aceite e testes de incompatibilidade entre versões de contratos, a fim de identificar os bloqueios para uma futura implementação aprovada.
