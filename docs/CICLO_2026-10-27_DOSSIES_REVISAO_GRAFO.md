# Ciclo 25 — Dossiês sintéticos de revisão de mudanças

**Estado:** implementação incremental em branch, aguardando verificação de CI e revisão do PR. **Não há homologação operacional.**

## Objetivo
Converter as dez propostas do Ciclo 24 em pacotes documentais comparáveis para futura análise multidisciplinar, sem conceder poder de aprovar mudanças, suprimir controles ou operar máquinas.

## Entregue neste incremento
- Módulo `pilot/change_review_packets.py`: um pacote por proposta, hash SHA-256 sobre JSON canônico da origem, vínculo ao hash do DAG anterior, classificação, pares e cenários afetados.
- Sete lacunas explícitas por pacote: identidade, competência independente, efetividade OEM, segurança, base jurídica, decisão assinada e auditoria.
- Cinco objeções **sintéticas**, associadas conceitualmente a TI, Segurança da Informação, Engenharia, Jurídico e Gestão da Manutenção. Não representam parecer real dessas áreas.
- Cinco motivos exemplificativos de reabertura, incluindo alteração de versão, revogação de evidência e conflito de responsáveis.
- Contrato JSON Schema para envelope `graph-change-review-packets.v1`, testes adversariais, geração HTML/JSON offline e etapa CI com verificação prévia do relatório do Ciclo 24.
- **Veto obrigatório:** `no_go` / `veto_no_merge`, sem assinaturas reais, aprovação humana, acesso ao SAP/ECM, compra, OS ou liberação.

## Arquitetura de confiança
O módulo constrói pacotes a partir de um relatório do Ciclo 24 que declara os bloqueios esperados. **Verificações de formato e hashes isolados não autenticam pessoas nem documentos externos.** Na execução CI, a origem é adicionalmente reconstruída e validada com `pilot.graph_change_review.verify_report` contra o conjunto fixado de especificações, cobertura e Go/No-Go. Não confundir SHA-256 de conteúdo com assinatura criptográfica.

## Executar após o Ciclo 24
```bash
python -m unittest discover -s tests -v
python -m pilot.change_review_packets \
  --cycle24 build/graph-change/graph-change-review.v1.json \
  --output build/graph-change/cycle25-review-packets.json \
  --html build/graph-change/cycle25-review-packets.html
```

## Pendências para completar o escopo integral da issue #50
1. Contratos específicos para `IndependentTechnicalReviewRequirement`, `ChangeObjection`, `DocumentaryEvidenceGap`, `StaleGraphRevision` e `ReviewAdjudication` com validações aninhadas estritas.
2. Modelar decisões e contestações interavaliadores independentes, sem identidade, assinatura ou consenso fictício.
3. Regras executáveis de invalidação para retirada de evidência, conflito e rotação de revisores, com rastreabilidade de eventos.
4. Bateria de cenários adversariais dedicada a autoaprovação, adulteração, falsas assinaturas e conflito ocultado.
5. Interface conceitual de handoff para ambiente privado autorizado, sem conectar sistema público a dados corporativos.

**Critério de bloqueio:** nenhum teste sintético representa parecer OEM, evidência de campo, licença, identidade autêntica ou autorização de manutenção.
