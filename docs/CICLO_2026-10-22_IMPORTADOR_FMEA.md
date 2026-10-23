# Ciclo 02 — Importação pública, pinada e verificável do FMEA Mining

**Data:** 22/10/2026  
**Escopo:** issue #2 — integração em leitura de conhecimento **não operacional**.  
**Estado:** implementação testada via GitHub Actions na branch de desenvolvimento; integração independente de SAP, telemetria ou equipamento.

## Pesquisa documental efetivamente usada

Foram examinados os arquivos **reais** do produtor `pedromaintenance/fmea-database-mining`:

- `data/governance/public-contract.v1.json`: contrato público `1.0.0`;
- `data/governance/public-export-policy.v1.json`: exportação apenas de hipóteses;
- `data/governance/public-content-release-policy.v1.json`: conteúdo independente da versão do pacote;
- `data/governance/public-content-releases.v1.json`: release atual `1.0.0`;
- `data/governance/snapshots/public-knowledge.content-1.0.0.json`: snapshot imutável;
- `schemas/public-knowledge-preview.schema.json`: estrutura do preview;
- `scripts/export-public-knowledge.mjs`: gerador upstream.

**Distinção indispensável:** a versão do repositório FMEA (`1.3.49` à época da pesquisa), a **versão de conteúdo público** (`1.0.0`), a versão do **contrato público** (`1.0.0`) e a **versão histórica do preview** (`1.3.12`) têm papéis diferentes. Esta integração não presume que mudanças internas no FMEA tenham sido publicadas no snapshot.

## Baseline importada

| Atributo | Estado |
| --- | --- |
| Produtor | `pedromaintenance/fmea-database-mining` |
| Commit fixo | `06541f688773f101e586cceed848d0140e73ba09` |
| Caminho | `data/governance/snapshots/public-knowledge.content-1.0.0.json` |
| SHA-256 declarado no registro upstream | `b780a1c95e6f2ab5b3fb1f9acd20a63a1a5abd0e3f3ed111f61052b2e8c59c65` |
| Cadeias causais aceitas | 24 |
| Fontes bibliográficas | 20 |
| Causas confirmadas | 0 |
| Ocorrências empíricas | 0 |
| Testes efetivamente realizados | 0 |
| Uso operacional homologado | **Não** |

**Famílias verificadas:** arrefecimento (8), material rodante (8), comandos finais (4), mangueiras hidráulicas (4).

O catálogo inclui as cadeias `FC-FD-001` a `FC-FD-004` sobre partículas e abrasão, água em lubrificante, lubrificação inadequada e fadiga de contato de rolamentos. Nenhum vínculo foi homologado para CAT 777E, série, posição ou circuito particular.

## Implementação

- `connectors/fmea-source-lock.v1.json` — travamento de produtor, SHA de commit, contrato, conteúdo, SHA-256 e campos autorizados.
- `connectors/fmea_public.py` — baixador de snapshot público **do commit exato** e validador fail-closed; admite arquivo local somente quando o mesmo SHA bate; sem dependências pip.
- `tests/test_fmea_public.py` — suíte de testes unitários com fixtures exclusivamente sintéticas e adversariais.
- `.github/workflows/validate.yml` — CI executa o importador real, confirma invariantes, publica índice e recibo como artefato temporário por 14 dias.

O resultado `build/fmea-public/fmea-public.index.json` é um **índice conceitual**, não base de ocorrências; o recibo `import-receipt.json` reporta quantidades, famílias, origem e bloqueios de autoridade.

## Como rodar

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python connectors/fmea_public.py --fetch --output build/fmea-public
```

Para ambiente offline, é necessário possuir o snapshot legítimo e íntegro em arquivo local:

```bash
python connectors/fmea_public.py --input ./snapshot-autorizado.json --output build/fmea-public
```

O hash deve ser idêntico ao travado. A opção `--input` **não** desativa a verificação da origem pelo checksum.

## Barreiras de integridade

1. Rejeita conteúdo com SHA diferente, alteração de campos, contagens inconsistentes ou fontes sem rastreabilidade.
2. Rejeita revisão/causa raiz confirmada, ocorrências reais ou classificação de evento.
3. Rejeita efeito apresentado como observado, teste marcado como executado ou aplicação por série/modelo adicionada.
4. Rejeita indicação de autorização operacional ou números de aceite inferidos da importação.
5. Preserva hipótese concorrente, método de investigação, fonte e limitações.

A importação **não** executa procedimentos de campo, não modifica o FMEA e não faz escrita SAP/ECM.

## Próximo trabalho delimitado

**Issue #3:** construir investigação didática estruturada de comando final, consumindo o índice gerado e acrescentando perguntas de identificação, evidências e testes diferenciais, mas sem tomar decisões operacionais. A escolha de CAT 777E é um contexto de estudo; nenhuma das quatro cadeias `FC-FD` do FMEA fica automaticamente aplicável ao modelo.

**Lacunas persistentes:** formato de questionário/registro de evidência, literatura OEM específica por série, limiares válidos, controles de autorização de fonte e avaliação independente da utilidade diagnóstica.
