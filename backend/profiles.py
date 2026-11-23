"""Authenticated profile reads and atomic profile/skill replacement."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StrictBool, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Skill, User, UserSkill

router = APIRouter(prefix="/api", tags=["profiles"])
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Year = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


class SkillSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: int = Field(strict=True, gt=0, le=2147483647)
    level: int = Field(strict=True, ge=1, le=5)
    open_to_teach: StrictBool


def unique_skills(skills: list[SkillSelection]) -> list[SkillSelection]:
    ids = [skill.skill_id for skill in skills]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate skill IDs are not allowed")
    return skills


Selections = Annotated[list[SkillSelection], AfterValidator(unique_skills)]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    department: Name | None
    year: Year | None
    availability: list[Name]
    hobbies: list[Name]
    skills: Selections


class CatalogSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SkillCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name


class ProfileSkill(SkillSelection):
    name: str


class ProfileOut(BaseModel):
    id: int
    email: str
    name: str
    department: str | None
    year: str | None
    availability: list[str]
    hobbies: list[str]
    skills: list[ProfileSkill]
    created_at: datetime


def read_profile(db: Session, user: User) -> ProfileOut:
    rows = db.execute(
        select(UserSkill, Skill.name)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(UserSkill.user_id == user.id)
        .order_by(Skill.name, Skill.id)
    ).all()
    return ProfileOut(
        id=user.id, email=user.email, name=user.name, department=user.department,
        year=user.year, availability=user.availability, hobbies=user.hobbies,
        created_at=user.created_at,
        skills=[ProfileSkill(skill_id=item.skill_id, name=name, level=item.level,
                             open_to_teach=item.open_to_teach) for item, name in rows],
    )


def save_profile(
    db: Session, user: User, selections: list[SkillSelection], details: ProfileUpdate | None = None,
) -> ProfileOut:
    try:
        # Serialize simultaneous replacements for the same user on PostgreSQL.
        db.execute(select(User.id).where(User.id == user.id).with_for_update())
        ids = [item.skill_id for item in selections]
        known = set(db.scalars(select(Skill.id).where(Skill.id.in_(ids))).all())
        unknown = sorted(set(ids) - known)
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown skill IDs: {unknown}")

        if details is not None:
            for field, value in details.model_dump(exclude={"skills"}).items():
                setattr(user, field, value)
        db.execute(delete(UserSkill).where(UserSkill.user_id == user.id))
        db.add_all([UserSkill(user_id=user.id, **item.model_dump()) for item in selections])
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return read_profile(db, user)


@router.get("/me", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return read_profile(db, user)


@router.put("/me", response_model=ProfileOut)
def put_profile(data: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return save_profile(db, user, data.skills, data)


@router.put("/me/skills", response_model=ProfileOut)
def put_skills(data: Selections, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return save_profile(db, user, data)


@router.get("/skills", response_model=list[CatalogSkill])
def get_skills(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Skill).order_by(Skill.name, Skill.id)).all()


@router.post("/skills", response_model=CatalogSkill, status_code=201)
def create_skill(
    data: SkillCreate, response: Response,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        # The unique index also handles simultaneous submissions of the same skill.
        row = db.execute(
            insert(Skill).values(name=data.name)
            .on_conflict_do_nothing(index_elements=[func.lower(func.btrim(Skill.name))])
            .returning(Skill.id, Skill.name)
        ).first()
        if row is None:
            row = db.execute(
                select(Skill.id, Skill.name).where(
                    func.lower(func.btrim(Skill.name)) == func.lower(func.btrim(data.name))
                )
            ).one()
            response.status_code = 200
        result = CatalogSkill(id=row.id, name=row.name)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
