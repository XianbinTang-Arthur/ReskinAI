#!/usr/bin/env bash
set -euo pipefail

APP_PORT=${APP_PORT:-8000}
SERVER_NAME=${SERVER_NAME:-_}
CLIENT_MAX_BODY_SIZE=${CLIENT_MAX_BODY_SIZE:-12m}
APP_DIR=${APP_DIR:-/home/ec2-user/ReskinAI}
TEMPLATE_HTTP=${TEMPLATE_HTTP:-$APP_DIR/deploy/nginx/reskinai.http.conf.template}
TARGET_CONF=${TARGET_CONF:-/etc/nginx/conf.d/reskinai.conf}

echo "[nginx] Installing nginx..."
sudo dnf install -y nginx

if [[ ! -f "$TEMPLATE_HTTP" ]]; then
  echo "[nginx] Template not found: $TEMPLATE_HTTP"
  exit 1
fi

echo "[nginx] Rendering config..."
tmp_conf=$(mktemp)
sed \
  -e "s|__SERVER_NAME__|$SERVER_NAME|g" \
  -e "s|__APP_PORT__|$APP_PORT|g" \
  -e "s|__CLIENT_MAX_BODY_SIZE__|$CLIENT_MAX_BODY_SIZE|g" \
  "$TEMPLATE_HTTP" > "$tmp_conf"

sudo cp "$tmp_conf" "$TARGET_CONF"
rm -f "$tmp_conf"

echo "[nginx] Validating config..."
sudo nginx -t

echo "[nginx] Enabling and restarting..."
sudo systemctl enable --now nginx
sudo systemctl restart nginx

echo "[nginx] Done. HTTP proxy is active on port 80."
