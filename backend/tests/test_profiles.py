from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import JWT_TOKEN
from backend.models import User


def selection(skill_id=1, level=3):
    return {"skill_id": skill_id, "level": level}


def profile_payload():
    return {
        "name": " Updated Student ",
        "availability": [" Weekends "], "hobbies": [" Photography ", "Trekking"],
        "skills": [selection()],
    }


def test_new_account_and_auth_compatibility(signed_in):
    response = signed_in.get("/api/me")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "email", "name", "availability", "hobbies", "skills", "created_at"}
    assert body["skills"] == body["hobbies"] == body["availability"] == []
    assert set(signed_in.get("/api/auth/me").json()) == {"id", "email", "name"}
    assert signed_in.get("/api/skills").json() == [{"id": 1, "name": "Python"}, {"id": 2, "name": "SQL"}]


def test_full_profile_and_skill_replacement(signed_in):
    response = signed_in.put("/api/me", json=profile_payload())
    assert response.status_code == 200
    saved = response.json()
    assert saved["name"] == "Updated Student"
    assert saved["hobbies"] == ["Photography", "Trekking"]
    assert saved["availability"] == ["Weekends"]
    assert saved["skills"] == [{**selection(), "name": "Python"}]
    assert signed_in.get("/api/me").json() == saved
    assert signed_in.put("/api/me", json=profile_payload()).json() == saved

    for skills in ([selection(1, 1), selection(2, 5)], [selection(2, 2)], []):
        response = signed_in.put("/api/me/skills", json=skills)
        assert response.status_code == 200
        current = response.json()
        assert current["skills"] == [{**item, "name": {1: "Python", 2: "SQL"}[item["skill_id"]]} for item in skills]
        assert {k: v for k, v in current.items() if k != "skills"} == {k: v for k, v in saved.items() if k != "skills"}
        assert signed_in.get("/api/me").json() == current


def test_full_profile_can_clear_lists(signed_in):
    assert signed_in.put("/api/me", json=profile_payload()).status_code == 200
    cleared = {"name": "Student", "availability": [], "hobbies": [], "skills": []}
    response = signed_in.put("/api/me", json=cleared)
    assert response.status_code == 200
    assert all(response.json()[key] == value for key, value in cleared.items())


@pytest.mark.parametrize("skills", [
    [selection(999)], [selection(), selection()],
    [selection(level=0)], [selection(level=6)], [selection(level=1.5)],
    [selection(level="3")], [selection(level=True)],
    [{**selection(), "open_to_teach": True}],
    [selection(skill_id=True)], [selection(skill_id="1")], [selection(skill_id=0)],
    [{"skill_id": 1}], [{"level": 2}], [{**selection(), "extra": True}],
])
def test_invalid_skills_are_atomic_for_both_endpoints(signed_in, skills):
    original = signed_in.put("/api/me", json=profile_payload()).json()
    for path, body in (("/api/me/skills", skills), ("/api/me", {**profile_payload(), "name": "Must not save", "skills": skills})):
        assert signed_in.put(path, json=body).status_code == 422
        assert signed_in.get("/api/me").json() == original


@pytest.mark.parametrize("change", [
    {"name": " "}, {"name": "x" * 101}, {"name": None},
    {"department": "Computer Science"}, {"department": None},
    {"year": "2"}, {"year": None},
    {"hobbies": [" "]}, {"availability": [3]}, {"hobbies": None},
    {"id": 2}, {"email": "changed@example.com"}, {"created_at": "2026-01-01"},
    {"password_hash": "bad"}, {"user_id": 2},
])
def test_invalid_profile_does_not_change_data(signed_in, change):
    before = signed_in.get("/api/me").json()
    assert signed_in.put("/api/me", json={**profile_payload(), **change}).status_code == 422
    assert signed_in.get("/api/me").json() == before


def test_full_replacement_requires_every_editable_field(signed_in):
    for field in profile_payload():
        body = profile_payload()
        del body[field]
        assert signed_in.put("/api/me", json=body).status_code == 422


@pytest.mark.parametrize("kind", ["missing", "invalid", "expired", "unknown_user"])
def test_every_endpoint_requires_valid_authentication(signed_in, kind):
    signed_in.headers.pop("Authorization")
    signed_in.cookies.clear()
    claims = {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    if kind == "expired":
        claims["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
    elif kind == "unknown_user":
        claims["sub"] = "9999"
    token = "not-a-token" if kind == "invalid" else jwt.encode(claims, JWT_TOKEN, algorithm="HS256")
    headers = {} if kind == "missing" else {"Authorization": "Bearer " + token}
    for method, path, body in (("GET", "/api/me", None), ("GET", "/api/skills", None),
                               ("POST", "/api/skills", {"name": "Rust"}),
                               ("PUT", "/api/me", profile_payload()), ("PUT", "/api/me/skills", [])):
        assert signed_in.request(method, path, headers=headers, json=body).status_code == 401


def test_users_have_independent_profiles(signed_in):
    alice_auth = signed_in.headers["Authorization"]
    alice = signed_in.put("/api/me", json=profile_payload()).json()
    bob = signed_in.post("/api/auth/signup", json={"name": "Bob", "email": "bob@example.com", "password": "test-password"}).json()
    signed_in.headers["Authorization"] = "Bearer " + bob["token"]
    assert signed_in.get("/api/me").json()["skills"] == []
    saved = signed_in.put("/api/me/skills", json=[selection(2)]).json()
    assert saved["id"] == bob["user"]["id"]
    assert saved["skills"][0]["skill_id"] == 2
    signed_in.headers["Authorization"] = alice_auth
    assert signed_in.get("/api/me").json() == alice


def test_commit_failure_rolls_back_entire_save(signed_in, profile_db, monkeypatch):
    before = signed_in.put("/api/me", json=profile_payload()).json()

    def fail_commit(self):
        self.flush()
        raise RuntimeError("Simulated database failure")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="Simulated database failure"):
            signed_in.put("/api/me", json={**profile_payload(), "name": "Must roll back", "skills": [selection(2)]})
    assert signed_in.get("/api/me").json() == before
    with profile_db() as db:
        assert db.scalar(select(User.name)) == before["name"]
