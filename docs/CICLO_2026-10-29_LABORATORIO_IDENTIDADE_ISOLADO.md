# Ciclo 40 — Homologação isolada de identidade e autorização, sem sistemas reais

**P&D v4.0.0 · 29/10/2026.** Continuidade do Ciclo 39. Esta implementação não cria um IdP corporativo nem testa OIDC com um provedor homologado. Ela oferece um simulador com decisões efetivamente executadas sobre recursos exclusivamente sintéticos para testar a semântica dos controles.

## Natureza do laboratório

O laboratório roda em um único processo Python, sem rede, sem arquivos privados, sem contas humanas, sem serviços de sessão compartilhados e sem conexão a SAP/ECM. A autenticação utiliza contas fictícias criadas em memória; a autorização só permite ações de laboratório sobre IDs de pacotes sintéticos. O token assinado é **formato proprietário e exclusivo para teste**, nunca um token de identidade ou acesso padronizado OIDC/OAuth 2.0. Não deve ser usado para autenticação de produção.

## Controles executáveis

| Controle | Implementação no laboratório | Limite |
| --- | --- | --- |
| Senha | Derivação PBKDF2-HMAC-SHA256 com salt aleatório por conta fictícia | Não é autenticação organizacional nem gestão de senhas de produção |
| Segundo fator | TOTP local baseado em HMAC, com prevenção de reutilização no mesmo período | Não há MFA institucional, fator de posse independente ou gestão externa de sementes |
| Sessão | Token de teste com HMAC-SHA256, emissor/audiência do laboratório, prazo de 900s, chave efêmera, revogação em memória | Não é OIDC/JWT, não funciona entre serviços e perde estado ao encerrar o processo |
| Papéis | Autor, custodiante, revisores A/B e adjudicador com ações específicas | Perfis artificiais; não comprova qualificação ou independência de duas pessoas |
| Recurso atribuído | ID de pacote da matriz do Ciclo 37 com vinculação a usuário sintético | Não toca no documento original nem no armazenamento privado do Ciclo 38 |
| Execução | Consulta o verificador de sessão e a autorização antes de toda ação no recurso artificial | Não existe backend corporativo ou API HTTP protegida |
| Auditoria | Resumo de resultados em memória, sem segredos ou pessoas | Não é custódia externa, trilha WORM nem log transacional |

## Cenários de ensaio

O dataset descreve 12 solicitações: 6 elegíveis para uma operação **dentro do sandbox** (leitura pública sintética, ações de custodiante, pareceres de revisores e rascunho de adjudicação) e 6 recusadas (autor acessando caso privado, revisor tentando adjudicar, adjudicador fazendo parecer de revisor, pacote não atribuído e ações relacionadas a ordens e liberação de equipamento). Os testes adversariais adicionais verificam credencial inválida, senha incorreta, MFA ausente ou repetido, expiração, revogação, alteração do MAC, tentativa de alterar papel, acesso entre pacotes, conflito de função e fonte adulterada.

**Atenção:** `sandboxResourceActionAllowed=true` quer dizer que uma **operação sobre um recurso sintético** foi permitida pelo laboratório; não significa `authorizationGranted` real. Os relatórios expõem separadamente `realResourcePermissionsGranted=0`, `realUsersAuthenticated=0`, `realPrivateDocumentsAccessed=0` e `realOperationalActions=0`.

## Referências técnicas e escopo

- [RFC 6238 — TOTP](https://www.rfc-editor.org/rfc/rfc6238.html): algoritmo de senha de uso único baseada em tempo; usado somente com sementes fictícias.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): deny by default e verificação em toda requisição.
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html): descreve um fluxo de autenticação federada real, **não implementado neste ciclo**.

## Comandos

```bash
python -m unittest tests.test_isolated_identity_lab -v
python -m governance.isolated_identity_lab \
  --output build/benchmarks/cycle40-isolated-identity-lab.json
```

Os testes criam segredos efêmeros em memória e não armazenam senhas, TOTP, tokens ou dados de identidade no JSON final. Os quatro contratos JSON Schema definem política, cenário, resultado individual e relatório.

## Limites e decisão

**A aprovação dos testes não certifica um sistema de identidade.** O laboratório de autenticação em memória não implementa flow de Authorization Code + PKCE, JWKS, assinatura assimétrica, OAuth, autenticação corporativa, vínculo de permissões a diretório, políticas ABAC ou revogação distribuída. Também não realiza autenticação do profissional de engenharia nem homologação diagnóstica.

Próximo ciclo deve analisar integração com **IdP de homologação real** e backend de recursos sintéticos, após escolha de fornecedor, contratos de segurança, isolamento de rede e aprovação institucional. Nenhuma integração deverá ocorrer por meio de tokens de produção ou documentos OEM confidenciais.

**Decisão:** `no_go_synthetic_lab_only_external_idp_and_acl_not_integrated`.
