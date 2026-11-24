"""Owner-only route: rank a team's pending join requests with the matching module."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .matching import Requirement, rank_users
from .models import JoinRequest, Team, TeamMember, TeamSkill, User, UserSkill

router = APIRouter(prefix="/api/teams", tags=["matching"])


def skill_levels(db: Session, user_ids: list[int]) -> dict[int, dict[int, int]]:
    """{user_id: {skill_id: level}} for the given users, read from user_skills."""
    levels: dict[int, dict[int, int]] = {user_id: {} for user_id in user_ids}
    rows = db.execute(select(UserSkill).where(UserSkill.user_id.in_(user_ids))).scalars()
    for row in rows:
        levels[row.user_id][row.skill_id] = row.level
    return levels


@router.get("/{team_id}/requests/ranked")
def ranked_requests(
    team_id: int,
    focus: list[int] = Query(default=[], description="Optional skill IDs to give more weight"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the team owner can rank requests")

    requests = db.scalars(
        select(JoinRequest).where(JoinRequest.team_id == team_id, JoinRequest.status == "pending")
    ).all()
    # Members added by name have no account and no skills on record, so only registered members count.
    member_ids = list(db.scalars(
        select(TeamMember.user_id).where(TeamMember.team_id == team_id, TeamMember.user_id.is_not(None))
    ))
    # Hard requirements are must-haves. (Their `count` is used by the approval feature.)
    requirements = [
        Requirement(skill_id=row.skill_id, min_level=row.min_level, must_have=row.is_hard)
        for row in db.scalars(select(TeamSkill).where(TeamSkill.team_id == team_id))
    ]

    requester_ids = [request.user_id for request in requests]
    levels = skill_levels(db, requester_ids + member_ids)

    ranking = rank_users(
        candidates={user_id: levels[user_id] for user_id in requester_ids},
        requirements=requirements,
        team_member_skills=[levels[user_id] for user_id in member_ids],
        focus_skill_ids=set(focus),
    )

    request_by_user = {request.user_id: request for request in requests}
    return [
        {"request_id": request_by_user[user_id].id, "user_id": user_id, **asdict(result)}
        for user_id, result in ranking
    ]
