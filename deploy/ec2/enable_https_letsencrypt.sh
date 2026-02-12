#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <domain> <email> [app_port]"
  echo "Example: $0 app.example.com devops@example.com 8000"
  exit 1
fi

DOMAIN="$1"
EMAIL="$2"
APP_PORT="${3:-8000}"
CLIENT_MAX_BODY_SIZE="${CLIENT_MAX_BODY_SIZE:-12m}"
APP_DIR=${APP_DIR:-/home/ec2-user/ReskinAI}
TEMPLATE_HTTPS=${TEMPLATE_HTTPS:-$APP_DIR/deploy/nginx/reskinai.https.conf.template}
TARGET_CONF=${TARGET_CONF:-/etc/nginx/conf.d/reskinai.conf}

echo "[https] Installing certbot..."
sudo dnf install -y certbot python3-certbot-nginx

if [[ ! -f "$TEMPLATE_HTTPS" ]]; then
  echo "[https] Template not found: $TEMPLATE_HTTPS"
  exit 1
fi

echo "[https] Issuing certificate for $DOMAIN ..."
sudo certbot certonly --nginx \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN"

echo "[https] Rendering HTTPS nginx config..."
tmp_conf=$(mktemp)
sed \
  -e "s|__DOMAIN__|$DOMAIN|g" \
  -e "s|__APP_PORT__|$APP_PORT|g" \
  -e "s|__CLIENT_MAX_BODY_SIZE__|$CLIENT_MAX_BODY_SIZE|g" \
  "$TEMPLATE_HTTPS" > "$tmp_conf"

sudo cp "$tmp_conf" "$TARGET_CONF"
rm -f "$tmp_conf"

echo "[https] Validating nginx config..."
sudo nginx -t
sudo systemctl restart nginx

if systemctl list-unit-files | grep -q certbot-renew.timer; then
  sudo systemctl enable --now certbot-renew.timer
fi

echo "[https] HTTPS enabled for $DOMAIN."
