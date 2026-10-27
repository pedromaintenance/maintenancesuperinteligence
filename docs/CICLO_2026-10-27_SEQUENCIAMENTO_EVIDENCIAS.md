# Ciclo 21 — Sequenciamento de evidências para futuro projeto privado

**27/10/2026 · P&D v2.1.0 · Issue #42**

## Objetivo e status

Organizar os requisitos de um possível ambiente privado de revisão técnica em uma **sequência de obtenção e validação de evidências**, preservando a decisão obrigatória **`no_go`**. O repositório público não implanta piloto, autentica revisores, acessa documentos corporativos, verifica publicação OEM por série nem autoriza manutenção.

O módulo `pilot/evidence_sequence.py` lê o pacote `pilot/go-nogo-package.v1.json` do Ciclo 20 e reconstitui toda a cadeia pública FMEA/dossiês/notificações/revisões para garantir que os documentos de origem não foram adulterados. O resultado é uma agenda lógica *sem* datas, custos, HH ou comprovação física.

## Grafo e ordenação

Há **13 controles e 17 dependências direcionadas**. A aplicação utiliza ordenação topológica de Kahn, escolhendo, entre nós liberados no grafo, a fase mais precoce e a ordem original do controle; nenhuma duração de serviço ou probabilidade é presumida. Ciclos, referências desconhecidas, autoprecedência, duplicação de vínculos e fases que precedam um controle obrigatório são rejeitados.

Os **três controles sem predecessores** são:

- `identity-proof` — base para identidade, competência, segregação, revisão assinada e controle de versão;
- `equipment-configuration` — entrada necessária para efetividade OEM por arranjo;
- `privacy-retention` — entrada necessária para legitimidade e restrições de tratamento de fontes.

Esses controles são pontos de partida **estruturais** do grafo, não uma classificação quantitativa de risco, criticidade de ativo, benefício econômico ou prioridade de investimento.

O relatório calcula a quantidade de controles a jusante e a profundidade de dependências como números combinatórios, não como prazo, duração, caminho crítico temporal ou esforço.

## Sete fases propostas

| Fase | Saída pretendida para um futuro ambiente privado | Situação real no projeto público |
| --- | --- | --- |
| P1 — Governança | Retenção/minimização e configuração do equipamento | Não comprovada |
| P2 — Identidade e segurança | Identificação, competências, independência, versão, assinatura, auditoria e revogação | Não comprovada |
| P3 — Legitimidade dos dados | Direitos de uso e acesso à evidência | Não comprovada |
| P4 — Efetividade OEM | Verificar publicação, revisão, série e arranjo em literatura autorizada | Não comprovada |
| P5 — Isolamento operacional | Barreiras explícitas contra SAP, ECM, requisição de peças e liberação | Não comprovada |
| P6 — Aceite externo | Pareceres independentes das cinco áreas | Não solicitado |
| P7 — Viabilidade | Avaliação de um possível piloto exclusivamente por governança corporativa própria | **NO GO** |

**Interpretação:** a ordem proposta é de organização documental, não a afirmação de que P2 ocorreu ou de que P3 precisa necessariamente começar somente depois da conclusão material de P2 em uma implantação real. Os vínculos técnicos efetivos são os 17 precedentes do grafo. Mudanças nas fases para um piloto real precisam ser decididas pelas áreas competentes, no ambiente privado, sem alterar o status `no_go` público.

## Matriz de evidência e responsáveis propostos

A especificação versionada gera 13 `proofRequests`, cada um com controle de origem, identificador fictício `SIM-PROOF-*`, área responsável, critério mínimo de aceite e predecessores. Os campos `reviewerVerified`, `documentRevisionCurrent`, `originAuthorized`, `licenseAndPrivacyCleared` e `mayBypass` permanecem *false*.

A interface de passagem de requisitos é um manifesto **conceitual** de cinco `SIM-HANDOFF-*`:

- **TI:** identidade, controle de versão e revogação.
- **Segurança da Informação:** autoria/assinatura e trilhas externas auditáveis.
- **Engenharia:** competência mecânica/elétrica, independência técnica e aplicabilidade documental OEM.
- **Jurídico:** conflito de interesses, direitos de uso, finalidade, retenção e proteção de dados.
- **Gestão de Manutenção:** configuração efetiva do equipamento e isolamento operacional.

