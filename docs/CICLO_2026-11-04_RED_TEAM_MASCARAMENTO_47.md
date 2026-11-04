# Ciclo 47 — Red team de mascaramento e proveniência documental

**P&D v4.7.0 · 04/11/2026 · proposta em branch dependente do Ciclo 46.**

**Decisão: NO GO.** Nenhum caso mecânico real foi diagnosticado, nenhum especialista independente participou, nenhum documento OEM por número de série foi homologado e nenhum teste ou intervenção foi autorizado.

## 1. Problema e contexto

Os Ciclos 30–32 implementaram a custódia privada e a verificação de qualidade dos lotes; o Ciclo 45 separou perguntas A/B sem indicar de qual método vieram; o Ciclo 46 acrescentou sinais simples de divulgação do método e a fila de pendências de adjudicação. Mesmo assim, uma pergunta aparentemente inocente pode trazer texto com caracteres invisíveis, alfabetos misturados ou instruções dirigidas ao revisor. E uma origem documental declarada "unverified" pode ser mascarada por um consenso artificial entre dois aliases.

O objetivo do Ciclo 47 é **red team de entrada textual e do estado documental**, não executar avaliação técnica independente nem escolher perguntas vencedoras.

## 2. O que é implementado

`benchmarks/cycle47_evidence_leakage.py` executa uma auditoria reprodutível e **somente de leitura** sobre as entradas privadas do Ciclo 45 e o handoff do Ciclo 46. Antes de analisar qualquer pergunta, exige que o Ciclo 46 reconstrua o handoff completo, incluindo o HMAC privado e a qualidade de dados dos Ciclos 30–32. Um handoff falsificado não é promovido.

A política `governance/cycle47-adversarial-policy.v1.json` é publicada e congelada nesta versão: o código não ajusta silenciosamente a sensibilidade em favor de melhores resultados.

### Verificações de texto

| Código | Exemplo fictício | Limite |
| --- | --- | --- |
| `hidden_unicode_control` | Caracteres Unicode invisíveis, como separadores de largura zero | Uma ocorrência pode ser legítima, não prova ataque |
| `mixed_script_confusable` | Texto latino misturado com letras visualmente semelhantes do cirílico ou grego | Heurística de mistura, não detecção completa de homoglifos |
| `obfuscated_method_origin_cue` | Termos que revelam o método, mesmo com separação artificial | Pode gerar falso positivo; não compreende semântica |
| `instructional_contamination` | Expressões que instruem o revisor a ignorar orientações ou responder de modo específico | Procura padrões; não demonstra intenção ou exploração real |
| `near_duplicate_question_pair` | Duas perguntas com Jaccard de tokens ≥ 0,9 | Semelhança lexical pode ocultar diferença diagnóstica relevante |
| `candidate_identifier_leak` | ID interno do método revelado dentro do texto A/B | Baseia-se apenas em igualdade textual, não verifica outros códigos implícitos |

O output **não reproduz o texto das perguntas**, apenas IDs custodiais, domínios, códigos de alerta e hashes dos documentos de base. A saída continua privada.

**Esses controles não são compreensão semântica nem prova de cegamento efetivo.** É possível induzir um revisor por vocabulário, complexidade, estilo ou contexto sem acionar nenhum código. Uma revisão humana independente continua indispensável.

### Verificações de proveniência

O auditor mantém separadamente três condições:

1. `synthetic_evidence_only`: a entrada é um exercício inventado, não uma observação real de manutenção;
2. `documentary_source_not_verified`: o estado documental é não verificado, contraditório, obsoleto ou revogado;
3. `oem_effectivity_not_verified`: inexiste confirmação de literatura aplicável à configuração e ao número de série.

Esses avisos são **necessidade de evidência ou revisão**, não demonstração de falsidade técnica. A própria arquitetura de casos do Ciclo 30 estabelece `oemEffectivityVerified=false` mesmo quando um caso tem origem autorizada. O Ciclo 47 **não inventa um mecanismo para alterar esse campo**.

