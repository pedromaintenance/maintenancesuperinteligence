# Ciclo 26 — Contestação independente fictícia e revogação de provas

**Versão P&D 2.6.0, 27/10/2026.** Decisão permanente `no_go`; sem piloto privado, assinatura real, revisão OEM ou autorização operacional.

## Problema
Uma explicação de dependências pode ficar obsoleta quando o grafo muda, uma prova é retirada ou duas áreas discordam. Um hash válido de relatório não equivale a identidade e nem mantém um aceite revogado.

## Entregas
- `pilot/review-contestations.v1.json`: dez situações **fictícias** associadas univocamente às dez propostas do Ciclo 24/25, cobrindo revisão obsoleta, retirada de evidência, discordância, autoaprovação, assinatura alegada, troca de responsável, revisão OEM suposta, ocultação de dissenso, falsa aprovação e ausência de evidência de segurança.
- `pilot/change_review_adjudication.py`: verificador com modelo de dados fechado, alias sintético, vínculo à versão de grafo, duas perspectivas explícitas de áreas distintas e rejeição de sinais ocultos.
- Em todo caso as **sete provas externas permanecem não verificadas**, a objeção é preservada e a decisão é `veto_no_merge`. Casos inválidos são bloqueados, nunca tratados como aprovações.
- Registro encadeado SHA-256 com `sourceEventDigest`, `sourcePacketDigest`, `resultDigest` e `previousDigest`. Encadeamento detecta adulteração quando reconstruído contra a origem canônica — **não fornece assinatura, identidade ou imutabilidade externa**.
- Contratos JSON Schema de entrada e saída, suíte adversarial e relatório JSON/HTML estático publicados pelo GitHub Actions.

## Cadeia de confiança do CI
`FMEA público pinado → Ciclo 24 verificado → Ciclo 25 verificado → Ciclo 26 reconstruído e comparado`.

O programa isolado que recebe um JSON arbitrário **não consegue autenticar a origem do arquivo**. O CI reduz esse risco ao reconstruir e comparar as fases anteriores. Os personagens de revisão são aliases puramente didáticos.

## Execução
Após os artefatos dos Ciclos 24 e 25:

```bash
python -m unittest discover -s tests -v
python -m pilot.change_review_adjudication \
  --packets build/graph-change/cycle25-review-packets.json \
  --output build/graph-change/cycle26-adjudication.json \
  --html build/graph-change/cycle26-adjudication.html
```

## Limites e próximos passos
Isto simula **regressões de governança**, não pareceres assinados. Não libera máquina, não cria nota ou ordem SAP, não muda ECM, não solicita peças e não verifica a série do equipamento. 
O próximo avanço deve priorizar um corpus independente de **investigações mecânicas educacionais**, com sintomas, hipótese concorrente, evidência discriminante, causa confirmada somente quando ancorada em fonte de caso autorizado e avaliação técnica externa. Dados empresariais e literatura OEM licenciada exigem ambiente privado e permissão.

O escopo de integração autenticada e revisão técnica real da issue #50 permanece aberto.
