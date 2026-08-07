# docker/backup/ — Backup Automático do Banco de Dados

Esta pasta contém a imagem Docker responsável por gerar backups periódicos do banco de dados MySQL. Corresponde ao serviço **`backup`** do `docker-compose.yml` (container `codego_backup`).

---

## Arquivos

### `Dockerfile`
Baseada na própria imagem `mysql:8` (para ter o `mysqldump` disponível sem precisar instalar nada extra). Instala o `cronie` para agendamento via cron, copia o `backup.sh` para dentro da imagem e registra um cron job que roda esse script **todos os dias às 02:00**, com saída redirecionada para `/var/log/backup.log` dentro do container. O comando principal (`CMD`) é `crond -n`, que mantém o cron rodando em primeiro plano — é isso que mantém o container vivo.

### `backup.sh`
Script que gera o dump do banco a cada execução:
1. Roda `mysqldump` (com `--single-transaction --routines --triggers`) contra o banco definido em `MYSQL_DATABASE`, usando as credenciais de `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD`.
2. Comprime a saída com `gzip` e salva em `/backups/codego_db_<data>_<hora>.sql.gz`.
3. Remove dumps antigos com `find "$BACKUP_DIR" -name "codego_db_*.sql.gz" -mtime +5 -delete`.

> **Atenção:** o comentário do script e a mensagem de log dizem que backups com mais de 30 dias são removidos, mas o comando real (`-mtime +5`) apaga qualquer arquivo com mais de **5 dias**. Um dos dois está errado — vale confirmar qual retenção é a pretendida antes de depender disso em produção.

---

## Configuração (via `docker-compose.yml`)

O serviço `backup` recebe as credenciais do banco por variável de ambiente e monta o volume `./backups:/backups` (pasta `backups/` na raiz de `projeto/`) para persistir os dumps fora do container, mesmo que ele seja recriado:

| Variável | Valor |
|---|---|
| `MYSQL_HOST` | `db` (nome do serviço do MySQL na rede interna do Compose) |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | `${MYSQL_ROOT_PASSWORD}` (lida do `.env` da raiz de `projeto/`) |
| `MYSQL_DATABASE` | `codego_db` |

---

## Como restaurar um backup manualmente

```bash
gunzip -c backups/codego_db_AAAA-MM-DD_HH-MM.sql.gz | docker exec -i mysql_sistema mysql -uroot -p codego_db
```

Substitua o nome do arquivo pelo dump desejado (listados em `projeto/backups/`) e informe a senha do MySQL quando solicitado.
