from fastapi.testclient import TestClient

from backend import main
from backend.main import app


def test_invalid_domain_returns_a_clear_400_response():
    client = TestClient(app)

    response = client.get("/api/opportunities?domain=civil")

    assert response.status_code == 400
    assert "Unsupported domain" in response.json()["detail"]


def test_valid_domain_returns_the_documented_response_shape(monkeypatch):
    monkeypatch.setattr(main, "scrape_opportunities", lambda domain: ([{"title": "Demo"}], ["One source failed."]))
    client = TestClient(app)

    response = client.get("/api/opportunities?domain=cse")

    assert response.status_code == 200
    assert response.json()["domain"] == "cse"
    assert response.json()["opportunities"] == [{"title": "Demo"}]
    assert response.json()["warnings"] == ["One source failed."]
    assert "fetched_at" in response.json()
