# Ciclo 44 — Ensaio de discriminação mecânica e pré-registro de avaliação externa

**P&D v4.4.0 (proposta em branch, sobre Ciclo 43) · 03/11/2026**

**Decisão obrigatória:** `no_go_symbolic_discrimination_not_validated_in_field`. O ciclo não comprova investigação causal eficaz, não recebe revisores humanos, não usa documentação OEM específica e não autoriza testes, compras, SAP, ECM ou liberação de equipamento.

## 1. Por que este ciclo foi necessário

O Ciclo 27 implementou uma boa proteção contra afirmar causa sem evidência, mas a escolha da próxima pergunta depende de uma ordem autoral de lacunas documentais. O Ciclo 43 expandiu a verificação dessas regras a 128 combinações estruturais. **Nenhum desses números mede se determinada pergunta realmente separa duas hipóteses físicas.**

Já existem soluções importantes nos Ciclos 29–32:

- Ciclo 29: simulação editorial de revisão cega, cujo gabarito continua publicamente acessível;
- Ciclo 30: `benchmarks/heldout_study.py` com casos e gabarito privados, congelamento, HMAC e duas submissões, sem autenticação real de revisores;
- Ciclos 31–32: qualidade de conjuntos e checagem de vazamento entre divisões; as linhagens e fontes seguem autodeclaradas;
- Ciclo 37: protocolo de duas revisões técnicas e adjudicação, mas sem pessoas efetivamente verificadas.

**Logo, não duplicamos a custódia.** O Ciclo 44 ensaia uma variável ainda pouco explorada: o potencial de uma pergunta *hipotética* discriminar hipóteses rivais, sem convertê-la em teste autorizado.

## 2. Objeto de comparação

O estudo público contém oito cenários artificiais, dois para cada domínio: comandos finais, hidráulica, eletrônica/ECM e arrefecimento. Cada cenário mantém **três hipóteses não confirmadas** e **três perguntas documentais**:

1. **Baseline:** pergunta de contextualização documental, utilizada como referência, mas não presumida fisicamente suficiente;
2. **Alternativa hipotética:** pergunta que, se as previsões autorais fossem válidas, distinguiria parte das hipóteses;
3. **Candidato documentalmente indisponível:** uma pergunta cuja capacidade de separar hipóteses parece superior em papel, porém seu pré-requisito fictício não está documentado.

As respostas possíveis são símbolos inventados (`group_a`, `group_b`, `group_c`), sem pressão, vazão, temperatura, componentes condenados, limites OEM, valores de probabilidade, medições ou dados operacionais. **São partições editoriais, não resultados observados.**

### Métrica calculável, e seus limites

Para três hipóteses existem três pares não ordenados. Para uma pergunta com todas as respostas simbólicas disponíveis, calculamos:

`P(q) = número de pares (Hi,Hj) em que a previsão simbólica é distinta`.

`P(q)` pertence ao intervalo inteiro de 0 a 3. Se faltar a previsão de alguma hipótese, a pergunta não recebe pontuação. Essa contagem não é entropia, ganho de informação de Shannon, valor esperado de teste, probabilidade posterior, sensibilidade, especificidade ou confiabilidade.

Para os quatro cenários sem contradição, a fixture foi construída com baseline simbólica 0/3, alternativa elegível 2/3 e candidato indisponível 3/3. Assim, o ensaio verifica **seleção sob uma restrição de pré-requisito**, não uma melhoria efetiva de 2/3 observada em máquinas.

Para os outros quatro cenários, a fonte fictícia tem contradição não resolvida. **Nenhuma pergunta recebe recomendação de ranking**, mesmo se uma delas teria partição teórica 3/3.

Se houver empate na maior contagem, o algoritmo se abstém: não inventa vantagem de segurança, custo ou eficiência para desempatar. Se houver ausência de previsão, não exclui hipótese e não transforma lacuna em resultado negativo.

## 3. Entregáveis reproduzíveis

| Artefato | Finalidade |
| --- | --- |
| `benchmarks/cycle44-symbolic-trials.v1.json` | Oito casos sintéticos, sem fatos de campo |
| `benchmarks/cycle44_discrimination.py` | Validação fechada, cálculo de pares, elegibilidade, abstenção e relatório offline |
| `tests/test_cycle44_discrimination.py` | Cobertura de conflito, ausência de previsão, pré-requisito, empate, adulteração e autorizações falsas |
| `contracts/cycle44-trials.schema.json` | Formato tipado dos cenários com negações estruturais |
| `contracts/cycle44-report.schema.json` | Formato tipado de saída e decisão NO GO |
| `.github/workflows/cycle44-discrimination.yml` | Teste isolado e artefatos públicos exclusivamente fictícios |

