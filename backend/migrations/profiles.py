"""Run the profile SQL migrations in one PostgreSQL transaction."""

from pathlib import Path

from sqlalchemy.engine import Engine

from ..config import engine


def migrate_profiles(target: Engine) -> None:
    if target.dialect.name != "postgresql":
        raise ValueError("The profile SQL migration requires PostgreSQL")
    migrations = Path(__file__).parent
    with target.begin() as connection:
        for name in (
            "002_user_profiles.sql",
            "003_shared_skill_names.sql",
            "004_remove_open_to_teach.sql",
            "005_remove_user_department_year.sql",
            "006_remove_user_availability.sql",
            "007_hobby_catalog.sql",
            "008_team_details.sql",
        ):
            connection.exec_driver_sql((migrations / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    migrate_profiles(engine)
    print("Profile migration completed.")
