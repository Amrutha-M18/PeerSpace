"""Seed everything PeerSpace needs for a demo with one command.

    python -m backend.seed           # skills, interests, demo users, opportunities, teams, join requests
    python -m backend.seed --reset   # delete the demo data first, then load it fresh

Safe to run again: anything that already exists (same email, opportunity title or team name)
is left alone. The demo data lives in backend/seed_data/demo.json, and every demo user logs in
with the password written there.
"""

import json
import sys
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from .auth import hash_password
from .config import engine as app_engine
from .migrations.profiles import migrate_profiles
from .models import (
    Base, Event, Hobby, Interest, JoinRequest, Opportunity, Skill, Team, TeamMember, TeamSkill,
    User, UserHobby, UserSkill,
)
from .seed_catalog import CATALOGUES, SEED_DIR, load_catalogue

DEMO_FILE = SEED_DIR / "demo.json"
MAX_CAPACITY = 20
LEVELS = range(1, 5)  # 1 Beginner .. 4 Expert, as in the frontend


def load_demo() -> dict:
    return json.loads(DEMO_FILE.read_text(encoding="utf-8"))


# ---------- check demo.json before writing anything

def check_demo(data: dict) -> list[str]:
    """Every way demo.json breaks the app's rules, in plain words (empty list = all good)."""
    problems = []
    users = data["users"]
    opportunities = {o["key"]: o for o in data["opportunities"]}

    emails = [u["email"].lower() for u in users.values()]
    problems += [f"Email used twice: {e}" for e, n in Counter(emails).items() if n > 1]
    for handle, user in users.items():
        problems += [f"{handle}: level for {s} must be 1-4" for s, level in user["skills"].items() if level not in LEVELS]
    for o in data["opportunities"]:
        if o["created_by"] not in users:
            problems.append(f"Opportunity {o['title']}: unknown user {o['created_by']}")
        size = o.get("team_size")
        if size is not None and not (2 <= size <= MAX_CAPACITY and o.get("is_team_based", True)):
            problems.append(f"Opportunity {o['title']}: team_size must be 2-20 and only on team-based opportunities")

    team_names = [t["name"] for t in data["teams"]]
    problems += [f"Team name used twice: {n}" for n, c in Counter(team_names).items() if c > 1]
    in_team = {}  # (opportunity key, user handle) -> team name
    for team in data["teams"]:
        where = f"Team {team['name']}"
        opportunity = opportunities.get(team["opportunity"])
        if opportunity is None:
            problems.append(f"{where}: unknown opportunity {team['opportunity']}")
            continue
        if not opportunity.get("is_team_based", True):
            problems.append(f"{where}: {opportunity['title']} doesn't take teams")
        limit = opportunity.get("team_size") or MAX_CAPACITY
        if not 2 <= team["capacity"] <= limit:
            problems.append(f"{where}: capacity must be 2-{limit}")
        people = [team["owner"], *team.get("members", [])]
        if len(people) + len(team.get("named_members", [])) > team["capacity"]:
            problems.append(f"{where}: more members than capacity")
        for handle in people:
            if handle not in users:
                problems.append(f"{where}: unknown user {handle}")
            elif (team["opportunity"], handle) in in_team:
                problems.append(f"{where}: {handle} is already in {in_team[team['opportunity'], handle]} for this opportunity")
            else:
                in_team[team["opportunity"], handle] = team["name"]
        requirements = team.get("hard", []) + team.get("soft", [])
        skills = [r["skill"].lower() for r in requirements]
        if len(skills) != len(set(skills)):
            problems.append(f"{where}: a skill is listed twice (it must be hard or soft, not both)")
        problems += [f"{where}: min_level for {r['skill']} must be 1-4" for r in requirements if r["min_level"] not in LEVELS]
        problems += [f"{where}: count for {r['skill']} is more than capacity"
                     for r in team.get("hard", []) if not 1 <= r.get("count", 1) <= team["capacity"]]

    teams = {t["name"]: t for t in data["teams"]}
    for request in data["join_requests"]:
        team = teams.get(request["team"])
        if team is None or request["user"] not in users:
            problems.append(f"Join request {request['user']} -> {request['team']}: unknown team or user")
        elif (team["opportunity"], request["user"]) in in_team:
            problems.append(f"Join request {request['user']} -> {request['team']}: already in a team for that opportunity")
    return problems


# ---------- remove the demo data

def reset_demo(db: Session, data: dict) -> int:
    """Delete the demo users and everything attached to them. Returns how many users were removed."""
    emails = [u["email"].lower() for u in data["users"].values()]
    user_ids = list(db.scalars(select(User.id).where(User.email.in_(emails))))
    if not user_ids:
        return 0
    opportunity_ids = list(db.scalars(select(Opportunity.id).where(Opportunity.created_by_id.in_(user_ids))))
    team_ids = list(db.scalars(select(Team.id).where(
        or_(Team.opportunity_id.in_(opportunity_ids), Team.owner_id.in_(user_ids))
    )))
    # Children first, so foreign keys never point at deleted rows.
    db.execute(delete(JoinRequest).where(or_(JoinRequest.team_id.in_(team_ids), JoinRequest.user_id.in_(user_ids))))
    db.execute(delete(TeamSkill).where(TeamSkill.team_id.in_(team_ids)))
    db.execute(delete(TeamMember).where(or_(TeamMember.team_id.in_(team_ids), TeamMember.user_id.in_(user_ids))))
    db.execute(delete(Event).where(or_(
        Event.team_id.in_(team_ids), Event.opportunity_id.in_(opportunity_ids), Event.user_id.in_(user_ids)
    )))
    db.execute(delete(Interest).where(or_(Interest.opportunity_id.in_(opportunity_ids), Interest.user_id.in_(user_ids))))
    db.execute(delete(Team).where(Team.id.in_(team_ids)))
    db.execute(delete(Opportunity).where(Opportunity.id.in_(opportunity_ids)))
    db.execute(delete(UserSkill).where(UserSkill.user_id.in_(user_ids)))
    db.execute(delete(UserHobby).where(UserHobby.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.id.in_(user_ids)))
    return len(user_ids)


