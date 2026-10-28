# Ciclo 35 — Revisão crítica das relações causais e preservação de dissenso

**P&D v3.5.0 · 28/10/2026.** Processo de crítica estruturada, ainda sem avaliações de profissionais externos comprovadas.

## Objetivo

Uma matriz que descreve resultados favoráveis, contrários e inconclusivos ainda pode conter relações causais frágeis. O Ciclo 35 fornece um processo para questionar **cada uma das 36 regras do Ciclo 34**, documentando justificativa e contraexemplo antes de propor sua correção. O fluxo não aceita revisões como homologação automática.

## Escopo e dados

- **36 regras** vinculadas por ID e texto exato à matriz do Ciclo 34; a fonte geral é referenciada pelo ID catalogado no Ciclo 33.
- **72 pareceres inteiramente fictícios**, produzidos pela equipe autora: dois personagens (`SIM-CRITIC-A`, `SIM-CRITIC-B`) em cada relação. Não são avaliações de especialistas humanos.
- Campos de parecer: `reviewId`, `ruleId`, `parentRecordId`, `ruleText`, `reviewerAlias`, `disposition`, `challengeType`, `argument`, `counterexample`, `sourceIds`, `sourceScope`, `proposedRevision` e negações de prova de campo/assinatura/autorização.
- Disposições previstas: conservar **apenas para estudo**, solicitar revisão, propor remoção ou declarar suporte insuficiente. Mesmo concordância entre personagens **não produz aprovação técnica**.

## Resultado da simulação

| Situação na triagem editorial | Número de regras |
| --- | ---: |
| Divergência entre os dois personagens, não resolvida | 12 |
| Dois pareceres propondo revisão, ainda sem aprovação | 12 |
| Dois pareceres considerando o suporte insuficiente | 12 |
| Relações técnicas confirmadas por especialistas independentes | 0 |

Todas as **36 relações** permanecem pendentes de avaliação independente; o código não modifica automaticamente a matriz original. O mecanismo não mede precisão diagnóstica, concordância de especialistas reais nem efeito de intervenção.

## Fonte, contraexemplo e revisão

Cada parecer deve incluir um argumento técnico, um contraexemplo hipotético e referência de contexto geral válida no catálogo do Ciclo 33. O programa impede referenciar fonte inexistente ou de outra hipótese parental. **A presença de uma fonte catalogada não comprova que o fabricante endossa a crítica ou a mudança solicitada.**

Exemplo: para um código armazenado, uma crítica pode exigir confirmação da data e estado ativo versus histórico antes de tratar a ocorrência como explicação do comportamento físico. Um contraexemplo seria um evento antigo sem repetição; isso não prova que a ECM ou circuito estejam íntegros.

## Proteção da integridade

- O lote de pareceres possui um **recibo SHA-256** ligado ao digest da matriz e da política.
- O relatório fornece uma cadeia de digests por entrada (`previousDigest`, `recordDigest`, `linkDigest`) e pode ser reconstituído/validado comparando-se dados de entrada íntegros.
- **Não é assinatura digital, carimbo de tempo, auditoria independente nem log imutável**. Um custodiante que controle todos os arquivos pode reescrever o conjunto; autenticação e carimbo exigiriam mecanismos externos.
- Uma submissão alterada após seu congelamento é rejeitada se o recibo original tiver sido preservado de maneira independente.

## Execução de demonstração pública

```bash
python -m unittest tests.test_causal_review -v
python -m knowledge.causal_review \
  --output build/benchmarks/cycle35-causal-review.json \
  --html build/benchmarks/cycle35-causal-review.html
```

## Entrada privada futura (não autenticada)

Existe modo local para importar comentários de dois aliases sem expô-los no GitHub. O arquivo privado deve usar o mesmo contrato, com `nature=unverified_private_reviewer_submissions`, e continuar marcando `authenticHumanReviewCount=0`, `independentTechnicalReviewCompleted=false` e todas as aprovações como falsas.

```bash
python -m knowledge.causal_review \
  --submissions /private/challenges.json \
  --seal-only --output /private/challenge-receipt.json

python -m knowledge.causal_review \
  --submissions /private/challenges.json \
  --receipt /private/challenge-receipt.json \
  --output /private/challenge-report.json
```

O recipiente privado é obrigatório fora do checkout Git. O código exige duas posições completas por regra, mas aliases diferentes **não comprovam independência, habilitação profissional ou consentimento**. A real identidade e as credenciais de qualquer avaliador devem ser verificadas por processo institucional separado.

## Contratos e limites

- `knowledge/causal_review.py` — valida, congela, avalia divergências e preserva hashes.
- `knowledge/causal-review-policy.v1.json` e `knowledge/causal-review-submissions.v1.json` — regras e lote de demonstração.
- `contracts/causal-review-{policy,submissions,receipt,report}.schema.json` — entradas e resultados.
- `tests/test_causal_review.py` — testes adversariais contra falsa autenticidade, fontes inválidas, desacoplamento da matriz, adulteração do recibo, autorização e regravação.

**Pendente para uso real:** seleção de especialistas independentes, verificação de identidade/competência, acesso legal à literatura OEM por série, processo de adjudicação documentado por profissional responsável e retenção dos registros em repositório privado gerido.

**Decisão:** `no_go_independent_causal_review_required`. Nenhum teste físico, ordem de serviço, troca de material, alteração ECM ou liberação é autorizado.
