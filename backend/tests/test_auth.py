"""Auth tests. They use a throwaway in-memory SQLite database, so no Postgres is needed."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.main import app
from backend.models import Base


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def signup(client, email="riya@example.com", password="secret123"):
    return client.post("/api/auth/signup", json={"email": email, "password": password, "name": "Riya"})


def test_signup_returns_a_token(client):
    res = signup(client)
    assert res.status_code == 201
    assert res.json()["token"]
    assert res.json()["user"]["email"] == "riya@example.com"


def test_invalid_email_is_rejected(client):
    assert signup(client, email="not-an-email").status_code == 422


def test_duplicate_email_returns_409(client):
    signup(client)
    assert signup(client, email="RIYA@example.com").status_code == 409


def test_login_with_right_password(client):
    signup(client)
    res = client.post("/api/auth/login", json={"email": "riya@example.com", "password": "secret123"})
    assert res.status_code == 200
    assert res.json()["token"]


def test_login_with_wrong_password_returns_401(client):
    signup(client)
    res = client.post("/api/auth/login", json={"email": "riya@example.com", "password": "wrong"})
    assert res.status_code == 401


def test_protected_route_without_token_returns_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_protected_route_with_bad_token_returns_401(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_protected_route_with_token_returns_the_user(client):
    token = signup(client).json()["token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["name"] == "Riya"


def test_password_is_not_stored_in_plain_text(client):
    signup(client)
    db = next(app.dependency_overrides[get_db]())
    from backend.models import User
    assert db.query(User).first().password_hash != "secret123"
