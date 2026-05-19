# README — Pasta `routes`

## Visão Geral

A pasta `routes` é responsável por definir todas as rotas HTTP da aplicação Flask. Cada arquivo representa um conjunto específico de funcionalidades do sistema, organizadas por contexto de negócio.

As rotas funcionam como a camada de comunicação entre:

* Frontend (templates HTML/forms)
* Serviços (`services`)
* Banco de dados
* Controle de autenticação/autorização

A estrutura utiliza `Blueprints` do Flask para modularizar o sistema e facilitar manutenção, escalabilidade e separação de responsabilidades.

---

# Estrutura da Pasta

```bash
routes/
│
├── auth_login.py
├── auth_password.py
├── auth_user.py
├── cadastro.py
├── dashboard.py
├── edicao.py
├── juridico.py
├── logs.py
└── relatorios.py
```

---

# Arquivos da Pasta `routes`

## 1. `auth_login.py`

### Responsabilidade

Responsável pelo fluxo de autenticação dos usuários do sistema.

### Principais Funcionalidades

* Exibição da tela de login
* Validação de credenciais
* Criação de sessão do usuário
* Redirecionamento por nível de acesso
* Logout

### Blueprint

```python
Blueprint("auth_login", __name__)
```

### Rotas Principais

| Rota      | Método   | Descrição                  |
| --------- | -------- | -------------------------- |
| `/`       | GET      | Exibe tela de login        |
| `/login`  | GET/POST | Realiza autenticação       |
| `/logout` | GET      | Finaliza sessão do usuário |

### Dependências

* `AuthService`
* `session`
* `flash`
* `redirect`
* `render_template`

### Objetivo Técnico

Centralizar toda a lógica inicial de autenticação e controle de sessão.

---

## 2. `auth_password.py`

### Responsabilidade

Gerencia funcionalidades relacionadas à recuperação e redefinição de senha.

### Principais Funcionalidades

* Solicitação de recuperação de senha
* Geração de token de recuperação
* Validação de token
* Definição de nova senha

### Blueprint

```python
Blueprint("auth_password", __name__)
```

### Rotas Principais

| Rota                       | Método   | Descrição                       |
| -------------------------- | -------- | ------------------------------- |
| `/recuperar-senha`         | GET/POST | Solicita recuperação de senha   |
| `/redefinir-senha/<token>` | GET/POST | Redefine senha utilizando token |

### Dependências

* `AuthService`
* `TokenService`
* `flash`
* `render_template`

### Objetivo Técnico

Permitir recuperação segura de acesso ao sistema.

---

## 3. `auth_user.py`

### Responsabilidade

Responsável pelo gerenciamento de usuários e colaboradores.

### Principais Funcionalidades

* Registro de usuários
* Cadastro de colaboradores
* Controle de permissões
* Restrição por perfil de acesso

### Blueprint

```python
Blueprint("auth_user", __name__)
```

### Rotas Principais

| Rota                     | Método   | Descrição                 |
| ------------------------ | -------- | ------------------------- |
| `/registrar-usuario`     | GET/POST | Cria novos usuários       |
| `/registrar-colaborador` | GET/POST | Cadastro de colaboradores |

### Dependências

* `AuthService`
* `role_required`
* `session`

### Objetivo Técnico

Controlar criação e gerenciamento de usuários do sistema.

---

## 4. `cadastro.py`

### Responsabilidade

Arquivo central do sistema responsável pelo cadastro de assentamentos, empresas e processos.

### Principais Funcionalidades

* Cadastro de processos
* Upload de arquivos
* Importação de planilhas
* Registro de histórico
* Integração com serviços jurídicos
* Controle de documentos
* Gravação de logs

### Blueprint

```python
Blueprint("cadastro", __name__)
```

### Funcionalidades Técnicas

* Upload seguro com `secure_filename`
* Geração de UUID para arquivos
* Integração com banco de dados
* Importação CSV/planilhas
* Registro de auditoria
* Histórico de alterações

### Dependências Importantes

* `CadastroService`
* `processo_documento_service`
* `processo_historico_service`
* `importacao_processos_service`
* `log_service`

### Objetivo Técnico

Centralizar o fluxo principal de cadastro e gerenciamento de processos do sistema.

---

## 5. `dashboard.py`

### Responsabilidade

Responsável pelo menu principal e navegação inicial do sistema.

### Principais Funcionalidades

* Exibição de menus por perfil
* Direcionamento entre módulos
* Controle de acesso por papel

### Blueprint

```python
Blueprint("dashboard", __name__)
```

### Rotas Principais

| Rota           | Método | Descrição                  |
| -------------- | ------ | -------------------------- |
| `/menu/<modo>` | GET    | Exibe menu conforme perfil |

