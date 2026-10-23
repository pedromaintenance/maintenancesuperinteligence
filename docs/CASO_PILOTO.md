# Caso-piloto: monitoramento e diagnóstico de comando final

**Natureza:** cenário **didático e hipotético**. Não é um laudo de frota, condição atual de máquina, instrução OEM nem recomendação de manutenção efetiva.

## Objetivo

Demonstrar o fluxo `problema → função → hipóteses concorrentes → teste discriminante → evidência → decisão revisada` usando o conhecimento causal do FMEA Mining sem copiar nem promover combinações heurísticas.

### Entrada hipotética

- Modelo informado: caminhão CAT 777E (**configuração/série não informadas**).
- Local: compartimento de comando final a identificar.
- Queixa: resultado de óleo com alteração de aditivos/metais e relato de ruído.
- Lacunas: histórico de troca de óleo, tipo e lote de lubrificante, unidades, limites e histórico de tendência, coleta, lado do compartimento, horas, condição de carga, temperatura e medições de inspeção.

### Hipóteses concorrentes iniciais

A. Mudança de produto/formulação de lubrificante **sem falha funcional demonstrada**.
B. Contaminação externa ou cruzada decorrente de vedação, respiração, coleta ou abastecimento.
C. Desgaste progressivo de engrenagens/rolamentos ou condição de lubrificação fora de requisitos.
D. Fonte independente de ruído ou viés de medição.

Nenhuma hipótese está confirmada. Observações semelhantes podem ser produzidas por mecanismos diferentes.

### Dados e testes potencialmente discriminantes

| Questão | Informação que falta | Limite de interpretação |
| --- | --- | --- |
| Produto alterado? | histórico de lubrificante anterior/atual, datas e compartimento | perfil aditivo diferente não prova dano |
| Metais em tendência? | valores, método, laboratório, amostragem consistente e replicações | metal isolado não identifica peça única |
| Contaminação ingressou? | inspeção de respiros/vedações, partículas, umidade e contexto | vedação visualmente alterada não prova ingresso efetivo |
| Há perda de função? | inspeção e testes OEM aplicáveis à série, além de sintomas e condição | ruído não prova fratura/engrenagem |
| Possível efeito sistêmico? | dano confirmado e propagação operacional documentada | efeito possível ≠ efeito ocorrido |

### Saída esperada do motor da superinteligência

1. **Fatos documentados**, com fontes e unidades quando houver.
2. **Hipóteses** em aberto e evidência que favorece/desfavorece cada uma.
3. **Plano investigativo**, sem desmontagem ou ajuste fora de procedimento.
4. **Alerta de segurança**, quando aplicável, dirigido à avaliação humana.
5. **Pendências de informação:** série, manual OEM e dados consistentes.
6. **Proposta de registro:** sintoma, observação, material desconhecido, teste proposto, resultado e limitações.
7. **Decisão:** classificada como `needs_evidence`, `escalate_to_specialist` ou `ready_for_human_review`; não liberação automática.

## Casos adversariais

- Se o usuário disser apenas "aditivos incompatíveis", a IA **não** deve afirmar desgaste.
- Se disser "metais elevados", não deve identificar rolamento versus engrenagem sem mais evidência.
- Se houver mudança documentada de formulação, reconhecer a explicação alternativa sem encerrar outras anomalias independentes.
- Se vier um valor de pressão ou torque sem série/revisão, não compará-lo com especificação não verificada.
- Se a origem de um dado for simulada, não rotulá-la como medição real.

## Critério de sucesso

O piloto só será aprovado quando responder adequadamente a casos **completos, incompletos, contraditórios e de risco**, usando fontes controladas e revisão humana. Conclusão correta pode ser **não determinar a causa**.
