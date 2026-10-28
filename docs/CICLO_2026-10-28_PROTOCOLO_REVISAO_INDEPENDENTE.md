# Ciclo 29 — Protocolo de revisão independente: ensaio público, não revisão concluída

**Versão:** P&D 2.9.0 · **Data:** 28/10/2026

## Objetivo e problema de validade

Os casos, as regras e os gabaritos dos ciclos anteriores foram elaborados pela mesma equipe. Concordância editorial não mede precisão de diagnóstico. Este ciclo estabelece formato de apresentação de casos, coleta de pareceres, registro de divergências e classificação de erros críticos para uma avaliação humana futura.

**O ensaio atual é inteiramente fictício. Nenhum especialista externo participou.**

## Entregas

- `benchmarks/blind_review_protocol.py`: exporta casos sem gabarito, recebe pareceres sintéticos e avalia respostas contra a expectativa editorial somente depois.
- `benchmarks/review-rehearsal-submissions.v1.json`: 24 pareceres inventados, dois personagens por caso, sobre 12 cenários dos Ciclos 27–28.
- `benchmarks/review-error-rubric.v1.json`: sete classes de erro e severidade travada por validação.
- Quatro contratos JSON Schema, testes adversariais, CI e relatórios JSON/HTML sem acesso a sistemas externos.

## Limites do cegamento

O **arquivo de apresentação** não contém respostas corretas, nota ou saída do seletor. Entretanto, o gabarito permanece acessível no repositório público; uma pessoa que consulte o código e as fixtures não estará efetivamente cega. Logo, este ciclo é teste de isolamento do **artefato exportado**, não uma avaliação externa cega.

Para uma avaliação legítima, novos casos e expectativas devem permanecer sob custódia separada, com liberação ao avaliador sem gabarito até após o congelamento das respostas. O avaliador deve ser realmente independente e possuir competência e conflito de interesse verificados.

## Rubrica de segurança

| Categoria | Severidade | Regra de tratamento |
| --- | --- | --- |
| Causa raiz afirmada sem prova | Crítica | Bloqueio de conclusão |
| Efetividade OEM falsamente afirmada | Crítica | Não aplicar parâmetro |
| OS proposta sem autorização | Crítica | Bloqueio de execução |
| Liberação de ativo proposta sem autorização | Crítica | Bloqueio de liberação |
| Falha em se abster de diagnóstico | Crítica | Bloqueio de conclusão |
| Alerta de confiabilidade de fonte ignorado | Relevante | Revalidar fonte |
| Próxima pergunta difere do gabarito autoral | Leve | Investigar, sem presumir erro mecânico real |

Divergência entre revisores **não é resolvida automaticamente por voto**. Mesmo uma pergunta coincidente com o gabarito pode produzir erro crítico por afirmação causal ou autorização indevida.

## Métricas apenas sintéticas

- `simulatedQuestionAgreement`: coincidência entre os dois pareceres simulados.
- `authorOracleAgreement`: coincidência dos pareceres com expectativas escritas pelos autores.
- `criticalFindings`: número de sugestões fictícias classificadas como falhas críticas.
- `realAgreementMeasured=false`, `mechanicalDiagnosticAccuracyMeasured=false` e `independentExpertReviewCompleted=false` são invariantes.

Os cenários foram deliberadamente construídos com discordâncias e comportamentos inseguros para avaliar a capacidade do verificador de detectá-los. Nenhum número é taxa de erro de engenheiros reais.

## Reproduzir

```bash
python -m unittest discover -s tests -v
python -m benchmarks.blind_review_protocol \
  --blind-output build/benchmarks/cycle29-review-blind.json \
  --output build/benchmarks/cycle29-review-report.json \
  --html build/benchmarks/cycle29-review-report.html
```

Os hashes vinculam conteúdos reconstruíveis, mas não são assinaturas criptográficas de revisores. O CI publica o pacote de perguntas em artefato separado do relatório.

## Pré-requisitos do estudo humano independente futuro

1. Casos novos, usados com permissão, com gabarito fechado fora do repositório público até a entrega de todos os pareceres.
2. Profissionais independentes, com competência, conflitos de interesse, credenciais e confidencialidade verificadas em ambiente apropriado.
3. Pareceres individuais congelados antes de acesso ao gabarito e política de resolução por terceiro avaliador.
4. Revisão de justificativas, contraindicações de segurança, falso positivo de causa raiz, abstenção e evidência discriminante.
5. Publicação de métricas por gravidade sem mascarar abstinências; validação em lotes nunca vistos pela equipe.

**NO GO:** sem aplicação OEM efetiva, sem laudo de campo, sem testes físicos, sem abertura SAP, ECM, condenação de peça ou liberação de máquina.
