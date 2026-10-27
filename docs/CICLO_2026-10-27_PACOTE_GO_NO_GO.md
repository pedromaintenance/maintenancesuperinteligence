# Ciclo 20 — Pacote Go/No-Go para um futuro piloto privado

**27/10/2026 · P&D v2.0.0 · Issue #40**

## Objetivo e decisão

O Ciclo 20 converte os controles do Ciclo 19 em um plano auditável de **evidência a obter, dependências, responsáveis propostos e critérios de veto** para avaliar um eventual piloto de revisão técnica em ambiente privado. Não implementa plataforma corporativa, acessos autenticados, cadastro SAP nem validação de operação em equipamentos.

**Decisão inequívoca dos cenários públicos:** `no_go`. São 13 pacotes de evidências não submetidos, 17 vínculos de dependência entre controles, cinco aceites externos sem assinatura e dez ameaças com mitigação não verificada. Esses números descrevem requisitos documentais e casos sintéticos, não observações de campo.

### Estados permitidos

| Estado | Significado no exercício |
| --- | --- |
| `requirements_defined` | Requisitos, fontes e donos propostos registrados |
| `evidence_not_submitted` | Nenhuma evidência privada encaminhada |
| `externally_review_pending` | Pendente de revisão competente fora do GitHub |
| `no_go` | **Veto à implantação ou operação real** |

Os estados `go`, `operationally_ready` e `approved` são expressamente proibidos neste repositório. Não existe função para trocar `no_go` por autorização. Qualquer futuro projeto real precisará de sistema e aprovações privados independentes.

## Matriz de dependência e aceite

| Área proponente | Controles | Evidência externa necessária |
| --- | --- | --- |
| **TI** | identity-proof, version-lock, revocation-reopen | Identidade corporativa única, revisão vigente e revogação efetiva |
| **Segurança da Informação** | signed-decision, trusted-audit | Integridade/autoria validadas externamente, auditoria protegida e tempo confiável |
| **Engenharia** | competence, two-independent-reviews, oem-effectivity | Formação/competência verificadas, revisores independentes e OEM com revisão/efetividade por configuração/série |
| **Jurídico** | conflict-screen, evidence-legitimacy, privacy-retention | Conflitos, licença, finalidade/base legal, classificação, retenção e restrição de compartilhamento |
| **Gestão de Manutenção** | equipment-configuration, operational-firewall | Histórico e arranjo vigente; revisão documental isolada de OS, peças, ECM e liberação |

O arquivo `pilot/go-nogo-package.v1.json` explicita dependências entre controles. Por exemplo: os dois pareceres independentes dependem de competência, impedimentos e versão documental; a autorização de uma publicação OEM por série depende de configuração e legitimidade da evidência. O validador recusa dependências trocadas, omissões, ciclos e qualquer afirmação de comprovação no ambiente público.

## Contratos publicados

1. `EvidenceSubmissionManifest`: ID fictício da evidência, categoria, controle, sem arquivo ou referência corporativa.
2. `AcceptanceReview`: área responsável, controles sob sua alçada, revisão externa ainda pendente e veto.
3. `GoNoGoDecision`: decisão `no_go`, estado das evidências e assinaturas ausentes.
4. `ApprovalDependency`: predecessores de cada controle e negação de avanço sem prova.
5. `FindingRemediation`: falha/ameaça, correção futura esperada, sem nome de pessoa, prazo inventado ou aceite.
6. `NoOperationalAuthority`: recusa explícita de registro SAP, modificação ECM, requisição de material, aprovação mecânica e liberação.

Os contratos adicionais cobrem desenho de estudo, classificação/retenção, controle, área, cenário adversarial, transição, pacote de entrada, gates e relatório. São **15 novos JSON Schemas** no total.

## Ameaças e correções esperadas

Os dez cenários de regressão derivam da matriz do Ciclo 19: principal duplicado sob IDs diferentes, credencial expirada, assinatura forjada, revisão OEM substituída, mudança de arranjo de máquina, conflito oculto, nota SAP indevida, vazamento de PII/telemetria, adulteração de auditoria e cópia de manual sem licença.

Todos resultam em `no_go` e `external_evidence_and_independent_review_required`. O sistema não interpreta o teste como falha ocorrida em mina. Evidências e identidade ainda não existem no repositório.

## Procedimento metodológico futuro

Um piloto real **somente poderá ser avaliado após projeto corporativo autorizado**. A proposta metodológica exige: definição de finalidade e base legal apropriada; política de informação aos participantes; classificação e minimização; coleta e amostragem justificadas; controle de qualificações e independência; rubrica documental congelada e revisada; avaliações cegas quando apropriado; tratamento de divergências; validação de segurança e efetividade OEM por máquina; e análise estatística escolhida **conforme o tipo de escala**.

Para categorias nominais e dois avaliadores, pode-se considerar Cohen's kappa; para categorias ordinais, medida ponderada; para múltiplos avaliadores ou situações com dados ausentes, escolher método com justificativa própria. Não atribuir estimativa de concordância, acurácia diagnóstica ou confiabilidade operacional sem dados reais autorizados e método apropriado. O projeto não coleta esses dados.

## Fontes e limites

- **NIST SP 800-63-4**: https://csrc.nist.gov/pubs/sp/800/63/4/final — identidade digital, autenticação e federação.
- **OWASP ASVS 5.0.0**: https://asvs.owasp.org/ — requisitos de segurança de aplicações.
- **LGPD, Lei 13.709/2018**: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm — princípios e requisitos de tratamento, sujeitos a avaliação jurídica no contexto real.
- **Efetividade OEM**: ainda **não comprovada**; exige documentação autorizada por fabricante, modelo, arranjo, série, revisão e pessoal tecnicamente habilitado. NIST/OWASP/LGPD não conferem essa efetividade.

Dados privados SAP, laudos de óleo, telemetria, manuais licenciados, registros de pessoas, credenciais, números de série reais e evidências físicas permanecem proibidos no repositório público. Retenção continua nula até política privada aprovada. SHA-256 é apenas mecanismo de comparação de conteúdo sintético; não equivale a assinatura ou custódia imutável.

## Execução e critérios de aceite sintético

Depois de produzir as entradas dos Ciclos 13–19:

```bash
python -m unittest discover -s tests -v

python -m pilot.go_nogo \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --readiness build/pilot/readiness-report.v1.json \
  --output build/go-nogo/no-go-report.v1.json \
  --html build/go-nogo/no-go-report.v1.html
```

O programa reconstrói os dossiês e relatórios canônicos desde o FMEA público pinado, rejeitando relatórios alterados antes da exportação. Os resultados JSON/HTML não contêm conexão, formulário, senha ou autorização SAP. O GitHub Actions verifica o mesmo fluxo e os casos negativos: falso aceite, transição `go`, permissão SAP, OEM ficticiamente validado, retenção não autorizada e concordância estatística fabricada.

A completude desta entrega é **de contrato e governança simulada**, não de implantação. Para qualquer futuro passo operacional, um sistema restrito independente deverá produzir identidade real, assinaturas, logs, validação OEM, evidência física, autorização jurídica e regras de segurança específicas.
