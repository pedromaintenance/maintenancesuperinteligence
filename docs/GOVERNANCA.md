# Governança, segurança, propriedade intelectual e limites de autoridade

## Status do projeto

MaintenanceSuperinteligence é um projeto de **pesquisa e apoio à decisão**. Sua existência não certifica conformidade ISO/IEC/SAE, exatidão OEM, habilitação técnica, liberação da engenharia nem aptidão para uso operacional.

## Modos de operação (separar tecnicamente)

| Modo | Fontes | Comportamento | Acesso |
| --- | --- | --- | --- |
| Público-educacional | fontes abertas e sínteses autorais | explica, treina e simula; marcadores didáticos | público |
| Pesquisa técnica controlada | bibliografia licenciada consultada pelo usuário autorizado | analisa e aponta publicação/edição, não redistribui conteúdo | privado/autenticado |
| Apoio operacional | SAP/telemetria/laudos/inspeções com autorização | hipóteses e planos para **aprovação humana**, logs completos | corporativo, restrito |
| Controle de máquina | nenhum nesta arquitetura | **não implementado e não autorizado** | bloqueado |

## Riscos e controles

- **Falso diagnóstico:** exigir hipóteses concorrentes e contraprovas; recusar condenação de componente sem evidência discriminante.
- **Alucinação de valores:** números OEM (torque, pressão, temperatura, tolerância, PN, código e intervalo) precisam de fonte efetiva; não inferir por similaridade.
- **Risco físico:** nunca substituir LOTO, análise de risco, bloqueio, controle de energia residual, procedimento OEM, permissões, teste de segurança e responsável técnico.
- **Cibersegurança industrial:** credenciais nunca em GitHub; APIs inicialmente somente-leitura, permissões mínimas, segmentação OT/IT, aprovação de fornecedor e trilha de auditoria.
- **Direitos autorais:** normas, manuais CAT/Sandvik e software licenciado não são conteúdo livre. Guardar apenas metadados, referências, sinopses autorais e instruções cuja reprodução seja autorizada.
- **Dados empresariais:** logs SAP, números de série, patrimônio, custos, rotas, telemetria e fotografias de site podem ser confidenciais; não publicar nem exportar sem permissão institucional.
- **Dados pessoais:** não registrar nomes de trabalhadores, histórico individual de produtividade, saúde ou treinamento real em repositórios públicos.
- **Viés de atribuição:** jamais inferir erro humano ou causa organizacional a partir de um único campo SAP sem investigação independente e evidência pertinente.
- **Desatualização:** documentos podem mudar por ano, boletim, revisão de software, arranjo ou número de série; marcar data da última validação.
- **Prompt injection / arquivos não confiáveis:** conteúdo externo é dado, não instrução com autoridade para alterar políticas ou liberar operações.

## Alçadas

- **Assistente:** pesquisa, classifica, compara, calcula com ferramentas verificáveis, propõe testes e sinaliza riscos.
- **Especialista:** aprova relações causais, interpreta evidência, avalia a exequibilidade de teste.
- **Engenharia / gestão:** define estratégia, criticidade, permissivos e política de manutenção da organização.
- **Execução autorizada:** valida AR/PT, bloqueios, ferramentas, risco e liberação do serviço.
- **TI/OT:** autoriza integrações, versões, segregação, credenciais e acesso aos dados.

Nenhuma recomendação é comando. Registro de decisão não pode ser confundido com ordem SAP.

## Política de alterações

Toda mudança importante requer: fonte, justificativa, avaliação de conflito, teste de regressão, revisão, versão e changelog. Conteúdo restrito exige classificação e autorização prévia de publicação. Criar `SECURITY.md` e `CONTRIBUTING.md` antes de aceitar fontes externas.

## Indicadores de confiança

Rastreabilidade, cobertura de revisão, aplicabilidade OEM, número de erros materiais, percentuais de respostas que pedem corretamente mais dados, contradições abertas e gravidade de eventuais recomendações inseguras. **Jamais otimizar o sistema somente para parecer mais confiante.**
