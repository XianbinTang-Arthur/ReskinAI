#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/home/ec2-user/ReskinAI}
ENV_FILE=${ENV_FILE:-$APP_DIR/.env.prod}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.prod.yml}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[deploy] Missing environment file: $ENV_FILE"
  exit 1
fi

cd "$APP_DIR"

echo "[deploy] Pulling latest images and building app..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull || true
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

echo "[deploy] Service status:"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

echo "[deploy] Health check:"
curl -fsS http://127.0.0.1:${APP_PORT:-8000}/healthz || true
