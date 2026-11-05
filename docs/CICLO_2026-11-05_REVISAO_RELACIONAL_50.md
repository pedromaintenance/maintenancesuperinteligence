# Ciclo 50 — Revisão da integração: validação estrutural vs. vínculos relacionais

**P&D v5.0.0 (pesquisa) · 05/11/2026 · proposta empilhada sobre o Ciclo 49.**

> **NO GO:** o código não autentica revisores, não comprova efetividade OEM, não determina causa raiz, não libera máquinas, não abre OS nem autoriza testes ou ações no SAP/ECM. A revisão executada é autoral e sintética, não uma code review independente formal.

## 1. Contexto e diagnóstico da cadeia

A `main` ainda corresponde ao Ciclo 42. Os PRs #69–75 (Ciclos 43–49) seguem abertos como *draft* e com as bases sequenciais. As execuções específica e geral do Ciclo 49 passaram no seu HEAD, confirmado no GitHub em 05/11/2026. **CI verde não é aceite de código por especialista nem autorização operacional.**

O Ciclo 49 executou 16 contratos JSON Schema sobre objetos sintéticos. A revisão encontrou uma fronteira metodológica importante: **a validade estrutural de um documento não implica validade das relações entre seus campos**. Algumas relações já são exigidas pelos validadores Python e não podem ser facilmente expressas por um schema estático sem recorrer a dados externos ou a extensões específicas.

## 2. Oito falhas relacionais que schemas estruturais admitem

O laboratório `governance/cycle50_relational_review.py` cria oito adulterações sobre cópias dos casos sintéticos originais e executa dois mecanismos para cada alteração: validador JSON Schema Draft 2020-12 e validador Python responsável pela relação.

| Vínculo auditado | Falha estrutural não detectada pelo schema | Proteção runtime |
| --- | --- | --- |
| C44 — hipóteses × mapa de respostas | Chave do mapa simbólico não pertence às três hipóteses registradas | `validate_fixture` rejeita divergência entre conjuntos |
| C44 — baseline × perguntas | `baselineQuestionId` referencia pergunta diferente da primeira registrada | `validate_fixture` verifica vínculo e pré-requisito |
| C44 — contradição × status | O campo `sourceStatus` contradiz o tipo declarado do caso | `validate_fixture` recusa incoerência |
| C45 — contagem × lista | `caseCount` está dentro da faixa, mas difere de `len(cases)` | `validate_packet` verifica igualdade |
| C45 — perguntas A/B | As perguntas possuem textos idênticos, embora com formatos válidos | `validate_packet` recusa o par |
| C45 — identificação de casos | Dois casos reutilizam um mesmo ID formalmente válido | `validate_packet` proíbe duplicidade |
| C48 — commit auditado | SHA válido de 40 caracteres não corresponde ao snapshot congelado | `validate_manifest` compara com os hashes auditados |
| C48 — base × PR anterior | Base de PR é string válida, mas contraria a cadeia de dependências | `validate_manifest` valida a sequência |

**A conclusão não é que os contratos existentes estejam necessariamente errados.** Os schemas cumprem uma função de validação estática, enquanto vínculos interdocumentais precisam do runtime. O risco aparece quando alguém usa **apenas** o resultado JSON Schema como justificativa de confiabilidade da evidência.

Todas as oito mutações são deliberadas e sintéticas; o resultado esperado é **schema aceita / runtime rejeita**. Esse contraste demonstra a necessidade das duas camadas, não capacidade diagnóstica.

## 3. Correção de integridade feita no Ciclo 49

O módulo `governance/cycle49_contract_integration.py` recebeu `verify_report(report)`, que **reconstrói a matriz completa de contratos** e compara o resultado calculado ao relatório recebido. A alteração corrige um ponto objetivo: anteriormente, era possível aumentar contagens de mutações ou alterar identificadores preservando uma estrutura ainda válida para o schema do relatório.

O Ciclo 50 testa três falsificações que continuam estruturalmente admissíveis, porém são bloqueadas pela recomputação:

1. Quantidade total de mutações rejeitadas artificialmente inflada;
2. Quantidade de mutações de um contrato individual inflada;
3. Identificador de contrato substituído por outro formalmente permitido.

A função recomputa os resultados com **o mesmo código e fixtures autorais**. Isso combate adulterações ou relatórios desatualizados, mas não se qualifica como auditoria independente, assinatura de revisor ou prova de fontes reais.

## 4. Arquivos, testes e CI

- `governance/cycle50_relational_review.py`: oito provas relacionais e três adulterações de relatório;
- `governance/cycle49_contract_integration.py`: acréscimo de `verify_report`;
- `tests/test_cycle50_relational_review.py`: testes de negativas, negação de autoridade, serialização sem dados privados;
- `contracts/cycle50-relational-review.schema.json`: contrato fechado, com 8 casos relacionais, 3 adulterações e campos de autoridade falsos;
- `.github/workflows/cycle50-relational-review.yml`: instalação de `jsonschema==4.23.0`, testes, recomputação e saída pública restrita;
- Este relatório, README e ROADMAP.

Reprodução:

```bash
python -m pip install jsonschema==4.23.0
python -m unittest tests.test_cycle49_contract_integration tests.test_cycle50_relational_review -v
python -m governance.cycle50_relational_review \
  --output build/governance/cycle50-relational-review.json \
  --markdown build/governance/cycle50-relational-review.md
```

O GitHub Actions pode armazenar **somente o resumo público com identificadores de verificações e contagens**. Nenhum pacote privado de revisores, chave HMAC, caso real, mapa de braços ou documento OEM é armazenado nos artefatos.

## 5. Limites e decisões de integração

A revisão identifica lacunas **de cobertura declarativa**, não uma falha mecânica nem uma permissão operacional. Os validadores Python já rejeitavam as oito alterações antes deste ciclo; o ganho é tornar essa proteção observável em CI, para não depender erroneamente de um schema isolado.

O resultado não esgota outros possíveis vínculos entre arquivos, versões, fontes, autores, permissões e efeitos físicos. Não prova segurança contra um adversário com acesso ao próprio código e às fixtures.

**Checklist institucional ainda pendente:** revisão dos PRs #69–76 por responsáveis de software, segurança e engenharia; confirmação dos checks e da ordem de merge; custódia independente; direitos de dados; efetividade OEM; pareceres técnicos; SST; pré-registro de estudo.

Os **13 requisitos de validação externa** descritos no Ciclo 48 permanecem não verificados. O projeto não pode declarar autorização para recrutamento, coleta privada de campo, intervenção, emissão de OS, SAP, ECM ou liberação de ativos.

**Decisão formal:** `no_go_relational_integrity_is_not_external_validation`.

## 6. Próxima ação recomendada

Usar este relatório junto ao resultado do Ciclo 49 para conduzir revisão humana dos PRs na ordem da cadeia, começando pelo #69. Depois da revisão, executar testes de regressão nos commits efetivamente integrados e obter aprovação externa específica antes de iniciar um estudo técnico com casos reais. Não avançar para novas camadas autorais apenas pelo aumento do número de testes.
