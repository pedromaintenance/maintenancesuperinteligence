# Revisão humana dos portais — formulário de trabalho

**Ciclo 54 · modelo de revisão, não laudo.** A presença deste arquivo não significa que alguém realizou os testes nem permite operar máquinas.

O revisor deve inspecionar o portal de conhecimento, o de auditoria e o de versões, em desktop e mobile. Registre falhas, ambiente, navegador, passo para reprodução e evidência acessível a quem for autorizado. O arquivo `review/portal_qa_template.v1.json` é um **modelo com todos os estados `not_tested`**, não uma homologação; não use nome completo, dados pessoais ou captura de documento interno em publicação pública.

| Verificação | Evidência a obter |
| --- | --- |
| `mobile_layout`: Em 320–390 px, menus e conteúdos devem permanecer legíveis sem sobreposição de controles | Navegador em smartphone real ou emulação de viewport, com capturas das três páginas |
| `zoom_reflow`: A 200% e 400% de zoom, leitura e ações continuam acessíveis | Navegador com zoom e quebra de linhas, com evidências |
| `keyboard_skip_focus`: Tab alcança o salto ao conteúdo, mantém foco visível e navega por links/botões | Usar exclusivamente teclado, gravando sequência e bloqueios |
| `audit_tabs`: Setas esquerda/direita, Home e End alternam as abas e preservam sentido do painel | Usar teclado, confirmar aria-selected e conteúdo exibido |
| `screen_reader`: Leitor de tela lê títulos, estados, links, filtros e alterações anunciadas | NVDA/VoiceOver real; registrar ambiente e ocorrências |
| `status_clarity`: Há distinção inequívoca entre deploy HTTP, revisão humana e validade mecânica | Ler os três portais e verificar NO GO, gates e snapshot histórico |
| `export_integrity`: JSON exportado de cada portal corresponde ao que está exibido | Acionar exportações e confrontar contagens/identificadores |
| `sources_permissions`: Links públicos não expõem dados corporativos restritos, credenciais ou literatura OEM licenciada | Revisão humana de conteúdo e permissões por custodiante autorizado |

**Critério mínimo de aceite documental:** registrar o resultado de cada verificação, abrir defeitos reproduzíveis para achados e obter revisão explícita do responsável pelo conteúdo público. A aprovação de publicação *não* substitui alçada de engenharia, SST, privacidade ou OEM.

### Separação das alçadas

- **Automatizado:** integridade SHA-256 de arquivos publicados via HTTP, após sucesso do GitHub Actions.
- **Revisão humana:** usabilidade, legibilidade, experiência com leitores de tela, pertinência e confidencialidade dos dados.
- **Validação mecânica:** processo independente com fontes aplicáveis, profissionais competentes e os 13 gates externos do estudo.

**Pendente:** executar checklist em browsers reais. **NO GO** para controle de máquinas, abertura de OS, alteração SAP/ECM e liberação.
