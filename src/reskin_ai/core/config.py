from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "ReSkin AI API"
    app_version: str = "0.1.0"
    app_env: str = os.getenv("APP_ENV", "dev").lower()
    model_version: str = os.getenv("MODEL_VERSION", "managed-image-v1")
    prompt_version: str = os.getenv("PROMPT_VERSION", "prompt-v1")
    safety_policy_version: str = os.getenv("SAFETY_POLICY_VERSION", "safety-v1")
    max_generation_variants: int = int(os.getenv("MAX_GENERATION_VARIANTS", "5"))
    max_upload_size_bytes: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "5242880"))
    storage_root: Path = field(
        default_factory=lambda: Path(os.getenv("STORAGE_ROOT", "storage")).resolve(),
    )
    state_file: Path = field(
        default_factory=lambda: Path(os.getenv("STATE_FILE", "storage/state.json")).resolve(),
    )
    web_root: Path = field(
        default_factory=lambda: Path(os.getenv("WEB_ROOT", "frontend")).resolve(),
    )
    database_url: str = os.getenv("DATABASE_URL", "")
    model_provider: str = os.getenv("MODEL_PROVIDER", "auto").lower()
    model_fallback_enabled: bool = _bool_env("MODEL_FALLBACK_ENABLED", True)
    model_retry_attempts: int = int(os.getenv("MODEL_RETRY_ATTEMPTS", "1"))
    # Image generation / edits can take longer than a typical HTTP request.
    # Keep this below the nginx proxy_read_timeout (default 120s in our template).
    model_request_timeout_seconds: int = int(os.getenv("MODEL_REQUEST_TIMEOUT_SECONDS", "110"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    openai_image_model: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    openai_edit_model: str = os.getenv("OPENAI_EDIT_MODEL", "dall-e-2")
    openai_image_size: str = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")

    @property
    def allowed_upload_types(self) -> set[str]:
        return {"image/jpeg", "image/png", "image/webp"}

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        sqlite_path = (self.storage_root / "reskin.db").resolve()
        return f"sqlite+pysqlite:///{sqlite_path}"


settings = Settings()