# ---------- add the demo data

def ids_by_name(db: Session, model) -> dict[str, int]:
    return {name.strip().lower(): row_id for row_id, name in db.execute(select(model.id, model.name))}


def find(ids: dict[str, int], name: str, what: str) -> int:
    if name.lower() not in ids:
        raise ValueError(f"demo.json uses the {what} {name!r}, which isn't in the {what} list (seed_data/*.txt)")
    return ids[name.lower()]


def seed_demo(db: Session, data: dict, today: date) -> Counter:
    """Add whatever demo rows are missing. Returns how many of each were added."""
    added = Counter()
    skills, hobbies = ids_by_name(db, Skill), ids_by_name(db, Hobby)
    password_hash = None  # bcrypt is slow on purpose, so hash the shared password only once

    users = {}  # handle -> User
    for handle, info in data["users"].items():
        email = info["email"].lower()
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            password_hash = password_hash or hash_password(data["password"])
            user = User(email=email, name=info["name"], password_hash=password_hash)
            db.add(user)
            db.flush()
            db.add_all([UserSkill(user_id=user.id, skill_id=find(skills, name, "skill"), level=level)
                        for name, level in info["skills"].items()])
            db.add_all([UserHobby(user_id=user.id, hobby_id=find(hobbies, name, "interest"))
                        for name in info["interests"]])
            added["users"] += 1
        users[handle] = user

    opportunities = {}  # key -> Opportunity
    for info in data["opportunities"]:
        opportunity = db.scalar(select(Opportunity).where(func.lower(Opportunity.title) == info["title"].lower()))
        if opportunity is None:
            opportunity = Opportunity(
                title=info["title"], category=info["category"], organizer=info.get("organizer"),
                description=info.get("description"), official_url=info.get("official_url"),
                starts_on=today + timedelta(days=info["starts_in_days"]),
                ends_on=today + timedelta(days=info["ends_in_days"]),
                is_team_based=info.get("is_team_based", True), team_size=info.get("team_size"),
                created_by_id=users[info["created_by"]].id,
            )
            db.add(opportunity)
            db.flush()
            added["opportunities"] += 1
        opportunities[info["key"]] = opportunity

    teams = {}  # name -> Team
    for info in data["teams"]:
        opportunity = opportunities[info["opportunity"]]
        team = db.scalar(select(Team).where(
            Team.opportunity_id == opportunity.id, func.lower(Team.name) == info["name"].lower()
        ))
        if team is None:
            owner = users[info["owner"]]
            members = [users[handle] for handle in info.get("members", [])]
            named = info.get("named_members", [])
            team = Team(
                opportunity_id=opportunity.id, owner_id=owner.id, name=info["name"],
                description=info.get("description"), capacity=info["capacity"],
                status="full" if 1 + len(members) + len(named) >= info["capacity"] else "open",
            )
            db.add(team)
            db.flush()
            db.add(TeamMember(team_id=team.id, user_id=owner.id, name=owner.name, role="owner"))
            db.add_all([TeamMember(team_id=team.id, user_id=m.id, name=m.name, role="member") for m in members])
            db.add_all([TeamMember(team_id=team.id, name=name, role="member") for name in named])
            db.add_all([TeamSkill(team_id=team.id, skill_id=find(skills, r["skill"], "skill"),
                                  min_level=r["min_level"], is_hard=True, count=r.get("count", 1))
                        for r in info.get("hard", [])])
            db.add_all([TeamSkill(team_id=team.id, skill_id=find(skills, r["skill"], "skill"),
                                  min_level=r["min_level"], is_hard=False, count=1)
                        for r in info.get("soft", [])])
            added["teams"] += 1
        teams[info["name"]] = team

    for info in data["join_requests"]:
        team, user = teams[info["team"]], users[info["user"]]
        exists = db.scalar(select(JoinRequest.id).where(
            JoinRequest.team_id == team.id, JoinRequest.user_id == user.id, JoinRequest.status == "pending"
        ))
        if not exists:
            db.add(JoinRequest(team_id=team.id, user_id=user.id, message=info.get("message"), status="pending"))
            added["join requests"] += 1
    return added


# ---------- everything together

def seed(engine=app_engine, reset: bool = False, today: date | None = None, log=print) -> Counter:
    data = load_demo()
    problems = check_demo(data)
    if problems:
        raise ValueError("demo.json has problems:\n  - " + "\n  - ".join(problems))

    Base.metadata.create_all(engine)
    migrate_profiles(engine)
    with engine.begin() as connection:
        for key in CATALOGUES:
            log(load_catalogue(connection, key))

    with Session(engine) as db:
        if reset:
            log(f"reset: removed {reset_demo(db, data)} demo users and their opportunities, teams and requests")
        added = seed_demo(db, data, today or date.today())
        db.commit()
    for what in ("users", "opportunities", "teams", "join requests"):
        log(f"{what}: {added[what]} added")
    return added


if __name__ == "__main__":
    args = sys.argv[1:]
    if args not in ([], ["--reset"]):
        sys.exit("Usage: python -m backend.seed [--reset]")
    try:
        seed(reset=args == ["--reset"])
    except ValueError as error:
        sys.exit(str(error))
    demo = load_demo()
    first = next(iter(demo["users"].values()))
    print(f"\nDone. Log in as any demo user, e.g. {first['email']} / {demo['password']}")
