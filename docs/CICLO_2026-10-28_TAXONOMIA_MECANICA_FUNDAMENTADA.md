# Ciclo 33 — Taxonomia mecânica: fontes, hipóteses e perguntas discriminantes

**P&D v3.3.0 · 28/10/2026.** Avanço no conhecimento mecânico de caráter documental, sem eficácia de campo demonstrada.

## Problema

Os ciclos 27–32 estabeleceram seleção de perguntas, custódia e controles de qualidade de amostras, mas as *etiquetas técnicas* continuavam predominantemente editoriais. Neste ciclo são documentados vínculos auditáveis com materiais públicos de fabricantes e com a página de escopo de uma norma. Isso **não torna essas etiquetas verdade causal, regra operacional OEM ou diagnóstico homologado**.

## Distinções semânticas

- **Função:** papel pretendido de um sistema (transmitir torque, atuar sob demanda, monitorar/comandar, retirar calor).
- **Falha funcional:** incapacidade potencial de cumprir o requisito sob condições especificadas; os cenários genéricos ainda não fornecem requisitos OEM por série.
- **Sintoma:** relato, evento ou resultado que demanda verificação e não identifica necessariamente a origem.
- **Mecanismo físico candidato:** processo potencial de dano/perturbação (por exemplo, partículas abrasivas, ar no fluido, restrição de troca térmica), **não comprovado** no equipamento.
- **Confundidor de interpretação:** diferença de formulação, código histórico ou evento eletrônico sem correlação física; **não é modo de dano**.
- **Evidência discriminante:** documento, histórico, tendência ou inspeção autorizada que poderia diferenciar alternativas. Nenhum teste ou medição foi executado pelo projeto.
- **Causa imediata e causa raiz:** nenhuma das 12 trilhas tem causa imediata ou causa raiz confirmada; fonte pública geral não é laudo de campo.

## Matriz das 12 trilhas

| Sistema | Candidatos físicos | Confundidor | Próxima verificação documental típica |
| --- | --- | --- | --- |
| Comando final | Contaminação particulada; dano de superfície em rolamento (analogia) | Mudança de referência química do óleo | Produto, histórico, origem de amostra, tendência e padrão de dano |
| Hidráulica | Partículas abrasivas; gás no fluido; mistura de fluidos | — | Proveniência do fluido, carga, documentação e planejamento de medições |
| Eletrônica | Condição de circuito/sinal (candidata, sem prova) | Código armazenado versus ativo; evento sem correlação física | ECM/configuração, histórico, cronologia e sinal independente autorizado |
| Arrefecimento | Restrição de ar; perda de líquido; contaminação/corrosão | — | Condição de fluxo de ar, nível, histórico, fluido e carga |

## Fontes consultadas e seus limites

1. **SKF — Bearing damage analysis, ISO 15243**: https://evolution.skf.com/bearing-damage-analysis-iso-15243-is-here-to-help-you/ — descreve modos de dano em rolamentos e fatores de instalação, lubrificação e contaminação. O vínculo ao comando final é uma **analogia técnica**, não prova de falha em um rolamento específico.
2. **ISO 15243:2017 — página pública da norma**: https://www.iso.org/standard/59619.html — confirma o escopo e terminologia da classificação de danos em rolamentos. O resumo **não reproduz o texto normativo completo** nem fornece critérios de aceitação para um caso.
3. **Caterpillar — S•O•S How to Take a Sample & Read Results**: https://www.cat.com/en_US/support/maintenance/sos-services/take-sample.html — discute identificação de sinais analíticos de desgaste e contaminação em fluidos. Não comprova deterioração nem fornece limites por compartimento nesta base.
4. **HYDAC — What is contamination?**: https://fluidcare-knowledge.hydac.com/hc/en-us/articles/40830822143249-What-is-contamination — distingue contaminantes sólidos, líquidos e gasosos e métodos de caracterização. A passagem da categoria geral ao problema hidráulico particular exige confirmação.
5. **Perkins — Electronic Services Tool**: https://www.perkins.com/en_GB/campaigns/rentalsupport/electronic-services-tool-2.html — a ferramenta lê códigos ativos e registrados e eventos de módulos compatíveis. Não determina automaticamente causa raiz a partir do registro.
6. **Caterpillar — Cat 814F, monitor e ET**: https://h-cpc.cat.com/cmms/v2?cid=406&f=product&gid=328&it=product&lid=en&nc=1&pid=752924&sc=NACD — apresenta capacidades diagnósticas em produto específico. **Não extrapolar** código, circuito ou parâmetro para outra ECM/série.
7. **Caterpillar — radiador, dicas de manutenção**: https://www.cat.com/pt_BR/support/maintenance/self-service-options/radiator.html — inclui riscos de obstrução, vazamento e contaminação/corrosão. Não indica um procedimento universal nem estabelece temperatura de alarme.

As fontes foram consultadas pelo conteúdo público disponível. Todo texto de correlação e pergunta discriminante é produzido para este projeto e representa **interpretação técnica revisável**, não citação normativa literal ou instrução aprovada.

## Conexão com o seletor existente

Os quatro domínios e seus `contextGate` são checados contra `benchmarks/mechanical_reasoning.py` (Ciclo 27). Nenhum seletor do Ciclo 27/28 foi reescrito: a taxonomia é um **nível de conhecimento candidato** a uma futura integração, não um diagnóstico automático.

## Reproduzir

```bash
python -m unittest tests.test_mechanical_evidence -v
python -m knowledge.mechanical_evidence \
  --output build/benchmarks/cycle33-mechanical-evidence.json \
  --html build/benchmarks/cycle33-mechanical-evidence.html
```

O CI valida campos, tipos de relação, fontes HTTPS de domínios confiáveis, negações de autoria/efeito OEM e evita que confundidores sejam apresentados como mecanismos de dano. O HTML mostra contexto e referências, nunca botões para ensaio, compra ou liberação.

## Critérios pendentes de avanço

- Revisor mecânico externo deve inspecionar vínculos *fonte → afirmação → hipótese* e anotar divergências, em especial os casos classificados como analogia.
- O engenheiro responsável deve vincular procedimento OEM à configuração e número de série de equipamento, com autorização de acesso, antes de qualquer decisão ou teste.
- Obter observações de campo autorizadas e independentes, com cadeia de origem e evidência, para comparar hipóteses concorrentes e discriminar falsos positivos.
- Diferenciar causa imediata, mecanismo e causa raiz somente com laudo e evidência suficiente.

**NO GO:** sem diagnóstico homologado, teste físico executado, OS, SAP, ECM, definição de valores de pressão/temperatura ou liberação operacional.
