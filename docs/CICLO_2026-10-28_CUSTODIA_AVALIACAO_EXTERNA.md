# Ciclo 30 — Custódia de casos inéditos e avaliação externa futura

**Versão:** P&D 3.0.0 · **Data:** 28/10/2026

## Objetivo

O Ciclo 29 exportava casos sem o gabarito, mas ambos existiam no mesmo repositório público. O Ciclo 30 estabelece uma **fronteira de armazenamento**: novos casos, respostas, chave de custódia, pareceres e relatórios ficam somente em diretórios locais externos ao checkout, administrados por um custodiante. É um protótipo de processo, não um serviço de avaliação ou um estudo independente realizado.

## Arquitetura do processo

1. **Preparar**: um custodiante autorizado cria dois arquivos privados, um com casos inéditos e outro com expectativas de avaliação. O utilitário exporta um pacote para os revisores sem respostas e um registro de compromisso HMAC-SHA256. Nenhum dos dois contém a chave.
2. **Distribuir**: o pacote de perguntas é fornecido aos avaliadores por canal externo autorizado. A ferramenta não envia mensagens nem verifica identidade.
3. **Congelar**: cada submissão é amarrada por SHA-256 ao pacote e recebe recibo separado; arquivos de saída já existentes não são sobrescritos.
4. **Pontuar**: somente o custodiante que conserva a chave e o gabarito consegue verificar o compromisso e comparar os dois pareceres congelados. O relatório fornece contagens de concordância e alertas críticos, não publica o gabarito.
5. **Adjudicar**: divergências exigem avaliação humana externa. Nenhum consenso é inferido automaticamente.

## Comandos CLI

São obrigatórios arquivos privados de entrada **fora da árvore de trabalho Git**. O conjunto público não fornece dados privados prontos. Os modelos de estrutura podem ser consultados em `contracts/heldout-*.schema.json` e os exemplos sintéticos são construídos temporariamente pela suíte `tests/test_heldout_study.py`.

```bash
python -m benchmarks.heldout_study prepare \
  --cases /private/cases.json --oracle /private/oracle.json \
  --key /private/custodian.key --packet /private/reviewer-packet.json \
  --lock /private/custody-lock.json

python -m benchmarks.heldout_study freeze \
  --packet /private/reviewer-packet.json \
  --submission /private/reviewer-a.json --receipt /private/receipt-a.json

python -m benchmarks.heldout_study freeze \
  --packet /private/reviewer-packet.json \
  --submission /private/reviewer-b.json --receipt /private/receipt-b.json

python -m benchmarks.heldout_study score \
  --packet /private/reviewer-packet.json --lock /private/custody-lock.json \
  --oracle /private/oracle.json --key /private/custodian.key \
  --submission-a /private/reviewer-a.json --submission-b /private/reviewer-b.json \
  --receipt-a /private/receipt-a.json --receipt-b /private/receipt-b.json \
  --output /private/heldout-report.json
```

A chave deve conter pelo menos 32 bytes aleatórios e, em sistemas POSIX, possuir permissões restritas. Por exemplo, gerá-la em diretório privado e definir `umask 077` antes de gravar. Não inserir chaves, dados de máquina, laudos, documentos licenciados ou credenciais em issues, PRs, logs e artefatos de CI.

## O que o HMAC protege — e o que não protege

- O compromisso **HMAC-SHA256** impede que uma mudança casual ou não autorizada no pacote/gabarito passe despercebida **sem posse da chave**. Ele não prova competência, independência, titularidade nem autorização do custodiante.
- Um custodiante malicioso que controle chave, dados e registro pode produzir outro conjunto válido. A chave é o ponto crítico de confiança. Para uso real, é necessária gestão de chaves, controle de acesso, trilha externa independente e versões retidas sob política formal.
- O recibo de SHA-256 apenas detecta alterações em submissões congeladas quando se dispõe de uma cópia confiável para comparação. **Não é assinatura digital, certificação de identidade ou carimbo temporal confiável.**
- O comando CLI restringe caminhos aos diretórios externos ao repositório e cria arquivos novos com permissão restrita; isso **não equivale a sandbox de sistema operacional, prevenção de exfiltração nem controle de acesso corporativo**.
- O relatório inclui somente contagens e identificadores de casos em divergência, não o texto da expectativa privada. Não contém detalhamento de todas as evidências nem prova de correção técnica.

## Validação no CI

A automação GitHub roda apenas testes que criam dados inventados em diretórios temporários do sistema, fora do checkout. O workflow não acessa credenciais, gabaritos privados, casos inéditos verdadeiros, literatura OEM licenciada ou dados reais de manutenção. Não há upload de artefatos contendo dados externos.

## Próximos passos obrigatórios para um estudo humano

- Contratar ou convidar revisores externos com concordância e conflitos de interesse documentados.
- Custodiar casos realmente inéditos, de fontes autorizadas, com objetivo e aplicabilidade da evidência estabelecidos.
- Definir acordo de confidencialidade, identificação de avaliadores, controle de acesso, revisão de dados e retenção.
- Manter gabarito e chave sob custodiante independente dos autores do seletor, preferencialmente em ambiente privado gerido.
- Formalizar revisão técnica dupla e terceiro parecer quando houver dissenso crítico; só então medir concordância e desempenho em falhas.

**Status de aceitação:** `no_go_independent_expert_verification_required`. Nenhuma revisão humana foi executada; nenhuma ordem, teste físico, alteração ECM ou liberação de máquina são autorizados.
