# Ciclo 37 — Preparação de revisão técnica independente

**P&D v3.7.0 · 29/10/2026.** Conecta o registro de hipóteses e dissenso dos Ciclos 33–36 a um protocolo de avaliação que possa receber evidências humanas posteriormente, sem presumir que elas já foram obtidas.

## Resultado entregue

O protocolo contém **36 pacotes sintéticos de trabalho**, um por regra discriminante do Ciclo 34, ligados por referência integral às 72 contestações editoriais do Ciclo 35, às 36 propostas do Ciclo 36 e ao registro de versões v1/v2. Foram criados **72 espaços para opiniões técnicas independentes e 36 espaços para decisões de adjudicação**. Nenhuma opinião real foi coletada, ninguém foi designado e nenhum convite foi enviado.

## Papéis segregados

| Papel | Responsabilidade pretendida | Restrição |
| --- | --- | --- |
| Autor da hipótese | Documentar mecanismo candidato, sintomas, contexto e fonte | Não homologar sua própria hipótese |
| Custodiante | Controlar identidade, credenciais, evidências e versões privadas | Não substituir parecer de engenheiro habilitado |
| Revisor técnico A | Avaliar a plausibilidade e contestar a primeira relação | Independente do autor e de interesses relevantes |
| Revisor técnico B | Avaliar independentemente, incluindo hipóteses rivais | Não pode ser a mesma pessoa que A |
| Adjudicador | Registrar decisão fundamentada, divergências e condicionantes | Distinto dos revisores e dos autores; requer competência reconhecida externamente |

Os `SIM-SLOT-*` são **placeholders**, não pessoas reais e não comprovação de identidade. Competência, independência e conflito de interesses exigem validação por processo organizacional externo. O sistema não pode realizar verificação profissional ou certificar assinatura humana.

## Oito gates obrigatórios para analisar uma relação

1. Identidade humana verificada.
2. Competência técnica e experiência verificadas no domínio mecânico correspondente.
3. Segregação de papéis, independência e ausência de conflitos de interesse verificadas.
4. Efetividade da literatura OEM por modelo, número de série, configuração e revisão da documentação.
5. Proveniência da evidência — autorização de acesso, origem, cadeia de custódia e qualidade da observação física quando aplicável.
6. Duas opiniões independentes, escritas e vinculadas à versão imutavelmente *referenciada* do texto original (hash não fornece imutabilidade).
7. Análise e resolução documentada dos contraexemplos relevantes e das divergências.
8. Decisão fundamentada de adjudicador independente, cuja identidade e habilitação tenham sido verificadas pelo custodiante.

## Critérios objetivos de encaminhamento

| Encaminhamento possível | Critério mínimo | Estado nesta versão |
| --- | --- | --- |
| Aceite técnico para pesquisa | Oito gates completos, pareceres qualificados e evidências convergentes contextualizadas; contraexemplos enfrentados e adjudicação verificada | **Bloqueado** |
| Rejeição técnica fundamentada | Contraevidência verificável, duas opiniões documentadas, registro fundamentado do adjudicador e comprovação da origem/versão das fontes | **Bloqueada** |
| Revisão proposta | Texto v2 comparável com v1 congelado, explicitação de restrições e nova rodada de avaliação; nunca altera automaticamente a regra original | Proposta, não homologação |
| Adiamento | Qualquer gate pendente, conflito técnico não resolvido, fonte sem efetividade ou evidência insuficiente | Estado obrigatório atual |

**Mesmo um aceite técnico para pesquisa não significa permissão de intervenção mecânica, pedido de peças ou liberação de equipamento.** Qualquer implementação operacional exigirá procedimento de engenharia e autorização institucional separada.

## Dossiê e privacidade

O repositório público expõe somente nomes genéricos de sistemas, hipóteses fictícias, referências públicas aos fabricantes e limites do escopo. Não armazena números de série internos, laudos reais, documentos OEM licenciados, identidades, certificados profissionais ou comentários humanos. O CLI gera pacotes de trabalho sintéticos com links para fontes gerais já catalogadas, além de relatório de lacunas.

O processo real deve exigir custódia **privada** dos dados pessoais e materiais corporativos/OEM, controle de acesso por função, retenção e consentimento adequados, verificação de credenciais e regras de publicação. Este ciclo não disponibiliza ingestão de resultados humanos reais nem envia convites.

## Implementação e execução

- `knowledge/independent-review-protocol.v1.json`: papéis, oito gates, critérios de aceite/rejeição e proibições.
- `knowledge/independent-review-worklist.v1.json`: 36 tarefas, versões congeladas, dissenso e requisitos de evidência.
- `knowledge/independent_review.py`: valida estrutura e negações, gera pacotes com proveniência e produz análise determinística de prontidão.
- `contracts/independent-review-{protocol,worklist,packets,readiness}.schema.json`: quatro contratos JSON.
- `tests/test_independent_review.py`: testes de segregação, dados falsos, perda de gates, adulteração de fonte, versão e permissões.

```bash
python -m unittest tests.test_independent_review -v
python -m knowledge.independent_review \
  --output build/benchmarks/cycle37-readiness.json \
  --packets build/benchmarks/cycle37-review-packets.json \
  --html build/benchmarks/cycle37-readiness.html
```

Os relatórios permanecem sintéticos. O artefato de CI é um documento de preparação, não um registro de revisão concluída. O algoritmo não converte consistência editorial em evidência física nem permite mudança automática de status de manutenção.

## Limite de evidência e próximo passo

O protocolo vincula versões por hashes reprodutíveis, mas uma cadeia SHA-256 sem carimbo de tempo externo, autenticação ou custódia independente pode ser refeita. Antes da primeira revisão real, deve existir um processo institucional de verificação de pessoas, literatura OEM licenciada por série, aceite de termos de confidencialidade, registro de conflito de interesses e coleta autorizada das evidências.

**Resultado:** nenhuma relação aceita ou rejeitada tecnicamente, **36 pendentes**, 0 profissionais verificados, 0 pareceres independentes, 0 assinaturas, 0 autorizações operacionais. `no_go_collect_real_credentials_and_review_evidence`.
