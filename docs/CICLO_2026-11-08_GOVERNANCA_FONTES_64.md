# Ciclo 64 — Governança estrutural de fontes, revisões e conflitos documentais

**08/11/2026 · P&D · proposta empilhada sobre C63 · NO GO**

## Problema
C63 verifica correspondência **apenas textual e numérica de metadados fictícios** entre equipamento e referência. Ainda que esses campos coincidam, um documento pode estar revogado, substituído, existir em revisões concorrentes, ou contradizer outra fonte. C64 introduz um portão de **governança declarativa de fontes sintéticas**, sem atribuir autenticidade ou aplicar manual OEM.

## Implementação
- `benchmarks/cycle64_source_governance.py`: primeiro executa `validate` de C63; exige ao menos uma entrada documental fictícia para cada referência e até 30 registros por ensaio.
- Cada registro carrega `sourceId`, `referenceId`, `lineageId`, `revisionOrdinal`, `status`, `supersedes`, `claimToken`, `sourceNature`, `provenanceVerified`.
- Estados documentais: `active`, `superseded`, `revoked`. Um `superseded` exige sucessor explícito `active` no mesmo ramo e na mesma referência, com ordinal crescente. Registros revogados nunca contam como ativos.
- Rejeita: elo inexistente, vínculo à própria fonte, regressão de revisão, garfos de substituição, duas revisões ativas na mesma linhagem, referência desconhecida, metadados reais ou alegação de proveniência autenticada.
- Duas linhagens ativas com `claimToken` diferentes criam `unresolvedActiveClaimConflict=true`; coincidência de rótulos não cria aprovação.
- `tests/test_cycle64_source_governance.py`: 19 métodos positivos e adversariais.
- `.github/workflows/cycle64-source-governance.yml`: regressão offline C58–C64 sem chaves, dados corporativos, rede industrial ou serviços OEM.

## Limites importantes
1. **Os documentos são integralmente inventados.** Todos os IDs seguem `SIM-`, `sourceNature=invented_document_only` e `provenanceVerified=false`.
2. `claimToken` é apenas uma etiqueta categórica artificial. Divergência entre etiquetas **não prova contradição semântica ou mecânica**, e igualdade não comprova consenso de especialistas.
3. O registro `supersedes` é declaração fornecida no arquivo, não comprovação de uma errata, boletim, revisão aprovada ou atualização oficial. O algoritmo testa coerência de vínculos, não autenticidade.
4. O modelo rejeita bifurcação de linhagem e múltiplas revisões ativas do mesmo documento porque não dispõe de política institucional para precedências e derivação. Em situações reais, isso pode exigir modelagem mais rica e adjudicação humana.
5. `revisionOrdinal` não é revisão OEM. Um número maior não autoriza substituir manual efetivo, pois versões podem ter escopos e arranjos distintos.
6. O ensaio não comprova validade temporal, direitos autorais, custódia, assinatura, identificação de fabricante, numeração de série real, vigência ou aplicabilidade de fonte.
7. A existência de fonte ativa **não** promove uso operacional. Mesmo com zero conflitos identificados, todas as fontes continuam não verificadas e resultado `NO GO`.

## Sinais de saída
- `activeSources` e `revokedSources`: contagens de registros fictícios por referência.
- `no_active_source`: não há fonte ativa declarada para a referência.
- `active_sources_disagree`: etiquetas divergentes entre linhagens ativas.
- `revoked_source_present`: existe fonte revogada entre os registros.
- `unresolvedConflicts`: quantidade de **referências** com etiquetas ativas divergentes, não quantidade de falhas mecânicas nem pareceres humanos.
- `sourceAuthenticityVerified=false`, `revisionApproved=false`, `oemEffectivityVerified=false`, `operationalAuthorityGranted=false`, `decision=NO GO`.

## Reproduzir
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics tests.test_cycle63_effectivity tests.test_cycle64_source_governance -v
python -m benchmarks.cycle64_source_governance --input /tmp/fontes-ficticias.json --output /tmp/recibo-c64-novo.json
```
Exemplo sintético: `fixture()` em `tests/test_cycle64_source_governance.py`.

## Próxima decisão: C65
Priorizar **adjudicação de conflitos e cadeia de revisão humana separada**: requisitos de parecer, justificativa, contestação, histórico imutável e autoridade externa adequada, sem preencher automaticamente os campos de aprovação.

**NO GO** para consulta operacional de parâmetros, abertura de OS, autorização de ensaios, mudança SAP/ECM, conclusão causal e liberação de equipamentos.
