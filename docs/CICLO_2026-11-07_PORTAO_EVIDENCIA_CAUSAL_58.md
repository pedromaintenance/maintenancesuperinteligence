# Ciclo 58 — Portão de evidência causal e hipóteses concorrentes

**07/11/2026 · P&D · Conteúdo de origem do C58, agora proposto como piloto isolado no Ciclo 69 · NO GO**

## Lacuna enfrentada
Os 24 cenários autorais e os 128 percursos contrafactuais anteriores validam a **estrutura da seleção de perguntas**, não a sua utilidade mecânica. O protocolo privado do Ciclo 30 já prepara a custódia de casos inéditos, mas seu gabarito `expectedQuestionId` não exige que autores justifiquem por que um teste distingue mecanismos concorrentes. O Ciclo 58 adiciona um portão de **estrutura de evidência causal**, sem substituir a custódia, o julgamento humano ou a literatura OEM.

## Entregas
- `benchmarks/cycle58_causal_gate.py`: valida offline um cenário **explicitamente sintético**, duas a cinco hipóteses concorrentes, possível contraprova para cada hipótese, um a doze testes propostos e a consequência prevista para **cada** hipótese.
- `tests/test_cycle58_causal_gate.py`: casos adversariais de promoção de causa, teste autorizado indevidamente, campo inesperado, falsa identidade de revisor, ausência de contraprova e falso poder discriminante.
- `.github/workflows/cycle58-causal-gate.yml`: verificação somente do módulo e dos testes sintéticos, sem segredos.
- Este documento registra premissas, limitações e critérios de conclusão.

## Regra discriminante
Um teste conta como *discriminante estrutural* apenas quando prevê `supports` para ao menos uma hipótese e `contradicts` para outra. Previsões devem incluir uma justificativa por hipótese; `indeterminate` é aceito, mas sozinho não diferencia mecanismos. A ferramenta verifica a **existência textual dessas distinções**, jamais sua correção física. As justificativas ainda podem ser inventadas, circularmente definidas ou mecanicamente falsas.

Há uma distinção intencional entre `counterEvidence` (qual observação refutaria a hipótese) e `proposedChecks` (quais verificações poderiam produzir evidência). **Não se registra teste como executado ou medição como obtida.**

## Limites inegociáveis
- Só aceita `origin: synthetic_training_only`; dados reais e conteúdo OEM privado não entram neste contrato público. Casos autorizados futuros continuam sob custódia privada e exigirão outra integração explicitamente aprovada.
- Cada hipótese fica em `uncertainty: unconfirmed`.
- `safeToPerform=false` significa **não autorizado a executar**, não que o teste seria intrinsecamente perigoso.
- `requiresApplicableProcedure=true` exige consulta de procedimento aplicável antes de qualquer execução por pessoa habilitada.
- Flags de confirmação causal, efetividade OEM, diagnóstico validado, revisão humana e autoridade operacional são obrigatoriamente falsas.
- O recibo só contém contagens e estado **`structural_pass_no_diagnostic_validation`**, sem reproduzir o material analisado.
- O script não lê rede, não gera ordem, não altera sistemas e se recusa a sobrescrever recibos já existentes.
- Não realiza detecção de dados sensíveis dentro de textos fornecidos: usar **somente exemplos fictícios e publicáveis**; não colar dados operacionais privados em issues/PRs/Actions.

## Reproduzir

```bash
python -m unittest tests.test_cycle58_causal_gate -v
python -m benchmarks.cycle58_causal_gate --input /caminho/local/caso-ficticio.json --output /caminho/local/recibo-novo.json
```

Um exemplar programático do contrato aparece em `sample()` no teste do Ciclo 58. Não há fixture de caso operacional.

## Próximas etapas para validade mecânica
1. Especialistas externos devem estabelecer **previamente** rubrica de validade de mecanismo, relação função-falha, aplicabilidade, custo, risco e valor informacional.
2. Custodiante autorizado prepara casos genuinamente inéditos fora do Git, elimina vazamentos de gabarito e documenta proveniência e permissões.
3. Dois profissionais independentes julgam, sem conhecer respostas do sistema, adequação do teste e suas implicações físicas; registrar desacordos e eventual terceiro parecer.
4. Somente após tal avaliação será possível discutir métricas de discriminação mecânica. Contagens de campos preenchidos **não são acurácia nem competência**.
5. **Extração C69:** este módulo foi separado como PR experimental diretamente sobre `main`, sem carregar os demais ciclos. Revisão humana de código e aprovação explícita de merge continuam pendentes. A cadeia de PRs de pesquisa não foi mesclada.

**Decisão:** `NO GO`. Nenhuma execução física, acesso SAP/ECM, autorização OEM, criação de OS ou liberação de máquina.

## Nota de portabilidade — Ciclo 69

Este é um **candidato isolado para revisão de integração**, não uma aprovação para mesclar. A pasta `benchmarks` é um pacote de namespace Python na árvore base; o módulo C58 depende apenas da biblioteca padrão, e os testes usam `unittest`. O workflow não requer os arquivos C57–C68. Nenhuma dependência funcional com SAP, ECM, OEM ou máquinas reais foi introduzida. Verificar compatibilidade com `main` e CI no commit exato deste PR antes de qualquer integração.
