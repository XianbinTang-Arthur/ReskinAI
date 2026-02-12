from __future__ import annotations

import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reskin_ai.dependencies import reset_repo  # noqa: E402
from reskin_ai.main import create_app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    reset_repo()
    app = create_app()
    return TestClient(app)


def create_session(client: TestClient, role: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/session", json={"role": role})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

