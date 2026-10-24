# Ciclo 11 — Prontidão e compatibilidade para implantação privada

**Data:** 24/10/2026 · **Versão P&D:** 1.1.0 · **Issue:** [#22](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/22)

## Escopo e resultado técnico

O Ciclo 10 definiu os contratos de integração do futuro ambiente restrito. O Ciclo 11 acrescenta um **gate de prontidão**: quais condições precisam ser cumpridas, em que ordem, com qual prova externa, por quem e com quais consequências se as condições mudarem.

**Nenhum ambiente foi implantado, nenhum usuário real foi autenticado, nenhuma literatura OEM foi efetivamente homologada e nenhum equipamento foi liberado.** Este projeto contém exclusivamente controles, estados e evidências sintéticos. A execução do CI mede conformidade do software com este contrato, não segurança ou aptidão para produção.

O avaliador `governance/deployment_readiness.py` consome `governance/deployment-readiness.v1.json` e a política de negação de autoridade do Ciclo 10. A saída identifica pendências, dependências, histórico de compatibilidade pública e os gatilhos que **obrigariam** nova verificação independente num ambiente corporativo.

## Os dez controles para o ambiente futuro

| Item | Controle | Responsável genérico | Risco de ausência |
| --- | --- | --- | --- |
| 1 | IdP corporativo com verificação server-side | TI / Segurança da Informação | Crítico |
| 2 | Identidade humana única e função ativa | TI / Gestão de Acessos | Crítico |
| 3 | Competência por disciplina verificada em fonte corporativa | Engenharia / Gestão de Competências | Alto |
| 4 | Segregação entre autor, revisores e adjudicador | Engenharia / Governança | Crítico |
| 5 | Declaração e verificação independente de conflitos de interesse | Compliance / Engenharia | Alto |
| 6 | Dois revisores humanos distintos e independentes | Engenharia / Revisão Técnica | Crítico |
| 7 | Versão imutável da afirmação e manifesto de fonte | Gestão Documental / Engenharia | Crítico |
| 8 | Carimbo de tempo e armazenamento de auditoria protegido | Segurança / Auditoria | Crítico |
| 9 | Licença e efetividade OEM por publicação/revisão/arranjo | Engenharia / Gestão Documental | Crítico |
| 10 | Aprovação operacional em fluxo independente | Operação / Manutenção / Segurança | Crítico |

A tabela resume dependências. A ordem de execução operacional é calculada como **ordenação topológica estável**; etapas sem precedência comum podem ser realizadas em paralelo, respeitando as dependências declaradas.

Observação de escopo: classificação, licenciamento, minimização de dados, retenção, integridade da evidência e proteção contra vazamento fazem parte dos critérios verificáveis dos controles de fonte, auditoria e aprovação, e não podem ser dispensados por segurança de rede.

## Estado inicial e avaliação

| Estado de controle | Quantidade | Semântica |
| --- | ---: | --- |
| `not_implemented` | 4 | O exercício ainda não descreve implementação demonstrada |
| `planned` | 3 | Existe previsão editorial; não foi comprovada execução |
| `available_unverified` | 3 | Existe uma referência fictícia a uma possibilidade; não foi verificada |
| `independently_verified` | **0** | Proibido na fixture pública |
| `revoked` | **0** | Estado reservado para futura fonte de confiança, não pode ser autodeclarado |

As três classes iniciais **não são um levantamento de maturidade real** da organização. A distribuição 4/3/3 serve apenas para exercitar a máquina de estados. Não significa que algum controle real foi iniciado, está disponível ou funciona.

O resultado do simulador permanece `acceptance=blocked_private_deployment`, com zero verificações independentes e dez dependências privadas pendentes. `mayConnectCorporateSystems`, `mayImportRealEvidence`, `mayApproveOemEffectivity`, `mayCreateWorkOrder` e `mayReleaseEquipment` são **sempre falsos**.

## Compatibilidade entre Ciclos 08, 09 e 10

A `CompatibilityMatrix` faz um teste **local de versão e schema declarados** dos quatro arquivos públicos:

1. `governance/review-packet.v1.json` (Ciclo 08);
2. `examples/restricted-review-threat-fixture.v1.json` (Ciclo 09);
3. `examples/integration-fixture.v1.json` (Ciclo 10);
4. `governance/integration-policy.v1.json` (Ciclo 10).

Um arquivo ausente, esquema ou versão divergente, entrada duplicada ou referência a caminho fora da lista provoca rejeição. O relatório registra SHA-256 dos **bytes públicos realmente lidos** para reprodutibilidade local, porém isso não autentica uma assinatura de especialista, não prova segurança do código e não autoriza migração para o ambiente privado.

Uma mudança futura de contrato ou dado exigirá versão de migração própria e revisão do modelo de confiança. Não existe mecanismo que aprove automaticamente a compatibilidade de dados e direitos de uso.

## Eventos que reabrem qualificação

O `ChangeImpact` descreve **cinco gatilhos obrigatórios**, cada um com relações explícitas de invalidação:

- **Nova revisão da afirmação:** refazer vínculo com evidência, pareceres, auditoria e autorização.
- **Nova revisão da publicação OEM:** reavaliar efetividade, pareceres e autorização.
- **Mudança na configuração do equipamento:** reavaliar efetividade, pareceres e autorização.
- **Revogação de identidade:** suspender validade de identidade, segregação, pareceres e autorização.
- **Mudança de qualificação:** revalidar competência, pareceres e autorização.

No protótipo não há aprovações reais para revogar. O modelo apenas testa que, **se** esses eventos ocorressem em um serviço privado autorizado, o estado anterior deixaria de ser válido e seria obrigatória nova revisão. Nenhum evento de exemplo contém CPF, matrícula, série de máquina, laudo, token ou documento licenciado.

## Contratos entregues

Foram adicionados seis JSON Schemas: `DeploymentControl`, `ControlEvidence`, `AcceptanceDecision`, `CompatibilityMatrix`, `ChangeImpact` e envelope `DeploymentReadinessFixture`.

O validador implementa controles relacionais adicionais aos JSON Schemas: identifica duplicações de controles ou evidências, exige ligação unívoca, detecta dependências órfãs/ciclos, garante dez IDs de prova definidos pela política e preserva os cinco gatilhos de mudança com seus escopos obrigatórios.

Os estados `independently_verified` e `revoked` são reconhecidos no vocabulário, mas **rejeitados como entradas públicas**, por não existir autoridade para attestá-los. Mesmo um comprovante fictício com hash preenchido não eleva o estado de um controle.

## Executar localmente

```bash
python -m unittest discover -s tests -v

python -m governance.deployment_readiness \
  --fixture governance/deployment-readiness.v1.json \
  --policy governance/integration-policy.v1.json \
  --output build/readiness/deployment-readiness.v1.report.json
```

O pipeline gera um relatório de prontidão sintética, confere as referências públicas dos Ciclos 08–10 e rejeita, como testes negativos, um controle falsamente marcado `independently_verified` e uma migração com versão de contrato inventada.

## Requisitos para avaliação real em ambiente privado

Antes da implantação, um grupo autorizado deverá estabelecer identidade e competência verificadas no backend, documentos de efetividade com direito de acesso, auditoria externa protegida, política de conflito de interesses, retenção/privacidade e aprovação distinta de operação. As equipes de **Engenharia, TI/Segurança, Privacidade/Jurídico e Gestão Documental** precisam aprovar os seus respectivos critérios. Identidades, evidências e aceites reais não pertencem ao repositório público.

**Próximo ciclo sugerido:** planejamento de uma interface de revisão de prontidão para humanos, com trilha de critérios e pendências, sem servir como portal real de autenticação ou transporte de documentos corporativos.

O principal ganho deste ciclo é tornar visível a diferença entre um contrato tecnicamente consistente e uma plataforma realmente apta à operação corporativa. O primeiro é testável neste repositório; o segundo depende de infraestrutura e evidência externa ainda inexistentes.
