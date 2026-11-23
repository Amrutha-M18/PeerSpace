from fastapi.testclient import TestClient
from sqlalchemy import inspect

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
    monkeypatch.setattr(main, "engine", profile_engine)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
    assert {column["name"] for column in inspect(profile_engine).get_columns("user_skills")} == {
        "user_id", "skill_id", "level",
    }
    assert {column["name"] for column in inspect(profile_engine).get_columns("users")} == set(
        User.__table__.columns.keys()
    )
