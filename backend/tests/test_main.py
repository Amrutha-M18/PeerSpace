from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from backend import main
from backend.main import app
from backend.models import User

def test_health_check():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_applies_profile_migrations(profile_engine, monkeypatch):
    # Exercise the real startup sequence against an isolated test schema.
    main.Base.metadata.create_all(profile_engine)
    with profile_engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE user_skills ADD COLUMN open_to_teach BOOLEAN NOT NULL")
        connection.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN department VARCHAR(100), ADD COLUMN year VARCHAR(30)"
        )
        connection.exec_driver_sql("ALTER TABLE users ADD COLUMN availability JSON NOT NULL")
    monkeypatch.setattr(main, "engine", profile_engine)

    def test_db():
        with Session(profile_engine) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, main.get_db, test_db)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        signup = client.post("/api/auth/signup", json={
            "name": "New", "email": "new@example.com", "password": "test-password",
        })
        assert signup.status_code == 201
        saved = client.put("/api/me", json={
            "name": "Updated", "hobbies": ["Photography"], "skills": [],
        }, headers={"Authorization": "Bearer " + signup.json()["token"]})
        assert saved.status_code == 200
        assert saved.json()["name"] == "Updated"
        assert saved.json()["hobbies"] == ["Photography"]
        assert set(saved.json()) == {"id", "email", "name", "hobbies", "skills", "created_at"}
    assert {column["name"] for column in inspect(profile_engine).get_columns("user_skills")} == {
        "user_id", "skill_id", "level",
    }
    assert {column["name"] for column in inspect(profile_engine).get_columns("users")} == set(
        User.__table__.columns.keys()
    )
