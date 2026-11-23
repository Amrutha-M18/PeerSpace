"""Main FastAPI application for the PeerSpace platform."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import auth
from .config import engine
from .models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # create any missing tables at startup (no Alembic)
    yield


app = FastAPI(title="PeerSpace API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router)


@app.get("/health")
def health_check():
    """Small endpoint to confirm that the backend has started."""
    return {"status": "ok"}
