"""HTTP API for the PeerSpace opportunity discovery POC."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import auth, opportunities
from .config import engine
from .database import get_db
from .models import Base
from .scraper import scrape_opportunities
from .sources import DOMAIN_LABELS


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
app.include_router(opportunities.router)


@app.get("/api/opportunities")
def get_opportunities(
    domain: str | None = Query(None, description="cse, electrical, or mechanical"),
    category: opportunities.Category | None = None,
    q: str | None = None,
    upcoming: bool | None = None,
    db: Session = Depends(get_db),
):
    """List saved opportunities, or fetch public listings for a domain."""
    if domain is None:
        return opportunities.list_opportunities(db, category, q, upcoming)

    if category is not None or q is not None or upcoming is not None:
        raise HTTPException(status_code=400, detail="Domain cannot be combined with stored opportunity filters.")
    if domain not in DOMAIN_LABELS:
        allowed = ", ".join(DOMAIN_LABELS)
        raise HTTPException(status_code=400, detail=f"Unsupported domain. Choose one of: {allowed}.")

    results, warnings = scrape_opportunities(domain)
    return {
        "domain": domain,
        "opportunities": results,
        "warnings": warnings,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health_check():
    """Small endpoint to confirm that the backend has started."""
    return {"status": "ok"}
