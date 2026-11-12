#Reads settings like the database URL from the environment

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_TOKEN = os.getenv("JWT_TOKEN")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Connected to PostgreSQL!")



