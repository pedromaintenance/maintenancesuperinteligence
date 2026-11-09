# Ciclo 65 — Trilha sintética de revisão, contestação e propostas de adjudicação

**08/11/2026 · P&D · proposta empilhada sobre C64 · NO GO**

## Problema e objetivo
O C64 identifica, em fontes **inteiramente inventadas**, possíveis conflitos de rótulos entre linhagens documentais ativas. Ainda não existe no incremento um registro estrutural de como tais divergências seriam examinadas por duas pessoas, contestadas e encaminhadas para um terceiro parecer. O C65 implementa um **ensaio offline do fluxo**, sem alegar que revisores humanos, especialistas externos ou órgãos autorizados tenham participado.

## Artefatos
- `benchmarks/cycle65_review_ledger.py` — validador determinístico; primeiro executa o portão C64, deriva referências com conflitos em aberto e aceita um log de até 60 eventos simulados.
- `tests/test_cycle65_review_ledger.py` — 23 métodos positivos e adversariais sobre integridade, papéis, contestações, proposta e negação de autoridade.
- `.github/workflows/cycle65-review-ledger.yml` — regressão Python offline de C58 a C65.
- Este documento — alcance, papéis, ameaças, critérios de revisão e próximos requisitos.

## Protocolo simulado
Cada evento usa apenas tokens públicos `SIM-` e registra `eventId`, `referenceId`, `eventType`, `actorRole`, `actorAlias`, `position`, `selectedClaimToken`, `targetEventId`, `requiredEvidence`, `previousDigest`, `digest`. Não inclui nome, email, credencial, número de equipamento, parecer livre ou texto OEM.

| Evento | Papel aceito | Condição |
|---|---|---|
| `assessment` | `reviewer_a` ou `reviewer_b` | Uma proposta de interpretação por papel, para referência que permanece em conflito |
| `challenge` | Um dos revisores | Só pode contestar avaliação **prévia** do outro papel, após registrar a própria avaliação |
| `adjudication_proposal` | `arbiter` | Requer as duas avaliações anteriores e um terceiro alias distinto; nunca fecha o conflito |

Uma posição pode preferir um token de fonte **ativa fictícia** ou declarar `insufficient_evidence`. Toda entrada também indica qual classe de evidência está faltando: autenticidade da fonte, escopo de revisão, efetividade de configuração ou revisão técnica independente. Isso é identificação de lacuna documental, não execução de teste nem comprovação física.

## Integridade da trilha
O primeiro `previousDigest` é SHA-256 do JSON canônico do **caso de origem C64 integral**. Cada evento posterior aponta para o digest do evento anterior. O digest de cada evento é calculado sobre seus campos, incluindo o vínculo ao anterior e excluindo apenas o próprio `digest`. Os campos e a sequência são verificados na leitura.

**Limite criptográfico decisivo:** uma pessoa que controle o arquivo inteiro pode reescrever o caso e recalcular a cadeia. Hashes não provam autoria, independência, data/hora confiável, aprovação técnica nem retenção imutável. Para custódia verdadeira, seria necessário âncora externa confiável, assinatura com identidade verificada, armazenamento protegido, política de retenção e revisão institucional. O ensaio **não** fornece isso.

## Resposta e bloqueios
O resultado permite estados apenas descritivos: `not_reviewed`, avaliação sintética de um/dois papéis, contestação sintética, proposta sintética. Sempre inclui:
- `conflictResolved=false` em cada trilha;
- `realHumanReviewCompleted=false`;
- `independentExpertReviewCompleted=false`;
- `technicalConflictResolved=false`;
- `oemEffectivityVerified=false`;
- `operationalAuthorityGranted=false`;
- `decision=NO GO`.

O módulo rejeita alegações de identidade validada, revisão efetiva, autoridade operacional, alteração SAP/ECM, execução de testes e liberação de equipamento. Mesmo dois pareceres concordantes mais uma proposta do terceiro personagem não geram aprovação.

## Reproduzir
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics tests.test_cycle63_effectivity tests.test_cycle64_source_governance tests.test_cycle65_review_ledger -v
python -m benchmarks.cycle65_review_ledger --input /tmp/conflito-ficticio.json --output /tmp/recibo-c65-novo.json
```
Funções `fixture()`, `append_event()` e `two_assessments()` no teste produzem registros fictícios sem backend nem dados privados.

## Critérios para eventual pesquisa com pessoas reais
1. Identificar legalmente revisores, competência, conflito de interesse, independência e autorização institucional **fora do repositório público**.
2. Adotar custódia separada e autorização de uso para fontes e casos inéditos; não publicar séries, laudos, contratos ou manuais OEM licenciados.
3. Congelar pré-registro de critérios, pareceres e evidências, com contestação e terceiro parecer que possam ser auditados por autoridade externa.
4. Separar `proposta de adjudicação`, `adjudicação efetiva`, `aprovação de referência` e `autorização operacional`; nenhuma transição automática entre elas.
5. Executar estudo de revisão independente em ambiente privado autorizado, com evidência real e adequação metrológica/OEM; só então considerar métricas mecânicas.

**Próximo ciclo sugerido:** C66 — protocolo de aceitação de estudos independentes e revisão dos limites de arquitetura, **não** mais um simulado de aprovação. Pode incluir matrizes de qualidade de evidência e critérios verificáveis de não progressão.

**Estado: NO GO para diagnósticos homologados, intervenção física, ordens de serviço, SAP, ECM e liberação de máquinas.**
