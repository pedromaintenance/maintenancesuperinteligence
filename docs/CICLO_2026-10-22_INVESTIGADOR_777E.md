# Ciclo 03 — Investigador diferencial de comandos finais (piloto 777E)

**Data de execução:** 22/10/2026 — ambiente de GitHub Actions.  
**Questão associada:** [#3 — Diagnóstico diferencial CAT 777E](https://github.com/pedromaintenance/maintenancesuperinteligence/issues/3).  
**Natureza:** exclusivamente **investigação didática, de hipóteses não confirmadas**.

## Objetivo atingido

Implementar e testar um mecanismo determinístico que parte de observações sintéticas, consulta exclusivamente o **índice público do FMEA Mining previamente validado**, preserva hipóteses concorrentes, seleciona investigações já propostas na fonte e comunica bloqueios/escalação. Não interpretar texto livre, não consultar equipamento, não executar teste, não prescrever correção nem autorizar liberação.

## Fonte primária efetivamente utilizada

Snapshot público do FMEA Mining: conteúdo `1.0.0`, contrato `1.0.0`, preview histórico `1.3.12`, hash SHA-256 `b780a1c95e6f2ab5b3fb1f9acd20a63a1a5abd0e3f3ed111f61052b2e8c59c65`.

Cadeias de **comando final** com IDs originais e limites inalterados:

| Cadeia FMEA | Escopo originalmente catalogado | O que não significa |
| --- | --- | --- |
| `FC-FD-001` | ingresso de partículas e potencial desgaste abrasivo | partículas não identificam automaticamente a peça ou mecanismo |
| `FC-FD-002` | água como possível fator de corrosão/desgaste | água na primeira amostra não comprova ingresso no compartimento |
| `FC-FD-003` | condição de lubrificação, formulação/viscosidade e deterioração potencial | aditivos diferentes não significam óleo incorreto nem falha |
| `FC-FD-004` | fadiga de contato de rolamentos, como mecanismo possível | ruído/metais não condenam rolamento e nem provam posição |

**Aplicabilidade real:** todos os campos `modelId`, `locationId` e `serialOrArrangement` nas cadeias continuam `null`. Usar CAT 777E neste piloto **não homologa** essas cadeias para modelo, série ou compartimento.

## Conhecimento do FMEA versus regras autorais deste piloto

**Extraído do FMEA:** títulos, função, falha candidata, hipóteses concorrentes, limitações, referências bibliográficas e **8 métodos/investigações propostos** nas quatro cadeias. Nenhum método foi executado.

**Proposto neste ciclo para fins de teste:** três alternativas explícitas do próprio caso-piloto (`PILOT-FORMULATION`, `PILOT-SAMPLE`, `PILOT-OTHER-NOISE`), 13 códigos de indício possíveis, matriz qualitativa de indícios que sustentam/enfraquecem hipóteses, e três pares de divergências. Essas ligações são **rubricas didáticas**, não inferências probabilísticas, conclusões normativas nem novos fatos OEM.

**Dados de entrada:** apenas casos `SIM-*` em `training_simulation`; cada observação possui `evidenceNature=simulation` e `sourceRef=SIM-*`. Dados empíricos são rejeitados pelo contrato do piloto; também não são aceitos valores de pressão, torque ou thresholds inventados como campos livres.

## Integridade do pipeline

O Ciclo 03 **não confia** somente na propriedade `inputSha256` informada pelo índice, pois um arquivo local poderia declarar o hash correto e ainda conter conteúdo adulterado. Para cada execução:

1. Exige snapshot `--snapshot` e confere seus **bytes reais** pelo SHA-256 do release;
2. Reexecuta os testes semânticos do importador do Ciclo 02;
3. Reconstrói o índice em memória usando `build_consumer_index`;
4. Se o usuário forneceu `--index`, compara **todos** os campos com o índice reconstruído, rejeitando qualquer divergência;
5. Só então valida o caso e produz um relatório não operacional.

O CI executa uma adulteração sintética do índice e **exige que o programa a rejeite**, mesmo apresentando um snapshot legítimo. O snapshot é guardado como artefato transitório no `build/` para permitir auditoria do pipeline; não é committado como um novo banco autoritativo.

## Quatro cenários de regressão

| Arquivo | Condição simulada | Resultado esperado |
| --- | --- | --- |
| `777e_additives_only.json` | perfil aditivo alterado, sem contexto | `needs_evidence`, nenhuma hipótese de desgaste promovida |
| `777e_change_documented.json` | mudança de produto registrada + aditivos alterados | formulação considerada como concorrente, sem encerrar outras hipóteses |
| `777e_water_disputed.json` | teste de água positivo e não reproduzido em eventos simulados | `escalate_to_specialist`, manter divergência explícita |
| `777e_debris_and_noise.json` | partículas crescentes, material magnético, ruído e relato de perda funcional | `escalate_to_specialist`, **sem** identificar peça condenada |

Há ainda testes unitários que rejeitam alteração de esquema, modelo não contemplado, dados reais disfarçados como entrada tipada, hipóteses confirmadas, inspeção dada como executada e efetividade OEM falsamente promovida.

## Como executar

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public

python -m investigations.final_drive \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --index build/fmea-public/fmea-public.index.json \
  --case examples/777e_additives_only.json \
  --output build/investigations/777e_additives_only.json
```

**Saída estruturada:** `hypotheses`, `observations`, `conflicts`, `knowledgeGaps`, `plannedInvestigations`, `bibliography`, `riskAlerts`, `decision`, `limitations`, `humanReviewRequired`. Campos `confirmedRootCause` e `condemnedComponent` permanecem `null`; `mayReleaseEquipment=false` e `mayCreateWorkOrder=false`.

## Critério de aceite e limites

CI deve validar casos sintéticos e integridade real do snapshot, verificar *abstenção correta* e impedir concordância com um índice fraudado. O resultado demonstra **funcionamento da lógica educacional e barreiras de integridade**, não acurácia ou sensibilidade diagnóstica de campo.

**Pendente para um produto de engenharia:** hierarquia real por série, especificações e procedimentos OEM autorizados, instrumentos e condições de coleta, evidências reais sob infraestrutura restrita, validação por mecânico/engenheiro e estudo de desempenho contra casos reais ou supervisionados.

## Encaminhamento

**Ciclo 04 sugerido:** criar um modelo independente e versionado de `Observation/TestResult/Evidence` e trilha de auditoria de hipótese; avançar para um estudo comparativo de inspeções e coleta em que a distinção entre `relatado`, `medido`, `simulado` e `confirmado` seja um contrato explícito, antes de permitir interpretação de linguagem natural.
