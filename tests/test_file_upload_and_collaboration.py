from __future__ import annotations

from conftest import auth_headers, create_session
from fastapi.testclient import TestClient

from reskin_ai import dependencies
from reskin_ai.services.model_provider import GeneratedAsset, GenerationBatch


def _create_generation_for_user(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    consent_id = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=headers,
    ).json()["id"]
    pref_id = client.post(
        "/api/v1/preferences",
        json={"style": "floral", "motifs": ["leaf"], "meaning_keywords": ["growth"], "avoid_list": []},
        headers=headers,
    ).json()["id"]
    upload = client.post(
        "/api/v1/uploads/file",
        data={"consent_id": consent_id},
        files={"file": ("scar.png", b"fake-image-binary", "image/png")},
        headers=headers,
    )
    assert upload.status_code == 200, upload.text
    upload_id = upload.json()["id"]
    generation = client.post(
        "/api/v1/generations",
        json={"upload_id": upload_id, "preference_id": pref_id, "variant_count": 2},
        headers=headers,
    )
    assert generation.status_code == 200, generation.text
    return generation.json()["id"], generation.json()["concepts"][0]["id"]


def test_file_upload_saves_and_serves_media(client: TestClient) -> None:
    session = create_session(client, "user")
    headers = auth_headers(session["token"])
    consent_id = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=headers,
    ).json()["id"]

    response = client.post(
        "/api/v1/uploads/file",
        data={"consent_id": consent_id},
        files={"file": ("scar.webp", b"raw-binary-content", "image/webp")},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    media_uri = payload["storage_uri"]
    media_response = client.get(media_uri)
    assert media_response.status_code == 200
    assert media_response.content == b"raw-binary-content"


def test_generation_uses_uploaded_image_bytes(client: TestClient, monkeypatch) -> None:
    class SpyProvider:
        def __init__(self) -> None:
            self.last_image: bytes | None = None
            self.last_content_type: str | None = None

        def generate(
            self,
            *,
            prompt_text: str,
            variant_count: int,
            input_image: bytes | None = None,
            input_content_type: str | None = None,
        ) -> GenerationBatch:
            self.last_image = input_image
            self.last_content_type = input_content_type
            assets = [GeneratedAsset(content=b"fake-png", extension=".png") for _ in range(variant_count)]
            return GenerationBatch(
                assets=assets,
                provider="spy",
                model_version="spy-v1",
                retries_used=0,
                provider_failures=0,
                used_fallback=False,
            )

    spy = SpyProvider()
    monkeypatch.setattr(dependencies, "_model_provider", spy)

    session = create_session(client, "user")
    headers = auth_headers(session["token"])
    consent_id = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=headers,
    ).json()["id"]
    preference_id = client.post(
        "/api/v1/preferences",
        json={"style": "floral", "motifs": ["leaf"], "meaning_keywords": ["growth"], "avoid_list": []},
        headers=headers,
    ).json()["id"]

    original_image = b"binary-upload-for-provider"
    upload = client.post(
        "/api/v1/uploads/file",
        data={"consent_id": consent_id},
        files={"file": ("scar.png", original_image, "image/png")},
        headers=headers,
    )
    assert upload.status_code == 200, upload.text

    generation = client.post(
        "/api/v1/generations",
        json={
            "upload_id": upload.json()["id"],
            "preference_id": preference_id,
            "variant_count": 1,
        },
        headers=headers,
    )
    assert generation.status_code == 200, generation.text
    assert spy.last_image == original_image
    assert spy.last_content_type == "image/png"


def test_collaboration_invite_note_revoke_flow(client: TestClient) -> None:
    user = create_session(client, "user")
    artist = create_session(client, "artist")
    user_headers = auth_headers(user["token"])
    artist_headers = auth_headers(artist["token"])

    _, concept_id = _create_generation_for_user(client, user_headers)

    invite = client.post(
        "/api/v1/collaborations/invite",
        json={"artist_actor_id": artist["actor_id"], "concept_ids": [concept_id]},
        headers=user_headers,
    )
    assert invite.status_code == 200, invite.text
    collaboration_id = invite.json()["id"]

    note = client.post(
        f"/api/v1/collaborations/{collaboration_id}/notes",
        json={"concept_id": concept_id, "note_text": "Use finer line weight around scar edge."},
        headers=artist_headers,
    )
    assert note.status_code == 200, note.text

    notes = client.get(f"/api/v1/collaborations/{collaboration_id}/notes", headers=user_headers)
    assert notes.status_code == 200
    assert len(notes.json()) == 1

    revoke = client.post(f"/api/v1/collaborations/{collaboration_id}/revoke", headers=user_headers)
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "revoked"

    blocked_note = client.post(
        f"/api/v1/collaborations/{collaboration_id}/notes",
        json={"note_text": "This should fail after revoke."},
        headers=artist_headers,
    )
    assert blocked_note.status_code == 409
    assert blocked_note.json()["code"] == "COLLABORATION_REVOKED"
