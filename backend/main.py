
"""Main FastAPI application for the PeerSpace platform."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import auth, opportunities
from .config import engine
from .database import get_db
from .models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
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
app.include_router(opportunities.router)


@app.get("/api/opportunities")
def get_opportunities(
    category: opportunities.Category | None = None,
    q: str | None = None,
    upcoming: bool | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    if domain is not None:
        raise HTTPException(
            status_code=400,
            detail="Domain-based scraping is no longer supported.",
        )

    return opportunities.list_opportunities(db, category, q, upcoming)


@app.get("/health")
def health_check():
    return {"status": "ok"}
