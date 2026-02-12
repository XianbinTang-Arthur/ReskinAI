from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_redirects_to_ui(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/ui/"


def test_ui_assets_are_served(client: TestClient) -> None:
    page = client.get("/ui/")
    assert page.status_code == 200
    assert "ReSkin AI | Commercial Product Console" in page.text

    client_page = client.get("/ui/client.html")
    assert client_page.status_code == 200
    assert "ReSkin AI | Client Flow" in client_page.text

    artist_page = client.get("/ui/artist.html")
    assert artist_page.status_code == 200
    assert "ReSkin AI | Artist Workspace" in artist_page.text

    admin_page = client.get("/ui/admin.html")
    assert admin_page.status_code == 200
    assert "ReSkin AI | Operations" in admin_page.text

    css = client.get("/ui/styles.css")
    assert css.status_code == 200

    app_js = client.get("/ui/app.js")
    assert app_js.status_code == 200
