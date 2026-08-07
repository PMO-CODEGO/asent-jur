#!/bin/sh
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y-%m-%d_%H-%M)
FILE="$BACKUP_DIR/codego_db_$DATE.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Iniciando backup..."
mysqldump \
  -h "$MYSQL_HOST" \
  -u "$MYSQL_USER" \
  -p"$MYSQL_PASSWORD" \
  --single-transaction \
  --routines \
  --triggers \
  "$MYSQL_DATABASE" | gzip > "$FILE"

echo "[$(date)] Backup salvo: $FILE"

# Remove backups com mais de 30 dias
find "$BACKUP_DIR" -name "codego_db_*.sql.gz" -mtime +30 -delete
echo "[$(date)] Backups antigos removidos (>30 dias)."
