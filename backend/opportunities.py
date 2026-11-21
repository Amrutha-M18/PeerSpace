"""Create and retrieve opportunities stored in the database."""

from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from .database import get_db
from .models import Opportunity

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])
Category = Literal["hackathon", "course project", "study group", "trek", "sport", "other"]


class OpportunityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    category: Category
    description: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    official_url: str | None = Field(default=None, max_length=500)
    team_size: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("ends_on cannot be before starts_on")
        return self


class OpportunityOut(OpportunityCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


@router.post("", response_model=OpportunityOut, status_code=201)
def create_opportunity(data: OpportunityCreate, db: Session = Depends(get_db)):
    opportunity = Opportunity(**data.model_dump())
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
