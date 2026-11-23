"""Run the profile SQL migration in one PostgreSQL transaction."""

from pathlib import Path

from sqlalchemy.engine import Engine

from ..config import engine


def migrate_profiles(target: Engine) -> None:
    if target.dialect.name != "postgresql":
        raise ValueError("The profile SQL migration requires PostgreSQL")
    migrations = Path(__file__).parent
    with target.begin() as connection:
        for name in ("002_user_profiles.sql", "003_shared_skill_names.sql"):
            connection.exec_driver_sql((migrations / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    migrate_profiles(engine)
    print("Profile migration completed.")
