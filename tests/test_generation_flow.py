from __future__ import annotations

from conftest import auth_headers, create_session
from fastapi.testclient import TestClient


def _prepare_user_flow(client: TestClient) -> tuple[dict[str, str], str, str]:
    session = create_session(client, "user")
    headers = auth_headers(session["token"])

    consent = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=headers,
    )
    assert consent.status_code == 200, consent.text
    consent_id = consent.json()["id"]

    pref = client.post(
        "/api/v1/preferences",
        json={
            "style": "floral",
            "motifs": ["lotus", "line-art"],
            "meaning_keywords": ["rebirth", "strength"],
            "avoid_list": ["dark skull"],
            "mood": "calm",
        },
        headers=headers,
    )
    assert pref.status_code == 200, pref.text
    pref_id = pref.json()["id"]

    upload = client.post(
        "/api/v1/uploads",
        json={
            "consent_id": consent_id,
            "filename": "scar.png",
            "content_type": "image/png",
            "size_bytes": 1024,
            "checksum": "abc123",
        },
        headers=headers,
    )
    assert upload.status_code == 200, upload.text
    upload_id = upload.json()["id"]
    return headers, pref_id, upload_id


def test_happy_path_generation(client: TestClient) -> None:
    headers, pref_id, upload_id = _prepare_user_flow(client)

    generation = client.post(
        "/api/v1/generations",
        json={"upload_id": upload_id, "preference_id": pref_id, "variant_count": 3},
        headers=headers,
    )
    assert generation.status_code == 200, generation.text
    payload = generation.json()
    assert payload["status"] == "completed"
    assert len(payload["concepts"]) == 3
    assert payload["model_version"] != ""
    assert payload["prompt_hash"] != ""

    admin_session = create_session(client, "admin")
    admin_headers = auth_headers(admin_session["token"])
    metrics = client.get("/api/v1/admin/metrics", headers=admin_headers)
    assert metrics.status_code == 200, metrics.text
    counters = metrics.json()["counters"]
    assert counters["generation_requests_total"] >= 1
    assert counters["generation_success_total"] >= 1
    assert counters["generation_latency_ms_last"] >= 0


def test_safety_blocked_prompt(client: TestClient) -> None:
    session = create_session(client, "user")
    headers = auth_headers(session["token"])

    consent = client.post(
        "/api/v1/consents",
        json={"policy_version": "consent-v1", "disclaimer_accepted": True},
        headers=headers,
    )
    consent_id = consent.json()["id"]

    pref = client.post(
        "/api/v1/preferences",
        json={
            "style": "text",
            "motifs": ["self-harm message"],
            "meaning_keywords": [],
            "avoid_list": [],
            "mood": "tense",
        },
        headers=headers,
    )
    pref_id = pref.json()["id"]

    upload = client.post(
        "/api/v1/uploads",
        json={
            "consent_id": consent_id,
            "filename": "scar.png",
            "content_type": "image/png",
            "size_bytes": 512,
        },
        headers=headers,
    )
    upload_id = upload.json()["id"]

    generation = client.post(
        "/api/v1/generations",
        json={"upload_id": upload_id, "preference_id": pref_id, "variant_count": 2},
        headers=headers,
    )
    assert generation.status_code == 422
    body = generation.json()
    assert body["code"] == "SAFETY_BLOCKED"
