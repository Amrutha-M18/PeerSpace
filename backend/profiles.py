"""Authenticated profile reads and atomic profile/skill replacement."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Hobby, Skill, User, UserHobby, UserSkill

router = APIRouter(prefix="/api", tags=["profiles"])
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SkillSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: int = Field(strict=True, gt=0, le=2147483647)
    level: int = Field(strict=True, ge=1, le=5)


def unique_skills(skills: list[SkillSelection]) -> list[SkillSelection]:
    ids = [skill.skill_id for skill in skills]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate skill IDs are not allowed")
    return skills


Selections = Annotated[list[SkillSelection], AfterValidator(unique_skills)]


HobbyId = Annotated[int, Field(strict=True, gt=0, le=2147483647)]


def unique_hobbies(hobby_ids: list[int]) -> list[int]:
    if len(hobby_ids) != len(set(hobby_ids)):
        raise ValueError("Duplicate hobby IDs are not allowed")
    return hobby_ids


# Interests are just picked or not picked: a list of hobby IDs, no levels.
HobbyIds = Annotated[list[HobbyId], AfterValidator(unique_hobbies)]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    hobbies: HobbyIds
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


class ProfileHobby(BaseModel):
    hobby_id: int
    name: str


class PublicProfileOut(BaseModel):
    """What any signed-in student can see about another user (no email)."""
    id: int
    name: str
    skills: list[ProfileSkill]


class ProfileOut(BaseModel):
    id: int
    email: str
    name: str
    hobbies: list[ProfileHobby]
    skills: list[ProfileSkill]
    created_at: datetime


def read_profile(db: Session, user: User) -> ProfileOut:
    rows = db.execute(
        select(UserSkill, Skill.name)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(UserSkill.user_id == user.id)
        .order_by(Skill.name, Skill.id)
    ).all()
    hobby_rows = db.execute(
        select(Hobby.id, Hobby.name)
        .join(UserHobby, UserHobby.hobby_id == Hobby.id)
        .where(UserHobby.user_id == user.id)
        .order_by(Hobby.name, Hobby.id)
    ).all()
    return ProfileOut(
        id=user.id, email=user.email, name=user.name,
        created_at=user.created_at,
        skills=[ProfileSkill(skill_id=item.skill_id, name=name, level=item.level) for item, name in rows],
        hobbies=[ProfileHobby(hobby_id=hobby_id, name=name) for hobby_id, name in hobby_rows],
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
            hobby_ids = details.hobbies
            known_hobbies = set(db.scalars(select(Hobby.id).where(Hobby.id.in_(hobby_ids))).all())
            unknown_hobbies = sorted(set(hobby_ids) - known_hobbies)
            if unknown_hobbies:
                raise HTTPException(status_code=422, detail=f"Unknown hobby IDs: {unknown_hobbies}")
            user.name = details.name
            db.execute(delete(UserHobby).where(UserHobby.user_id == user.id))
            db.add_all([UserHobby(user_id=user.id, hobby_id=hobby_id) for hobby_id in hobby_ids])
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


def add_to_catalog(db: Session, model: type[Skill] | type[Hobby], name: str, response: Response) -> CatalogSkill:
    """Insert a catalogue entry, or return the existing one (names match ignoring case and spaces)."""
    try:
        # The unique index also handles simultaneous submissions of the same name.
        row = db.execute(
            insert(model).values(name=name)
            .on_conflict_do_nothing(index_elements=[func.lower(func.btrim(model.name))])
            .returning(model.id, model.name)
        ).first()
        if row is None:
            row = db.execute(
                select(model.id, model.name).where(
                    func.lower(func.btrim(model.name)) == func.lower(func.btrim(name))
                )
            ).one()
            response.status_code = 200
        result = CatalogSkill(id=row.id, name=row.name)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


@router.get("/skills", response_model=list[CatalogSkill])
def get_skills(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Skill).order_by(Skill.name, Skill.id)).all()


@router.post("/skills", response_model=CatalogSkill, status_code=201)
def create_skill(
    data: SkillCreate, response: Response,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return add_to_catalog(db, Skill, data.name, response)


@router.get("/hobbies", response_model=list[CatalogSkill])
def get_hobbies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Hobby).order_by(Hobby.name, Hobby.id)).all()


@router.post("/hobbies", response_model=CatalogSkill, status_code=201)
def create_hobby(
    data: SkillCreate, response: Response,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return add_to_catalog(db, Hobby, data.name, response)


@router.get("/users/{user_id}", response_model=PublicProfileOut)
def get_user_profile(
    user_id: int = Path(gt=0, le=2147483647),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    profile = read_profile(db, target)
    return PublicProfileOut(id=profile.id, name=profile.name, skills=profile.skills)
