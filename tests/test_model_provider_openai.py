from __future__ import annotations

import base64
import json

from reskin_ai.services.model_provider import OpenAIImageProvider


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def read(self) -> bytes:
        return self._body


def test_openai_generations_payload_omits_response_format(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(req, timeout):  # noqa: ANN001
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        captured["body"] = req.data
        payload = {
            "data": [
                {
                    "b64_json": base64.b64encode(b"generated-image").decode("ascii"),
                }
            ]
        }
        return _FakeResponse(json.dumps(payload))

    monkeypatch.setattr("reskin_ai.services.model_provider.request.urlopen", fake_urlopen)
    provider = OpenAIImageProvider(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        image_model="gpt-image-1",
        image_size="1024x1024",
        timeout_seconds=5,
    )
    assets = provider.generate(prompt_text="floral", variant_count=1)

    request_body = captured["body"]
    assert isinstance(request_body, (bytes, bytearray))
    payload = json.loads(bytes(request_body).decode("utf-8"))
    assert "response_format" not in payload
    assert captured["url"] == "https://api.openai.com/v1/images/generations"
    assert len(assets) == 1
    assert assets[0].content == b"generated-image"


def test_openai_edits_payload_includes_uploaded_image(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(req, timeout):  # noqa: ANN001
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        captured["body"] = req.data
        payload = {
            "data": [
                {
                    "b64_json": base64.b64encode(b"edited-image").decode("ascii"),
                }
            ]
        }
        return _FakeResponse(json.dumps(payload))

    monkeypatch.setattr("reskin_ai.services.model_provider.request.urlopen", fake_urlopen)
    provider = OpenAIImageProvider(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        image_model="gpt-image-1",
        image_size="1024x1024",
        timeout_seconds=5,
    )
    assets = provider.generate(
        prompt_text="line-art",
        variant_count=1,
        input_image=b"input-image-binary",
        input_content_type="image/png",
    )

    assert captured["url"] == "https://api.openai.com/v1/images/edits"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    content_type = str(headers.get("content-type", ""))
    assert content_type.startswith("multipart/form-data; boundary=")
    body = captured["body"]
    assert isinstance(body, (bytes, bytearray))
    body_bytes = bytes(body)
    assert b'name="image"; filename="upload.png"' in body_bytes
    assert b"Content-Type: image/png" in body_bytes
    assert b"input-image-binary" in body_bytes
    assert b'name="input_fidelity"' in body_bytes
    assert b"high" in body_bytes
    assert len(assets) == 1
    assert assets[0].content == b"edited-image"
