"""PostgreSQL-only checks, isolated in temporary schemas of a disposable test DB."""

from pathlib import Path

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from backend.migrations.profiles import migrate_profiles
from backend.models import Skill, User, UserSkill
from backend.profiles import read_profile

LEGACY_USERS = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY, email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, name VARCHAR(100) NOT NULL,
    department VARCHAR(100), year VARCHAR(30), skills JSON NOT NULL,
    availability JSON NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT now()
)
"""


def test_fresh_migration_matches_models_and_is_repeatable(profile_engine):
    migrate_profiles(profile_engine)
    migrate_profiles(profile_engine)
    inspector = inspect(profile_engine)
    for model in (User, Skill, UserSkill):
        expected = model.__table__
        columns = inspector.get_columns(expected.name)
        assert {column["name"] for column in columns} == set(expected.columns.keys())
        for column in columns:
            target = expected.columns[column["name"]]
            assert column["nullable"] == target.nullable
            assert str(column["type"].compile(dialect=profile_engine.dialect)) == str(target.type.compile(dialect=profile_engine.dialect))
        assert inspector.get_pk_constraint(expected.name)["constrained_columns"] == [column.name for column in expected.primary_key]
    assert inspector.get_unique_constraints("skills")[0]["column_names"] == ["name"]
    assert inspector.get_unique_constraints("users")[0]["column_names"] == ["email"]
    assert {fk["constrained_columns"][0] for fk in inspector.get_foreign_keys("user_skills")} == {"user_id", "skill_id"}
    assert inspector.get_check_constraints("user_skills")[0]["name"] == "ck_user_skills_level"
    with Session(profile_engine) as db:
        assert db.scalars(select(Skill)).all() == []
        user = User(email="fresh@example.com", password_hash="hash", name="Fresh")
        skill = Skill(name="Python")
        db.add_all([user, skill])
        db.commit()
        db.add(UserSkill(user_id=user.id, skill_id=skill.id, level=5))
        db.commit()
        profile = read_profile(db, user)
        assert profile.hobbies == []
        assert profile.skills[0].name == "Python"


def test_upgrade_preserves_existing_user_and_adds_defaults(profile_engine):
    with profile_engine.begin() as connection:
        connection.exec_driver_sql(LEGACY_USERS)
        connection.exec_driver_sql("INSERT INTO users (email,password_hash,name,skills,availability) VALUES ('old@example.com','hash','Existing','[]','[\"Weekends\"]')")
    migrate_profiles(profile_engine)
    with Session(profile_engine) as db:
        user = db.scalar(select(User))
        assert user.name == "Existing" and user.email == "old@example.com"
        assert user.availability == ["Weekends"] and user.hobbies == []
        assert user.skills == []
        # Signup-style inserts also work against the upgraded legacy schema.
        db.add(User(email="new@example.com", password_hash="hash", name="New"))
        db.commit()


@pytest.mark.parametrize("teaching_flag", [True, False])
def test_upgrade_removes_teaching_flag_and_preserves_selections(profile_engine, teaching_flag):
    baseline = Path(__file__).parents[1] / "migrations" / "002_user_profiles.sql"
    with profile_engine.begin() as connection:
        connection.exec_driver_sql(baseline.read_text(encoding="utf-8"))
        # Reproduce the previously deployed schema, including its required flag.
        connection.exec_driver_sql("ALTER TABLE user_skills ADD COLUMN open_to_teach BOOLEAN NOT NULL")
        user_id = connection.execute(text("INSERT INTO users (email,password_hash,name,availability) VALUES ('old@example.com','hash','Existing','[]') RETURNING id")).scalar_one()
        skill_id = connection.execute(text("INSERT INTO skills (name) VALUES ('Python') RETURNING id")).scalar_one()
        connection.execute(
            text("INSERT INTO user_skills (user_id,skill_id,level,open_to_teach) VALUES (:user,:skill,4,:flag)"),
            {"user": user_id, "skill": skill_id, "flag": teaching_flag},
        )

    migrate_profiles(profile_engine)
    migrate_profiles(profile_engine)

    assert {column["name"] for column in inspect(profile_engine).get_columns("user_skills")} == {
        "user_id", "skill_id", "level",
    }
    with Session(profile_engine) as db:
        user = db.get(User, user_id)
        assert user.email == "old@example.com"
        assert read_profile(db, user).skills[0].model_dump() == {
            "skill_id": skill_id, "name": "Python", "level": 4,
        }
        skill = Skill(name="SQL")
        db.add(skill)
        db.flush()
        db.add(UserSkill(user_id=user_id, skill_id=skill.id, level=2))
        db.commit()
        assert len(read_profile(db, user).skills) == 2


@pytest.mark.parametrize("retired_values", [("Computer Science", "2"), (None, None)])
def test_upgrade_removes_retired_profile_fields_and_preserves_data(profile_engine, retired_values):
    baseline = Path(__file__).parents[1] / "migrations" / "002_user_profiles.sql"
    with profile_engine.begin() as connection:
        connection.exec_driver_sql(baseline.read_text(encoding="utf-8"))
        connection.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN department VARCHAR(100), ADD COLUMN year VARCHAR(30)"
        )
    with Session(profile_engine) as db:
        user = User(
            email="existing@example.com", password_hash="preserved-hash", name="Existing",
            hobbies=["Photography"], availability=["Weekends"],
        )
        skill = Skill(name="Python")
        db.add_all([user, skill])
        db.flush()
        db.add(UserSkill(user_id=user.id, skill_id=skill.id, level=4))
        db.execute(
            text("UPDATE users SET department=:department, year=:year WHERE id=:id"),
            {"department": retired_values[0], "year": retired_values[1], "id": user.id},
        )
        db.commit()
        user_id = user.id
        before = read_profile(db, user).model_dump()

    migrate_profiles(profile_engine)
    migrate_profiles(profile_engine)

    assert {column["name"] for column in inspect(profile_engine).get_columns("users")} == set(
        User.__table__.columns.keys()
    )
    with Session(profile_engine) as db:
        user = db.get(User, user_id)
        assert read_profile(db, user).model_dump() == before
        assert user.password_hash == "preserved-hash"
        assert user.skills == []
        user.name = "Updated"
        db.commit()
        assert read_profile(db, user).name == "Updated"


def test_nonempty_legacy_skills_abort_without_schema_or_data_changes(profile_engine):
    with profile_engine.begin() as connection:
        connection.exec_driver_sql(LEGACY_USERS)
        connection.exec_driver_sql("INSERT INTO users (email,password_hash,name,skills,availability) VALUES ('old@example.com','hash','Existing','[\"Python\"]','[]')")
    with pytest.raises(DBAPIError, match="Nonempty legacy user skills"):
        migrate_profiles(profile_engine)
    inspector = inspect(profile_engine)
    assert inspector.get_table_names() == ["users"]
    assert "hobbies" not in {column["name"] for column in inspector.get_columns("users")}
    with profile_engine.connect() as connection:
        assert connection.execute(text("SELECT skills FROM users")).scalar() == ["Python"]


def test_postgres_enforces_skill_constraints(profile_engine):
    migrate_profiles(profile_engine)
    with profile_engine.begin() as connection:
        user_id = connection.execute(text("INSERT INTO users (email,password_hash,name,availability) VALUES ('test@example.com','hash','Test','[]') RETURNING id")).scalar_one()
        skill_id = connection.execute(text("INSERT INTO skills (name) VALUES ('Python') RETURNING id")).scalar_one()
        insert_sql = text("INSERT INTO user_skills (user_id,skill_id,level) VALUES (:user,:skill,:level)")
        valid = {"user": user_id, "skill": skill_id, "level": 3}
        for invalid in ({"level": 0}, {"level": 6}, {"level": None}, {"skill": 9999}, {"user": 9999}):
            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(insert_sql, {**valid, **invalid})
        connection.execute(insert_sql, valid)
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(insert_sql, valid)
        connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})
        assert connection.execute(text("SELECT COUNT(*) FROM user_skills")).scalar() == 0


def test_catalog_upgrade_preserves_ids_and_rejects_case_duplicates(profile_engine):
    old_migration = Path(__file__).parents[1] / "migrations" / "002_user_profiles.sql"
    with profile_engine.begin() as connection:
        connection.exec_driver_sql(old_migration.read_text(encoding="utf-8"))
        skill_id = connection.execute(text("INSERT INTO skills (name) VALUES ('python') RETURNING id")).scalar_one()
    migrate_profiles(profile_engine)
    with profile_engine.begin() as connection:
        assert connection.execute(text("SELECT id FROM skills WHERE name='python'")).scalar_one() == skill_id
        assert connection.execute(text("SELECT COUNT(*) FROM skills")).scalar_one() == 1
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(text("INSERT INTO skills (name) VALUES (' PYTHON ')"))


def test_catalog_upgrade_does_not_delete_conflicting_old_entries(profile_engine):
    old_migration = Path(__file__).parents[1] / "migrations" / "002_user_profiles.sql"
    with profile_engine.begin() as connection:
        connection.exec_driver_sql(old_migration.read_text(encoding="utf-8"))
        connection.execute(text("INSERT INTO skills (name) VALUES ('Python'), ('python')"))
    with pytest.raises(IntegrityError):
        migrate_profiles(profile_engine)
    with profile_engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM skills")).scalar_one() == 2
    assert "uq_skills_name_normalized" not in {index["name"] for index in inspect(profile_engine).get_indexes("skills")}
