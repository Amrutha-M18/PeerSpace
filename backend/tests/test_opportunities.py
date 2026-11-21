import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.main import app
from backend.models import Base


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def test_db():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_create_and_retrieve_opportunity(client):
    payload = {
        "title": "Campus Hackathon 2026", "category": "hackathon",
        "starts_on": "2026-12-01", "ends_on": "2026-12-02",
        "official_url": "https://example.com/hackathon", "team_size": 4,
        "description": "Build a project together.",
    }
    created = client.post("/api/opportunities", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert all(body[key] == value for key, value in payload.items())
    retrieved = client.get(f"/api/opportunities/{body['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json() == body


def test_missing_opportunity_and_invalid_input(client):
    assert client.get("/api/opportunities/999").status_code == 404
    assert client.post("/api/opportunities", json={"title": "A", "category": "invalid"}).status_code == 422
    assert client.post("/api/opportunities", json={
        "title": "A", "category": "other", "starts_on": "2026-12-02", "ends_on": "2026-12-01"
    }).status_code == 422
