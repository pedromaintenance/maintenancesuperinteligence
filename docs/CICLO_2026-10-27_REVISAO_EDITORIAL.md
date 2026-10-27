# Ciclo 18 — Protocolo de revisão editorial fictícia

**Versão P&D:** 1.8.0 · **Data:** 27/10/2026 · **Issue:** #36.

## Objetivo

Modelar como quatro rascunhos sintéticos de notificações de manutenção transitariam por atribuição de revisores, divergência, correções documentais, reabertura por alteração de contexto e revogação de perfil. Não simular nenhuma revisão profissional autêntica, homologação OEM ou autorização operacional.

Todas as identidades começam por SIM-, são fictícias, não têm credenciais ou assinaturas verificadas e não correspondem a trabalhadores da mina. A biblioteca não acessa SAP PM, ECM, telemetria ou laudos corporativos.

## Casos implementados

| Documento | Cenário sintético | Resultado |
| --- | --- | --- |
| SIM-NOTE-001 (óleo do comando final) | Dois perfis independentes por ID apontam correções de escopo na revisão 1 | requires_revision |
| SIM-NOTE-002 (hidráulica) | Dois pareceres editoriais divergem e adjudicador preserva a divergência | unresolved_disagreement |
| SIM-NOTE-003 (DTC armazenado) | Correção sintética de texto cria revisão 2, mudança hipotética da efetividade OEM reabre revisão 3; pareceres de revisão 1 tornam-se obsoletos | pending_real_review |
| SIM-NOTE-004 (DTC ativo) | Dois perfis sugerem completude editorial, mas o custodiante fictício revoga um perfil; não há aprovação real | pending_real_review |

São quatro casos, **14 personas fictícias e 16 eventos**. Nenhuma revisão real, alteração física, coleta ou ordem de manutenção ocorreu.

## Segregação de funções

Os papéis são autor, revisor, adjudicador e custodiante, com permissões não intercambiáveis. O autor submete, corrige ou reabre a revisão. O revisor pode registrar uma única opinião editorial por versão vigente, somente na disciplina declarada correspondente (lubrificação, hidráulica ou eletrônica). O adjudicador pode preservar conflito, nunca produzir aprovação real. O custodiante somente revoga um perfil fictício.

A validação recusa autoavaliação do autor, dois perfis com a mesma chave de persona, revisor de disciplina diferente, registro em revisão obsoleta, nonce/evento duplicado, papel impróprio, assinatura preenchida, falsa certificação e evento de liberação operacional. Mesmo duas opiniões de completude fictícias **não** constituem autenticação de dois revisores reais.

## Revisões e auditoria

Cada revisão gera um digest SHA-256 sobre a base sintética, identificador de revisão, motivo e digest anterior. Eventos encadeiam digest precedente, conteúdo do evento e revisão vigente. O verificador recompõe todos os estados e hashes a partir do fixture canônico.

**Atenção:** as revisões são eventos lógicos de treinamento: não é editado nenhum texto real do rascunho. O histórico não é uma auditoria imutável externa; não há assinatura digital, chave privada, carimbo temporal confiável nem verificação de identidade.

Qualquer mudança hipotética de sintoma, arranjo, referência OEM ou conteúdo exige nova revisão e invalida avaliações anteriores. Perfis revogados continuam registrados no histórico, mas seus pareceres não contam como vigentes.

## Limites de aceitação

Treze bloqueios permanecem falsos: identidade e competência, independência, revisão humana autêntica da versão vigente, efetividade OEM por série, evidência física, âncora externa de auditoria, método seguro, abertura de nota/ordem SAP, compra de materiais, alteração ECM ou liberação do equipamento.

O cenário de divergência conserva a discordância. Nenhuma saída recebe estado de aprovado por especialista. A rubrica do Ciclo 17 continua sendo somente um controle de completude documental dos exemplos fictícios, não uma medida de acurácia, confiabilidade interavaliadores, competência real ou validade mecânica.

## Arquivos e testes

O fixture está em editorial/review-fixture.v1.json; o motor e gerador de HTML offline em editorial/review_protocol.py. Há doze contratos JSON Schema em contracts/editorial-*, cobrindo atribuição, competência, evento, revisão, opinião, adjudicação, auditoria, lacunas, fronteira de aceite, fixture, caso e relatório.

Os testes adversariais rejeitam dupla identidade, falso papel ou competência, assinatura ou aprovação fabricada, conflito apagado, revisão obsoleta, salto de revisão, nonce repetido, falso custodiante, alteração de digest e permissão SAP/ECM/liberação.

O GitHub Actions reconstrói a base FMEA pública pinada e os artefatos dos Ciclos 13–17 antes de gerar os relatórios JSON e HTML, exclusivamente fictícios.

## Execução

Executar primeiro o fluxo documentado dos Ciclos 13–17 para gerar os arquivos de entrada; depois:

    python -m editorial.review_protocol --snapshot build/fmea-public/fmea-public.snapshot.json --quality build/quality/notification-quality.v1.json --drafts build/notifications/maintenance-drafts.v1.json --output build/editorial/review-protocol.v1.json --html build/editorial/review-protocol.v1.html

Os artefatos podem ser lidos offline. Nenhum formulário, JavaScript ou integração corporativa está presente.

## Próxima investigação

Desenhar um protocolo de aceite externo de uma futura revisão profissional independente em ambiente privado aprovado por TI, Jurídico, Segurança da Informação e Engenharia. Um piloto real exige credenciais, competência, critérios de efetividade OEM, políticas de retenção e segregação de dados, aprovação formal, segurança e autorização operacional externas. O repositório público não concede essa aprovação.
