# ASENT JUR

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
projeto_teste/
├── app/
│   ├── routes/          # Rotas da aplicação
│   ├── services/        # Regras de negócio e serviços
│   ├── static/          # Arquivos estáticos
│   ├── templates/       # Templates HTML
│   ├── config.py        # Configurações da aplicação
│   └── db.py            # Configuração do banco de dados
├── docker/
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

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
SECRET_KEY=sua_chave_secreta

DB_HOST=db
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=codego_db
DB_PORT=3306

SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_email
```

---

# Executando com Docker

## 1. Clonar o repositório

```bash
git clone https://github.com/PMO-CODEGO/asent-jur.git
cd asent-jur/projeto_teste
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
* Configurar variáveis sensíveis no ambiente
* Não versionar arquivos `.env`
* Configurar backup do banco de dados

---

# Licença

Este projeto é de uso interno da CODEGO.

---

# Autor

Desenvolvido para o projeto ASENT JUR.
