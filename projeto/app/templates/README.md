# app/templates/ — Templates HTML

Esta pasta contém todos os arquivos de template HTML da aplicação, renderizados pelo motor **Jinja2** do Flask. Cada arquivo corresponde a uma tela ou fragmento de tela exibido ao usuário.

---

## Autenticação e Usuários

| Arquivo | Descrição |
|---|---|
| `login.html` | Tela de login — página inicial da aplicação (rota `/`) |
| `recuperar_senha.html` | Formulário onde o usuário informa o e-mail para receber o link de recuperação de senha |
| `redefinir_senha.html` | Formulário de redefinição de senha, acessado via link com token enviado por e-mail |
| `registrar_usuario.html` | Formulário de auto-cadastro de novos usuários |
| `registrar_colaborador.html` | Formulário de cadastro de colaborador preenchido por gestores — o departamento é pré-definido com base no perfil do gestor logado |

---

## Menus e Navegação

| Arquivo | Descrição |
|---|---|
| `menu.html` | Menu principal do módulo de **Assentamento** — exibido após login de usuários do setor de assentamento |
| `menu_jur.html` | Menu principal do módulo **Jurídico** — exibido após login de usuários do setor jurídico |

---

## Módulo de Assentamento

| Arquivo | Descrição |
|---|---|
| `cadastro.html` | Formulário de cadastro de novo lote/empresa no módulo de Assentamento |
| `selecionar_edicao.html` | Listagem de empresas para seleção antes de editar — exibe indicadores visuais de atualização vencida (mais de 1 ano sem atualização) |
| `editar.html` | Formulário de edição dos dados de assentamento de uma empresa |
| `relatorios.html` | Página de geração de relatórios do módulo de Assentamento |

---

## Módulo Jurídico

| Arquivo | Descrição |
|---|---|
| `cadastro_jur.html` | Formulário de cadastro de novo processo judicial, com campos para partes, prazos, movimentações e documentos |
| `importar_processos_jur.html` | Tela de importação de processos em lote via planilha `.csv` ou `.xlsx`, com etapa de mapeamento de colunas |
| `editar_jur.html` | Formulário de edição completa de um processo judicial |
| `detalhe_jur.html` | Tela de detalhes de um processo judicial — exibe histórico de alterações, partes vinculadas, prazos, movimentações e documentos anexados |
| `consulta_assentamento_jur.html` | Listagem de todos os lotes/empresas para consulta pelo setor Jurídico |
| `detalhe_assentamento_jur.html` | Detalhes de um lote/empresa específico, exibindo apenas os campos de assentamento (visão somente leitura para o Jurídico) |
| `prazos_jur.html` | Painel de monitoramento de prazos processuais com filtros por situação: vencido, hoje, próximo, futuro, sem data |
| `relatorios_jur.html` | Página de geração de relatórios do módulo Jurídico |

---

## Administração

| Arquivo | Descrição |
|---|---|
| `logs.html` | Tabela de auditoria de ações do sistema — acessível apenas por administradores. Exibe os últimos 1.000 registros com filtro por usuário e por período. |

---

## Parciais (fragmentos reutilizáveis)

A subpasta `partials/` contém fragmentos HTML incluídos em outras páginas via Jinja2:

| Arquivo | Incluído em | Descrição |
|---|---|---|
| `partials/processo_eventos_lista.html` | `detalhe_jur.html` | Renderiza a lista de eventos de um processo (prazos, movimentações, histórico de alterações) de forma reutilizável |
