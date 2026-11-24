"""Asking to join a team, withdrawing, and seeing your own requests."""


def sign_up(client, name):
    token = client.post("/api/auth/signup", json={
        "name": name, "email": f"{name.lower()}@example.com", "password": "test-password",
    }).json()["token"]
    return {"Authorization": "Bearer " + token}


def test_join_withdraw_and_status(signed_in):
    client = signed_in  # the team owner
    opportunity = client.post("/api/opportunities", json={"title": "Hack", "category": "hackathon"}).json()["id"]
    team = client.post(f"/api/opportunities/{opportunity}/teams", json={"name": "Alpha", "capacity": 3}).json()["id"]
    asha = sign_up(client, "Asha")

    # The owner can't ask to join their own team.
    assert client.post(f"/api/teams/{team}/requests").status_code == 409

    sent = client.post(f"/api/teams/{team}/requests", json={"message": "  Python, ML  "}, headers=asha)
    assert sent.status_code == 201
    assert sent.json()["status"] == "pending" and sent.json()["message"] == "Python, ML"
    assert client.post(f"/api/teams/{team}/requests", headers=asha).status_code == 409  # no duplicates

    mine = client.get(f"/api/opportunities/{opportunity}/my-requests", headers=asha).json()
    assert [(r["team_id"], r["status"]) for r in mine] == [(team, "pending")]

    # The owner sees it in the ranked list.
    assert [r["user_id"] for r in client.get(f"/api/teams/{team}/requests/ranked").json()] == [sent.json()["user_id"]]

    assert client.delete(f"/api/teams/{team}/requests/mine", headers=asha).status_code == 204
    assert client.get(f"/api/opportunities/{opportunity}/my-requests", headers=asha).json() == []
    assert client.delete(f"/api/teams/{team}/requests/mine", headers=asha).status_code == 404
    assert client.post(f"/api/teams/{team}/requests", headers=asha).status_code == 201  # can ask again


def test_join_rules(signed_in, profile_db):
    from backend.models import JoinRequest

    client = signed_in
    opportunity = client.post("/api/opportunities", json={"title": "Trek", "category": "trek"}).json()["id"]
    full = client.post(f"/api/opportunities/{opportunity}/teams",
                       json={"name": "Full", "capacity": 2, "default_members": ["Ravi"]}).json()["id"]
    asha, ben = sign_up(client, "Asha"), sign_up(client, "Ben")
    assert client.post(f"/api/teams/{full}/requests", headers=asha).json()["detail"] == "This team is full"

    # Ben has his own team, so he can't ask to join another team in the same opportunity.
    bens = client.post(f"/api/opportunities/{opportunity}/teams", json={"name": "Bens", "capacity": 4}, headers=ben).json()["id"]
    assert client.post(f"/api/teams/{full}/requests", headers=ben).json()["detail"] == "You're already in a team for this opportunity"
    assert client.post(f"/api/teams/{bens}/requests", headers=ben).json()["detail"] == "You're already in this team"

    # Once the owner declines, the same person can't ask again.
    request = client.post(f"/api/teams/{bens}/requests", headers=asha).json()["id"]
    with profile_db() as db:
        db.get(JoinRequest, request).status = "rejected"
        db.commit()
    assert client.post(f"/api/teams/{bens}/requests", headers=asha).status_code == 409
    assert client.get(f"/api/opportunities/{opportunity}/my-requests", headers=asha).json()[0]["status"] == "rejected"

    assert client.post("/api/teams/999/requests", headers=asha).status_code == 404
    assert client.get("/api/opportunities/999/my-requests", headers=asha).status_code == 404
    client.headers.pop("Authorization")
    client.cookies.clear()  # signing up also set a login cookie
    assert client.post(f"/api/teams/{bens}/requests").status_code == 401
