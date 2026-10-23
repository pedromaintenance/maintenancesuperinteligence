# Arquitetura de referência v0.1 — MaintenanceSuperinteligence

**Estado:** desenho de P&D; nenhum dos serviços abaixo está implementado.

## Objetivo operacional

Responder perguntas técnicas e produzir investigações reproduzíveis **com fundamento documental, conhecimento físico, evidências e restrições de configuração**. A plataforma deverá saber expressar incerteza e solicitar o dado discriminante necessário; não terá autoridade para controlar máquinas.

## Camadas e fluxo

```text
Fontes públicas / contratos FMEA / bibliografia / dados privados autorizados
   ↓ adaptadores controlados por licença, versão, hash e política de acesso
Área de ingestão/quarentena → classificação → extração → validação de esquema
   ↓
Catálogo de objetos (ativos, modelos, circuitos, componentes, funções, procedimentos)
   ↔ Grafo de conhecimento (relações causais tipadas e fonte por aresta)
   ↔ Evidências / séries temporais / eventos (segregados por tenant e finalidade)
   ↓
Busca híbrida: filtros exatos por modelo/série + pesquisa lexical + semântica
   ↓
Orquestrador: formula hipótese → busca fontes → encontra contraprovas → seleciona testes
   ↓
Ferramentas determinísticas: cálculo, unidades, curvas, métricas, comparação com limites válidos
   ↓
Verificadores: proveniência, aplicabilidade, segurança, conflito, dado faltante
   ↓
Resposta estruturada: fatos | hipóteses | evidências | riscos | próximos testes | referências
   ↓
Engenheiro / técnico / planejador (decide, executa e devolve resultado)
   ↓
Feedback revisado e versionado → novo conhecimento (nunca autopromoção)
```

## Serviços planejados

1. **Catalog Service:** ontologia, aliases PT/EN, hierarquia funcional, hierarquia física, posições LE/LD, modelos, arranjos e revisão.
2. **Source Registry:** identificadores de fonte, URI, editor, edição, data de acesso, classe jurídica, versão, seções e *effective serial range*; guarda ponteiro, não o manual protegido.
3. **Evidence Ledger:** medições, condições, instrumentos, calibração, hora, horímetro, origem real/simulada, autorização e trilha imutável; acesso privado para registros operacionais.
4. **Failure Reasoner:** utiliza mecanismos e testes diferenciais do FMEA; distingue observação, correlação, causa imediata, contribuinte e raiz.
5. **Strategy Engine:** recomenda ações de RCM, planejamento, inspeção, materiais, custo/risco e políticas do ciclo de vida, com revisão humana.
6. **Knowledge Gap Engine:** registra lacunas: literatura OEM por série, baseline, teste inexistente, material desconhecido, número de peça incerto, revisão ausente.
7. **Evaluation Harness:** benchmark, regressões de semântica, testes adversariais, auditoria de citações, indicadores de erro e avaliação humana.
8. **Policy Gateway:** identificação de dados restritos, bloqueio de ações operacionais e separação entre assistente consultivo e sistema de execução.

## Modelo mínimo de entidades

- `AssetModel`: fabricante, família, modelo e tipo.
- `AssetConfiguration`: variante, série/arranjo, revisões e softwares pertinentes; **somente em ambiente autorizado se identificável**.
- `FunctionalLocation`, `Function`, `PerformanceRequirement`, `FunctionalFailure`.
- `Component`, `FailureMode`, `Damage`, `Mechanism`, `CauseCandidate`, `Effect`.
- `Observation`, `Signal`, `DiagnosticCode`, `TestMethod`, `TestResult`, `Evidence`.
- `MaintenanceTask`, `MaintenanceStrategy`, `WorkPackage`, `SparePartRequirement`.
- `Source`, `Claim`, `Applicability`, `ReviewDecision`, `KnowledgeGap`.
- `Competency`, `LearningObjective`, `AssessmentCase`.

Cada ligação no grafo deve ter `relationType`, `sourceId`, `nature`, `status`, `applicability`, `limitations`, `createdAt`, `reviewedBy` e `version`.

### Exemplo conceitual (não representa um evento real)

```text
Função: manter circulação adequada de refrigerante
Sintoma relatado: superaquecimento em carga
Hipótese A: redução de fluxo por restrição no circuito
Hipótese B: perda de capacidade de dissipação do conjunto radiador/ventilador
Hipótese C: leitura incorreta de sensor/medição
Evidências necessárias: condições de carga, tendência, inspeção, medições OEM aplicáveis
Saída permitida: roteiros de verificação e critérios de registro
Saída proibida: "troque a bomba" apenas com o sintoma
```

## Tecnologia proposta — evolutiva, não obrigatória

**MVP:** GitHub + Markdown/JSON/JSON Schema + Python (validação, cálculos, ETL) + CLI. Começar com **busca textual e filtros determinísticos** é útil e inspecionável.

**Segunda fase:** SQLite/PostgreSQL para metadados e eventos; índice semântico e busca híbrida; API FastAPI; frontend de consulta; armazenamento de objetos para fontes autorizadas; autenticação e auditoria.

**Terceira fase:** grafo especializado **se houver benefício medido** contra PostgreSQL; agentes especializados subordinados ao orquestrador, com ferramentas de leitura e verificação; time series, modelos estatísticos e eventualmente modelos preditivos após base de treinamento adequada.

**Nunca:** depender do LLM como fonte única, tratá-lo como instrumento de medição, transformar similaridade vetorial em causa confirmada, ou conceder privilégios de escrita em SAP/ECM por conveniência.

## Interfaces iniciais a especificar

`GET /v1/knowledge/claims` (filtra modelo, componente, status), `GET /v1/knowledge/sources`, `POST /v1/investigations/draft` (assistivo), `GET /v1/research/gaps`, `POST /v1/evaluations/run` (sintético). Nenhuma rota executará intervenção, liberação ou alteração de ativo.

## Qualidade e observabilidade

Métricas obrigatórias: % de afirmações com fonte verificável; % de respostas com efetividade compatível; taxa de contradições; lacunas identificadas; cobertura de testes concorrentes; **abstenção correta**; reprovação por risco; resultado por tema/modelo; desempenho com fontes desatualizadas; deriva de versão.

Acurácia deve ser reportada por conjunto e criticidade; evitar pontuação agregada que esconda falhas perigosas.
