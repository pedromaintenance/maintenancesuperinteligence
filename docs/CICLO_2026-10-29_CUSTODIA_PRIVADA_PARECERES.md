# Ciclo 38 — Custódia privada de pareceres técnicos e limites da autenticação

**P&D v3.8.0 · 29/10/2026.** Caminho local de integridade documental para apoiar futura revisão independente, mantendo explícita a separação entre autoria declarada e autenticação real.

## Objetivo e implementação

O Ciclo 37 forneceu 36 pacotes de revisão, com dois espaços para revisores técnicos e um para adjudicador por relação. Neste ciclo o novo módulo `governance/private_review_custody.py` permite receber **um pacote privado por execução**, com dois comentários e um registro de adjudicação **deferida**, associados a um dos 36 pacotes fixos. As evidências, chaves, recibos e pareceres não são adicionados ao repositório; os testes usam apenas textos e documentos fictícios gerados em diretório temporário.

**Não houve ingresso de pareceres humanos reais nem autenticação externa.** As identidades são pseudônimos de papéis declarados; o módulo não verifica formação, registro profissional, vínculo com a empresa, conflitos de interesse, consentimento, efetividade OEM ou autoridade.

## Controles efetivamente executados

| Controle | Implementação atual | Limite |
| --- | --- | --- |
| Restrições de caminho | Input, chave, recibo, anexos e saída obrigatoriamente fora do checkout | Não controla políticas do volume, backup ou sincronização do computador |
| Integridade de anexos | Leitura dos bytes de 1–4 arquivos locais, comparação SHA-256 e limite de 20 MiB por arquivo | Não autentica a origem técnica ou veracidade do laudo |
| Integridade do pacote | Digests da submissão, pacote público congelado, política e anexos | Não prova autoria, timestamp ou imutabilidade externa |
| Selagem | HMAC-SHA256 com chave local de pelo menos 32 bytes, protegida por permissões de arquivo POSIX quando aplicável | É autenticação **do segredo local**, não assinatura digital de engenheiros |
| Segregação editorial | Exige slots distintos A, B e adjudicador, com pseudônimos diferentes | Um mesmo indivíduo poderia controlar todos os pseudônimos |
| Privacidade da saída | Relatório resumido somente com IDs e digests; sem caminho, corpo do parecer ou nomes | Os dados privados no disco **não são criptografados** pelo projeto |
| Escrita privada | Recibos e relatórios não sobrescrevem arquivos; `0600` quando suportado | Não é transação atômica nem storage WORM |
| Limite operacional | Sem aceite técnico automático, adjudicação marcada como adiada e todas as permissões falsas | Continua necessário procedimento e autorização separados para qualquer serviço |

### Modelo de confiança

**Prova de identidade, autenticação e federação são etapas distintas.** A NIST SP 800-63-4 e seus volumes especializados descrevem esses domínios; este projeto usa as publicações como referências arquiteturais, sem alegar implementação, avaliação normativa ou certificação de nível de garantia.

- NIST SP 800-63-4 — https://csrc.nist.gov/pubs/sp/800/63/4/final
- NIST SP 800-63B-4 — https://www.nist.gov/publications/nist-sp-800-63b-4digital-identity-guidelines-authentication-and-authenticator
- NIST SP 800-63C-4 — https://csrc.nist.gov/pubs/sp/800/63/c/4/final

Um `externalClaimReference` é apenas um identificador opaco informado, **não um token de provedor de identidade verificado**. A presença de um pseudônimo, ticket ou HMAC não atribui credenciais técnicas, autoridade de revisão ou anuência de outra pessoa.

## Fluxo local (necessita diretório externo ao clone)

Cada submissão privada deve obedecer a `contracts/private-review-submission.schema.json`, referenciar `IRP-001` a `IRP-036` e o `packetDigest` obtido de `knowledge.independent_review.public_packet` **não existe**; no módulo implementado, use `governance.private_review_custody.public_packet("IRP-001")` e `pilot.change_review_packets.digest(packet)` para gerar o digest correto. O `records` contém os slots `technical_reviewer_a`, `technical_reviewer_b` e `adjudicator`, com pseudônimos diferentes e pareceres não verificados. A decisão do adjudicador deve ser `defer_unverified`. O array `evidenceFiles` contém caminhos absolutos privados e SHA-256 dos bytes.

```bash
python -m governance.private_review_custody seal \
  --submission /caminho-privado/parecer.json \
  --key /caminho-privado/chave-custodiante.bin \
  --receipt /caminho-privado/recibo.json

python -m governance.private_review_custody audit \
  --submission /caminho-privado/parecer.json \
  --key /caminho-privado/chave-custodiante.bin \
  --receipt /caminho-privado/recibo.json \
  --report /caminho-privado/relatorio-sintetico.json
```

**Atenção:** use somente documentos cuja posse e processamento estejam autorizados. A ferramenta não autentica consentimento; opere sobre armazenamento privado com criptografia/controle de acesso providos externamente quando houver dados empresariais, documentos OEM licenciados ou dados pessoais. Não publique arquivos privados, seus digests de conteúdo confidencial ou recibos do caso.

## Testes de segurança

`tests/test_private_review_custody.py` cria arquivos temporários fictícios e verifica: alteração de anexos, HMAC errado, alteração posterior de comentário, fonte técnica forjada, papéis duplicados, pseudônimo fraudulento, alegação falsa de credencial/consentimento, excesso de autoridade, caminho dentro do checkout, chave fraca/permissão inadequada, symlink e repetição de arquivos.

O CI publica somente o código e a verificação de **dados de teste sintéticos**. Os materiais reais não são lidos nem enviados ao GitHub Actions.

## Riscos e evolução

- **Falta IAM/IdP**: autenticação forte e afirmações de identidade com assinaturas verificadas por provedor confiável.
- **Falta segregação efetiva RBAC**: papéis atualmente declarativos, sem sessão autenticada nem política de acesso organizacional.
- **Falta proteção confidencial externa**: criptografia em repouso e durante trânsito, classificação documental, trilha de auditoria gerida e retenção/acesso conforme governança corporativa.
- **Falta custódia temporal confiável**: carimbo de tempo externo, logs imutáveis ou armazenamento WORM quando necessário.
- **Falta qualificação técnica**: OEM por série, revisão independente de engenharia, escopo aprovado e controle de conflito de interesses.
- **Limite contra TOCTOU**: há janela entre verificação de arquivos e uso posterior se o filesystem não tiver controle de bloqueio ou snapshots; para ambiente real exigir serviço gerenciado.

**Conclusão:** integridade local verificável de arquivos e submissões; **zero identidade humana autenticada, zero revisão independente homologada, zero autoridade operacional**. Toda saída mantém `no_go_private_integrity_only_external_identity_and_authorization_required`.
