# projeto — Raiz do Projeto

Este é o diretório principal da aplicação **CODEGO / Asent-Jur**, um sistema web desenvolvido em Python/Flask para gestão de assentamentos industriais e processos jurídicos dos distritos industriais administrados pela CODEGO (Companhia de Desenvolvimento Econômico de Goiás).

---

## Estrutura de pastas

```
projeto/
├── app/                  # Código-fonte da aplicação Flask
├── backups/              # Dumps .sql.gz gerados pelo serviço de backup
├── docker/
│   ├── backup/           # Imagem que roda o backup periódico do MySQL
│   └── mysql/init/       # Scripts SQL de inicialização do banco
├── nginx/                # Configuração do servidor web Nginx
├── uploads/              # Arquivos enviados pelos usuários (documentos, imagens)
├── .env / .env.example   # Variáveis de ambiente (.env não é versionado)
├── Dockerfile            # Imagem Docker da aplicação
├── docker-compose.yml    # Orquestração dos serviços (web, db, backup, nginx)
├── requirements.txt      # Dependências Python do projeto
└── run.py                # Ponto de entrada da aplicação
```

---

## Arquivos da raiz

### `run.py`
Ponto de entrada da aplicação. Chama `create_app()` do módulo `app` para inicializar o Flask e sobe o servidor em modo de desenvolvimento (`debug=True`). Em produção, esse arquivo é ignorado — o Gunicorn é iniciado diretamente pelo Dockerfile.

### `requirements.txt`
Lista todas as dependências Python necessárias para rodar a aplicação. Principais bibliotecas:

| Biblioteca | Finalidade |
|---|---|
| `Flask` | Framework web principal |
| `gunicorn` | Servidor WSGI para produção |
| `Flask-Bcrypt` / `bcrypt` | Hash seguro de senhas |
| `mysql-connector-python` | Conexão com o banco MySQL |
| `reportlab` | Geração de PDFs |
| `openpyxl` | Leitura e escrita de planilhas `.xlsx` |
| `python-dotenv` | Carregamento de variáveis de ambiente via `.env` |
| `itsdangerous` | Geração e validação de tokens seguros (recuperação de senha) |
| `Jinja2` / `MarkupSafe` | Motor de templates HTML |

### `Dockerfile`
Define a imagem Docker da aplicação. Usa `python:3.11-slim` como base, instala as dependências do sistema (compilador C e cliente MySQL), copia o código e sobe a aplicação com **Gunicorn** em 4 workers na porta `8000`.

### `docker-compose.yml`
Orquestra quatro serviços:
- **`web`** — A aplicação Flask/Gunicorn (container `codego_app`). Depende do banco de dados e lê variáveis de ambiente de um arquivo `.env`. O healthcheck usa `python -c "import urllib.request; ..."` (não `curl`, que não está instalado na imagem).
- **`db`** — MySQL 8 (container `mysql_sistema`). Inicializa o banco automaticamente com os scripts SQL da pasta `docker/mysql/init/`. Os dados são persistidos em um volume Docker. A porta `3307` do host é mapeada para a `3306` do container.
- **`backup`** — Container que roda `docker/backup/backup.sh` periodicamente (via cron, todo dia às 02:00), gerando dumps `.sql.gz` do banco em `backups/` e removendo os mais antigos. Ver [docker/backup/README.md](docker/backup/README.md).
- **`nginx`** — Proxy reverso que recebe as requisições na porta `80` e as repassa para o Gunicorn na porta `8000`. Também serve arquivos estáticos diretamente.

### `.dockerignore`
Lista arquivos e pastas que não devem ser copiados para dentro da imagem Docker durante o build, como caches, arquivos temporários e credenciais.

---

## Como rodar localmente

1. Crie um arquivo `.env` na raiz (use o [.env.example](.env.example) como base) com as variáveis: `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SMTP_USER`, `SMTP_PASS`, `SMTP_SERVER`, `SMTP_PORT`, `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`.
2. Execute:
   ```bash
   docker-compose up --build
   ```
3. Acesse `http://localhost` no navegador.
