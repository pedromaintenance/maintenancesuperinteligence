# Ciclo 62 — Semântica de referências técnicas e limites sintéticos

**08/11/2026 · P&D · empilhado sobre Ciclo 61 · NO GO**

## Problema material
C60 calcula intervalos dimensionais. C61 verifica a comparabilidade contextual das leituras fictícias. Ainda faltava distinguir **o que significa o número usado como referência**. Um valor nominal não é um limite de falha; um limiar de alarme não é um limite de segurança; uma faixa de aceitação não é uma autorização de execução.

## Entregas
- `benchmarks/cycle62_reference_semantics.py` — recebe caso C61, valida os seus dados, identifica referências por tipo e calcula relações intervalares em unidades convertidas para SI.
- `tests/test_cycle62_reference_semantics.py` — 18 métodos de teste com cobertura de cinco semânticas, origem, direção, contexto e rejeições adversariais.
- `.github/workflows/cycle62-reference-semantics.yml` — regressão offline C58–C62.
- Documento atual — contrato, hipóteses, limites, uso e próximos passos.

## Semânticas distintas
| Tipo | Estrutura | Resultado permitido |
|---|---|---|
| `nominal_target` | Valor pontual | Relação intervalar com ponto de referência; **não** conformidade |
| `expected_operating_band` | Limites inferior e superior | Dentro/abaixo/acima/sobreposição parcial, apenas matemática |
| `alarm_threshold` | Valor e direção (`above`/`below`) | Limiar ultrapassado, não ultrapassado ou cruzamento incerto, **não** alarme real |
| `safety_threshold` | Valor e direção | Mesma relação matemática, **não** avaliação de segurança real |
| `acceptance_band` | Limites inferior e superior | Relação matemática, **não** aceite ou rejeição de componente |

Os limiares consideram a direção estrita: `above` significa maior que o valor e `below` significa menor que o valor. Igualdade não equivale a ultrapassagem. Para bandas, extremos pertencem à faixa.

## Portas de integridade
1. **Entrada:** usa `validate` do C61 e rejeita referência observacional quando o resultado não é leitura fictícia ou o contexto operacional difere.
2. **Dimensão:** referência e resultado devem compartilhar grandeza física; conversão SI por tabela do C60.
3. **Efetividade:** origem só pode ser `invented_training_source`, identificador `SIM-`, revisão `SYNTHETIC` e `effectivityVerified=false`; não há fonte OEM real ou tolerância autorizada.
4. **Semântica:** bandas exigem limites; limiares exigem direção; nominal não pode ter direção de alarme.
5. **Observação:** intervalos de incerteza fictícios podem cruzar limiares; isso é incerteza matemática, não status operacional.
6. **Negação:** todo flag de aprovação, diagnóstico, autoridade, escrita SAP/ECM, teste ou liberação deve ser falso; resposta sempre `NO GO`.

## Limitações metrológicas e mecânicas
O modelo não valida faixa de calibração, amostragem, sensores reais, fontes OEM, assinatura e revisão documental, série do equipamento, ambiente, transientes, ciclo de trabalho, unidades não incluídas ou condições de prova. A semântica de limiar se restringe a um único valor/direção fictícios; **não** interpreta alarmes com histerese, retardo, severidade, persistência ou combinações lógicas.

Não equiparar concordância com uma faixa de referência à conformidade OEM. Não usar para justificar intervenção em máquina, alteração de setpoint, emissão de OS, bloqueio ou liberação. A publicação no GitHub é pública: não inserir dados corporativos restritos ou licenciados.

## Reproduzir
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics -v
python -m benchmarks.cycle62_reference_semantics --input /tmp/referencias-ficticias.json --output /tmp/recibo-c62-novo.json
```
`fixture()` no arquivo de testes é entrada artificial reproduzível. Um teste aprovado verifica somente código e estrutura, não competência mecânica.

## Próximo passo proposto
**Ciclo 63:** qualificar aplicabilidade de referências por fabricante, modelo, arranjo, série e revisão documental **sem publicar literatura OEM privada**, criando protocolo para revisão humana e trilha de divergência de fontes. A integração com dados reais exige autorização institucional e custódia restrita.

**Decisão formal: NO GO.**
