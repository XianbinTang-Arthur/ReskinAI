# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and follows Semantic Versioning.

## [Unreleased]

### Changed
- Upgraded SCMP to v1.1 at `docs/scmp/SCMP.md` with:
  - safety-critical identity framing
  - environment model and isolation strategy (`dev` / `staging` / `prod`)
  - operational incident management with SEV0-SEV3 classification
  - reliability targets (SLO) and error budget policy
  - model registry requirements for AI behavior changes
  - ADR policy and architecture decision memory workflow
- Generation pipeline upgraded to resilient provider strategy:
  - OpenAI image provider support with retry + local fallback
  - generation telemetry counters for success/failure/retry/fallback and latency
  - provider diagnostics surfaced in admin metrics
  - health endpoint includes provider mode and fallback flag
- Frontend upgraded from debug console to commercial product console:
  - hero narrative + live status board
  - one-click "Run Onboarding Sandbox" flow with synthetic test image generation
  - preserved manual User/Artist/Admin workbench for detailed operations
  - split UI into multi-page workspaces to reduce on-screen cognitive load:
    - `frontend/index.html`
    - `frontend/client.html`
    - `frontend/artist.html`
    - `frontend/admin.html`

### Added
- Initial proposal document at `docs/proposal/RESKINAI_PROPOSAL_V1.md`.
- SCMP package:
  - `docs/scmp/SCMP.md`
  - `docs/scmp/templates/CHANGE_REQUEST_TEMPLATE.md`
  - `docs/scmp/templates/RELEASE_CHECKLIST.md`
  - `docs/scmp/templates/BASELINE_RECORD_TEMPLATE.md`
- Additional SCMP governance assets:
  - `docs/scmp/templates/INCIDENT_REPORT_TEMPLATE.md`
  - `docs/scmp/templates/MODEL_REGISTRY_ENTRY_TEMPLATE.md`
  - `docs/scmp/templates/ADR_TEMPLATE.md`
  - `docs/scmp/adr/README.md`
  - `docs/scmp/adr/ADR-0001-model-hosting-strategy.md`
  - `docs/scmp/adr/ADR-0002-image-storage-encryption.md`
- SPMP package:
  - `docs/spmp/SPMP.md`
  - `docs/spmp/templates/PROJECT_STATUS_REPORT_TEMPLATE.md`
  - `docs/spmp/templates/RISK_REGISTER_TEMPLATE.md`
- SRS package:
  - `docs/srs/SRS.md`
  - `docs/srs/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- SDD package:
  - `docs/sdd/SDD.md`
  - `docs/sdd/COMPONENT_TRACEABILITY_MATRIX.md`
- Initial Python backend implementation scaffold:
  - `pyproject.toml`
  - `src/reskin_ai/main.py`
  - `src/reskin_ai/api/router.py`
  - `src/reskin_ai/api/routes/*`
  - `src/reskin_ai/core/config.py`
  - `src/reskin_ai/core/errors.py`
  - `src/reskin_ai/dependencies.py`
  - `src/reskin_ai/repository.py`
  - `src/reskin_ai/schemas.py`
  - `src/reskin_ai/services/generation.py`
  - `src/reskin_ai/services/safety.py`
  - `tests/conftest.py`
  - `tests/test_generation_flow.py`
  - `tests/test_admin_and_deletion.py`
  - `README.md`
- Usable MVP backend upgrades:
  - local persistent state file support in `src/reskin_ai/repository.py`
  - local media storage service in `src/reskin_ai/services/storage.py`
  - static media serving at `/media` in `src/reskin_ai/main.py`
  - multipart upload endpoint `POST /api/v1/uploads/file`
  - generated concept SVG assets with directly accessible `storage_uri`
  - collaboration workflow endpoints under `/api/v1/collaborations/*`
  - new schemas for collaboration request/response payloads
  - end-to-end tests for file upload and collaboration lifecycle:
    - `tests/test_file_upload_and_collaboration.py`
  - repository hygiene ignore rules in `.gitignore`
- Database upgrade (SQLAlchemy + Alembic):
  - SQLAlchemy runtime integration and model schema:
    - `src/reskin_ai/db/models.py`
    - `src/reskin_ai/db/session.py`
    - `src/reskin_ai/repository.py`
  - Configurable `DATABASE_URL` with SQLite default fallback:
    - `src/reskin_ai/core/config.py`
  - Alembic migration scaffold and initial schema migration:
    - `alembic.ini`
    - `alembic/env.py`
    - `alembic/script.py.mako`
    - `alembic/versions/0001_initial.py`
  - Postgres optional dependency group:
    - `pyproject.toml` (`postgres` extra with `psycopg[binary]`)
- Pilot frontend console (static SPA on `/ui/`):
  - static UI mount and root redirect:
    - `src/reskin_ai/main.py`
  - frontend assets:
    - `frontend/index.html`
    - `frontend/styles.css`
    - `frontend/app.js`
  - static UI smoke tests:
    - `tests/test_ui_static.py`
- Real model integration and monitoring components:
  - `src/reskin_ai/services/model_provider.py`
