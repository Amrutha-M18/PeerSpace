from concurrent.futures import ThreadPoolExecutor

import pytest


def test_added_skill_is_shared_and_can_be_selected(signed_in):
    original_auth = signed_in.headers["Authorization"]
    response = signed_in.post("/api/skills", json={"name": "  Rust  "})
    assert response.status_code == 201
    skill = response.json()
    assert set(skill) == {"id", "name"}
    assert skill["name"] == "Rust"
    assert skill in signed_in.get("/api/skills").json()
    assert signed_in.get("/api/me").json()["skills"] == []

    bob = signed_in.post("/api/auth/signup", json={
        "name": "Bob", "email": "bob@example.com", "password": "test-password",
    }).json()
    signed_in.headers["Authorization"] = "Bearer " + bob["token"]
    assert skill in signed_in.get("/api/skills").json()
    assert signed_in.post("/api/skills", json={"name": "rust"}).json() == skill
    saved = signed_in.put("/api/me/skills", json=[{
        "skill_id": skill["id"], "level": 4,
    }])
    assert saved.status_code == 200
    assert saved.json()["skills"] == [{
        "skill_id": skill["id"], "name": "Rust", "level": 4,
    }]
    signed_in.headers["Authorization"] = original_auth
    assert signed_in.get("/api/me").json()["skills"] == []


def test_duplicate_names_reuse_catalog_entry(signed_in):
    for name in ("Python", "python", " PYTHON ", "\tpython\n"):
        response = signed_in.post("/api/skills", json={"name": name})
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "Python"}
    assert len(signed_in.get("/api/skills").json()) == 2


def test_simultaneous_submissions_create_one_entry(signed_in):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(
            lambda name: signed_in.post("/api/skills", json={"name": name}),
            ["Rust", " rust "],
        ))
    assert sorted(response.status_code for response in responses) == [200, 201]
    assert responses[0].json() == responses[1].json()
    assert len(signed_in.get("/api/skills").json()) == 3


@pytest.mark.parametrize("body", [
    {}, {"name": ""}, {"name": " \t\n"}, {"name": "x" * 101},
    {"name": None}, {"name": 123}, {"name": "Rust", "user_id": 1},
])
def test_invalid_catalog_entries_are_rejected(signed_in, body):
    assert signed_in.post("/api/skills", json=body).status_code == 422
    assert len(signed_in.get("/api/skills").json()) == 2


def test_catalog_name_maximum_length(signed_in):
    response = signed_in.post("/api/skills", json={"name": "x" * 100})
    assert response.status_code == 201
    assert response.json()["name"] == "x" * 100
