from __future__ import annotations

import base64
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request

from reskin_ai.core.config import Settings, settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedAsset:
    content: bytes
    extension: str


@dataclass(frozen=True)
class GenerationBatch:
    assets: list[GeneratedAsset]
    provider: str
    model_version: str
    retries_used: int
    provider_failures: int
    used_fallback: bool


class ModelGenerationError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        retries_used: int,
        provider_failures: int,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.retries_used = retries_used
        self.provider_failures = provider_failures


class BaseModelProvider(Protocol):
    provider_name: str
    model_version: str

    def generate(
        self,
        *,
        prompt_text: str,
        variant_count: int,
        input_image: bytes | None = None,
        input_content_type: str | None = None,
    ) -> list[GeneratedAsset]:
        ...


class LocalSvgProvider:
    provider_name = "local"
    model_version = "local-svg-v1"

    @staticmethod
    def _build_svg(prompt_text: str, variant_index: int) -> bytes:
        safe_text = prompt_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
<defs>
<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#f7efe0"/>
<stop offset="100%" stop-color="#d8ecea"/>
</linearGradient>
</defs>
<rect width="100%" height="100%" fill="url(#bg)"/>
<circle cx="512" cy="512" r="{310 + (variant_index * 12)}" fill="none" stroke="#0b7a78" stroke-width="7"/>
<circle cx="512" cy="512" r="{245 + (variant_index * 10)}" fill="none" stroke="#e86d2a" stroke-width="4"/>
<text x="50%" y="16%" text-anchor="middle" font-size="42" fill="#1a3f46">ReSkin Concept {variant_index}</text>
<text x="50%" y="24%" text-anchor="middle" font-size="20" fill="#355a62">Prototype Preview</text>
<text x="50%" y="88%" text-anchor="middle" font-size="18" fill="#3f5054">{safe_text[:120]}</text>
</svg>"""
        return body.encode("utf-8")

    def generate(
        self,
        *,
        prompt_text: str,
        variant_count: int,
        input_image: bytes | None = None,
        input_content_type: str | None = None,
    ) -> list[GeneratedAsset]:
        return [
            GeneratedAsset(content=self._build_svg(prompt_text, variant_index=index), extension=".svg")
            for index in range(1, variant_count + 1)
        ]


class OpenAIImageProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        image_model: str,
        image_size: str,
        timeout_seconds: int,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.image_model = image_model
        self.image_size = image_size
        self.timeout_seconds = timeout_seconds
        self.model_version = image_model

    @staticmethod
    def _guess_extension(content_type: str | None) -> str:
        normalized = (content_type or "").lower().strip()
        if normalized == "image/jpeg":
            return ".jpg"
        if normalized == "image/png":
            return ".png"
        if normalized == "image/webp":
            return ".webp"
        return ".png"

    @staticmethod
    def _encode_multipart(
        *,
        fields: dict[str, str],
        files: list[tuple[str, str, str, bytes]],
    ) -> tuple[bytes, str]:
        boundary = f"----reskinai-{uuid.uuid4().hex}"
        body = bytearray()
        boundary_bytes = boundary.encode("ascii")

        for name, value in fields.items():
            body.extend(b"--" + boundary_bytes + b"\r\n")
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            body.extend(value.encode("utf-8"))
            body.extend(b"\r\n")

        for field_name, filename, content_type, content in files:
            body.extend(b"--" + boundary_bytes + b"\r\n")
            body.extend(
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{filename}"\r\n'
                ).encode()
            )
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
            body.extend(content)
            body.extend(b"\r\n")

        body.extend(b"--" + boundary_bytes + b"--\r\n")
        return bytes(body), f"multipart/form-data; boundary={boundary}"

    def _download_image_bytes(self, image_url: str) -> bytes:
        req = request.Request(image_url, method="GET")
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            return resp.read()

    @staticmethod
    def _extract_openai_error_code(details: str) -> str | None:
        try:
            parsed = json.loads(details)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        err = parsed.get("error")
        if not isinstance(err, dict):
            return None
        code = err.get("code")
        if isinstance(code, str) and code.strip():
            return code.strip()
        return None

    def _generate_without_image(self, *, prompt: str, variant_count: int) -> list[GeneratedAsset]:
        payload = {
            "model": self.image_model,
            "prompt": prompt,
            "size": self.image_size,
            "n": variant_count,
            # Prefer base64 to avoid handling expiring URLs.
            "response_format": "b64_json",
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url}/images/generations",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            body = resp.read().decode("utf-8")
        parsed = json.loads(body)
        outputs = parsed.get("data", [])
        if not isinstance(outputs, list) or not outputs:
            raise RuntimeError("OpenAI image generation returned empty data payload.")

        assets: list[GeneratedAsset] = []
        for item in outputs:
            if not isinstance(item, dict):
                continue
            b64_image = item.get("b64_json")
            if isinstance(b64_image, str) and b64_image:
                assets.append(GeneratedAsset(content=base64.b64decode(b64_image), extension=".png"))
                continue
            image_url = item.get("url")
            if isinstance(image_url, str) and image_url:
                assets.append(GeneratedAsset(content=self._download_image_bytes(image_url), extension=".png"))

        if len(assets) < variant_count:
            raise RuntimeError(
                f"OpenAI image generation returned {len(assets)} images; expected {variant_count}.",
            )
        return assets[:variant_count]

    def generate(
        self,
        *,
        prompt_text: str,
        variant_count: int,
        input_image: bytes | None = None,
        input_content_type: str | None = None,
    ) -> list[GeneratedAsset]:
        prompt = (
            "Skin-aware tattoo concept designed with dignity and calm. Keep it elegant and safe. "
            "No violent symbols, no text overlays. "
            f"Personalization input: {prompt_text}"
        )

        if input_image:
            extension = self._guess_extension(input_content_type)
            body, content_type = self._encode_multipart(
                fields={
                    "model": self.image_model,
                    "prompt": prompt,
                    "size": self.image_size,
                    "n": str(variant_count),
                    "input_fidelity": "high",
                    "response_format": "b64_json",
                },
                files=[
                    (
                        "image",
                        f"upload{extension}",
                        input_content_type or "image/png",
                        input_image,
                    )
                ],
            )
            req = request.Request(
                url=f"{self.base_url}/images/edits",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": content_type,
                },
            )
        else:
            return self._generate_without_image(prompt=prompt, variant_count=variant_count)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            if input_image and exc.code == 400 and self._extract_openai_error_code(details) == "moderation_blocked":
                # The uploaded photo may be flagged by the image safety system. For emotional-safety and privacy,
                # automatically retry without sending the user's image.
                logger.warning("OpenAI edits blocked by safety; retrying without user image.")
                return self._generate_without_image(prompt=prompt, variant_count=variant_count)
            raise RuntimeError(f"OpenAI image generation failed: HTTP {exc.code} {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI image generation network failure: {exc.reason}") from exc

        parsed = json.loads(body)
        outputs = parsed.get("data", [])
        if not isinstance(outputs, list) or not outputs:
            raise RuntimeError("OpenAI image generation returned empty data payload.")

        assets: list[GeneratedAsset] = []
        for item in outputs:
            if not isinstance(item, dict):
                continue
            b64_image = item.get("b64_json")
            if isinstance(b64_image, str) and b64_image:
                assets.append(GeneratedAsset(content=base64.b64decode(b64_image), extension=".png"))
                continue
            image_url = item.get("url")
            if isinstance(image_url, str) and image_url:
                assets.append(GeneratedAsset(content=self._download_image_bytes(image_url), extension=".png"))

        if len(assets) < variant_count:
            raise RuntimeError(
                f"OpenAI image generation returned {len(assets)} images; expected {variant_count}.",
            )
        return assets[:variant_count]


class ResilientModelProvider:
    def __init__(
        self,
        *,
        primary: BaseModelProvider | None,
        fallback: BaseModelProvider,
        retry_attempts: int,
        fallback_enabled: bool,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.retry_attempts = max(0, retry_attempts)
        self.fallback_enabled = fallback_enabled

    def generate(
        self,
        *,
        prompt_text: str,
        variant_count: int,
        input_image: bytes | None = None,
        input_content_type: str | None = None,
    ) -> GenerationBatch:
        if self.primary is None:
            assets = self.fallback.generate(
                prompt_text=prompt_text,
                variant_count=variant_count,
                input_image=input_image,
                input_content_type=input_content_type,
            )
            return GenerationBatch(
                assets=assets,
                provider=self.fallback.provider_name,
                model_version=self.fallback.model_version,
                retries_used=0,
                provider_failures=0,
                used_fallback=False,
            )

        failures = 0
        retries_used = 0
        max_attempts = self.retry_attempts + 1
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            try:
                assets = self.primary.generate(
                    prompt_text=prompt_text,
                    variant_count=variant_count,
                    input_image=input_image,
                    input_content_type=input_content_type,
                )
                return GenerationBatch(
                    assets=assets,
                    provider=self.primary.provider_name,
                    model_version=self.primary.model_version,
                    retries_used=retries_used,
                    provider_failures=failures,
                    used_fallback=False,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                failures += 1
                # Keep this log intentionally concise: it is used to debug production provider failures
                # without leaking sensitive request content.
                message = str(exc).replace("\n", " ").strip()
                if len(message) > 700:
                    message = message[:700] + "..."
                if attempt < max_attempts - 1:
                    retries_used += 1
                    logger.warning(
                        "Primary model generation failed; retrying (%s/%s). error=%s:%s",
                        retries_used,
                        self.retry_attempts,
                        type(exc).__name__,
                        message,
                    )

        if self.fallback_enabled:
            if last_error is not None:
                message = str(last_error).replace("\n", " ").strip()
                if len(message) > 700:
                    message = message[:700] + "..."
                logger.warning(
                    "Falling back to local model provider after primary failure. error=%s:%s",
                    type(last_error).__name__,
                    message,
                )
            else:
                logger.warning("Falling back to local model provider after primary failure.")
            assets = self.fallback.generate(
                prompt_text=prompt_text,
                variant_count=variant_count,
                input_image=input_image,
                input_content_type=input_content_type,
            )
            return GenerationBatch(
                assets=assets,
                provider=self.fallback.provider_name,
                model_version=f"{self.fallback.model_version}+fallback",
                retries_used=retries_used,
                provider_failures=failures,
                used_fallback=True,
            )

        message = str(last_error) if last_error else "Unknown model provider error."
        raise ModelGenerationError(
            message,
            provider=self.primary.provider_name,
            retries_used=retries_used,
            provider_failures=failures,
        )


def build_model_provider(config: Settings = settings) -> ResilientModelProvider:
    fallback = LocalSvgProvider()
    primary: BaseModelProvider | None = None
    requested = config.model_provider.lower()
    if requested in {"openai", "auto"} and config.openai_api_key:
        primary = OpenAIImageProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            image_model=config.openai_image_model,
            image_size=config.openai_image_size,
            timeout_seconds=config.model_request_timeout_seconds,
        )
    elif requested == "openai" and not config.openai_api_key:
        logger.warning("MODEL_PROVIDER=openai is set but OPENAI_API_KEY is missing. Local fallback will be used.")

    return ResilientModelProvider(
        primary=primary,
        fallback=fallback,
        retry_attempts=config.model_retry_attempts,
        fallback_enabled=config.model_fallback_enabled,
    )
