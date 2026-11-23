#Reads settings like the database URL from the environment

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

load_dotenv()

# Defaults match docker-compose.yaml, so the app also runs without a .env file.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mydb")
database_url = make_url(DATABASE_URL)
if database_url.get_backend_name() != "postgresql":
    raise ValueError("DATABASE_URL must use PostgreSQL")
if database_url.drivername == "postgresql":
    # Keep plain PostgreSQL URLs on the driver declared in requirements.txt.
    database_url = database_url.set(drivername="postgresql+psycopg2")
JWT_TOKEN = os.getenv("JWT_TOKEN", "dev-only-secret-change-me-in-the-env-file")  # secret used to sign login tokens

engine = create_engine(database_url)