```bash
python -m unittest tests.test_cycle44_discrimination -v
python -m benchmarks.cycle44_discrimination \
  --output build/benchmarks/cycle44-discrimination.json \
  --markdown build/benchmarks/cycle44-discrimination.md
```

O programa não lê repositórios externos, laudos, SAP, ECM, credenciais, dados empresariais ou internet.

## 4. Como transformar esta pesquisa em um estudo independente de verdade

O primeiro estudo humano **não ocorrerá neste repositório público**. Deve aproveitar a infraestrutura já criada nos Ciclos 30–32 e acrescentar estas condições mínimas:

**A. Pré-registro e custódia.** O custodiante independente registra *antes* da coleta os objetivos, critérios de inclusão/exclusão, estratos por sistema, critérios de falha crítica, tamanho amostral justificado, baseline congelada, política para faltantes e método de análise. Casos inéditos, gabaritos e dados identificáveis ficam em repositório/ambiente privado autorizado.

**B. Engenharia dos casos.** Os casos devem expor função e requisito, condição de operação, sintomas, hipóteses rivais, evidência disponível, contraprova e aplicabilidade do conhecimento. É indispensável distinguir cenário didático, evidência física de caso autorizado e verdade causal adjudicada. Caso não exista verdade verificada, não rotular como caso de diagnóstico correto/incorreto.

**C. Comparação cega pareada.** Para cada caso, os avaliadores recebem duas perguntas candidatas em ordem randomizada, sem saber qual foi produzida pelo método base e qual veio do seletor experimental. É necessário evitar vazamento de redação ou pistas óbvias de origem. As propostas devem permanecer apenas orientações de investigação sujeitas a autorização; não são instruções de execução.

**D. Pareceres externos.** Dois especialistas qualificados, sem conflito declarado, avaliam independentemente: capacidade de separar mecanismos, pertinência da fonte, proporcionalidade do esforço, segurança, mensurabilidade, condições de validade e quando se abster. Divergências são registradas literalmente e encaminhadas a adjudicador terceiro, sem mascaramento como consenso. Os controles de autenticidade/identidade são externos ao código atual.

**E. Medições pré-registradas.** Registrar, com numerador e denominador, preferência cega entre perguntas, casos empatados, abstenções justificadas, perguntas inseguras, ausência de efeito OEM, discordância interavaliadores e taxa de não avaliáveis. Reportar incerteza e tamanho da amostra. Sem verdade física, não usar a expressão 'acurácia diagnóstica'. Medir desfechos de manutenção somente em futura pesquisa autorizada e comparável.

**F. Critérios de suspensão.** Uma recomendação que ignore condição de segurança, alegue especificação OEM inexistente, induza teste invasivo não autorizado, suprima hipótese rival ou invente evidência deve ser rejeitada, ainda que pontue bem em uma medida de discriminação.

## 5. Ataques adversariais previstos

- **Partição perfeita mas indisponível:** a melhor pergunta em papel não possui pré-requisito; não selecioná-la.
- **Fonte contraditória:** bloquear a comparação, mesmo diante de três resultados simbólicos distintos.
- **Previsão incompleta:** valor desconhecido não é resultado negativo.
- **Empate:** não fabricar vantagem estatística, custo ou segurança.
- **Falso aval humano:** nenhum campo pode converter a simulação editorial em revisão externa.
- **Promoção operacional:** testes, ordens, parâmetros ECM e liberação permanecem proibidos.
- **Sobrecarga de números:** não confundir pares separados com probabilidade, ganho de disponibilidade ou acurácia.

## 6. Próxima fronteira

O Ciclo 44 avança de uma *ordem fixa de perguntas* para um **contrato verificável de potencial discriminante sob premissas explícitas**. Porém as próprias premissas continuam inventadas. O próximo ciclo não deve aumentar a quantidade de cenários autorais apenas para melhorar métricas.

A entrega com maior valor agora será integrar a comparação cega pareada aos pacotes privados dos Ciclos 30–32, acrescentando custódia de preferências, métricas de discordância e protocolos de adjudicação externos, sem publicar dados sensíveis e **sem alegar avaliação humana até que ela realmente aconteça**.
