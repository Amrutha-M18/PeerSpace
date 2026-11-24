"""Create teams, view them, and let the owner remove members."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Opportunity, Skill, Team, TeamMember, TeamSkill, User

router = APIRouter(prefix="/api", tags=["teams"])

MAX_CAPACITY = 20
Text100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SkillId = Annotated[int, Field(strict=True, gt=0, le=2147483647)]
Level = Annotated[int, Field(strict=True, ge=1, le=5)]


# ---------- request bodies

class HardRequirement(BaseModel):
    """Must be met. `count` = how many members the team needs with this skill."""
    model_config = ConfigDict(extra="forbid")

    skill_id: SkillId
    min_level: Level
    count: int = Field(default=1, strict=True, ge=1, le=MAX_CAPACITY)


class SoftRequirement(BaseModel):
    """Nice to have: counts towards the match score but filters no one out."""
    model_config = ConfigDict(extra="forbid")

    skill_id: SkillId
    min_level: Level = 1


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Text100
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None = None
    capacity: int = Field(strict=True, ge=2, le=MAX_CAPACITY)  # total team size, owner included
    default_members: list[Text100] = []                         # people added by name
    hard_requirements: list[HardRequirement] = []
    soft_requirements: list[SoftRequirement] = []

    @model_validator(mode="after")
    def check_team(self):
        if 1 + len(self.default_members) > self.capacity:
            raise ValueError("More members than the team's capacity (the owner counts as one)")
        skill_ids = [r.skill_id for r in self.hard_requirements + self.soft_requirements]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Each skill can be listed once, as either a hard or a soft requirement")
        for requirement in self.hard_requirements:
            if requirement.count > self.capacity:
                raise ValueError("A hard requirement can't need more members than the team's capacity")
        return self


# ---------- responses

class MemberOut(BaseModel):
    id: int
    name: str
    user_id: int | None  # empty for people added by name
    role: str


class HardRequirementOut(HardRequirement):
    name: str


class SoftRequirementOut(SoftRequirement):
    name: str


class TeamOut(BaseModel):
    id: int
    opportunity_id: int
    owner_id: int
    name: str
    description: str | None
    capacity: int
    status: str
    open_slots: int
    members: list[MemberOut]
    hard_requirements: list[HardRequirementOut]
    soft_requirements: list[SoftRequirementOut]
    created_at: datetime


def read_team(db: Session, team: Team) -> TeamOut:
    members = db.scalars(
        select(TeamMember).where(TeamMember.team_id == team.id).order_by(TeamMember.id)
    ).all()
    requirements = db.execute(
        select(TeamSkill, Skill.name)
        .join(Skill, Skill.id == TeamSkill.skill_id)
        .where(TeamSkill.team_id == team.id)
        .order_by(Skill.name)
    ).all()
    return TeamOut(
        id=team.id, opportunity_id=team.opportunity_id, owner_id=team.owner_id,
        name=team.name, description=team.description, capacity=team.capacity,
        status=team.status, open_slots=max(team.capacity - len(members), 0),
        created_at=team.created_at,
        members=[MemberOut(id=m.id, name=m.name, user_id=m.user_id, role=m.role) for m in members],
        hard_requirements=[
            HardRequirementOut(skill_id=r.skill_id, name=name, min_level=r.min_level, count=r.count)
            for r, name in requirements if r.is_hard
        ],
        soft_requirements=[
            SoftRequirementOut(skill_id=r.skill_id, name=name, min_level=r.min_level)
            for r, name in requirements if not r.is_hard
        ],
    )


def get_team_or_404(db: Session, team_id: int, lock: bool = False) -> Team:
    query = select(Team).where(Team.id == team_id)
    if lock:
        query = query.with_for_update()  # stops two changes to the same team racing
    team = db.scalar(query)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# ---------- routes

@router.post("/opportunities/{opportunity_id}/teams", response_model=TeamOut, status_code=201)
def create_team(
    opportunity_id: int, data: TeamCreate,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if not opportunity.is_team_based:
        raise HTTPException(status_code=422, detail="This opportunity doesn't take teams")
    if opportunity.team_size and data.capacity > opportunity.team_size:
        raise HTTPException(
            status_code=422, detail=f"Teams for this opportunity can have at most {opportunity.team_size} people",
        )

    # A student can be in only one team per opportunity.
    already_in_team = db.scalar(
        select(TeamMember.id).join(Team, Team.id == TeamMember.team_id)
        .where(TeamMember.user_id == user.id, Team.opportunity_id == opportunity_id)
    )
    if already_in_team:
        raise HTTPException(status_code=409, detail="You are already in a team for this opportunity")

    name_taken = db.scalar(
        select(Team.id).where(
            Team.opportunity_id == opportunity_id,
            func.lower(Team.name) == data.name.lower(),
        )
    )
    if name_taken:
        raise HTTPException(status_code=409, detail="A team with this name already exists for this opportunity")

    requirements = data.hard_requirements + data.soft_requirements
    skill_ids = [r.skill_id for r in requirements]
    known = set(db.scalars(select(Skill.id).where(Skill.id.in_(skill_ids))).all())
    unknown = sorted(set(skill_ids) - known)
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown skill IDs: {unknown}")

    try:
        member_count = 1 + len(data.default_members)
        team = Team(
            opportunity_id=opportunity_id, owner_id=user.id, name=data.name,
            description=data.description or None, capacity=data.capacity,
            status="full" if member_count >= data.capacity else "open",
        )
        db.add(team)
        db.flush()  # gives the team its id

        db.add(TeamMember(team_id=team.id, user_id=user.id, name=user.name, role="owner"))
        db.add_all([TeamMember(team_id=team.id, name=name, role="member") for name in data.default_members])
        db.add_all([
            TeamSkill(team_id=team.id, skill_id=r.skill_id, min_level=r.min_level, is_hard=True, count=r.count)
            for r in data.hard_requirements
        ])
        db.add_all([
            TeamSkill(team_id=team.id, skill_id=r.skill_id, min_level=r.min_level, is_hard=False, count=1)
            for r in data.soft_requirements
        ])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return read_team(db, team)


@router.get("/opportunities/{opportunity_id}/teams", response_model=list[TeamOut])
def list_teams(opportunity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.get(Opportunity, opportunity_id) is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    teams = db.scalars(select(Team).where(Team.opportunity_id == opportunity_id).order_by(Team.id)).all()
    return [read_team(db, team) for team in teams]


@router.get("/teams/{team_id}", response_model=TeamOut)
def get_team(team_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return read_team(db, get_team_or_404(db, team_id))


@router.delete("/teams/{team_id}/members/{member_id}", response_model=TeamOut)
def remove_member(
    team_id: int, member_id: int,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        team = get_team_or_404(db, team_id, lock=True)
        if team.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Only the team owner can remove members")
        member = db.get(TeamMember, member_id)
        if member is None or member.team_id != team.id:
            raise HTTPException(status_code=404, detail="Member not found in this team")
        if member.role == "owner":
            raise HTTPException(status_code=400, detail="The owner can't be removed from their own team")
        db.delete(member)
        team.status = "open"  # a slot just opened up
        db.commit()
    except Exception:
        db.rollback()
        raise
    return read_team(db, team)
