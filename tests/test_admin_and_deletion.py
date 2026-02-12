from __future__ import annotations

from conftest import auth_headers, create_session
from fastapi.testclient import TestClient


def _create_generation(client: TestClient, headers: dict[str, str]) -> str:
    consent_id = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=headers,
    ).json()["id"]
    pref_id = client.post(
        "/api/v1/preferences",
        json={"style": "minimal", "motifs": ["leaf"], "meaning_keywords": ["hope"], "avoid_list": []},
        headers=headers,
    ).json()["id"]
    upload_id = client.post(
        "/api/v1/uploads",
        json={
            "consent_id": consent_id,
            "filename": "scar.webp",
            "content_type": "image/webp",
            "size_bytes": 888,
        },
        headers=headers,
    ).json()["id"]
    generation = client.post(
        "/api/v1/generations",
        json={"upload_id": upload_id, "preference_id": pref_id, "variant_count": 1},
        headers=headers,
    )
    assert generation.status_code == 200, generation.text
    return generation.json()["id"]


def test_admin_can_disable_generation(client: TestClient) -> None:
    admin_session = create_session(client, "admin")
    user_session = create_session(client, "user")

    admin_headers = auth_headers(admin_session["token"])
    user_headers = auth_headers(user_session["token"])

    disable = client.post(
        "/api/v1/admin/generation/disable",
        json={"disabled": True, "reason": "incident drill"},
        headers=admin_headers,
    )
    assert disable.status_code == 200, disable.text
    assert disable.json()["generation_disabled"] is True

    consent_id = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=user_headers,
    ).json()["id"]
    pref_id = client.post(
        "/api/v1/preferences",
        json={"style": "line", "motifs": ["lotus"], "meaning_keywords": ["growth"], "avoid_list": []},
        headers=user_headers,
    ).json()["id"]
    upload_id = client.post(
        "/api/v1/uploads",
        json={
            "consent_id": consent_id,
            "filename": "s.png",
            "content_type": "image/png",
            "size_bytes": 777,
        },
        headers=user_headers,
    ).json()["id"]

    blocked = client.post(
        "/api/v1/generations",
        json={"upload_id": upload_id, "preference_id": pref_id, "variant_count": 1},
        headers=user_headers,
    )
    assert blocked.status_code == 503
    assert blocked.json()["code"] == "GENERATION_DISABLED"


def test_user_deletion_removes_generation_access(client: TestClient) -> None:
    user_session = create_session(client, "user")
    headers = auth_headers(user_session["token"])
    generation_id = _create_generation(client, headers)

    deletion = client.post("/api/v1/deletions", json={"reason": "user request"}, headers=headers)
    assert deletion.status_code == 200, deletion.text
    assert deletion.json()["status"] == "completed"

    generation = client.get(f"/api/v1/generations/{generation_id}", headers=headers)
    assert generation.status_code == 401
