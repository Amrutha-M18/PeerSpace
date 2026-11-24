"""Create, list, and retrieve opportunities stored in the database."""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Opportunity, User

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


def list_opportunities(db: Session, category: str | None, q: str | None, upcoming: bool | None):
    query = select(Opportunity)
    if category:
        query = query.where(Opportunity.category == category)
    if q and q.strip():
        keyword = q.strip()
        query = query.where(or_(
            Opportunity.title.icontains(keyword, autoescape=True),
            Opportunity.description.icontains(keyword, autoescape=True),
        ))
    if upcoming:
        query = query.where(Opportunity.starts_on >= date.today())
    return [OpportunityOut.model_validate(item) for item in db.scalars(query.order_by(Opportunity.id)).all()]


@router.post("", response_model=OpportunityOut, status_code=201)
def create_opportunity(
    data: OpportunityCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    opportunity = Opportunity(**data.model_dump(), created_by_id=user.id)
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.get("/{opportunity_id}", response_model=OpportunityOut)
def get_stored_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity
