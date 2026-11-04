# Ciclo 45 — Comparação cega pareada e dissenso sem falsa homologação

**P&D v4.5.0 · 04/11/2026 · incremento de pesquisa empilhado sobre o Ciclo 44.**

> **Decisão: NO GO.** Nenhum parecer humano independente foi obtido, nenhum conhecimento OEM específico foi verificado, nenhuma identidade profissional foi autenticada e nenhuma recomendação operacional foi aprovada.

## 1. Problema de pesquisa e continuidade

O Ciclo 44 calcula, a partir de respostas **simbólicas inventadas**, quais pares de hipóteses uma pergunta poderia separar. Essa contagem estrutural não garante que a pergunta tenha real poder diagnóstico, seja segura, tenha boa relação esforço/benefício ou seja respondível no campo.

Os Ciclos 30–32 já estabelecem custódia privada externa ao checkout, HMAC, recibos de congelamento, splits train/dev/test e gate de qualidade antes de distribuir casos. O Ciclo 45 **reutiliza** os validadores desses ciclos e acrescenta um protocolo para comparar duas perguntas **no mesmo caso** sem expor ao avaliador a origem metodológica de cada uma.

O objetivo operacional futuro é responder, com revisores humanos qualificados, à pergunta: **qual das duas perguntas é mais relevante para diferenciar hipóteses concorrentes, considerando evidência, segurança e viabilidade?** O protótipo público mede apenas a consistência de um procedimento de pesquisa, não responde a essa pergunta.

## 2. Fluxo de custódia e alçadas

| Etapa | Responsável necessário | Implementação atual | Limite |
| --- | --- | --- | --- |
| Selecionar casos e fontes | Custodiante externo independente | Entrada JSON privada com contrato já usado no Ciclo 30 | Identidade, titularidade e origem não autenticadas |
| Validar independência de train/dev/test | Custodiante e auditor técnico | Gate privado do Ciclo 32 obrigatório | Metadados de linhagem são autodeclarados |
| Congelar duas perguntas candidatas | Autor do estudo, fora da área do revisor | Input privado por ID; textos e IDs de referência ocultados no pacote | Não valida semântica OEM nem neutralidade linguística |
| Distribuir ordem A/B | Custodiante | Sorteio criptográfico aproximadamente balanceado e mapa privado | Não substitui identidade, randomização institucional ou registro externo |
| Coletar dois julgamentos | Dois revisores independentes | JSON com aliases sintéticos, escolha A/B/empate/abstenção, justificativa e sinais de risco | Zero humanos identificados/verificados |
| Congelar julgamentos | Custodiante | Recibos de hash, sem sobrescrita | Hash não equivale a assinatura humana ou timestamp confiável |
| Reconciliar | Adjudicador técnico externo | Algoritmo identifica concordância e marca conflitos para adjudicação | Não inventa consenso, não adjudica tecnicamente |
| Analisar/relatar | Equipe científica | Contagens com denominador e estado NO GO | Não mede melhora diagnóstica de campo |

### Segurança informacional

Casos, candidatos, gabarito de origem das perguntas, chave, pacote para revisores, submissões e relatórios são mantidos **fora do checkout público**, em diretório privado sob responsabilidade do custodiante. O comando de pontuação exige reconstrução do pacote e comparação HMAC contra o mapa privado, além de reverificação do recibo de qualidade.

A randomização evita simplesmente apresentar o método experimental sempre em A. O sorteio não é uma garantia de cegamento perfeito: **vocabulário, tamanho, detalhe ou estilo das perguntas podem revelar a origem**. Um estudo real exige revisão de mascaramento e investigação sobre vazamento de método.

O segredo HMAC é local e apenas vincula conteúdos ao segredo guardado. Não prova que a pessoa que gerou os registros é quem afirma ser. Processos do mesmo usuário podem ler arquivos não protegidos pelo sistema; é necessário isolamento institucional externo para dados reais.

## 3. Implementação e contratos

`benchmarks/cycle45_blinded_pairwise.py` implementa:

- `validate_candidates`: candidatos por mesmo conjunto custodial de casos, IDs distintos e ausência de falsa autorização de teste;
- `balanced_assignment`: embaralha posições A/B mantendo diferença máxima de uma posição entre métodos num lote de 2–50 casos;
- `build_packet`: constrói pacote com contexto do caso e pergunta A/B, sem IDs dos candidatos ou indicação baseline/experimental;
- `prepare`: exige gate do Ciclo 32, gera pacote, mapa privado e recibo de qualidade;
- `check_custody`: reconstrói a relação de origem com HMAC e todos os digests;
- `validate_submission`: aceita preferência A/B, empate ou abstenção, justificativa e flags limitadas. Rejeita autorização e autenticação fictícias;
- `freeze_receipt`: congela cada submissão sem substituir assinatura ou verificação humana;
- `score`: contabiliza preferências concordantes, empates, abstenções, riscos e discordâncias, mas não cria aprovação técnica.

