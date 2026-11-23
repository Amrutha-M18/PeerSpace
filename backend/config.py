#Reads settings like the database URL from the environment

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

load_dotenv()

# Defaults match docker-compose.yaml, so the app also runs without a .env file.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/mydb")
JWT_TOKEN = os.getenv("JWT_TOKEN", "dev-only-secret-change-me-in-the-env-file")  # secret used to sign login tokens

engine = create_engine(database_url)



