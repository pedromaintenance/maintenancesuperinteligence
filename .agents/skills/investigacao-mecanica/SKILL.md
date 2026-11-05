---
name: investigacao-mecanica
description: Estruturar hipóteses, evidências e perguntas diagnósticas para manutenção mecânica sem simular autorização ou diagnóstico de campo.
---

# Skill — Investigação mecânica consultiva

## Quando usar
Problema sobre equipamento, componente, sintomas, modo de falha, inspeção ou escolha de pergunta discriminante.

## Procedimento
1. Defina ativo, configuração e **função**. Se modelo/série/revisão OEM não forem conhecidos, registre a lacuna.
2. Diferencie sintoma, falha funcional, dano, mecanismo, causa imediata, contribuinte e causa raiz **ainda não confirmada**.
3. Formule hipóteses concorrentes com sinais a favor e contra.
4. Para cada pergunta candidata, registre o que distinguiria cada hipótese e se depende de procedimento, instrumento, condição de carga ou risco.
5. Consulte os métodos, árvores e evidências públicas do repositório. Não conclua superioridade por gabaritos autorais ou casos fictícios.
6. Declare limites de segurança, fontes efetivas e eventuais conflitos documentais.
7. Entregue próximo passo como **solicitação de informação, inspeção a planejar ou encaminhamento à engenharia autorizada**; nenhum comando ou teste físico é disparado.

## Saída
`função | sintoma | hipóteses | evidências | contraprovas | dados faltantes | risco | ação consultiva | necessidade de aprovação`.

## Proibições
Não inventar PN, valores de pressão/torque, procedimento OEM, série aplicável ou causa raiz. Não emitir OS, alterar SAP/ECM, executar teste, liberar equipamento ou atribuir culpa de trabalhadores sem análise.

## Referências
`docs/ARQUITETURA.md`, `docs/GOVERNANCA.md`, `benchmarks/mechanical_reasoning.py`, `docs/CICLO_2026-11-05_REVISAO_RELACIONAL_50.md`.
