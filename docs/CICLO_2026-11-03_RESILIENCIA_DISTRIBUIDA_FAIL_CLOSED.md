# Ciclo 42 — Resiliência distribuída e negação segura sob falhas

**P&D v4.2.0 · 03/11/2026.** Laboratório HTTP sintético sobre os processos de identidade e recursos do Ciclo 41. Objetivo: testar que falhas de infraestrutura e condições de corrida não promovam indevidamente uma autorização.

## Escopo e premissas

O exercício utiliza apenas `127.0.0.1`, identidades fictícias geradas durante a execução e IDs públicos de casos artificiais. Os testes são conduzidos entre **processos Python independentes** que compartilham, apenas durante o ensaio, uma chave efêmera para a introspecção. Não existe conexão com OIDC, IdP empresarial, documentos privados, SAP/ECM ou equipamentos; não é teste de resiliência de infraestrutura corporativa real.

Os endpoints de laboratório `/lab-fault-next-introspection` e `/lab-rotate-service-key` só funcionam quando o harness cria os processos explicitamente com `LAB_FAULTS_ENABLED=1`. Fora dessa modalidade, devem retornar HTTP 404. Dentro do sandbox, só aceitam operações sensíveis com a chave temporária de serviço. **Não reutilizar esses endpoints ou a lógica de sessões em produção.**

## 15 salvaguardas verificáveis

| Grupo | Condição injetada | Resultado exigido |
| --- | --- | --- |
| 1 | Injeção/rotação desativadas no Ciclo 41 normal | HTTP 404 |
| 2 | Controle de falha sem chave ou chave errada | HTTP 403 |
| 3 | Resposta de introspecção `active: true` sem atributos obrigatórios | HTTP 403, nunca concessão |
| 4 | Introspecção responde HTTP 503 | HTTP 403 no recurso |
| 5 | Introspecção mais lenta que timeout configurado | Negação no recurso, sem fallback |
| 6 | Chave rotacionada no serviço de identidade, recurso ainda na antiga | Negação durante dessincronização |
| 7 | Mesma chave nova instalada nos dois processos | Recuperação somente de acesso sintético |
| 8 | Chave antiga após rotação | Introspecção rejeita a chave anterior |
| 9 | 16 acessos simultâneos a pacote não atribuído | 16 recusas |
| 10 | 16 requisições simultâneas de ação operacional proibida | 16 recusas |
| 11 | 16 requisições concorrentes a uma revogação | Apenas respostas sintéticas válidas/recusas, sem erro que autorize sistemas reais |
| 12 | 16 requisições novas **após confirmação da revogação** | 16 recusas |
| 13 | Processo de identidade encerrado, API de recursos ativa | Negação segura |
| 14 | Nova solicitação após a queda, com sessão anteriormente válida | Negação repetida; sem cache de autorização |
| 15 | Validade expira durante a introspecção, antes da verificação no serviço de identidade | Negação segura |

## Mudanças de engenharia

**Contrato de introspecção estrito:** o serviço de recursos exige status 200, `active` estritamente booleano `true`, identidade sintética, role, lista de atribuições e as marcações explícitas `realIdentityVerified=false` e `realOIDCAuthenticated=false`. Uma resposta incompleta ou divergente nunca concede acesso.

**Tratamento de transporte:** conexões interrompidas, timeout, erro HTTP, resposta inválida ou JSON malformado resultam em negação, sem reutilizar uma decisão anterior. Há proteção contra respostas tardias após o cliente encerrar a conexão.

**Sincronização local de estado:** identidade, MFA, revogação, atualização de relógio e introspecção utilizam exclusão mútua no processo de identidade durante operações críticas. Isso fornece um ponto de consistência *local*, não uma transação distribuída com a API de recursos.

**Rotação de chave:** o ensaio troca o segredo primeiro em um processo, confirma a negação durante a divergência e depois atualiza o outro. A chave antiga é recusada após a rotação. Essa é uma experiência de falha segura, **não** um mecanismo de rotação tolerante a falhas ou gestão de segredos de produção.

## Limite de revogação concorrente

Uma requisição pode ser introspectada como ativa **antes** da confirmação de revogação e receber resposta da API depois dela. Isso não demonstra falha de software quando as verificações têm pontos de linearização diferentes: uma promessa de negação instantânea para toda operação já iniciada exigiria outro protocolo, tokens vinculados a versões, cancelamento de operações em andamento ou coordenação transacional.

O critério efetivamente testado é mais preciso: **depois que o serviço de identidade confirma a revogação, todas as 16 novas requisições do lote são negadas**. Os 16 pedidos deliberadamente concorrentes à revogação podem receber autorização sintética ou negação conforme a ordem da verificação. O relatório **não afirma linearizabilidade global**, nem registra uma taxa inventada de sucesso das corridas.

## Procedimento reprodutível

```bash
python -m unittest tests.test_distributed_resilience -v
python -m governance.distributed_resilience \
  --output build/benchmarks/cycle42-distributed-resilience.json
```

O programa inicia e encerra os subprocessos em context managers. Chaves, senhas, OTPs, tokens, PID e endereços de portas efêmeras não são colocados no relatório. O relatório declara 15 guardas, 16 negações de acesso cruzado, 16 negações operacionais, 16 requisições na corrida com resultados restritos e 16 negações posteriores à confirmação de revogação.

## Artefatos versionados

- `governance/distributed_resilience.py`: execução, injeção, concorrência e relatório sem segredos.
- `governance/distributed-resilience-policy.v1.json`: regras de negação, limites do sandbox e proibições de autoridade.
- `governance/distributed-resilience-fixture.v1.json`: nomes e parâmetros dos 15 guardas e da base artificial.
- `governance/loopback_http_services.py`: introspecção endurecida, sincronização de estado e controles de falha desabilitados por padrão.
- `governance/loopback_service_harness.py`: execução opcional com fault injection e objetos de processo apenas no harness privado.
- `contracts/distributed-resilience-{policy,fixture,guard,report}.schema.json`: quatro contratos JSON Schema.
- `tests/test_distributed_resilience.py`: suíte adversarial e regressiva integrada ao GitHub Actions.

## Riscos não resolvidos e evolução

O laboratório não tem autenticação mútua de serviço por TLS/mTLS, gestão corporativa de segredos, identidade de workload, revogação distribuída, tracing completo, controle de carga, autorizações com TTL independente, circuit breaker de produção, idempotência de operações ou garantias de linearizabilidade global. A possibilidade de observar um grant de laboratório de uma solicitação iniciada antes da revogação **não foi eliminada**.

Antes de homologar qualquer serviço real, é necessário definir o contrato de negação, a semântica temporal de revogação, controles de cancelamento em trânsito, arquitetura de segredos e identidade, monitoramento de timeout/latência e isolamento/risco operacional com a organização e a engenharia responsável.

**Decisão:** `no_go_fault_tolerant_synthetic_loopback_not_enterprise_authorization`: zero identidades reais verificadas, zero documentos privados acessados, zero permissões corporativas e zero intervenções autorizadas.
