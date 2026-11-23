"""The starter lists in backend/seed_data/ and the loader that reads them."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.migrations.profiles import migrate_profiles
from backend.models import Hobby, Skill
from backend.seed_catalog import CATALOGUES, read_names


def test_seed_files_have_no_blank_or_duplicate_names():
    for key, (_, filename) in CATALOGUES.items():
        names = read_names(filename)
        assert len(names) >= 20, key
        assert all(name == name.strip() and not name.startswith("#") for name in names)
        lowered = [name.lower() for name in names]
        assert len(lowered) == len(set(lowered)), f"duplicate in {filename}"
        assert all(len(name) <= 100 for name in names)


def test_seed_lists_load_into_the_catalogue_tables(profile_engine):
    migrate_profiles(profile_engine)
    for _ in range(2):  # running twice adds nothing new
        with profile_engine.begin() as connection:
            for model, filename in CATALOGUES.values():
                connection.execute(
                    insert(model).values([{"name": name} for name in read_names(filename)])
                    .on_conflict_do_nothing(index_elements=[func.lower(func.btrim(model.name))])
                )
    with Session(profile_engine) as db:
        assert db.scalar(select(func.count()).select_from(Skill)) == len(read_names("skills.txt"))
        assert db.scalar(select(func.count()).select_from(Hobby)) == len(read_names("hobbies.txt"))
