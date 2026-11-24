"""Team page: owner-only applicant list (matching module), accept and decline."""

import pytest


def person(client, name, skills=None, interests=()):
    """Sign up a user, give them skills ({name: level}) and interests; return their auth header."""
    token = client.post("/api/auth/signup", json={
        "name": name, "email": f"{name.lower()}@example.com", "password": "test-password",
    }).json()["token"]
    headers = {"Authorization": "Bearer " + token}
    skill_ids = {s["name"]: s["id"] for s in client.get("/api/skills", headers=headers).json()}
    hobby_ids = {h["name"]: h["id"] for h in client.get("/api/hobbies", headers=headers).json()}
    body = {
        "name": name,
        "skills": [{"skill_id": skill_ids[n], "level": lvl} for n, lvl in (skills or {}).items()],
        "hobbies": [hobby_ids[n] for n in interests],
    }
    assert client.put("/api/me", json=body, headers=headers).status_code == 200
    return headers


@pytest.fixture
def team(profile_client):
    """Owner (Python 4) with a team of 3: must-have Python Advanced, nice-to-have SQL."""
    client = profile_client
    owner = person(client, "Owner", {"Python": 4})
    skills = {s["name"]: s["id"] for s in client.get("/api/skills", headers=owner).json()}
    opportunity = client.post("/api/opportunities", json={"title": "Hack", "category": "hackathon"}, headers=owner).json()["id"]
    team = client.post(f"/api/opportunities/{opportunity}/teams", headers=owner, json={
        "name": "Alpha", "capacity": 3,
        "hard_requirements": [{"skill_id": skills["Python"], "min_level": 3, "count": 2}],
        "soft_requirements": [{"skill_id": skills["SQL"], "min_level": 2}],
    }).json()
    return {"client": client, "owner": owner, "team": team, "opportunity": opportunity, "skills": skills}


