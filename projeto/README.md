# projeto — Raiz do Projeto

Este é o diretório principal da aplicação **CODEGO / Asent-Jur**, um sistema web desenvolvido em Python/Flask para gestão de assentamentos industriais e processos jurídicos dos distritos industriais administrados pela CODEGO (Companhia de Desenvolvimento Econômico de Goiás).

---

## Estrutura de pastas

```
projeto/
├── app/                  # Código-fonte da aplicação Flask
├── docker/               # Configurações do banco de dados MySQL (scripts SQL)
├── nginx/                # Configuração do servidor web Nginx
├── output/               # Arquivos gerados pela aplicação (PDFs)
├── tmp/                  # Arquivos temporários de desenvolvimento (não vai para produção)
├── Dockerfile            # Imagem Docker da aplicação
├── docker-compose.yml    # Orquestração dos serviços (app, banco, nginx)
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
Orquestra três serviços:
- **`web`** — A aplicação Flask/Gunicorn. Depende do banco de dados e lê variáveis de ambiente de um arquivo `.env`.
- **`db`** — MySQL 8. Inicializa o banco automaticamente com os scripts SQL da pasta `docker/mysql/init/`. Os dados são persistidos em um volume Docker.
- **`nginx`** — Proxy reverso que recebe as requisições na porta `80` e as repassa para o Gunicorn na porta `8000`. Também serve arquivos estáticos diretamente.

### `.dockerignore`
Lista arquivos e pastas que não devem ser copiados para dentro da imagem Docker durante o build, como caches, arquivos temporários e credenciais.

---

## Como rodar localmente

1. Crie um arquivo `.env` na raiz com as variáveis: `SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`, `SMTP_USER`, `SMTP_PASS`.
2. Execute:
   ```bash
   docker-compose up --build
   ```
3. Acesse `http://localhost` no navegador.
