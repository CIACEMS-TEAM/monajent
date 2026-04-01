#!/bin/bash
# Backup PostgreSQL automatique
# Exécuté par cron dans le container backup

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="monajent_${TIMESTAMP}.sql.gz"
KEEP_DAYS=${BACKUP_KEEP_DAYS:-7}

echo "[$(date)] Démarrage backup PostgreSQL..."

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST:-postgres}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-monajent}" \
    -d "${POSTGRES_DB:-monajent}" \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_DIR}/${FILENAME}"

SIZE=$(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)
echo "[$(date)] Backup créé: ${FILENAME} (${SIZE})"

# Nettoyage des anciens backups
echo "[$(date)] Nettoyage des backups > ${KEEP_DAYS} jours..."
find "${BACKUP_DIR}" -name "monajent_*.sql.gz" -mtime +${KEEP_DAYS} -delete

COUNT=$(ls -1 "${BACKUP_DIR}"/monajent_*.sql.gz 2>/dev/null | wc -l)
echo "[$(date)] Terminé. ${COUNT} backup(s) conservé(s)."
