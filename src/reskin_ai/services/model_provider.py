from __future__ import annotations

import base64
import io
import json
import logging
import re
import time
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


class ModelRateLimitError(ModelGenerationError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        retries_used: int,
        provider_failures: int,
        retry_after_seconds: int | None,
    ) -> None:
        super().__init__(
            message,
            provider=provider,
            retries_used=retries_used,
            provider_failures=provider_failures,
        )
        self.retry_after_seconds = retry_after_seconds


class ModelAuthError(ModelGenerationError):
    pass


class ModelSafetyBlockedError(ModelGenerationError):
    pass


class ProviderRateLimitError(RuntimeError):
    def __init__(self, message: str, *, retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ProviderAuthError(RuntimeError):
    pass


class ProviderSafetyBlockedError(RuntimeError):
    pass


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

    @staticmethod
    def _extract_openai_error_message(details: str) -> str | None:
        try:
            parsed = json.loads(details)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        err = parsed.get("error")
        if not isinstance(err, dict):
            return None
        msg = err.get("message")
        if isinstance(msg, str) and msg.strip():
            return msg.strip()
        return None

    @staticmethod
    def _extract_retry_after_seconds(message: str) -> int | None:
        match = re.search(r"try again in (\\d+)s", message, flags=re.IGNORECASE)
        if not match:
            return None
        try:
            value = int(match.group(1))
        except ValueError:
            return None
        return value if value > 0 else None

    @staticmethod
    def _suggest_model_from_message(message: str) -> str | None:
        # Example: "Invalid value: 'gpt-image-1'. Value must be 'dall-e-2'."
        needle = "Value must be '"
        start = message.find(needle)
        if start == -1:
            return None
        start += len(needle)
        end = message.find("'", start)
        if end == -1:
            return None
        candidate = message[start:end].strip()
        return candidate or None

    def _generate_without_image(self, *, prompt: str, variant_count: int) -> list[GeneratedAsset]:
        def _do_request(model_name: str) -> str:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "size": self.image_size,
                "n": variant_count,
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
                return resp.read().decode("utf-8")

        try:
            body = _do_request(self.image_model)
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            if exc.code in {401, 403}:
                raise ProviderAuthError("OpenAI authentication failed.") from exc
            if exc.code == 429:
                message = self._extract_openai_error_message(details) or "OpenAI rate limit exceeded."
                raise ProviderRateLimitError(
                    message,
                    retry_after_seconds=self._extract_retry_after_seconds(message),
                ) from exc
            message = self._extract_openai_error_message(details) or ""
            suggested = self._suggest_model_from_message(message) if message else None
            if suggested and suggested.lower() != self.image_model.lower():
                logger.warning(
                    "OpenAI image model rejected; retrying with suggested model. requested=%s suggested=%s",
                    self.image_model,
                    suggested,
                )
                body = _do_request(suggested)
            else:
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

    def _parse_target_size(self) -> int:
        # Expect strings like "1024x1024". DALL-E 2 edits are square.
        raw = (self.image_size or "").lower().strip()
        match = re.match(r"^(\\d+)x(\\d+)$", raw)
        if not match:
            return 1024
        try:
            w = int(match.group(1))
            h = int(match.group(2))
        except ValueError:
            return 1024
        return w if w == h and w in {256, 512, 1024} else 1024

    @staticmethod
    def _fit_square_canvas(*, img, edge: int, resample, fill_rgba: tuple[int, int, int, int]):
        from PIL import Image  # type: ignore

        w, h = img.size
        if w <= 0 or h <= 0:
            canvas = Image.new("RGBA", (edge, edge), fill_rgba)
            return canvas
        scale = min(edge / w, edge / h)
        new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
        if new_size != img.size:
            img = img.resize(new_size, resample=resample)
        canvas = Image.new("RGBA", (edge, edge), fill_rgba)
        px = (edge - img.size[0]) // 2
        py = (edge - img.size[1]) // 2
        canvas.paste(img, (px, py))
        return canvas

    def _prepare_edit_image_and_mask(
        self,
        *,
        base_image: bytes,
        base_content_type: str | None,
        scar_mask_png: bytes,
    ) -> tuple[bytes, bytes]:
        """
        DALL-E 2 edits expect:
        - image + mask as PNG
        - image + mask with same dimensions
        - mask alpha: transparent pixels indicate the area to replace
        """

        from PIL import Image, ImageFilter, ImageOps  # type: ignore

        edge = self._parse_target_size()
        base = Image.open(io.BytesIO(base_image)).convert("RGBA")
        # Use a calm fill color based on a center pixel to avoid harsh borders.
        cx = max(0, min(base.size[0] - 1, base.size[0] // 2))
        cy = max(0, min(base.size[1] - 1, base.size[1] // 2))
        r, g, b, _a = base.getpixel((cx, cy))
        fill = (int(r), int(g), int(b), 255)
        base_sq = self._fit_square_canvas(
            img=base,
            edge=edge,
            resample=Image.Resampling.LANCZOS,
            fill_rgba=fill,
        )
        out_img = io.BytesIO()
        base_sq.save(out_img, format="PNG", optimize=True)

        mask_src = Image.open(io.BytesIO(scar_mask_png)).convert("RGBA")
        # The canvas mask uses alpha in the painted region. Convert to a binary region mask.
        region = mask_src.getchannel("A").point(lambda p: 255 if p > 16 else 0)
        region = region.filter(ImageFilter.GaussianBlur(radius=1.2))
        # OpenAI edits: transparent pixels indicate the area to replace.
        alpha = ImageOps.invert(region).convert("L")
        mask_rgba = Image.new("RGBA", mask_src.size, (0, 0, 0, 255))
        mask_rgba.putalpha(alpha)
        mask_sq = self._fit_square_canvas(
            img=mask_rgba,
            edge=edge,
            resample=Image.Resampling.NEAREST,
            fill_rgba=(0, 0, 0, 255),
        )
        out_mask = io.BytesIO()
        mask_sq.save(out_mask, format="PNG", optimize=True)
        return out_img.getvalue(), out_mask.getvalue()

    def edit_with_mask(
        self,
        *,
        prompt_text: str,
        variant_count: int,
        base_image: bytes,
        base_content_type: str | None,
        scar_mask_png: bytes,
        edit_model: str,
    ) -> list[GeneratedAsset]:
        # Photo-realistic preview: preserve skin texture outside the masked area.
        prompt = (
            "Apply a tasteful tattoo design ONLY inside the masked region. "
            "Keep the rest of the photo unchanged: preserve skin texture, lighting, color, and anatomy. "
            "Tattoo style should be calm, premium, and respectful; no text, no logos, no watermarks. "
            f"Design preferences: {prompt_text}"
        )

        try:
            prepared_image, prepared_mask = self._prepare_edit_image_and_mask(
                base_image=base_image,
                base_content_type=base_content_type,
                scar_mask_png=scar_mask_png,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Unable to prepare image/mask for edits: {exc}") from exc

        body, content_type = self._encode_multipart(
            fields={
                "model": edit_model,
                "prompt": prompt,
                "size": self.image_size,
                "n": str(variant_count),
            },
            files=[
                ("image", "photo.png", "image/png", prepared_image),
                ("mask", "mask.png", "image/png", prepared_mask),
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

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body_text = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            if exc.code in {401, 403}:
                raise ProviderAuthError("OpenAI authentication failed.") from exc
            if exc.code == 429:
                message = self._extract_openai_error_message(details) or "OpenAI rate limit exceeded."
                raise ProviderRateLimitError(
                    message,
                    retry_after_seconds=self._extract_retry_after_seconds(message),
                ) from exc
            if exc.code == 400 and self._extract_openai_error_code(details) == "moderation_blocked":
                raise ProviderSafetyBlockedError("OpenAI safety system blocked the photo preview.") from exc
            raise RuntimeError(f"OpenAI image edit failed: HTTP {exc.code} {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI image edit network failure: {exc.reason}") from exc

        parsed = json.loads(body_text)
        outputs = parsed.get("data", [])
        if not isinstance(outputs, list) or not outputs:
            raise RuntimeError("OpenAI image edit returned empty data payload.")

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
                f"OpenAI image edit returned {len(assets)} images; expected {variant_count}.",
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
        # Important: our default production pipeline generates a "design asset" (not a photo edit)
        # and then renders an ink preview over the user's image locally. To avoid "mosaic" overlays,
        # we ask the model for clean linework on a plain background.
        prompt = (
            "Design a tattoo concept as a clean stencil asset. "
            "Style: elegant, calm, dignity-centered. "
            "Output requirements: plain white background, black ink linework only, no shading, no gradients, "
            "no skin texture, no photo background, no text, no watermark, no borders. "
            "Center the design with comfortable margins. "
            "Safety: no violence, no gore, no explicit content. "
            f"Personalization input: {prompt_text}"
        )

        # OpenAI's classic edits endpoint only supports specific models (commonly `dall-e-2`).
        # For other models (e.g. `gpt-image-1`) we fall back to text-only generation to keep the
        # product usable and to avoid uploading sensitive images unnecessarily.
        if input_image and self.image_model.lower() != "dall-e-2":
            logger.info(
                "OpenAI image model does not support edits; generating without user image. model=%s",
                self.image_model,
            )
            return self._generate_without_image(prompt=prompt, variant_count=variant_count)

        if input_image:
            extension = self._guess_extension(input_content_type)
            body, content_type = self._encode_multipart(
                fields={
                    "model": self.image_model,
                    "prompt": prompt,
                    "size": self.image_size,
                    "n": str(variant_count),
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
            if exc.code == 429:
                message = self._extract_openai_error_message(details) or "OpenAI rate limit exceeded."
                raise ProviderRateLimitError(
                    message,
                    retry_after_seconds=self._extract_retry_after_seconds(message),
                ) from exc
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
            except ProviderAuthError as exc:
                raise ModelAuthError(
                    str(exc),
                    provider=self.primary.provider_name,
                    retries_used=retries_used,
                    provider_failures=failures + 1,
                ) from exc
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                failures += 1
                # Keep this log intentionally concise: it is used to debug production provider failures
                # without leaking sensitive request content.
                message = str(exc).replace("\n", " ").strip()
                if len(message) > 700:
                    message = message[:700] + "..."
                if isinstance(exc, ProviderRateLimitError):
                    # Optional: respect retry-after hints for small waits to reduce user-visible failures.
                    wait_seconds = exc.retry_after_seconds
                    if attempt < max_attempts - 1 and wait_seconds and wait_seconds <= 12:
                        logger.warning(
                            "Primary model rate-limited; waiting %ss then retrying (%s/%s).",
                            wait_seconds,
                            attempt + 1,
                            max_attempts,
                        )
                        time.sleep(wait_seconds)
                if attempt < max_attempts - 1:
                    retries_used += 1
                    logger.warning(
                        "Primary model generation failed; retrying (%s/%s). error=%s:%s",
                        retries_used,
                        self.retry_attempts,
                        type(exc).__name__,
                        message,
                    )

        if isinstance(last_error, ProviderRateLimitError):
            raise ModelRateLimitError(
                str(last_error),
                provider=self.primary.provider_name,
                retries_used=retries_used,
                provider_failures=failures,
                retry_after_seconds=last_error.retry_after_seconds,
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

    def inpaint_preview(
        self,
        *,
        prompt_text: str,
        variant_count: int,
        base_image: bytes,
        base_content_type: str | None,
        scar_mask_png: bytes,
        edit_model: str,
    ) -> GenerationBatch:
        if self.primary is None or not hasattr(self.primary, "edit_with_mask"):
            raise ModelGenerationError(
                "Primary model provider does not support inpaint previews.",
                provider=self.fallback.provider_name if self.primary is None else self.primary.provider_name,
                retries_used=0,
                provider_failures=0,
            )

        failures = 0
        retries_used = 0
        max_attempts = self.retry_attempts + 1
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            try:
                # mypy: dynamic capability check via hasattr above.
                assets = self.primary.edit_with_mask(  # type: ignore[attr-defined]
                    prompt_text=prompt_text,
                    variant_count=variant_count,
                    base_image=base_image,
                    base_content_type=base_content_type,
                    scar_mask_png=scar_mask_png,
                    edit_model=edit_model,
                )
                return GenerationBatch(
                    assets=assets,
                    provider=self.primary.provider_name,
                    model_version=f"{self.primary.model_version}+edits",
                    retries_used=retries_used,
                    provider_failures=failures,
                    used_fallback=False,
                )
            except ProviderAuthError as exc:
                raise ModelAuthError(
                    str(exc),
                    provider=self.primary.provider_name,
                    retries_used=retries_used,
                    provider_failures=failures + 1,
                ) from exc
            except ProviderSafetyBlockedError as exc:
                raise ModelSafetyBlockedError(
                    str(exc),
                    provider=self.primary.provider_name,
                    retries_used=retries_used,
                    provider_failures=failures + 1,
                ) from exc
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                failures += 1
                message = str(exc).replace("\n", " ").strip()
                if len(message) > 700:
                    message = message[:700] + "..."
                if isinstance(exc, ProviderRateLimitError):
                    wait_seconds = exc.retry_after_seconds
                    if attempt < max_attempts - 1 and wait_seconds and wait_seconds <= 12:
                        logger.warning(
                            "Primary inpaint rate-limited; waiting %ss then retrying (%s/%s).",
                            wait_seconds,
                            attempt + 1,
                            max_attempts,
                        )
                        time.sleep(wait_seconds)
                if attempt < max_attempts - 1:
                    retries_used += 1
                    logger.warning(
                        "Primary inpaint failed; retrying (%s/%s). error=%s:%s",
                        retries_used,
                        self.retry_attempts,
                        type(exc).__name__,
                        message,
                    )

        if isinstance(last_error, ProviderRateLimitError):
            raise ModelRateLimitError(
                str(last_error),
                provider=self.primary.provider_name,
                retries_used=retries_used,
                provider_failures=failures,
                retry_after_seconds=last_error.retry_after_seconds,
            )

        message = str(last_error) if last_error else "Unknown inpaint provider error."
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