def ask(t, headers, message=None):
    response = t["client"].post(f"/api/teams/{t['team']['id']}/requests", json={"message": message}, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def test_applicants_are_scored_sorted_and_owner_only(team):
    t, client = team, team["client"]
    strong = person(client, "Strong", {"Python": 4, "SQL": 3}, interests=["Trekking"])
    weak = person(client, "Weak", {"Python": 2})
    none = person(client, "None")
    ask(t, strong, "I know Python well")
    ask(t, weak)
    ask(t, none)
    url = f"/api/teams/{t['team']['id']}/applicants"

    applicants = client.get(url, headers=t["owner"]).json()  # default: non-decreasing score
    scores = [a["score"] for a in applicants]
    assert scores == sorted(scores)
    assert [a["name"] for a in applicants] == ["None", "Weak", "Strong"]

    best = client.get(url, params={"order": "best_first"}, headers=t["owner"]).json()
    assert [a["name"] for a in best] == ["Strong", "Weak", "None"]

    strong_card = best[0]
    assert strong_card["eligible"] is True and strong_card["missing_must_haves"] == []
    assert strong_card["message"] == "I know Python well" and strong_card["interests"] == ["Trekking"]
    python = next(c for c in strong_card["skill_checks"] if c["name"] == "Python")
    assert python == {"skill_id": t["skills"]["Python"], "name": "Python", "must_have": True, "required_level": 3,
                      "user_level": 4, "meets": True, "team_covers": True, "in_focus": False}
    assert strong_card["skill_checks"][0]["must_have"] is True  # must-haves listed first
    assert best[1]["eligible"] is False and best[1]["missing_must_haves"] == ["Python"]

    # Focusing on Python makes the owner's coverage stop discounting it.
    focused = client.get(url, params={"focus": t["skills"]["Python"], "order": "best_first"}, headers=t["owner"]).json()
    assert next(c for c in focused[0]["skill_checks"] if c["name"] == "Python")["in_focus"] is True

    # Nobody but the owner sees requests.
    assert client.get(url, headers=strong).status_code == 403
    assert client.get(f"/api/teams/{t['team']['id']}/requests/ranked", headers=strong).status_code == 403
    assert client.get("/api/teams/999/applicants", headers=t["owner"]).status_code == 404


def test_accept_and_decline(team):
    t, client = team, team["client"]
    team_id = t["team"]["id"]
    asha = person(client, "Asha", {"Python": 3})
    ben = person(client, "Ben", {"Python": 4})
    cara = person(client, "Cara")
    asha_request = ask(t, asha)
    ben_request = ask(t, ben)
    cara_request = ask(t, cara)

    # Asha also asked another team in the same opportunity; accepting her here drops that request.
    other_owner = person(client, "Other")
    other_team = client.post(f"/api/opportunities/{t['opportunity']}/teams", json={"name": "Beta", "capacity": 4}, headers=other_owner).json()["id"]
    assert client.post(f"/api/teams/{other_team}/requests", headers=asha).status_code == 201

    assert client.post(f"/api/teams/{team_id}/requests/{asha_request}/accept", headers=asha).status_code == 403
    accepted = client.post(f"/api/teams/{team_id}/requests/{asha_request}/accept", headers=t["owner"])
    assert accepted.status_code == 200
    body = accepted.json()
    assert [m["name"] for m in body["members"]] == ["Owner", "Asha"]
    assert body["open_slots"] == 1 and body["status"] == "open"
    assert body["hard_requirements"][0]["members_with_skill"] == 2  # Owner and Asha both have Python 3+
    mine = client.get(f"/api/opportunities/{t['opportunity']}/my-requests", headers=asha).json()
    assert [(r["team_id"], r["status"]) for r in mine] == [(team_id, "accepted")]
    assert client.post(f"/api/teams/{team_id}/requests/{asha_request}/accept", headers=t["owner"]).status_code == 409

    # Declining: the applicant sees "rejected" and can't ask again.
    declined = client.post(f"/api/teams/{team_id}/requests/{cara_request}/decline", headers=t["owner"])
    assert declined.status_code == 200 and declined.json()["status"] == "rejected"
    assert client.post(f"/api/teams/{team_id}/requests", headers=cara).status_code == 409

    # Ben fills the last place, so the team is full.
    full = client.post(f"/api/teams/{team_id}/requests/{ben_request}/accept", headers=t["owner"]).json()
    assert full["status"] == "full" and full["open_slots"] == 0
    assert client.get(f"/api/teams/{team_id}/applicants", headers=t["owner"]).json() == []

    # Anyone signed in can view the team page data; a member can't see requests.
    assert client.get(f"/api/teams/{team_id}", headers=cara).status_code == 200
    assert client.get(f"/api/teams/{team_id}/applicants", headers=ben).status_code == 403


def test_cannot_accept_into_a_full_team_or_someone_already_in_a_team(team):
    t, client = team, team["client"]
    team_id = t["team"]["id"]
    people = [person(client, n) for n in ("Dev", "Eve", "Fay")]
    requests = [ask(t, h) for h in people]
    for request in requests[:2]:
        assert client.post(f"/api/teams/{team_id}/requests/{request}/accept", headers=t["owner"]).status_code == 200
    full = client.post(f"/api/teams/{team_id}/requests/{requests[2]}/accept", headers=t["owner"])
    assert full.status_code == 409 and "full" in full.json()["detail"]

    # Fay joins her own team elsewhere; once a place opens here, she still can't be accepted.
    client.post(f"/api/opportunities/{t['opportunity']}/teams", json={"name": "Fays", "capacity": 2}, headers=people[2])
    member = next(m for m in client.get(f"/api/teams/{team_id}", headers=t["owner"]).json()["members"] if m["name"] == "Eve")
    assert client.delete(f"/api/teams/{team_id}/members/{member['id']}", headers=t["owner"]).status_code == 200
    taken = client.post(f"/api/teams/{team_id}/requests/{requests[2]}/accept", headers=t["owner"])
    assert taken.status_code == 409 and taken.json()["detail"] == "Fay has already joined Fays"
