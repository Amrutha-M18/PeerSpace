"""HTTP API for the PeerSpace opportunity discovery POC."""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .scraper import scrape_opportunities
from .sources import DOMAIN_LABELS

app = FastAPI(title="PeerSpace Opportunity Discovery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/opportunities")
def get_opportunities(domain: str = Query(..., description="cse, electrical, or mechanical")):
    """Fetch current public opportunities for one supported engineering domain."""
    if domain not in DOMAIN_LABELS:
        allowed = ", ".join(DOMAIN_LABELS)
        raise HTTPException(status_code=400, detail=f"Unsupported domain. Choose one of: {allowed}.")

    opportunities, warnings = scrape_opportunities(domain)
    return {
        "domain": domain,
        "opportunities": opportunities,
        "warnings": warnings,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health_check():
    """Small endpoint to confirm that the backend has started."""
    return {"status": "ok"}
