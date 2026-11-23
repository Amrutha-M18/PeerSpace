import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from .config import engine
from .migrations.profiles import migrate_profiles
from .models import Base, Hobby, Skill

SEED_DIR = Path(__file__).parent / "seed_data"
CATALOGUES = {"skills": (Skill, "skills.txt"), "hobbies": (Hobby, "hobbies.txt")}


def read_names(filename: str) -> list[str]:
    """One name per line; blank lines and lines starting with # are skipped."""
    names = []
    for line in (SEED_DIR / filename).read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            names.append(name)
    return names


def seed(which: list[str]) -> None:
    Base.metadata.create_all(engine)
    migrate_profiles(engine)
    with engine.begin() as connection:
        for key in which:
            model, filename = CATALOGUES[key]
            names = read_names(filename)
            before = connection.scalar(select(func.count()).select_from(model))
            connection.execute(
                insert(model).values([{"name": name} for name in names])
                .on_conflict_do_nothing(index_elements=[func.lower(func.btrim(model.name))])
            )
            after = connection.scalar(select(func.count()).select_from(model))
            print(f"{key}: {after - before} added, {after} in the table ({filename} lists {len(names)})")


if __name__ == "__main__":
    which = sys.argv[1:] or list(CATALOGUES)
    unknown = [name for name in which if name not in CATALOGUES]
    if unknown:
        sys.exit(f"Unknown catalogue: {', '.join(unknown)}. Use: skills, hobbies")
    seed(which)
