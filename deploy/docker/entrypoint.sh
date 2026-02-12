#!/usr/bin/env sh
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] Running database migrations..."
  attempts=0
  until alembic upgrade head; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 30 ]; then
      echo "[entrypoint] Migration failed after ${attempts} attempts."
      exit 1
    fi
    echo "[entrypoint] Migration attempt ${attempts} failed. Retrying in 2s..."
    sleep 2
  done
  echo "[entrypoint] Migrations complete."
fi

exec uvicorn reskin_ai.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*"
