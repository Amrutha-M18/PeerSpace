"""PostgreSQL-only tests with a disposable database and isolated schemas."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from backend.config import engine as application_engine
from backend.database import get_db
from backend.main import app
from backend.models import Base, Skill


@pytest.fixture(scope="session")
def test_database_url():
    configured = os.getenv("PEERSPACE_TEST_DATABASE_URL")
    if configured:
        url = make_url(configured)
        if url.get_backend_name() != "postgresql":
            pytest.fail("PEERSPACE_TEST_DATABASE_URL must use PostgreSQL")
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg2")
        yield url
        return

    # Use the configured server credentials, but never its application database tables.
    name = "peerspace_test_" + uuid4().hex
    admin = create_engine(application_engine.url, isolation_level="AUTOCOMMIT")
    created = False
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        created = True
        yield application_engine.url.set(database=name)
    finally:
        if created:
            with admin.begin() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{name}"')
        admin.dispose()


@pytest.fixture
def profile_engine(test_database_url):
    # Every test owns a unique schema, including migration tests that need an empty schema.
    schema = "test_" + uuid4().hex
    admin = create_engine(test_database_url)
    engine = create_engine(test_database_url, connect_args={"options": f"-csearch_path={schema}"})
    created = False
    try:
        with admin.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        created = True
        yield engine
    finally:
        engine.dispose()
        if created:
            with admin.begin() as connection:
                connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        admin.dispose()


@pytest.fixture
def profile_db(profile_engine):
    Base.metadata.create_all(profile_engine)
    return sessionmaker(bind=profile_engine)


@pytest.fixture
def client(profile_db):
    def test_db():
        with profile_db() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    client = TestClient(app)
    try:
        # Do not run app lifespan: it initializes the configured development DB.
        yield client
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def profile_client(client, profile_db):
    with profile_db() as db:
        db.add_all([Skill(name="Python"), Skill(name="SQL")])
        db.commit()
    return client


@pytest.fixture
def signed_in(profile_client):
    payload = {"name": "Student", "email": "student@example.com", "password": "test-password"}
    response = profile_client.post("/api/auth/signup", json=payload)
    assert response.status_code == 201
    login = profile_client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    profile_client.headers["Authorization"] = "Bearer " + login.json()["token"]
    return profile_client