`tests/test_cycle45_blinded_pairwise.py` testa alterações de pacote, mapeamento, segredo, metadados, identidades alegadas, preferências, recibos e tentativa de reutilizar caminho privado dentro do repositório.

`.github/workflows/cycle45-blinded-review.yml` executa **somente fixtures sintéticas geradas em diretórios temporários**. Não transfere dados privados a artefatos do Actions.

## 4. Métrica e não equivalência

As duas submissões podem resultar em:

- Concordância simples de preferência (com denominador explícito).
- Consenso descritivo a favor da pergunta-base ou experimental, apenas se não houver flags, empates ou abstenção.
- Empate, duas abstenções, dissenso ou flag de risco, sem forçar um vencedor.
- Caso que exige adjudicação: **nenhuma resolução automática**.

Exemplo didático: se quatro casos receberam duas opiniões artificiais e houve três preferências coincidentes, o relatório retorna 3/4 de concordância. Isso **não é concordância entre especialistas reais**; os aliases e suas respostas foram criados no teste.

Preferências podem ser correlacionadas, e concordância não prova acerto. Nem mesmo avaliações humanas concordantes seriam, sozinhas, prova de causa raiz, sensibilidade, especificidade ou redução de falhas.

O desmascaramento para a pontuação é realizado somente no lado custodial e depois de congelar as duas submissões. O resultado contém contagens de preferência sob origem dos candidatos, mas **nunca afirma diagnóstico válido**.

## 5. Reprodução sem publicar casos

O laboratório não inclui pacote de estudo pronto, gabarito, identidade, credencial, laudo real ou literaturas proprietárias. Para executar a CLI, o operador prepara arquivos **privados** fora do checkout, obedecendo os esquemas do Ciclo 30 e o manifesto de qualidade do Ciclo 32.

```bash
python -m unittest tests.test_cycle45_blinded_pairwise -v

python -m benchmarks.cycle45_blinded_pairwise prepare \
  --source /private/cases.json \
  --candidates /private/paired-candidates.json \
  --quality-metadata /private/quality-metadata.json \
  --quality-policy /private/quality-policy.json \
  --key /private/custodian.key \
  --packet /private/paired-reviewer-packet.json \
  --lock /private/paired-mapping-lock.json \
  --quality-receipt /private/paired-quality-receipt.json
```

Após duas submissões privadas separadas, congelar cada uma com `freeze` e pontuar com `score`, fornecendo os mesmos argumentos de origem/qualidade/chave e os dois pares `--submission-a/--receipt-a` e `--submission-b/--receipt-b`, além de `--output`. O arquivo de saída também deve permanecer **privado**.

A CLI cria novos arquivos com exclusividade, recusando substituição. Um fluxo interrompido durante gravações pode deixar arquivos parciais, que o custodiante deve tratar como tentativa falha e recuperar sob nova execução identificada — não substituir silenciosamente o registro.

## 6. Antes de qualquer estudo humano

1. Formalizar objetivo, critérios de inclusão, tamanho amostral, plano estatístico, critérios de suspensão, tratamento de dados e autorização institucional.
2. Verificar e documentar autorização de uso de cada caso, titularidade do material, competência técnica, independência e conflitos dos revisores.
3. Manter corpus inédito, derivação e gabaritos fora do repositório público, com custódia independente dos autores do algoritmo.
4. Verificar que a redação das perguntas A/B não revela sua origem; congelar baseline e método experimental antes da entrega aos avaliadores.
5. Coletar duas avaliações independentes sem troca de informações, documentar divergências e solicitar parecer fundamentado de adjudicador distinto.
6. Reportar preferência, discordância, taxa de rejeição/abstenção e intervalos de incerteza apropriados — nunca acurácia de causa raiz sem verdade causal verificada.
7. Preservar autorização humana separada para qualquer medição, intervenção, notificação, compra, alteração ECM ou liberação de equipamento.

## 7. Riscos materiais que permanecem

- O código **não verifica a identidade dos revisores**; apelidos diferentes podem representar a mesma pessoa.
- Hash/HMAC não prova independência, autoria ou consentimento.
- Qualidade documental está baseada em metadados declarados e comparação lexical; similaridade semântica pode escapar.
- A organização das perguntas pode induzir viés de ordem ou de formulação apesar do balanceamento.
- Não há avaliação física, limites OEM por configuração/serie, probabilidade ou custo de teste.
- Abstenção e dissenso não são erros por padrão; podem ser manifestações tecnicamente corretas de incerteza.
- **NO GO:** nenhum aceite mecânico, execução, alteração de equipamento, escrita SAP ou permissão institucional é criada.

**Próxima fronteira:** preparar um protocolo de adjudicação externa e auditoria efetiva da neutralidade linguística e custódia das respostas. A evolução seguinte deve priorizar independência de avaliação e qualidade do corpus, não a quantidade de cenários sintéticos.
