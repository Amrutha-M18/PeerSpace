from datetime import date, timedelta

def test_create_and_retrieve_opportunity(signed_in):
    client = signed_in
    payload = {
        "title": "Campus Hackathon 2026", "category": "hackathon",
        "starts_on": "2026-12-01", "ends_on": "2026-12-02",
        "official_url": "https://example.com/hackathon", "team_size": 4,
        "description": "Build a project together.", "organizer": "Coding Club",
    }
    created = client.post("/api/opportunities", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert all(body[key] == value for key, value in payload.items())
    me = client.get("/api/auth/me").json()
    assert body["created_by_id"] == me["id"]  # the signed-in owner is recorded
    assert body["is_team_based"] is True       # default
    retrieved = client.get(f"/api/opportunities/{body['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json() == body


def test_missing_opportunity_and_invalid_input(signed_in):
    client = signed_in
    assert client.get("/api/opportunities/999").status_code == 404
    assert client.post("/api/opportunities", json={"title": "A", "category": "invalid"}).status_code == 422
    assert client.post("/api/opportunities", json={
        "title": "A", "category": "other", "starts_on": "2026-12-02", "ends_on": "2026-12-01"
    }).status_code == 422


def test_list_search_and_filter_opportunities(signed_in):
    client = signed_in
    today = date.today()
    items = [
        {"title": "Campus Hackathon", "category": "hackathon", "description": "Build apps", "starts_on": str(today)},
        {"title": "Old Hackathon", "category": "hackathon", "description": "Campus projects", "starts_on": str(today - timedelta(days=1))},
        {"title": "Study Night", "category": "study group", "description": "On CAMPUS", "starts_on": str(today + timedelta(days=1))},
        {"title": "Undated Event", "category": "other"},
    ]
    for item in items:
        assert client.post("/api/opportunities", json=item).status_code == 201

    def titles(params):
        response = client.get("/api/opportunities", params=params)
        assert response.status_code == 200
        return [item["title"] for item in response.json()]

    assert len(titles({})) == 4
    assert titles({"category": "hackathon"}) == ["Campus Hackathon", "Old Hackathon"]
    assert titles({"q": "cAmPuS"}) == ["Campus Hackathon", "Old Hackathon", "Study Night"]
    assert titles({"upcoming": "true"}) == ["Campus Hackathon", "Study Night"]
    assert titles({"category": "hackathon", "q": "campus", "upcoming": "true"}) == ["Campus Hackathon"]
    assert titles({"q": "missing"}) == []


def test_domain_cannot_be_combined_with_stored_filters(client):
    response = client.get("/api/opportunities", params={"domain": "cse", "upcoming": "false"})
    assert response.status_code == 400


def test_creating_an_opportunity_requires_login(client):
    response = client.post("/api/opportunities", json={"title": "A", "category": "other"})
    assert response.status_code == 401


def test_opportunity_input_rules(signed_in):
    def post(**fields):
        return signed_in.post("/api/opportunities", json={"title": "Trek", "category": "trek", **fields})

    trimmed = post(title="  Weekend Trek  ", organizer="  ", official_url="")
    assert trimmed.status_code == 201
    assert trimmed.json()["title"] == "Weekend Trek"
    assert trimmed.json()["organizer"] is None and trimmed.json()["official_url"] is None

    assert post(title="   ").status_code == 422                       # blank title
    assert post(official_url="example.com").status_code == 422        # needs http(s)://
    assert post(team_size=1).status_code == 422                       # a team needs 2+
    assert post(team_size=21).status_code == 422
    assert post(is_team_based=False, team_size=4).status_code == 422  # size only for team-based

    solo = post(is_team_based=False)
    assert solo.status_code == 201 and solo.json()["is_team_based"] is False


def test_teams_respect_the_opportunity(signed_in):
    def new_opportunity(**fields):
        return signed_in.post("/api/opportunities", json={"title": "Event", "category": "other", **fields}).json()["id"]

    limited = new_opportunity(team_size=3)
    too_big = signed_in.post(f"/api/opportunities/{limited}/teams", json={"name": "Big", "capacity": 4})
    assert too_big.status_code == 422
    assert signed_in.post(f"/api/opportunities/{limited}/teams", json={"name": "Fits", "capacity": 3}).status_code == 201

    solo = new_opportunity(is_team_based=False)
    assert signed_in.post(f"/api/opportunities/{solo}/teams", json={"name": "T", "capacity": 2}).status_code == 422
