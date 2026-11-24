"""The owner-only ranking route, against PostgreSQL (uses conftest.py fixtures)."""

from backend.models import JoinRequest, Opportunity, Team, TeamMember, TeamSkill, User, UserSkill


def make_team(profile_db, owner_email="student@example.com", sql_is_hard=False):
    """Owner (the signed-in student) + 2 applicants. Skills 1 = Python, 2 = SQL (seeded)."""
    with profile_db() as db:
        owner = db.query(User).filter_by(email=owner_email).one()
        riya = User(email="riya@example.com", password_hash="x", name="Riya")
        dev = User(email="dev@example.com", password_hash="x", name="Dev")
        db.add_all([riya, dev]); db.flush()
        opp = Opportunity(title="Hackathon", category="hackathon"); db.add(opp); db.flush()
        team = Team(opportunity_id=opp.id, owner_id=owner.id, name="Pixel", capacity=4)
        db.add(team); db.flush()
        db.add_all([TeamSkill(team_id=team.id, skill_id=1, min_level=3, is_hard=False),
                    TeamSkill(team_id=team.id, skill_id=2, min_level=3, is_hard=sql_is_hard)])
        db.add_all([TeamMember(team_id=team.id, user_id=owner.id, name=owner.name, role="owner"),
                    TeamMember(team_id=team.id, name="Kabir")])  # added by name: no skills on record
        db.add_all([UserSkill(user_id=owner.id, skill_id=1, level=4),  # team has Python
                    UserSkill(user_id=riya.id, skill_id=2, level=4),   # Riya: SQL
                    UserSkill(user_id=dev.id, skill_id=1, level=5)])   # Dev: Python
        db.add_all([JoinRequest(team_id=team.id, user_id=riya.id), JoinRequest(team_id=team.id, user_id=dev.id)])
        db.commit()
        return team.id, riya.id, dev.id


def test_owner_sees_requests_ranked_by_fit(signed_in, profile_db):
    team_id, riya, dev = make_team(profile_db)
    res = signed_in.get(f"/api/teams/{team_id}/requests/ranked")
    assert res.status_code == 200
    ranked = res.json()
    # The team already has Python, so Riya (SQL) fills the gap and ranks first.
    assert [r["user_id"] for r in ranked] == [riya, dev]
    assert ranked[0]["score"] == 80.0 and ranked[0]["skills"][0]["team_covers"] is True


def test_hard_requirement_is_a_must_have(signed_in, profile_db):
    team_id, riya, dev = make_team(profile_db, sql_is_hard=True)
    ranked = {r["user_id"]: r for r in signed_in.get(f"/api/teams/{team_id}/requests/ranked").json()}
    assert ranked[riya]["eligible"] is True
    assert ranked[dev]["eligible"] is False and ranked[dev]["missing_must_haves"] == [2]


def test_focus_filter_reorders(signed_in, profile_db):
    team_id, riya, dev = make_team(profile_db)
    res = signed_in.get(f"/api/teams/{team_id}/requests/ranked", params={"focus": [1]})
    assert [r["user_id"] for r in res.json()] == [dev, riya]


def test_only_the_owner_can_rank(signed_in, profile_db):
    team_id, *_ = make_team(profile_db)
    with profile_db() as db:
        db.query(Team).filter_by(id=team_id).update({"owner_id": db.query(User).filter_by(email="riya@example.com").one().id})
        db.commit()
    assert signed_in.get(f"/api/teams/{team_id}/requests/ranked").status_code == 403
    assert signed_in.get("/api/teams/999999/requests/ranked").status_code == 404
