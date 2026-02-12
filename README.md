# ReSkin AI

Usable backend prototype for ReSkin AI (FastAPI + SQLAlchemy + local media storage).

## Local setup

```bash
python -m pip install -e .[dev]
uvicorn reskin_ai.main:app --reload
```

## Database

Default local database: `sqlite+pysqlite:///storage/reskin.db`  
Override with env var:

```bash
set DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME
```

Run migrations:

```bash
alembic upgrade head
```

API docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/healthz`
- Pilot UI Console: `http://127.0.0.1:8000/ui/`
  - Client flow: `http://127.0.0.1:8000/ui/client.html`
  - Artist workspace: `http://127.0.0.1:8000/ui/artist.html`
  - Operations: `http://127.0.0.1:8000/ui/admin.html`

## Model provider

The generation pipeline supports a resilient model provider strategy:
- Primary: OpenAI image generation (`MODEL_PROVIDER=openai` or `auto` with API key)
- Fallback: local SVG provider (enabled by default)

Example (PowerShell):

```bash
set MODEL_PROVIDER=openai
set OPENAI_API_KEY=your_key_here
set OPENAI_IMAGE_MODEL=gpt-image-1
set MODEL_RETRY_ATTEMPTS=1
set MODEL_FALLBACK_ENABLED=true
```

If OpenAI fails, the API records retry/failure metrics and can fall back to local rendering for service continuity.

## Quick start flow

1. Create a `user` session at `POST /api/v1/auth/session`.
2. Create consent at `POST /api/v1/consents`.
3. Upload scar image via multipart at `POST /api/v1/uploads/file`.
4. Create preferences at `POST /api/v1/preferences`.
5. Generate concepts at `POST /api/v1/generations`.
6. Open returned concept `storage_uri` under `/media/...`.
7. Invite artist via `POST /api/v1/collaborations/invite`.
8. Artist adds notes via `POST /api/v1/collaborations/{id}/notes`.

Or open `http://127.0.0.1:8000/ui/` and click **Run Onboarding Sandbox** for a one-click internal QA walkthrough.

## Test and lint

```bash
ruff check src tests
pytest
```

## Docker Compose (production style)

```bash
cp .env.prod.example .env.prod
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
bash deploy/ec2/setup_nginx_proxy.sh
```

See deployment guide: `docs/DEPLOY_EC2_DOCKER.md`.
