"""Create, list, and retrieve opportunities stored in the database."""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .feed import is_over, match_interests, sort_key
from .models import Hobby, Opportunity, Team, User, UserHobby

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])
Category = Literal["hackathon", "course project", "study group", "trek", "sport", "other"]
MAX_TEAM_SIZE = 20  # same limit as a team's capacity
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Text200 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Text500 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Text2000 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class OpportunityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    category: Category
    organizer: Text200 | None = None
    description: Text2000 | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    official_url: Text500 | None = None
    is_team_based: bool = True                                  # can people form teams for it?
    team_size: int | None = Field(default=None, ge=2, le=MAX_TEAM_SIZE)  # max people per team, if any

    @field_validator("organizer", "description", "official_url")
    @classmethod
    def empty_to_none(cls, value: str | None):
        return value or None

    @field_validator("official_url")
    @classmethod
    def validate_url(cls, value: str | None):
        if value and not value.lower().startswith(("http://", "https://")):
            raise ValueError("official_url must start with http:// or https://")
        return value

    @model_validator(mode="after")
    def validate_opportunity(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("ends_on cannot be before starts_on")
        if not self.is_team_based and self.team_size is not None:
            raise ValueError("team_size only applies to team-based opportunities")
        return self


class OpportunityOut(BaseModel):
    """What the API returns. Plain types (no input rules) so older rows always load."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    organizer: str | None
    description: str | None
    starts_on: date | None
    ends_on: date | None
    official_url: str | None
    is_team_based: bool
    team_size: int | None
    created_by_id: int | None
    created_at: datetime


class FeedItem(OpportunityOut):
    match_score: int               # 0 = no overlap with the user's interests
    matched_interests: list[str]   # the user's interests this opportunity fits, best first
    team_count: int
    open_team_count: int


def list_stored(db: Session, category: str | None, q: str | None) -> list[Opportunity]:
    """Opportunities in a category and/or whose title, description or organizer contains `q`."""
    query = select(Opportunity)
    if category:
        query = query.where(Opportunity.category == category)
    if q and q.strip():
        keyword = q.strip()
        query = query.where(or_(
            Opportunity.title.icontains(keyword, autoescape=True),
            Opportunity.description.icontains(keyword, autoescape=True),
            Opportunity.organizer.icontains(keyword, autoescape=True),
        ))
    return list(db.scalars(query.order_by(Opportunity.id)))


def list_opportunities(db: Session, category: str | None, q: str | None, upcoming: bool | None):
    found = list_stored(db, category, q)
    if upcoming:
        found = [o for o in found if o.starts_on is not None and o.starts_on >= date.today()]
    return [OpportunityOut.model_validate(item) for item in found]


@router.post("", response_model=OpportunityOut, status_code=201)
def create_opportunity(
    data: OpportunityCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    opportunity = Opportunity(**data.model_dump(), created_by_id=user.id)
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.get("/feed", response_model=list[FeedItem])
def opportunity_feed(
    q: str | None = None,
    category: Category | None = None,
    include_past: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Opportunities for the dashboard, best match with the user's interests first."""
    today = date.today()
    found = [o for o in list_stored(db, category, q) if include_past or not is_over(o, today)]
    interests = list(db.scalars(
        select(Hobby.name).join(UserHobby, UserHobby.hobby_id == Hobby.id).where(UserHobby.user_id == user.id)
    ))
    teams = {
        opportunity_id: (total, open_count)
        for opportunity_id, total, open_count in db.execute(
            select(Team.opportunity_id, func.count(), func.count(case((Team.status == "open", 1))))
            .where(Team.opportunity_id.in_([o.id for o in found]))
            .group_by(Team.opportunity_id)
        )
    }
    matches = {o.id: match_interests(o, interests) for o in found}
    return [
        FeedItem(
            **OpportunityOut.model_validate(o).model_dump(),
            match_score=matches[o.id].score, matched_interests=matches[o.id].interests,
            team_count=teams.get(o.id, (0, 0))[0], open_team_count=teams.get(o.id, (0, 0))[1],
        )
        for o in sorted(found, key=lambda o: sort_key(o, matches[o.id]))
    ]


# Keep this after /feed, or "feed" would be read as an opportunity id.
@router.get("/{opportunity_id}", response_model=OpportunityOut)
def get_stored_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity
