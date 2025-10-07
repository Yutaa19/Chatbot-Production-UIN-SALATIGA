#!/bin/bash
# scripts/deploy.sh
# Deployment script untuk production

set -e  # Hentikan jika ada error

PROJECT_DIR="/home/chatbot/chatbot-rag-uin-salatiga"
LOG_FILE="$PROJECT_DIR/logs/deploy.log"

echo "$(date): Memulai deployment..." >> "$LOG_FILE"

cd "$PROJECT_DIR"

# Tarik kode terbaru
git pull origin main >> "$LOG_FILE" 2>&1

# Update dependensi (hanya production)
source venv/bin/activate
pip install -r requirements.txt --upgrade >> "$LOG_FILE" 2>&1

# Restart service (via systemd)
sudo systemctl restart chatbot.service

# Cek health endpoint
sleep 5
if curl -f http://localhost:8000/api/health >> "$LOG_FILE" 2>&1; then
    echo "$(date): Deployment berhasil." >> "$LOG_FILE"
else
    echo "$(date): ERROR: Health check gagal!" >> "$LOG_FILE"
    exit 1
fi