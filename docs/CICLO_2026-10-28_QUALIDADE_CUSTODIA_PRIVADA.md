# Ciclo 32 — Qualidade obrigatória antes de distribuir casos custodiais

**P&D 3.2.0 · 28/10/2026.** A auditoria de qualidade deixa de ser opcional na interface de distribuição e pontuação do Ciclo 30.

## Controles integrados

1. O CLI `prepare` exige `--quality-metadata`, `--quality-policy` e `--quality-receipt`. Todos os arquivos ficam **fora do repositório público**, inclusive fonte de casos e gabarito.
2. O auditor cruza 100% dos registros `test` com os casos custodiais por ID, domínio, narrativa, status documental e digest. Metadados trocados, incompletos ou falsificados são rejeitados.
3. Entre `train`, `dev` e `test`, procura reutilização de linhagem, grupo de origem, referência de evidência, texto idêntico e semelhança lexical Jaccard superior ao limiar definido pela política.
4. Exige mínimos de divisões, presença dos domínios selecionados, situações documentais e etiquetas de hipóteses. Todas as hipóteses permanecem não confirmadas e exigem abstenção.
5. Se a auditoria reprovar, o CLI não grava pacote, lock ou recibo. No comando `score`, a fonte, o manifesto, a política e o recibo são verificados novamente antes de qualquer pontuação.

## Estruturas privadas

`contracts/private-quality-metadata.schema.json` contém os registros com `split`, `domain`, `mechanismTag`, `lineage`, `sourceGroup`, `evidenceRef`, `narrative`, `caseDigest`, `documentaryStatus`, `abstentionRequired=true` e `causeConfirmed=false`. No teste, o `caseDigest` corresponde ao hash canônico de `caseId`, `domain`, `symptom`, `observations`; em treino/dev, ao hash de `caseId` e `narrative`.

`contracts/private-quality-policy.schema.json` define `splitMinimums`, `requiredTestDomains`, `requiredTestStatuses`, `requiredTestMechanisms` e `nearDuplicateThreshold`. O comprovante em `contracts/private-quality-receipt.schema.json` vincula por digest pacote, metadados, política e resultado da auditoria.

## Uso

Os exemplos de comandos `prepare` e `score` do [Ciclo 30](CICLO_2026-10-28_CUSTODIA_AVALIACAO_EXTERNA.md) foram atualizados. Uma demonstração de montagem de entradas sintéticas em diretório temporário consta de `private_quality_fixture` em `tests/test_heldout_study.py`. O `freeze` mantém a interface anterior.

## Limitações e consequências

- Linhagens e fontes são autodeclaradas; a auditoria não autentica sua origem. Parafrasear a mesma ocorrência pode burlar uma comparação lexical.
- Etiquetas de mecanismos são hipóteses de cobertura, não verdades OEM, falhas físicas comprovadas ou diagnósticos por especialistas.
- Digests e recibos não são assinaturas humanas. O HMAC do Ciclo 30 vincula pacote e gabarito, mas não demonstra autoria humana ou qualificação técnica.
- A política de cobertura pode ser criada pelo custodiante; aprovação independente continua necessária. APIs Python de baixo nível permanecem acessíveis para teste, enquanto a interface CLI exige o gate.

**NO GO:** nenhum acesso SAP, alteração ECM, teste físico, autorização de OS, troca de peças ou liberação de equipamento. Revisão humana independente e documentação OEM efetiva permanecem requisitos futuros.
