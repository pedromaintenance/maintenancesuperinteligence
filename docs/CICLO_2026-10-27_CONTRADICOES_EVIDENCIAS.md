# Ciclo 22 — Contradições de evidência e revisão cruzada das dependências

**27/10/2026 · P&D v2.2.0 · Issue #44**

## Objetivo

O Ciclo 22 acrescenta uma camada de **detecção de inconsistência documental simulada e propagação de reabertura** sobre a sequência de evidências dos Ciclos 20 e 21. O sistema identifica condições em que duas declarações fictícias são incompatíveis, compara revisões e aponta quais controles dependentes deveriam ser novamente examinados por responsáveis competentes.

**Nada foi observado em campo.** As seis situações são exercícios versionados, não achados de inspeção, eventos corporativos, erros de identidade realmente detectados, falhas OEM confirmadas ou defeitos mecânicos. O resultado permanece `no_go` em todas as execuções públicas.

## Cenários obrigatórios

| Caso sintético | Afirmações contraditórias hipotéticas | Revisão cruzada proposta |
| --- | --- | --- |
| `SIM-CONFLICT-01` | Principal único versus aparente duplicação de pessoa | TI ↔ Engenharia |
| `SIM-CONFLICT-02` | Competência vigente versus credencial expirada | Engenharia ↔ TI |
| `SIM-CONFLICT-03` | Revisão OEM vigente versus publicação supersedida | Engenharia ↔ Gestão de Manutenção |
| `SIM-CONFLICT-04` | Configuração inalterada versus arranjo alterado | Gestão de Manutenção ↔ Engenharia |
| `SIM-CONFLICT-05` | Parecer editorial que apoia versus parecer que contesta | Engenharia ↔ Segurança da Informação |
| `SIM-CONFLICT-06` | Retenção autorizada versus ausência de base legal/retenção aprovada | Jurídico ↔ Segurança da Informação |

Cada cenário possui dois objetos `EvidenceConsistencyAssertion`, ambos com `origin=fictional_hypothesis_only`, `observed=false`, `authenticated=false`, documento de origem nulo, identidade nula e revisões de contexto/documento explicitamente fictícias 1 e 2. O par contém uma contradição **definida pelo fixture editorial**; o motor não faz inferência semântica geral a partir de texto livre nem emite diagnóstico sobre evidência real.

## Grafo de dependências e cascata de reabertura

O grafo de origem possui **13 controles e 17 vínculos** conforme o contrato do Ciclo 20 e a ordenação topológica do Ciclo 21. Cada cenário indica dois controles iniciais, e o algoritmo `descendant_cascade` percorre, por arestas reversas de precedência, o fecho transitivo de dependentes.

Exemplo: uma revisão OEM hipoteticamente substituída exige reavaliar `oem-effectivity`, sua relação com `equipment-configuration` e dependências posteriores como `operational-firewall`. Uma lacuna na política de retenção pode se propagar a `evidence-legitimacy`, `oem-effectivity` e controles operacionais.

A lista resultante é ordenada pela sequência topológica original, não por pontuação de gravidade, duração, custo ou probabilidade. Não é um plano de serviço. O algoritmo **não descarta hipóteses mecânicas, condena componentes, infere teste efetuado ou remove outras dependências**. Cada controle afetado passa conceitualmente ao estado de reavaliação externa, ainda `unverified`.

Se o grafo upstream perder uma aresta obrigatória ou houver mudança na ordenação canônica, o processamento é recusado. Em produção real, versões de documentos, credenciais e registros de configuração precisariam de assinatura/identidade autenticadas e fonte técnica autorizada, inexistentes aqui.

## Perguntas de revisão cruzada

A matriz de revisão possui seis objetos `CrossFunctionalReviewQuestion`. Cada pergunta define área primária, área contraparte, controles de origem/destino e o ponto a verificar. Todos os campos de resposta permanecem `external_review_not_performed` ou `not_available`, com `answeredByRealPerson=false` e `approvalGranted=false`.

