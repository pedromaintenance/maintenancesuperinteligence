# Mapa de domínios — escopo de longo prazo

Esta página é o **mapa de pesquisa**, não uma declaração de domínio já alcançado.

| Domínio | Conhecimentos a construir | Produtos futuros |
| --- | --- | --- |
| **Gestão de ativos** | política, objetivos, SAMP, criticidade, valor, risco, ciclo de vida, LCC/TCO, substituição, rebuild, desmobilização, CAPEX/OPEX, custos e sustentabilidade | matrizes de decisão; modelos de ciclo de vida |
| **PCM e execução** | identificação da demanda, registro SAP PM, backlog, refinamento, planejamento de serviços, job plans, HH, materiais, programação semanal, restrições, checklists, encerramento e lições aprendidas | assistente de escopo; qualidade de notas e OS; checklists |
| **Confiabilidade** | RCM, FMEA/FMECA, RCA, Weibull, MTBF/MTTR contextualizados, disponibilidade, mantenabilidade, RBD, criticidade, perfil de perdas, eventos censurados e denominadores | análises reproduzíveis, planos de tratamento |
| **Preventiva** | estratégias por horímetro/calendário/ciclo/condição; lubrificação; torques; inspeções; kits; intervalos OEM; otimização com histórico | revisão assistida de tarefas e intervalos |
| **Preditiva / monitoramento** | SOS e tendências de óleo, ferrografia, vibração, termografia, ultrassom, partículas, desgaste, telemetria, desvio multivariado, prognóstico e incerteza | detecção/análise de anomalias com evidências |
| **Corretiva e recuperação** | diagnóstico, isolamento de energia, preparação, desmontagem/montagem, metrologia, soldagem, usinagem, testes de aceitação, retorno e análise pós-serviço | planos de intervenção sob revisão |
| **Fundamentos** | matemática, estatística, estática, dinâmica, resistência, termodinâmica, transferência de calor, mecânica de fluidos, materiais, tribologia, eletromagnetismo, controle e desenho técnico | base conceitual ligada a casos reais |
| **Sistemas mecânicos** | motor diesel e emissões, admissão/escape, alimentação, arrefecimento, lubrificação, transmissão, diferencial, comandos finais, freios, pneus, suspensão, material rodante, FPS, estruturas | mapas funcionais e árvores de falha |
| **Fluidos e acionamentos** | bombas, válvulas, cilindros, vedações, acumuladores, mangueiras, compressores, ar comprimido, lubrificação centralizada | métodos de ensaio e diagnóstico |
| **Eletricidade e eletrônica** | geração/distribuição, aterramento, sensores, atuadores, chicotes, conectores, ECU/ECM, sinal analógico/digital, PWM, CAN/J1939, LIN/Ethernet quando aplicável, DTC/FMI e redes | mapas de sinais e interpretação contextual |
| **Controle e softwares OEM** | Cat SIS e Cat ET; VisionLink; telemetria AEMP; plataformas Sandvik e suas versões *a identificar*; calibrações e parâmetros apenas documentados; leitura de *snapshots*, logs e códigos | guias **de navegação e interpretação** autorizados |
| **Equipamentos de mineração** | caminhões 777; escavadeiras 6030/395/336; tratores D9; carregadeiras 966; motoniveladoras 16; perfuratrizes DR410i/DI650i; demais famílias por expansão | atlas por modelo, configuração, sistema e circuito |
| **Operação e mina** | ciclo de carga/transporte, perfuração, vias, geotecnia/interface, utilização, severidade operacional, produtividade, combustível, logística e risco ambiental | modelos de contexto operacional |
| **Sistemas corporativos e dados** | SAP PM/MM, cadastros, estruturas funcionais, PR/PO, Power BI, qualidade de dados, ETL, rastreabilidade, SQL, APIs, segurança e observabilidade | conectores com acesso mínimo e somente-leitura inicialmente |
| **Segurança e fatores humanos** | energia perigosa, LOTO, permissões, içamento, pressão hidráulica acumulada, trabalho em altura/espaço confinado conforme aplicabilidade, ergonomia, fadiga, treinamento e cultura de reporte | gates de risco e revisão humana |

## Regra para conhecimento OEM

`fabricante + modelo + configuração + série/prefixo + subsistema + revisão do documento + (ECM/versão de software, quando pertinente)` devem ser campos separados; ausência de qualquer dimensão crítica degrada a resposta para **conceitual/genérica**, nunca para especificação confirmada.

Nunca presumir que a função existe em todos os modelos, que nomes de softwares são universais ou que um DTC, CID/FMI ou evento tenha significado idêntico entre ECMs.

## Interoperabilidade sem centralizar material proprietário

Arquitetura orientada por **interfaces e referências**. O conhecimento público guarda sínteses originais, taxonomias e ponteiros. Os documentos sob licença e os dados corporativos ficam em serviços restritos separados, com autorização por usuário, logs de acesso e política de retenção.

## Priorização de pesquisas

Usar uma matriz explícita: `valor operacional potencial × criticidade × lacuna de conhecimento × viabilidade de evidência`, com segurança como condição bloqueadora e não um número compensável. Estabelecer pilotos em máquinas presentes no jogo e problemas já modelados no FMEA; só depois escalar.
