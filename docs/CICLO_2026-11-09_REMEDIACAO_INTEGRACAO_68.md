# Ciclo 68 — Remediação de gatilhos CI e contratos de integração da pesquisa

**09/11/2026 · Engenharia de manutenção / P&D · pesquisa sintética · NO GO operacional · não mesclar**

## Escopo executivo
O C67 auditou a cadeia de PRs #83–#92, encontrou seis workflows específicos (C61–C66) com sete arestas de dependência sem cobertura nos filtros de disparo `paths`, e registrou divergência da branch de pesquisa frente à `main`. O C68 **corrige as sete arestas** em sua própria branch, fixa contratos mínimos das saídas dos módulos C58–C66, acrescenta testes que detectam regressão dos caminhos e descreve uma estratégia de integração controlada. Nada é mesclado à `main` neste ciclo.

### Alterações efetivamente efetuadas
- Seis workflows `cycle61-metrology-context.yml` ... `cycle66-study-preregistration.yml`: agora incluem, em **push e pull_request**, ambos os caminhos `benchmarks/cycleXX_*.py` e `tests/test_cycleXX_*.py` das dependências diretas.
- `C61 ← C60`, `C62 ← C60+C61`, `C63 ← C62`, `C64 ← C63`, `C65 ← C64`, `C66 ← C65`. São **sete relações entre seis workflows**. C59 já incluía a dependência C58; C60 não importa módulo de ciclo anterior.
- `contracts/cycle68-research-interfaces.v1.json`: contrato versionado do módulo `validate`, do fixture público, esquema da resposta, campos tipados e invariantes `false`. É **contrato de interface de software sintético**, não homologação de fórmula, procedimento ou parâmetro.
- `benchmarks/cycle68_integration_gate.py`: verifica AST dos imports, inventário C67, filtros para os dois eventos, contrato de saída de cada módulo sobre fixture fictício, e invariantes de autoridade. Só produz estado de integração estrutural `pass/fail`, sem jamais devolver GO.
- `tests/test_cycle68_integration_gate.py`: testes positivos e negativos, incluindo remoção simulada de um trigger, alteração indevida de esquema, tentativa de escrita SAP e ausência de módulo.
- `tests/test_cycle67_architecture_audit.py`: a expectativa anterior de encontrar sete lacunas foi atualizada para exigir **zero lacunas remanescentes**, mantendo o inventário temporal do C67 sem reescrever o passado.
- `.github/workflows/cycle68-integration-gate.yml`: regressão offline C58–C68 com recibo JSON anexado.

## Critérios de interpretação da auditoria
A inspeção do gatilho comprova que o texto do workflow inclui o caminho exigido nos blocos `push` e `pull_request`. **Não** comprova que GitHub executará o workflow sob toda política de branches, path filtering combinado, regras de proteção ou cenários de merge. O CI aprovado no commit exato é evidência adicional de execução, mas não prova observabilidade de todo evento futuro.

O smoke de interface executa `validate` com dados inventados do fixture público. A leitura de código por AST comprova presença de imports declarados, não ausência de dependências indiretas dinâmicas. O contrato registra apenas um subconjunto dos campos públicos como estáveis para futura consolidação; mudanças de versão devem ganhar revisão explícita, sem fingir compatibilidade retroativa.

**O resultado de interface `pass` não é prontidão de merge:** todos os relatórios precisam devolver `readyForMerge=false`, `operationalAuthorityGranted=false` e `decision=NO GO`. As 8 verificações humanas de QA de portal e 13 gates de evidência externa documentados no C57 não foram executados aqui, tampouco revisão humana independente ou confirmação OEM.

## Estratégia de consolidação — executar depois, com revisão
1. **Higiene de CI:** confirmar workflow C68 no SHA final, examinar o recibo, verificar zero falhas estruturais e sete arestas remediadas. Se um upstream mudar, confirmar execução do workflow downstream correspondente. Não considerar CI verde como aptidão diagnóstica.
2. **Separar lotes temáticos:** extrair C58–59 (hipóteses e observações), C60–63 (metrologia, contexto, limites e efetividade), C64–66 (documentos e pesquisa independente), preservando contratos de módulo e flags de bloqueio. Usar PRs menores contra uma base atualizada, evitando introduzir toda a cadeia histórica.
3. **Reconciliar `main`:** atualizar `compare_commits` no momento real da decisão e identificar mudanças independentes. No snapshot do C67 a branch de C66 estava 286 commits à frente e 11 atrás da `main` e havia 159 arquivos diferentes. Esses números não descrevem a branch atual nem são verificações ao vivo.
4. **Revisão humana do código e governança:** validar compatibilidade das interfaces, direitos de uso, privacidade, licenças, integridade de logs e executabilidade offline. A documentação dos ciclos 29–32 continua sendo o protocolo de custódia e avaliação separada, e não é substituída por C65–66.
5. **Aprovação técnica e estudo real são projetos diferentes:** confirmar por engenheiro competente, em ambiente autorizado, aplicabilidade de fontes e métodos. Projetar estudo independente com casos inéditos, gabaritos custodiados e julgamentos externos. Até isso existir, `NO GO` prevalece inclusive para a `main`.
6. **Proibição de merge automático:** o C68 propõe higiene; não abre ordem de serviço, não escreve no SAP/ECM, não classifica condição real, não autoriza ensaio de campo nem condena/libera equipamentos.

## Execução reproduzível
```bash
python -m unittest tests.test_cycle58_causal_gate tests.test_cycle59_observation_consistency tests.test_cycle60_metrology tests.test_cycle61_metrology_context tests.test_cycle62_reference_semantics tests.test_cycle63_effectivity tests.test_cycle64_source_governance tests.test_cycle65_review_ledger tests.test_cycle66_study_preregistration tests.test_cycle67_architecture_audit tests.test_cycle68_integration_gate -v
mkdir -p build/cycle68
python -m benchmarks.cycle68_integration_gate --output build/cycle68/interface-audit.json
```

Saída somente de resultados sintéticos, sem dados de frota, operação, série real, documentos OEM licenciados ou credenciais.

**Decisão formal do C68: NO GO operacional e integração condicionada à revisão humana e atualização da base.**
