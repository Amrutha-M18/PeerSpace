"""Ask to join a team, take the request back, and see your own requests.

Accepting or declining requests is the team owner's job (see the approval feature).
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import JoinRequest, Opportunity, Team, TeamMember, User
from .teams import get_team_or_404

router = APIRouter(prefix="/api", tags=["join requests"])


class JoinRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None


class JoinRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    user_id: int
    message: str | None
    status: str  # pending, accepted, rejected
    created_at: datetime


@router.post("/teams/{team_id}/requests", response_model=JoinRequestOut, status_code=201)
def request_to_join(
    team_id: int, data: JoinRequestIn | None = None,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        team = get_team_or_404(db, team_id, lock=True)  # lock: two clicks can't make two requests
        in_team = db.scalar(
            select(TeamMember.team_id).join(Team, Team.id == TeamMember.team_id)
            .where(TeamMember.user_id == user.id, Team.opportunity_id == team.opportunity_id)
        )
        if in_team == team.id:
            raise HTTPException(status_code=409, detail="You're already in this team")
        if in_team:
            raise HTTPException(status_code=409, detail="You're already in a team for this opportunity")
        if team.status == "full":
            raise HTTPException(status_code=409, detail="This team is full")

        earlier = db.scalar(
            select(JoinRequest).where(JoinRequest.team_id == team.id, JoinRequest.user_id == user.id)
            .order_by(JoinRequest.id.desc())
        )
        if earlier and earlier.status == "pending":
            raise HTTPException(status_code=409, detail="You've already asked to join this team")
        if earlier and earlier.status == "rejected":
            raise HTTPException(status_code=409, detail="The owner declined your request to join this team")

        request = JoinRequest(team_id=team.id, user_id=user.id, message=(data.message if data else None) or None)
        db.add(request)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(request)
    return request


@router.delete("/teams/{team_id}/requests/mine", status_code=204)
def withdraw_request(team_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = db.scalar(select(JoinRequest).where(
        JoinRequest.team_id == team_id, JoinRequest.user_id == user.id, JoinRequest.status == "pending"
    ))
    if request is None:
        raise HTTPException(status_code=404, detail="You have no pending request for this team")
    db.delete(request)
    db.commit()
    return Response(status_code=204)


@router.get("/opportunities/{opportunity_id}/my-requests", response_model=list[JoinRequestOut])
def my_requests(opportunity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The signed-in user's requests to teams of this opportunity (newest first)."""
    if db.get(Opportunity, opportunity_id) is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return db.scalars(
        select(JoinRequest).join(Team, Team.id == JoinRequest.team_id)
        .where(Team.opportunity_id == opportunity_id, JoinRequest.user_id == user.id)
        .order_by(JoinRequest.id.desc())
    ).all()
