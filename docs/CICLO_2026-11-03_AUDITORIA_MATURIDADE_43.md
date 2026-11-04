# Ciclo 43 — Auditoria de maturidade, cobertura contrafactual e fronteiras de validade

**P&D v4.3.0 (proposta em branch) · 03/11/2026 · Baseline congelada da `main`: `604c9fa2f98393ca31bef5cf31c40a60566851e7`**

**Estado: NO GO para homologação diagnóstica ou autoridade operacional.** Este documento descreve um incremento de **auditoria de pesquisa**, não mais um avanço de autenticação, nem uma alegação de competência mecânica demonstrada.

## 1. Pergunta central

A plataforma possui ontologias, contratos, ferramentas de investigação, ensaios de governança e serviço HTTP isolado. Qual é a **classe de evidência** que sustenta cada afirmação de maturidade?

A resposta encontrada no código é assimétrica:

- **Implementado e testável:** seleção determinística de perguntas documentais, preservação de hipóteses concorrentes e abstenção; ensaios de negação segura em recursos inventados.
- **Implementado parcialmente:** disciplina de contratos e verificação de metadados; os 245 arquivos em `contracts/` na baseline não equivalem a 245 esquemas integralmente executados e cobertos. `scripts/validate.py` se apresenta corretamente como validação básica, não execução universal do JSON Schema.
- **Projetado, mas não demonstrado:** revisão mecânica independente, autorização por série OEM, eficácia diagnóstica e custódia de casos reais.
- **Bloqueado deliberadamente:** ações SAP, ECM, testes físicos, emissão de ordens e liberação de equipamentos.

Hash de um arquivo prova identidade *relativa ao conteúdo recebido*. Não prova identidade humana, direito de uso de literatura, medição física ou aprovação do fabricante.

## 2. Teste causal dos mecanismos efetivamente implementados

### 2.1. O que significa 24/24 no Ciclo 27

Os 24 cenários originais estão distribuídos em quatro famílias: comando final, hidráulica, eletrônica/ECM e arrefecimento. O algoritmo implementa uma ordem editorial de **quatro portas documentais por família**, com precedência para a contradição. Havendo todas as portas preenchidas, encaminha para análise especializada.

O gabarito está fisicamente separado em arquivo JSON, mas sua elaboração é **autoral**, orientada pela mesma política. Assim, **24/24 mede conformidade com essa política**, não sensibilidade, especificidade, precisão de predição, redução de indisponibilidade, seleção ótima de ensaio ou acerto de causa raiz.

Os próprios testes do Ciclo 27 cobrem transições específicas e mutações. Isso é bom para não regressão, mas não demonstra generalização causal.

### 2.2. Avanço específico do Ciclo 43

O novo programa `benchmarks/cycle43_readiness.py` verifica exaustivamente as 2 possibilidades de contradição combinadas às 16 combinações das quatro portas de cada domínio: **2 × 16 × 4 = 128 contextos sintéticos**. Ele confirma:

1. Contradições narrativas mantêm precedência sobre avanço na investigação;
2. A primeira lacuna documental conforme ordem autoral determina a próxima pergunta;
3. Contexto documental completo exige revisão especializada;
4. Nenhum percurso promove causa confirmada, probabilidade numérica, teste executado ou permissão operacional;
5. A saída mantém três hipóteses não confirmadas por família.

Isso aumenta a **cobertura estrutural de combinações lógicas**. Como a expectativa decorre da mesma definição de portas usada pelo seletor, permanece **teste de autoconsistência**; não deve ser rotulado como benchmark independente.

### 2.3. O que não foi testado

O módulo ainda não observa relações físicas como pressão × vazão × temperatura × perda de carga, dependência de ciclo/carga, efeitos de desgaste e contaminação, consequências de um teste invasivo, disponibilidade de instrumento, custo diagnóstico, qualidade metrológica ou assimetria de risco.

A seleção por primeira lacuna documental pode ser segura, mas não é necessariamente a escolha de **maior valor informacional**, menor custo, menor risco ou maior poder discriminante. Esse problema exige dados, hipóteses, custos/risco e casos revisados por especialistas.

## 3. Critérios de maturidade: não confundir classes de prova

| Proposição | Evidência no repositório | Limite |
| --- | --- | --- |
| Seletor segue sua regra autoral | Código, 24 casos e testes; 128 novos contextos | Não mede acerto de diagnóstico |
| Há fontes e contratos auditáveis | Inventário de arquivos e hashes | Não autentica fontes externas |
| Existe protocolo de revisão técnica | Ciclos 29 e 37 e modelos de parecer | Não há revisores independentes de fato |
| Autorização sintética falha de forma segura nos ensaios | Ciclos 40–42 | Não é ambiente corporativo, TLS/mTLS ou prova de segurança OT |
| Existe preparação para P&D vertical | Casos fictícios e árvores | Não há parecer OEM por série nem caso de campo homologado |

### Gatilhos que mantêm NO GO

