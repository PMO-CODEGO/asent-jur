# app/ — Núcleo da Aplicação Flask

Esta pasta contém todo o código-fonte da aplicação. A estrutura segue o padrão **Application Factory** do Flask, onde a aplicação é criada por uma função (`create_app`) em vez de ser instanciada diretamente como variável global.

---

## Estrutura

```
app/
├── routes/       # Blueprints com as rotas HTTP (controllers)
├── services/     # Lógica de negócio desacoplada das rotas
├── templates/    # Páginas HTML (Jinja2)
├── static/       # Arquivos estáticos (imagens, logos)
├── utils/        # Utilitários reutilizáveis (decorators, segurança)
├── __init__.py   # Application Factory — cria e configura o app Flask
├── config.py     # Classe de configuração da aplicação
├── constants.py  # Constantes globais (campos, labels, opções de seleção)
├── db.py         # Função de conexão com o banco de dados MySQL
└── extensions.py # Extensões Flask inicializadas separadamente (Bcrypt)
```

---

## Arquivos

### `__init__.py` — Application Factory
Contém a função `create_app()`, que:
1. Instancia o app Flask.
2. Carrega variáveis de ambiente via `python-dotenv`.
3. Aplica a configuração de `config.py`.
4. Inicializa a extensão de hash de senha (`bcrypt`).
5. Registra todos os **Blueprints** (grupos de rotas) da aplicação.

Blueprints registrados:
| Blueprint | Arquivo de origem | Área |
|---|---|---|
| `auth_login_bp` | `routes/auth_login.py` | Login e logout |
| `auth_password_bp` | `routes/auth_password.py` | Recuperação de senha |
| `auth_user_bp` | `routes/auth_user.py` | Cadastro de usuários |
| `cadastro_bp` | `routes/cadastro.py` | Cadastro de empresas e processos |
| `relatorio_bp` | `routes/relatorios.py` | Geração de relatórios em PDF |
| `logs_bp` | `routes/logs.py` | Auditoria de ações |
| `edicao_bp` | `routes/edicao.py` | Edição de dados de assentamento e processos |
| `juridico_bp` | `routes/juridico.py` | Módulo jurídico (consultas e prazos) |
| `dashboard_bp` | `routes/dashboard.py` | Menu principal |

---

### `config.py` — Configuração
Define a classe `Config` que lê variáveis sensíveis do ambiente (`.env`). Parâmetros configurados:

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave usada para assinar sessões e tokens |
| `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` | Credenciais do MySQL |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | Configurações de e-mail (Gmail) |
| `SESSION_COOKIE_SECURE` | Se `True`, cookies só trafegam por HTTPS |

---

### `constants.py` — Constantes Globais
Centraliza todas as definições de dados que são usadas em múltiplos lugares da aplicação:

- **`COLUNAS`** — Lista com os nomes internos (snake_case) de todos os campos da tabela `municipal_lots`.
- **`LABELS`** — Dicionário que mapeia cada campo interno para o seu rótulo em português para exibição no frontend.
- **`chaves_fixas`** — Subconjunto de `COLUNAS` com os campos gerenciados pelo setor de Assentamento.
- **`chaves_editaveis`** — Subconjunto de `COLUNAS` com os campos gerenciados pelo setor Jurídico (`processo_judicial`, `status`, `assunto_judicial`, `valor_da_causa`).
- **`colunas_map`** — Dicionário que mapeia os nomes das colunas das planilhas importadas para os nomes internos do banco.
- **`campos_numericos`** — Lista de campos que devem ser tratados como número.
- **`ramo_de_atividade_opcoes`** — Lista de todos os ramos de atividade disponíveis para seleção (ex: Farmacêutico, Metalúrgica, Alimentício...).
- **`status_opcoes`**, **`status_de_assentamento_opcoes`**, **`acao_judicial_opcoes`**, **`imovel_opcoes`** — Listas de valores válidos para os campos de seleção dos formulários.

---

### `db.py` — Conexão com o Banco
Exporta a função `get_db()`, que abre e retorna uma conexão MySQL usando as credenciais definidas em `config.py`. Usa `charset=utf8mb4` para suporte completo a caracteres especiais e emojis. A conexão deve ser aberta e fechada dentro de cada requisição usando `with get_db() as db:`.

---

### `extensions.py` — Extensões Flask
Instancia o objeto `Bcrypt` (para hash de senhas) fora da Application Factory. Isso é necessário para evitar dependências circulares: `__init__.py` importa `extensions.py` para inicializar o Bcrypt, e os services importam `extensions.py` para usar o Bcrypt, sem precisar importar o app inteiro.

---

## Roles (perfis de acesso)

O sistema possui os seguintes perfis, definidos no `AuthService`:

| Departamento (no banco) | Role na sessão | Acesso |
|---|---|---|
| Administrador / admin | `admin` | Acesso total, incluindo logs |
| Gestor - Assentamento | `assent_gestor` | Gestão do módulo de assentamento |
| Gestor - Jurídico | `jur_gestor` | Gestão do módulo jurídico |
| Usuário - Assentamento | `assent` | Consulta e edição no módulo de assentamento |
| Usuário - Jurídico | `jur` | Consulta e edição no módulo jurídico |
