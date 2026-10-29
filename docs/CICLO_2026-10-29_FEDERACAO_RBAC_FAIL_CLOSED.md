# Ciclo 39 — Arquitetura de identidade federada e autorização RBAC (fail-closed)

**P&D v3.9.0 · 29/10/2026.** Preparação de controles para utilização futura de um provedor de identidade (IdP) confiável, sem transformar afirmações sintéticas em autenticação ou acesso real.

## Resultado entregue

O ciclo implementa um **pré-avaliador educativo**: associa cinco perfis artificiais a permissões hipotéticas e exerce **30 solicitações simuladas** contra o registro congelado de 36 pacotes de revisão técnica. Mesmo nas solicitações com papel e formato de declaração compatíveis, o resultado de autorização **permanece negado**, pois não existe um IdP corporativo conectado, validação criptográfica da assinatura, diretório de papéis corporativos, ACL efetiva ou sessão autenticada. Nenhum arquivo da custódia do Ciclo 38 é aberto.

## Referenciais de arquitetura

- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html): sem validação de assinatura JWT, issuer `iss`, audience `aud`, validade, nonce e outros controles em um provedor realmente registrado, um conjunto de *claims* JSON não prova autenticação. Este projeto **não aceita nem verifica ID Tokens reais**.
- [NIST SP 800-63-4](https://csrc.nist.gov/pubs/sp/800/63/4/final): prova de identidade, autenticação e federação são funções relacionadas mas distintas; a ferramenta não implementa os requisitos de um serviço certificado.
- [NIST SP 800-63C-4](https://csrc.nist.gov/pubs/sp/800/63/c/4/final): uma federação exige relação de confiança entre provedores e partes confiantes; a `syntheticIssuer` de testes não possui essa relação.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): priorizar default deny, privilégio mínimo e verificação a cada requisição.

## Modelo de segurança

| Papel proposto | Ações hipoteticamente elegíveis | Limite |
| --- | --- | --- |
| Autor | Ler metadados públicos de pesquisa | Não consultar casos privados nem aprovar suas próprias relações |
| Custodiante | Ler índice de documentos privados e preparar pacote | Não julgar uma hipótese, nem executar manutenção |
| Revisor A | Ler caso privado atribuído e submeter parecer técnico | Não pode adjudicar o próprio parecer |
| Revisor B | Ler caso privado atribuído e submeter parecer técnico | Deve ser pessoa distinta de A, verificada externamente |
| Adjudicador | Ler caso atribuído e submeter decisão de adjudicação | Não é revisão independente A/B nem autoridade de liberação |

**Nenhuma dessas ações privadas é efetivamente executada pelo módulo.** São apenas direitos propostos, que precisariam ser concedidos por um serviço de autorização após autenticação/competência/independência verificadas e escopo de recurso definido.

## Cenários adversariais

O dataset em `governance/federation-rbac-rehearsal.v1.json` testa emissor incorreto, audiência errada, claims expiradas e futuras, nonce incompatível, token-replay representado por jti repetido, declaração falsa de papel, identidade de sujeito divergente, `alg=none`, ausência de MFA simulada, atributos malformados, vida útil excessiva, autodeclaração de assinatura verificada, ID de pacote desconhecido, ações fora do papel e tentativas de alterar a taxonomia ou liberar equipamento.

**Distinção central:** `hypotheticalRoleAndShapeEligible=true` significa somente que o cenário artificial respeitou requisitos editoriais de formato/perfil. Não representa token real, sessão ativa, verificação de assinatura, autenticação pessoal, permissão real, aptidão do profissional ou conformidade com OIDC/NIST.

## Gates para integração futura

1. Contratar/aprovar um IdP institucional e registrar client_id, emissor, audience, JWKS e algoritmos de assinatura permitidos; selecionar uma biblioteca de validação confiável, sem criar validador criptográfico caseiro.
2. Operar fluxo OIDC adequado ao cliente/aplicação, preferencialmente Authorization Code + PKCE, validando de fato assinatura, issuer, audience, exp, nonce e regras aplicáveis antes de criar uma sessão.
3. Integrar diretório de funcionários, vínculo profissional, gestão de competências, revogação, MFA e verificação de conflitos de interesse em serviço privado institucional.
4. Implementar autorização **no backend e por recurso** com papel, identidade, caso atribuído, finalidade, classificação documental, expiração, consentimento e log de auditoria imutável externamente.
5. Segregar autor/revisor A/revisor B/adjudicador com IDs organizacionais realmente distintos; criar fluxo de revogação e reabertura de decisões.
6. Testar em ambiente de homologação isolado, com credenciais fictícias emitidas pelo IdP de testes, inspeção de logs e provas de negação por padrão e menor privilégio.

## Entregáveis

- `governance/federation-rbac-policy.v1.json`: contrato declarativo sem fornecedor corporativo assumido, permissões hipotéticas e negações.
- `governance/federation-rbac-rehearsal.v1.json`: 30 casos de claims fictícias, cinco perfis e identidades simuladas.
- `governance/federation_rbac.py`: avaliação didática de forma e escopo, detecção de violações, relatório de negação permanente e HTML offline.
- `contracts/federation-rbac-{policy,rehearsal,preflight-result,report}.schema.json`: quatro contratos.
- `tests/test_federation_rbac.py`: testes adversariais e regressivos contra claims forjadas e alegações de acesso.

```bash
python -m unittest tests.test_federation_rbac -v
python -m governance.federation_rbac \
  --output build/benchmarks/cycle39-rbac-preflight.json \
  --html build/benchmarks/cycle39-rbac-preflight.html
```

## Limites explícitos

Não há OIDC login, API de IdP, JWK, login SSO, JWKS atualizado, sessão, MFA real, token bearer, prova de identidade, verificação de competência, autorização a objeto, política RBAC aplicada por serviço, conexão a SAP/ECM ou emissão de permissão para manutenção. Os campos `signatureValidated`, `issuerTrusted` e `roleAssignmentVerified` dos testes são **dados controlados fictícios**, jamais verificação criptográfica real.

**Decisão:** `no_go_connect_verified_oidc_idp_and_real_access_enforcement`, com **0 usuários autenticados, 0 documentos privados acessados e 0 autorizações reais concedidas**. A fase seguinte depende de infraestrutura externa, decisão institucional e revisão de segurança.
