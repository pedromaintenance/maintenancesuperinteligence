# Ciclo 16 — Rascunhos didáticos de notificações de manutenção

**Data:** 24/10/2026. **Versão P&D:** 1.6.0. **Issue:** [#32](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/32).

## Objetivo e resultado

Transformar os quatro dossiês e árvores de investigação do Ciclo 15 em **documentação técnica preparatória** para treinamento de mecânicos, eletricistas, inspetores e planejadores. A saída demonstra a estrutura lógica de uma notificação de manutenção: sintoma, função e requisito, efeitos potenciais, hipóteses abertas, escopo delimitado, evidência ainda necessária, risco de postergação e critérios de revisão.

**Nada neste módulo é uma nota SAP PM verdadeira.** Todos os IDs são `SIM-NOTE-00x`; não existe interface de importação, integração com sistemas de produção, chamada SAP, registro de equipamento real, autenticação corporativa ou autorização de intervenção.

## Rascunhos integrados

| Rascunho fictício | Disciplina | Sintoma do exercício | Escopo de investigação |
| --- | --- | --- | --- |
| SIM-NOTE-001 | Mecânica / Lubrificação | Perfil de aditivos isoladamente diferente no comando final CAT 777E | Identificar produto, histórico e amostra antes de interpretar alteração e propor inspeção |
| SIM-NOTE-002 | Mecânica / Hidráulica | Atuação lenta e contexto de carga contraditório | Conciliar carga, configuração e documentação aplicável do circuito |
| SIM-NOTE-003 | Elétrica / Eletrônica | Código genérico armazenado, sem comprovação de atividade | Reconstruir contexto de registro e comparar evidência física apenas após revisão |
| SIM-NOTE-004 | Elétrica / Eletrônica | Código genérico considerado ativo somente no cenário fictício | Distinguir histórico, tempo de ocorrência, configuração e leitura independente |

Não existem números de equipamento corporativo, série, laudos SOS, registros ECM, OS SAP ou medições de campo. O nome da família CAT 777E é usado somente como referência educacional pública, sem validar arranjo ou efetividade por série.

## Critérios estruturais

**MaintenanceSymptom** — traz o relato do exercício e o requisito funcional, com a origem marcada como `fictional_report_not_field_measurement`. Relato não é medição.

**HypothesisRegister** — conserva todas as hipóteses como `open_not_confirmed`; nenhuma probabilidade, culpabilidade de componente ou descarte são atribuídos. Descrição de possível mecanismo não é causa raiz.

**InspectionScope** — indica atividade `plan_human_investigation_only`, texto deliberadamente não operacional, nó original da árvore, métodos e fontes públicas do catálogo. Métodos permanecem `not_performed` e sujeitos a procedimento OEM e segurança.

**PlanningConstraint** — define disciplina, mas mantém `workHours=null`, `materials=[]`, `cost=null`, `numericPriority=null`, `oemPressureOrWearLimits=null`, `executionProcedures=[]`, serial e números SAP nulos. A intervenção não foi dimensionada com base em dados reais.

**PostponementRisk** — registra o risco qualitativo **editorial** de adiar a investigação, não um risco residual calculado no campo. Não autoriza continuar operando.

**NotificationDraft** — agrega todos os objetos e gates com a identificação obrigatória `SIMULAÇÃO EDUCACIONAL — NÃO É NOTA OU ORDEM SAP`. Nenhuma saída pode ser convertida diretamente pelo projeto em ordem, nota, compra de peça, alteração ECM ou liberação.

## Causalidade e abstenção

A origem dos rascunhos é exclusivamente `casefiles/integrated.py`, que verificou, anteriormente, o snapshot público FMEA pinado, métodos, matriz discriminante, oráculo sintético e prontidão restrita bloqueada. O gerador `notifications/drafts.py` verifica correspondência exata dos quatro casos e dos quatro elementos da coleção `investigationTrees`, incluindo:

- raiz editorial realmente selecionada, respectivo par de hipóteses e métodos de referência;
- estado de contexto `not_measured`, `contradicted` ou `inconclusive`;
- decisão `abstain_pending_verified_evidence`, sem ramo hipotético tratado como observado;
- hipóteses mantidas abertas, nenhuma causa raiz confirmada, ensaio executado ou intervenção autorizada;
- gate OEM/revisão humana pendente e documentação de segurança ainda não aplicável a uma máquina real.

Números SHA-256 dos artefatos sintéticos proporcionam **integridade comparativa de software**, não certificação de fonte real nem assinatura técnica.

## O que um planejador pode aprender

O rascunho demonstra como se descreve **o problema a verificar**, e não como se condena um componente ou se redige antecipadamente uma ordem de substituição. A disciplina é informada, mas materiais, ferramentas, HH, sequência física, disponibilidade de equipamento, acesso e programação dependem de levantamento validado no contexto próprio. Um bom texto técnico separa a hipótese de falha da atividade de inspeção necessária para confirmá-la.

**Exemplo de distinção didática:** uma mudança de perfil químico em óleo não é evidência suficiente de dano a um comando final; pode justificar a revisão de formulação, identificação do produto, coleta e tendência antes de decidir a tratativa. O exemplo não substitui a revisão de laudo por engenheiro e laboratório nem autoriza ignorar outros indicadores de risco.

## Implementação, contratos e testes

- `notifications/training-spec.v1.json`: quatro cenários e textos editoriais fictícios, sem dado de máquina real.
- `notifications/drafts.py`: motor de validação, rastreabilidade, montagem, exportação offline JSON/HTML e rejeição de autorização.
- Oito contratos JSON Schema: `MaintenanceSymptom`, `InspectionScope`, `HypothesisRegister`, `PlanningConstraint`, `PostponementRisk`, `NotificationDraft`, `NotificationTrainingSpec` e `NotificationTrainingCollection`.
- `tests/test_notification_drafts.py`: cenários adversariais para campos corporativos, procedimento invasivo, número SAP, materiais inventados, HH, risco quantificado, alteração de papel, confirmação de causa, falsa observação de campo, alteração de árvore e liberação.
- O CI executa o novo gerador com os quatro casos já verificados e disponibiliza JSON/HTML temporários. São utilizados apenas dados de treinamento, sem pesquisa de sistemas corporativos.

## Executar localmente

```bash
python -m unittest discover -s tests -v

python connectors/fmea_public.py --fetch --output build/fmea-public

python -m casefiles.integrated \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --output build/trees/technical-cases.v1.json

python -m notifications.drafts \
  --source build/trees/technical-cases.v1.json \
  --spec notifications/training-spec.v1.json \
  --output build/notifications/maintenance-drafts.v1.json \
  --html build/notifications/maintenance-drafts.v1.html
```

O HTML fica disponível localmente para leitura e impressão. Não há JavaScript, formulário, requisição externa, botão de envio para SAP ou exportação para um conector empresarial.

## Limites e próxima investigação

O sistema **não mede a qualidade real das notificações** nem a eficácia das atividades de manutenção. Ainda faltam validações independentes com especialistas, critérios específicos por máquina/série, métodos OEM autorizados, avaliação de riscos, controles de competência e infraestrutura privada. CI verde representa conformidade sintética com regras explícitas, não segurança operacional.

**Ciclo seguinte recomendado:** construir uma rubrica para avaliar a **qualidade documental e a completude de rascunhos** de notificação, distinguindo informações faltantes, ambiguidade, escopo invasivo sem autorização e separação de causa/efeito, sem promover as avaliações sintéticas a validação de campo.
