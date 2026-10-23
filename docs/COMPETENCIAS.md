# Ontologia inicial de competências

**Fonte primária consultada:** [`engine.js`, constante `SKILL_CATALOG`](https://github.com/pedromaintenance/porcaria-voce-quebra-eu-conserto/blob/main/engine.js), complementada por [`competency.js`](https://github.com/pedromaintenance/porcaria-voce-quebra-eu-conserto/blob/main/competency.js) e [`training.js`](https://github.com/pedromaintenance/porcaria-voce-quebra-eu-conserto/blob/main/training.js), consulta em 22/10/2026.

## Inventário fiel do P.O.R.C.A.R.I.A. — 56 habilidades

### 22 disciplinas e fundamentos físicos

| ID do jogo | Nome |
| --- | --- |
| `hydraulics` | Hidráulica |
| `electrical` | Elétrica |
| `electronics` | Eletrônica |
| `lubrication` | Lubrificação |
| `welding` | Soldagem |
| `machining` | Usinagem |
| `pneumatics` | Pneumática |
| `maintenance_mechanics` | Mecânica de manutenção |
| `materials_mechanics` | Mecânica dos materiais |
| `fluid_mechanics` | Mecânica dos fluidos |
| `thermodynamics` | Termodinâmica |
| `heat_transfer` | Transferência de calor |
| `dynamics` | Dinâmica |
| `statics` | Estática |
| `vibrations` | Vibrações mecânicas |
| `tribology` | Tribologia |
| `metrology` | Metrologia |
| `technical_drawing` | Desenho técnico |
| `instrumentation` | Instrumentação |
| `automation` | Automação e controle |
| `strength_of_materials` | Resistência dos materiais |
| `electromagnetism` | Eletromagnetismo |

### 25 sistemas e conjuntos

| ID do jogo | Nome |
| --- | --- |
| `undercarriage` | Material rodante |
| `fps` | FPS |
| `engines` | Motores |
| `tires` | Pneus |
| `hydraulic_cylinders` | Cilindros hidráulicos |
| `hoses` | Mangueiras |
| `valves` | Válvulas |
| `embedded_electronics` | Eletrônica embarcada |
| `transmission` | Transmissão |
| `final_drives` | Comandos finais |
| `steering` | Direção |
| `brakes` | Freios |
| `suspension` | Suspensão |
| `cooling` | Arrefecimento |
| `fuel` | Combustível e injeção |
| `air_intake` | Admissão e escape |
| `lubrication_system` | Sistema de lubrificação |
| `hydraulic_circuit` | Circuitos hidráulicos |
| `electric_circuit` | Sistema elétrico |
| `pumps` | Bombas |
| `rotary_drives` | Redutores de giro |
| `drilling` | Perfuração |
| `compressors` | Compressores |
| `air_conditioning` | Ar-condicionado |
| `structures` | Estruturas e soldas |

**Nota:** `fps` designa o sistema de implementos frontais, conforme o contexto do jogo; registrar definição local e sinônimos antes de integração com catálogos OEM.

### 9 modelos

| ID | Modelo |
| --- | --- |
| EQ01 | CAT 777E |
| EQ02 | CAT 6030 |
| EQ03 | CAT 395 |
| EQ04 | CAT 336GC |
| EQ05 | Sandvik DR410i |
| EQ06 | Sandvik DI650i |
| EQ07 | CAT D9 |
| EQ08 | CAT 966 |
| EQ09 | CAT 16 |

## Como o jogo usa essas competências

- Cada mecânico tem valores de 0 a 100 para as três dimensões: `disciplines`, `systems`, `machines`.
- `competency.js` pondera disciplina (40%), sistema (35%) e modelo (25%) para gerar uma **proficiência de jogo** que influencia chances virtuais de diagnóstico e velocidade de reparo.
- `training.js` implementa capacitação interna e externa, duração de 12h simuladas, progressão e teto por instrutor; a prática em OS também pode aumentar pontos.
- Isso é **mecânica de simulação**, não escala validada de competência real. Nenhuma probabilidade do jogo deve ser usada para concluir a chance de acerto de um profissional ou tempo de reparo numa mina.

## Transposição para a inteligência de engenharia

Preservar os IDs originais como `gameSkillId`, mas criar uma ontologia extensível e separada:

```text
Conhecimento fundamental -> disciplina -> sistema -> subsistema -> componente
                                      \-> família de equipamento -> modelo -> arranjo/série
                            -> procedimento -> ensaio -> evidência -> decisão
```

Uma competência profissional futura terá eixos adicionais: `knowledge` (conceito), `diagnostic` (diagnóstico diferencial), `execution` (intervenção), `planning` (planejamento), `safety` (controles/qualificações), `tooling` (ferramentas e software) e `evidence` (capacidade de medir/documentar), separados de pontuações lúdicas.

**Expansões necessárias fora do jogo:** gestão de ativos, PCM, confiabilidade, engenharia econômica, OPEX/CAPEX/TCO/LCC, gestão de sobressalentes e MRO, RCM/FMEA/RCA, gestão de pessoas, gestão de mudanças, software embarcado e redes CAN/J1939, controle de versões, cibersegurança OT, ciência de dados, estatística, IA, termografia, ultrassom, NDT, hidráulica avançada, CTS, calibração, vibração e análise de óleo.

## Critérios de maturidade de uma competência

1. **Indexada:** tema nomeado, escopo, sinônimos e classificação.
2. **Fundamentada:** teoria e fontes apropriadas.
3. **Explicável:** função e mecanismos físicos descritos.
4. **Investigável:** hipóteses e testes discriminantes revisados.
5. **Aplicável:** limites por fabricante, modelo, configuração e procedimento.
6. **Demonstrada:** exemplos testados/avaliados e revisão humana.
7. **Operacionalmente autorizada:** somente sob governança específica da organização; nunca presumida pela plataforma.

Cada passagem deve registrar prova e revisor. A trilha `operacionalmente autorizada` é externa ao GitHub público.
