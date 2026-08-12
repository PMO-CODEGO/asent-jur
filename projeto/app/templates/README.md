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
| `inicio_assent.html` | Tela inicial do módulo de **Assentamento** (rota `/assent/inicio`) — atalhos para Controle de Área e para o módulo Jurídico |
| `menu_jur.html` | Menu renderizado pela rota `/menu/<modo>` — na prática é a única tela que essa rota exibe, independente do `modo` |
| `mapa_distritos.html` | Mapa dos distritos industriais/agroindustriais administrados pela CODEGO, compartilhado entre Assentamento e Jurídico |
| `distrito_detalhe.html` | Página de detalhe de um distrito específico do mapa (dados vêm do dicionário `DISTRITOS` em `routes/dashboard.py`, não do banco) |

---

## Módulo de Assentamento

| Arquivo | Descrição |
|---|---|
| `cadastro.html` | Formulário de cadastro de novo lote/empresa no módulo de Assentamento. Select de município populado por `municipio_service.listar_municipios()`. |
| `selecionar_edicao.html` | Listagem de empresas para seleção antes de editar — exibe indicadores visuais de atualização vencida (mais de 1 ano sem atualização) |
| `editar.html` | Formulário de edição dos dados de assentamento de uma empresa |
| `relatorios.html` | Página de geração de relatórios do módulo de Assentamento |
| `controle_area.html` | Hub (rota `/assent/controle-area`) com cards de navegação para Áreas Brutas, Galerias/Condomínio, Áreas Parceladas e Cadastro de Módulos |
| `areas_brutas.html` | Listagem de imóveis das tabelas `areas_brutas` e `areas_brutas_judicial`, com avaliações de valor por ano (2021–2024) |
| `areas_brutas_form.html` | Formulário de criação/edição de um registro de área bruta |
| `areas_parceladas.html` | Listagem de `areas_parceladas_regularizadas` e `loteamentos_irregulares` lado a lado, com painéis de detalhe expansíveis por linha |
| `areas_brutas_parceladas_form.html` | Formulário compartilhado de criação/edição para as três famílias de área parcelada (regularizadas, galerias/condomínio e loteamentos irregulares) |
| `galerias.html` | Listagem dos registros de `galerias_condominios` |
| `cadastro_modulos.html` | Listagem dos registros de `municipal_lots` por município/distrito/quadra/módulo |
| `cadastro_modulos_form.html` | Formulário de criação/edição de um registro de módulo |

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
| `partials/guia_mascote.html` | 17 telas principais (ver abaixo) | Codi — personagem-guia flutuante (mascote no canto inferior direito) com dicas contextuais por tela |

### Codi, o personagem-guia (`guia_mascote.html`)

Widget autocontido (HTML + CSS + JS inline, sem dependências externas) que mostra o Codi — mascote da CODEGO — como um avatar flutuante com dicas sobre a tela atual, escritas na primeira pessoa como se ele estivesse falando (ver conteúdo em `app/services/guia_service.py`). Duas imagens em `app/static/`: `mascote_codego.png` (corpo inteiro, pose parada, usada no botão flutuante) e `mascote_codego_apontando.png` (pose apontando, usada no cabeçalho do balão de dicas). Para incluir numa tela nova:

```jinja
{% set guia_pagina = 'cadastro' %}{% include 'partials/guia_mascote.html' %}
```

logo antes do `</body>`. O conteúdo (contexto da tela + lista de falas) de cada `guia_pagina` fica centralizado em `app/services/guia_service.py` (`GUIA_CONTEUDO`), exposto aos templates como a função global do Jinja `guia_dicas(pagina)` (registrada em `app/__init__.py`). Se a chave não existir no dicionário, o `{% include %}` não renderiza nada — então basta adicionar a entrada em `guia_service.py` para "ligar" o Codi numa tela que já tem o include, ou adicionar as duas linhas (entrada + include) numa tela nova.

O balão tem um "rabinho" apontando para o Codi no botão flutuante, reforçando que é ele quem está falando. Na primeira visita de cada tela (controlado via `localStorage`, `guia_visto_<pagina>`) o balão já abre sozinho; depois de fechado uma vez, só reabre se o usuário clicar no botão.
