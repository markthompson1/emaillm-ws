#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
git pull origin main
./.venv/bin/pip install --upgrade -r requirements.txt
sudo systemctl restart emaillm
echo "Deployed to VPS"
