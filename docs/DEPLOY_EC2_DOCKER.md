# ReSkin AI EC2 Deployment (Docker Compose)

This document targets Amazon Linux 2023 EC2 instances and deploys:
- `reskinai-api` (FastAPI app)
- `reskinai-postgres` (PostgreSQL 16)
- `nginx` reverse proxy on `80/443`

## 1) Security prerequisites

- Ensure Security Group allows:
  - TCP `22` from your IP (SSH)
  - TCP `80` from users
  - TCP `443` from users (after HTTPS is enabled)
- Do **not** commit `.env.prod` into git.
- Rotate any API key that has been exposed in chat/logs.

## 2) Bootstrap EC2 host

Run on EC2:

```bash
bash deploy/ec2/bootstrap_amzn2023.sh
```

Then re-login to apply docker group membership.

## 3) Prepare production env

Create `/home/ec2-user/ReskinAI/.env.prod`:

```bash
cp .env.prod.example .env.prod
vi .env.prod
```

Required values:
- `POSTGRES_PASSWORD`
- `OPENAI_API_KEY` (if using OpenAI generation)

Recommended:
- `APP_BIND_IP=127.0.0.1` (keep app private behind nginx)

## 4) Deploy

```bash
bash deploy/ec2/deploy_compose.sh
```

## 5) Verify

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
curl http://127.0.0.1:8000/healthz
```

Open:
- `http://<EC2_PUBLIC_IP>/ui/`

## 6) Configure nginx reverse proxy (HTTP)

```bash
bash deploy/ec2/setup_nginx_proxy.sh
```

Optional custom host name:

```bash
SERVER_NAME=app.example.com bash deploy/ec2/setup_nginx_proxy.sh
```

If port `80` is already occupied by another service, stop/move that service first.

## 7) Enable HTTPS with Let's Encrypt (when domain is ready)

```bash
bash deploy/ec2/enable_https_letsencrypt.sh app.example.com you@example.com
```

Before running the command:
- DNS `A` record must point to your EC2 public IP.
- Security Group must allow port `443`.

## 8) Common operations

Restart:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml restart
```

Logs:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f app
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f db
```

Stop:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml down
```
