# Arquivo público de evidências de publicação — GitHub Pages

Este diretório preserva **documentos públicos de entrega do site**, não dados corporativos de mina, diagnósticos, aprovações profissionais ou certificados. **NO GO operacional.**

## Primeira evidência com verificação HTTP

`2026-11-07-run-42412015125/` contém o ZIP binário original e os dois JSONs originais do [GitHub Actions #42412015125](https://github.com/pedromaintenance/maintenancesuperinteligence/actions/runs/42412015125).

- Commit que foi publicado: `b930a177cc9ba1c94c32785f8fa0b16c37723afb`.
- Artefato do GitHub Actions: ID `13589439429`; expiração prevista `2026-12-07T20:38:33Z`.
- SHA-256 original do ZIP: `58b0b05a15589ddeec6f9f25cd6f57d3a7c10031300cee86734b2aa58646101b`.
- SHA-256 de `pages-release-candidate.json`: `9bd547dae00b6d59a9dad0c91493e9d1f399fbca0844a2757dd6f610aa02257b`.
- SHA-256 de `pages-http-receipt.json`: `729a14ee3f9f595223729516a76251294eded07b270d7594c5c5f8b7812cf483`.

O arquivo ZIP foi obtido do artefato do GitHub e seu SHA-256 foi comparado com o digest exposto pelo GitHub. O workflow de custódia na `main` verifica os hashes e a igualdade dos membros do ZIP com os dois JSONs preservados.

**Limite:** igualdade SHA-256 prova integridade dos bytes recebidos no momento do deploy, não a identidade de um revisor, a disponibilidade contínua da página ou sua conformidade técnica. Nenhuma avaliação humana foi realizada; 13 gates técnicos externos do estudo continuam não verificados. Novos deploys exigem nova evidência conferida, não inferência a partir do status de CI.
