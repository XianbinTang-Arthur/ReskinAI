from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from reskin_ai.api.router import get_api_router
from reskin_ai.core.config import settings
from reskin_ai.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    register_exception_handlers(app)
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    settings.web_root.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(settings.storage_root)), name="media")
    app.mount("/ui", StaticFiles(directory=str(settings.web_root), html=True), name="ui")
    app.include_router(get_api_router())

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse(url="/ui/")

    @app.get("/healthz")
    def healthcheck() -> dict[str, str | bool]:
        return {
            "status": "ok",
            "env": settings.app_env,
            "model_provider": settings.model_provider,
            "model_version": settings.model_version,
            "fallback_enabled": settings.model_fallback_enabled,
        }

    return app


app = create_app()
