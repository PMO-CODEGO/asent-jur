# nginx/ — Configuração do Servidor Web

Esta pasta contém a configuração do **Nginx**, que atua como proxy reverso na frente da aplicação Flask/Gunicorn em ambiente de produção.

---

## Arquivos

### `nginx.conf`

Arquivo de configuração principal do Nginx. Define um servidor HTTP na porta `80` com as seguintes regras:

---

#### Configurações gerais

| Diretiva | Valor | Descrição |
|---|---|---|
| `server_tokens` | `off` | Oculta a versão do Nginx nos cabeçalhos HTTP de resposta, reduzindo a exposição de informações do servidor |
| `client_max_body_size` | `50M` | Permite upload de arquivos de até **50 MB** — necessário para o anexo de documentos aos processos judiciais |

---

#### `location /` — Proxy para a aplicação

Todas as requisições que chegam na raiz são repassadas para o Gunicorn rodando em `http://web:8000` (nome do serviço definido no `docker-compose.yml`).

Headers de proxy configurados:
- `Host` — repassa o host original da requisição.
- `X-Real-IP` — repassa o IP real do cliente.
- `X-Forwarded-For` — repassa a cadeia de IPs (útil quando há múltiplos proxies).

**Cabeçalhos de segurança** adicionados em todas as respostas:

| Header | Valor | Proteção |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Impede que o navegador tente "adivinhar" o tipo do conteúdo — evita ataques via MIME sniffing |
| `X-Frame-Options` | `SAMEORIGIN` | Bloqueia que a aplicação seja carregada em iframes de outros domínios — proteção contra **clickjacking** |
| `X-XSS-Protection` | `1; mode=block` | Ativa a proteção contra XSS embutida no navegador e bloqueia a página em caso de detecção |

---

#### `location /static` — Arquivos estáticos

Arquivos estáticos (imagens, logos, fotos de empresas) são servidos diretamente do disco pelo Nginx a partir da pasta `/app/static/`, **sem passar pelo Gunicorn**. Isso reduz a carga na aplicação Python e melhora o desempenho para recursos que não mudam com frequência.

O volume `./app/static` é montado no container do Nginx via `docker-compose.yml`.

---

## Arquitetura de produção

```
Usuário (navegador)
        │  porta 80
        ▼
    [ Nginx ]
    /        \
   /          \
/static    tudo o mais
  │               │
Disco        [ Gunicorn ]
(arquivos        porta 8000
estáticos)         │
              [ Flask App ]
                   │
              [ MySQL 8 ]
```
