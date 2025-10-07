#!/bin/bash
# scripts/backup.sh
# Backup harian Qdrant ke Google Cloud Storage

set -e

PROJECT_DIR="/home/chatbot/chatbot-rag-uin-salatiga"
BACKUP_DIR="/tmp/qdrant-backup-$(date +%Y%m%d)"
BUCKET="gs://uin-chatbot-backup"

# Buat snapshot Qdrant
curl -X POST "http://localhost:6333/collections/campus_knowledge/snapshots" \
  -H "Content-Type: application/json" >> /dev/null

# Salin snapshot ke folder sementara
mkdir -p "$BACKUP_DIR"
cp /qdrant/storage/snapshots/campus_knowledge/*.snapshot "$BACKUP_DIR/" 2>/dev/null || true

# Upload ke Cloud Storage
if [ -n "$(ls -A $BACKUP_DIR)" ]; then
    gsutil -m cp "$BACKUP_DIR"/*.snapshot "$BUCKET/$(date +%Y/%m/%d)/"
    echo "$(date): Backup Qdrant berhasil ke $BUCKET"
else
    echo "$(date): Tidak ada snapshot ditemukan."
fi

# Bersihkan
rm -rf "$BACKUP_DIR"