Uma área não concede alçada à outra automaticamente. É necessário impedir que uma confirmação documental de TI seja interpretada como validação mecânica de uma publicação OEM, ou que a recomendação de Engenharia seja confundida com autorização de operação ou acesso SAP.

## Achados, prova obsoleta e estados

O `ContradictionFinding` possui sempre `hypothetical_inconsistency_to_investigate`, `realWorldConflictConfirmed=false`, `mechanicalFailureConfirmed=false`. Dois objetos `StaleProofInvalidation` por cenário demonstram que declarações de versão anterior não podem sustentar decisão sem revalidação, mas não são classificados como prova de falha física.

O `DependencyReopenCascade` registra raízes, descendentes, contagem, exigência de revisão e bloqueio de operação. O `NoGoDisposition` exige prova externa, nova verificação de versão e revisão humana autenticada, mantendo proibição explícita de enviar SAP, alterar ECM, criar OS ou liberar equipamento.

Estados como `approved`, `go`, `real_fault_confirmed` ou `evidence_verified` não são emitidos no corpus público. Não existe fluxo para iniciar piloto real.

## Contratos e ferramentas

- `pilot/evidence-contradictions.v1.json`: seis pares conflitantes, seis perguntas e política obrigatória de `no_go`.
- `pilot/evidence_contradictions.py`: validação estrita e montagem determinística, cálculo de descendentes, prova de origem pública e exportações JSON/HTML offline.
- `tests/test_evidence_contradictions.py`: regressões de cascata, independência entre ramos, OEM substituído, competência, revisão adulterada, conflito omitido, fonte não autorizada, falsa identidade, aprovação humana e manipulação do grafo.
- **Dez JSON Schemas**: `EvidenceConsistencyAssertion`, `CrossFunctionalReviewQuestion`, `ContradictionFinding`, `StaleProofInvalidation`, `DependencyReopenCascade`, `NoGoDisposition`, fixture, cenário e envelopes de resultado/relatório.
- GitHub Actions: gera relatórios JSON/HTML, reconstrói integralmente os dossiês e pacotes canônicos, verifica o resultado, inspeciona estados de autoridade e rejeita seis variantes adversariais de fixture.

Os hashes SHA-256 indicam identidade de conteúdo para testes de regressão, **não** assinatura digital, imutabilidade externa, cadeia de custódia corporativa ou prova técnica independente.

## Execução local

Após gerar o snapshot FMEA público pinado, pacote Go/No-Go e sequência do Ciclo 21:

```bash
python -m unittest discover -s tests -v

python -m pilot.evidence_contradictions \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --sequence build/sequencing/evidence-sequence.v1.json \
  --gng build/go-nogo/no-go-report.v1.json \
  --output build/contradictions/contradictions.v1.json \
  --html build/contradictions/contradictions.v1.html
```

A CLI compara as fontes com uma reconstrução determinística do material público versionado, e recusa dados alterados, incluindo texto confidencial, documento/usuário real, mudança de dependências, evidência marcada como observada ou pretendida aprovação. HTML é estático com CSP, sem JavaScript, formulário, login ou rede.

## Limites e próximos passos

Nenhum manual OEM licenciado, identificador ou número de série de equipamento real, amostra de óleo, telemetria, dado SAP, credencial, dado pessoal ou assinatura foi incluído. Os responsáveis e perguntas são referências propostas de governança, sem aceites externos. A reabertura de controle **não mede** risco operacional nem autoriza qualquer decisão de manutenção.

O próximo candidato de P&D é analisar a **cobertura dos cenários e a qualidade das explicações da cascata**: verificar se cada dependência importante recebe justificativa rastreável e se diferentes mudanças hipotéticas conduzem aos mesmos estados de veto sem omissões. Isso pode ser feito no repositório público com dados inteiramente fictícios, sem fingir validação de campo.
