# Ciclo 04 — Evidências, ensaios e proveniência auditável

**Situação:** protótipo didático v0.4.0, ligado à [Issue #8](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/8).  
**Aplicação-piloto:** quatro investigações sintéticas CAT 777E do Ciclo 03.  
**Fonte de conhecimento:** snapshot público FMEA Mining conteúdo 1.0.0, contrato 1.0.0, preview 1.3.12, SHA-256 `b780a1c95e6f2ab5b3fb1f9acd20a63a1a5abd0e3f3ed111f61052b2e8c59c65`.

## Problema resolvido

No ciclo anterior, os sinais eram códigos de cenário. Isso não distingue suficientemente **relato**, **observação**, **ensaio proposto**, **ensaio efetivamente executado**, **resultado de teste**, **interpretação** e **revisão profissional**.

Neste ciclo criamos entidades independentes, relações verificáveis e uma trilha de integridade. É fundamental que frases como «água confirmada na recoleta» em um cenário não se tornem, por si sós, comprovação de um teste executado na máquina. Na nova estrutura, todos os códigos dos quatro cenários **são registrados como relatos simulados**, mesmo quando sua redação menciona teste ou medição.

## Contratos implementados

| Entidade | Papel na investigação | Restrições do piloto |
| --- | --- | --- |
| `Observation` | relato original ou sinal codificado, com origem, contexto e limitações | apenas `simulation`; operador não é instrumento |
| `TestMethod` | método proposto pelo FMEA, com vínculo ao ID original | oito métodos com `proposed_not_executed`, nunca promovidos |
| `TestResult` | resultado de **execução explicitamente simulada**, registrado em objeto separado | exige método conhecido, instrumento/identificação de calibração **fictícios**, condição, ponto, momento e horímetro |
| `Evidence` | interpretação qualitativa vinculada a **uma** observação ou resultado | `consistent_with`, `inconsistent_with` ou `not_discriminating`; jamais confirmação automática |
| `HypothesisAssessment` | mantém as sete hipóteses, vínculos de evidência, disposição e revisão | `confidence=null`, `rootCauseConfirmed=false`, revisão independente pendente |

Esquemas em `contracts/{observation,test-method,test-result,evidence,hypothesis-assessment,evidence-ledger}.schema.json`. O validador Python em `evidence/ledger.py` impõe também relações **entre** objetos que não são demonstradas apenas pelos esquemas isolados.

`EvidenceLedger` agrega as cinco entidades e ancora `caseId`, hash do caso, proveniência do FMEA, bloqueios de liberação, identidade do revisor e eventos auditáveis.

## Fluxo real da implementação

```text
Caso fictício estritamente tipado (SIM-*)
      |
      +--> Relato de operador (OBS-000, nenhum instrumento)
      +--> Sinais do exercício (OBS-001...; natureza = simulation)
      |
Índice FMEA público previamente autenticado pelo snapshot SHA-256
      |
      +--> Oito TestMethod propostos, não executados
      |
Regra pedagógica de hipóteses do Ciclo 03
      |
      +--> Evidências qualitativas EVD-* com origem em OBS-*
      +--> Sete HypothesisAssessment, nenhum confirmado
      +--> TestResult[] vazio por padrão
      |
Ledger validado -> seis eventos de hash encadeado -> relatório v2
      |
Revisão humana pendente; nenhuma liberação ou OS
```

A CLI do Ciclo 03 foi ampliada: mantém o mesmo caso, valida o snapshot original e devolve uma nova propriedade `evidenceLedger` no relatório **`maintenance-superinteligence.final-drive-investigation.v2`**. Mudança de versão explícita: consumidores que necessitarem do contrato antigo v1 devem fixar versão anterior ou adaptar.

## Execução

```bash
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m investigations.final_drive \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --index build/fmea-public/fmea-public.index.json \
  --case examples/777e_additives_only.json \
  --output build/investigations/777e_additives_only.json
```

**Exemplo de TestResult deliberadamente fictício:**

```bash
python -m investigations.final_drive \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --index build/fmea-public/fmea-public.index.json \
  --case examples/777e_water_disputed.json \
  --simulated-test-results examples/777e_simulated_test_results.json \
  --output build/investigations/supplementary_simulation.json
```

No segundo comando, o `TestResult` é aceito apenas como evento didático explícito. Os oito `TestMethod` oriundos do FMEA continuam com `status=proposed_not_executed` e o resultado simulado **não altera** as hipóteses nem libera a máquina.

## Auditoria técnica e integridade

- Cada objeto possui identificador estável **no caso**; `sourceRef` usa espaço de nomes `SIM-*`, não referência SAP.
- Cada evidência de hipótese precisa apontar para uma origem única e possuir referência de volta no `HypothesisAssessment`.
- O validador verifica o relato original, valores e fontes dos sinais com o caso de entrada, e confronta relações de indícios com a rubrica didática do investigador.
- Nenhum resultado real, informação de máquina identificável, dado corporativo, valor OEM não verificado, confiança numérica, homologação de série ou identidade fictícia de revisor é permitido.
- A cadeia de **seis hashes SHA-256** cobre: entrada do caso, observações, métodos, resultados sintéticos, interpretações e avaliações/revisão. É **detecção de alterações semânticas e estruturais**, mas **não autenticação criptográfica contra um atacante com poder de reescrever todos os dados e recalcular hashes**. Para futura integridade de evidência real serão necessários assinatura, controle de acesso, registro de tempo e trilha externa imutável.

## Casos adversariais

Os testes verificam, entre outros: resultado real sendo aceito como simulação; método do FMEA marcado como executado; resultado sem contexto/instrumento; hipótese com confiança inventada; causa raiz confirmada sem revisão; vínculo circular ou órfão; troca de fonte; inversão de indício favorável para contrário; omissão de dado neutro; e adulteração seguida de recálculo local dos hashes.

**O sucesso do CI mede consistência do software e invariantes do modelo**, não a capacidade de diagnosticar um comando final real.

## Lacunas e próximo ciclo

1. Contratos v1 são restritos a `training_simulation`; a coleta de dados reais autorizados exige um **ambiente separado** e arquitetura de privacidade, retenção, autorização e custódia.
2. `TestResult` exige metadados preenchidos, mas são **apenas campos simulados**: a existência de `instrumentId` e `calibrationReference` não comprova calibração.
3. Os sinais ainda são escolhidos por códigos predefinidos; não há parser robusto de documentos ou linguagem natural.
4. Não há comparação com valores OEM por série, julgamento estatístico quantitativo, baseline verdadeiro ou autorização operacional.
5. Próximo passo recomendado: biblioteca de métodos de observação e testes discriminantes com formulários específicos por disciplina (óleo, hidráulica, vibração, elétrica), mantendo interface pública didática e infraestrutura operacional separadas.
