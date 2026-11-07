# Ciclo 55 — Custódia versionada das evidências do GitHub Pages

**Data de recuperação: 07/11/2026 · P&D · proposta em PR draft sobre o Ciclo 54.**

## Questão que este ciclo enfrenta

O deploy do Pages foi comprovado por workflow e verificação HTTP no Ciclo 54, mas os artefatos `pages-release-evidence-<run-id>` têm prazo de retenção **de 30 dias**. Sem um registro persistente, perderíamos acesso ao manifesto e ao recibo originais assim que o GitHub descartasse o ZIP.

O Ciclo 55 **não altera o site publicado**: organiza custódia de evidências públicas e um procedimento de importação para futuros deploys. O arquivamento proposto está na branch de pesquisa; só ganha lugar na `main` após revisão e merge.

## Evidência efetivamente recuperada

O artefato do workflow foi baixado do GitHub e o ZIP foi conferido em **07/11/2026**.

| Atributo | Valor confirmado |
| --- | --- |
| Execução GitHub Actions | [#42412015125](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42412015125) |
| Commit implantado | `b930a177cc9ba1c94c32785f8fa0b16c37723afb` |
| Artefato | `pages-release-evidence-42412015125` |
| ID do artefato | `13589439429` |
| Digest SHA-256 do ZIP | `58b0b05a15589ddeec6f9f25cd6f57d3a7c10031300cee86734b2aa58646101b` |
| Data informada de expiração | **07/12/2026, 20:38:33 UTC** |
| JSON candidato | `9bd547dae00b6d59a9dad0c91493e9d1f399fbca0844a2757dd6f610aa02257b` |
| JSON recibo HTTP | `729a14ee3f9f595223729516a76251294eded07b270d7594c5c5f8b7812cf483` |

O **ZIP binário original também foi preservado no Git** como `source-artifact.zip`, com SHA-256 `58b0b05a...` e Git blob `5346143119a21443462ded761b220b6260c49b5e`. Portanto, mesmo após a expiração no GitHub Actions, o auditor pode verificar o ZIP completo, reabrir os dois membros originais e comprovar que são idênticos aos JSONs versionados. Essa verificação de bytes não substitui a validação independente da origem do arquivo no GitHub.

Os documentos estão em `archives/pages/2026-11-07-run-42412015125/`:

- `source-artifact.zip` — ZIP original completo do GitHub Actions, armazenado como arquivo binário no repositório;
- `pages-release-candidate.json` — resultado da preparação antes do deploy (`liveHttpBytesVerified=false`);
- `pages-http-receipt.json` — resultado da comparação HTTP pós-deploy (`liveHttpBytesVerified=true`);
- `custody-manifest.v1.json` — proveniência e digests conferidos, três hashes SHA-256 de HTML e respectivos Git blobs no commit de origem.

`archives/pages/index.v1.json` oferece uma entrada simples para agentes de IA e pessoas. O script `governance/cycle55_evidence_custody.py` recusa qualquer modificação nos bytes originais e em identificadores/direitos observados.

## Procedimento reprodutível para arquivar outros deploys

1. Consultar no **GitHub Actions** uma execução de publicação realmente concluída e bem-sucedida; conferir commit, run ID, nome do artefato, digest do ZIP, ID e expiração. Não usar apenas nome de branch ou screenshot como evidência.
2. Baixar o ZIP original antes da expiração. Validar que ele contém somente `pages-release-candidate.json` e `pages-http-receipt.json`.
3. Obter pelo GitHub os Git blobs dos arquivos `index.html`, `auditoria.html` e `versoes.html` **no commit da execução**. Não usar os hashes da branch atual se já tiver mudado.
4. Executar o importador com os dados confirmados, por exemplo:

```bash
python scripts/import_pages_evidence.py \
  --archive arquivo-original.zip \
  --archive-sha256 HASH_SHA256_DO_ZIP_CONFERIDO_NO_GITHUB \
  --commit SHA_COMPLETO_DA_EXECUCAO \
  --run-id ID_DA_EXECUCAO \
  --artifact-id ID_DO_ARTEFATO \
  --expires-at 2026-12-07T20:38:33Z \
  --git-blob index.html SHA_GIT_BLOB_DA_VERSAO \
  --git-blob auditoria.html SHA_GIT_BLOB_DA_VERSAO \
  --git-blob versoes.html SHA_GIT_BLOB_DA_VERSAO \
  --output-dir archives/pages/AAAA-MM-DD-run-ID
```

5. Revisar a saída, incluindo o ZIP copiado sem alterações. O importador **não consulta o GitHub** para confirmar que os valores informados são verdadeiros, apenas os confronta com o ZIP. Portanto, deve existir validação humana dos IDs, URLs e blobs.
6. Adicionar uma nova entrada ao índice **sem alterar os registros anteriores**. Abrir PR de revisão com ambos os JSONs e manifesto; passar pelo CI de custódia. Proibir segredos, conteúdo corporativo ou dados de manutenção restritos.
7. Fazer merge somente depois de revisão explícita. **Não publicar automaticamente essa evidência no GitHub Pages, nem atualizar `main` por um job com privilégios de escrita.**

## CI e fronteiras de confiança

```bash
python -m governance.cycle55_evidence_custody --check
python -m unittest tests.test_cycle54_pages_release_gate tests.test_cycle55_evidence_custody -v
```

O workflow `.github/workflows/cycle55-evidence-custody.yml` verifica hashes dos JSONs, conteúdo contraditório, alteração de origem, abuso do ZIP, declaração falsa de sucesso ou de aprovação operacional, e Schema JSON. Não usa rede externa para validar o estado presente das páginas.

O recebimento de três HTTP 200 com SHA-256 correto em **um instante** não comprova que o serviço está acessível agora, que pessoas conseguem usá-lo, que a documentação é cientificamente verdadeira ou que existem aprovações de engenharia.

A revisão humana prevista em `docs/QA_HUMANA_PORTAIS_54.md` continua **não executada**. Os 13 gates externos de validação técnica permanecem não verificados.

**Decisão: NO GO para teste físico, ordem de serviço, escrita SAP/ECM, validação OEM ou liberação operacional.**
