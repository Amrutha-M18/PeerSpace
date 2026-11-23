from datetime import date, timedelta

def test_create_and_retrieve_opportunity(client):
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
    retrieved = client.get(f"/api/opportunities/{body['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json() == body


def test_missing_opportunity_and_invalid_input(client):
    assert client.get("/api/opportunities/999").status_code == 404
    assert client.post("/api/opportunities", json={"title": "A", "category": "invalid"}).status_code == 422
    assert client.post("/api/opportunities", json={
        "title": "A", "category": "other", "starts_on": "2026-12-02", "ends_on": "2026-12-01"
    }).status_code == 422


def test_list_search_and_filter_opportunities(client):
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
