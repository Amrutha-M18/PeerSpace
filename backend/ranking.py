"""Owner-only routes: rank a team's pending join requests with the matching module.

- GET /api/teams/{id}/requests/ranked   short list: request, user and score
- GET /api/teams/{id}/applicants        everything the team page shows the owner:
                                         profile details plus a skill-by-skill comparison
"""

from dataclasses import asdict
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .matching import MatchResult, Requirement, rank_users
from .models import Hobby, JoinRequest, Skill, Team, TeamMember, TeamSkill, User, UserHobby, UserSkill

router = APIRouter(prefix="/api/teams", tags=["matching"])
Order = Literal["lowest_first", "best_first"]


def skill_levels(db: Session, user_ids: list[int]) -> dict[int, dict[int, int]]:
    """{user_id: {skill_id: level}} for the given users, read from user_skills."""
    levels: dict[int, dict[int, int]] = {user_id: {} for user_id in user_ids}
    rows = db.execute(select(UserSkill).where(UserSkill.user_id.in_(user_ids))).scalars()
    for row in rows:
        levels[row.user_id][row.skill_id] = row.level
    return levels


def owned_team(db: Session, team_id: int, user: User) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the team owner can see join requests")
    return team


def rank_requests(
    db: Session, team: Team, focus: set[int], order: Order = "best_first",
) -> list[tuple[JoinRequest, MatchResult]]:
    """Score every pending request for the team with the matching module.

    best_first:   eligible people first, then highest score (the matching module's order)
    lowest_first: plain non-decreasing score order (ties: earliest request first)
    """
    requests = db.scalars(
        select(JoinRequest).where(JoinRequest.team_id == team.id, JoinRequest.status == "pending")
        .order_by(JoinRequest.id)
    ).all()
    # Members added by name have no account and no skills on record, so only registered members count.
    member_ids = list(db.scalars(
        select(TeamMember.user_id).where(TeamMember.team_id == team.id, TeamMember.user_id.is_not(None))
    ))
    requirements = [
        Requirement(skill_id=row.skill_id, min_level=row.min_level, must_have=row.is_hard)
        for row in db.scalars(select(TeamSkill).where(TeamSkill.team_id == team.id))
    ]
    requester_ids = [request.user_id for request in requests]
    levels = skill_levels(db, requester_ids + member_ids)

    ranking = rank_users(
        candidates={user_id: levels[user_id] for user_id in requester_ids},
        requirements=requirements,
        team_member_skills=[levels[user_id] for user_id in member_ids],
        focus_skill_ids=focus,
    )
    by_user = {request.user_id: request for request in requests}
    ranked = [(by_user[user_id], result) for user_id, result in ranking]
    if order == "lowest_first":
        ranked.sort(key=lambda pair: (pair[1].score, pair[0].id))
    return ranked


@router.get("/{team_id}/requests/ranked")
def ranked_requests(
    team_id: int,
    focus: list[int] = Query(default=[], description="Optional skill IDs to give more weight"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = owned_team(db, team_id, user)
    return [
        {"request_id": request.id, "user_id": request.user_id, **asdict(result)}
        for request, result in rank_requests(db, team, set(focus))
    ]


# ---------- the owner's applicant list on the team page

class SkillCheck(BaseModel):
    """One of the team's skills, compared with what the applicant has."""
    skill_id: int
    name: str
    must_have: bool
    required_level: int
    user_level: int        # 0 = doesn't have it
    meets: bool
    team_covers: bool      # a current member already meets it (so it counts for less)
    in_focus: bool


class ApplicantSkill(BaseModel):
    skill_id: int
    name: str
    level: int


class Applicant(BaseModel):
    request_id: int
    user_id: int
    name: str
    message: str | None
    requested_at: datetime
    score: float                 # 0-100, from the matching module
    eligible: bool               # meets every must-have
    missing_must_haves: list[str]
    skill_checks: list[SkillCheck]
    other_skills: list[ApplicantSkill]  # skills the team didn't ask for, strongest first
    interests: list[str]


@router.get("/{team_id}/applicants", response_model=list[Applicant])
def team_applicants(
    team_id: int,
    focus: list[int] = Query(default=[], description="Skill IDs the owner wants to weigh more"),
    order: Order = "lowest_first",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = owned_team(db, team_id, user)
    ranked = rank_requests(db, team, set(focus), order)
    user_ids = [request.user_id for request, _ in ranked]

    names = dict(db.execute(select(User.id, User.name).where(User.id.in_(user_ids))).all())
    hard = {row.skill_id: row.is_hard for row in db.scalars(select(TeamSkill).where(TeamSkill.team_id == team.id))}
    skill_names = dict(db.execute(select(Skill.id, Skill.name)).all())
    skills_of: dict[int, list[ApplicantSkill]] = {user_id: [] for user_id in user_ids}
    for row in db.scalars(select(UserSkill).where(UserSkill.user_id.in_(user_ids)).order_by(UserSkill.level.desc())):
        skills_of[row.user_id].append(ApplicantSkill(skill_id=row.skill_id, name=skill_names[row.skill_id], level=row.level))
    interests_of: dict[int, list[str]] = {user_id: [] for user_id in user_ids}
    for user_id, hobby in db.execute(
        select(UserHobby.user_id, Hobby.name).join(Hobby, Hobby.id == UserHobby.hobby_id)
        .where(UserHobby.user_id.in_(user_ids)).order_by(Hobby.name)
    ):
        interests_of[user_id].append(hobby)

    applicants = []
    for request, result in ranked:
        checks = [
            SkillCheck(
                skill_id=s.skill_id, name=skill_names[s.skill_id], must_have=hard.get(s.skill_id, False),
                required_level=s.required_level, user_level=s.user_level, meets=s.user_level >= s.required_level,
                team_covers=s.team_covers, in_focus=s.in_focus,
            )
            for s in result.skills
        ]
        checks.sort(key=lambda c: (not c.must_have, c.name))  # must-haves first
        applicants.append(Applicant(
            request_id=request.id, user_id=request.user_id, name=names[request.user_id],
            message=request.message, requested_at=request.created_at,
            score=result.score, eligible=result.eligible,
            missing_must_haves=sorted(skill_names[i] for i in result.missing_must_haves),
            skill_checks=checks,
            other_skills=[s for s in skills_of[request.user_id] if s.skill_id not in hard],
            interests=interests_of[request.user_id],
        ))
    return applicants
