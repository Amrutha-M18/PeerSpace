"""`python -m backend.seed`: the demo data follows the app's rules and loads safely."""

import copy

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import JoinRequest, Opportunity, Skill, Team, User
from backend.seed import check_demo, load_demo, seed


def quiet(*_):
    pass


def counts(engine):
    with Session(engine) as db:
        return {model.__name__: db.scalar(select(func.count()).select_from(model))
                for model in (User, Opportunity, Team, JoinRequest)}


def test_demo_file_follows_the_rules():
    assert check_demo(load_demo()) == []


def test_rule_breaks_are_reported():
    data = copy.deepcopy(load_demo())
    data["teams"][0]["capacity"] = 9                   # HackCampus allows teams of 4
    data["teams"][1]["members"].append("rohan")        # rohan is already in Pixel Pushers
    data["teams"][0]["soft"].append({"skill": "Python", "min_level": 2})  # Python is already hard
    problems = "\n".join(check_demo(data))
    assert "capacity must be 2-4" in problems
    assert "rohan is already in Pixel Pushers" in problems
    assert "listed twice" in problems


def test_seed_is_safe_to_rerun_and_reset(profile_engine):
    data = load_demo()
    expected = {"User": len(data["users"]), "Opportunity": len(data["opportunities"]),
                "Team": len(data["teams"]), "JoinRequest": len(data["join_requests"])}

    first = seed(profile_engine, log=quiet)
    assert counts(profile_engine) == expected
    assert first["users"] == expected["User"]
    with Session(profile_engine) as db:
        assert db.scalar(select(func.count()).select_from(Skill)) > 40  # catalogues loaded too

    again = seed(profile_engine, log=quiet)
    assert sum(again.values()) == 0                    # nothing added twice
    assert counts(profile_engine) == expected

    seed(profile_engine, reset=True, log=quiet)
    assert counts(profile_engine) == expected          # removed, then loaded fresh


def test_seeded_data_works_through_the_api(client, profile_engine):
    seed(profile_engine, log=quiet)
    login = client.post("/api/auth/login", json={"email": "diya@peerspace.demo", "password": "peerspace123"})
    assert login.status_code == 200
    client.headers["Authorization"] = "Bearer " + login.json()["token"]

    opportunities = client.get("/api/opportunities").json()
    assert len(opportunities) == 9
    upcoming = [o["title"] for o in client.get("/api/opportunities", params={"upcoming": "true"}).json()]
    assert "Freshers' Design Sprint" not in upcoming   # the one in the past

    hackcampus = next(o["id"] for o in opportunities if o["title"] == "HackCampus 2026")
    teams = {t["name"]: t for t in client.get(f"/api/opportunities/{hackcampus}/teams").json()}
    pixel = teams["Pixel Pushers"]
    assert [m["name"] for m in pixel["members"]] == ["Diya Patel", "Rohan Gupta", "Aisha Khan"]
    assert pixel["open_slots"] == 1

    # Diya owns Pixel Pushers, so she can rank its three pending requests.
    ranked = client.get(f"/api/teams/{pixel['id']}/requests/ranked").json()
    with Session(profile_engine) as db:
        names = {u.id: u.name for u in db.scalars(select(User))}
    order = [names[r["user_id"]] for r in ranked]
    assert set(order[:2]) == {"Aarav Sharma", "Ishita Rao"} and order[2] == "Tanvi Desai"
    assert ranked[2]["eligible"] is False              # Tanvi's Python is below the must-have level
