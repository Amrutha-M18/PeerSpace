from datetime import date, datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped,mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    year: Mapped[str | None] = mapped_column(String(30))         
    # Existing JSON field retained for compatibility; profile APIs use UserSkill.
    skills: Mapped[list] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    hobbies: Mapped[list] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    availability: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    __table_args__ = (
        Index("uq_skills_name_normalized", func.lower(func.btrim(name)), unique=True),
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    level: Mapped[int]
    open_to_teach: Mapped[bool]

    __table_args__ = (CheckConstraint("level BETWEEN 1 AND 5", name="ck_user_skills_level"),)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30))           
    organizer: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(20), default="user")
    is_team_based: Mapped[bool] = mapped_column(default=True)   
    starts_on: Mapped[date | None]
    ends_on: Mapped[date | None]
    official_url: Mapped[str | None] = mapped_column(String(500))
    team_size: Mapped[int | None]
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    capacity: Mapped[int]                                      
    needed_skills: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="open")  
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20), default="member") 
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("team_id", "user_id"),)


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    looking_for_team: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "opportunity_id"),)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(40))   
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
