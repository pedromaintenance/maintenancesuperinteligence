---
name: auditoria-evidencias
description: Auditar afirmações técnicas contra fontes, natureza da evidência, contradições e limites de autoridade na Maintenance Superintelligence.
---

# Skill — Auditoria de evidências

## Quando usar
Ao receber uma alegação técnica, relatório de teste, link documental, parecer ou mudança de status de maturidade.

## Procedimento
1. Leia `AGENTS.md`, `docs/GOVERNANCA.md` e `interfaces/catalog.v1.json`.
2. Identifique a **proposição exata**. Separe afirmação factual, hipótese, simulação, intenção e resultado observado.
3. Liste as fontes por caminho, versão/revisão, origem, escopo e direito de acesso. Não copie conteúdo de literatura OEM protegida.
4. Valide as relações entre documentos. Presença de arquivo e SHA não provam licença, autenticidade de pessoa ou aplicabilidade OEM.
5. Procure contradições e lacunas; mantenha explicitamente o que não pode ser verificado.
6. Indique testes determinísticos disponíveis e a **natureza sintética** de cada execução. Não transforme CI em revisão humana.
7. Produza relatório com: proposição, evidências favoráveis, contraprovas, limitações, confiança condicionada, riscos e próxima evidência a obter.

## Saída esperada
`claim | source_path | evidence_nature | corroboration | contradictions | applicability | gaps | status | next_evidence`.

## Proibições
Nunca conferir autoridade para teste, OS, SAP, ECM ou liberação. Não publicar casos internos, dados identificáveis, documentos licenciados ou credenciais. Se a fonte for insuficiente, responder **não verificado**.

## Referências internas
`governance/cycle48-study-readiness.v1.json`, `docs/CICLO_2026-11-05_PRONTIDAO_ESTUDO_48.md`, `docs/ROADMAP.md`.
