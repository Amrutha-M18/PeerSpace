"""Creating teams, viewing them, and removing members. Skills 1 = Python, 2 = SQL (seeded)."""

import pytest

from backend.models import Opportunity


def new_opportunity(client, title="Hackathon"):
    return client.post("/api/opportunities", json={"title": title, "category": "hackathon"}).json()["id"]


def team_payload(**changes):
    payload = {
        "name": "Pixel",
        "description": "Building a campus app",
        "capacity": 4,
        "default_members": ["Kabir", " Meera "],
        "hard_requirements": [{"skill_id": 1, "min_level": 3, "count": 2}],
        "soft_requirements": [{"skill_id": 2, "min_level": 2}],
    }
    payload.update(changes)
    return payload


def other_user(client, email="riya@example.com"):
    """Sign up a second user and return headers that act as them."""
    client.post("/api/auth/signup", json={"email": email, "password": "password123", "name": "Riya"})
    token = client.post("/api/auth/login", json={"email": email, "password": "password123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_team(signed_in):
    opp = new_opportunity(signed_in)
    res = signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload())
    assert res.status_code == 201
    team = res.json()
    assert team["name"] == "Pixel" and team["opportunity_id"] == opp
    assert team["capacity"] == 4 and team["open_slots"] == 1 and team["status"] == "open"
    owner, kabir, meera = team["members"]
    assert owner["role"] == "owner" and owner["user_id"] == team["owner_id"] and owner["name"] == "Student"
    assert kabir == {"id": kabir["id"], "name": "Kabir", "user_id": None, "role": "member"}
    assert meera["name"] == "Meera"  # trimmed
    assert team["hard_requirements"] == [{"skill_id": 1, "name": "Python", "min_level": 3, "count": 2}]
    assert team["soft_requirements"] == [{"skill_id": 2, "name": "SQL", "min_level": 2}]
    assert signed_in.get(f"/api/teams/{team['id']}").json() == team
    assert signed_in.get(f"/api/opportunities/{opp}/teams").json() == [team]


def test_minimal_team_and_full_team(signed_in):
    opp = new_opportunity(signed_in)
    team = signed_in.post(f"/api/opportunities/{opp}/teams", json={"name": "Solo+1", "capacity": 2}).json()
    assert team["members"][0]["role"] == "owner" and team["open_slots"] == 1
    assert team["description"] is None and team["hard_requirements"] == team["soft_requirements"] == []
    opp2 = new_opportunity(signed_in, "Trek")
    full = signed_in.post(f"/api/opportunities/{opp2}/teams", json={"name": "Full", "capacity": 2, "default_members": ["Kabir"]})
    assert full.json()["status"] == "full" and full.json()["open_slots"] == 0


@pytest.mark.parametrize("changes", [
    {"name": " "}, {"name": "x" * 101}, {"capacity": 1}, {"capacity": 21}, {"capacity": "4"},
    {"capacity": 2, "default_members": ["Kabir", "Meera"]},           # owner + 2 > 2
    {"default_members": [""]}, {"default_members": ["x" * 101]},
    {"hard_requirements": [{"skill_id": 1, "min_level": 0}]},
    {"hard_requirements": [{"skill_id": 1, "min_level": 6}]},
    {"hard_requirements": [{"skill_id": 1, "min_level": 3, "count": 0}]},
    {"hard_requirements": [{"skill_id": 1, "min_level": 3, "count": 5}]},  # more than capacity 4
    {"hard_requirements": [{"skill_id": 1, "min_level": 3}, {"skill_id": 1, "min_level": 2}]},
    {"soft_requirements": [{"skill_id": 1, "min_level": 2}]},           # Python is already hard
    {"soft_requirements": [{"skill_id": 2, "min_level": 2, "count": 3}]},
    {"hard_requirements": [{"skill_id": 999, "min_level": 3}]},
    {"owner_id": 5},
])
def test_invalid_teams_are_rejected(signed_in, changes):
    opp = new_opportunity(signed_in)
    assert signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload(**changes)).status_code == 422
    assert signed_in.get(f"/api/opportunities/{opp}/teams").json() == []


def test_team_rules(signed_in, profile_db):
    opp = new_opportunity(signed_in)
    assert signed_in.post("/api/opportunities/999999/teams", json=team_payload()).status_code == 404
    assert signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload()).status_code == 201
    # One team per student per opportunity
    again = signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload(name="Another"))
    assert again.status_code == 409
    # Team names are unique within an opportunity (ignoring case)
    riya = other_user(signed_in)
    clash = signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload(name="pixel"), headers=riya)
    assert clash.status_code == 409
    assert signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload(name="Byte"), headers=riya).status_code == 201
    # Opportunities that don't take teams (e.g. a scraped internship)
    with profile_db() as db:
        solo = Opportunity(title="Internship", category="other", is_team_based=False)
        db.add(solo); db.commit(); solo_id = solo.id
    assert signed_in.post(f"/api/opportunities/{solo_id}/teams", json=team_payload()).status_code == 422


def test_owner_removes_a_member(signed_in):
    opp = new_opportunity(signed_in)
    team = signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload(capacity=3)).json()
    assert team["status"] == "full"
    owner, kabir, _ = team["members"]
    res = signed_in.delete(f"/api/teams/{team['id']}/members/{kabir['id']}")
    assert res.status_code == 200
    updated = res.json()
    assert [m["name"] for m in updated["members"]] == ["Student", "Meera"]
    assert updated["status"] == "open" and updated["open_slots"] == 1
    assert signed_in.delete(f"/api/teams/{team['id']}/members/{kabir['id']}").status_code == 404
    assert signed_in.delete(f"/api/teams/{team['id']}/members/{owner['id']}").status_code == 400


def test_only_the_owner_removes_members(signed_in):
    opp = new_opportunity(signed_in)
    team = signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload()).json()
    kabir = team["members"][1]
    riya = other_user(signed_in)
    assert signed_in.delete(f"/api/teams/{team['id']}/members/{kabir['id']}", headers=riya).status_code == 403
    assert signed_in.delete(f"/api/teams/999999/members/{kabir['id']}").status_code == 404
    # A member id from a different team
    opp2 = new_opportunity(signed_in, "Trek")
    other = signed_in.post(f"/api/opportunities/{opp2}/teams", json=team_payload(name="Byte"), headers=riya).json()
    assert signed_in.delete(f"/api/teams/{team['id']}/members/{other['members'][1]['id']}").status_code == 404


def test_team_routes_need_login(signed_in):
    opp = new_opportunity(signed_in)
    team = signed_in.post(f"/api/opportunities/{opp}/teams", json=team_payload()).json()
    signed_in.headers.pop("Authorization")
    signed_in.cookies.clear()
    for method, path in (("POST", f"/api/opportunities/{opp}/teams"), ("GET", f"/api/opportunities/{opp}/teams"),
                         ("GET", f"/api/teams/{team['id']}"), ("DELETE", f"/api/teams/{team['id']}/members/1")):
        assert signed_in.request(method, path, json=team_payload()).status_code == 401