### Dependências

* `role_required`
* `render_template`

### Objetivo Técnico

Fornecer interface inicial adequada para cada tipo de usuário.

---

## 6. `edicao.py`

### Responsabilidade

Gerencia edição de processos, documentos e informações cadastradas.

### Principais Funcionalidades

* Edição de processos
* Atualização de documentos
* Histórico de alterações
* Controle de mudanças
* Busca de processos
* Registro de auditoria

### Blueprint

```python
Blueprint("edicao", __name__)
```

### Funcionalidades Técnicas

* Comparação de alterações
* Controle de histórico
* Upload de documentos
* Busca paginada
* Manipulação de datas

### Dependências Importantes

* `CadastroService`
* `processo_historico_service`
* `processo_busca_service`
* `log_service`

### Objetivo Técnico

Permitir manutenção e atualização segura dos registros do sistema.

---

## 7. `juridico.py`

### Responsabilidade

Responsável pelo módulo jurídico da aplicação.

### Principais Funcionalidades

* Consulta de assentamentos
* Controle de prazos jurídicos
* Filtros jurídicos
* Integração com schema jurídico
* Visualização de processos

### Blueprint

```python
Blueprint("juridico", __name__)
```

### Rotas Principais

| Rota                | Método | Descrição                        |
| ------------------- | ------ | -------------------------------- |
| `/jur/assentamento` | GET    | Consulta assentamentos jurídicos |

### Dependências

* `prazo_service`
* `juridico_schema_service`
* `get_db`

### Objetivo Técnico

Isolar funcionalidades relacionadas ao departamento jurídico.

---

## 8. `logs.py`

### Responsabilidade

Gerencia visualização e filtragem de logs do sistema.

### Principais Funcionalidades

* Consulta de logs
* Filtro por usuário
* Filtro por período
* Auditoria de ações
* Monitoramento administrativo

### Blueprint

```python
Blueprint("logs", __name__)
```

### Rotas Principais

| Rota    | Método | Descrição                 |
| ------- | ------ | ------------------------- |
| `/logs` | GET    | Visualiza logs do sistema |

### Dependências

* `get_db`
* `role_required`

### Objetivo Técnico

Garantir rastreabilidade e auditoria das ações executadas no sistema.

---

## 9. `relatorios.py`

### Responsabilidade

Responsável pela geração de relatórios e exportações do sistema.

### Principais Funcionalidades

* Geração de PDF
* Exportação de relatórios
* Construção dinâmica de tabelas
* Inserção de marca d’água
* Relatórios jurídicos
* Relatórios empresariais

### Blueprint

```python
Blueprint("relatorio", __name__)
```

### Funcionalidades Técnicas

* Uso da biblioteca `ReportLab`
* Geração dinâmica de PDF
* Manipulação de memória com `BytesIO`
* Customização visual de tabelas

### Dependências Importantes

* `pdf_service`
* `ReportLab`
* `juridico_schema_service`
* `get_db`

### Objetivo Técnico

Centralizar toda a geração documental do sistema.

---

# Arquitetura Utilizada

A pasta `routes` segue uma arquitetura baseada em:

* Flask Blueprints
* Separação por domínio
* Services Layer
* Controle de acesso via decorators
* Integração com banco de dados
* Templates HTML

Fluxo simplificado:

```text
Usuário → Route → Service → Banco de Dados → Template/Resposta
```

---

# Controle de Permissões

Grande parte das rotas utiliza o decorator:

```python
@role_required(...)
```

Esse mecanismo restringe acesso conforme perfil do usuário.

Perfis encontrados no sistema:

* `admin`
* `jur`
* `jur_gestor`
* `assent`
* `assent_gestor`

---

# Observações Técnicas

## Uso de Blueprints

Todos os módulos utilizam `Blueprints`, permitindo:

* Modularização
* Facilidade de manutenção
* Separação de responsabilidades
* Escalabilidade

## Uso de Services

As regras de negócio ficam concentradas na pasta `services`, enquanto as rotas apenas:

* Recebem requisições
* Validam entradas
* Chamam serviços
* Retornam respostas

## Auditoria

O sistema possui rastreamento de ações através:

* Logs
* Histórico de processos
* Controle de alterações

---

# Conclusão

A pasta `routes` representa a camada principal de comunicação da aplicação Flask, organizando funcionalidades por domínio e mantendo separação clara entre autenticação, cadastro, jurídico, relatórios, edição e auditoria.

Essa estrutura facilita:

* Escalabilidade
* Organização do código
* Segurança
* Reutilização
* Manutenção futura
* Controle de acesso
