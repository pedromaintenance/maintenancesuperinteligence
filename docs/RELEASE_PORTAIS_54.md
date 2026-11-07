# Ciclo 54 — Gate de publicação HTTP e revisão humana dos portais

**Data: 07/11/2026 · pesquisa empilhada sobre o Ciclo 53 · versão proposta.**

> **NO GO para operação industrial.** Essa entrega mede integridade de entrega de três arquivos públicos por HTTP. Não mede qualidade de diagnóstico, semântica mecânica, acessibilidade real em leitor de tela, licença OEM nem autorização para intervir em equipamentos.

## Evidência do primeiro deploy com verificação HTTP real

Em **07/11/2026**, o workflow [GitHub Pages #42412015125](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42412015125) concluiu com `success` para o commit `b930a177cc9ba1c94c32785f8fa0b16c37723afb` da `main`. O log registra duas etapas distintas: `prepare` com `liveHttpBytesVerified: false` e `verify` com `filesChecked: 3`, `liveHttpBytesVerified: true`, `humanQualifiedReviewVerified: false` e `operationalAuthorityGranted: false`.

O artefato **`pages-release-evidence-42412015125`**, criado pela execução, contém o manifesto preparado e o recibo de conferência HTTP (hashes de resposta iguais aos arquivos fonte). O workflow publicou os mesmos três HTMLs já existentes; alterou-se apenas a **infraestrutura de publicação**. Essa evidência comprova igualdade de conteúdo por HTTP na janela de teste, não usabilidade humana nem diagnóstico de campo.

## Falha de processo identificada

Até o Ciclo 53, o GitHub Actions confirmava que **a ação de publicação havia terminado**, mas o projeto não exigia evidência automatizada de que os três HTMLs estavam efetivamente sendo servidos com o mesmo conteúdo do deploy. A inspeção dos recibos era manual e a revisão humana de ergonomia não tinha um checklist reprodutível.

A documentação deve separar três eventos:

1. **Candidate staged:** arquivos locais foram preparados, validados e tiveram SHA-256 calculado; ainda não houve confirmação de entrega.
2. **GitHub Pages deploy succeeded:** o GitHub informou que a ação de deploy concluiu.
3. **HTTP byte match:** o workflow buscou cada URL pública e verificou HTTP 200, tamanho e SHA-256 correspondente ao arquivo preparado. Isso não prova renderização, acessibilidade ou operação.

A partir deste ciclo, a ação `deploy-pages@v4` mantém a publicação atual, mas a validação HTTP **deve falhar fechada** se o conteúdo servido não corresponder ao manifesto. O workflow registra dois artefatos: `pages-release-candidate.json` e, **somente em caso de êxito da conferência**, `pages-http-receipt.json`.

## Contratos e artefatos

- `scripts/pages_release_gate.py prepare`: lê apenas `index.html`, `auditoria.html`, `versoes.html` da pasta de publicação. Rejeita itens adicionais, links simbólicos, conteúdo incompleto, JavaScript externo e discrepâncias entre catálogos. Exige **NO GO visível**, marcações básicas de acessibilidade e os **13 gates externos não verificados** no índice embutido.
- `scripts/pages_release_gate.py verify`: após o deploy, busca as três URLs públicas no domínio fixo `pedromaintenance.github.io`, com parâmetros de cache-busting. Requer resposta HTTP 200, conteúdo com hash SHA-256 idêntico e tamanho correspondente. Falhas, respostas antigas, redirecionamentos finais para outro domínio ou dados alterados encerram a etapa com erro.
- `contracts/pages-release-candidate.schema.json`: o candidato obrigatoriamente informa `liveHttpBytesVerified: false`.
- `contracts/pages-http-receipt.schema.json`: só admite `liveHttpBytesVerified: true` no recibo do HTTP e mantém revisão humana e autorização operacional **false**.
- `tests/test_cycle54_pages_release_gate.py`: testes de conteúdo adulterado, mudanças de gates, recursos externos, redirecionamentos, HTTP 404, conteúdo inesperado e tentativa de atribuir aprovação.
- `.github/workflows/cycle54-release-gate.yml`: CI sintético/local da preparação e dos contratos, **sem consulta externa**.
- `.github/workflows/pages.yml` na `main`: integra o gate ao deploy real, com evidência preservada em **artefato do workflow**, sem `commit` automático, permissão de escrita adicional ou arquivo com credenciais.

## Revisão humana

O arquivo `docs/QA_HUMANA_PORTAIS_54.md` descreve testes concretos de:

- Layout mobile e zoom de 200–400%;
- Navegação por teclado, foco, salto para conteúdo e seleção de abas;
- NVDA/VoiceOver, anúncios dinâmicos e estrutura semântica;
- Clareza de status NO GO, fontes, versões e exportação JSON;
- Revisão de segurança e licenças do conteúdo público.

O modelo `review/portal_qa_template.v1.json` mantém **todas as verificações em `not_tested`**. A conclusão da ação HTTP não preenche respostas humanas, nem substitui revisão de um profissional competente. Não registrar dados pessoais ou documentos de mina no repositório.

## Comandos de reprodução

```bash
python -m unittest tests.test_cycle54_pages_release_gate -v

python scripts/pages_release_gate.py prepare \
  --site-dir portal \
  --source-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --run-id 1 \
  --output build/pages-release-candidate.json

# Verificação HTTP só após deploy comprovado e com URL oficial do GitHub Pages:
python scripts/pages_release_gate.py verify \
  --candidate build/pages-release-candidate.json \
  --base-url https://pedromaintenance.github.io/maintenancesuperinteligence/ \
  --output build/pages-http-receipt.json
```

O exemplo com SHA de `a` e run ID `1` **é um exercício de preparação**, não uma publicação real. No workflow, esses campos são substituídos pelo SHA e run ID do próprio GitHub Actions.

## Critérios de aceite e limitações

**Aceite automatizado:** os três bytes-fonte foram validados e o servidor do Pages devolveu bytes com hashes idênticos, comprovados por um recibo vinculado ao commit e run ID de publicação. O artefato pode ser recuperado do GitHub Actions e comparado com o commit correspondente.

**Pendências humanas:** testar a experiência em navegadores reais, avaliar contraste e reflow, revisar todas as fontes e metadados públicos e conferir direitos de publicação.

**Limitações técnicas:** CDN, disponibilidade por região e mudanças posteriores ao teste não são monitoradas continuamente. Este gate é uma verificação pontual. Mesmo com HTTP 200 e hashes iguais, HTML pode estar inacessível, mal interpretado ou cientificamente incorreto. O mecanismo não monitora sistemas SAP/ECM, não gera OS e não autoriza manutenção.

Os 13 gates externos do estudo continuam pendentes. Os PRs de pesquisa permanecem em revisão e **não devem ser integrados automaticamente**.

**Decisão:** `NO GO` para operação, mesmo com implantação HTML validada.
