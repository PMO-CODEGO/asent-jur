# ASSENT JUR

Sistema web desenvolvido para gerenciamento jurídico e administrativo de processos.

O projeto foi desenvolvido utilizando Flask, MySQL, Docker e Nginx, oferecendo funcionalidades relacionadas a autenticação, cadastro, relatórios, dashboard e controle jurídico.

---

# Tecnologias Utilizadas

* Python 3
* Flask
* MySQL 8
* Docker
* Docker Compose
* Nginx
* Gunicorn
* Jinja2
* OpenPyXL
* ReportLab

---

# Estrutura do Projeto

```bash
projeto/
├── app/
│   ├── routes/          # Rotas da aplicação
│   ├── services/        # Regras de negócio e serviços
│   ├── static/          # Arquivos estáticos
│   ├── templates/       # Templates HTML
│   ├── utils/           # Decorators e utilitários
│   ├── config.py        # Configurações da aplicação
│   └── db.py            # Configuração do banco de dados
├── backups/             # Dumps do banco gerados pelo serviço de backup
├── docker/
│   ├── backup/          # Imagem que roda o backup periódico do MySQL
│   └── mysql/init/      # Scripts de inicialização do MySQL
├── nginx/               # Configuração do Nginx
├── uploads/             # Upload de arquivos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.py
```

---

# Funcionalidades

* Autenticação de usuários
* Recuperação de senha
* Cadastro e edição de registros
* Dashboard administrativo
* Controle jurídico de processos
* Geração de relatórios
* Exportação de arquivos
* Registro de logs
* Upload e gerenciamento de documentos

---

# Pré-requisitos

Antes de executar o projeto, certifique-se de possuir instalado:

* Docker
* Docker Compose

Ou, caso deseje rodar localmente:

* Python 3.11+
* MySQL 8
* pip

---

# Variáveis de Ambiente

Crie um arquivo `.env` dentro de `projeto/` (use o [.env.example](projeto/.env.example) como base) com as seguintes variáveis:

```env
SECRET_KEY=sua_chave_secreta

DB_HOST=db
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=codego_db

FLASK_ENV=production

SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

MYSQL_ROOT_PASSWORD=sua_senha
MYSQL_PASSWORD=sua_senha
```

`MYSQL_ROOT_PASSWORD` e `MYSQL_PASSWORD` são lidas pelo `docker-compose.yml` para configurar o container do MySQL e o serviço de backup — devem ter o mesmo valor de `DB_PASSWORD`. **Nunca** commite o `.env` real; ele já está no `.gitignore`.

---

# Executando com Docker

## 1. Clonar o repositório

```bash
git clone https://github.com/PMO-CODEGO/asent-jur.git
cd asent-jur/projeto
```

## 2. Subir os containers

```bash
docker compose up --build
```

## 3. Acessar a aplicação

Abra no navegador:

```bash
http://localhost
```

---

# Executando Localmente

## 1. Criar ambiente virtual

### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 2. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 3. Configurar banco de dados

Crie um banco MySQL e ajuste as variáveis do arquivo `.env`.

---

## 4. Executar aplicação

```bash
python run.py
```

A aplicação estará disponível em:

```bash
http://127.0.0.1:5000
```

---

# Dependências Principais

```txt
Flask
Flask-Bcrypt
mysql-connector-python
reportlab
openpyxl
gunicorn
python-dotenv
```

---

# Arquitetura da Aplicação

O sistema segue uma organização baseada em:

* Routes → Controle das rotas HTTP
* Services → Regras de negócio
* Templates → Interface HTML
* Static → Arquivos estáticos
* Database → Integração com MySQL

---

# Melhorias Futuras

* Implementação de testes automatizados
* Pipeline CI/CD
* Controle de permissões por perfil
* API REST
* Logs centralizados
* Deploy em cloud

---

# Segurança

Recomendações para ambiente de produção:

* Alterar a senha padrão do MySQL
* Utilizar HTTPS
* Configurar variáveis sensíveis no ambiente (nunca em texto puro no `docker-compose.yml` ou em outros arquivos versionados)
* Não versionar arquivos `.env`
* Configurar backup do banco de dados (já feito pelo serviço `backup` do `docker-compose.yml`, ver [docker/backup](projeto/docker/backup))
* Adicionar proteção CSRF nos formulários (ainda não implementada)
* Servir a aplicação por HTTPS — hoje roda em HTTP puro (`SESSION_COOKIE_SECURE = False` em `app/config.py`)

---

# Licença

Este projeto é de uso interno da CODEGO.

---

# Autor

Desenvolvido para o projeto ASENT JUR.