Qualquer declaração de *causa confirmada*, acurácia diagnóstica, revisão humana concluída, identidade empresarial validada, acesso a documento privado, efeito OEM verificado, teste autorizado ou liberação operacional sem evidências válidas deve ser rejeitada.

O relatório carrega esses limites expressamente e sua reconstrução é testada contra adulterações.

## 4. Backlog aberto — reconciliação baseada no escopo

Snapshot GitHub de 03/11/2026; **não é consulta dinâmica a issues** no programa offline.

| Issue | Situação na auditoria | Próximo passo |
| --- | --- | --- |
| #1 — Ontologia e schemas | Revisar critérios de aceite antigos frente à evolução real | Inventariar schemas aplicados, casos negativos, referências e estados de revisão; fechar somente escopo verificável |
| #4 — 56 competências | Aberta | Mapear habilidades para tarefas, rubricas e progresso educacional sem equivaler pontuação a habilitação profissional |
| #5 — Governança | Aberta | Separar controles sintéticos de auditoria independente, conformidade real e responsabilidades institucionais |
| #50 — Dossiês do grafo | Parcialmente implementada conforme documentação do Ciclo 25 | Verificar exigências aninhadas, autenticidade e revisão humana; histórico dos Ciclos 25–26 não autoriza encerramento automático |

**Regra de governança:** nenhum script do Ciclo 43 altera issues, fecha backlog ou muda evidências originais automaticamente. A revisão requer confirmação dos critérios pelos responsáveis.

## 5. Ferramentas e artefatos

- `benchmarks/cycle43-readiness.v1.json` — recorte explicitamente congelado, estado de cinco claims, quatro issues e dez negações;
- `benchmarks/cycle43_readiness.py` — valida inventário, calcula hashes, verifica 24 expectativas autorais e 128 combinações, emite JSON e Markdown;
- `tests/test_cycle43_readiness.py` — testes negativos de promoção indevida, travessia de paths, lacunas, issue encerrada, saída falsificada e seletor inseguro;
- `.github/workflows/cycle43-readiness.yml` — CI independente, **sem segredos**, com execução offline e sem alteração de ambientes externos;
- Este relatório.

### Reproduzir

```bash
python -m unittest tests.test_cycle43_readiness -v
python -m benchmarks.cycle43_readiness \
  --output build/benchmarks/cycle43-readiness.json \
  --markdown build/benchmarks/cycle43-readiness.md
```

**Atenção:** o inventário usa os arquivos da árvore executada. As referências a issues são um snapshot editorial, não estados confirmados em tempo real. Uma atualização futura do baseline exige novo ciclo ou nova versão de contrato, nunca reescrever silenciosamente a prova histórica.

## 6. Riscos remanescentes e ordem proposta

1. **Circularidade metodológica (prioridade máxima):** conseguir casos inéditos e pareceres efetivamente independentes, com custódia externa ao autor do seletor. Registrar discordância entre avaliadores.
2. **Validade mecânica:** criar banco de casos por função, requisito, sintoma, condição, hipótese, evidência discriminante e estado de causa, sem extrair informação privada para GitHub público.
3. **Confiabilidade da cadeia de conhecimento:** ampliar validação de schemas com referências aninhadas, instâncias positivas e negativas, e cobertura por contrato realmente usado.
4. **Manutenibilidade do CI:** estudar a decomposição do `.github/workflows/validate.yml` (aprox. 134 KB na baseline) e testar se os gates ficam mais claros, sem remover controles existentes.
5. **Governança de issues:** recompor backlog por entregável e dependência, sem confundir implementação parcial com aceite institucional.
6. **Segurança:** preservar laboratório HTTP como prova sintética, e não transportar seus tokens, endpoints de fault injection e mecanismos de sessão para produção.

## 7. Próxima decisão técnica (Ciclo 44 candidato)

**Corpus cego de plausibilidade e perguntas discriminantes**, inicialmente sintético e externamente revisável:

- conjunto de casos inéditos sem gabarito no pacote entregue ao avaliador;
- fonte, escopo, contexto e limitações por cenário;
- critérios de julgamento definidos *antes* da análise;
- no mínimo dois pareceres independentes, quando efetivamente obtidos;
- análise de concordância e discordância com intervalos de confiança adequados ao tamanho amostral;
- comparação com baseline simples (primeira lacuna documental) e, quando aplicável, estratégia de valor informacional;
- manutenção de NO GO até comprovação de autoria, competência, custódia, efetividade e permissões.

Não armazenar casos empresariais, catálogos OEM licenciados, segredos, dados SAP ou telemetria identificável no repositório público.

## Conclusão

O Ciclo 43 **não prova que a plataforma diagnostica falhas**. Entrega uma fronteira verificável entre:
(1) regra codificada e testada;
(2) raciocínio mecânico plausível;
(3) evidência diagnóstica validada;
(4) autorização institucional e operacional.

**Resultado esperado e decisão:** `no_go_independent_validation_not_performed`. O desenvolvimento deve continuar com validação de conhecimento mecânico, não por crescimento indiscriminado de contratos.
