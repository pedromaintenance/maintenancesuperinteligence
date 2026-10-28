# Ciclo 34 — Matriz de evidências discriminantes

**P&D 3.4.0 · 28/10/2026.** Continuação da taxonomia técnica do Ciclo 33; sem validação mecânica de campo.

## Pergunta técnica

Como registrar quais achados *poderiam* favorecer ou enfraquecer uma hipótese e quais achados não permitem distingui-la, sem transformar plausibilidade em causa raiz confirmada?

## Fronteira semântica

A estrutura do Ciclo 33 (`knowledge/mechanical-evidence-map.v1.json`) permanece fonte de identificação de função, falha funcional, hipótese ou confundidor, pergunta discriminante e bibliografia geral. A matriz deste ciclo acrescenta condições editoriais **formuladas no condicional**, e não observações efetivamente realizadas em máquinas.

| Resultado qualitativo | Significado permitido | Interpretação proibida |
| --- | --- | --- |
| Favorece relativamente | Evidência hipotética compatível com a hipótese; outras causas continuam possíveis | Causa confirmada ou probabilidade percentual |
| Enfraquece relativamente | Evidência hipotética pode diminuir a prioridade explicativa da hipótese | Exclusão definitiva do mecanismo |
| Inconclusivo | Contexto insuficiente para diferenciar alternativas | Autorização para substituir componente |
| Favorece + enfraquece | Conflito que exige conciliação documental e revisão | Escolha automática da versão mais conveniente |

## Estrutura e cobertura

- **12 trilhas parentais** em comando final, hidráulica, eletrônica e arrefecimento; inclui **3 confundidores de interpretação**, não classificados como modos físicos de falha.
- **36 regras editoriais** (`DISC-001-1` até `DISC-012-3`): uma condicional favorável, uma contrária e uma inconclusiva por trilha.
- **48 cenários fictícios**: quatro por trilha — suporte isolado, enfraquecimento isolado, conflito e insuficiência.
- Cada resultado preserva `hypothesisStatus=open_unconfirmed`, `rootCauseConfirmed=false`, `observedEvidenceCount=0`, `mayExecuteTests=false`, `mayCreateWorkOrder=false`, `mayReleaseEquipment=false`.

## Exemplos de raciocínio causal

### Comando final

Uma diferença química entre duas análises de óleo pode ser compatível com alteração de formulação do lubrificante. Se o histórico confirmar produtos diferentes, a hipótese de diferença de baseline ganha plausibilidade documental. Se o histórico confirmar o mesmo produto, ela perde apoio relativo. Sem histórico confiável, o achado continua inconclusivo. **Nenhum dos três resultados comprova desgaste ou autoriza condenar o componente.**

### Hidráulica

Uma atuação lenta com relatos de espuma poderia sustentar investigação sobre gás incorporado ao fluido; se a documentação indicar alteração de carga e não sustentar aeração, a hipótese perde força relativa. A atuação lenta isolada não determina válvula, bomba, ar ou regime de carga.

### Eletrônica

Um código gravado só pode ser interpretado dentro do estado ativo/registrado e da cronologia de eventos da ECM aplicável. Um registro antigo pode ser um confundidor. Mesmo um código ativo em coincidência temporal **não confirma automaticamente defeito de chicote ou sensor**.

### Arrefecimento

Um bloqueio externo de passagem de ar documentado seria compatível com hipótese de rejeição térmica insuficiente. Aquecimento sob carga, sem caracterização da condição externa e do circuito, permanece inespecífico; a causa raiz exige novas evidências independentes.

## Referências e limitações

Os vínculos técnicos gerais permanecem aqueles explicitamente catalogados no [Ciclo 33](CICLO_2026-10-28_TAXONOMIA_MECANICA_FUNDAMENTADA.md): SKF, Caterpillar, HYDAC, Perkins e escopo público da ISO 15243. As frases condicionais, consequências e perguntas discriminantes deste ciclo são **inferências autorais** para pesquisa. Nenhuma dessas fontes certificou estas 36 regras para uma série OEM, nem revisou as 48 respostas fictícias. A matriz não mede probabilidade de falha, taxa de falsos positivos, precisão diagnóstica, repetibilidade entre engenheiros ou efeito de intervenção.

## Contratos e testes

- `knowledge/discriminating-evidence-matrix.v1.json` — regras hipotéticas e vínculos imutáveis aos IDs parentais.
- `knowledge/discrimination-scenarios.v1.json` — conjunto autoral de cenários com hipóteses não confirmadas.
- `knowledge/discrimination-policy.v1.json` — política de resultados permitidos e veto às alegações de aprovação.
- `knowledge/discriminating_evidence.py` — auditoria referencial, avaliador qualitativo e relatórios JSON/HTML.
- `contracts/discriminating-evidence-matrix.schema.json`, `contracts/discrimination-scenarios.schema.json`, `contracts/discrimination-policy.schema.json`, `contracts/discrimination-report.schema.json` — contratos.
- `tests/test_discriminating_evidence.py` — 10 grupos de testes de regressão, contrafactuais, conflito, fraude de medição, adulteração e saída HTML segura.

```bash
python -m unittest tests.test_discriminating_evidence -v
python -m knowledge.discriminating_evidence \
  --output build/benchmarks/cycle34-discrimination.json \
  --html build/benchmarks/cycle34-discrimination.html
```

## Próximos requisitos antes de considerar o modelo em campo

1. Especialista externo deve revisar direção, escopo, confundidores e relevância das 36 relações, incluindo situações que possam inverter a interpretação.
2. Um conjunto novo de casos deve incluir observações de campo legítimas, autorizadas e rastreáveis, custodiadas fora do repositório, com histórico de máquina e documentação OEM por série.
3. Medir concordância entre especialistas, erros críticos de inferência, abstenção correta e possíveis falsos positivos, preservando conflito sem votação automática.
4. Continuar proibindo qualquer saída que autorize intervenção, teste físico, pedido de peças, SAP ou liberação.

**Decisão do Ciclo 34:** demonstração editorial de discriminação qualitativa, `NO GO` diagnóstico e operacional.