## 3. Regras de decisão

A precedência do estado do caso é:

- Já havia necessidade de adjudicação no Ciclo 46? Mantém `pending_external_adjudication`.
- A origem documental permanece limitada? Marca `blocked_documentary_provenance`.
- Surgiram apenas alertas textuais adicionais? Marca `pending_external_blinding_review`.
- Nenhum desses alertas foi identificado? Marca `pending_external_validation_no_go`.

Todos os estados incluem `requiresExternalReview=true`. Nenhuma transição autoriza aceite, intervenção, teste físico, alteração ECM, emissão de OS, escrita SAP ou liberação de equipamento.

A regra de prioridade *não* afirma que um caso com fonte incompleta deva dispensar análise de segurança: os alertas são preservados separadamente, inclusive quando o estado principal é bloqueio de proveniência.

## 4. Exercícios adversariais

A suíte `tests/test_cycle47_evidence_leakage.py` fabrica em memória quatro casos sem dados de máquinas, com múltiplos ataques de redação e contexto. Inclui:

- `ba​seline` com caractere invisível e `ex-perimental` com separação;
- letra cirílica visualmente parecida com uma letra latina;
- mensagem adversarial de instrução inserida na pergunta;
- ID interno do candidato exposto no texto;
- duas perguntas quase idênticas;
- tentativa de trocar política, HMAC, handoff ou estado de autoridade;
- reconstrução de ponta a ponta de pacote A/B artificial adulterado, para conferir sinalização adicional;
- CLI em diretório temporário privado, impedindo sobrescrever relatórios.

Uma resposta red team bem-sucedida significa **que o filtro detectou o ataque inventado**. Não significa que detectará todos os ataques possíveis ou que validará perguntas mecânicas genuínas.

## 5. Artefatos

- `benchmarks/cycle47_evidence_leakage.py` — auditor e CLI privados;
- `governance/cycle47-adversarial-policy.v1.json` — política de triagem congelada;
- `contracts/cycle47-adversarial-policy.schema.json` — contrato tipado da política;
- `contracts/cycle47-readiness-report.schema.json` — contrato de saída, com negações operacionais;
- `tests/test_cycle47_evidence_leakage.py` — cenários sintéticos e adulterações;
- `.github/workflows/cycle47-evidence-leakage.yml` — CI sem segredos, uploads ou casos privados;
- este relatório, além de README e ROADMAP atualizados.

### Reprodução

```bash
python -m unittest tests.test_cycle47_evidence_leakage -v
```

A CLI exige arquivos privados da mesma execução dos Ciclos 45 e 46, com as opções `--source`, `--candidates`, `--quality-metadata`, `--quality-policy`, `--packet`, `--lock`, `--quality-receipt`, `--key`, `--submission-a/b`, `--receipt-a/b`, `--handoff` e `--output`. As políticas dos Ciclos 46 e 47 são carregadas do repositório e podem ser fornecidas explicitamente por caminho. **A saída continua fora do checkout público.**

## 6. Implicações materiais e limitações

- Os dados das provas e seus metadados não são autenticados pelo GitHub. A restrição de caminhos reduz vazamentos acidentais; **não é sandbox de execução nem controle de acesso institucional**.
- Capturar termos de origem não equivale a detectar viés semântico. Serão necessários revisores que examinem a efetiva neutralidade das perguntas.
- Similaridade textual não mede valor de informação, custo de ensaio ou risco operacional. O par aparentemente semelhante pode representar testes fisicamente diferentes.
- Duas submissões artificiais e HMAC não representam pareceres assinados por engenheiros.
- Nenhuma métrica de desempenho físico ou estatística de acurácia diagnóstica foi medida.
- O acúmulo de ciclos sintéticos não deve se tornar substituto de evidência real. **As próximas entregas com maior valor envolvem aprovação institucional, fontes autorizadas e avaliação independente — não simplesmente mais casos fictícios.**

**Status formal:** `no_go_masking_and_provenance_not_independently_validated`.
