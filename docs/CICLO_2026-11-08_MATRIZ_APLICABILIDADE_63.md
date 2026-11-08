# Ciclo 63 — Matriz de aplicabilidade de referências (efetividade fictícia)

**08/11/2026 · P&D · branch empilhada sobre Ciclo 62 · NO GO**

## Por que existe
Os Ciclos 60–62 demonstraram conversão de unidades, comparação de condições e distinção semântica de referências **fictícias**. Contudo, a igualdade de fabricante/modelo não basta para aplicar um valor técnico. Série, arranjo, configuração de componente e revisão de software podem determinar a aplicabilidade de literatura OEM. O Ciclo 63 introduz uma matriz de **comparação estrutural de metadados**, sem afirmar acesso ao SIS, a documentos licenciados, a equipamentos reais ou a uma revisão OEM validada.

## Artefatos
- `benchmarks/cycle63_effectivity.py`: executa `validate` do Ciclo 62 e exige dados de máquina **inventada**, um perfil por referência e declara divergências explícitas de metadados.
- `tests/test_cycle63_effectivity.py`: 18 métodos de teste, incluindo seis campos de configuração, intervalo de série, origem, duplicidade, negações de autorização e preservação de dados.
- `.github/workflows/cycle63-effectivity.yml`: regressão offline encadeada C58–C63.
- Este documento para revisão dos pressupostos e fronteiras de validade.

## Contrato
Cada caso inclui `asset.configuration` com `manufacturer`, `model`, `arrangement`, `component`, `configuration` e `softwareRevision`; `asset.serial` contém prefixo e número fictícios. Cada referência do C62 recebe exatamente um perfil `effectivities`, com os mesmos seis atributos mais `serialRange`, `sourceRevision=SYNTHETIC`, `sourceStatus=unverified_synthetic` e `oemVerified=false`.

As comparações exigem **igualdade exata** dos seis identificadores e inclusão numérica da série no intervalo [início, fim], com prefixo igual. O contrato atual não implementa modelos de intercambialidade, aplicabilidade condicional, atualizações de componentes, *serial breaks* complexos ou substituição por boletins de serviço; essas relações exigiriam regras explícitas e autorizadas, nunca inferência automática.

## Resultado seguro
`metadataMatch=true` significa apenas **igualdade de strings e números artificiais fornecidos pelo mesmo arquivo**. Não significa que o manual ou componente seja aplicável. O retorno sempre contém:
- `oemEffectivityVerified=false`;
- `referenceApproved=false`;
- `diagnosticAccuracyValidated=false`;
- `operationalAuthorityGranted=false`;
- `decision=NO GO`.

Divergências são registradas por identificadores de campo e faixa, sem aceitar números reais de série ou acesso a inventário corporativo.

## Limites técnicos
1. Todos os identificadores aceitos são `SIM-`; nenhum manual real, série CAT, SAP, ECM, arquivo de concessionária, histórico de manutenção ou ficha de engenharia é ingerido.
2. Igualdade nominal não autentica nenhuma fonte, revisão, validade temporal, escopo contratual ou direito de uso.
3. Uma configuração real pode sofrer alteração em campo não refletida no cadastro. O algoritmo não verifica alterações físicas, *retrofits* ou composição atual do ativo.
4. O modelo exige uma única faixa por referência no ensaio; manuais reais podem conter faixas descontínuas, exceções e condições alternativas.
5. Essa etapa **não decide** se um parâmetro técnico é seguro, se uma peça pode ser condenada ou se uma OS pode ser emitida. O contrato falha fechado para afirmações de autoridade.

## Reproduzir
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics tests.test_cycle63_effectivity -v
python -m benchmarks.cycle63_effectivity --input /tmp/ensaio-ficticio.json --output /tmp/recibo-c63-novo.json
```

`fixture()` em `tests/test_cycle63_effectivity.py` fornece entrada integralmente inventada.

## Próximo gargalo: verificação documental independente
O Ciclo 64 deve avaliar **cadeia de fontes e conflitos de revisão**: identificação da fonte, precedência de revisões, revogação, dependências e conflitos não resolvidos, ainda sem importar conteúdo proprietário. Nenhum modelo de fontes pode fingir autorização institucional ou homologação.

**Decisão: NO GO para aplicação OEM real, testes físicos, acesso SAP/ECM, condenação, abertura de OS e liberação de ativos.**