Não é API, caixa postal, conector, solicitação enviada ou aceite eletrônico. Nenhum nome de pessoa, credencial, assinatura, série ou arquivo corporativo é incorporado.

## Dez cenários adversariais e motivo de veto

A matriz reaproveita o registro sintético do Ciclo 20, exigindo `deny_and_reopen_external_review` para conflito não verificado, identidade duplicada, credencial revogada, assinatura forjada, mudança OEM, alteração de arranjo, nota SAP indevida, violação de segregação de dados, auditoria adulterada e material licenciado publicado sem direito.

Cada cenário conserva `actualIncidentConfirmed=false` e `remediationClosed=false`. Não se trata de incidentes ocorridos em mina, nem de planos de correção aprovados. Sua finalidade é testar que **nenhum atalho ao controle de origem libera a fase seguinte**.

## Normas, governança e limites de interpretação

O planejamento mantém as referências públicas dos ciclos anteriores: [NIST SP 800-63-4](https://csrc.nist.gov/pubs/sp/800/63/4/final) para identidade; [OWASP ASVS](https://asvs.owasp.org/) para requisitos de segurança de aplicações; e [LGPD (Lei 13.709/2018)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) para requisitos de tratamento de dados sujeitos à avaliação jurídica específica.

**Efetividade OEM não decorre de NIST, OWASP ou LGPD.** Ela precisa ser demonstrada posteriormente por publicação do fabricante obtida licitamente, revisão/efetividade por série e configuração real, em ambiente aprovado.

Nenhuma documentação técnica de fabricante protegida por licença, telemetria, laudo SOS, informação pessoal, credencial ou registro SAP entra na base pública. A integridade por SHA-256 compara fixtures e relatórios sintéticos; não comprova autenticidade pessoal, assinatura digital, tempo confiável ou imutabilidade externa.

## Arquivos e testes

- `pilot/evidence-sequencing.v1.json`: fases, manifestos, responsáveis propostos, dez ameaças e limites.
- `pilot/evidence_sequence.py`: validação estrita, grafo acíclico, ordenação topológica, impacto estrutural, abstenção e relatórios JSON/HTML offline.
- Onze contratos JSON Schema em `contracts/`: fase, prova, handoff, ameaça, política, especificação, saídas por fase/controle/handoff/ameaça e relatório.
- `tests/test_evidence_sequencing.py`: regressões estruturais e bloqueios de ciclo, fase antecipada, prova falsa, revisão obsoleta, assinatura/aceite não autenticado, custo/prazo/HH fabricado e transferência SAP/ECM.
- `.github/workflows/validate.yml`: reconstrói o corpus FMEA pinado, verifica as saídas do Ciclo 20 e produz o relatório deste ciclo, com testes de adulteração.

## Reproduzir localmente

Após gerar os artefatos anteriores conforme os Ciclos 13–20:

```bash
python -m unittest discover -s tests -v

python -m pilot.evidence_sequence \
  --snapshot build/fmea-public/fmea-public.snapshot.json \
  --gng build/go-nogo/no-go-report.v1.json \
  --output build/sequencing/evidence-sequence.v1.json \
  --html build/sequencing/evidence-sequence.v1.html
```

O HTML é estático, com política restritiva de conteúdo e sem JavaScript, formulários ou conexão corporativa. A aprovação pública continua impossível.

## Conclusão técnica e próxima etapa

O principal ganho do Ciclo 21 é tornar explícita a **ordem de obtenção de provas** para que uma futura equipe privada possa enxergar dependências e itens ainda não verificáveis. A arquitetura não mede viabilidade econômica, não dimensiona cronograma nem fornece go-live.

Próximo ciclo possível: preparar uma matriz de revisão cruzada entre áreas e um checklist de *readiness review* metodológica, com simulações de contradição entre provas e política de invalidação. Qualquer evidência real deve permanecer fora do repositório público e exigir autorização formal.
